import math
import random
import pygame
from personaje import Personaje
from habilidades import dibujar_panel_habilidades, dibujar_badge_ayuda, dibujar_tooltip
from herramientas import EspadaLigera
from vegetacion import SistemaVegetacion, OSCURECIMIENTO

# -----------------------------
# CONFIGURACIÓN DEL MAPA
# -----------------------------
RADIO_MUNDO = 5000          # Límite circular del mapa
MARGEN_MUNDO = 150          # Espacio extra alrededor del círculo (zona oscura fuera del mapa)
TAMANO_MUNDO = (RADIO_MUNDO + MARGEN_MUNDO) * 2
CENTRO_MUNDO = pygame.Vector2(RADIO_MUNDO + MARGEN_MUNDO, RADIO_MUNDO + MARGEN_MUNDO)

MIN_ROCAS = 100
MAX_ROCAS = 250
MIN_CHARCOS = 4
MAX_CHARCOS = 6
RADIO_CHARCO_MIN = 100
RADIO_CHARCO_MAX = 500
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
        extension = radio + ANCHO_BARRO + 2
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

    def contiene(self, punto):
        """True si el punto (centro del jugador) está sobre el agua."""
        return any((punto - c).length() <= r for c, r in self.circulos)

    def en_zona_peligro(self, punto):
        """True si el punto está en la zona central peligrosa de un lago grande."""
        return self.es_lago_profundo and (punto - self.centro).length() <= self.radio_peligro

    def dibujar(self, pantalla, desplazamiento):
        pantalla.blit(self.superficie, (self.rect.x - desplazamiento[0], self.rect.y - desplazamiento[1]))


