import math
import random
import pygame
from personaje import (Personaje, repartir_dano, REGEN_ESCUDO_RETRASO, REGEN_ESCUDO_POR_SEGUNDO,
                       AUTOAPUNTADO_MARGEN_CLIC, MONEDAS_POR_NIVEL, PUNTOS_MEJORA_POR_NIVEL,
                       REGEN_ENERGIA_POR_PUNTO, REGEN_ENERGIA_TOPE)
from habilidades import (dibujar_panel_habilidades, dibujar_badge_ayuda, dibujar_tooltip, PIXELES_POR_PUNTO_EMPUJE,
                         actualizar_anulacion_escudo_magico, actualizar_ralentizacion, aplicar_quemadura,
                         aplicar_veneno, enemigo_en, COLOR_VENENO)
from herramientas import EspadaLigera, EspadaLarga
from vegetacion import SistemaVegetacion, OSCURECIMIENTO, RejillaEspacial, CELDA_REJILLA
from fauna import SistemaFauna
from inventario import dibujar_inventario, rect_inventario, nuevo_estado_inventario, manejar_clic_inventario
import talismanes as TL
import gacha as GACHA

# -----------------------------
# CONFIGURACIÓN DEL MAPA
# -----------------------------
RADIO_MUNDO = 10000         # Límite circular del mapa
MARGEN_MUNDO = 150          # Espacio extra alrededor del círculo (zona oscura fuera del mapa)
TAMANO_MUNDO = (RADIO_MUNDO + MARGEN_MUNDO) * 2
CENTRO_MUNDO = pygame.Vector2(RADIO_MUNDO + MARGEN_MUNDO, RADIO_MUNDO + MARGEN_MUNDO)

# Rocas y lagos escalan con el AREA del mundo: la densidad se define para un mundo de
# referencia (radio 5000) y se multiplica por (RADIO_MUNDO / referencia)^2.
RADIO_MUNDO_REFERENCIA = 5000
ESCALA_AREA_MUNDO = (RADIO_MUNDO / RADIO_MUNDO_REFERENCIA) ** 2
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
ZONA_SEGURA_SPAWN = 140     # Radio alrededor del centro sin obstáculos (para no aparecer atrapado)
SUAVIZADO_CAMARA = 8.0      # Más alto = la cámara sigue más pegada al personaje
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

    def contiene(self, punto):
        """True si el punto (centro del jugador) está sobre el agua."""
        return any((punto - c).length() <= r for c, r in self.circulos)

    def en_zona_peligro(self, punto):
        """True si el punto está en la zona central peligrosa de un lago grande."""
        return self.es_lago_profundo and (punto - self.centro).length() <= self.radio_peligro

    def dibujar(self, pantalla, desplazamiento):
        pantalla.blit(self.superficie, (self.rect.x - desplazamiento[0], self.rect.y - desplazamiento[1]))


def generar_charcos():
    """Genera MIN_CHARCOS a MAX_CHARCOS lagos (escalan con el area del mundo) con radio
    RADIO_CHARCO_MIN a RADIO_CHARCO_MAX dentro del círculo, sin solaparse."""
    charcos = []
    objetivo = random.randint(MIN_CHARCOS, MAX_CHARCOS)
    intentos = 0
    while len(charcos) < objetivo and intentos < objetivo * INTENTOS_POR_CHARCO:
        intentos += 1
        radio = random.randint(RADIO_CHARCO_MIN, RADIO_CHARCO_MAX)
        extension = radio + ANCHO_BARRO + 10

        angulo = random.uniform(0, math.tau)
        distancia = math.sqrt(random.random()) * (RADIO_MUNDO - extension)
        if distancia - extension < ZONA_SEGURA_SPAWN:
            continue

        x = CENTRO_MUNDO.x + math.cos(angulo) * distancia
        y = CENTRO_MUNDO.y + math.sin(angulo) * distancia
        nuevo = Charco(x, y, radio)

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


