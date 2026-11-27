import math
import random
import pygame
from personaje import (Personaje, repartir_dano, REGEN_ESCUDO_RETRASO, REGEN_ESCUDO_POR_SEGUNDO,
                       AUTOAPUNTADO_MARGEN_CLIC, MONEDAS_POR_NIVEL, PUNTOS_MEJORA_POR_NIVEL,
                       REGEN_ENERGIA_POR_PUNTO, REGEN_ENERGIA_TOPE)
from habilidades import (dibujar_panel_habilidades, dibujar_badge_ayuda, dibujar_tooltip, PIXELES_POR_PUNTO_EMPUJE,
                         actualizar_anulacion_escudo_magico, actualizar_ralentizacion, aplicar_quemadura,
                         aplicar_veneno, aplicar_corrosion, factor_dano_corrosion, enemigo_en,
                         COLOR_VENENO, encender_combustible,
                         animaciones_activas, set_animaciones_activas)
from herramientas import EspadaLigera, EspadaLarga
from vegetacion import SistemaVegetacion, OSCURECIMIENTO, RejillaEspacial, CELDA_REJILLA
from limite_mundo import LIMITE as LIMITE_MUNDO, BORDE_LIBRE
from diseno_mapa import Diseno
import fauna as FAUNA
from fauna import SistemaFauna
from spawn import Casa, RADIO_JARDIN
from vendedores import SistemaVendedores, dibujar_tienda, rect_tienda, todos_al_maximo
from tumba import Tumba, guardar_estado, restaurar_estado
from inventario import dibujar_inventario, rect_inventario, nuevo_estado_inventario, manejar_clic_inventario
import talismanes as TL
import gacha as GACHA

# -----------------------------
# CONFIGURACIÓN DEL MAPA
# -----------------------------
# Mapa cuadrado (limite_mundo.LIMITE, Fase 2 del plan de NPC): lado 17 700 px, la misma
# superficie que el circulo de radio 10 000 de antes, con la casa del spawn en el centro.
LIMITE = LIMITE_MUNDO
TAMANO_MUNDO = LIMITE.tamano
CENTRO_MUNDO = pygame.Vector2(LIMITE.centro)

# Rocas y lagos escalan con el AREA del mundo: la densidad se define para un mundo de
# referencia (un circulo de radio 5000) y se multiplica por area / area de referencia.
RADIO_MUNDO_REFERENCIA = 5000
ESCALA_AREA_MUNDO = LIMITE.area / (math.pi * RADIO_MUNDO_REFERENCIA ** 2)
ROCAS_POR_AREA_REFERENCIA = (150, 300)
CHARCOS_POR_AREA_REFERENCIA = (6, 10)
MIN_ROCAS = round(ROCAS_POR_AREA_REFERENCIA[0] * ESCALA_AREA_MUNDO)       # 600 en radio 10000
MAX_ROCAS = round(ROCAS_POR_AREA_REFERENCIA[1] * ESCALA_AREA_MUNDO)       # 1200
MIN_CHARCOS = round(CHARCOS_POR_AREA_REFERENCIA[0] * ESCALA_AREA_MUNDO)   # 24
MAX_CHARCOS = round(CHARCOS_POR_AREA_REFERENCIA[1] * ESCALA_AREA_MUNDO)   # 40
INTENTOS_POR_ROCA = 30          # Intentos de colocacion por roca objetivo
INTENTOS_POR_CHARCO = 60        # Intentos de colocacion por lago objetivo
RADIO_CHARCO_MIN = 150
RADIO_CHARCO_MAX = 750
ANCHO_BARRO = 7             # Margen de barro alrededor del agua
ZONA_SEGURA_SPAWN = RADIO_JARDIN + 50   # Sin rocas, lagos ni plantas: la casa del spawn y su jardin
SEPARACION_ROCAS = 15       # px minimos entre una roca y cualquier otro obstaculo al generarla
SUAVIZADO_CAMARA = 8.0      # Más alto = la cámara sigue más pegada al personaje
# Semilla fija del terreno: lagos, vegetacion y rocas salen identicos en cada partida (mapa
# principal fijo). Paso intermedio hasta el mundo guardado en archivo (Fase 2 del plan de NPC).
# Solo fija el terreno: la fauna, los cofres y el botin siguen siendo aleatorios.
SEMILLA_MUNDO = 1
MAPA_POR_DEFECTO = "principal"   # mapas/principal.json (Fase 2); habra 4 mapas extra
# Interruptor general de los personajes NPC (plan de NPC). Todavia sin efecto: no hay NPC.
NPC_ACTIVOS = False
TAMANO_CUADRICULA = 60

COLOR_FUERA_MAPA = (16, 18, 23)
COLOR_SUELO = (28, 32, 40)
COLOR_CUADRICULA = (36, 42, 52)
COLOR_BORDE_MAPA = (90, 105, 130)
COLOR_BARRO = (128, 98, 66)
COLOR_AGUA = (38, 104, 182)
COLOR_AGUA_CLARA = (62, 136, 214)
COLOR_AGUA_PROFUNDA = (16, 52, 104)   # Centro oscuro de los lagos grandes (zona de peligro)
COLOR_NENUFAR = (46, 120, 70)
COLOR_NENUFAR_BORDE = (28, 80, 48)
COLOR_FLOR = (235, 225, 240)
COLOR_FLOR_ROSA = (235, 150, 185)
COLOR_JUNCO = (70, 140, 70)
COLOR_JUNCO_PUNTA = (120, 85, 50)

# Lagos grandes: si el radio supera este umbral, su centro es una zona peligrosa
RADIO_LAGO_PELIGRO = 300
DEBUFF_LAGO_PROFUNDO = 0.80           # -80% de movilidad en la zona central
DANO_LAGO_PROFUNDO = 10               # Vida perdida por segundo en la zona central
FACTOR_ZONA_PELIGRO = 0.35            # Tamaño de la zona central respecto al radio del lago