def generar_charcos():
    """Genera de 4 a 6 charcos con radio aleatorio de 100 a 500 dentro del círculo, sin solaparse."""
    charcos = []
    objetivo = random.randint(MIN_CHARCOS, MAX_CHARCOS)
    intentos = 0
    while len(charcos) < objetivo and intentos < 1000:
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
class Roca:
    def __init__(self, x, y, lado):
        self.rect = pygame.Rect(round(x - lado / 2), round(y - lado / 2), lado, lado)
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
    Genera entre 100 y 250 rocas (pequeñas, grandes y gigantes) dentro del círculo, sin solaparse
    ni caer sobre zonas ocupadas (charcos, arbustos: cualquier objeto con .rect).
    """
    charcos = zonas_ocupadas
    cantidad = random.randint(MIN_ROCAS, MAX_ROCAS)
    rocas = []
    intentos = 0

    while len(rocas) < cantidad and intentos < 8000:
        intentos += 1

        # 60% pequeñas (22-45), 35% grandes (70-130), 5% gigantes (150-300)
        r = random.random()
        if r < 0.60:
            lado = random.randint(22, 45)
        elif r < 0.95:
            lado = random.randint(70, 130)
        else:
            lado = random.randint(150, 300)
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

        # Evitar solapamiento (con un pequeño hueco para poder pasar entre rocas)
        if any(nueva.rect.inflate(30, 30).colliderect(r.rect) for r in rocas):
            continue

        # No colocar rocas dentro de los charcos
        if any(nueva.rect.inflate(20, 20).colliderect(c.rect) for c in charcos):
            continue

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

    # Mini tarjeta de avatar con ángulo de orientación
    avatar_y = y + 68
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
    arma_h = 84
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
            pct_deb = int(round(arma.debuff_velocidad * 100))
            txt_est_arma = fuente_mini.render(f"DESENFUNDADA (-{pct_deb}% Vel)", True, (255, 130, 80))
            dano_arma = arma.calcular_dano(jugador)
            txt_dano = fuente_mini.render(f"Daño: {dano_arma:.1f} (Fza x{arma.multiplicador_dano:.1f})", True, (255, 215, 0))
        else:
            txt_est_arma = fuente_mini.render("GUARDADA (Pulsa [1])", True, (140, 150, 170))
            txt_dano = fuente_mini.render(f"Daño: Fuerza x{arma.multiplicador_dano:.1f}", True, (180, 160, 90))

        pantalla.blit(txt_est_arma, (x + 20, arma_y + 25))
        pantalla.blit(txt_dano, (x + 20, arma_y + 40))

        # Barra de durabilidad
        txt_dur = fuente_mini.render(f"Durabilidad: {arma.durabilidad}/{arma.durabilidad_max}", True, (150, 160, 180))
        pantalla.blit(txt_dur, (x + 20, arma_y + 55))
        bw = ancho - 40
        prog_dur = max(0.0, min(1.0, arma.durabilidad / max(1, arma.durabilidad_max)))
        col_dur = (100, 220, 120) if prog_dur > 0.5 else ((230, 200, 70) if prog_dur > 0.2 else (230, 90, 70))
        pygame.draw.rect(pantalla, (40, 45, 55), (x + 20, arma_y + 71, bw, 6), border_radius=3)
        if not arma.roto and prog_dur > 0:
            pygame.draw.rect(pantalla, col_dur, (x + 20, arma_y + 71, int(bw * prog_dur), 6), border_radius=3)

    # Lista de Estadísticas
    offset_y = arma_y + 96
    pct_vel = int(round((jugador.velocidad / jugador.velocidad_base - 1.0) * 100))
    str_pct = f" ({pct_vel:+d}%)" if pct_vel != 0 else ""

    # Cada stat: (etiqueta, valor, color, clave_mejora). clave None = no se puede subir.
    stats = [
        ("Tamaño (Nivel)", f"{jugador.tamano}", (200, 220, 255), None),
        ("Vida", f"{jugador.vida} / {jugador.vida_max}", (255, 95, 95), "vida"),
        ("Fuerza Base", f"{jugador.fuerza_base:.1f}", (200, 190, 180), "fuerza"),
        ("Fuerza Actual", f"{jugador.fuerza:.2f}", (255, 120, 60) if jugador.fuerza > jugador.fuerza_base else (220, 220, 220), None),
        ("Velocidad Base", f"{jugador.velocidad_base:.1f}", (170, 190, 210), "velocidad"),
        ("Velocidad Actual", f"{jugador.velocidad:.2f}{str_pct}", (90, 220, 255) if pct_vel > 0 else ((255, 100, 70) if pct_vel < 0 else (220, 220, 220)), None),
        ("Energía", f"{jugador.energia} / {jugador.energia_max}", (180, 130, 255), "energia"),
        ("Defensa", f"{jugador.defensa}", (120, 255, 150), "defensa")
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

    # Pie de página con indicadores
    txt_lvl = fuente_mini.render("[L] subir nivel · [J] golpe (debug)", True, (150, 200, 255))
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
            "Fuerza: base del daño del arma.",
            "Velocidad: desplazamiento; cambia con agua, arma y Destello.",
            "Energía: coste de habilidades. Regenera +1 cada 3s parado, cada 6s en movimiento.",
            "Defensa: reduce el daño recibido.",
            "",
            "Mejora con [+]: cuesta 1 punto (el arma cuesta 2).",
            "[L] sube de nivel y otorga 3 puntos.",
        ]
        dibujar_tooltip(pantalla, x + ancho + 6, y + 40, "Estadísticas",
                        lineas_info, fuente_sub, fuente_mini)

    return botones


# -----------------------------
# EJECUCIÓN PRINCIPAL DEL MUNDO (PYGAME)
# -----------------------------
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
    ancho_panel_der = 240

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
    rocas = generar_rocas(list(charcos) + vegetacion.arbustos)
    vegetacion.registrar_obstaculos(rocas)

    # Capa oscura para simular la poca visibilidad dentro de un arbusto
    capa_oscura = pygame.Surface((mundo_w, mundo_h), pygame.SRCALPHA)
    capa_oscura.fill((0, 0, 0, OSCURECIMIENTO))

    # Instanciar personaje en el centro del mapa
    jugador = Personaje(
        nombre=config.get("nombre", "Héroe"),
        x=CENTRO_MUNDO.x,
        y=CENTRO_MUNDO.y,
        tamano=config.get("tamano", 1),
        velocidad=config.get("velocidad", 3),
        vida=config.get("vida", 20),
        fuerza=config.get("fuerza", 3),
        energia=config.get("energia", 80),
        defensa=config.get("defensa", 5),
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
        "nombre": pygame.font.SysFont("Segoe UI", 11, bold=True)
    }

    reloj = pygame.time.Clock()
    ejecutando = True
    mostrar_hitboxes = False  # Alternable con la tecla [H]
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

    while ejecutando:
        dt = reloj.tick(60) / 1000.0  # Delta time en segundos

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    ejecutando = False

                # [H] Alternar visualización de hitboxes para depuración
                elif evento.key == pygame.K_h:
                    mostrar_hitboxes = not mostrar_hitboxes

                # [1] Exclusivo para Herramientas (Espada Ligera sacar/guardar)
                elif evento.key == pygame.K_1:
                    if jugador.herramienta:
                        jugador.herramienta.toggle()

                # [L] (debug) Subir de nivel: otorga 3 puntos de mejora
                elif evento.key == pygame.K_l:
                    jugador.subir_nivel()

                # [J] (debug) Simular un golpe del arma (desgasta 1) para probar la rotura
                elif evento.key == pygame.K_j:
                    if jugador.herramienta:
                        jugador.herramienta.desgastar()

                # Teclas dinámicas [2], [3] y [4] para Habilidades
                else:
                    for hab in jugador.habilidades:
                        if evento.key == hab.tecla:
                            hab.intentar_activar(jugador)

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
                        if jugador.puntos_mejora > 0 and 0 <= indice < len(jugador.habilidades):
                            if jugador.habilidades[indice].subir_nivel():
                                jugador.puntos_mejora -= 1
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

        # Actualizar herramienta (temporizador y cálculo de su hitbox)
        if jugador.herramienta:
            jugador.herramienta.actualizar(dt, jugador)

        # Actualizar proyectiles disparados (Disparo Veloz) — chocan con las rocas
        jugador.actualizar_proyectiles(dt, limites_mundo, rocas)
        # Los proyectiles desaparecen al salir del círculo del mapa
        jugador.proyectiles = [
            p for p in jugador.proyectiles
            if (p.posicion - CENTRO_MUNDO).length() <= RADIO_MUNDO + p.radio
        ]

        # Actualizar regeneración global de energía
        jugador.actualizar_regeneracion(dt)

        # Actualizar todas las habilidades equipadas
        for hab in jugador.habilidades:
            hab.actualizar(dt, jugador)

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

        # Calcular velocidad acumulando debuffs y buffs
        jugador.actualizar_velocidad()

        # Mover personaje respetando el círculo del mapa y las rocas
        jugador.mover(limites_mundo, CENTRO_MUNDO, RADIO_MUNDO, rocas, vegetacion.obstaculos_para(jugador))

        # Arbustos: ocultarse, veneno, orbes de curación y reaparición de frutales
        vegetacion.actualizar(dt, jugador)

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
        pantalla.set_clip(area_mundo_pantalla)

        dibujar_suelo(pantalla, vista, desplazamiento)

        for charco in charcos:
            if charco.rect.colliderect(vista):
                charco.dibujar(pantalla, desplazamiento)

        for roca in rocas:
            if roca.rect.colliderect(vista):
                roca.dibujar(pantalla, desplazamiento)

        # Dibujar personaje, auras interiores, herramienta rotada y proyectiles
        jugador.dibujar(pantalla, fuentes["nombre"], desplazamiento)

        # Arbustos por encima de los personajes (el que te oculta se ve semitransparente)
        vegetacion.dibujar(pantalla, vista, desplazamiento, jugador)

        # Dentro de un arbusto: el mapa se oscurece y solo tú ves los orbes de tu arbusto
        if jugador.oculto:
            pantalla.blit(capa_oscura, (mundo_x, mundo_y))
            vegetacion.dibujar_interior(pantalla, desplazamiento, jugador)

        # Dibujar Hitboxes si está activada la visualización [H]
        if mostrar_hitboxes:
            ox, oy = desplazamiento
            # Arbustos con su tipo revelado (solo en modo depuración)
            vegetacion.dibujar_hitboxes(pantalla, vista, desplazamiento, fuentes["mini"])

            # Hitbox del personaje (rectángulo verde brillante y círculo exterior)
            pygame.draw.rect(pantalla, (0, 255, 120), jugador.hitbox.move(-ox, -oy), 1)
            pygame.draw.circle(pantalla, (0, 255, 120), (round(jugador.posicion.x - ox), round(jugador.posicion.y - oy)), jugador.radio, 1)

            # Hitbox de la espada si está desenfundada (rectángulo amarillo)
            if jugador.herramienta and jugador.herramienta.activa and jugador.herramienta.hitbox:
                pygame.draw.rect(pantalla, (255, 235, 50), jugador.herramienta.hitbox.move(-ox, -oy), 1)

            # Hitbox de cada proyectil activo (rectángulo rojo)
            for p in jugador.proyectiles:
                if p.hitbox:
                    pygame.draw.rect(pantalla, (255, 70, 70), p.hitbox.move(-ox, -oy), 1)

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
        txt_oculto = "  |  OCULTO EN ARBUSTO" if jugador.oculto else ""
        if jugador.oculto:
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

        # 2. Dibujar Interfaces Laterales (Fuera del mundo)
        # Panel Izquierdo: Ficha del Personaje y Estado del Arma
        botones_stats = dibujar_panel_estadisticas(pantalla, 0, 0, ancho_panel_izq, alto_pantalla, jugador, fuentes, mostrar_hitboxes, info_abierta)

        # Panel Derecho: Habilidades y Manual (sus botones [+] se suman a los del panel izquierdo)
        botones_hab = dibujar_panel_habilidades(pantalla, ancho_pantalla - ancho_panel_der, 0, ancho_panel_der, alto_pantalla, jugador.habilidades, jugador, fuentes, info_abierta)
        if botones_hab:
            botones_stats.update(botones_hab)

        pygame.display.flip()

    pygame.quit()