def generar_rocas(zonas_ocupadas=()):
    """
    Genera MIN_ROCAS a MAX_ROCAS rocas (escalan con el area del mundo; pequeñas, grandes y
    gigantes) dentro del círculo, sin solaparse ni caer sobre zonas ocupadas (charcos,
    arbustos, arboles: cualquier objeto con .rect).
    """
    cantidad = random.randint(MIN_ROCAS, MAX_ROCAS)
    rocas = []
    intentos = 0
    rejilla = RejillaEspacial(CELDA_REJILLA)
    for z in zonas_ocupadas:
        rejilla.agregar(z.rect)

    while len(rocas) < cantidad and intentos < cantidad * INTENTOS_POR_ROCA:
        intentos += 1

        # 60% pequeñas (22-45), 35% grandes (70-130), 5% gigantes (150-300)
        r = random.random()
        if r < 0.60:
            lado = random.randint(22, 45)
        elif r < 0.95:
            lado = random.randint(70, 130)
        else:
            lado = random.randint(LADO_ROCA_GIGANTE, 300)
        media_diagonal = lado * 0.75

        # Posición aleatoria uniforme dentro del círculo (dejando la roca completa dentro)
        angulo = random.uniform(0, math.tau)
        distancia = math.sqrt(random.random()) * (RADIO_MUNDO - media_diagonal - 10)
        x = CENTRO_MUNDO.x + math.cos(angulo) * distancia
        y = CENTRO_MUNDO.y + math.sin(angulo) * distancia

        # Respetar la zona segura del centro donde aparece el personaje
        if distancia - media_diagonal < ZONA_SEGURA_SPAWN:
            continue

        nueva = Roca(x, y, lado)

        # Evitar solapamiento con rocas/charcos/vegetacion (rejilla espacial = rapido)
        if rejilla.hay_colision(nueva.rect.inflate(30, 30)):
            continue
        rejilla.agregar(nueva.rect)
        rocas.append(nueva)

    return rocas