# -----------------------------
# CHARCOS DE AGUA (RALENTIZAN -50%)
# -----------------------------
class Charco:
    """Charco con forma de nube: unión de un círculo central y varios lóbulos alrededor."""

    def __init__(self, x, y, radio):
        self.centro = pygame.Vector2(x, y)
        self.radio = radio

        # Círculos que forman la nube (en coordenadas del mundo)
        self.circulos = [(pygame.Vector2(x, y), radio * 0.62)]
        lobulos = random.randint(5, 8)
        for i in range(lobulos):
            ang = (i / lobulos) * math.tau + random.uniform(-0.3, 0.3)
            r_lobulo = radio * random.uniform(0.32, 0.45)
            dist = (radio - r_lobulo) * random.uniform(0.85, 1.0)
            pos = pygame.Vector2(x + math.cos(ang) * dist, y + math.sin(ang) * dist)
            self.circulos.append((pos, r_lobulo))

        self.evaporados = []      # circulos evaporados por Estrella Ignea (ya no son agua)

        # Pre-renderizar el charco una sola vez (barro + agua + brillo)
        extension = radio + ANCHO_BARRO + 18
        lado = int(extension * 2)
        self.superficie = pygame.Surface((lado, lado), pygame.SRCALPHA)
        origen = pygame.Vector2(x - extension, y - extension)
        self.rect = pygame.Rect(round(origen.x), round(origen.y), lado, lado)

        locales = [(c - origen, r) for c, r in self.circulos]
        for c, r in locales:
            pygame.draw.circle(self.superficie, COLOR_BARRO, (round(c.x), round(c.y)), round(r + ANCHO_BARRO))
        for c, r in locales:
            pygame.draw.circle(self.superficie, COLOR_AGUA, (round(c.x), round(c.y)), round(r))
        for c, r in locales:
            pygame.draw.circle(self.superficie, COLOR_AGUA_CLARA,
                               (round(c.x - r * 0.15), round(c.y - r * 0.15)), round(r * 0.6))

        # Lago profundo: zona central oscura con efectos peligrosos (-80% vel y daño por segundo)
        self.es_lago_profundo = radio > RADIO_LAGO_PELIGRO
        self.radio_peligro = radio * FACTOR_ZONA_PELIGRO if self.es_lago_profundo else 0
        if self.es_lago_profundo:
            centro_local = self.centro - origen
            pygame.draw.circle(self.superficie, COLOR_AGUA_PROFUNDA,
                               (round(centro_local.x), round(centro_local.y)), round(self.radio_peligro))

        # Flora acuatica: nenufares sobre el agua y juncos/espadanas en las orillas
        self.nenufares = []  # posiciones (mundo) de los nenufares, para la fauna
        for _ in range(max(2, int(radio / 45))):
            c, r = random.choice(locales)
            pr = random.randint(5, 9)
            ang = random.uniform(0, math.tau)
            d = random.uniform(0, max(0.0, r - pr - 3))
            lx = c.x + math.cos(ang) * d
            ly = c.y + math.sin(ang) * d
            self.nenufares.append((pygame.Vector2(origen.x + lx, origen.y + ly), pr))
            pygame.draw.circle(self.superficie, COLOR_NENUFAR_BORDE, (round(lx), round(ly)), pr + 1)
            pygame.draw.circle(self.superficie, COLOR_NENUFAR, (round(lx), round(ly)), pr)
            na = random.uniform(0, math.tau)
            pygame.draw.line(self.superficie, COLOR_AGUA, (round(lx), round(ly)),
                             (round(lx + math.cos(na) * pr), round(ly + math.sin(na) * pr)), 2)
            if random.random() < 0.4:
                pygame.draw.circle(self.superficie, random.choice((COLOR_FLOR, COLOR_FLOR_ROSA)), (round(lx), round(ly)), 2)
        for _ in range(max(3, int(radio / 35))):
            c, r = random.choice(locales)
            ang = random.uniform(0, math.tau)
            bx = c.x + math.cos(ang) * r
            by = c.y + math.sin(ang) * r
            for _ in range(random.randint(2, 4)):
                tx = bx + random.uniform(-4, 4)
                ty = by + random.uniform(-3, 3)
                h = random.randint(8, 16)
                pygame.draw.line(self.superficie, COLOR_JUNCO, (round(tx), round(ty)), (round(tx), round(ty - h)), 1)
                if random.random() < 0.5:
                    pygame.draw.circle(self.superficie, COLOR_JUNCO_PUNTA, (round(tx), round(ty - h)), 2)

    def evaporar(self, centro, radio):
        """Estrella Ignea: el agua dentro del circulo desaparece para siempre (queda la orilla)."""
        self.evaporados.append((pygame.Vector2(centro), radio))
        origen = pygame.Vector2(self.rect.topleft)
        # Mancha de orilla solo dentro de la forma del charco (con su borde de barro)
        forma = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        for c, r in self.circulos:
            pygame.draw.circle(forma, (255, 255, 255, 255), (round(c.x - origen.x), round(c.y - origen.y)), round(r + ANCHO_BARRO))
        mancha = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.circle(mancha, (*COLOR_BARRO, 255), (round(centro.x - origen.x), round(centro.y - origen.y)), round(radio))
        mancha.blit(forma, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        self.superficie.blit(mancha, (0, 0))

    def _evaporado(self, punto):
        return any((punto - c).length() <= r for c, r in self.evaporados)

    def contiene(self, punto):
        """True si el punto (centro del jugador) está sobre el agua."""
        return any((punto - c).length() <= r for c, r in self.circulos) and not self._evaporado(punto)

    def en_zona_peligro(self, punto):
        """True si el punto está en la zona central peligrosa de un lago grande."""
        return (self.es_lago_profundo and (punto - self.centro).length() <= self.radio_peligro
                and not self._evaporado(punto))

    def dibujar(self, pantalla, desplazamiento):
        pantalla.blit(self.superficie, (self.rect.x - desplazamiento[0], self.rect.y - desplazamiento[1]))


def fuera_de_zonas_libres(p, extension, diseno):
    """True si un objeto de 'extension' px en 'p' no pisa el jardin de la casa ni las zonas
    despejadas del diseno (p. ej. la del guardian)."""
    if (p - CENTRO_MUNDO).length() - extension < ZONA_SEGURA_SPAWN:
        return False
    return all((p - c).length() - extension >= r for c, r in diseno.zonas_libres_abs(LIMITE))


def generar_charcos(diseno=None):
    """Genera los lagos (por defecto MIN_CHARCOS a MAX_CHARCOS, que escalan con el area del
    mundo) dentro del cuadrado y sin solaparse. Las 'lagunas' del diseno (lagos grandes, con
    zona profunda) se colocan primero."""
    d = diseno if diseno is not None else Diseno()
    charcos = []
    objetivo = random.randint(*(d.lagos or (MIN_CHARCOS, MAX_CHARCOS)))
    radios_lagunas = [random.randint(*d.laguna_radio) for _ in range(d.lagunas)]
    intentos = 0
    while len(charcos) < objetivo and intentos < objetivo * INTENTOS_POR_CHARCO:
        intentos += 1
        if len(charcos) < len(radios_lagunas):
            radio = radios_lagunas[len(charcos)]
        else:
            radio = random.randint(*(d.lago_radio or (RADIO_CHARCO_MIN, RADIO_CHARCO_MAX)))
        extension = radio + ANCHO_BARRO + 10
        p = d.punto(LIMITE, "lago", extension + BORDE_LIBRE)
        if not fuera_de_zonas_libres(p, extension, d):
            continue
        nuevo = Charco(p.x, p.y, radio)

        if any(nuevo.rect.inflate(40, 40).colliderect(c.rect) for c in charcos):
            continue
        charcos.append(nuevo)
    return charcos


# -----------------------------
# ROCAS (OBSTÁCULOS DECORATIVOS)
# -----------------------------
LADO_ROCA_GIGANTE = 150     # Desde este lado la roca es gigante (Cortar solo la destruye a nivel 20)


class Roca:
    def __init__(self, x, y, lado):
        self.rect = pygame.Rect(round(x - lado / 2), round(y - lado / 2), lado, lado)
        self.gigante = lado >= LADO_ROCA_GIGANTE
        # Tono café pálido con ligera variación para que no todas se vean iguales
        v = random.randint(-14, 14)
        self.color = (186 + v, 160 + v, 124 + v)
        self.color_borde = (138 + v, 114 + v, 84 + v)
        self.color_brillo = (206 + v, 184 + v, 150 + v)

    def dibujar(self, superficie, desplazamiento=(0, 0)):
        rect = self.rect.move(-desplazamiento[0], -desplazamiento[1])
        radio_borde = max(3, rect.width // 8)
        pygame.draw.rect(superficie, self.color, rect, border_radius=radio_borde)
        # Brillo superior izquierdo para dar volumen
        brillo = pygame.Rect(rect.x + 4, rect.y + 4, rect.width // 2, max(3, rect.height // 5))
        pygame.draw.rect(superficie, self.color_brillo, brillo, border_radius=radio_borde)
        pygame.draw.rect(superficie, self.color_borde, rect, width=2, border_radius=radio_borde)


def _lado_roca(prob_gigante=0.05):
    """60 % pequeñas (22-45), el resto grandes (70-130) salvo 'prob_gigante' gigantes (150-300)."""
    r = random.random()
    if r < prob_gigante:
        return random.randint(LADO_ROCA_GIGANTE, 300)
    if r < prob_gigante + 0.35:
        return random.randint(70, 130)
    return random.randint(22, 45)


def generar_rocas(zonas_ocupadas=(), diseno=None):
    """
    Genera las rocas (por defecto MIN_ROCAS a MAX_ROCAS, que escalan con el area del mundo;
    pequeñas, grandes y gigantes) dentro del cuadrado, sin solaparse ni caer sobre zonas
    ocupadas (charcos, arbustos, arboles: cualquier objeto con .rect). Primero las montañas del
    diseno (grupos de rocas grandes y gigantes) y despues las sueltas.
    """
    d = diseno if diseno is not None else Diseno()
    rocas = []
    rejilla = RejillaEspacial(CELDA_REJILLA)
    for z in zonas_ocupadas:
        rejilla.agregar(z.rect)

    def colocar(x, y, lado):
        media_diagonal = lado * 0.75
        p = pygame.Vector2(x, y)
        if not LIMITE.dentro(p, media_diagonal + BORDE_LIBRE) or not fuera_de_zonas_libres(p, media_diagonal, d):
            return False
        nueva = Roca(x, y, lado)
        # Separacion minima con rocas/charcos/vegetacion (rejilla espacial = rapido)
        if rejilla.hay_colision(nueva.rect.inflate(SEPARACION_ROCAS * 2, SEPARACION_ROCAS * 2)):
            return False
        rejilla.agregar(nueva.rect)
        rocas.append(nueva)
        return True

    # Montañas: grupos de rocas alrededor de un punto (u, v) del diseno
    for u, v, radio, n, prob_gigante in d.montanas:
        centro = d.absoluto(LIMITE, u, v)
        puestas = intentos = 0
        while puestas < n and intentos < n * INTENTOS_POR_ROCA:
            intentos += 1
            ang = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * radio
            lado = _lado_roca(prob_gigante) if random.random() < 0.85 else random.randint(70, 130)
            puestas += colocar(centro.x + math.cos(ang) * dist, centro.y + math.sin(ang) * dist, lado)

    # Rocas sueltas, repartidas segun los factores del diseno
    cantidad = len(rocas) + random.randint(*(d.rocas or (MIN_ROCAS, MAX_ROCAS)))
    intentos = 0
    while len(rocas) < cantidad and intentos < cantidad * INTENTOS_POR_ROCA:
        intentos += 1
        lado = _lado_roca()
        p = d.punto(LIMITE, "roca", lado * 0.75 + BORDE_LIBRE)
        colocar(p.x, p.y, lado)
    return rocas


def generar_terreno(semilla=SEMILLA_MUNDO, diseno=None):
    """Genera el terreno (lagos, vegetacion, rocas y cuevas de oso) con una semilla fija y las
    reglas de un diseno (diseno_mapa; por defecto todo al azar). Es lo que usa el generador del
    mapa (mapa.py) y el respaldo si falta el archivo del mapa. Usa el generador global durante
    la generacion y despues lo devuelve a su estado anterior, asi lo que se sortea luego (fauna,
    cofres, botin...) sigue siendo imprevisible."""
    estado_azar = random.getstate()
    random.seed(semilla)
    try:
        charcos = generar_charcos(diseno)
        vegetacion = SistemaVegetacion(LIMITE, ZONA_SEGURA_SPAWN, charcos, diseno)
        rocas = generar_rocas(list(charcos) + vegetacion.arbustos + vegetacion.arboles, diseno)
        vegetacion.registrar_obstaculos(rocas)
        FAUNA.marcar_cuevas(rocas, diseno, LIMITE)
    finally:
        random.setstate(estado_azar)
    return charcos, vegetacion, rocas


def dibujar_suelo(pantalla, vista, desplazamiento):
    """
    Dibuja solo la parte visible del suelo: zona exterior, cuadrado del mapa, cuadrícula
    recortada al cuadrado, borde y marca del centro.
    """
    ox, oy = desplazamiento
    mapa = LIMITE.rect
    visible = mapa.clip(vista)
    if visible.width <= 0 or visible.height <= 0:
        return
    pygame.draw.rect(pantalla, COLOR_SUELO, visible.move(-ox, -oy))

    # Cuadrícula: solo las líneas visibles, recortadas al cuadrado
    inicio_x = (visible.left // TAMANO_CUADRICULA) * TAMANO_CUADRICULA
    for gx in range(inicio_x, visible.right + 1, TAMANO_CUADRICULA):
        if gx >= visible.left:
            pygame.draw.line(pantalla, COLOR_CUADRICULA, (gx - ox, visible.top - oy), (gx - ox, visible.bottom - oy), 1)
    inicio_y = (visible.top // TAMANO_CUADRICULA) * TAMANO_CUADRICULA
    for gy in range(inicio_y, visible.bottom + 1, TAMANO_CUADRICULA):
        if gy >= visible.top:
            pygame.draw.line(pantalla, COLOR_CUADRICULA, (visible.left - ox, gy - oy), (visible.right - ox, gy - oy), 1)

    # Borde del mapa y marca del centro (spawn)
    pygame.draw.rect(pantalla, COLOR_BORDE_MAPA, mapa.move(-ox, -oy), 3)
    pygame.draw.circle(pantalla, (45, 52, 66), (round(CENTRO_MUNDO.x - ox), round(CENTRO_MUNDO.y - oy)), 30, 1)

# -----------------------------
# DIBUJAR PANEL LATERAL IZQUIERDO (ESTADÍSTICAS Y HERRAMIENTA)
# -----------------------------
def dibujar_panel_estadisticas(pantalla, x, y, ancho, alto, jugador, fuentes, mostrar_hitboxes, info_abierta=None):
    fuente_titulo = fuentes["titulo"]
    fuente_sub = fuentes["sub"]
    fuente_mini = fuentes["mini"]
    fuente_val = fuentes["valor"]

    panel = pygame.Surface((ancho, alto))
    panel.fill((20, 23, 30))
    pantalla.blit(panel, (x, y))

    pygame.draw.line(pantalla, (45, 52, 68), (x + ancho, y), (x + ancho, y + alto), 2)

    botones = {}  # Botones (clave -> Rect): claves de stat, "__arma__" y "__info_stats__"

    # Cabecera
    titulo = fuente_titulo.render("FICHA PERSONAJE", True, (255, 215, 0))
    pantalla.blit(titulo, (x + 14, y + 15))

    # Icono de ayuda (?) -> explica las estadísticas como tooltip
    botones["__info_stats__"] = dibujar_badge_ayuda(pantalla, x + ancho - 20, y + 42, fuente_sub, info_abierta == "stats")

    color_pts = (120, 255, 150) if jugador.puntos_mejora > 0 else (130, 140, 160)
    sub = fuente_sub.render(f"Nivel {jugador.nivel}  ·  Puntos: {jugador.puntos_mejora}", True, color_pts)
    pantalla.blit(sub, (x + 14, y + 38))

    pygame.draw.line(pantalla, (45, 52, 68), (x + 14, y + 58), (x + ancho - 14, y + 58), 1)

    # Experiencia hacia el siguiente nivel (MÁX en el nivel máximo)
    if jugador.xp_siguiente is None:
        txt_xp = fuente_mini.render("XP: MÁX", True, COLOR_XP_MAX)
        prog_xp, col_xp = 1.0, COLOR_XP_MAX
    else:
        txt_xp = fuente_mini.render(f"XP: {jugador.xp:.1f} / {jugador.xp_siguiente}", True, COLOR_XP)
        prog_xp, col_xp = max(0.0, min(1.0, jugador.xp / jugador.xp_siguiente)), COLOR_XP
    pantalla.blit(txt_xp, (x + 14, y + 62))
    txt_monedas = fuente_mini.render(f"Monedas: {jugador.monedas}", True, COLOR_MONEDAS)
    pantalla.blit(txt_monedas, (x + ancho - 14 - txt_monedas.get_width(), y + 62))
    pygame.draw.rect(pantalla, (40, 45, 55), (x + 14, y + 78, ancho - 28, 5), border_radius=3)
    if prog_xp > 0:
        pygame.draw.rect(pantalla, col_xp, (x + 14, y + 78, int((ancho - 28) * prog_xp), 5), border_radius=3)

    # Mini tarjeta de avatar con ángulo de orientación
    avatar_y = y + 90
    pygame.draw.rect(pantalla, (26, 30, 40), (x + 12, avatar_y, ancho - 24, 52), border_radius=6)
    pygame.draw.rect(pantalla, (50, 60, 80), (x + 12, avatar_y, ancho - 24, 52), width=1, border_radius=6)

    pygame.draw.circle(pantalla, jugador.color, (x + 38, avatar_y + 26), 15)
    pygame.draw.circle(pantalla, (255, 255, 255), (x + 38, avatar_y + 26), 15, 2)

    nom_surf = fuente_sub.render(jugador.nombre, True, (255, 255, 255))
    pantalla.blit(nom_surf, (x + 64, avatar_y + 8))

    estado_mov = "En movimiento" if jugador.esta_en_movimiento() else "Parado (Regen x2)"
    color_mov = (100, 200, 255) if jugador.esta_en_movimiento() else (100, 255, 140)
    mov_surf = fuente_mini.render(f"{estado_mov} | {jugador.angulo:.0f}°", True, color_mov)
    pantalla.blit(mov_surf, (x + 64, avatar_y + 29))

    # Tarjeta de Herramienta / Arma
    arma = jugador.herramienta
    arma_y = avatar_y + 60
    es_arco = arma is not None and hasattr(arma, "comprar_flechas")
    arma_h = 136 if es_arco else 84   # el Arco suma la fila de carga y la compra de flechas
    pygame.draw.rect(pantalla, (28, 33, 44), (x + 12, arma_y, ancho - 24, arma_h), border_radius=6)
    if arma and arma.roto:
        color_borde_arma = (210, 80, 70)
    elif arma and arma.activa:
        color_borde_arma = (100, 255, 140)
    else:
        color_borde_arma = (50, 60, 80)
    pygame.draw.rect(pantalla, color_borde_arma, (x + 12, arma_y, ancho - 24, arma_h), width=1, border_radius=6)

    nombre_arma = arma.nombre if arma else "Sin arma"
    txt_arma_nom = fuente_sub.render(f"🗡 [1] {nombre_arma}", True, (255, 255, 255))
    pantalla.blit(txt_arma_nom, (x + 20, arma_y + 6))

    if arma:
        # Nivel (o ROTA) a la derecha del nombre
        if arma.roto:
            txt_nv = fuente_mini.render("ROTA", True, (255, 90, 80))
        else:
            color_nv = (255, 215, 120) if arma.nivel_maximo() else (160, 200, 255)
            txt_nv = fuente_mini.render(f"Nv {arma.nivel}/{arma.nivel_max}", True, color_nv)
        nv_x = x + ancho - 20 - txt_nv.get_width()
        pantalla.blit(txt_nv, (nv_x, arma_y + 8))

        # Botón [+] del arma (gasta un punto de mejora compartido; repara o sube de nivel)
        if jugador.puntos_mejora >= 2 and (arma.roto or arma.nivel < arma.nivel_max):
            bsize = 16
            rect_btn_arma = pygame.Rect(nv_x - bsize - 8, arma_y + 6, bsize, bsize)
            pygame.draw.rect(pantalla, (34, 78, 44), rect_btn_arma, border_radius=4)
            pygame.draw.rect(pantalla, (100, 230, 130), rect_btn_arma, width=1, border_radius=4)
            signo_arma = fuente_val.render("+", True, (150, 255, 180))
            pantalla.blit(signo_arma, signo_arma.get_rect(center=rect_btn_arma.center))
            botones["__arma__"] = rect_btn_arma

        if arma.roto:
            txt_est_arma = fuente_mini.render("ROTA — [+] para reparar", True, (255, 110, 100))
            txt_dano = fuente_mini.render("Daño inactivo", True, (120, 130, 150))
        elif arma.activa:
            db = arma.debuff_velocidad
            if db < 0:  # Valor negativo = buff de velocidad (ej. dagas a nivel máx)
                txt_vel = f"+{int(round(-db * 100))}% Vel"
                color_est = (120, 230, 150)
            else:
                txt_vel = f"-{int(round(db * 100))}% Vel"
                color_est = (255, 130, 80)
            txt_est_arma = fuente_mini.render(f"DESENFUNDADA ({txt_vel})", True, color_est)
            if arma.es_escudo:
                txt_dano = fuente_mini.render(f"Bloquea · desgaste -{arma.reduccion_desgaste * 100:g}% · Esc +{arma.bonus_escudos * 100:g}%", True, (120, 200, 255))
            elif es_arco:
                dano_arma = arma.calcular_dano(jugador)
                txt_dano = fuente_mini.render(f"Daño {dano_arma:.1f} · Flechas {arma.flechas}/{arma.capacidad_carcaj}", True, (255, 215, 0))
            else:
                dano_arma = arma.calcular_dano(jugador)
                txt_dano = fuente_mini.render(f"Daño {dano_arma:.1f} · Cad {arma.cadencia_efectiva(jugador):.2f}/s", True, (255, 215, 0))
        else:
            txt_est_arma = fuente_mini.render("GUARDADA (Pulsa [1])", True, (140, 150, 170))
            if arma.es_escudo:
                txt_dano = fuente_mini.render(f"Escudos +{arma.bonus_escudos * 100:g}% · [1] para bloquear", True, (120, 150, 180))
            elif es_arco:
                txt_dano = fuente_mini.render(f"Daño: Fuerza x{arma.multiplicador_dano:.2f} · Flechas {arma.flechas}/{arma.capacidad_carcaj}", True, (180, 160, 90))
            else:
                txt_dano = fuente_mini.render(f"Daño: Fuerza x{arma.multiplicador_dano:.1f}", True, (180, 160, 90))

        pantalla.blit(txt_est_arma, (x + 20, arma_y + 25))
        pantalla.blit(txt_dano, (x + 20, arma_y + 40))

        # Barra de durabilidad
        txt_dur = fuente_mini.render(f"Durabilidad: {arma.durabilidad:g}/{arma.durabilidad_max}", True, (150, 160, 180))
        pantalla.blit(txt_dur, (x + 20, arma_y + 55))
        bw = ancho - 40
        prog_dur = max(0.0, min(1.0, arma.durabilidad / max(1, arma.durabilidad_max)))
        col_dur = (100, 220, 120) if prog_dur > 0.5 else ((230, 200, 70) if prog_dur > 0.2 else (230, 90, 70))
        pygame.draw.rect(pantalla, (40, 45, 55), (x + 20, arma_y + 71, bw, 6), border_radius=3)
        if not arma.roto and prog_dur > 0:
            pygame.draw.rect(pantalla, col_dur, (x + 20, arma_y + 71, int(bw * prog_dur), 6), border_radius=3)

        if es_arco:
            # Carga actual: tramo completo alcanzado (alcance y % de daño) y barra hasta 5 s
            if arma.cargando and arma.tramo_carga >= 1:
                alcance, pct = arma.TRAMOS_CARGA[arma.tramo_carga]
                txt_carga = f"Carga {arma.tiempo_carga:.1f}s · {alcance} px · {pct * 100:.0f}%"
                col_carga = (130, 225, 255)
            elif arma.cargando:
                txt_carga = f"Carga {arma.tiempo_carga:.1f}s · sin disparo (<1s)"
                col_carga = (200, 170, 120)
            else:
                txt_carga = "Mantén [Espacio] para cargar"
                col_carga = (140, 150, 170)
            pantalla.blit(fuente_mini.render(txt_carga, True, col_carga), (x + 20, arma_y + 82))
            prog_carga = arma.tiempo_carga / arma.CARGA_MAX
            pygame.draw.rect(pantalla, (40, 45, 55), (x + 20, arma_y + 97, bw, 6), border_radius=3)
            if prog_carga > 0:
                pygame.draw.rect(pantalla, (120, 220, 255), (x + 20, arma_y + 97, int(bw * prog_carga), 6), border_radius=3)

            # Boton de compra de flechas (lote de 10). Gris si el carcaj esta lleno o falta energia
            puede_comprar = arma.flechas < arma.capacidad_carcaj and jugador.energia >= arma.costo_flechas
            rect_flechas = pygame.Rect(x + 20, arma_y + 108, bw, 20)
            pygame.draw.rect(pantalla, (34, 60, 78) if puede_comprar else (36, 40, 50), rect_flechas, border_radius=5)
            pygame.draw.rect(pantalla, (120, 210, 255) if puede_comprar else (70, 78, 92), rect_flechas, width=1, border_radius=5)
            txt_comprar = fuente_mini.render(f"[R] Comprar {arma.FLECHAS_POR_LOTE} flechas · {arma.costo_flechas} En.", True,
                                             (190, 235, 255) if puede_comprar else (120, 128, 140))
            pantalla.blit(txt_comprar, txt_comprar.get_rect(center=rect_flechas.center))
            botones["__flechas__"] = rect_flechas

    # Lista de Estadísticas
    offset_y = arma_y + arma_h + 12
    pct_vel = int(round((jugador.velocidad / jugador.velocidad_base - 1.0) * 100))
    str_pct = f" ({pct_vel:+d}%)" if pct_vel != 0 else ""

    # Cada stat: (etiqueta, valor, color, clave_mejora). clave None = no se puede subir.
    arma_cad = jugador.herramienta
    if arma_cad and arma_cad.cadencia > 0 and not arma_cad.roto:
        cad_txt = f"{arma_cad.cadencia_efectiva(jugador):.2f}/s"
    else:
        cad_txt = f"+{jugador.cadencia:.2f}/s"
    stats = [
        ("Tamaño (Nivel)", f"{jugador.tamano}", (200, 220, 255), None),
        ("Vida", f"{jugador.vida} / {jugador.vida_max}", (255, 95, 95), "vida"),
        ("Daño", f"{jugador.fuerza:.2f}", (255, 120, 60) if jugador.fuerza > jugador.fuerza_base else (220, 220, 220), "fuerza"),
        ("Velocidad", f"{jugador.velocidad:.2f}{str_pct}", (90, 220, 255) if pct_vel > 0 else ((255, 100, 70) if pct_vel < 0 else (220, 220, 220)), "velocidad"),
        ("Cadencia", cad_txt, (255, 200, 120) if jugador.cadencia > 0 else (220, 220, 220), "cadencia"),
        ("Energía", f"{jugador.energia} / {jugador.energia_max}", (180, 130, 255), "energia"),
        ("Escudo", f"{jugador.escudo:.1f} / {jugador.escudo_max:.0f}", (120, 255, 150), "escudo"),
        ("Escudo M.", f"ANULADO {jugador.anulacion_escudo_magico:.0f}s" if jugador.anulacion_escudo_magico > 0
                      else f"{jugador.escudo_magico:.1f} / {jugador.escudo_magico_max:.0f}",
         (220, 60, 60) if jugador.anulacion_escudo_magico > 0 else (90, 200, 255), "escudo_magico"),
        ("Regen En.", f"+{jugador.bono_regen_energia * 100:.0f}%" + (" (máx)" if jugador.regen_energia_al_tope else ""),
         (150, 210, 255), "regen_energia")
    ]

    puede_subir = jugador.puntos_mejora > 0

    for etiqueta, valor, color_val, clave in stats:
        txt_etiq = fuente_mini.render(f"{etiqueta}:", True, (160, 170, 190))
        pantalla.blit(txt_etiq, (x + 14, offset_y))

        if clave is not None and puede_subir:
            # Botón [+] a la derecha; el valor se corre a su izquierda
            bsize = 16
            rect_btn = pygame.Rect(x + ancho - 14 - bsize, offset_y - 1, bsize, bsize)
            pygame.draw.rect(pantalla, (34, 78, 44), rect_btn, border_radius=4)
            pygame.draw.rect(pantalla, (100, 230, 130), rect_btn, width=1, border_radius=4)
            signo = fuente_val.render("+", True, (150, 255, 180))
            pantalla.blit(signo, signo.get_rect(center=rect_btn.center))
            botones[clave] = rect_btn

            txt_val = fuente_val.render(str(valor), True, color_val)
            pantalla.blit(txt_val, (rect_btn.x - 6 - txt_val.get_width(), offset_y))
        else:
            txt_val = fuente_val.render(str(valor), True, color_val)
            pantalla.blit(txt_val, (x + ancho - 14 - txt_val.get_width(), offset_y))

        # Barra de progreso de Energía
        if etiqueta == "Energía":
            bw = ancho - 28
            bh = 6
            prog_en = max(0.0, min(1.0, jugador.energia / max(1, jugador.energia_max)))
            pygame.draw.rect(pantalla, (40, 35, 55), (x + 14, offset_y + 19, bw, bh), border_radius=3)
            pygame.draw.rect(pantalla, (180, 130, 255), (x + 14, offset_y + 19, int(bw * prog_en), bh), border_radius=3)
            offset_y += 10

        offset_y += 26

    # Boton para volver a la pantalla de seleccion (reprobar rapido)
    rect_menu = pygame.Rect(x + 12, alto - 100, ancho - 24, 24)
    pygame.draw.rect(pantalla, (40, 46, 60), rect_menu, border_radius=6)
    pygame.draw.rect(pantalla, (120, 160, 220), rect_menu, width=1, border_radius=6)
    txt_menu = fuente_sub.render("Volver a selección [M]", True, (180, 210, 255))
    pantalla.blit(txt_menu, txt_menu.get_rect(center=rect_menu.center))
    botones["__menu__"] = rect_menu

    # Pie de página con indicadores
    txt_lvl = fuente_mini.render("[Espacio] golpe · [I] inventario · [L] nivel", True, (150, 200, 255))
    pantalla.blit(txt_lvl, (x + 14, alto - 68))

    color_hb = (100, 255, 140) if mostrar_hitboxes else (120, 130, 150)
    txt_hb = fuente_mini.render(f"[H] Hitboxes: {'ACTIVAS' if mostrar_hitboxes else 'OCULTAS'}", True, color_hb)
    pantalla.blit(txt_hb, (x + 14, alto - 48))

    txt_salir = fuente_mini.render("[ESC] Salir del juego", True, (110, 120, 140))
    pantalla.blit(txt_salir, (x + 14, alto - 28))

    # Tooltip de estadísticas (al pulsar el icono '?' de la cabecera)
    if info_abierta == "stats":
        lineas_info = [
            "Vida: puntos de vida (se cura con orbes de frutales).",
            "Daño: fuerza del personaje; sube con [+] y con Burst de Fuerza. Es la base del golpe del arma.",
            "Velocidad: desplazamiento; cambia con agua, arma y Destello.",
            "Energía: coste de habilidades. Regenera +1 cada 3s parado, cada 6s en movimiento.",
            "Escudo: absorbe daño físico; se gasta y regenera tras 10s sin recibir golpes.",
            "Escudo M.: absorbe daño mágico (habilidades); se gasta y regenera igual.",
            f"Regen En.: acelera la regeneración de energía (+{REGEN_ENERGIA_POR_PUNTO * 100:.0f}%/punto, máx. +{REGEN_ENERGIA_TOPE * 100:.0f}%); x2 en agua, x4 en zona profunda.",
            "",
            "Clic derecho sobre un enemigo: Autoapuntado (lo miras siempre; -40% Vel;",
            "se suelta a más de 500, en terreno libre o sobre el mismo objetivo).",
            "",
            "Mejora con [+]: cuesta 1 punto (el arma cuesta 2).",
            f"[L] sube de nivel y otorga {PUNTOS_MEJORA_POR_NIVEL} puntos.",
        ]
        dibujar_tooltip(pantalla, x + ancho + 6, y + 40, "Estadísticas",
                        lineas_info, fuente_sub, fuente_mini)

    return botones


# -----------------------------
# EJECUCIÓN PRINCIPAL DEL MUNDO (PYGAME)
# -----------------------------
ITERACIONES_SEPARACION = 2   # pasadas por frame para resolver solapamientos entre cuerpos
# Cuerpo de niebla (Espectro): al terminar, busqueda del hueco libre mas cercano en anillos
PASO_BUSQUEDA_HUECO = 8      # px entre anillos de la busqueda
ALCANCE_BUSQUEDA_HUECO = 1500  # px maximos de busqueda (una roca gigante mide 150-300)


def rect_circulo_colisionan(rect, centro, radio):
    """Colision entre un rectangulo (hitbox del arma) y un circulo (enemigo)."""
    cx = max(rect.left, min(centro.x, rect.right))
    cy = max(rect.top, min(centro.y, rect.bottom))
    dx = centro.x - cx
    dy = centro.y - cy
    return (dx * dx + dy * dy) <= radio * radio


def punto_libre(punto, radio, rocas, circulares, cuerpos, limite=LIMITE):
    """True si un circulo en 'punto' no toca rocas, obstaculos circulares (centro, radio),
    cuerpos solidos ni sale del mapa."""
    if not limite.dentro(punto, radio):
        return False
    if any(rect_circulo_colisionan(r.rect, punto, radio) for r in rocas):
        return False
    if any((punto - c).length() < r + radio for c, r in circulares):
        return False
    return not any((punto - c.posicion).length() < c.radio + radio for c in cuerpos)


def sacar_a_hueco_libre(entidad, rocas, circulares, cuerpos, limite=LIMITE):
    """Cuerpo de niebla al terminar: si la entidad quedo dentro de algo, la mueve al punto libre
    mas cercano (anillos cada PASO_BUSQUEDA_HUECO px). Devuelve True si la movio."""
    radio = entidad.radio
    origen = pygame.Vector2(entidad.posicion)
    alcance = ALCANCE_BUSQUEDA_HUECO + radio
    zona = pygame.Rect(0, 0, alcance * 2, alcance * 2)
    zona.center = (round(origen.x), round(origen.y))
    rocas = [r for r in rocas if zona.colliderect(r.rect)]
    circulares = [(c, r) for c, r in circulares if (c - origen).length() <= alcance + r]
    cuerpos = [c for c in cuerpos if c is not entidad and (c.posicion - origen).length() <= alcance + c.radio]
    libre = lambda p: punto_libre(p, radio, rocas, circulares, cuerpos, limite)
    if libre(origen):
        return False
    for d in range(PASO_BUSQUEDA_HUECO, ALCANCE_BUSQUEDA_HUECO + 1, PASO_BUSQUEDA_HUECO):
        pasos = max(8, int(math.tau * d / PASO_BUSQUEDA_HUECO))
        for k in range(pasos):
            ang = math.tau * k / pasos
            p = origen + pygame.Vector2(math.cos(ang), math.sin(ang)) * d
            if libre(p):
                entidad.posicion = p
                entidad.destino = p.copy()
                entidad.empuje.update(0, 0)
                return True
    return False


def hitboxes_de_armas_chocan(arma_a, arma_b):
    """True si alguna hitbox del arma A toca alguna del arma B (choque de filos)."""
    rects_b = [h for h in arma_b.obtener_hitboxes() if h]
    if not rects_b:
        return False
    for ha in arma_a.obtener_hitboxes():
        if ha and ha.collidelist(rects_b) != -1:
            return True
    return False


COLOR_MIRA = (255, 60, 60)

# Experiencia y muerte del jugador
COLOR_XP = (120, 200, 255)
COLOR_XP_MAX = (255, 215, 120)
COLOR_MONEDAS = (245, 200, 70)
DURACION_TEXTO_FLOTANTE = 1.4      # s que dura un "+2 XP" / "NIVEL 5" sobre el personaje
SUBIDA_TEXTO_FLOTANTE = 40         # px que sube en ese tiempo
ALFA_PANTALLA_MUERTE = 170
DURACION_AVISO_TOTEM = 3.5         # s que se ve "El Tótem de vida te salvó"
COLOR_TOTEM_AVISO = (120, 240, 150)
MONEDAS_PRUEBA = 100               # [K] (prueba): monedas para probar el Gacha
PROB_DEBUG_TOTEM = 0.2             # [T] (prueba): probabilidad de dar un tótem en vez de un anillo
PUNTOS_PRUEBA_SHADOW = 999         # shadow498: puntos de mejora extra para editar las stats con el panel ([L] o botones +)


# Parpadeo rojo al perder vida (cualquier ser vivo: jugador, maniqui, fauna y sombras)
PARPADEO_DURACION = 0.3        # s que dura el parpadeo tras perder vida
PARPADEO_PERIODO = 0.075       # s de cada fase encendido/apagado (2 destellos)
PARPADEO_ALFA = 170            # opacidad maxima del rojo
PARPADEO_COLOR = (255, 40, 40)
_cache_parpadeo = {}


def actualizar_parpadeos(entidades, dt):
    """Detecta quien perdio vida desde el cuadro anterior (golpes, efectos, terreno...) y
    arranca su parpadeo. Guarda en cada entidad su vida previa y el tiempo de parpadeo."""
    for e in entidades:
        vida = getattr(e, "vida", None)
        if vida is None:
            continue
        previa = getattr(e, "_vida_parpadeo", None)
        if previa is not None and vida < previa:
            e._t_parpadeo = PARPADEO_DURACION
        elif getattr(e, "_t_parpadeo", 0.0) > 0:
            e._t_parpadeo = max(0.0, e._t_parpadeo - dt)
        e._vida_parpadeo = vida


def _visible_para_parpadeo(e):
    if getattr(e, "vivo", True) is False:
        return False
    return not (getattr(e, "invisible", False) or getattr(e, "en_cueva", False)
                or getattr(e, "sumergido", False) or getattr(e, "estado", "") == "escondido")


def dibujar_parpadeos(pantalla, entidades, desplazamiento):
    """Tinte rojo sobre el cuerpo mientras dura el parpadeo: dos destellos que se apagan."""
    for e in entidades:
        t = getattr(e, "_t_parpadeo", 0.0)
        if t <= 0 or not _visible_para_parpadeo(e):
            continue
        transcurrido = PARPADEO_DURACION - t
        if int(transcurrido / PARPADEO_PERIODO) % 2:
            continue                                   # fase apagada
        radio = max(4, int(getattr(e, "radio", 12)))
        alfa = int(PARPADEO_ALFA * t / PARPADEO_DURACION)
        clave = (radio, alfa // 10)
        sup = _cache_parpadeo.get(clave)
        if sup is None:
            sup = pygame.Surface((radio * 2 + 2, radio * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(sup, (*PARPADEO_COLOR, (alfa // 10) * 10), (radio + 1, radio + 1), radio)
            _cache_parpadeo[clave] = sup
        pantalla.blit(sup, (round(e.posicion.x - desplazamiento[0]) - radio - 1,
                            round(e.posicion.y - desplazamiento[1]) - radio - 1))


def dibujar_mira(pantalla, objetivo, desplazamiento):
    """Mira roja del Autoapuntado sobre el objetivo: anillo con cuatro marcas."""
    cx = round(objetivo.posicion.x - desplazamiento[0])
    cy = round(objetivo.posicion.y - desplazamiento[1])
    r = objetivo.radio + 10
    pygame.draw.circle(pantalla, COLOR_MIRA, (cx, cy), r, 2)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pygame.draw.line(pantalla, COLOR_MIRA, (cx + dx * (r - 5), cy + dy * (r - 5)),
                         (cx + dx * (r + 6), cy + dy * (r + 6)), 2)


def resolver_solapamientos(entidades):
    """Separa los cuerpos circulares que se solapan (jugador, invocaciones, maniqui) para que
    no queden uno encima de otro. Cada uno necesita `posicion`, `radio` y `masa`: el de menos
    masa cede mas (masa infinita = no se mueve). Si dos cuerpos coinciden exactamente se
    separan en una direccion aleatoria."""
    for _ in range(ITERACIONES_SEPARACION):
        for i in range(len(entidades)):
            a = entidades[i]
            for j in range(i + 1, len(entidades)):
                b = entidades[j]
                minima = a.radio + b.radio
                delta = b.posicion - a.posicion
                dist2 = delta.length_squared()
                if dist2 >= minima * minima:
                    continue
                ma, mb = a.masa, b.masa
                if math.isinf(ma) and math.isinf(mb):
                    continue
                if dist2 == 0:
                    ang = random.uniform(0, math.tau)
                    normal = pygame.Vector2(math.cos(ang), math.sin(ang))
                    solape = minima
                else:
                    dist = math.sqrt(dist2)
                    normal = delta / dist
                    solape = minima - dist
                # Parte del solape que cede cada uno (proporcional a la masa del otro)
                if math.isinf(ma):
                    parte_a, parte_b = 0.0, 1.0
                elif math.isinf(mb):
                    parte_a, parte_b = 1.0, 0.0
                else:
                    parte_a, parte_b = mb / (ma + mb), ma / (ma + mb)
                a.posicion -= normal * (solape * parte_a)
                b.posicion += normal * (solape * parte_b)


# -----------------------------
# COMBATIENTES (Fase 1 del plan de NPC)
# -----------------------------
# Todo personaje que pelea (el jugador y, mas adelante, los NPC) pasa por las mismas funciones:
# combatiente_golpes -> combatiente_habilidades -> combatiente_estado. El jugador las llama desde
# el bucle de iniciar_mundo en el orden de siempre (entre medias van pasos solo del mundo); los
# demas combatientes las llaman seguidas en actualizar_combatiente. Las ordenes llegan como
# "intenciones" del Personaje (mover_a, pulsar_ataque, pulsar_habilidad...): el jugador las genera
# con el teclado y el raton; un bot las generara con su inteligencia (Fase 4).
VISTA_COMBATIENTE = (1800, 1200)    # px alrededor de un combatiente no jugador en los que ve enemigos


class Contexto:
    """Lo que comparten todos los combatientes del mundo (antes, variables sueltas del bucle)."""

    def __init__(self, rocas, vegetacion, charcos, fauna, limites_mundo):
        self.rocas = rocas
        self.vegetacion = vegetacion
        self.charcos = charcos
        self.fauna = fauna
        self.limites_mundo = limites_mundo
        self.combatientes = []          # personajes que no son el jugador (NPC)

    def agregar_combatiente(self, personaje):
        personaje.es_combatiente = True
        self.combatientes.append(personaje)
        return personaje


def vista_de(c):
    """Rectangulo del mundo que 've' un combatiente (para buscar a sus enemigos)."""
    ancho, alto = VISTA_COMBATIENTE
    return pygame.Rect(round(c.posicion.x - ancho / 2), round(c.posicion.y - alto / 2), ancho, alto)


def enemigos_de(c, ctx, jugador):
    """Objetivos de un combatiente que no es el jugador: el jugador, los demas combatientes y los
    animales que tiene cerca. (Las facciones y el odio entre razas llegan en la Fase 5.)"""
    rivales = ([jugador] if jugador is not c and jugador.vida > 0 else []) + [o for o in ctx.combatientes if o is not c and o.vida > 0]
    return rivales + ctx.fauna.animales_con_vida(vista_de(c))


def golpear_personaje(atacante, obj, dano, arma):
    """Golpe de arma a un personaje (jugador o NPC), con las mismas reglas que el golpe del maniqui:
    invulnerable tras otro golpe, el Escudo desenfundado lo bloquea (repele al atacante y desgasta
    su arma) y marca al agresor para que sus sombras de anillo lo defiendan."""
    if obj.invulnerable:
        return
    TL.marcar_agresor(obj, atacante)
    if dano > 0 and obj.bloquear_con_escudo(dano, atacante.posicion):
        if hasattr(atacante, "aplicar_empuje"):
            atacante.aplicar_empuje(atacante.posicion - obj.posicion, obj.herramienta.puntos_empuje)
        arma.desgastar(1)
        return
    if dano > 0:
        atacante.golpear_con_arma(obj, dano, arma.tipo_dano)
        obj.aplicar_empuje(obj.posicion - atacante.posicion, arma.puntos_empuje)
        obj.marcar_golpe()
        arma.desgastar(1)


def combatiente_golpes(c, dt, enemigos):
    """Arma del combatiente: su animacion, el ataque mantenido y el golpe (choque de armas con
    prioridad o golpe al cuerpo del enemigo)."""
    if c.herramienta:
        c.herramienta.actualizar(dt, c)
    # Mantener el ataque repite el golpe segun la cadencia del arma
    if c.mantiene_ataque and c.herramienta and not c.controlado:
        c.herramienta.atacar(c)
    arma_actual = c.herramienta
    if not (arma_actual and getattr(arma_actual, "golpeando", False)):
        return
    for enemigo in enemigos:
        if id(enemigo) in arma_actual.enemigos_golpeados:
            continue
        arma_enemiga = getattr(enemigo, "herramienta", None)
        # 1) Choque de armas: mi filo toca su espada -> repelido mutuo igual + ambas se desgastan
        if (arma_enemiga and not arma_enemiga.roto
                and hitboxes_de_armas_chocan(arma_actual, arma_enemiga)):
            arma_actual.enemigos_golpeados.add(id(enemigo))
            fuerza_choque = max(arma_actual.puntos_empuje, arma_enemiga.puntos_empuje)
            dir_al_enemigo = enemigo.posicion - c.posicion
            c.aplicar_empuje(-dir_al_enemigo, fuerza_choque)                # yo retrocedo
            if hasattr(enemigo, "aplicar_empuje"):
                enemigo.aplicar_empuje(dir_al_enemigo, fuerza_choque)       # el enemigo retrocede igual
            arma_actual.desgastar(1)
            arma_enemiga.desgastar(1)
            continue
        # 2) Golpe al cuerpo del enemigo
        tocado = any(
            hb and rect_circulo_colisionan(hb, enemigo.posicion, enemigo.radio)
            for hb in arma_actual.obtener_hitboxes()
        )
        if not tocado:
            continue
        arma_actual.enemigos_golpeados.add(id(enemigo))
        dano = arma_actual.calcular_dano(c)
        if c.corrosion is not None:
            dano = round(dano * factor_dano_corrosion(c), 2)    # corroido: pega menos
        if isinstance(enemigo, Personaje):
            golpear_personaje(c, enemigo, dano, arma_actual)
        elif dano > 0 and hasattr(enemigo, "recibir_dano"):
            c.golpear_con_arma(enemigo, dano, arma_actual.tipo_dano)
            if hasattr(enemigo, "aturdir_ataque"):
                enemigo.aturdir_ataque()     # retrasa su siguiente ataque (animales)
            if hasattr(enemigo, "aplicar_empuje"):
                enemigo.aplicar_empuje(enemigo.posicion - c.posicion, arma_actual.puntos_empuje)
            arma_actual.desgastar(1)


def combatiente_habilidades(c, ctx, dt, enemigos):
    """Proyectiles, regeneracion, habilidades (equipadas y guardadas), sombras de los anillos,
    cuchillas, explosiones y combustible del combatiente."""
    # Proyectiles (Disparo Veloz, Carga de Fuego, Disparo Venenoso, flechas): chocan con las rocas
    c.actualizar_proyectiles(dt, ctx.limites_mundo, ctx.rocas)
    # Los proyectiles desaparecen al salir del mapa
    c.proyectiles = [p for p in c.proyectiles if LIMITE.dentro(p.posicion, -p.radio)]
    for p in c.proyectiles:
        if not p.activo or getattr(p, "clavada", False):
            continue
        for enemigo in enemigos:
            if not getattr(enemigo, "vivo", True):
                continue
            if rect_circulo_colisionan(p.hitbox, enemigo.posicion, enemigo.radio):
                if hasattr(p, "puntos_empuje"):
                    # Flecha: daño fisico, empuje fijo del arma y desgaste del arco si hace daño
                    aplicado = c.golpear_con_arma(enemigo, p.dano, p.tipo_dano)
                    enemigo.aplicar_empuje(p.direccion, p.puntos_empuje)
                    if aplicado > 0:
                        p.arco.desgastar(1)
                elif hasattr(enemigo, "recibir_dano"):
                    enemigo.recibir_dano(p.dano, getattr(p, "tipo_dano", "magico"),
                                         enemigo.posicion - p.posicion)
                if hasattr(p, "quemadura_dano") and hasattr(enemigo, "quemadura"):
                    aplicar_quemadura(enemigo, p.quemadura_dano, p.quemadura_duracion)
                    encender_combustible(enemigo, p.dano)   # combustible pegado: +50 % por carga
                if hasattr(p, "veneno_total") and hasattr(enemigo, "veneno"):
                    aplicar_veneno(enemigo, p.veneno_total, p.veneno_duracion)
                    if p.corrosion_tope is not None:
                        aplicar_corrosion(enemigo, p.corrosion_tope, p.veneno_duracion, impacto=True)
                if hasattr(p, "impactar"):
                    p.impactar()            # Estrella Ignea: explota 0.5 s despues
                p.activo = False
                break
    c.proyectiles = [p for p in c.proyectiles if p.activo]

    # Regeneración de energía y de los escudos físico y mágico
    c.actualizar_regeneracion(dt)
    c.actualizar_regeneracion_escudo(dt)
    c.actualizar_regeneracion_escudo_magico(dt)

    # Habilidades equipadas; las guardadas en la colección siguen su recarga
    for hab in c.habilidades:
        hab.actualizar(dt, c)
    for hab in c.habilidades_guardadas():
        hab.actualizar(dt, c)
    # Sombras de los anillos (lo siguen y lo defienden)
    c.sombras_anillo.actualizar(dt, c)

    # Cuchillas de Cortar: golpean al primer enemigo o destruyen una roca/arbusto
    for hab in c.habilidades:
        if hasattr(hab, "actualizar_cuchillas"):
            destruidas = hab.actualizar_cuchillas(ctx.rocas, ctx.vegetacion.arbustos, ctx.vegetacion.arboles,
                                                  enemigos, LIMITE)
            ctx.vegetacion.liberar_obstaculos(destruidas)
    # Estrella Ignea: choques con troncos/arbustos, explosiones y suelo en llamas
    for hab in c.habilidades:
        if hasattr(hab, "actualizar_explosiones"):
            destruidas, evaporado = hab.actualizar_explosiones(dt, c, enemigos, ctx.rocas, ctx.vegetacion.arbustos,
                                                               ctx.vegetacion.arboles, ctx.charcos)
            ctx.vegetacion.liberar_obstaculos(destruidas)
            for centro_ev, radio_ev in evaporado:
                ctx.fauna.quitar_fauna_acuatica(centro_ev, radio_ev)

    # Combustible de Desmantelar: suelto, pegado a enemigos, explosiones y suelo en llamas
    c.combustible.actualizar(dt, c, enemigos, ctx.charcos)


def combatiente_estado(c, ctx, dt, enemigos, enemigos_sin_tumba):
    """Ondas, auras y telarañas del combatiente, sus efectos y estados, el terreno (agua y zona
    profunda), el autoapuntado y el movimiento con empuje."""
    # Ondas Sonoras: anillos que golpean una vez a cada enemigo (atraviesan obstaculos)
    for hab in c.habilidades:
        if hasattr(hab, "actualizar_ondas"):
            hab.actualizar_ondas(dt, enemigos)
    # Auras (Aura Electrica, Relampago, humo de Corrosion), tambien las otorgadas
    for hab in c.habilidades_en_efecto():
        if hasattr(hab, "actualizar_dano_enemigos"):
            hab.actualizar_dano_enemigos(dt, enemigos_sin_tumba, c)
    # Sombra Araña: las telaranas atrapan a los enemigos que las pisan
    for hab in c.habilidades:
        if hasattr(hab, "actualizar_telaranas"):
            hab.actualizar_telaranas(dt, enemigos_sin_tumba)
    # Efectos temporales otorgados (ej. por Golpe de Suerte), desangrado, invulnerabilidad,
    # veneno, ralentizacion, fundido de Paso 0 y anillo de regeneracion
    c.actualizar_efectos(dt)
    c.actualizar_desangrado(dt)
    c.actualizar_invulnerabilidad(dt)
    c.actualizar_reloj(dt)
    c.actualizar_veneno(dt)
    c.actualizar_ralentizacion(dt)
    c.actualizar_desvanecimiento(dt)
    c.actualizar_talismanes(dt)
    # Estados puestos por otros combatientes (quemadura, corrosion, sueno, huida, telarana)
    c.actualizar_estados(dt)

    # Terreno: ¿pisa agua? ¿zona profunda de un lago grande? (10 de daño por segundo)
    c.en_agua = any(ch.contiene(c.posicion) for ch in ctx.charcos)
    c.en_agua_profunda = any(ch.en_zona_peligro(c.posicion) for ch in ctx.charcos)
    if c.en_agua_profunda:
        c.tiempo_dano_lago += dt
        while c.tiempo_dano_lago >= 1.0:
            c.tiempo_dano_lago -= 1.0
            c.vida = max(0, c.vida - DANO_LAGO_PROFUNDO)
    else:
        c.tiempo_dano_lago = 0.0

    # Autoapuntado: mira al objetivo (o lo suelta si muere o sale de rango) antes de moverse
    c.actualizar_autoapuntado(dt)
    # Velocidad acumulando debuffs y buffs
    c.actualizar_velocidad()
    # Mover respetando el cuadrado del mapa y las rocas. Con Cuerpo de niebla (Espectro) solo lo
    # frenan las cuevas de oso y los arbustos en los que no cabe.
    if c.inspector:                             # ShadowGOD: lo atraviesa todo
        c.mover(ctx.limites_mundo, LIMITE, [], [])
    elif c.cuerpo_de_niebla:
        c.mover(ctx.limites_mundo, LIMITE,
                [r for r in ctx.rocas if getattr(r, "es_cueva", False)],
                ctx.vegetacion.obstaculos_para(c, con_troncos=False))
    else:
        c.mover(ctx.limites_mundo, LIMITE, ctx.rocas, ctx.vegetacion.obstaculos_para(c))
    # Retroceso acumulado por empuje
    c.actualizar_empuje(dt, LIMITE)
    if c.inspector:
        c.vida = c.vida_max                     # ShadowGOD no pierde vida (lagos, hierba, quemadura...)


def salud_de(objetivos):
    """Vida de cada objetivo que no es un personaje (animales, vendedores...) antes de un turno."""
    return [(o, o.vida) for o in objetivos if not isinstance(o, Personaje)]


def marcar_autor(salud_antes, de_npc):
    """Quien hirio por ultima vez a cada objetivo: si lo remata un NPC (o sus efectos y sombras
    despues de su golpe), la XP y las monedas no son para el jugador (respuesta del 27/11)."""
    for o, vida in salud_antes:
        if o.vida < vida:
            o.ultimo_golpe_npc = de_npc


def actualizar_combatiente(c, ctx, dt, jugador):
    """Un fotograma completo de un combatiente que no es el jugador (sus intenciones ya puestas)."""
    enemigos = enemigos_de(c, ctx, jugador)
    antes = salud_de(enemigos)
    combatiente_golpes(c, dt, enemigos)
    combatiente_habilidades(c, ctx, dt, enemigos)
    combatiente_estado(c, ctx, dt, enemigos, enemigos)
    ctx.vegetacion.actualizar_personaje(dt, c)
    marcar_autor(antes, True)


def retirar_combatientes_muertos(ctx):
    """Quita del mundo a los combatientes sin vida (y a sus sombras). Devuelve los retirados."""
    muertos = [c for c in ctx.combatientes if c.vida <= 0]
    for c in muertos:
        sombras = []
        for hab in c.coleccion_habilidades + [c.sombras_anillo]:
            for cr in getattr(hab, "criaturas", ()):
                cr.vivo = False
                sombras.append(cr)
        ctx.fauna.olvidar_objetivos([c] + sombras)
        ctx.combatientes.remove(c)
    return muertos


def cuerpos_de_combatiente(c):
    """Cuerpos solidos de un combatiente: el suyo (salvo con Cuerpo de niebla) y sus sombras."""
    cuerpos = [] if c.cuerpo_de_niebla or c.inspector else [c]
    for hab in c.fuentes_criaturas():
        cuerpos.extend(getattr(hab, "criaturas", ()))
    return cuerpos


# -----------------------------
# SHADOWGOD (personaje de inspeccion del mapa, Fase 2 del plan de NPC)
# -----------------------------
NIVELES_ZOOM = (1.0, 0.8, 0.6, 0.4, 0.25, 0.15, 0.1, 0.06)   # 0.06: el mapa entero en pantalla
ZOOM_LIENZO_MIN = 0.4         # hasta aqui se dibuja el mundo real; mas lejos, el mapa (imagen fija)
ESCALA_MAPA_LEJANO = 0.1      # resolucion de la imagen del mapa entero (1770 px)
TECLAS_ACERCAR = (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS)
TECLAS_ALEJAR = (pygame.K_MINUS, pygame.K_KP_MINUS)
COLOR_BOTON_INSPECTOR = (40, 44, 56)
COLOR_BORDE_INSPECTOR = (150, 120, 230)
CUADROS_REFERENCIA = 10       # misma cuadricula A-J / 1-10 que la vista previa del mapa


def dibujar_mapa_lejano(pantalla, area, imagen, vista, z):
    """Vista lejana de ShadowGOD: el trozo visible de la imagen del mapa entero, escalado."""
    e = ESCALA_MAPA_LEJANO
    origen = pygame.Vector2(LIMITE.rect.topleft)
    fuente = pygame.Rect(round((vista.x - origen.x) * e), round((vista.y - origen.y) * e),
                         max(1, round(vista.width * e)), max(1, round(vista.height * e)))
    recorte = fuente.clip(imagen.get_rect())
    if recorte.width <= 0 or recorte.height <= 0:
        return
    destino = pygame.Rect(area.x + round((recorte.x - fuente.x) * z / e), area.y + round((recorte.y - fuente.y) * z / e),
                          max(1, round(recorte.width * z / e)), max(1, round(recorte.height * z / e)))
    pantalla.blit(pygame.transform.scale(imagen.subsurface(recorte), destino.size), destino.topleft)
    pygame.draw.rect(pantalla, COLOR_BORDE_MAPA, pygame.Rect(
        area.x + round((LIMITE.rect.x - vista.x) * z), area.y + round((LIMITE.rect.y - vista.y) * z),
        round(LIMITE.lado * z), round(LIMITE.lado * z)), 2)


def dibujar_capas(pantalla, area, datos_mapa, rocas, vista, z, fuente):
    """Capas del mapa (ShadowGOD, tecla [V] o boton): cuadricula de referencia, zonas con nombre,
    puntos de aparicion por raza y cuevas de oso."""
    import mapa as MAPA
    a_pantalla = lambda p: (round(area.x + (p[0] - vista.x) * z), round(area.y + (p[1] - vista.y) * z))
    paso = LIMITE.lado / CUADROS_REFERENCIA
    for k in range(CUADROS_REFERENCIA + 1):
        x = LIMITE.rect.x + k * paso
        y = LIMITE.rect.y + k * paso
        pygame.draw.line(pantalla, (235, 235, 235), a_pantalla((x, LIMITE.rect.top)), a_pantalla((x, LIMITE.rect.bottom)), 1)
        pygame.draw.line(pantalla, (235, 235, 235), a_pantalla((LIMITE.rect.left, y)), a_pantalla((LIMITE.rect.right, y)), 1)
    for k in range(CUADROS_REFERENCIA):
        for i in range(CUADROS_REFERENCIA):
            centro = a_pantalla((LIMITE.rect.x + (i + 0.08) * paso, LIMITE.rect.y + (k + 0.08) * paso))
            if area.collidepoint(centro):
                txt = fuente.render("%s%d" % ("ABCDEFGHIJ"[i], k + 1), True, (240, 240, 240))
                pantalla.blit(txt, centro)
    for z_ in datos_mapa.get("zonas", []):
        color = MAPA.COLORES_RAZA.get(z_["nombre"], (255, 255, 255))
        c = a_pantalla((z_["x"], z_["y"]))
        pygame.draw.circle(pantalla, color, c, max(3, round(z_["radio"] * z)), 2)
        txt = fuente.render(z_["nombre"], True, color)
        pantalla.blit(txt, txt.get_rect(center=c))
    for raza, puntos in datos_mapa.get("aparicion", {}).items():
        color = MAPA.COLORES_RAZA.get(raza, (255, 255, 255))
        for p in puntos:
            pygame.draw.circle(pantalla, (0, 0, 0), a_pantalla(p), 7)
            pygame.draw.circle(pantalla, color, a_pantalla(p), 5)
    for r in rocas:
        if hasattr(r, "angulo_entrada"):        # cuevas de oso (las paredes de la casa no)
            pygame.draw.circle(pantalla, (255, 255, 255), a_pantalla(r.rect.center), max(6, round(r.rect.width * z)), 2)


def dibujar_botones_inspector(pantalla, area, zoom, capas, fuente):
    """Botones de ShadowGOD arriba a la derecha del mundo: acercar, alejar y capas."""
    botones = {}
    x = area.right - 12
    for clave, texto in (("__capas__", "Capas [V]" + (" *" if capas else "")),
                         ("__zoom_menos__", "-"), ("__zoom_mas__", "+")):
        sup = fuente.render(texto, True, (235, 235, 245))
        rect = pygame.Rect(0, 0, max(34, sup.get_width() + 16), 30)
        rect.topright = (x, area.y + 12)
        pygame.draw.rect(pantalla, COLOR_BOTON_INSPECTOR, rect, border_radius=6)
        pygame.draw.rect(pantalla, COLOR_BORDE_INSPECTOR, rect, 2, border_radius=6)
        pantalla.blit(sup, sup.get_rect(center=rect.center))
        botones[clave] = rect
        x = rect.left - 8
    txt = fuente.render("ShadowGOD  zoom x%.2f  (rueda, + / -)" % zoom, True, COLOR_BORDE_INSPECTOR)
    pantalla.blit(txt, (x - txt.get_width() - 8, area.y + 18))
    return botones


class Maniqui:
    """Maniqui de pruebas en el centro del mapa: 100 de vida y escudos fisico y magico de 50,
    lleva una Espada Larga y ataca en intervalos (IA simple); recibe dano y desangrado. Los escudos siguen las mismas reglas que los del
    personaje (reparto, regeneracion tras 10 s sin dano y anulacion del escudo magico por
    Cortar). Al destruirse reaparece a los 5 s con vida y escudos llenos. Es un cuerpo fijo:
    nada lo atraviesa ni lo desplaza (solo su propio retroceso al recibir dano)."""
    VIDA_MAX = 100
    ESCUDO_MAX = 50
    ESCUDO_MAGICO_MAX = 50
    RESPAWN = 5.0
    masa = float("inf")

    def __init__(self, centro):
        self.posicion = pygame.Vector2(centro)
        self.ancla = pygame.Vector2(centro)      # vuelve aqui tras el retroceso
        self.vida_max = self.VIDA_MAX
        self.escudo_max = float(self.ESCUDO_MAX)
        self.escudo_magico_max = float(self.ESCUDO_MAGICO_MAX)
        self.radio = 18
        self.empuje = pygame.Vector2(0, 0)
        # Combate del maniqui (IA simple con espada)
        self.angulo = 0.0
        self.fuerza = 2.0
        self.RANGO_ATAQUE = 150
        self.INTERVALO_ATAQUE = 2.0
        self._reiniciar()

    def _reiniciar(self):
        """Vida y escudos llenos, sin efectos (al crearse y al reaparecer)."""
        self.vida = self.vida_max
        self.escudo = self.escudo_max
        self.escudo_magico = self.escudo_magico_max
        self.tiempo_sin_dano_escudo = 0.0
        self.tiempo_sin_dano_escudo_magico = 0.0
        self.anulacion_escudo_magico = 0.0
        self.escudo_magico_guardado = 0.0
        self.vivo = True
        self.desangrado = None
        self.veneno = None
        self.corrosion = None
        self.ralentizacion = 0.0          # no se mueve, pero la muestra (Onda Sonora)
        self.tiempo_ralentizacion = 0.0
        self.en_agua = False
        self.empuje.update(0, 0)
        self._t_respawn = 0.0
        self.tiempo_desde_ataque = 0.0
        self.herramienta = EspadaLarga()
        self.herramienta.activa = True
        self.quemadura = None
        self.inmovilizado = None
        self.dormido = None               # Palabras Malditas: Duerme
        self.huida = None                 # Palabras Malditas: Huye (no se mueve: solo deja de atacar)

    @property
    def controlado(self):
        """Paralizado, dormido o asustado: no ataca (igual que la fauna)."""
        return self.inmovilizado is not None or self.dormido is not None or self.huida is not None

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        """Reparte el dano entre su escudo y la vida (mismas reglas que el personaje).
        Devuelve el dano aplicado."""
        d = max(0.0, float(cantidad))
        if d <= 0 or not self.vivo:
            return 0.0
        magico = tipo_dano == "magico"
        absorbido, dano_vida = repartir_dano(d, tipo_dano, self.escudo_magico if magico else self.escudo)
        if magico:
            self.escudo_magico = max(0.0, round(self.escudo_magico - absorbido, 2))
            self.tiempo_sin_dano_escudo_magico = 0.0
        else:
            self.escudo = max(0.0, round(self.escudo - absorbido, 2))
            self.tiempo_sin_dano_escudo = 0.0
        self.vida = max(0.0, round(self.vida - dano_vida, 2))
        total = round(absorbido + dano_vida, 2)
        if direccion_empuje is not None:
            self.aplicar_empuje(direccion_empuje, total)
        if self.vida <= 0:
            self.vivo = False
            self._t_respawn = self.RESPAWN
        return total

    def _regenerar_escudos(self, dt):
        """Tras REGEN_ESCUDO_RETRASO s sin dano, +REGEN_ESCUDO_POR_SEGUNDO por segundo.
        El escudo magico no se regenera mientras esta anulado."""
        if self.escudo < self.escudo_max:
            self.tiempo_sin_dano_escudo += dt
            if self.tiempo_sin_dano_escudo >= REGEN_ESCUDO_RETRASO:
                self.escudo = min(self.escudo_max, round(self.escudo + REGEN_ESCUDO_POR_SEGUNDO * dt, 2))
        if actualizar_anulacion_escudo_magico(self, dt):
            return
        if self.escudo_magico < self.escudo_magico_max:
            self.tiempo_sin_dano_escudo_magico += dt
            if self.tiempo_sin_dano_escudo_magico >= REGEN_ESCUDO_RETRASO:
                self.escudo_magico = min(self.escudo_magico_max, round(self.escudo_magico + REGEN_ESCUDO_POR_SEGUNDO * dt, 2))

    def aplicar_empuje(self, direccion, puntos):
        """Retroceso al recibir dano; luego regresa a su ancla (ver actualizar)."""
        if puntos <= 0:
            return
        dirv = pygame.Vector2(direccion)
        if dirv.length_squared() == 0:
            return
        self.empuje += dirv.normalize() * (puntos * PIXELES_POR_PUNTO_EMPUJE)

    def curar(self, cantidad):
        return 0.0  # el maniqui no se cura

    def actualizar(self, dt, jugador=None):
        if not self.vivo:
            self._t_respawn -= dt
            if self._t_respawn <= 0:
                self._reiniciar()
                self.posicion.update(self.ancla)   # reaparece centrado
            return
        self._regenerar_escudos(dt)
        actualizar_ralentizacion(self, dt)
        # IA simple: mirar al jugador y lanzar golpes en intervalos. No detecta al jugador
        # oculto en un arbusto ni invisible (Paso 0); un golpe ya en marcha sigue su curso.
        if jugador is not None and getattr(jugador, "detectable", True) and not self.controlado:
            hacia = jugador.posicion - self.posicion
            if hacia.length_squared() > 0:
                self.angulo = math.degrees(math.atan2(hacia.x, -hacia.y)) % 360.0
            self.tiempo_desde_ataque += dt
            if (hacia.length() <= self.RANGO_ATAQUE + jugador.radio
                    and self.tiempo_desde_ataque >= self.INTERVALO_ATAQUE):
                if self.herramienta.atacar(self):
                    self.tiempo_desde_ataque = 0.0
        self.herramienta.actualizar(dt, self)
        if self.desangrado is not None:
            self.desangrado.actualizar(dt, self)
            if not self.desangrado.activo:
                self.desangrado = None
            if self.vida <= 0:
                self.vivo = False
                self._t_respawn = self.RESPAWN
        if self.quemadura is not None:
            self.quemadura.actualizar(dt, self)
            if not self.quemadura.activo:
                self.quemadura = None
            if self.vida <= 0:
                self.vivo = False
                self._t_respawn = self.RESPAWN
        if self.veneno is not None:
            self.veneno.actualizar(dt, self)     # recibir_dano ya gestiona la muerte
            if not self.veneno.activo:
                self.veneno = None
        if self.corrosion is not None:
            self.corrosion.actualizar(dt, self)
            if not self.corrosion.activo:
                self.corrosion = None
        if self.huida is not None:
            self.huida.actualizar(dt, self, mover=False)
            if not self.huida.activo:
                self.huida = None
        if self.dormido is not None:
            self.dormido.actualizar(dt, self)
            if not self.dormido.activo:
                self.dormido = None
        if self.inmovilizado is not None:
            self.inmovilizado.actualizar(dt, self)
            if not self.inmovilizado.activo:
                self.inmovilizado = None
            if self.vida <= 0:
                self.vivo = False
                self._t_respawn = self.RESPAWN
        # Movimiento (retroceso + regreso a ancla): bloqueado mientras esta inmovilizado
        if self.inmovilizado is None:
            if self.empuje.length_squared() >= 0.25:
                paso = self.empuje * min(1.0, dt * 14.0)
                self.posicion += paso
                self.empuje -= paso
            hacia_ancla = self.ancla - self.posicion
            if hacia_ancla.length() > 0.5:
                self.posicion += hacia_ancla * min(1.0, dt * 3.0)

    def dibujar(self, pantalla, desplazamiento=(0, 0), fuente=None):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        r = self.radio
        sangrando = self.desangrado is not None and self.desangrado.activo
        # Poste
        pygame.draw.line(pantalla, (90, 70, 50), (px, py + r), (px, py + r + 16), 4)
        # Cuerpo (saco de pruebas) y diana
        pygame.draw.circle(pantalla, (200, 180, 140), (px, py), r)
        pygame.draw.circle(pantalla, (120, 100, 70), (px, py), r, 2)
        pygame.draw.circle(pantalla, (200, 70, 60), (px, py), r // 2, 2)
        pygame.draw.circle(pantalla, (200, 70, 60), (px, py), 2)
        # Indicador de veneno (anillo verde)
        if self.veneno is not None and self.veneno.activo:
            pygame.draw.circle(pantalla, COLOR_VENENO, (px, py), r + 8, 2)
        # Indicador de quemadura (anillo naranja)
        if getattr(self, "quemadura", None) is not None and self.quemadura.activo:
            pygame.draw.circle(pantalla, (255, 140, 40), (px, py), r + 4, 2)
        if getattr(self, "inmovilizado", None) is not None and self.inmovilizado.activo:
            pygame.draw.circle(pantalla, (170, 185, 210), (px, py), r + 6, 1)
        # Espada del maniqui (coordenadas de mundo)
        if getattr(self, "herramienta", None):
            self.herramienta.dibujar(pantalla, self, desplazamiento)
        # Barra de vida
        bw = 46
        bx = px - bw // 2
        by = py - r - 12
        pygame.draw.rect(pantalla, (40, 40, 40), (bx, by, bw, 5), border_radius=2)
        prop = max(0.0, self.vida / self.vida_max)
        if prop > 0:
            col = (200, 90, 90) if sangrando else (90, 200, 110)
            pygame.draw.rect(pantalla, col, (bx, by, int(bw * prop), 5), border_radius=2)
        # Barras de escudo (fisico verde, magico azul) encima de la vida
        for i, (valor, maximo, color) in enumerate((
                (self.escudo, self.escudo_max, (120, 255, 150)),
                (self.escudo_magico, self.escudo_magico_max, (90, 200, 255)))):
            sy = by - 5 - i * 5
            pygame.draw.rect(pantalla, (40, 40, 40), (bx, sy, bw, 3))
            if maximo > 0 and valor > 0:
                pygame.draw.rect(pantalla, color, (bx, sy, int(bw * valor / maximo), 3))
        if self.anulacion_escudo_magico > 0:
            # Escudo magico anulado: barra tachada en rojo
            pygame.draw.rect(pantalla, (220, 30, 40), (bx - 1, by - 11, bw + 2, 5), 1)
        # Marca de desangrado: tres gotas rojas
        if sangrando:
            for i in range(3):
                pygame.draw.circle(pantalla, (210, 70, 70), (px - 8 + i * 8, by - 16), 2)
        # Indicador de ralentizacion (no se mueve, pero se ve el debuff recibido)
        if fuente is not None and self.tiempo_ralentizacion > 0:
            txt = fuente.render(f"Vel -{self.ralentizacion * 100:g}%", True, (235, 235, 255))
            pantalla.blit(txt, txt.get_rect(midleft=(bx + bw + 4, by - 3)))


def dibujar_pantalla_muerte(pantalla, area, fuentes):
    """Velo oscuro sobre el mundo con el aviso de muerte y dos botones.
    Devuelve {"reaparecer": Rect, "menu": Rect}."""
    velo = pygame.Surface(area.size, pygame.SRCALPHA)
    velo.fill((0, 0, 0, ALFA_PANTALLA_MUERTE))
    pantalla.blit(velo, area.topleft)
    caja = pygame.Rect(0, 0, 360, 190)
    caja.center = area.center
    pygame.draw.rect(pantalla, (26, 20, 24), caja, border_radius=10)
    pygame.draw.rect(pantalla, (200, 70, 70), caja, width=2, border_radius=10)
    titulo = fuentes["hab_contador"].render("HAS MUERTO", True, (235, 90, 90))
    pantalla.blit(titulo, titulo.get_rect(center=(caja.centerx, caja.y + 34)))
    aviso = fuentes["texto"].render("Reapareces en el centro desde el nivel 1.", True, (200, 200, 210))
    pantalla.blit(aviso, aviso.get_rect(center=(caja.centerx, caja.y + 66)))
    botones = {}
    for i, (clave, texto, borde) in enumerate((("reaparecer", "Reaparecer [R]", (100, 230, 130)),
                                               ("menu", "Volver al menú principal [M]", (120, 160, 220)))):
        r = pygame.Rect(caja.x + 30, caja.y + 92 + i * 42, caja.width - 60, 32)
        pygame.draw.rect(pantalla, (40, 46, 60), r, border_radius=6)
        pygame.draw.rect(pantalla, borde, r, width=1, border_radius=6)
        t = fuentes["sub"].render(texto, True, (230, 235, 245))
        pantalla.blit(t, t.get_rect(center=r.center))
        botones[clave] = r
    return botones


def iniciar_mundo(config):
    """
    Inicia y gestiona el bucle del mundo del juego en pantalla completa.
    Recibe un diccionario `config` con los datos del personaje y habilidades.
    """
    pygame.init()

    info_pantalla = pygame.display.Info()
    ancho_pantalla = info_pantalla.current_w
    alto_pantalla = info_pantalla.current_h

    pantalla = pygame.display.set_mode((ancho_pantalla, alto_pantalla), pygame.FULLSCREEN)
    pygame.display.set_caption("Level - Mundo (Pantalla Completa)")

    # Proporciones optimizadas: laterales compactos para maximizar el mundo central
    ancho_panel_izq = 230
    ancho_panel_der = 320

    mundo_x = ancho_panel_izq
    mundo_y = 0
    mundo_w = ancho_pantalla - ancho_panel_izq - ancho_panel_der
    mundo_h = alto_pantalla

    # Coordenadas del mundo: cuadrado que contiene el círculo de radio 3000.
    # La cámara dibuja solo la porción visible dentro del área central de la pantalla.
    limites_mundo = (0, 0, TAMANO_MUNDO, TAMANO_MUNDO)
    area_mundo_pantalla = pygame.Rect(mundo_x, mundo_y, mundo_w, mundo_h)

    # Mapa fijo guardado (mapas/<nombre>.json). Si falta o esta roto: aviso y generador con la
    # semilla fija, asi el juego nunca se queda sin mundo. config['mapa'] elige otro mapa.
    import mapa as MAPA                    # aqui: mapa.py importa este modulo
    cargado, motivo = MAPA.cargar_terreno(config.get("mapa", MAPA_POR_DEFECTO))
    if cargado is not None:
        charcos, vegetacion, rocas, datos_mapa = cargado
    else:
        print("Aviso: no se pudo cargar el mapa (%s); se genera con la semilla fija." % motivo)
        charcos, vegetacion, rocas = generar_terreno()
        datos_mapa = {"zonas": [], "aparicion": {}}
    fauna = SistemaFauna(LIMITE, vegetacion, charcos, rocas)

    # Casa del spawn: paredes solidas e indestructibles (van con las rocas, despues de la fauna
    # para que ningun oso las elija de cueva) y jardin sin fauna
    casa = Casa(CENTRO_MUNDO)
    rocas.extend(casa.paredes)
    FAUNA.ZONA_PROHIBIDA = (pygame.Vector2(CENTRO_MUNDO), casa.radio_jardin)

    # Maniqui de pruebas en el jardin, al sur de la puerta
    maniqui = Maniqui(casa.punto_maniqui)

    # Contexto compartido por los combatientes (Fase 1 del plan de NPC). 'combatientes' en la
    # configuracion: personajes extra que pelean en el mundo (por ahora solo en las pruebas).
    ctx = Contexto(rocas, vegetacion, charcos, fauna, limites_mundo)
    for otro in config.get("combatientes", ()):
        ctx.agregar_combatiente(otro)

    # Capa oscura para simular la poca visibilidad dentro de un arbusto
    capa_oscura = pygame.Surface((mundo_w, mundo_h), pygame.SRCALPHA)
    capa_oscura.fill((0, 0, 0, OSCURECIMIENTO))

    # Instanciar personaje en el centro del mapa (los mismos datos sirven para reaparecer)
    def datos_jugador(habilidades, herramienta):
        return dict(
            nombre=config.get("nombre", "Héroe"),
            x=CENTRO_MUNDO.x,
            y=CENTRO_MUNDO.y,
            tamano=config.get("tamano", 1),
            velocidad=config.get("velocidad", 3),
            vida=config.get("vida", 20),
            fuerza=config.get("fuerza", 3),
            energia=config.get("energia", 80),
            escudo=config.get("escudo", 0),
            escudo_magico=config.get("escudo_magico", 0),
            color=config.get("color", (0, 150, 255)),
            habilidades=habilidades,
            herramienta=herramienta
        )

    jugador = Personaje(
        nombre=config.get("nombre", "Héroe"),
        x=CENTRO_MUNDO.x,
        y=CENTRO_MUNDO.y,
        tamano=config.get("tamano", 1),
        velocidad=config.get("velocidad", 3),
        vida=config.get("vida", 20),
        fuerza=config.get("fuerza", 3),
        energia=config.get("energia", 80),
        escudo=config.get("escudo", 0),
        escudo_magico=config.get("escudo_magico", 0),
        color=config.get("color", (0, 150, 255)),
        habilidades=config.get("habilidades", []),
        herramienta=config.get("herramienta", EspadaLigera())
    )

    def aplicar_extras_pruebas(j):
        """Opciones del personaje de pruebas (shadow498), elegidas en la creación:
        - 'puntos_extra': un gran lote de puntos de mejora para subir las stats a gusto con el
          panel existente (botones + o la tecla [L]).
        - 'dar_todo': todas las armas, todas las habilidades y todos los objetos (anillos al
          máximo + tótems) en el inventario."""
        j.inspector = bool(config.get("inspector"))     # ShadowGOD (ver Personaje.inspector)
        if config.get("puntos_extra"):
            j.puntos_mejora += PUNTOS_PRUEBA_SHADOW
        if config.get("dar_todo"):
            for n in j.herramientas_faltantes():
                j.agregar_herramienta(n)
            for n in j.habilidades_faltantes():
                j.agregar_habilidad(n)
            for id_anillo, datos in TL.ANILLOS.items():
                for _ in range(datos["nivel_max"]):
                    j.talismanes.agregar_anillo(id_anillo)
            for _ in range(TL.TOTEM_MAX):
                j.talismanes.agregar_totem()
            j.recalcular_talismanes()

    aplicar_extras_pruebas(jugador)
    es_pruebas = config.get("es_pruebas", False)   # shadow498: habilita teclas de prueba extra ([0])

    fuentes = {
        "titulo": pygame.font.SysFont("Segoe UI", 14, bold=True),
        "sub": pygame.font.SysFont("Segoe UI", 11, bold=True),
        "texto": pygame.font.SysFont("Segoe UI", 11),
        "mini": pygame.font.SysFont("Segoe UI", 10),
        "valor": pygame.font.SysFont("Segoe UI", 12, bold=True),
        "contador": pygame.font.SysFont("Segoe UI", 20, bold=True),
        "nombre": pygame.font.SysFont("Segoe UI", 11, bold=True),
        "hab_nom": pygame.font.SysFont("Segoe UI", 14, bold=True),
        "hab_sub": pygame.font.SysFont("Segoe UI", 12, bold=True),
        "hab_det": pygame.font.SysFont("Segoe UI", 12),
        "hab_mini": pygame.font.SysFont("Segoe UI", 11),
        "hab_contador": pygame.font.SysFont("Segoe UI", 22, bold=True)
    }

    reloj = pygame.time.Clock()
    ejecutando = True
    muerto = False            # Vida a 0: el mundo se congela y sale la pantalla de muerte
    tumba = None              # Tumba de la ultima muerte sin totem (guarda el progreso 10 min)
    inventario_abierto = False  # [I]: inventario superpuesto (NO pausa el mundo)
    tienda_abierta = None       # [E] junto a un vendedor: su tienda (NO pausa el mundo)
    mensaje_tienda = None
    estado_inv = nuevo_estado_inventario()
    aviso_totem = None          # [texto, segundos transcurridos] tras salvarte un tótem
    cola_ruletas = []           # premios de orbes Gacha por mostrar
    ruleta_mundo = None         # ruleta de anillos que se está mostrando sobre el mundo
    botones_muerte = {}
    textos_flotantes = []     # [texto, color, posicion en el mundo, segundos transcurridos]
    motivo_salida = "salir"   # "salir" = cerrar juego; "menu" = volver a seleccion
    mostrar_hitboxes = False  # Alternable con la tecla [H]
    mostrar_brujula = False   # Alternable con la tecla [C]
    botones_stats = {}        # Botones del panel (clave -> Rect), se actualizan cada frame
    info_abierta = None       # Tooltip de ayuda abierto: None, "stats" o "hab"

    # Cámara: punto del mundo que queda en el centro del área visible
    camara = pygame.Vector2(jugador.posicion)

    def vista_camara():
        """Rectángulo (en coordenadas del mundo) que la cámara está mostrando con la vista normal.
        Es la que usa la logica (fauna, enemigos cercanos) aunque ShadowGOD aleje la vista."""
        return pygame.Rect(
            round(camara.x - mundo_w / 2),
            round(camara.y - mundo_h / 2),
            mundo_w,
            mundo_h
        )

    # ShadowGOD: nivel de zoom (indice en NIVELES_ZOOM), capas y la imagen del mapa entero
    zoom_inspector = [0]
    mostrar_capas = False
    imagen_lejana = [None]

    def zoom_actual():
        return NIVELES_ZOOM[zoom_inspector[0]] if jugador.inspector else 1.0

    def vista_dibujo():
        """Rectángulo del mundo que se dibuja (más grande con la vista alejada de ShadowGOD)."""
        z = zoom_actual()
        ancho, alto = round(mundo_w / z), round(mundo_h / z)
        return pygame.Rect(round(camara.x - ancho / 2), round(camara.y - alto / 2), ancho, alto)

    def raton_a_mundo(mx, my):
        """Punto del mundo bajo el ratón (tiene en cuenta el zoom de ShadowGOD)."""
        v, z = vista_dibujo(), zoom_actual()
        return pygame.Vector2(v.x + (mx - mundo_x) / z, v.y + (my - mundo_y) / z)

    def cambiar_zoom(paso):
        zoom_inspector[0] = max(0, min(len(NIVELES_ZOOM) - 1, zoom_inspector[0] + paso))

    def salvar_con_totem():
        """Un Tótem de vida equipado evita la muerte: vuelves al centro con la vida, la energía
        y los escudos llenos y sin efectos; conservas nivel, XP, monedas y objetos. Tus sombras
        desaparecen, como en una muerte normal."""
        objetivos_viejos = [jugador]
        for hab in jugador.fuentes_criaturas():
            for cr in getattr(hab, "criaturas", ()):
                cr.vivo = False
                objetivos_viejos.append(cr)
        jugador.sombras_anillo.matar_todas()      # vuelven tras su tiempo de reaparición
        fauna.olvidar_objetivos(objetivos_viejos)
        jugador.posicion = pygame.Vector2(CENTRO_MUNDO)
        jugador.destino = pygame.Vector2(CENTRO_MUNDO)
        jugador.empuje.update(0, 0)
        jugador.vida = jugador.vida_max
        jugador.energia = jugador.energia_max
        jugador.escudo = jugador.escudo_max
        jugador.escudo_magico = jugador.escudo_magico_max
        jugador.desangrado = None
        jugador.veneno = None
        jugador.ralentizacion = 0.0
        jugador.tiempo_ralentizacion = 0.0
        jugador.tiempo_dano_lago = 0.0
        jugador.objetivo_apuntado = None
        camara.update(jugador.posicion)

    def dar_talisman_prueba():
        """[T] (prueba): un anillo al azar con las probabilidades de rareza del Gacha, o un tótem."""
        col = jugador.talismanes
        if random.random() < PROB_DEBUG_TOTEM:
            res, id_obj = col.agregar_totem(), TL.TOTEM
        else:
            r, acum, rareza = random.random(), 0.0, TL.COMUN
            for rz, prob in TL.PROB_RAREZA.items():
                acum += prob
                if r < acum:
                    rareza = rz
                    break
            id_obj = random.choice(TL.anillos_de_rareza(rareza))
            res = col.agregar_anillo(id_obj)
        if res == "maximo":
            jugador.monedas += TL.DEVOLUCION_REPETIDO
            texto = f"{TL.nombre_objeto(id_obj)} al máximo: +{TL.DEVOLUCION_REPETIDO} monedas"
        elif id_obj == TL.TOTEM:
            texto = f"+1 Tótem de vida (x{col.totems})"
        else:
            texto = f"{TL.nombre_objeto(id_obj)} Nv {col.anillos[id_obj]}"
        jugador.recalcular_talismanes()
        textos_flotantes.append([texto, TL.color_objeto(id_obj), jugador.posicion - pygame.Vector2(0, 48), 0.0])

    # Equipo de la creación: al morir sin tótem se vuelve a él (se pierde lo del Gacha)
    equipo_inicial = ([(type(h), h.tecla, h.tecla_str) for h in jugador.habilidades],
                      type(jugador.herramienta) if jugador.herramienta else None)

    def dar_objeto_prueba():
        """[Y] (prueba): una herramienta o habilidad que no tengas, a nivel 1."""
        opciones = ([("herr", n) for n in jugador.herramientas_faltantes()]
                    + [("hab", n) for n in jugador.habilidades_faltantes()])
        if not opciones:
            texto, color = "Ya lo tienes todo", (200, 200, 210)
        else:
            tipo, nombre = random.choice(opciones)
            if tipo == "herr":
                jugador.agregar_herramienta(nombre)
                texto, color = f"Herramienta nueva: {nombre}", (255, 200, 120)
            else:
                jugador.agregar_habilidad(nombre)
                texto, color = f"Habilidad nueva: {nombre}", (170, 205, 255)
        textos_flotantes.append([texto, color, jugador.posicion - pygame.Vector2(0, 48), 0.0])

    def limpiar_cooldowns():
        """[0] (shadow498): pone a 0 el cooldown de todas las habilidades que esten en recarga,
        dejandolas listas al instante. Es de un solo uso por pulsacion: al reutilizar la
        habilidad vuelve su cooldown normal."""
        n = 0
        for hab in jugador.coleccion_habilidades:
            if getattr(hab, "estado", None) == "COOLDOWN":
                hab.tiempo_restante_cooldown = 0.0
                hab.estado = "LISTA"
                n += 1
        if n:
            texto, color = f"Cooldown eliminado ({n})", (120, 230, 255)
        else:
            texto, color = "Ninguna habilidad en recarga", (200, 200, 210)
        textos_flotantes.append([texto, color, jugador.posicion - pygame.Vector2(0, 48), 0.0])

    def regenerar_stats():
        """[F] (shadow498): rellena vida, energia, escudo y escudo magico a su maximo
        (incluye los bonos de talisman). Si hay una anulacion de escudo magico activa, el
        relleno se aplica al valor que recupera al terminar."""
        jugador.vida = jugador.vida_max
        jugador.energia = jugador.energia_max
        jugador.escudo = jugador.escudo_max
        if getattr(jugador, "anulacion_escudo_magico", 0.0) > 0:
            jugador.escudo_magico_guardado = jugador.escudo_magico_max
        else:
            jugador.escudo_magico = jugador.escudo_magico_max
        textos_flotantes.append(["Estadisticas al 100%", (150, 255, 180),
                                 jugador.posicion - pygame.Vector2(0, 48), 0.0])

    def reaparecer():
        """El jugador vuelve al centro desde cero (nivel 1, XP 0, la herramienta y las
        habilidades de la creación a nivel 1, vida y energía llenas). Pierde todo lo conseguido
        (talismanes, herramientas y habilidades extra). Sus sombras desaparecen; el mundo sigue igual."""
        objetivos_viejos = [jugador]
        for hab in jugador.coleccion_habilidades + [jugador.sombras_anillo]:
            for cr in getattr(hab, "criaturas", ()):
                cr.vivo = False
                objetivos_viejos.append(cr)
        fauna.olvidar_objetivos(objetivos_viejos)
        nuevas = []
        for cls, tecla, tecla_str in equipo_inicial[0]:
            nueva = cls()
            nueva.asignar_tecla(tecla, tecla_str)
            nuevas.append(nueva)
        herramienta = equipo_inicial[1]() if equipo_inicial[1] else None
        # Se reinicia el mismo objeto: quien lo referencia (maniqui, fauna) sigue valiendo
        jugador.__init__(**datos_jugador(nuevas, herramienta))
        aplicar_extras_pruebas(jugador)
        camara.update(jugador.posicion)
        textos_flotantes.clear()

    vendedores = SistemaVendedores(LIMITE, casa, charcos, jugador)

    while ejecutando:
        dt = reloj.tick(60) / 1000.0  # Delta time en segundos

        # Tumba: su tiempo corre siempre (tambien con la pantalla de muerte o el inventario)
        if tumba is not None:
            tumba.actualizar(dt)
            if tumba.caducada:
                tumba = None
                if not muerto:
                    textos_flotantes.append(["La tumba desapareció", (200, 200, 210),
                                             jugador.posicion - pygame.Vector2(0, 48), 0.0])

        # Modo combate de las sombras: mantener la tecla de una invocacion activa pone a
        # sus criaturas en guardia (se dirigen con el clic derecho).
        teclas_estado = pygame.key.get_pressed()
        for hab in jugador.habilidades:
            if hasattr(hab, "ordenar"):
                hab.modo_combate = (hab.estado == "INVOCADO" and teclas_estado[hab.tecla])

        # Enemigos actuales (por ahora solo el maniqui de pruebas)
        enemigos_sin_tumba = (([maniqui] if maniqui.vivo else []) + fauna.animales_con_vida(vista_camara())
                              + vendedores.objetivos() + [c for c in ctx.combatientes if c.vida > 0])
        # La tumba recibe solo los golpes directos (arma, proyectiles, cuchillas, ondas, explosiones)
        enemigos = enemigos_sin_tumba + ([tumba] if tumba is not None and tumba.vivo else [])

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            # Muerto: solo valen reaparecer y volver al menú (teclas o botones)
            elif muerto:
                accion = None
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_r, pygame.K_RETURN):
                        accion = "reaparecer"
                    elif evento.key == pygame.K_m:
                        accion = "menu"
                    elif evento.key == pygame.K_ESCAPE:
                        ejecutando = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    for clave, rect in botones_muerte.items():
                        if rect.collidepoint(evento.pos):
                            accion = clave
                if accion == "reaparecer":
                    reaparecer()
                    muerto = False
                elif accion == "menu":
                    motivo_salida = "menu"
                    ejecutando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False

                # [M] Volver a la pantalla de seleccion/creacion (sin cerrar el juego)
                elif evento.key == pygame.K_m:
                    motivo_salida = "menu"
                    ejecutando = False

                # [I] Abrir / cerrar el inventario (el mundo sigue en marcha)
                elif evento.key == pygame.K_i:
                    inventario_abierto = not inventario_abierto

                # [H] Alternar visualización de hitboxes para depuración
                elif evento.key == pygame.K_h:
                    mostrar_hitboxes = not mostrar_hitboxes
                elif evento.key == pygame.K_c:
                    mostrar_brujula = not mostrar_brujula

                # [E] Comerciar con el vendedor cercano (o cerrar su tienda)
                elif evento.key == pygame.K_e and not muerto:
                    if tienda_abierta is not None:
                        tienda_abierta = None
                    else:
                        cercano = vendedores.cercano(jugador)
                        if cercano is not None:
                            tienda_abierta, mensaje_tienda = cercano, None
                            inventario_abierto = False
                        elif todos_al_maximo(jugador) and vendedores.alguno_cerca(jugador):
                            textos_flotantes.append(["Ya tienes todos los anillos al máximo", COLOR_XP_MAX,
                                                     jugador.posicion - pygame.Vector2(0, 48), 0.0])

                # [1] Exclusivo para Herramientas (Espada Ligera sacar/guardar)
                elif evento.key == pygame.K_1:
                    jugador.alternar_arma()

                # [K] (prueba) +100 monedas para probar el Gacha
                elif evento.key == pygame.K_k:
                    jugador.monedas += MONEDAS_PRUEBA
                    textos_flotantes.append([f"+{MONEDAS_PRUEBA} monedas (prueba)", COLOR_MONEDAS,
                                             jugador.posicion - pygame.Vector2(0, 48), 0.0])

                # [Y] (prueba) Conseguir una herramienta o habilidad nueva al azar
                elif evento.key == pygame.K_y:
                    dar_objeto_prueba()

                # [T] (prueba) Conseguir un talismán al azar (hasta que exista el Gacha)
                elif evento.key == pygame.K_t:
                    dar_talisman_prueba()

                # [L] (debug) Subir de nivel: otorga PUNTOS_MEJORA_POR_NIVEL puntos de mejora
                elif evento.key == pygame.K_l:
                    jugador.subir_nivel()

                # [0] (shadow498) Eliminar el cooldown actual de todas las habilidades (un solo uso)
                elif es_pruebas and evento.key == pygame.K_0:
                    limpiar_cooldowns()

                # [F] (shadow498) Rellenar todas las estadisticas al 100%
                elif es_pruebas and evento.key == pygame.K_f:
                    regenerar_stats()

                # ShadowGOD: [+] / [-] acercan y alejan la vista, [V] muestra las capas del mapa
                elif jugador.inspector and evento.key in TECLAS_ACERCAR:
                    cambiar_zoom(-1)
                elif jugador.inspector and evento.key in TECLAS_ALEJAR:
                    cambiar_zoom(1)
                elif jugador.inspector and evento.key == pygame.K_v:
                    mostrar_capas = not mostrar_capas

                # [Espacio] Golpe cuerpo a cuerpo con el arma (manual); con el Arco empieza a cargar
                elif evento.key == pygame.K_SPACE:
                    jugador.pulsar_ataque()
                # [R] Arco: comprar un lote de 10 flechas con energia
                elif evento.key == pygame.K_r:
                    if jugador.herramienta and hasattr(jugador.herramienta, "comprar_flechas"):
                        jugador.herramienta.comprar_flechas(jugador)
                # [J] (debug) Simular un golpe del arma (desgasta 1) para probar la rotura
                elif evento.key == pygame.K_j:
                    if jugador.herramienta:
                        jugador.herramienta.desgastar()

                # Teclas dinámicas [2], [3] y [4] para Habilidades
                else:
                    # Cargables: empiezan a cargar; invocacion activa: modo combate; si no, se activa
                    for hab in jugador.habilidades:
                        if evento.key == hab.tecla:
                            jugador.pulsar_habilidad(hab)

            # Soltar la tecla de una habilidad cargable: dispara la carga acumulada.
            # Soltar la de una invocacion: si no se dio otra orden, vuelve al estado pasivo.
            elif evento.type == pygame.KEYUP:
                # Soltar [Espacio] con el Arco: dispara la flecha si la carga llego a 1 s
                if evento.key == pygame.K_SPACE:
                    jugador.soltar_ataque()
                for hab in jugador.habilidades:
                    if evento.key == hab.tecla:
                        jugador.soltar_habilidad(hab)

            elif evento.type == pygame.MOUSEWHEEL:
                if jugador.inspector:                 # rueda arriba = acercar, abajo = alejar
                    cambiar_zoom(-1 if evento.y > 0 else 1)

            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mouse_x, mouse_y = evento.pos

                    # ¿Clic en un botón [+] (stats, arma o habilidad)? Todos gastan puntos de mejora.
                    click_btn = None
                    for nombre_btn, rect_btn in botones_stats.items():
                        if rect_btn.collidepoint(mouse_x, mouse_y):
                            click_btn = nombre_btn
                            break

                    if click_btn == "__info_stats__":
                        info_abierta = None if info_abierta == "stats" else "stats"
                    elif click_btn == "__info_hab__":
                        info_abierta = None if info_abierta == "hab" else "hab"
                    elif click_btn == "__arma__":
                        info_abierta = None
                        # El arma cuesta 2 puntos por mejora de nivel
                        if jugador.puntos_mejora >= 2 and jugador.herramienta and jugador.herramienta.subir_nivel():
                            jugador.puntos_mejora -= 2
                    elif click_btn and click_btn.startswith("__hab__"):
                        info_abierta = None
                        indice = int(click_btn.split("_")[-1])
                        if 0 <= indice < len(jugador.habilidades):
                            hab_mejora = jugador.habilidades[indice]
                            # Cada habilidad define cuántos puntos cuesta su mejora (1 por defecto)
                            costo = hab_mejora.costo_mejora     # coste del siguiente nivel (leer antes de subir)
                            if jugador.puntos_mejora >= costo and hab_mejora.subir_nivel():
                                jugador.puntos_mejora -= costo
                    elif click_btn and click_btn.startswith("__modo__"):
                        info_abierta = None
                        indice = int(click_btn.split("_")[-1])
                        if 0 <= indice < len(jugador.habilidades):
                            jugador.habilidades[indice].cambiar_modo(jugador)
                    elif click_btn == "__zoom_mas__":
                        cambiar_zoom(-1)
                    elif click_btn == "__zoom_menos__":
                        cambiar_zoom(1)
                    elif click_btn == "__capas__":
                        mostrar_capas = not mostrar_capas
                    elif click_btn == "__toggle_anim__":
                        info_abierta = None
                        set_animaciones_activas(not animaciones_activas())
                    elif click_btn == "__flechas__":
                        info_abierta = None
                        jugador.herramienta.comprar_flechas(jugador)
                    elif click_btn == "__menu__":
                        info_abierta = None
                        motivo_salida = "menu"
                        ejecutando = False
                    elif click_btn == "__cerrar_inv__":
                        inventario_abierto = False
                    elif click_btn == "__cerrar_tienda__":
                        tienda_abierta = None
                    elif click_btn == "__tienda_fondo__":
                        pass                      # clic dentro de la tienda: no mueve al personaje
                    elif click_btn and click_btn.startswith("__tienda__"):
                        if tienda_abierta is not None:
                            mensaje_tienda = tienda_abierta.comprar(int(click_btn.split("_")[-1]), jugador)
                    elif click_btn == "__inv_fondo__":
                        pass                      # clic dentro del inventario: no mueve al personaje
                    elif click_btn and click_btn.startswith("__inv__"):
                        manejar_clic_inventario(click_btn, jugador, estado_inv, pygame.time.get_ticks() / 1000.0)
                    elif click_btn:
                        info_abierta = None
                        jugador.subir_stat(click_btn)
                    # Clic fuera de cualquier botón: cerrar tooltip y, si cae en el mundo, mover
                    elif mundo_x <= mouse_x <= (mundo_x + mundo_w):
                        info_abierta = None
                        # Convertir clic de pantalla a coordenadas del mundo según la cámara
                        jugador.mover_a(raton_a_mundo(mouse_x, mouse_y), LIMITE)

                elif evento.button == 3:
                    # Clic derecho: dirige a las sombras en modo combate (mantener su tecla).
                    # Sobre un enemigo lo persiguen aunque se mueva; en terreno libre van al
                    # punto; cerca del jugador vuelven a seguirlo. El clic izquierdo sigue
                    # libre para mover al personaje.
                    # Sin ninguna invocacion en modo combate, el clic derecho es el Autoapuntado:
                    # sobre un enemigo lo fija; en terreno libre o sobre el mismo objetivo lo quita.
                    mouse_x, mouse_y = evento.pos
                    sobre_inventario = ((inventario_abierto and rect_inventario(area_mundo_pantalla).collidepoint(mouse_x, mouse_y))
                                        or (tienda_abierta is not None and rect_tienda(area_mundo_pantalla).collidepoint(mouse_x, mouse_y)))
                    if mundo_x <= mouse_x <= (mundo_x + mundo_w) and not sobre_inventario:
                        punto = raton_a_mundo(mouse_x, mouse_y)
                        en_combate = jugador.ordenar_sombras(punto, enemigos_sin_tumba)
                        # Con la tecla de una invocacion mantenida el clic derecho es una orden aunque
                        # esa invocacion no pueda recibirla ahora (Sombra Arana en recarga): nunca
                        # cambia el Autoapuntado
                        tecla_invocacion = any(hasattr(h, "ordenar") and teclas_estado[h.tecla]
                                               for h in jugador.habilidades)
                        if not en_combate and not tecla_invocacion:
                            jugador.apuntar(enemigo_en(punto, enemigos, AUTOAPUNTADO_MARGEN_CLIC))

        # Muerto: el mundo queda congelado detrás de la pantalla de muerte
        if not muerto:
            # El jugador es un combatiente mas (Fase 1 del plan de NPC): pasa por las mismas
            # funciones que los NPC, en el orden de siempre, con los pasos del mundo entre medias.
            # Mantener [Espacio] = intencion de mantener el ataque (golpes segun la cadencia).
            jugador.mantiene_ataque = bool(teclas_estado[pygame.K_SPACE])
            salud_antes = salud_de(enemigos)        # lo que hiera el jugador vuelve a ser suyo
            combatiente_golpes(jugador, dt, enemigos)

            # Golpe del arma del enemigo (maniqui): dana al jugador y a sus invocaciones de sombra
            for enemigo in enemigos:
                arma_enemiga = getattr(enemigo, "herramienta", None)
                if not (arma_enemiga and getattr(arma_enemiga, "golpeando", False)):
                    continue
                if getattr(enemigo, "es_combatiente", False):
                    continue                            # un combatiente golpea en su propio turno
                objetivos = [jugador]
                for hab in jugador.fuentes_criaturas():
                    objetivos.extend(getattr(hab, "criaturas", ()))
                for obj in objetivos:
                    if id(obj) in arma_enemiga.enemigos_golpeados:
                        continue
                    toca = any(
                        hb and rect_circulo_colisionan(hb, obj.posicion, obj.radio)
                        for hb in arma_enemiga.obtener_hitboxes()
                    )
                    if not toca:
                        continue
                    arma_enemiga.enemigos_golpeados.add(id(obj))
                    if obj is jugador and jugador.invulnerable:
                        continue                        # invulnerable tras otro golpe
                    TL.marcar_agresor(obj, enemigo)     # las sombras de los anillos te defienden
                    dano = round(arma_enemiga.calcular_dano(enemigo) * factor_dano_corrosion(enemigo), 2)
                    # Escudo desenfundado cubriendo el golpe: como un choque, no hace daño, el
                    # atacante sale repelido con el empuje del escudo y su arma se desgasta 1
                    if obj is jugador and dano > 0 and jugador.bloquear_con_escudo(dano, enemigo.posicion):
                        if hasattr(enemigo, "aplicar_empuje"):
                            enemigo.aplicar_empuje(enemigo.posicion - jugador.posicion, jugador.herramienta.puntos_empuje)
                        arma_enemiga.desgastar(1)
                        continue
                    if dano > 0 and hasattr(obj, "recibir_dano"):
                        obj.recibir_dano(dano, arma_enemiga.tipo_dano, obj.posicion - enemigo.posicion)
                        if obj is jugador:
                            jugador.marcar_golpe()
                        arma_enemiga.desgastar(1)

            combatiente_habilidades(jugador, ctx, dt, enemigos)

            # Tumba rota: se recupera el personaje guardado (se descarta la vida nueva)
            if tumba is not None and tumba.rota:
                # Las sombras de la vida nueva desaparecen (se descarta esa vida)
                objetivos_viejos = []
                for hab in jugador.coleccion_habilidades + [jugador.sombras_anillo]:
                    for cr in getattr(hab, "criaturas", ()):
                        cr.vivo = False
                        objetivos_viejos.append(cr)
                fauna.olvidar_objetivos(objetivos_viejos)
                restaurar_estado(jugador, tumba.estado)
                tumba = None
                textos_flotantes.append(["¡Recuperaste todo lo de la tumba!", COLOR_XP_MAX,
                                         jugador.posicion - pygame.Vector2(0, 48), 0.0])

            maniqui.en_agua = any(c.contiene(maniqui.posicion) for c in charcos)
            combatiente_estado(jugador, ctx, dt, enemigos, enemigos_sin_tumba)
            marcar_autor(salud_antes, False)

            # Arbustos: ocultarse, veneno, orbes de curación y reaparición de frutales
            vegetacion.actualizar(dt, jugador)

            # Los demas combatientes (NPC). En una partida normal todavia no hay ninguno.
            for otro in list(ctx.combatientes):
                actualizar_combatiente(otro, ctx, dt, jugador)
            retirar_combatientes_muertos(ctx)

            # Maniqui de pruebas (tiquea su desangrado y su reaparicion)
            maniqui.actualizar(dt, jugador)

            # Cuerpos solidos: combatientes, maniqui e invocaciones no se solapan entre si
            # (con Cuerpo de niebla el combatiente no entra: atraviesa a todos)
            todos = [jugador] + ctx.combatientes
            cuerpos = ([] if jugador.cuerpo_de_niebla or jugador.inspector else [jugador]) + ([maniqui] if maniqui.vivo else [])
            for hab in jugador.fuentes_criaturas():
                cuerpos.extend(getattr(hab, "criaturas", ()))
            for otro in ctx.combatientes:
                cuerpos.extend(cuerpos_de_combatiente(otro))
            cuerpos.extend(fauna.cuerpos_solidos(vista_camara()))
            if tumba is not None:
                cuerpos.append(tumba)           # solida: nada la atraviesa ni la mueve
            # Fin del Cuerpo de niebla: si quedo dentro de algo, sale al hueco libre mas cercano
            for c in todos:
                niebla = c.cuerpo_de_niebla
                if getattr(c, "niebla_previa", False) and not niebla:
                    propias = {id(cr) for hab in c.fuentes_criaturas() for cr in getattr(hab, "criaturas", ())}
                    ajenos = [o for o in cuerpos if id(o) not in propias]   # sus sombras se apartan solas
                    sacar_a_hueco_libre(c, rocas, vegetacion.obstaculos_para(c), ajenos,
                                        LIMITE)
                c.niebla_previa = niebla
            resolver_solapamientos(cuerpos)
            for c in todos:
                c.hitbox.x = round(c.posicion.x - c.radio)
                c.hitbox.y = round(c.posicion.y - c.radio)

        # Cámara que sigue suavemente al personaje
        factor = min(1.0, SUAVIZADO_CAMARA * dt)
        camara += (jugador.posicion - camara) * factor
        if jugador.inspector:
            camara.update(jugador.posicion)

        # -----------------------------
        # RENDERIZADO
        # -----------------------------
        pantalla.fill(COLOR_FUERA_MAPA)

        # 1. Dibujar el mundo (solo lo visible), recortado al área central entre paneles
        vista = vista_camara()
        desplazamiento = (vista.x - mundo_x, vista.y - mundo_y)  # mundo -> pantalla
        if not muerto:
            fauna.actualizar(dt, jugador, vista, vendedores.objetivos(), ctx.combatientes)
            vendedores.actualizar(dt, jugador)
            if tienda_abierta is not None and not tienda_abierta.puede_comerciar(jugador):
                tienda_abierta = None          # se alejo, huyo, murio o se fue a casa
            xp_vend, monedas_vend = vendedores.tomar_recompensa()
            # Experiencia de los animales (y vendedores) que mataste tú o tus sombras
            xp = fauna.tomar_xp() + xp_vend
            if xp > 0:
                niveles = jugador.ganar_xp(xp)
                textos_flotantes.append([f"+{xp:g} XP", COLOR_XP, pygame.Vector2(jugador.posicion), 0.0])
                if niveles:
                    textos_flotantes.append([f"NIVEL {jugador.nivel}  +{niveles * MONEDAS_POR_NIVEL} monedas", COLOR_XP_MAX,
                                             jugador.posicion - pygame.Vector2(0, 32), 0.0])
            # Monedas de la caza
            monedas = fauna.tomar_monedas() + monedas_vend
            if monedas > 0:
                jugador.monedas += monedas
                textos_flotantes.append([f"+{monedas} monedas", COLOR_MONEDAS,
                                         jugador.posicion - pygame.Vector2(0, 16), 0.0])
            # Orbes Gacha de la cueva del oso: ruleta gratis de anillos (el premio se aplica ya)
            for _ in range(fauna.tomar_ruletas()):
                premio = GACHA.tirar_anillo(jugador)
                cola_ruletas.append(premio)
                estado_inv.setdefault("historial", []).insert(0, premio)
                del estado_inv["historial"][8:]
            if jugador.vida <= 0 and jugador.talismanes.usar_totem():
                salvar_con_totem()
                aviso_totem = [f"El Tótem de vida te salvó (quedan {jugador.talismanes.totems})", 0.0]
            elif jugador.vida <= 0:
                muerto = True
                # Sin totem: el progreso queda en una tumba donde caiste (sustituye a la anterior)
                tumba = Tumba(jugador.posicion, guardar_estado(jugador))
                inventario_abierto = False   # la pantalla de muerte manda
        # ShadowGOD con la vista alejada: hasta ZOOM_LIENZO_MIN el mundo se dibuja de verdad en un
        # lienzo mas grande que se reduce a la pantalla; mas lejos se ve el mapa entero (imagen fija
        # del terreno). Con zoom 1 (siempre, salvo ShadowGOD) todo es exactamente como antes.
        z = zoom_actual()
        pantalla_real = pantalla
        lejana = z < ZOOM_LIENZO_MIN
        if z < 1.0:
            vista = vista_dibujo()
            if not lejana:
                pantalla = pygame.Surface(vista.size)
                pantalla.fill(COLOR_FUERA_MAPA)
                desplazamiento = (vista.x, vista.y)
        if not lejana:
            pantalla.set_clip(area_mundo_pantalla if pantalla is pantalla_real else None)

            dibujar_suelo(pantalla, vista, desplazamiento)
            casa.dibujar_suelo(pantalla, vista, desplazamiento)

            for charco in charcos:
                if charco.rect.colliderect(vista):
                    charco.dibujar(pantalla, desplazamiento)

            # Peces y ranas (ambiental): se omiten con las animaciones pausadas (rendimiento)
            if animaciones_activas():
                fauna.dibujar_peces(pantalla, vista, desplazamiento)
                fauna.dibujar_ranas(pantalla, vista, desplazamiento)

            for roca in rocas:
                if roca.rect.colliderect(vista):
                    roca.dibujar(pantalla, desplazamiento)
            fauna.dibujar_entradas_cueva(pantalla, vista, desplazamiento)

            # Pasto y flores (cobertura de suelo, bajo las entidades)
            vegetacion.dibujar_cobertura(pantalla, vista, desplazamiento)
            fauna.dibujar_madrigueras(pantalla, vista, desplazamiento)
            # Cofres escondidos (a ras de suelo; arboles y arbustos los tapan)
            fauna.dibujar_cofres(pantalla, vista, desplazamiento)
            # Arboles (bosques): sombra + tronco solido bajo las entidades; la copa va al final
            vegetacion.dibujar_arboles_base(pantalla, vista, desplazamiento)
            # Telaranas de la Sombra Araña (en el suelo, bajo las entidades)
            for c in [jugador] + ctx.combatientes:
                for hab in c.habilidades:
                    if hasattr(hab, "dibujar_telaranas"):
                        hab.dibujar_telaranas(pantalla, desplazamiento)
                    if hasattr(hab, "dibujar_suelo"):
                        hab.dibujar_suelo(pantalla, desplazamiento)
                c.combustible.dibujar_suelo(pantalla, desplazamiento)
            if tumba is not None and tumba.vivo:
                tumba.dibujar(pantalla, desplazamiento, fuentes["mini"])
            # Maniqui de pruebas en el centro
            maniqui.dibujar(pantalla, desplazamiento, fuentes["mini"])

            # Dibujar personaje, auras interiores, herramienta rotada y proyectiles (y los demas
            # combatientes, con el mismo dibujo; solo el jugador tiene paneles, inventario y textos)
            jugador.dibujar(pantalla, fuentes["nombre"], desplazamiento)
            for otro in ctx.combatientes:
                otro.dibujar(pantalla, fuentes["nombre"], desplazamiento)
            fauna.dibujar_conejos(pantalla, vista, desplazamiento)
            fauna.dibujar_venados(pantalla, vista, desplazamiento)
            fauna.dibujar_jabalies(pantalla, vista, desplazamiento)
            fauna.dibujar_zorros(pantalla, vista, desplazamiento)
            fauna.dibujar_lobos(pantalla, vista, desplazamiento)
            fauna.dibujar_osos(pantalla, vista, desplazamiento)
            fauna.dibujar_cocodrilos(pantalla, vista, desplazamiento)
            vendedores.dibujar(pantalla, vista, desplazamiento, fuentes["mini"], jugador)

            # Mira roja sobre el enemigo autoapuntado
            if jugador.objetivo_apuntado is not None:
                dibujar_mira(pantalla, jugador.objetivo_apuntado, desplazamiento)

            # Dibujar invocaciones (conejos y futuras) de las habilidades que las tengan
            for c in [jugador] + ctx.combatientes:
                for hab in c.habilidades:
                    if hasattr(hab, "dibujar_invocaciones"):
                        hab.dibujar_invocaciones(pantalla, desplazamiento)
                    if hasattr(hab, "dibujar_cuchillas"):
                        hab.dibujar_cuchillas(pantalla, desplazamiento)
                    if hasattr(hab, "dibujar_ondas"):
                        hab.dibujar_ondas(pantalla, desplazamiento)
                    if hasattr(hab, "dibujar_explosiones"):
                        hab.dibujar_explosiones(pantalla, desplazamiento)
                c.sombras_anillo.dibujar_invocaciones(pantalla, desplazamiento)
                c.combustible.dibujar(pantalla, desplazamiento)

            # Parpadeo rojo de todo lo vivo que acaba de perder vida (jugador, maniqui, fauna, sombras)
            vivos_parpadeo = ([jugador] + ([maniqui] if maniqui.vivo else []) + fauna.animales_con_vida(vista)
                              + vendedores.objetivos())
            for c in [jugador] + ctx.combatientes:
                if c is not jugador:
                    vivos_parpadeo.append(c)
                for hab in c.fuentes_criaturas():
                    vivos_parpadeo.extend(getattr(hab, "criaturas", ()))
            actualizar_parpadeos(vivos_parpadeo, 0.0 if muerto else dt)
            if animaciones_activas():
                dibujar_parpadeos(pantalla, vivos_parpadeo, desplazamiento)

            # Arbustos por encima de los personajes (el que te oculta se ve semitransparente)
            vegetacion.dibujar(pantalla, vista, desplazamiento, jugador)
            if animaciones_activas():
                fauna.dibujar_mariposas(pantalla, vista, desplazamiento)
            # Copas de los arboles encima de todo, arbustos incluidos (profundidad). Se vuelven
            # semitransparentes si hay una entidad debajo: jugador, maniqui, invocaciones o fauna.
            entidades = [jugador] + ([maniqui] if maniqui.vivo else [])
            for c in [jugador] + ctx.combatientes:
                if c is not jugador:
                    entidades.append(c)
                for hab in c.fuentes_criaturas():
                    entidades.extend(getattr(hab, "criaturas", ()))
            entidades.extend(fauna.cuerpos_solidos(vista))
            vegetacion.dibujar_arboles_copas(pantalla, vista, desplazamiento, entidades)
            # Techo de la casa (casi transparente con el jugador dentro)
            casa.dibujar_techo(pantalla, vista, desplazamiento, casa.contiene(jugador.posicion))
            # Pajaros (ambiental): se omiten con las animaciones pausadas (rendimiento)
            if animaciones_activas():
                fauna.dibujar_pajaros(pantalla, vista, desplazamiento)

            # Dentro de un arbusto o invisible (Paso 0): el mapa se oscurece una sola vez (aunque
            # se den ambos) y en el arbusto solo tú ves sus orbes
            if (jugador.oculto or jugador.invisible or fauna.jugador_en_cueva(jugador)) and not jugador.inspector:
                pantalla.blit(capa_oscura, (mundo_x, mundo_y))
                vegetacion.dibujar_interior(pantalla, desplazamiento, jugador)
            fauna.dibujar_orbes_cueva(pantalla, vista, desplazamiento)
        if z < 1.0:
            lienzo = pantalla
            pantalla = pantalla_real
            pantalla.set_clip(area_mundo_pantalla)
            if not lejana:
                pantalla.blit(pygame.transform.scale(lienzo, area_mundo_pantalla.size), area_mundo_pantalla.topleft)
            else:
                if imagen_lejana[0] is None:
                    imagen_lejana[0] = MAPA.imagen_terreno(charcos, vegetacion, rocas, ESCALA_MAPA_LEJANO)
                dibujar_mapa_lejano(pantalla, area_mundo_pantalla, imagen_lejana[0], vista, z)
        if mostrar_capas and jugador.inspector:
            dibujar_capas(pantalla, area_mundo_pantalla, datos_mapa, rocas, vista, z, fuentes["mini"])
        if jugador.inspector and z < 1.0:
            # el propio ShadowGOD, siempre visible aunque la vista este muy lejos
            px = area_mundo_pantalla.x + (jugador.posicion.x - vista.x) * z
            py = area_mundo_pantalla.y + (jugador.posicion.y - vista.y) * z
            pygame.draw.circle(pantalla, (0, 0, 0), (round(px), round(py)), 8)
            pygame.draw.circle(pantalla, jugador.color, (round(px), round(py)), 6)
            desplazamiento = (vista.x - mundo_x, vista.y - mundo_y)

        # Aviso del Tótem de vida (arriba, en el centro del mundo)
        if aviso_totem is not None:
            aviso_totem[1] += dt
            if aviso_totem[1] >= DURACION_AVISO_TOTEM:
                aviso_totem = None
            else:
                sup_t = fuentes["hab_contador"].render(aviso_totem[0], True, COLOR_TOTEM_AVISO)
                alfa_t = 255 if aviso_totem[1] < DURACION_AVISO_TOTEM - 0.8 else int(255 * (DURACION_AVISO_TOTEM - aviso_totem[1]) / 0.8)
                fondo_t = pygame.Surface((sup_t.get_width() + 40, sup_t.get_height() + 16), pygame.SRCALPHA)
                pygame.draw.rect(fondo_t, (10, 30, 16, 200), fondo_t.get_rect(), border_radius=10)
                pygame.draw.rect(fondo_t, (*COLOR_TOTEM_AVISO, 255), fondo_t.get_rect(), width=2, border_radius=10)
                fondo_t.blit(sup_t, (20, 8))
                fondo_t.set_alpha(alfa_t)
                pantalla.blit(fondo_t, fondo_t.get_rect(center=(area_mundo_pantalla.centerx, area_mundo_pantalla.y + 70)))

        # Textos flotantes de XP y subida de nivel (con la vista normal)
        for tf in (textos_flotantes if z == 1.0 else ()):
            tf[3] += dt
            prog = tf[3] / DURACION_TEXTO_FLOTANTE
            sup = fuentes["sub"].render(tf[0], True, tf[1])
            sup.set_alpha(int(255 * max(0.0, 1.0 - prog)))
            pos_tf = (round(tf[2].x - desplazamiento[0]) - sup.get_width() // 2,
                      round(tf[2].y - desplazamiento[1] - jugador.radio - 32 - SUBIDA_TEXTO_FLOTANTE * prog))
            pantalla.blit(sup, pos_tf)
        textos_flotantes[:] = [tf for tf in textos_flotantes if tf[3] < DURACION_TEXTO_FLOTANTE]

        # Tumba: flecha en el borde hacia ella, con la distancia y el tiempo que le queda
        if tumba is not None and not muerto:
            tumba.dibujar_indicador(pantalla, area_mundo_pantalla, jugador, fuentes["mini"])

        # Brujula [C]: flechas hacia el conejo, lobo, oso y maniqui mas cercanos
        if mostrar_brujula and z == 1.0:
            ox, oy = desplazamiento
            cx = round(jugador.posicion.x - ox); cy = round(jugador.posicion.y - oy)
            objetivos_b = fauna.brujula(jugador.posicion)
            if maniqui.vivo:
                objetivos_b.append(("M", (230, 120, 120), pygame.Vector2(maniqui.posicion)))
            objetivos_b.extend(vendedores.brujula())
            fuente_b = fuentes["mini"]
            for etiqueta_b, color_b, pos_b in objetivos_b:
                d_b = pos_b - jugador.posicion
                dist_b = d_b.length()
                if dist_b < 1:
                    continue
                dn = d_b.normalize()
                bx = cx + int(dn.x * 58); by = cy + int(dn.y * 58)
                perp = pygame.Vector2(-dn.y, dn.x)
                p1 = (bx + int(dn.x * 9), by + int(dn.y * 9))
                p2 = (bx - int(dn.x * 5) + int(perp.x * 5), by - int(dn.y * 5) + int(perp.y * 5))
                p3 = (bx - int(dn.x * 5) - int(perp.x * 5), by - int(dn.y * 5) - int(perp.y * 5))
                pygame.draw.polygon(pantalla, color_b, [p1, p2, p3])
                txt_b = fuente_b.render("%s %d" % (etiqueta_b, int(dist_b)), True, color_b)
                pantalla.blit(txt_b, (cx + int(dn.x * 76) - txt_b.get_width() // 2, cy + int(dn.y * 76) - txt_b.get_height() // 2))
            leyenda = fuente_b.render("[C] Brujula  C=conejo  L=lobo  O=oso  M=maniqui  V=vendedor", True, (200, 210, 225))
            pantalla.blit(leyenda, (mundo_x + 12, mundo_y + 12))

        # Dibujar Hitboxes si está activada la visualización [H]
        if mostrar_hitboxes and z == 1.0:
            ox, oy = desplazamiento
            # Arbustos con su tipo revelado (solo en modo depuración)
            vegetacion.dibujar_hitboxes(pantalla, vista, desplazamiento, fuentes["mini"])

            # Hitbox del personaje (rectángulo verde brillante y círculo exterior)
            pygame.draw.rect(pantalla, (0, 255, 120), jugador.hitbox.move(-ox, -oy), 1)
            pygame.draw.circle(pantalla, (0, 255, 120), (round(jugador.posicion.x - ox), round(jugador.posicion.y - oy)), jugador.radio, 1)

            # Hitbox del maniqui y de las invocaciones (círculo magenta)
            for cuerpo in cuerpos:
                if cuerpo is not jugador:
                    pygame.draw.circle(pantalla, (255, 90, 220), (round(cuerpo.posicion.x - ox), round(cuerpo.posicion.y - oy)), cuerpo.radio, 1)

            # Hitbox de la espada si está desenfundada (rectángulo amarillo)
            if jugador.herramienta and jugador.herramienta.activa:
                if jugador.herramienta.es_escudo:
                    # Escudo: su hitbox es el arco frontal que bloquea
                    arco = jugador.herramienta.puntos_arco(jugador, jugador.herramienta.radio_arco(jugador))
                    pygame.draw.lines(pantalla, (255, 235, 50), False, [(px - ox, py - oy) for px, py in arco], 1)
                else:
                    for hb in jugador.herramienta.obtener_hitboxes():
                        pygame.draw.rect(pantalla, (255, 235, 50), hb.move(-ox, -oy), 1)

            # Hitbox de cada proyectil activo (rectángulo rojo)
            for p in jugador.proyectiles:
                if p.hitbox:
                    pygame.draw.rect(pantalla, (255, 70, 70), p.hitbox.move(-ox, -oy), 1)

            # Filo de cada cuchilla de Cortar (segmento rojo: es lo que colisiona)
            for hab in jugador.habilidades:
                for c in getattr(hab, "cuchillas", ()):
                    a, b = c.extremos()
                    pygame.draw.line(pantalla, (255, 70, 70), (a.x - ox, a.y - oy), (b.x - ox, b.y - oy), 1)

            # Hitbox de cada roca (rectángulo naranja)
            for roca in rocas:
                if roca.rect.colliderect(vista):
                    pygame.draw.rect(pantalla, (255, 160, 60), roca.rect.move(-ox, -oy), 1)

            # Zona de agua de cada charco (círculos azul claro)
            for charco in charcos:
                if charco.rect.colliderect(vista):
                    for c, r in charco.circulos:
                        pygame.draw.circle(pantalla, (120, 200, 255), (round(c.x - ox), round(c.y - oy)), round(r), 1)

        pantalla.set_clip(None)

        # Coordenadas del jugador respecto al centro (para ver cuánto avanzas)
        rel = jugador.posicion - CENTRO_MUNDO
        al_borde = LIMITE.distancia_al_borde(jugador.posicion)
        if jugador.en_agua_profunda:
            txt_agua = "  |  LAGO PROFUNDO: -80% Vel, -10 Vida/s"
        elif jugador.en_agua:
            txt_agua = "  |  EN AGUA: -50% Vel"
        else:
            txt_agua = ""
        txt_oculto = (("  |  OCULTO EN ARBUSTO" if jugador.oculto else "") + ("  |  INVISIBLE" if jugador.invisible else "")
                      + ("  |  AUTOAPUNTADO: -40% Vel" if jugador.objetivo_apuntado is not None else ""))
        if jugador.oculto or jugador.invisible:
            color_info = (140, 230, 140)
        elif jugador.en_agua_profunda:
            color_info = (90, 150, 230)
        elif jugador.en_agua:
            color_info = (120, 200, 255)
        else:
            color_info = (150, 160, 180)
        txt_coord = fuentes["mini"].render(
            f"Posición: ({rel.x:.0f}, {rel.y:.0f})  |  Al borde: {al_borde:.0f}  |  Rocas: {len(rocas)}  |  Charcos: {len(charcos)}{txt_agua}{txt_oculto}",
            True, color_info
        )
        pantalla.blit(txt_coord, (mundo_x + 12, mundo_h - 22))
        if jugador.mensaje_apuntado:
            txt_aviso = fuentes["sub"].render(jugador.mensaje_apuntado, True, (255, 150, 90))
            pantalla.blit(txt_aviso, (mundo_x + 12, mundo_h - 42))

        # 2. Dibujar Interfaces Laterales (Fuera del mundo)
        # Panel Izquierdo: Ficha del Personaje y Estado del Arma
        botones_stats = dibujar_panel_estadisticas(pantalla, 0, 0, ancho_panel_izq, alto_pantalla, jugador, fuentes, mostrar_hitboxes, info_abierta)

        # Panel Derecho: Habilidades y Manual (sus botones [+] se suman a los del panel izquierdo)
        botones_hab = dibujar_panel_habilidades(pantalla, ancho_pantalla - ancho_panel_der, 0, ancho_panel_der, alto_pantalla, jugador.habilidades, jugador, fuentes, info_abierta)
        if botones_hab:
            botones_stats.update(botones_hab)

        # Inventario [I]: encima del mundo, que sigue en marcha detrás
        if inventario_abierto and not muerto:
            botones_stats.update(dibujar_inventario(pantalla, area_mundo_pantalla, jugador, fuentes,
                                                    pygame.time.get_ticks() / 1000.0, estado_inv))
        if tienda_abierta is not None and not muerto:
            botones_stats.update(dibujar_tienda(pantalla, area_mundo_pantalla, tienda_abierta, jugador, fuentes,
                                                pygame.time.get_ticks() / 1000.0, mensaje_tienda))

        # Ruleta del orbe Gacha (encima del mundo y del inventario; no bloquea)
        t_ruleta = pygame.time.get_ticks() / 1000.0
        if ruleta_mundo is None and cola_ruletas:
            ruleta_mundo = GACHA.nueva_ruleta(cola_ruletas.pop(0), t_ruleta, solo_anillos=True)
        if ruleta_mundo is not None:
            if GACHA.ruleta_mundo_terminada(ruleta_mundo, t_ruleta):
                ruleta_mundo = None
            else:
                GACHA.dibujar_ruleta_mundo(pantalla, area_mundo_pantalla, ruleta_mundo, t_ruleta, fuentes)

        botones_muerte = dibujar_pantalla_muerte(pantalla, area_mundo_pantalla, fuentes) if muerto else {}
        if jugador.inspector:
            botones_stats.update(dibujar_botones_inspector(pantalla, area_mundo_pantalla, zoom_actual(),
                                                           mostrar_capas, fuentes["sub"]))

        pygame.display.flip()

    pygame.quit()
    return motivo_salida