def dibujar_suelo(pantalla, vista, desplazamiento):
    """
    Dibuja solo la parte visible del suelo: zona exterior, círculo del mapa,
    cuadrícula recortada al círculo, borde y marca del centro.
    """
    ox, oy = desplazamiento
    cx = CENTRO_MUNDO.x
    cy = CENTRO_MUNDO.y
    centro_pantalla = (round(cx - ox), round(cy - oy))
    r2 = RADIO_MUNDO * RADIO_MUNDO

    pygame.draw.circle(pantalla, COLOR_SUELO, centro_pantalla, RADIO_MUNDO)

    # Líneas verticales visibles, cortadas a la cuerda del círculo
    inicio_x = (vista.left // TAMANO_CUADRICULA) * TAMANO_CUADRICULA
    for gx in range(inicio_x, vista.right + 1, TAMANO_CUADRICULA):
        dx = gx - cx
        if dx * dx >= r2:
            continue
        media = math.sqrt(r2 - dx * dx)
        y1 = max(vista.top, cy - media)
        y2 = min(vista.bottom, cy + media)
        if y1 < y2:
            pygame.draw.line(pantalla, COLOR_CUADRICULA, (gx - ox, y1 - oy), (gx - ox, y2 - oy), 1)

    # Líneas horizontales visibles
    inicio_y = (vista.top // TAMANO_CUADRICULA) * TAMANO_CUADRICULA
    for gy in range(inicio_y, vista.bottom + 1, TAMANO_CUADRICULA):
        dy = gy - cy
        if dy * dy >= r2:
            continue
        media = math.sqrt(r2 - dy * dy)
        x1 = max(vista.left, cx - media)
        x2 = min(vista.right, cx + media)
        if x1 < x2:
            pygame.draw.line(pantalla, COLOR_CUADRICULA, (x1 - ox, gy - oy), (x2 - ox, gy - oy), 1)

    # Borde del mapa y marca del centro (spawn)
    pygame.draw.circle(pantalla, COLOR_BORDE_MAPA, centro_pantalla, RADIO_MUNDO, 3)
    pygame.draw.circle(pantalla, (45, 52, 66), centro_pantalla, 30, 1)

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


def rect_circulo_colisionan(rect, centro, radio):
    """Colision entre un rectangulo (hitbox del arma) y un circulo (enemigo)."""
    cx = max(rect.left, min(centro.x, rect.right))
    cy = max(rect.top, min(centro.y, rect.bottom))
    dx = centro.x - cx
    dy = centro.y - cy
    return (dx * dx + dy * dy) <= radio * radio


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
        if jugador is not None and getattr(jugador, "detectable", True):
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

    charcos = generar_charcos()
    vegetacion = SistemaVegetacion(CENTRO_MUNDO, RADIO_MUNDO, ZONA_SEGURA_SPAWN, charcos)
    rocas = generar_rocas(list(charcos) + vegetacion.arbustos + vegetacion.arboles)
    vegetacion.registrar_obstaculos(rocas)
    fauna = SistemaFauna(CENTRO_MUNDO, RADIO_MUNDO, vegetacion, charcos, rocas)

    # Maniqui de pruebas en el centro del mapa (recibe dano para probar las invocaciones)
    maniqui = Maniqui(CENTRO_MUNDO)

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
    inventario_abierto = False  # [I]: inventario superpuesto (NO pausa el mundo)
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
        """Rectángulo (en coordenadas del mundo) que la cámara está mostrando."""
        return pygame.Rect(
            round(camara.x - mundo_w / 2),
            round(camara.y - mundo_h / 2),
            mundo_w,
            mundo_h
        )

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
        camara.update(jugador.posicion)
        textos_flotantes.clear()

    while ejecutando:
        dt = reloj.tick(60) / 1000.0  # Delta time en segundos

        # Modo combate de las sombras: mantener la tecla de una invocacion activa pone a
        # sus criaturas en guardia (se dirigen con el clic derecho).
        teclas_estado = pygame.key.get_pressed()
        for hab in jugador.habilidades:
            if hasattr(hab, "ordenar"):
                hab.modo_combate = (hab.estado == "INVOCADO" and teclas_estado[hab.tecla])

        # Enemigos actuales (por ahora solo el maniqui de pruebas)
        enemigos = ([maniqui] if maniqui.vivo else []) + fauna.animales_con_vida(vista_camara())

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

                # [1] Exclusivo para Herramientas (Espada Ligera sacar/guardar)
                elif evento.key == pygame.K_1:
                    if jugador.herramienta:
                        jugador.herramienta.toggle()

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

                # [Espacio] Golpe cuerpo a cuerpo con el arma (manual); con el Arco empieza a cargar
                elif evento.key == pygame.K_SPACE:
                    if jugador.herramienta and hasattr(jugador.herramienta, "iniciar_carga"):
                        jugador.herramienta.iniciar_carga()
                    elif jugador.herramienta:
                        jugador.herramienta.atacar(jugador)
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
                    for hab in jugador.habilidades:
                        if evento.key == hab.tecla:
                            # Las habilidades cargables (ej. Carga de Fuego) empiezan a cargar al pulsar
                            if getattr(hab, "cargable", False):
                                hab.iniciar_carga(jugador)
                            # Invocacion ya activa: la tecla controla el modo combate
                            elif hab.estado == "INVOCADO" and hasattr(hab, "pulsar_tecla_combate"):
                                hab.pulsar_tecla_combate()
                            else:
                                hab.intentar_activar(jugador)

            # Soltar la tecla de una habilidad cargable: dispara la carga acumulada.
            # Soltar la de una invocacion: si no se dio otra orden, vuelve al estado pasivo.
            elif evento.type == pygame.KEYUP:
                # Soltar [Espacio] con el Arco: dispara la flecha si la carga llego a 1 s
                if evento.key == pygame.K_SPACE and jugador.herramienta \
                        and hasattr(jugador.herramienta, "soltar_carga"):
                    flecha = jugador.herramienta.soltar_carga(jugador)
                    if flecha:
                        jugador.proyectiles.append(flecha)
                for hab in jugador.habilidades:
                    if evento.key != hab.tecla:
                        continue
                    if getattr(hab, "cargable", False):
                        hab.soltar_carga(jugador)
                    elif hasattr(hab, "soltar_tecla_combate"):
                        hab.soltar_tecla_combate()

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
                            if jugador.puntos_mejora >= hab_mejora.costo_mejora and hab_mejora.subir_nivel():
                                jugador.puntos_mejora -= hab_mejora.costo_mejora
                    elif click_btn == "__flechas__":
                        info_abierta = None
                        jugador.herramienta.comprar_flechas(jugador)
                    elif click_btn == "__menu__":
                        info_abierta = None
                        motivo_salida = "menu"
                        ejecutando = False
                    elif click_btn == "__cerrar_inv__":
                        inventario_abierto = False
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
                        vista = vista_camara()
                        jugador.destino = pygame.Vector2(
                            vista.x + (mouse_x - mundo_x),
                            vista.y + (mouse_y - mundo_y)
                        )

                elif evento.button == 3:
                    # Clic derecho: dirige a las sombras en modo combate (mantener su tecla).
                    # Sobre un enemigo lo persiguen aunque se mueva; en terreno libre van al
                    # punto; cerca del jugador vuelven a seguirlo. El clic izquierdo sigue
                    # libre para mover al personaje.
                    # Sin ninguna invocacion en modo combate, el clic derecho es el Autoapuntado:
                    # sobre un enemigo lo fija; en terreno libre o sobre el mismo objetivo lo quita.
                    mouse_x, mouse_y = evento.pos
                    sobre_inventario = inventario_abierto and rect_inventario(area_mundo_pantalla).collidepoint(mouse_x, mouse_y)
                    if mundo_x <= mouse_x <= (mundo_x + mundo_w) and not sobre_inventario:
                        vista = vista_camara()
                        punto = pygame.Vector2(
                            vista.x + (mouse_x - mundo_x),
                            vista.y + (mouse_y - mundo_y)
                        )
                        en_combate = [h for h in jugador.habilidades if getattr(h, "modo_combate", False)]
                        for hab in en_combate:
                            hab.ordenar(punto, jugador, enemigos)
                        if not en_combate:
                            jugador.alternar_autoapuntado(enemigo_en(punto, enemigos, AUTOAPUNTADO_MARGEN_CLIC))

        # Muerto: el mundo queda congelado detrás de la pantalla de muerte
        if not muerto:
            # Actualizar herramienta (temporizador y cálculo de su hitbox)
            if jugador.herramienta:
                jugador.herramienta.actualizar(dt, jugador)

            # Mantener [Espacio] repite el golpe segun la cadencia del arma
            if teclas_estado[pygame.K_SPACE] and jugador.herramienta:
                jugador.herramienta.atacar(jugador)

            # Golpe del jugador: choque de armas (prioridad) o golpe al cuerpo del enemigo
            arma_actual = jugador.herramienta
            if arma_actual and getattr(arma_actual, "golpeando", False):
                for enemigo in enemigos:
                    if id(enemigo) in arma_actual.enemigos_golpeados:
                        continue
                    arma_enemiga = getattr(enemigo, "herramienta", None)
                    # 1) Choque de armas: mi filo toca su espada -> repelido mutuo igual + ambas se desgastan
                    if (arma_enemiga and not arma_enemiga.roto
                            and hitboxes_de_armas_chocan(arma_actual, arma_enemiga)):
                        arma_actual.enemigos_golpeados.add(id(enemigo))
                        fuerza_choque = max(arma_actual.puntos_empuje, arma_enemiga.puntos_empuje)
                        dir_al_enemigo = enemigo.posicion - jugador.posicion
                        jugador.aplicar_empuje(-dir_al_enemigo, fuerza_choque)      # yo retrocedo
                        if hasattr(enemigo, "aplicar_empuje"):
                            enemigo.aplicar_empuje(dir_al_enemigo, fuerza_choque)   # el enemigo retrocede igual
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
                    dano = arma_actual.calcular_dano(jugador)
                    if dano > 0 and hasattr(enemigo, "recibir_dano"):
                        enemigo.recibir_dano(dano, arma_actual.tipo_dano)
                        if hasattr(enemigo, "aturdir_ataque"):
                            enemigo.aturdir_ataque()     # retrasa su siguiente ataque (animales)
                        if hasattr(enemigo, "aplicar_empuje"):
                            enemigo.aplicar_empuje(enemigo.posicion - jugador.posicion, arma_actual.puntos_empuje)
                        arma_actual.desgastar(1)

            # Golpe del arma del enemigo (maniqui): dana al jugador y a sus invocaciones de sombra
            for enemigo in enemigos:
                arma_enemiga = getattr(enemigo, "herramienta", None)
                if not (arma_enemiga and getattr(arma_enemiga, "golpeando", False)):
                    continue
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
                    dano = arma_enemiga.calcular_dano(enemigo)
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

            # Actualizar proyectiles disparados (Disparo Veloz) — chocan con las rocas
            jugador.actualizar_proyectiles(dt, limites_mundo, rocas)
            # Los proyectiles desaparecen al salir del círculo del mapa
            jugador.proyectiles = [
                p for p in jugador.proyectiles
                if (p.posicion - CENTRO_MUNDO).length() <= RADIO_MUNDO + p.radio
            ]

            # Proyectiles (Disparo Veloz, Carga de Fuego, Disparo Venenoso, flechas del Arco) golpean a los enemigos
            for p in jugador.proyectiles:
                if not p.activo or getattr(p, "clavada", False):
                    continue
                for enemigo in enemigos:
                    if not getattr(enemigo, "vivo", True):
                        continue
                    if rect_circulo_colisionan(p.hitbox, enemigo.posicion, enemigo.radio):
                        if hasattr(p, "puntos_empuje"):
                            # Flecha: daño fisico, empuje fijo del arma y desgaste del arco si hace daño
                            aplicado = enemigo.recibir_dano(p.dano, p.tipo_dano)
                            enemigo.aplicar_empuje(p.direccion, p.puntos_empuje)
                            if aplicado > 0:
                                p.arco.desgastar(1)
                        elif hasattr(enemigo, "recibir_dano"):
                            enemigo.recibir_dano(p.dano, getattr(p, "tipo_dano", "magico"),
                                                 enemigo.posicion - p.posicion)
                        if hasattr(p, "quemadura_dano") and hasattr(enemigo, "quemadura"):
                            aplicar_quemadura(enemigo, p.quemadura_dano, p.quemadura_duracion)
                        if hasattr(p, "veneno_total") and hasattr(enemigo, "veneno"):
                            aplicar_veneno(enemigo, p.veneno_total, p.veneno_duracion)
                        p.activo = False
                        break
            jugador.proyectiles = [p for p in jugador.proyectiles if p.activo]

            # Actualizar regeneración global de energía
            jugador.actualizar_regeneracion(dt)
            # Actualizar regeneración del escudo físico
            jugador.actualizar_regeneracion_escudo(dt)
            # Actualizar regeneración del escudo mágico
            jugador.actualizar_regeneracion_escudo_magico(dt)

            # Actualizar todas las habilidades equipadas
            for hab in jugador.habilidades:
                hab.actualizar(dt, jugador)
            # Las habilidades guardadas en la colección siguen su recarga
            for hab in jugador.habilidades_guardadas():
                hab.actualizar(dt, jugador)
            # Sombras de los anillos (te siguen y te defienden)
            jugador.sombras_anillo.actualizar(dt, jugador)

            # Cuchillas de Cortar: golpean al primer enemigo o destruyen una roca/arbusto
            for hab in jugador.habilidades:
                if hasattr(hab, "actualizar_cuchillas"):
                    destruidas = hab.actualizar_cuchillas(rocas, vegetacion.arbustos, vegetacion.arboles, enemigos, CENTRO_MUNDO, RADIO_MUNDO)
                    vegetacion.liberar_obstaculos(destruidas)

            # Ondas Sonoras: anillos que golpean una vez a cada enemigo (atraviesan obstaculos)
            maniqui.en_agua = any(c.contiene(maniqui.posicion) for c in charcos)
            for hab in jugador.habilidades:
                if hasattr(hab, "actualizar_ondas"):
                    hab.actualizar_ondas(dt, enemigos)
            # Aura Electrica: dano por segundo a los enemigos dentro del aura
            for hab in jugador.habilidades:
                if hasattr(hab, "actualizar_dano_enemigos"):
                    hab.actualizar_dano_enemigos(dt, enemigos, jugador)
            # Sombra Araña: las telaranas atrapan a los enemigos que las pisan
            for hab in jugador.habilidades:
                if hasattr(hab, "actualizar_telaranas"):
                    hab.actualizar_telaranas(dt, enemigos)
            # Efectos temporales otorgados (ej. por Golpe de Suerte)
            jugador.actualizar_efectos(dt)
            # Desangrado activo (resta vida por intervalo; preparado para el combate)
            jugador.actualizar_desangrado(dt)
            # Invulnerabilidad breve tras recibir un golpe
            jugador.actualizar_invulnerabilidad(dt)
            # Veneno activo (ej. el que da Golpe de Suerte al portador)
            jugador.actualizar_veneno(dt)
            # Ralentizacion recibida (ej. Onda Sonora de un enemigo)
            jugador.actualizar_ralentizacion(dt)
            # Fundido visual de Paso 0 (desvanecerse / volver a verse)
            jugador.actualizar_desvanecimiento(dt)
            # Anillo de regeneración inversa (cura cada cierto tiempo)
            jugador.actualizar_talismanes(dt)

            # Terreno: ¿el jugador está pisando agua? ¿zona profunda de un lago grande?
            jugador.en_agua = any(c.contiene(jugador.posicion) for c in charcos)
            jugador.en_agua_profunda = any(c.en_zona_peligro(jugador.posicion) for c in charcos)

            # Zona profunda: 10 de daño por segundo
            if jugador.en_agua_profunda:
                jugador.tiempo_dano_lago += dt
                while jugador.tiempo_dano_lago >= 1.0:
                    jugador.tiempo_dano_lago -= 1.0
                    jugador.vida = max(0, jugador.vida - DANO_LAGO_PROFUNDO)
            else:
                jugador.tiempo_dano_lago = 0.0

            # Autoapuntado: mira al objetivo (o lo suelta si muere o sale de rango) antes de moverse
            jugador.actualizar_autoapuntado(dt)

            # Calcular velocidad acumulando debuffs y buffs
            jugador.actualizar_velocidad()

            # Mover personaje respetando el círculo del mapa y las rocas
            jugador.mover(limites_mundo, CENTRO_MUNDO, RADIO_MUNDO, rocas, vegetacion.obstaculos_para(jugador))

            # Aplicar el retroceso acumulado por empuje (combate futuro; por ahora suele ser 0)
            jugador.actualizar_empuje(dt, CENTRO_MUNDO, RADIO_MUNDO)

            # Arbustos: ocultarse, veneno, orbes de curación y reaparición de frutales
            vegetacion.actualizar(dt, jugador)

            # Maniqui de pruebas (tiquea su desangrado y su reaparicion)
            maniqui.actualizar(dt, jugador)

            # Cuerpos solidos: jugador, maniqui e invocaciones no se solapan entre si
            cuerpos = [jugador] + ([maniqui] if maniqui.vivo else [])
            for hab in jugador.fuentes_criaturas():
                cuerpos.extend(getattr(hab, "criaturas", ()))
            cuerpos.extend(fauna.cuerpos_solidos(vista_camara()))
            resolver_solapamientos(cuerpos)
            jugador.hitbox.x = round(jugador.posicion.x - jugador.radio)
            jugador.hitbox.y = round(jugador.posicion.y - jugador.radio)

        # Cámara que sigue suavemente al personaje
        factor = min(1.0, SUAVIZADO_CAMARA * dt)
        camara += (jugador.posicion - camara) * factor

        # -----------------------------
        # RENDERIZADO
        # -----------------------------
        pantalla.fill(COLOR_FUERA_MAPA)

        # 1. Dibujar el mundo (solo lo visible), recortado al área central entre paneles
        vista = vista_camara()
        desplazamiento = (vista.x - mundo_x, vista.y - mundo_y)  # mundo -> pantalla
        if not muerto:
            fauna.actualizar(dt, jugador, vista)
            # Experiencia de los animales que mataste tú o tus sombras
            xp = fauna.tomar_xp()
            if xp > 0:
                niveles = jugador.ganar_xp(xp)
                textos_flotantes.append([f"+{xp:g} XP", COLOR_XP, pygame.Vector2(jugador.posicion), 0.0])
                if niveles:
                    textos_flotantes.append([f"NIVEL {jugador.nivel}  +{niveles * MONEDAS_POR_NIVEL} monedas", COLOR_XP_MAX,
                                             jugador.posicion - pygame.Vector2(0, 32), 0.0])
            # Monedas de la caza
            monedas = fauna.tomar_monedas()
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
                inventario_abierto = False   # la pantalla de muerte manda
        pantalla.set_clip(area_mundo_pantalla)

        dibujar_suelo(pantalla, vista, desplazamiento)

        for charco in charcos:
            if charco.rect.colliderect(vista):
                charco.dibujar(pantalla, desplazamiento)

        # Peces (sombras bajo el agua), por debajo de todo lo demas
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
        for hab in jugador.habilidades:
            if hasattr(hab, "dibujar_telaranas"):
                hab.dibujar_telaranas(pantalla, desplazamiento)
        # Maniqui de pruebas en el centro
        maniqui.dibujar(pantalla, desplazamiento, fuentes["mini"])

        # Dibujar personaje, auras interiores, herramienta rotada y proyectiles
        jugador.dibujar(pantalla, fuentes["nombre"], desplazamiento)
        fauna.dibujar_conejos(pantalla, vista, desplazamiento)
        fauna.dibujar_venados(pantalla, vista, desplazamiento)
        fauna.dibujar_jabalies(pantalla, vista, desplazamiento)
        fauna.dibujar_zorros(pantalla, vista, desplazamiento)
        fauna.dibujar_lobos(pantalla, vista, desplazamiento)
        fauna.dibujar_osos(pantalla, vista, desplazamiento)
        fauna.dibujar_cocodrilos(pantalla, vista, desplazamiento)

        # Mira roja sobre el enemigo autoapuntado
        if jugador.objetivo_apuntado is not None:
            dibujar_mira(pantalla, jugador.objetivo_apuntado, desplazamiento)

        # Dibujar invocaciones (conejos y futuras) de las habilidades que las tengan
        for hab in jugador.habilidades:
            if hasattr(hab, "dibujar_invocaciones"):
                hab.dibujar_invocaciones(pantalla, desplazamiento)
            if hasattr(hab, "dibujar_cuchillas"):
                hab.dibujar_cuchillas(pantalla, desplazamiento)
            if hasattr(hab, "dibujar_ondas"):
                hab.dibujar_ondas(pantalla, desplazamiento)
        jugador.sombras_anillo.dibujar_invocaciones(pantalla, desplazamiento)

        # Parpadeo rojo de todo lo vivo que acaba de perder vida (jugador, maniqui, fauna, sombras)
        vivos_parpadeo = [jugador] + ([maniqui] if maniqui.vivo else []) + fauna.animales_con_vida(vista)
        for hab in jugador.fuentes_criaturas():
            vivos_parpadeo.extend(getattr(hab, "criaturas", ()))
        actualizar_parpadeos(vivos_parpadeo, 0.0 if muerto else dt)
        dibujar_parpadeos(pantalla, vivos_parpadeo, desplazamiento)

        # Arbustos por encima de los personajes (el que te oculta se ve semitransparente)
        vegetacion.dibujar(pantalla, vista, desplazamiento, jugador)
        fauna.dibujar_mariposas(pantalla, vista, desplazamiento)
        # Copas de los arboles encima de todo, arbustos incluidos (profundidad). Se vuelven
        # semitransparentes si hay una entidad debajo: jugador, maniqui, invocaciones o fauna.
        entidades = [jugador] + ([maniqui] if maniqui.vivo else [])
        for hab in jugador.fuentes_criaturas():
            entidades.extend(getattr(hab, "criaturas", ()))
        entidades.extend(fauna.cuerpos_solidos(vista))
        vegetacion.dibujar_arboles_copas(pantalla, vista, desplazamiento, entidades)
        # Pajaros: vuelan por encima de las copas
        fauna.dibujar_pajaros(pantalla, vista, desplazamiento)

        # Dentro de un arbusto o invisible (Paso 0): el mapa se oscurece una sola vez (aunque
        # se den ambos) y en el arbusto solo tú ves sus orbes
        if jugador.oculto or jugador.invisible or fauna.jugador_en_cueva(jugador):
            pantalla.blit(capa_oscura, (mundo_x, mundo_y))
            vegetacion.dibujar_interior(pantalla, desplazamiento, jugador)
        fauna.dibujar_orbes_cueva(pantalla, vista, desplazamiento)

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

        # Textos flotantes de XP y subida de nivel
        for tf in textos_flotantes:
            tf[3] += dt
            prog = tf[3] / DURACION_TEXTO_FLOTANTE
            sup = fuentes["sub"].render(tf[0], True, tf[1])
            sup.set_alpha(int(255 * max(0.0, 1.0 - prog)))
            pos_tf = (round(tf[2].x - desplazamiento[0]) - sup.get_width() // 2,
                      round(tf[2].y - desplazamiento[1] - jugador.radio - 32 - SUBIDA_TEXTO_FLOTANTE * prog))
            pantalla.blit(sup, pos_tf)
        textos_flotantes[:] = [tf for tf in textos_flotantes if tf[3] < DURACION_TEXTO_FLOTANTE]

        # Brujula [C]: flechas hacia el conejo, lobo, oso y maniqui mas cercanos
        if mostrar_brujula:
            ox, oy = desplazamiento
            cx = round(jugador.posicion.x - ox); cy = round(jugador.posicion.y - oy)
            objetivos_b = fauna.brujula(jugador.posicion)
            if maniqui.vivo:
                objetivos_b.append(("M", (230, 120, 120), pygame.Vector2(maniqui.posicion)))
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
            leyenda = fuente_b.render("[C] Brujula  C=conejo  L=lobo  O=oso  M=maniqui", True, (200, 210, 225))
            pantalla.blit(leyenda, (mundo_x + 12, mundo_y + 12))

        # Dibujar Hitboxes si está activada la visualización [H]
        if mostrar_hitboxes:
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
        dist_centro = rel.length()
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
            f"Posición: ({rel.x:.0f}, {rel.y:.0f})  |  Distancia al centro: {dist_centro:.0f} / {RADIO_MUNDO}  |  Rocas: {len(rocas)}  |  Charcos: {len(charcos)}{txt_agua}{txt_oculto}",
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

        pygame.display.flip()

    pygame.quit()
    return motivo_salida
