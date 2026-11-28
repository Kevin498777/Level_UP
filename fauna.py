# -*- coding: utf-8 -*-
"""
Fauna ambiental del mundo (FASE 1): sin colision, pura vida visual.

- Mariposas y luciernagas que revolotean sobre praderas y flores.
- Pajaros posados en los arboles que alzan vuelo si el jugador se acerca.
- Peces como sombras bajo el agua de los lagos.

Todo se actualiza y dibuja solo cerca de la camara (culling por 'vista') para
no afectar el rendimiento aunque el mundo sea enorme.
"""

import math
import random
import pygame
from habilidades import aplicar_desangrado, factor_dano_corrosion, actualizar_ralentizacion, ralentizacion_total
from personaje import repartir_dano, REGEN_ESCUDO_RETRASO, REGEN_ESCUDO_POR_SEGUNDO
from talismanes import marcar_agresor

# Margen extra (px) alrededor de la vista para activar/mantener la fauna.
MARGEN_CULL = 90
PIXELES_POR_PUNTO_EMPUJE = 6   # igual que en el juego: puntos de arma -> px de empuje

# Experiencia que da cada animal al morir a manos del jugador o de sus invocaciones
# (Documentacion/sistema_xp.md). Lo que matan los depredadores salvajes no da XP.
XP_CONEJO = 0.5
XP_VENADO = 2.0
XP_ZORRO = 3.0
XP_JABALI = 5.0
XP_COCODRILO = 10.0
XP_OSO = 15.0
XP_ORBE_CUEVA = 2.0          # al recoger el orbe de vida de la cueva de un oso
XP_ORBE_XP = 5.0             # orbe de XP de la cueva del oso
PROB_ORBE_GACHA = 0.5        # probabilidad de que el oso deje además un orbe Gacha (ruleta de anillos)
XP_LOBO = 5.0
XP_LOBO_ALFA = 8.0
XP_MANADA_COMPLETA = 3.0     # bono al acabar con toda la manada (alfa incluido)

# Monedas al morir (mismas reglas que la XP): (probabilidad, minimo, maximo). La cantidad es un
# entero al azar entre minimo y maximo. Por ahora no se gastan y se pierden al morir.
MONEDAS_CONEJO = (0.05, 1, 1)
MONEDAS_VENADO = (0.25, 1, 2)
MONEDAS_ZORRO = (0.40, 1, 3)
MONEDAS_JABALI = (0.70, 2, 5)
MONEDAS_LOBO = (1.0, 5, 10)
MONEDAS_LOBO_ALFA = (1.0, 7, 10)
MONEDAS_COCODRILO = (1.0, 6, 12)
MONEDAS_OSO = (1.0, 8, 12)

# Reaparicion de fauna (sin pasar nunca el maximo de cada especie)
LOBO_REAPARICION = 60.0      # cada 60 s la manada crece +1 lobo (hasta 4)
LOBO_REAPARECEN = 2          # si la manada fue exterminada, otra se inicia con 2 lobos en otro bosque
MANADA_DIST_NUEVA = 1500.0   # la manada nueva aparece al menos a esta distancia de la anterior
OSO_REAPARICION = 180.0      # 3 min despues de morir aparece un oso nuevo en su cueva
ZORRO_REAPARICION = 180.0    # cada 3 min aparece un zorro nuevo en el mundo
ZORRO_REPRO_INTERVALO = 120.0  # cada 2 min nace +1 si hay al menos 2 zorros


# Golpe de arma del jugador a un animal: retrasa su siguiente ataque (y no se encadena)
ATURDIR_GOLPE = 0.3          # s de retraso del siguiente ataque del animal
ATURDIR_INMUNE = 1.0         # s sin poder volver a aturdirlo
SALTO_MAX_FRENADO = 200.0    # px: un desplazamiento mayor entre frames (reaparicion) no se frena
# Jardin de la casa del spawn: (centro, radio) donde ningun animal puede entrar (lo fija mundo)
ZONA_PROHIBIDA = None
# Lo que matan los NPC se regenera este numero de veces mas rapido (sin pasar los maximos)
RITMO_TRAS_NPC = 5


def bloqueado_por_escudo(atacante, objetivo, dano):
    """Si el objetivo lleva el Escudo desenfundado cubriendo al atacante, bloquea el golpe o
    la mordida entera (igual que con el maniqui): sin dano ni efectos, el portador recibe el
    empuje del escudo y el atacante sale repelido con el empuje del escudo. True si bloqueo."""
    marcar_agresor(objetivo, atacante)     # las sombras de los anillos defienden al atacado
    bloquear = getattr(objetivo, "bloquear_con_escudo", None)
    if bloquear is None or dano <= 0 or not bloquear(dano, atacante.posicion):
        return False
    atacante.aplicar_empuje(atacante.posicion - objetivo.posicion, objetivo.herramienta.puntos_empuje)
    return True


def golpear_objetivo(atacante, objetivo, dano, empuje=0):
    """Golpe de un animal (mordida, embestida, zarpazo). Devuelve True si el golpe entra.
    No entra si el objetivo esta invulnerable tras otro golpe o si lo bloquea su Escudo.
    Empuje: con 'empuje' > 0 el objetivo retrocede solo esos puntos (el empuje propio del
    animal); con 0 retrocede 1 punto por punto de dano (el de recibir_dano). Nunca ambos."""
    if getattr(objetivo, "invulnerable", False):
        return False
    if bloqueado_por_escudo(atacante, objetivo, dano):
        return False
    if not hasattr(objetivo, "recibir_dano"):
        return False
    hacia = objetivo.posicion - atacante.posicion
    dano = round(dano * factor_dano_corrosion(atacante), 2)     # Corrosion: pega menos
    if hasattr(objetivo, "_golpe_de_fauna"):
        objetivo._golpe_de_fauna = True     # vendedor: si muere de este golpe no da recompensa
    objetivo.recibir_dano(dano, "fisico", None if empuje > 0 else hacia)
    if hasattr(objetivo, "_golpe_de_fauna"):
        objetivo._golpe_de_fauna = False
    if empuje > 0 and hasattr(objetivo, "aplicar_empuje"):
        objetivo.aplicar_empuje(hacia, empuje)
    if hasattr(objetivo, "marcar_golpe"):
        objetivo.marcar_golpe()             # invulnerabilidad breve del jugador
    return True


# =====================================================================
# MARIPOSAS / LUCIERNAGAS  (poblacion dinamica alrededor de la camara)
# =====================================================================
MARIPOSA_MAX = 6              # tope de mariposas visibles a la vez
MARIPOSA_VEL = 26.0            # px/s de deambular
PROB_LUCIERNAGA = 0.22         # fraccion que son luciernagas (volando, sin noche)
MARIPOSA_COLORES = [
    (245, 245, 235), (250, 210, 70), (240, 140, 50),
    (95, 155, 230), (230, 120, 180), (250, 250, 250),
]

_GLOW = None


def _glow_luciernaga():
    """Halo ambar pre-renderizado para las luciernagas."""
    global _GLOW
    if _GLOW is None:
        r = 7
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for rad, a in ((7, 35), (5, 70), (3, 130)):
            pygame.draw.circle(s, (255, 220, 120, a), (r, r), rad)
        _GLOW = s
    return _GLOW


class Mariposa:
    def __init__(self, x, y):
        self.centro = pygame.Vector2(x, y)
        self.luciernaga = random.random() < PROB_LUCIERNAGA
        self.color = (255, 215, 120) if self.luciernaga else random.choice(MARIPOSA_COLORES)
        self.dir = random.uniform(0, math.tau)
        self.vel = MARIPOSA_VEL * random.uniform(0.7, 1.3)
        self.fase = random.uniform(0, math.tau)
        self._t_giro = random.uniform(0.3, 1.0)

    def actualizar(self, dt):
        self._t_giro -= dt
        if self._t_giro <= 0:
            self.dir += random.uniform(-1.2, 1.2)
            self._t_giro = random.uniform(0.3, 1.0)
        self.fase += dt * 13.0
        self.centro.x += math.cos(self.dir) * self.vel * dt
        self.centro.y += math.sin(self.dir) * self.vel * dt
        self.centro.y += math.sin(self.fase * 0.3) * 6 * dt  # flotar vertical

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        if self.luciernaga:
            glow = _glow_luciernaga()
            pantalla.blit(glow, (px - glow.get_width() // 2, py - glow.get_height() // 2))
            pygame.draw.circle(pantalla, self.color, (px, py), 2)
            return
        # Mariposa: dos alas cuyo ancho oscila (aleteo)
        ancho = 2 + int(abs(math.sin(self.fase)) * 3)
        pygame.draw.ellipse(pantalla, self.color, (px - ancho, py - 3, ancho, 6))
        pygame.draw.ellipse(pantalla, self.color, (px, py - 3, ancho, 6))
        pygame.draw.line(pantalla, (45, 38, 32), (px, py - 3), (px, py + 3), 1)


# =====================================================================
# PAJAROS  (anclados a un arbol; vuelan si te acercas y regresan)
# =====================================================================
PAJARO_PROB = 0.20             # fraccion de arboles con pajaro
PAJARO_SUSTO = 120.0           # px: distancia a la que alzan vuelo
PAJARO_VEL_VUELO = 150.0       # px/s
PAJARO_COLORES = [(45, 40, 38), (28, 28, 34), (95, 65, 45)]


class Pajaro:
    def __init__(self, arbol):
        self.arbol = arbol
        self.base = pygame.Vector2(arbol.centro.x, arbol.centro.y - arbol.radio_copa + 2)
        self.centro = pygame.Vector2(self.base)
        self.estado = "posado"   # posado / huyendo / regresando
        self.color = random.choice(PAJARO_COLORES)
        self.fase = random.uniform(0, math.tau)
        self.vel_vuelo = pygame.Vector2()
        self._t = 0.0

    def _huir(self, jugador):
        self.estado = "huyendo"
        hacia = self.centro - jugador.posicion
        if hacia.length() < 1:
            hacia = pygame.Vector2(0, -1)
        self.vel_vuelo = hacia.normalize() * PAJARO_VEL_VUELO
        self.vel_vuelo.y -= 50   # sesgo hacia arriba
        self._t = random.uniform(1.5, 2.5)

    def actualizar(self, dt, jugador):
        self.fase += dt * 15.0
        dist = (jugador.posicion - self.base).length()
        if self.estado == "posado":
            if dist < PAJARO_SUSTO:
                self._huir(jugador)
        elif self.estado == "huyendo":
            self.centro += self.vel_vuelo * dt
            self.vel_vuelo *= max(0.0, 1 - dt * 0.8)
            self._t -= dt
            if self._t <= 0 and dist > PAJARO_SUSTO * 1.6:
                self.estado = "regresando"
        elif self.estado == "regresando":
            if dist < PAJARO_SUSTO:
                self._huir(jugador)
            else:
                d = self.base - self.centro
                if d.length() <= 5:
                    self.centro.update(self.base)
                    self.estado = "posado"
                else:
                    self.centro += d.normalize() * PAJARO_VEL_VUELO * dt

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        if self.estado == "posado":
            pygame.draw.ellipse(pantalla, self.color, (px - 6, py - 4, 12, 8))
            pygame.draw.circle(pantalla, self.color, (px + 6, py - 4), 3)
        else:
            a = 4 + int(abs(math.sin(self.fase)) * 6)
            pygame.draw.line(pantalla, self.color, (px, py), (px - 9, py - a), 3)
            pygame.draw.line(pantalla, self.color, (px, py), (px + 9, py - a), 3)


# =====================================================================
# PECES  (sombras bajo el agua; se dispersan si entras al agua cerca)
# =====================================================================
PEZ_MIN_RADIO_LAGO = 120.0     # solo lagos de este radio o mas
PEZ_VEL = (16.0, 32.0)


class Pez:
    def __init__(self, charco):
        self.charco = charco
        ang = random.uniform(0, math.tau)
        r = random.uniform(0, max(0.0, charco.radio * 0.6))
        self.centro = pygame.Vector2(charco.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
        self.dir = random.uniform(0, math.tau)
        self.vel = random.uniform(*PEZ_VEL)
        self.largo = random.uniform(9, 16)
        self._t_giro = random.uniform(0.5, 1.5)

    def actualizar(self, dt, jugador):
        self._t_giro -= dt
        if self._t_giro <= 0:
            self.dir += random.uniform(-0.8, 0.8)
            self._t_giro = random.uniform(0.5, 1.5)
        vel = self.vel
        dist = (jugador.posicion - self.centro).length()
        if getattr(jugador, "en_agua", False) and dist < 95:
            self.dir = math.atan2(self.centro.y - jugador.posicion.y,
                                  self.centro.x - jugador.posicion.x)
            vel = self.vel * 2.3
        nuevo = pygame.Vector2(self.centro.x + math.cos(self.dir) * vel * dt,
                               self.centro.y + math.sin(self.dir) * vel * dt)
        if (nuevo - self.charco.centro).length() > self.charco.radio - 10:
            self.dir += math.pi   # rebote hacia dentro del lago
        else:
            self.centro.update(nuevo)

    def dibujar(self, pantalla, desplazamiento):
        px = self.centro.x - desplazamiento[0]
        py = self.centro.y - desplazamiento[1]
        L = max(6, int(self.largo))
        W = max(4, int(self.largo * 0.5))
        surf = pygame.Surface((L, W), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (10, 25, 40, 85), (0, 0, L, W))
        surf = pygame.transform.rotate(surf, -math.degrees(self.dir))
        pantalla.blit(surf, surf.get_rect(center=(round(px), round(py))))


# =====================================================================
# SISTEMA DE FAUNA
# =====================================================================

# =====================================================================
# RANAS  (orilla de lagos; saltitos y brinco al agua si te acercas)
# =====================================================================
RANA_SUSTO = 72.0              # px: distancia a la que saltan al agua
RANA_COLORES = [(70, 130, 60), (90, 155, 72), (58, 110, 55)]


class Rana:
    def __init__(self, charco):
        self.charco = charco
        self.color = random.choice(RANA_COLORES)
        self._colocar_en_orilla()
        self.estado = "quieta"          # quieta / saltando / sumergida
        self._espera = random.uniform(1.2, 3.5)
        self._origen = pygame.Vector2(self.centro)
        self._destino = pygame.Vector2(self.centro)
        self._tt = 0.0
        self._dur = 0.28
        self._sumergir = False

    def _colocar_en_orilla(self):
        nen = getattr(self.charco, "nenufares", None)
        if nen and random.random() < 0.5:
            c, _r = random.choice(nen)
            self.centro = pygame.Vector2(c)
            self.en_nenufar = True
            return
        ang = random.uniform(0, math.tau)
        r = max(0.0, self.charco.radio - random.uniform(4, 14))
        self.centro = pygame.Vector2(self.charco.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
        self.en_nenufar = False

    def _saltar(self, destino, sumergir=False):
        self._origen = pygame.Vector2(self.centro)
        self._destino = destino
        self._tt = 0.0
        self._sumergir = sumergir
        self.estado = "saltando"

    def actualizar(self, dt, jugador):
        dist = (jugador.posicion - self.centro).length()
        if self.estado == "sumergida":
            self._espera -= dt
            if self._espera <= 0 and dist > RANA_SUSTO * 1.6:
                self._colocar_en_orilla()
                self.estado = "quieta"
                self._espera = random.uniform(1.2, 3.5)
            return
        if self.estado == "quieta":
            if dist < RANA_SUSTO:
                hacia = self.charco.centro - self.centro
                paso = hacia.normalize() * 28 if hacia.length() > 1 else pygame.Vector2(0, -20)
                self._saltar(self.centro + paso, sumergir=True)
            else:
                self._espera -= dt
                if self._espera <= 0:
                    ang = random.uniform(0, math.tau)
                    destino = self.centro + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(6, 16)
                    if (destino - self.charco.centro).length() > self.charco.radio:
                        destino = pygame.Vector2(self.centro)
                    self._saltar(destino)
                    self._espera = random.uniform(1.2, 3.5)
        elif self.estado == "saltando":
            self._tt += dt
            t = min(1.0, self._tt / self._dur)
            self.centro = self._origen.lerp(self._destino, t)
            if t >= 1.0:
                if self._sumergir:
                    self.estado = "sumergida"
                    self._espera = random.uniform(2.5, 4.5)
                else:
                    self.estado = "quieta"

    def dibujar(self, pantalla, desplazamiento):
        if self.estado == "sumergida":
            return
        alto = 0.0
        if self.estado == "saltando":
            alto = math.sin(min(1.0, self._tt / self._dur) * math.pi) * 7
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1] - alto)
        pygame.draw.ellipse(pantalla, self.color, (px - 5, py - 3, 10, 6))
        pygame.draw.circle(pantalla, self.color, (px - 3, py - 4), 2)
        pygame.draw.circle(pantalla, self.color, (px + 3, py - 4), 2)
        pygame.draw.circle(pantalla, (15, 20, 15), (px - 3, py - 4), 1)
        pygame.draw.circle(pantalla, (15, 20, 15), (px + 3, py - 4), 1)


# =====================================================================
# COFRE  (collectible escondido entre la vegetacion; por mundo, no reaparece)
# =====================================================================
COFRE_MIN = 20
COFRE_MAX = 40
COFRE_MONEDAS = 5
COFRE_XP = 2
COFRE_RADIO = 12


class Cofre:
    """Cofre escondido entre arboles y arbustos: al tocarlo da COFRE_MONEDAS y COFRE_XP una
    sola vez. No reaparece (hay entre COFRE_MIN y COFRE_MAX por mundo)."""
    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = COFRE_RADIO
        self.abierto = False

    def intentar_abrir(self, jugador):
        if self.abierto:
            return False
        if (jugador.posicion - self.posicion).length() <= self.radio + jugador.radio:
            self.abierto = True
            return True
        return False

    def dibujar(self, pantalla, desplazamiento):
        if self.abierto:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        pygame.draw.rect(pantalla, (120, 82, 45), (px - 9, py - 4, 18, 11), border_radius=2)
        pygame.draw.rect(pantalla, (150, 104, 60), (px - 9, py - 9, 18, 6), border_radius=2)
        pygame.draw.rect(pantalla, (70, 48, 28), (px - 9, py - 9, 18, 16), 1, border_radius=2)
        pygame.draw.rect(pantalla, (235, 200, 90), (px - 2, py - 7, 4, 8))
        pygame.draw.circle(pantalla, (255, 230, 130), (px, py - 3), 1)


def marcar_cuevas(rocas, diseno=None, limite=None):
    """Elige las cuevas de oso entre las rocas gigantes, las marca con es_cueva (nada puede
    destruirlas) y les da la direccion de su entrada. Devuelve la lista. Sin diseno (o si no fija
    cuevas): OSO_MIN a OSO_MAX al azar. Con diseno: 'cuevas' en total, con un minimo por region
    ('cuevas_por_region') y separadas al menos 'separacion_cuevas' px."""
    # las piedras especiales de montaña (indestructibles) no son cuevas
    gigantes = [r for r in rocas if getattr(r, "gigante", False) and not getattr(r, "indestructible", False)]
    random.shuffle(gigantes)
    if diseno is None or diseno.cuevas is None:
        cuevas = gigantes[:min(len(gigantes), random.randint(OSO_MIN, OSO_MAX))]
    else:
        cuevas = []
        centro = lambda r: pygame.Vector2(r.rect.center)
        separada = lambda r: all((centro(r) - centro(c)).length() >= diseno.separacion_cuevas for c in cuevas)
        for region, minimo in diseno.cuevas_por_region.items():
            for r in gigantes:
                if sum(diseno.region_de(*limite.relativo(c.rect.center)) == region for c in cuevas) >= minimo:
                    break
                if r not in cuevas and diseno.region_de(*limite.relativo(r.rect.center)) == region and separada(r):
                    cuevas.append(r)
        for r in gigantes:
            if len(cuevas) >= diseno.cuevas:
                break
            if r not in cuevas and separada(r):
                cuevas.append(r)
    for r in cuevas:
        r.es_cueva = True
        r.angulo_entrada = random.uniform(0, math.tau)
    return cuevas


class SistemaFauna:
    def __init__(self, limite, vegetacion, charcos, rocas=()):
        self.limite = limite                 # cuadrado del mapa (limite_mundo.LimiteMundo)
        self.centro_mundo = pygame.Vector2(limite.centro)
        self.vegetacion = vegetacion
        self.charcos = charcos
        self.rocas = list(rocas)
        self.deuda_npc = {}                 # especie -> animales que mataron los NPC sin reponer
        self._rocas_mundo = rocas          # lista viva: Cortar puede destruir rocas (cuevas)
        self.mariposas = []
        self.xp_pendiente = 0.0            # XP ganada por el jugador y aun no entregada
        self.ruletas_pendientes = 0        # orbes Gacha recogidos (ruleta de anillos por girar)
        self.monedas_pendientes = 0        # monedas ganadas y aun no entregadas

        # Pajaros: una fraccion de los arboles existentes.
        self.pajaros = [Pajaro(a) for a in vegetacion.arboles if random.random() < PAJARO_PROB]

        # Peces: 2 a 5 por lago mediano/grande.
        self.peces = []
        for c in charcos:
            if c.radio >= PEZ_MIN_RADIO_LAGO:
                n = min(5, max(2, int(c.radio / 120)))
                self.peces.extend(Pez(c) for _ in range(n))

        # Ranas: 1 a 3 por lago mediano/grande.
        self.ranas = []
        for c in charcos:
            if c.radio >= PEZ_MIN_RADIO_LAGO:
                self.ranas.extend(Rana(c) for _ in range(random.randint(1, 3)))

        # Madrigueras de conejos salvajes en el pasto alto (10 a 15 en el mundo).
        self.madrigueras = []
        self.conejos = []
        self._zonas_madriguera = list(getattr(vegetacion, "pastizales", [])) or list(getattr(vegetacion, "praderas", []))
        if self._zonas_madriguera:
            for _ in range(random.randint(MADRIGUERAS_MIN, MADRIGUERAS_MAX)):
                self._nueva_madriguera()

        # Venados: poblacion global repartida por el mundo (hasta VENADO_MAX).
        self.venados = [self._nuevo_venado() for _ in range(VENADO_MAX)]
        self._t_repro_venado = 0.0

        # Jabalies y zorros: poblacion global repartida por el mundo.
        self.jabalies = [self._nuevo_jabali() for _ in range(JABALI_MAX)]
        self._t_repro_jabali = 0.0
        self.zorros = [self._nuevo_zorro() for _ in range(ZORRO_MAX)]
        self._t_reap_zorro = 0.0
        self._t_repro_zorro = 0.0

        # Manadas de lobos (7 por mundo), en los bosques.
        self.manadas = []
        self._bosques = list(getattr(vegetacion, "bosques_fauna", None) or getattr(vegetacion, "bosques", []))
        for _ in range(LOBO_MANADAS):
            self.manadas.append(Manada(self._centro_manada()))

        # Osos: uno por cueva. Las cuevas son parte del terreno (mundo.generar_terreno las marca
        # con la semilla fija); si nadie las marco (terreno hecho a mano en pruebas), se eligen aqui.
        self.rugidos = []
        cuevas = [r for r in self.rocas if getattr(r, "es_cueva", False)] or marcar_cuevas(self.rocas)
        self.osos = [Oso(r) for r in cuevas]

        # Cocodrilos: 2 por lago profundo; 3 si el lago es muy grande (radio >= COCODRILO_LAGO_GRANDE).
        self.cocodrilos = []
        for c in self.charcos:
            if getattr(c, "es_lago_profundo", False):
                n = COCODRILO_POR_LAGO_GRANDE if c.radio >= COCODRILO_LAGO_GRANDE else COCODRILO_POR_LAGO
                self.cocodrilos.extend(Cocodrilo(c) for _ in range(n))

        # Lobos solitarios: hostiles unicos (fuerza de alfa, su propia onda sonora).
        self.lobos_solitarios = [self._nuevo_lobo_solitario() for _ in range(LOBO_SOL_CANTIDAD)]

        # Cofres escondidos entre arboles y arbustos (por mundo, no reaparecen).
        self.cofres = []
        anclas = [a.centro for a in getattr(vegetacion, "arboles", [])] + \
                 [a.centro for a in getattr(vegetacion, "arbustos", [])]
        if anclas:
            for _ in range(random.randint(COFRE_MIN, COFRE_MAX)):
                base = random.choice(anclas); p = base
                for _intento in range(6):
                    ang = random.uniform(0, math.tau); r = random.uniform(12, 42)
                    p = base + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
                    if not any(c.contiene(p) for c in self.charcos):
                        break
                self.cofres.append(Cofre(p.x, p.y))

    def _punto_mariposa(self, zona):
        """Punto para generar una mariposa: sesgado hacia flores visibles."""
        flores = self.vegetacion.flores
        for _ in range(6):
            if flores:
                f = random.choice(flores)
                if zona.collidepoint(f.centro.x, f.centro.y):
                    return pygame.Vector2(f.centro.x + random.uniform(-25, 25),
                                          f.centro.y + random.uniform(-25, 25))
        for _ in range(6):
            p = pygame.Vector2(random.uniform(zona.left, zona.right),
                               random.uniform(zona.top, zona.bottom))
            if not self.limite.dentro(p):
                continue
            if any(c.contiene(p) for c in self.charcos):
                continue
            return p
        return None

    def actualizar(self, dt, jugador, vista, presas_hostiles=(), combatientes=()):
        """'presas_hostiles': otros objetivos que atacan los hostiles (lobos, osos, cocodrilos,
        lobos solitarios) ademas del jugador y sus sombras, p. ej. los vendedores ambulantes.
        'combatientes': otros personajes (no el jugador); como el jugador, asustan a los animales
        y los hostiles los atacan si son detectables (no ocultos ni invisibles)."""
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        # Antes de limpiar las listas: XP de los animales que murieron desde el ultimo frame.
        self._recoger_muertes()

        # Mariposas: cull de las que se alejan y repoblado alrededor de la camara.
        self.mariposas = [m for m in self.mariposas
                          if zona.collidepoint(m.centro.x, m.centro.y)]
        for m in self.mariposas:
            m.actualizar(dt)
        intentos = 0
        while len(self.mariposas) < MARIPOSA_MAX and intentos < 8:
            intentos += 1
            p = self._punto_mariposa(zona)
            if p is not None:
                self.mariposas.append(Mariposa(p.x, p.y))

        # Pajaros: solo los cercanos (por su arbol o en pleno vuelo).
        for pj in self.pajaros:
            if zona.collidepoint(pj.centro.x, pj.centro.y) or zona.collidepoint(pj.base.x, pj.base.y):
                pj.actualizar(dt, jugador)

        # Peces: solo los de lagos en vista.
        for pz in self.peces:
            if zona.collidepoint(pz.centro.x, pz.centro.y):
                pz.actualizar(dt, jugador)

        # Ranas: solo las de lagos en vista.
        for rn in self.ranas:
            if zona.collidepoint(rn.centro.x, rn.centro.y):
                rn.actualizar(dt, jugador)

        # Amenazas de las que huyen los animales: el jugador y sus sombras (invocaciones).
        amenazas = [jugador] if getattr(jugador, "detectable", True) else []
        fuentes = jugador.fuentes_criaturas() if hasattr(jugador, "fuentes_criaturas") else getattr(jugador, "habilidades", ())
        for hab in fuentes:
            for cr in getattr(hab, "criaturas", ()):
                if getattr(cr, "vivo", True):
                    amenazas.append(cr)
        for c in combatientes:
            if c.vida > 0 and getattr(c, "detectable", True):
                amenazas.append(c)
            for hab in c.fuentes_criaturas():
                amenazas.extend(cr for cr in getattr(hab, "criaturas", ()) if getattr(cr, "vivo", True))
        # Los zorros hambrientos y visibles tambien asustan a los conejos (depredador).
        for z in getattr(self, "zorros", ()):
            if z.vivo and z.hambriento and not z.invisible:
                amenazas.append(z)
        hostiles = amenazas + [p for p in presas_hostiles if zona.collidepoint(p.posicion.x, p.posicion.y)]

        # Conejos salvajes: quitar muertos y actualizar los cercanos.
        self.conejos = [c for c in self.conejos if c.vivo]
        for cn in self.conejos:
            if zona.collidepoint(cn.posicion.x, cn.posicion.y) or zona.collidepoint(cn.madriguera.centro.x, cn.madriguera.centro.y):
                cn.actualizar(dt, jugador, amenazas)
        # Reproduccion por madriguera: cada 30 s nace +1 si hay >=2 y no supera el maximo.
        for m in self.madrigueras:
            m._t_repro += dt * self._ritmo("ConejoSalvaje")
            if m._t_repro >= CONEJO_REPRO_INTERVALO:
                m._t_repro -= CONEJO_REPRO_INTERVALO
                vivos = sum(1 for c in self.conejos if c.madriguera is m)
                if 2 <= vivos < m.max_conejos:
                    self.conejos.append(ConejoSalvaje(m))
                    self._pagar("ConejoSalvaje")
        # Madriguera sin conejos: se destruye y aparece otra en otra parte del pasto alto.
        habitadas = {id(c.madriguera) for c in self.conejos}
        for i, m in enumerate(self.madrigueras):
            if id(m) not in habitadas and self._zonas_madriguera:
                self.madrigueras.pop(i)
                self._nueva_madriguera(evitar=zona)
                break                      # una por frame basta

        # Venados: quitar muertos y actualizar los cercanos.
        self.venados = [v for v in self.venados if v.vivo]
        for v in self.venados:
            if zona.collidepoint(v.posicion.x, v.posicion.y):
                v.actualizar(dt, jugador, amenazas)
        # Reproduccion: cada 60 s nace +1 si hay >=2 venados y no supera VENADO_MAX.
        self._t_repro_venado += dt * self._ritmo("Venado")
        if self._t_repro_venado >= VENADO_REPRO_INTERVALO:
            self._t_repro_venado -= VENADO_REPRO_INTERVALO
            if 2 <= len(self.venados) < VENADO_MAX:
                padre = random.choice(self.venados)
                off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
                self.venados.append(Venado(padre.posicion.x + off.x, padre.posicion.y + off.y))
                self._pagar("Venado")

        # Jabalies: quitar muertos, actualizar los cercanos, reproduccion.
        self.jabalies = [j for j in self.jabalies if j.vivo]
        for j in self.jabalies:
            if zona.collidepoint(j.posicion.x, j.posicion.y):
                j.actualizar(dt, jugador, amenazas)
        self._t_repro_jabali += dt * self._ritmo("Jabali")
        if self._t_repro_jabali >= JABALI_REPRO_INTERVALO:
            self._t_repro_jabali -= JABALI_REPRO_INTERVALO
            if 2 <= len(self.jabalies) < JABALI_MAX:
                padre = random.choice(self.jabalies)
                off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
                self.jabalies.append(Jabali(padre.posicion.x + off.x, padre.posicion.y + off.y))
                self._pagar("Jabali")

        # Zorros: quitar muertos, actualizar los cercanos (cazan conejos).
        self.zorros = [z for z in self.zorros if z.vivo]
        for z in self.zorros:
            if zona.collidepoint(z.posicion.x, z.posicion.y):
                z.actualizar(dt, jugador, amenazas, self.conejos)
        # Reaparicion (uno nuevo cada 3 min, lejos de la vista) y reproduccion (cada 2 min, con >= 2).
        self._t_reap_zorro += dt * self._ritmo("Zorro")
        if self._t_reap_zorro >= ZORRO_REAPARICION:
            self._t_reap_zorro -= ZORRO_REAPARICION
            if len(self.zorros) < ZORRO_MAX:
                self.zorros.append(self._nuevo_zorro(evitar=zona))
                self._pagar("Zorro")
        self._t_repro_zorro += dt * self._ritmo("Zorro")
        if self._t_repro_zorro >= ZORRO_REPRO_INTERVALO:
            self._t_repro_zorro -= ZORRO_REPRO_INTERVALO
            if 2 <= len(self.zorros) < ZORRO_MAX:
                padre = random.choice(self.zorros)
                off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
                self.zorros.append(Zorro(padre.posicion.x + off.x, padre.posicion.y + off.y))
                self._pagar("Zorro")

        # Manadas de lobos: crecen cada minuto (fuera de combate) y se actualizan las que
        # tienen algun lobo cerca de la camara.
        presas = [c for c in self.conejos if c.vivo] + [v for v in self.venados if v.vivo]
        for man in self.manadas:
            man._t_repro += dt * self._ritmo("Lobo")
            if man._t_repro >= LOBO_REAPARICION:
                man._t_repro -= LOBO_REAPARICION
                # Exterminada: la manada nueva se inicia en otro bosque, fuera de la vista
                otro = self._centro_manada(evitar=zona, lejos_de=man.centro) if not man.vivos() else None
                antes = sum(1 for l in man.lobos if l.vivo)
                man.repoblar(otro)
                if sum(1 for l in man.lobos if l.vivo) > antes:
                    self._pagar("Lobo")
            if any(l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y) for l in man.lobos):
                man.actualizar(dt, jugador, hostiles, presas)
            else:
                man.alertada = False     # fuera de la vista no hay combate (si no, nunca creceria)

        # Osos: un oso nuevo aparece en su cueva 3 min despues de morir el anterior (si la
        # roca sigue en pie y el jugador no esta dentro de la cueva).
        for i, oso in enumerate(self.osos):
            if oso.vivo or not oso._xp_contada:
                continue
            oso._t_reaparicion += dt * (RITMO_TRAS_NPC if getattr(oso, "ultimo_golpe_npc", False) else 1)
            if (oso._t_reaparicion >= OSO_REAPARICION and oso.roca in self._rocas_mundo
                    and (jugador.posicion - oso.entrada).length() > ENTRADA_RADIO * 2):
                self.osos[i] = oso.renacer()
        # Osos: actualizar los cercanos (y su orbe tras morir).
        for oso in self.osos:
            cerca = zona.collidepoint(oso.posicion.x, oso.posicion.y) or zona.collidepoint(oso.cueva.x, oso.cueva.y)
            if not cerca:
                continue
            if oso.vivo:
                oso.actualizar(dt, jugador, hostiles, self.charcos, self.rugidos)
            if oso.orbe is not None and oso.orbe.activo:
                oso.orbe.actualizar(dt, jugador)
                if not oso.orbe.activo:
                    self.xp_pendiente += XP_ORBE_CUEVA
            for orbe in oso.orbes_extra:
                if orbe.activo:
                    orbe.actualizar(dt, jugador)
                    if not orbe.activo:
                        if orbe.tipo == "xp":
                            self.xp_pendiente += XP_ORBE_XP
                        elif orbe.tipo == "gacha":
                            self.ruletas_pendientes += 1
        # Ondas de choque de los rugidos
        for r in self.rugidos:
            r.actualizar(dt, jugador)
        self.rugidos = [r for r in self.rugidos if r.activa]

        # Cocodrilos: emboscada acuatica (actualizar los cercanos).
        for coco in self.cocodrilos:
            if coco.vivo and (zona.collidepoint(coco.posicion.x, coco.posicion.y) or zona.collidepoint(coco.centro_lago.x, coco.centro_lago.y)):
                coco.actualizar(dt, jugador, hostiles)

        # Lobos solitarios: reaparece otro 1 min tras morir (siempre hay LOBO_SOL_CANTIDAD).
        for i, ls in enumerate(self.lobos_solitarios):
            if ls.vivo or not ls._xp_contada:
                continue
            ls._t_reaparicion += dt * (RITMO_TRAS_NPC if getattr(ls, "ultimo_golpe_npc", False) else 1)
            if ls._t_reaparicion >= LOBO_SOL_REAPARICION:
                self.lobos_solitarios[i] = self._nuevo_lobo_solitario(evitar=zona)
        for ls in self.lobos_solitarios:
            if ls.vivo and zona.collidepoint(ls.posicion.x, ls.posicion.y):
                ls.actualizar(dt, jugador, hostiles, self.rugidos)

        # Cofres escondidos: al tocarlos dan monedas + XP una vez (no reaparecen).
        for cofre in self.cofres:
            if not cofre.abierto and zona.collidepoint(cofre.posicion.x, cofre.posicion.y):
                if cofre.intentar_abrir(jugador):
                    self.monedas_pendientes += COFRE_MONEDAS
                    self.xp_pendiente += COFRE_XP

    # ---- Dibujo por capas (llamados desde el render de mundo.py) ----
    def dibujar_peces(self, pantalla, vista, desplazamiento):
        for pz in self.peces:
            if vista.collidepoint(pz.centro.x, pz.centro.y):
                pz.dibujar(pantalla, desplazamiento)

    def dibujar_ranas(self, pantalla, vista, desplazamiento):
        for rn in self.ranas:
            if vista.collidepoint(rn.centro.x, rn.centro.y):
                rn.dibujar(pantalla, desplazamiento)

    def dibujar_pajaros(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for pj in self.pajaros:
            if zona.collidepoint(pj.centro.x, pj.centro.y):
                pj.dibujar(pantalla, desplazamiento)

    def dibujar_mariposas(self, pantalla, vista, desplazamiento):
        for m in self.mariposas:
            m.dibujar(pantalla, desplazamiento)

    def _punto_venado(self, zona, jugador):
        for _ in range(8):
            p = pygame.Vector2(random.uniform(zona.left, zona.right), random.uniform(zona.top, zona.bottom))
            if not self.limite.dentro(p):
                continue
            if any(c.contiene(p) for c in self.charcos):
                continue
            if (p - jugador.posicion).length() < VENADO_SUSTO * 1.1:
                continue
            return p
        return None

    def _punto_mundo(self, evitar=None):
        """Punto al azar dentro del mundo y fuera del agua (y fuera del rect 'evitar', p. ej.
        la vista de la camara, para que lo nuevo no aparezca delante del jugador)."""
        for _ in range(20):
            p = self.limite.punto_al_azar(self.limite.mitad * 0.05)
            if any(c.contiene(p) for c in self.charcos):
                continue
            if evitar is not None and evitar.collidepoint(p.x, p.y):
                continue
            return p
        return pygame.Vector2(self.centro_mundo)

    def _centro_manada(self, evitar=None, lejos_de=None):
        """Punto dentro de un bosque al azar para una manada (fuera de 'evitar' y, si se
        puede, a mas de MANADA_DIST_NUEVA del centro anterior)."""
        centro = None
        for _ in range(15):
            if self._bosques:
                centro_b, radio_b = random.choice(self._bosques)
                ang = random.uniform(0, math.tau)
                r = random.uniform(0, max(0.0, radio_b * 0.6))
                centro = pygame.Vector2(centro_b) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
            else:
                centro = self._punto_mundo()
            if evitar is not None and evitar.collidepoint(centro.x, centro.y):
                continue
            if lejos_de is not None and (centro - lejos_de).length() < MANADA_DIST_NUEVA:
                continue
            break
        return centro

    def _nueva_madriguera(self, evitar=None):
        """Crea una madriguera en un pastizal al azar con sus conejos (2 a 10).
        Nunca cae sobre un lago/charco; si se indica, tambien evita la zona `evitar`."""
        pos = None
        respaldo = None
        for _ in range(30):
            centro_p, radio_p = random.choice(self._zonas_madriguera)
            ang = random.uniform(0, math.tau)
            r = random.uniform(0, max(0.0, radio_p * 0.7))
            p = pygame.Vector2(centro_p) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
            if any(c.contiene(p) for c in self.charcos):
                continue                      # nunca sobre el agua
            if respaldo is None:
                respaldo = p                  # primer punto fuera del agua (por si no hay mejor)
            if evitar is None or not evitar.collidepoint(p.x, p.y):
                pos = p
                break
        pos = pos or respaldo
        if pos is None:
            return None                       # todos los intentos cayeron en agua (muy raro)
        m = Madriguera(pos)
        self.madrigueras.append(m)
        for _ in range(random.randint(*CONEJOS_POR_MADRIGUERA)):
            self.conejos.append(ConejoSalvaje(m))
        return m

    def _nuevo_venado(self):
        p = self._punto_mundo()
        return Venado(p.x, p.y)

    def _nuevo_jabali(self):
        p = self._punto_mundo()
        return Jabali(p.x, p.y)

    def _nuevo_zorro(self, evitar=None):
        p = self._punto_mundo(evitar)
        return Zorro(p.x, p.y)

    def _nuevo_lobo_solitario(self, evitar=None):
        p = self._punto_mundo(evitar)
        return LoboSolitario(p.x, p.y)

    # ---- Experiencia y monedas ----
    def _contar_muerte(self, animal):
        """Suma la XP y las monedas de un animal muerto una sola vez. True si las gano el jugador."""
        if animal.vivo or animal._xp_contada:
            return False
        animal._xp_contada = True
        # Rematado por un NPC: la XP es para el NPC (no para el jugador) y su especie se
        # regenera RITMO_TRAS_NPC veces mas rapido hasta reponerlo (Fase 4)
        if getattr(animal, "ultimo_golpe_npc", False) and not animal.muerto_por_fauna:
            asesino = getattr(animal, "ultimo_golpe_por", None)
            if asesino is not None:
                asesino.ganar_xp(animal.xp)
            especie = type(animal).__name__
            self.deuda_npc[especie] = self.deuda_npc.get(especie, 0) + 1
            return False
        # Cazado por un depredador: no da XP ni monedas al jugador
        if animal.muerto_por_fauna:
            return False
        self.xp_pendiente += animal.xp
        self.monedas_pendientes += animal.tirar_monedas()
        return True

    def _ritmo(self, especie):
        """RITMO_TRAS_NPC si un NPC mato animales de esta especie y aun no se han repuesto."""
        return RITMO_TRAS_NPC if self.deuda_npc.get(especie, 0) > 0 else 1

    def _pagar(self, especie):
        """Nacio o reaparecio uno de esta especie: se descuenta de lo que mataron los NPC."""
        if self.deuda_npc.get(especie, 0) > 0:
            self.deuda_npc[especie] -= 1

    def _recoger_muertes(self):
        for grupo in (self.conejos, self.venados, self.jabalies, self.zorros, self.osos, self.cocodrilos, self.lobos_solitarios):
            for animal in grupo:
                self._contar_muerte(animal)
        for man in self.manadas:
            murio = False
            for lobo in man.lobos:
                if self._contar_muerte(lobo):
                    murio = True
                    man.alfa_cazado = man.alfa_cazado or lobo.es_alfa
            # Bono solo por la manada completa: hay que haber cazado tambien a su alfa
            if murio and not man.vivos() and man.alfa_cazado and not man.bono_dado:
                man.bono_dado = True
                self.xp_pendiente += XP_MANADA_COMPLETA
        # Un oso muerto por un efecto (desangrado, quemadura...) tambien deja su orbe. El que
        # remata un NPC no deja ninguno (no te aprovechas de lo que mato otro).
        # (el golpe mortal ya los solto: si lo remato un NPC se retiran antes de poder cogerlos)
        for oso in self.osos:
            if oso.vivo:
                continue
            if getattr(oso, "ultimo_golpe_npc", False):
                oso.orbe = None
                oso.orbes_extra = []
            elif oso.orbe is None:
                oso.dejar_orbes()

    def quitar_fauna_acuatica(self, centro, radio):
        """Agua evaporada (Estrella Ignea): los peces y ranas de ese circulo desaparecen."""
        self.peces = [p for p in self.peces if (p.centro - centro).length() > radio]
        self.ranas = [r for r in self.ranas if (r.centro - centro).length() > radio]

    def tomar_ruletas(self):
        """Orbes Gacha recogidos desde la última llamada (cada uno = una ruleta de anillos)."""
        n, self.ruletas_pendientes = self.ruletas_pendientes, 0
        return n

    def tomar_xp(self):
        """Devuelve la XP ganada por el jugador desde la ultima llamada y la reinicia."""
        self._recoger_muertes()
        xp, self.xp_pendiente = self.xp_pendiente, 0.0
        return xp

    def tomar_monedas(self):
        """Devuelve las monedas ganadas por el jugador desde la ultima llamada y las reinicia."""
        self._recoger_muertes()
        monedas, self.monedas_pendientes = self.monedas_pendientes, 0
        return monedas

    def olvidar_objetivos(self, objetivos):
        """Tras la muerte del jugador: los animales dejan de perseguirlo a el y a sus sombras."""
        ids = {id(o) for o in objetivos}
        for z in self.zorros:
            if z.presa is not None and id(z.presa) in ids:
                z._liberar_robo()
        for man in self.manadas:
            man.alertada = False
        for ls in self.lobos_solitarios:
            ls.alertada = False
        for oso in self.osos:
            if oso.vivo and oso.estado == "ataca":
                oso.estado = "regresa"
        for coco in self.cocodrilos:
            if coco.vivo and coco.estado == "ataca":
                coco.estado = "regresa"
                coco._objetivo = None

    def cuerpos_solidos(self, vista):
        """Animales con colision solida cerca de la camara (para resolver_solapamientos)."""
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        solidos = []
        for cn in self.conejos:
            if cn.solido and zona.collidepoint(cn.posicion.x, cn.posicion.y):
                solidos.append(cn)
        for v in self.venados:
            if v.vivo and zona.collidepoint(v.posicion.x, v.posicion.y):
                solidos.append(v)
        for j in self.jabalies:
            if j.vivo and zona.collidepoint(j.posicion.x, j.posicion.y):
                solidos.append(j)
        for z in self.zorros:
            if z.vivo and not z.invisible and zona.collidepoint(z.posicion.x, z.posicion.y):
                solidos.append(z)
        for man in self.manadas:
            for l in man.lobos:
                if l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y):
                    solidos.append(l)
        for ls in self.lobos_solitarios:
            if ls.vivo and zona.collidepoint(ls.posicion.x, ls.posicion.y):
                solidos.append(ls)
        for o in self.osos:
            if o.vivo and not o.en_cueva and zona.collidepoint(o.posicion.x, o.posicion.y):
                solidos.append(o)
        for co in self.cocodrilos:
            if co.vivo and not co.sumergido and zona.collidepoint(co.posicion.x, co.posicion.y):
                solidos.append(co)
        return solidos

    def animales_con_vida(self, vista):
        """Animales que pueden recibir dano cerca de la camara (venados y conejos)."""
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        res = [v for v in self.venados if v.vivo and zona.collidepoint(v.posicion.x, v.posicion.y)]
        res += [c for c in self.conejos if c.vivo and c.estado != "escondido" and zona.collidepoint(c.posicion.x, c.posicion.y)]
        res += [j for j in self.jabalies if j.vivo and zona.collidepoint(j.posicion.x, j.posicion.y)]
        res += [z for z in self.zorros if z.vivo and not z.invisible and zona.collidepoint(z.posicion.x, z.posicion.y)]
        for man in self.manadas:
            res += [l for l in man.lobos if l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y)]
        res += [ls for ls in self.lobos_solitarios if ls.vivo and zona.collidepoint(ls.posicion.x, ls.posicion.y)]
        res += [o for o in self.osos if o.vivo and not o.en_cueva and zona.collidepoint(o.posicion.x, o.posicion.y)]
        res += [co for co in self.cocodrilos if co.vivo and not co.sumergido and zona.collidepoint(co.posicion.x, co.posicion.y)]
        return res

    def dibujar_cofres(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for cofre in self.cofres:
            if not cofre.abierto and zona.collidepoint(cofre.posicion.x, cofre.posicion.y):
                cofre.dibujar(pantalla, desplazamiento)

    def dibujar_madrigueras(self, pantalla, vista, desplazamiento):
        for m in self.madrigueras:
            if vista.collidepoint(m.centro.x, m.centro.y):
                m.dibujar(pantalla, desplazamiento)

    def dibujar_conejos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for cn in self.conejos:
            if zona.collidepoint(cn.posicion.x, cn.posicion.y):
                cn.dibujar(pantalla, desplazamiento)

    def dibujar_venados(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for v in self.venados:
            if zona.collidepoint(v.posicion.x, v.posicion.y):
                v.dibujar(pantalla, desplazamiento)

    def dibujar_jabalies(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for j in self.jabalies:
            if zona.collidepoint(j.posicion.x, j.posicion.y):
                j.dibujar(pantalla, desplazamiento)

    def dibujar_zorros(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for z in self.zorros:
            if zona.collidepoint(z.posicion.x, z.posicion.y):
                z.dibujar(pantalla, desplazamiento)

    def dibujar_lobos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for man in self.manadas:
            for l in man.lobos:
                if zona.collidepoint(l.posicion.x, l.posicion.y):
                    l.dibujar(pantalla, desplazamiento)
        for ls in self.lobos_solitarios:
            if zona.collidepoint(ls.posicion.x, ls.posicion.y):
                ls.dibujar(pantalla, desplazamiento)

    def dibujar_osos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for oso in self.osos:
            if zona.collidepoint(oso.posicion.x, oso.posicion.y):
                oso.dibujar(pantalla, desplazamiento)
        for r in self.rugidos:
            r.dibujar(pantalla, desplazamiento)

    def dibujar_cocodrilos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for coco in self.cocodrilos:
            if zona.collidepoint(coco.posicion.x, coco.posicion.y):
                coco.dibujar(pantalla, desplazamiento)

    def dibujar_entradas_cueva(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for oso in self.osos:
            if zona.collidepoint(oso.cueva.x, oso.cueva.y):
                oso.dibujar_entrada(pantalla, desplazamiento)

    def dibujar_orbes_cueva(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for oso in self.osos:
            if oso.orbe is not None and zona.collidepoint(oso.cueva.x, oso.cueva.y):
                oso.orbe.dibujar(pantalla, desplazamiento)
                for orbe in oso.orbes_extra:
                    orbe.dibujar(pantalla, desplazamiento)

    def brujula(self, pos):
        """Devuelve [(etiqueta, color, posicion)] del conejo, lobo y oso vivos mas cercanos."""
        objetivos = []
        def cercano(items):
            vivos = [i for i in items if getattr(i, "vivo", True)]
            if not vivos:
                return None
            return min(vivos, key=lambda i: (i.posicion - pos).length_squared())
        c = cercano(self.conejos)
        if c is not None:
            objetivos.append(("C", (150, 205, 120), pygame.Vector2(c.posicion)))
        lobos = [l for m in self.manadas for l in m.lobos] + list(self.lobos_solitarios)
        lo = cercano(lobos)
        if lo is not None:
            objetivos.append(("L", (205, 205, 225), pygame.Vector2(lo.posicion)))
        oso = cercano(self.osos)
        if oso is not None:
            objetivos.append(("O", (210, 150, 90), pygame.Vector2(oso.posicion)))
        return objetivos

    def jugador_en_cueva(self, jugador):
        for oso in self.osos:
            if (not oso.vivo) and (jugador.posicion - oso.entrada).length() <= ENTRADA_RADIO:
                return True
        return False


# =====================================================================
# CONEJOS SALVAJES Y MADRIGUERAS  (praderas; huyen a su madriguera)
# =====================================================================
MADRIGUERAS_MIN = 15
MADRIGUERAS_MAX = 15
CONEJOS_POR_MADRIGUERA = (2, 10)
CONEJO_RADIO = 7
CONEJO_MASA = 1.0
CONEJO_VISION = 100.0          # ve al jugador a esta distancia -> huye
CONEJO_VEL_PASEO = 45.0
CONEJO_VEL_HUIDA = 160.0
CONEJO_COLORES = [(150, 130, 110), (172, 150, 128), (132, 116, 98), (120, 120, 126)]
CONEJO_VIDA = (5, 20)
CONEJO_MAX_MADRIGUERA = 10
CONEJO_REPRO_INTERVALO = 30.0


class AnimalCombatible:
    """Interfaz minima de 'enemigo' para que armas, habilidades, mascotas y telaranas
    puedan danar/atrapar al animal (se mete en la lista 'enemigos' del juego).
    No tiene escudos: recibir_dano (definido en cada animal) baja la vida directo."""
    XP = 0.0                               # experiencia al morir (cada especie la define)
    MONEDAS = (0.0, 0, 0)                  # (probabilidad, minimo, maximo) de monedas al morir

    @property
    def xp(self):
        return self.XP

    @property
    def monedas(self):
        return self.MONEDAS

    def tirar_monedas(self):
        """Monedas que suelta al morir: con su probabilidad, un entero entre minimo y maximo."""
        prob, minimo, maximo = self.monedas
        if prob <= 0 or random.random() >= prob:
            return 0
        return random.randint(minimo, maximo)

    def _init_combate(self):
        self._xp_contada = False           # su XP ya se sumo (o se descarto) al morir
        self.muerto_por_fauna = False      # lo mato un depredador salvaje: no da XP
        self.escudo = 0.0
        self.escudo_magico = 0.0
        self.anulacion_escudo_magico = 0.0
        self.herramienta = None            # no ataca: los bucles de 'arma enemiga' lo saltan
        self.detectable = True
        self.desangrado = None
        self.veneno = None
        self.quemadura = None
        self.corrosion = None
        self.inmovilizado = None
        self.dormido = None                # Palabras Malditas: Duerme
        self.huida = None                  # Palabras Malditas: Huye
        self.ralentizacion = 0.0
        self.tiempo_ralentizacion = 0.0
        self._pos_frenado = None           # posicion del frame anterior (ver _frenar)
        self._t_inmune_aturdir = 0.0      # tras un aturdimiento no se le puede volver a aturdir

    def aturdir_ataque(self):
        """Golpe de arma del jugador: retrasa su siguiente ataque ATURDIR_GOLPE s. Despues queda
        ATURDIR_INMUNE s sin poder aturdirse otra vez (las armas rapidas no lo bloquean del todo)."""
        if self._t_inmune_aturdir > 0:
            return False
        for attr in ("_cd_mordida", "_cd_golpe", "_cd_zarpazo"):
            if hasattr(self, attr):
                setattr(self, attr, max(getattr(self, attr), ATURDIR_GOLPE))
        self._t_inmune_aturdir = ATURDIR_INMUNE
        return True

    @property
    def apuntable(self):
        """False si el animal esta fuera del alcance del jugador (invisible, en su cueva,
        sumergido o escondido en la madriguera): el Autoapuntado lo suelta."""
        return (self.vivo and not getattr(self, "invisible", False) and not getattr(self, "en_cueva", False)
                and not getattr(self, "sumergido", False) and getattr(self, "estado", "") != "escondido")

    @property
    def controlado(self):
        """Paralizado (telarana, aturdimiento, No te muevas), dormido o huyendo: su IA no actua
        (la huida lo mueve sola en _tick_efectos)."""
        return self.inmovilizado is not None or self.dormido is not None or self.huida is not None

    def aplicar_empuje(self, direccion, puntos):
        if puntos <= 0 or direccion is None or direccion.length() == 0:
            return
        paso = direccion.normalize() * min(float(puntos) * PIXELES_POR_PUNTO_EMPUJE, 96.0)
        self.posicion += paso
        if self._pos_frenado is not None:
            self._pos_frenado += paso          # el empuje recibido no se frena

    def _frenar(self):
        """Ralentizacion (Onda Sonora, Palabras Malditas) y corrosion: recorta el desplazamiento
        desde el frame anterior en el porcentaje mas fuerte. Vale para todas las especies sin tocar
        su IA. Un salto mayor que SALTO_MAX_FRENADO (reaparicion) no se frena."""
        factor = ralentizacion_total(self)
        if self._pos_frenado is not None and factor > 0:
            delta = self.posicion - self._pos_frenado
            if delta.length() <= SALTO_MAX_FRENADO:
                self.posicion.update(self._pos_frenado + delta * (1.0 - factor))
        self._pos_frenado = pygame.Vector2(self.posicion)

    def _fuera_del_jardin(self):
        """Ningun animal entra en el jardin de la casa (ZONA_PROHIBIDA): se le saca al borde."""
        if ZONA_PROHIBIDA is None:
            return
        centro, radio = ZONA_PROHIBIDA
        lejos = self.posicion - centro
        minimo = radio + self.radio
        if lejos.length() < minimo:
            normal = lejos.normalize() if lejos.length_squared() > 0 else pygame.Vector2(1, 0)
            self.posicion.update(centro + normal * minimo)
            self._pos_frenado = pygame.Vector2(self.posicion)

    def _tick_efectos(self, dt):
        actualizar_ralentizacion(self, dt)
        self._frenar()
        self._fuera_del_jardin()
        if self._t_inmune_aturdir > 0:
            self._t_inmune_aturdir = max(0.0, self._t_inmune_aturdir - dt)
        if self.desangrado is not None:
            self.desangrado.actualizar(dt, self)
            if not self.desangrado.activo:
                self.desangrado = None
        if self.quemadura is not None:
            self.quemadura.actualizar(dt, self)
            if not self.quemadura.activo:
                self.quemadura = None
        if self.veneno is not None:
            self.veneno.actualizar(dt, self)
            if not self.veneno.activo:
                self.veneno = None
        if self.corrosion is not None:
            self.corrosion.actualizar(dt, self)
            if not self.corrosion.activo:
                self.corrosion = None
        if self.inmovilizado is not None:
            self.inmovilizado.actualizar(dt, self)
            if not self.inmovilizado.activo:
                self.inmovilizado = None
        if self.huida is not None:
            self.huida.actualizar(dt, self)
            if not self.huida.activo:
                self.huida = None
        if self.dormido is not None:
            self.dormido.actualizar(dt, self)
            if not self.dormido.activo:
                self.dormido = None
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False


class Madriguera:
    def __init__(self, centro):
        self.centro = pygame.Vector2(centro)
        self.radio_zona = random.uniform(180, 320)   # radio de deambular (separacion progresiva)
        self.max_conejos = CONEJO_MAX_MADRIGUERA
        self._t_repro = random.uniform(0, CONEJO_REPRO_INTERVALO)

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        # Pasto alto alrededor (mechones mas altos que el pasto normal)
        for i in range(12):
            ang = (i / 12) * math.tau
            bx = px + round(math.cos(ang) * 17)
            by = py + round(math.sin(ang) * 11)
            pygame.draw.line(pantalla, (58, 118, 56), (bx, by), (bx - 2, by - 15), 2)
            pygame.draw.line(pantalla, (78, 142, 70), (bx + 2, by), (bx + 1, by - 18), 2)
        # Monticulo de tierra y agujero
        pygame.draw.ellipse(pantalla, (96, 74, 54), (px - 16, py - 8, 32, 18))
        pygame.draw.ellipse(pantalla, (74, 56, 40), (px - 16, py - 8, 32, 18), 1)
        pygame.draw.ellipse(pantalla, (26, 19, 15), (px - 8, py - 4, 16, 11))


class ConejoSalvaje(AnimalCombatible):
    XP = XP_CONEJO
    MONEDAS = MONEDAS_CONEJO

    def __init__(self, madriguera):
        self.madriguera = madriguera
        self.radio = CONEJO_RADIO
        self.masa = CONEJO_MASA
        self.color = random.choice(CONEJO_COLORES)
        self.vida = random.randint(*CONEJO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self._init_combate()
        self.vel_mult = 1.0
        self.posicion = self._punto_zona()
        self.destino = pygame.Vector2(self.posicion)
        self.estado = "deambula"          # deambula / huye / escondido
        self._espera = random.uniform(0.5, 2.5)
        self._t_esc = 0.0
        self.dir_mira = pygame.Vector2(1, 0)

    @property
    def solido(self):
        return self.vivo and self.estado != "escondido"

    def _punto_zona(self):
        ang = random.uniform(0, math.tau)
        r = random.uniform(0, self.madriguera.radio_zona)
        return pygame.Vector2(self.madriguera.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.estado = "huye"          # al recibir dano huye a la madriguera
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self.posicion += direccion_empuje.normalize() * 4
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.controlado:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()
        if amenazas:
            cercana = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())
            dist_j = (cercana.posicion - self.posicion).length()
        else:
            dist_j = float("inf")

        if self.estado == "escondido":
            self._t_esc -= dt
            if self._t_esc <= 0 and dist_j > CONEJO_VISION * 1.4:
                self.posicion = pygame.Vector2(self.madriguera.centro)
                self.estado = "deambula"
                self._espera = random.uniform(0.5, 2.0)
            return

        # Si ve al jugador, huye a la madriguera.
        if dist_j < CONEJO_VISION:
            self.estado = "huye"

        if self.estado == "huye":
            if dist_j > CONEJO_VISION * 1.5:
                # Ya no lo persiguen: deja de huir y deambula donde este.
                self.estado = "deambula"
                self._espera = random.uniform(0.5, 2.0)
                return
            d = self.madriguera.centro - self.posicion
            if d.length() <= 10:
                self.estado = "escondido"
                self._t_esc = 60.0
                return
            self.posicion += d.normalize() * CONEJO_VEL_HUIDA * self.vel_mult * dt
            self.dir_mira = d.normalize()
            return

        # Deambula alrededor de su madriguera, con pausas.
        self._espera -= dt
        d = self.destino - self.posicion
        if self._espera <= 0:
            self.destino = self._punto_zona()
            self._espera = random.uniform(0.8, 2.6)
        elif d.length() > 3:
            self.posicion += d.normalize() * CONEJO_VEL_PASEO * self.vel_mult * dt
            self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if self.estado == "escondido":
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        der = self.dir_mira.x >= 0
        s = 1 if der else -1
        pygame.draw.ellipse(pantalla, c, (px - 7, py - 5, 14, 10))        # cuerpo
        hx = px + s * 5
        pygame.draw.circle(pantalla, c, (hx, py - 3), 4)                  # cabeza
        pygame.draw.ellipse(pantalla, c, (hx - 3, py - 13, 3, 9))         # orejas
        pygame.draw.ellipse(pantalla, c, (hx + 1, py - 13, 3, 9))
        pygame.draw.circle(pantalla, (235, 235, 230), (px - s * 6, py + 2), 2)   # cola
        pygame.draw.circle(pantalla, (20, 18, 16), (hx + s, py - 4), 1)   # ojo
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 4, 1)
        if self.vida < self.vida_max:
            w = 14
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 7, py - 16, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 7, py - 16, fw, 3))


# =====================================================================
# VENADOS  (timidos; huyen lejos y se regeneran si reciben dano)
# =====================================================================
VENADO_MAX = 70
VENADO_RADIO = 12
VENADO_MASA = 40.0
VENADO_VIDA = (20, 40)
VENADO_REGEN_INTERVALO = 2.0   # 1 pv cada 2 s tras recibir dano
VENADO_SUSTO = 160.0
VENADO_VEL_PASEO = 40.0
VENADO_VEL_HUIDA = 235.0
VENADO_REPRO_INTERVALO = 60.0
VENADO_COLORES = [(140, 96, 60), (120, 82, 52), (156, 110, 72)]


class Venado(AnimalCombatible):
    XP = XP_VENADO
    MONEDAS = MONEDAS_VENADO

    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = VENADO_RADIO
        self.masa = VENADO_MASA
        self.color = random.choice(VENADO_COLORES)
        self.vida = random.randint(*VENADO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.cornamenta = random.random() < 0.5
        self.estado = "pasta"             # pasta / huye
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.5, 4.0)
        self._t_huida = 0.0
        self._danado = False
        self._regen_t = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self._danado = True
        self.estado = "huye"
        self._t_huida = random.uniform(2.5, 4.0)
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self.posicion += direccion_empuje.normalize() * 6
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None):
        if not self.vivo:
            return
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.controlado:
            return
        # Regeneracion: 1 pv cada 2 s mientras este dañado.
        if self._danado and self.vida < self.vida_max:
            self._regen_t += dt
            while self._regen_t >= VENADO_REGEN_INTERVALO:
                self._regen_t -= VENADO_REGEN_INTERVALO
                self.vida = min(self.vida_max, self.vida + 1)
            if self.vida >= self.vida_max:
                self._danado = False
                self._regen_t = 0.0

        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()
        if amenazas:
            cercana = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())
            dist_j = (cercana.posicion - self.posicion).length()
        else:
            cercana = None
            dist_j = float("inf")
        if dist_j < VENADO_SUSTO:
            self.estado = "huye"

        if self.estado == "huye":
            if cercana is None:
                self.estado = "pasta"
                self._espera = random.uniform(2.0, 5.0)
                self.destino = pygame.Vector2(self.posicion)
            else:
                d = self.posicion - cercana.posicion
                if d.length() < 1:
                    d = pygame.Vector2(1, 0)
                self.posicion += d.normalize() * VENADO_VEL_HUIDA * dt
                self.dir_mira = d.normalize()
                # Huye definitivamente: solo deja de correr cuando esta bien lejos.
                if dist_j > VENADO_SUSTO * 2.0:
                    self.estado = "pasta"
                    self._espera = random.uniform(2.0, 5.0)
                    self.destino = pygame.Vector2(self.posicion)
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                if cercana is not None and dist_j < VENADO_SUSTO * 2.5:
                    # Elige un destino ALEJANDOSE del jugador (no vuelve hacia el).
                    away = self.posicion - cercana.posicion
                    base = away.normalize() if away.length() > 1 else pygame.Vector2(1, 0)
                    ang = math.atan2(base.y, base.x) + random.uniform(-0.6, 0.6)
                    self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(60, 130)
                else:
                    ang = random.uniform(0, math.tau)
                    self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(30, 90)
                self._espera = random.uniform(2.0, 5.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * VENADO_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-6, 6):                                               # patas
            pygame.draw.line(pantalla, (92, 64, 42), (px + lx, py + 2), (px + lx, py + 11), 2)
        pygame.draw.ellipse(pantalla, c, (px - 11, py - 6, 22, 13))      # cuerpo
        nx = px + s * 11
        pygame.draw.line(pantalla, c, (px + s * 7, py - 4), (nx, py - 12), 4)   # cuello
        pygame.draw.circle(pantalla, c, (nx, py - 13), 4)               # cabeza
        pygame.draw.circle(pantalla, (70, 48, 32), (nx + s * 3, py - 12), 2)    # hocico
        if self.cornamenta:
            for dxh in (-2, 2):
                bx = nx + dxh
                pygame.draw.line(pantalla, (212, 192, 152), (bx, py - 16), (bx, py - 22), 2)
                pygame.draw.line(pantalla, (212, 192, 152), (bx, py - 20), (bx + dxh, py - 24), 2)
        pygame.draw.circle(pantalla, (236, 226, 216), (px - s * 11, py - 2), 2)  # cola
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self._danado and self.vida < self.vida_max:                 # barra de vida
            w = 22
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 11, py - 20, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 11, py - 20, fw, 3))


# =====================================================================
# JABALI  (neutral; si lo golpean entra en RABIA y embiste al atacante)
# =====================================================================
JABALI_MAX = 40
JABALI_RADIO = 14
JABALI_MASA = 60.0
JABALI_VIDA = (40, 70)
JABALI_DANO = (10, 18)
JABALI_EMPUJE = 40               # empuje muy alto
JABALI_VEL_PASEO = 30.0
JABALI_VEL_RABIA = 195.0
JABALI_VEL_HUIDA = 175.0
JABALI_RABIA_DUR = 6.0
JABALI_GOLPE_CD = 1.0
JABALI_REPRO_INTERVALO = 60.0
JABALI_COLORES = [(92, 72, 56), (76, 58, 46), (106, 82, 62)]


class Jabali(AnimalCombatible):
    XP = XP_JABALI
    MONEDAS = MONEDAS_JABALI

    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = JABALI_RADIO
        self.masa = JABALI_MASA
        self.color = random.choice(JABALI_COLORES)
        self.vida = random.randint(*JABALI_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.estado = "deambula"          # deambula / rabia / huye
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.5, 4.0)
        self._t_rabia = 0.0
        self._t_huida = 0.0
        self._cd_golpe = 0.0
        self._objetivo_pos = None
        self._jitter = pygame.Vector2()
        self._t_jitter = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.estado = "rabia"
        self._t_rabia = JABALI_RABIA_DUR
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self._objetivo_pos = self.posicion - direccion_empuje   # hacia quien lo golpeo
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def _elegir_objetivo(self, jugador, amenazas):
        if not amenazas:
            return None
        if self._objetivo_pos is not None:
            return min(amenazas, key=lambda o: (o.posicion - self._objetivo_pos).length_squared())
        return min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())

    def actualizar(self, dt, jugador, amenazas=None):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.controlado:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()

        if self.estado == "rabia":
            self._t_rabia -= dt
            self._cd_golpe -= dt
            objetivo = self._elegir_objetivo(jugador, amenazas)
            if objetivo is None:
                if self._t_rabia <= 0:
                    self.estado = "huye"
                    self._t_huida = random.uniform(2.5, 4.0)
                    self._objetivo_pos = None
                return
            self._t_jitter -= dt
            if self._t_jitter <= 0:
                ang = random.uniform(-1.0, 1.0)
                self._jitter = pygame.Vector2(math.cos(ang), math.sin(ang))
                self._t_jitter = random.uniform(0.15, 0.35)
            d = objetivo.posicion - self.posicion
            base = d.normalize() if d.length() > 0 else pygame.Vector2(1, 0)
            dir_mov = base + self._jitter * 0.6
            if dir_mov.length() > 0:
                dir_mov = dir_mov.normalize()
                self.posicion += dir_mov * JABALI_VEL_RABIA * dt
                self.dir_mira = dir_mov
            if d.length() <= self.radio + getattr(objetivo, "radio", 10) + 4 and self._cd_golpe <= 0:
                self._cd_golpe = JABALI_GOLPE_CD
                dano = random.randint(*JABALI_DANO)
                golpear_objetivo(self, objetivo, dano, JABALI_EMPUJE)
            if self._t_rabia <= 0:
                self.estado = "huye"
                self._t_huida = random.uniform(2.5, 4.0)
                self._objetivo_pos = None
        elif self.estado == "huye":
            self._t_huida -= dt
            d = self.posicion - jugador.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * JABALI_VEL_HUIDA * dt
            self.dir_mira = d.normalize()
            if self._t_huida <= 0:
                self.estado = "deambula"
                self._espera = random.uniform(1.5, 4.0)
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(30, 90)
                self._espera = random.uniform(1.5, 4.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * JABALI_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-8, 8):
            pygame.draw.line(pantalla, (60, 46, 36), (px + lx, py + 3), (px + lx, py + 12), 2)
        pygame.draw.ellipse(pantalla, c, (px - 13, py - 7, 26, 15))
        nx = px + s * 13
        pygame.draw.circle(pantalla, c, (nx, py - 1), 6)
        pygame.draw.circle(pantalla, (40, 30, 24), (nx + s * 4, py - 1), 2)
        pygame.draw.line(pantalla, (225, 220, 205), (nx + s * 3, py + 1), (nx + s * 7, py - 3), 2)
        ojo = (230, 60, 50) if self.estado == "rabia" else (25, 20, 16)
        pygame.draw.circle(pantalla, ojo, (nx, py - 3), 1)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = 26; fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 13, py - 20, w, 3))
            pygame.draw.rect(pantalla, (210, 120, 70), (px - 13, py - 20, fw, 3))


# =====================================================================
# ZORRO  (neutral; muerde si lo acorralan/golpean; caza conejos; Paso 0)
# =====================================================================
ZORRO_MAX = 30
ZORRO_RADIO = 9
ZORRO_MASA = 6.0
ZORRO_VIDA = (15, 30)
ZORRO_DANO = (5, 10)
ZORRO_DIST = 120.0
ZORRO_ACORRALA = 45.0
ZORRO_VEL_PASEO = 42.0
ZORRO_VEL = 150.0
ZORRO_HAMBRE = 300.0             # 5 min
ZORRO_RANGO_CAZA = 450.0
ZORRO_ROBO = 0.30
ZORRO_PASO0_PROB = 0.30
ZORRO_PASO0_DUR = 5.0
ZORRO_PASO0_CD = 10.0            # recarga de Paso 0
ZORRO_VISTA = 500.0             # a esta distancia dejas de ser su objetivo (sales de su pantalla)
ZORRO_MORDIDA_CD = 1.2
ZORRO_COLORES = [(192, 110, 55), (172, 96, 46), (206, 126, 66)]
ZORRO_DESVANECER = 0.4           # s que tarda en desvanecerse con su Paso 0 (solo visual)
ZORRO_CAPA = 40                  # lado de la capa con la que se dibuja el fundido


class Zorro(AnimalCombatible):
    XP = XP_ZORRO
    MONEDAS = MONEDAS_ZORRO

    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = ZORRO_RADIO
        self.masa = ZORRO_MASA
        self.color = random.choice(ZORRO_COLORES)
        self.vida = random.randint(*ZORRO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.estado = "ronda"            # ronda / caza / muerde
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self.vel_mult = 1.0
        self._hambre_t = random.uniform(0, ZORRO_HAMBRE)
        self.hambriento = False
        self.presa = None
        self.invisible = False
        self.visibilidad = 1.0           # fundido visual de su Paso 0 (1 visible, 0 invisible)
        self._paso0_t = 0.0
        self._paso0_cd = 0.0
        self._presa_es_conejo = False
        self._agredido = False
        self._cd_mordida = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def _robar_de(self, objetivo, es_conejo=False):
        if self.presa is objetivo:
            return
        self._liberar_robo()
        self.presa = objetivo
        self._presa_es_conejo = es_conejo
        self.vel_mult = 1.0 + ZORRO_ROBO
        if hasattr(objetivo, "vel_mult"):
            objetivo.vel_mult = 1.0 - ZORRO_ROBO

    def _mantener_robo(self, objetivo):
        if not hasattr(objetivo, "vel_mult") and hasattr(objetivo, "ralentizacion"):
            objetivo.ralentizacion = max(getattr(objetivo, "ralentizacion", 0.0), ZORRO_ROBO)
            if hasattr(objetivo, "tiempo_ralentizacion"):
                objetivo.tiempo_ralentizacion = max(getattr(objetivo, "tiempo_ralentizacion", 0.0), 0.3)

    def _liberar_robo(self):
        if self.presa is not None and hasattr(self.presa, "vel_mult"):
            self.presa.vel_mult = 1.0
        self.presa = None
        self._presa_es_conejo = False
        self.vel_mult = 1.0

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self._agredido = True
        self._cd_mordida = 0.0
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
            self._liberar_robo()
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None, conejos=()):
        self._tick_efectos(dt)
        if not self.vivo:
            self._liberar_robo()
            return
        if self.controlado:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()

        # Fundido visual del Paso 0 (la invisibilidad en si es instantanea)
        paso = dt / ZORRO_DESVANECER
        if self.invisible:
            self.visibilidad = max(0.0, self.visibilidad - paso)
        else:
            self.visibilidad = min(1.0, self.visibilidad + paso)

        # Paso 0: invisibilidad activa y recarga (CD de 10 s).
        if self.invisible:
            self._paso0_t -= dt
            if self._paso0_t <= 0:
                self.invisible = False
                self._paso0_cd = ZORRO_PASO0_CD
        else:
            self._paso0_cd -= dt

        self._hambre_t += dt
        self.hambriento = self._hambre_t >= ZORRO_HAMBRE
        self._cd_mordida -= dt

        candidatos = [o for o in amenazas if o is not self and not isinstance(o, Zorro)]
        amenaza = min(candidatos, key=lambda o: (o.posicion - self.posicion).length_squared()) if candidatos else None
        d_amen = (amenaza.posicion - self.posicion).length() if amenaza is not None else float("inf")

        # El robo es permanente: la presa se mantiene hasta morir, esconderse o salir de la vista.
        if self.presa is not None:
            viva = getattr(self.presa, "vivo", True)
            escondida = getattr(self.presa, "estado", None) == "escondido"
            lejos = (self.presa.posicion - self.posicion).length() > ZORRO_VISTA
            indetectable = (not self._presa_es_conejo) and (not getattr(self.presa, "detectable", True))
            if (not viva) or escondida or lejos or indetectable:
                mad = getattr(self.presa, "madriguera", None) if self._presa_es_conejo else None
                self._liberar_robo()
                if mad is not None:
                    away = self.posicion - mad.centro
                    paso = away.normalize() * 160 if away.length() > 1 else pygame.Vector2(1, 0) * 160
                    self.destino = self.posicion + paso
                    self._espera = random.uniform(2.0, 3.5)
                    self.estado = "ronda"

        # Conejo-presa (cuando tiene hambre).
        presa_conejo = None
        if self.hambriento and conejos:
            vivos = [c for c in conejos if c.vivo and c.estado != "escondido"]
            if vivos:
                cand = min(vivos, key=lambda c: (c.posicion - self.posicion).length_squared())
                if (cand.posicion - self.posicion).length() <= ZORRO_RANGO_CAZA:
                    presa_conejo = cand

        # Paso 0: un tiro del 30% al detectar algo si el CD esta listo; si falla, reinicia los 10 s.
        detecta = (d_amen < ZORRO_DIST * 1.5) or (presa_conejo is not None) or (self.presa is not None)
        if not self.invisible and self._paso0_cd <= 0 and detecta:
            if random.random() < ZORRO_PASO0_PROB:
                self.invisible = True
                self._paso0_t = ZORRO_PASO0_DUR
            else:
                self._paso0_cd = ZORRO_PASO0_CD

        # Si lo acorralan o lo golpearon, esa amenaza pasa a ser su objetivo (robo permanente).
        if amenaza is not None and (d_amen < ZORRO_ACORRALA or self._agredido):
            self._robar_de(amenaza, es_conejo=False)
        self._agredido = False

        # 1) Objetivo-amenaza (jugador/sombra): muerde si esta cerca, huye y sigue robando.
        presa = self.presa
        if presa is not None and not self._presa_es_conejo:
            self._mantener_robo(presa)
            dp = (presa.posicion - self.posicion).length()
            if self._cd_mordida <= 0 and dp < ZORRO_ACORRALA + 6:
                self._cd_mordida = ZORRO_MORDIDA_CD
                dano = random.randint(*ZORRO_DANO)
                golpear_objetivo(self, presa, dano)
            if self.presa is None:
                presa = None
            if presa is not None:
                d = self.posicion - presa.posicion
                if d.length() < 1:
                    d = pygame.Vector2(1, 0)
                self.posicion += d.normalize() * ZORRO_VEL * self.vel_mult * dt
                self.dir_mira = d.normalize()
                return

        # 2) Hambriento: caza al conejo (lo mata al contacto y se llena).
        if presa_conejo is not None:
            self.estado = "caza"
            self._robar_de(presa_conejo, es_conejo=True)
            d = presa_conejo.posicion - self.posicion
            dist = d.length()
            if dist <= self.radio + presa_conejo.radio + 2:
                presa_conejo.vivo = False
                presa_conejo.muerto_por_fauna = True
                self._liberar_robo()
                self._hambre_t = 0.0
                self.hambriento = False
                self.estado = "ronda"
            elif dist > 0:
                self.posicion += d.normalize() * ZORRO_VEL * self.vel_mult * dt
                self.dir_mira = d.normalize()
            return

        # 3) Ronda: mantiene distancia de la amenaza o deambula.
        if d_amen < ZORRO_DIST:
            d = self.posicion - amenaza.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * ZORRO_VEL_PASEO * 1.4 * dt
            self.dir_mira = d.normalize()
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(40, 120)
                self._espera = random.uniform(1.0, 3.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * ZORRO_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo or self.visibilidad <= 0:     # Paso 0: completamente invisible
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        if self.visibilidad < 1:
            # Desvaneciendose (o reapareciendo): se dibuja en una capa con transparencia
            m = ZORRO_CAPA // 2
            capa = pygame.Surface((ZORRO_CAPA, ZORRO_CAPA), pygame.SRCALPHA)
            self._dibujar_cuerpo(capa, m, m)
            capa.set_alpha(round(255 * self.visibilidad))
            pantalla.blit(capa, (px - m, py - m))
            return
        self._dibujar_cuerpo(pantalla, px, py)

    def _dibujar_cuerpo(self, pantalla, px, py):
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-5, 5):
            pygame.draw.line(pantalla, (120, 70, 35), (px + lx, py + 2), (px + lx, py + 9), 2)
        pygame.draw.ellipse(pantalla, c, (px - 9, py - 4, 18, 9))
        nx = px + s * 9
        pygame.draw.circle(pantalla, c, (nx, py - 2), 4)
        pygame.draw.polygon(pantalla, c, [(nx - 2, py - 5), (nx - 1, py - 9), (nx + 2, py - 5)])
        pygame.draw.polygon(pantalla, c, [(nx + 1, py - 5), (nx + 3, py - 9), (nx + 4, py - 5)])
        pygame.draw.circle(pantalla, (20, 16, 12), (nx + s * 2, py - 2), 1)
        pygame.draw.circle(pantalla, (245, 240, 235), (px - s * 9, py), 3)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = 18; fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 9, py - 14, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 9, py - 14, fw, 3))


# =====================================================================
# LOBOS EN MANADA  (hostiles; cazan al jugador/sombras y, con hambre, presas)
# =====================================================================
LOBO_MANADAS = 8
LOBO_POR_MANADA = 4
LOBO_VIDA = 25
LOBO_VIDA_ALFA = 40
LOBO_DANO = 8
LOBO_DANO_ALFA = 15
LOBO_DESANGRADO = 0.10
LOBO_DESANGRADO_ALFA = 0.30
LOBO_DETECCION = 250.0
LOBO_PIERDE = 600.0              # pierde el rastro si te alejas mas
LOBO_RANGO_CAZA = 450.0
LOBO_HAMBRE = 360.0             # 6 min
LOBO_RADIO = 10
LOBO_RADIO_ALFA = 12
LOBO_MASA = 8.0
LOBO_VEL = 165.0
LOBO_VEL_RETIRADA = 210.0
LOBO_VEL_PASEO = 40.0
LOBO_MORDIDA_CD = 2.0              # una mordida cada 2 s por lobo
LOBO_COLOR = [(90, 92, 100), (76, 78, 86), (108, 110, 118)]
LOBO_COLOR_ALFA = (58, 60, 70)


# ---- Lobo solitario: un unico lobo con fuerza de alfa; no forma manada ----
LOBO_SOL_CANTIDAD = 6
LOBO_SOL_VIDA = LOBO_VIDA_ALFA        # 40, fuerza de alfa
LOBO_SOL_DANO = LOBO_DANO_ALFA        # 15
LOBO_SOL_DESANGRADO = 0.20            # 20% de probabilidad al morder
LOBO_SOL_DETECCION = 200.0            # un poco menor que la manada comun (250)
LOBO_SOL_PIERDE = 600.0               # pierde el rastro si te alejas mas
LOBO_SOL_VEL = 165.0
LOBO_SOL_VEL_PASEO = 40.0
LOBO_SOL_REAPARICION = 60.0           # 1 min tras morir aparece otro (siempre hay 6)
LOBO_SOL_XP = 10.0
LOBO_SOL_MONEDAS = (1.0, 10, 10)      # 10 monedas fijas
LOBO_SOL_RADIO = LOBO_RADIO_ALFA
LOBO_SOL_COLOR = (70, 62, 70)         # gris oscuro
LOBO_SOL_ONDA_CD = 10.0               # activa la onda sonora cada 10 s en combate
LOBO_SOL_ONDA_DANO = 5                # dano magico de la onda
LOBO_SOL_ONDA_RALENT = 0.10           # ralentiza 10%
LOBO_SOL_ONDA_DUR = 2.0               # durante 2 s
LOBO_SOL_ONDA_RADIO = 200.0
LOBO_SOL_ONDA_VEL = 320.0


class Lobo(AnimalCombatible):
    def __init__(self, x, y, manada, alfa=False):
        self.posicion = pygame.Vector2(x, y)
        self.manada = manada
        self.es_alfa = alfa
        self.radio = LOBO_RADIO_ALFA if alfa else LOBO_RADIO
        self.masa = LOBO_MASA
        self.color = LOBO_COLOR_ALFA if alfa else random.choice(LOBO_COLOR)
        self.vida = LOBO_VIDA_ALFA if alfa else LOBO_VIDA
        self.vida_max = self.vida
        self.dano = LOBO_DANO_ALFA if alfa else LOBO_DANO
        self.prob_desangrado = LOBO_DESANGRADO_ALFA if alfa else LOBO_DESANGRADO
        self.vivo = True
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self._cd_mordida = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    @property
    def xp(self):
        return XP_LOBO_ALFA if self.es_alfa else XP_LOBO

    @property
    def monedas(self):
        return MONEDAS_LOBO_ALFA if self.es_alfa else MONEDAS_LOBO

    def evolucionar_alfa(self):
        """La manada llego a 4 sin alfa: este lobo pasa a ser el alfa (gana la vida que le falta)."""
        self.es_alfa = True
        self.radio = LOBO_RADIO_ALFA
        self.color = LOBO_COLOR_ALFA
        self.vida += LOBO_VIDA_ALFA - self.vida_max
        self.vida_max = LOBO_VIDA_ALFA
        self.dano = LOBO_DANO_ALFA
        self.prob_desangrado = LOBO_DESANGRADO_ALFA

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.manada.alertada = True      # al ser agredido, la manada se alerta
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def _mover_hacia(self, objetivo_pos, vel, dt):
        d = objetivo_pos - self.posicion
        if d.length() > 0:
            self.posicion += d.normalize() * vel * dt
            self.dir_mira = d.normalize()
        return d.length()

    def _morder(self, objetivo):
        if self._cd_mordida > 0:
            return
        self._cd_mordida = LOBO_MORDIDA_CD
        if not golpear_objetivo(self, objetivo, self.dano):
            return
        if random.random() < self.prob_desangrado and hasattr(objetivo, "desangrado"):
            aplicar_desangrado(objetivo)

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        rr = self.radio
        for lx in (-rr + 2, rr - 2):
            pygame.draw.line(pantalla, (58, 60, 68), (px + lx, py + 2), (px + lx, py + rr), 2)
        pygame.draw.ellipse(pantalla, c, (px - rr, py - rr + 3, rr * 2, rr + 4))
        nx = px + s * rr
        pygame.draw.circle(pantalla, c, (nx, py - 1), rr - 3)
        pygame.draw.polygon(pantalla, c, [(nx - 2, py - 4), (nx - 1, py - 8), (nx + 2, py - 4)])
        pygame.draw.polygon(pantalla, c, [(nx + 1, py - 4), (nx + 3, py - 8), (nx + 4, py - 4)])
        ojo = (235, 200, 60) if self.es_alfa else (210, 210, 225)
        pygame.draw.circle(pantalla, ojo, (nx + s * 2, py - 1), 1)
        pygame.draw.circle(pantalla, (235, 235, 240), (px - s * rr, py + 2), 2)
        if self.es_alfa:
            pygame.draw.circle(pantalla, (235, 200, 60), (px, py - rr - 2), 2)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = self.radio * 2
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - self.radio, py - self.radio - 8, w, 3))
            col = (235, 160, 60) if self.es_alfa else (120, 200, 90)
            pygame.draw.rect(pantalla, col, (px - self.radio, py - self.radio - 8, fw, 3))


class Manada:
    def __init__(self, centro):
        self.centro = pygame.Vector2(centro)
        self.alertada = False
        self._hambre_t = random.uniform(0, LOBO_HAMBRE)
        self._t_repro = 0.0
        self.bono_dado = False           # ya se dio el bono por exterminarla
        self.alfa_cazado = False         # el jugador mato a su alfa (requisito del bono)
        self.lobos = []
        for i in range(LOBO_POR_MANADA):
            off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
            self.lobos.append(Lobo(centro.x + off.x, centro.y + off.y, self, alfa=(i == 0)))

    def vivos(self):
        return [l for l in self.lobos if l.vivo]

    def repoblar(self, nuevo_centro=None):
        """Cada minuto: si la manada fue exterminada se inicia otra con 2 lobos (en
        'nuevo_centro', otro bosque); si no, nace +1 junto a un lobo vivo (hasta 4). Al llegar
        a 4 sin alfa, uno evoluciona. No crece mientras esta en combate (alertada)."""
        vivos = self.vivos()
        if not vivos:
            self.alertada = False        # exterminada: ya no hay combate que esperar
        if self.alertada:
            return
        # Quitar los muertos cuya XP ya se conto (los de este frame se cuentan en el siguiente)
        self.lobos = [l for l in self.lobos if l.vivo or not l._xp_contada]
        if not vivos:
            if nuevo_centro is not None:
                self.centro = pygame.Vector2(nuevo_centro)
            nuevos, base = LOBO_REAPARECEN, self.centro
            self.bono_dado = False
            self.alfa_cazado = False
        elif len(vivos) < LOBO_POR_MANADA:
            nuevos, base = 1, random.choice(vivos).posicion
        else:
            nuevos, base = 0, self.centro
        for _ in range(nuevos):
            off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
            self.lobos.append(Lobo(base.x + off.x, base.y + off.y, self))
        vivos = self.vivos()
        if len(vivos) >= LOBO_POR_MANADA and not any(l.es_alfa for l in vivos):
            max(vivos, key=lambda l: l.vida).evolucionar_alfa()

    def actualizar(self, dt, jugador, amenazas, presas):
        vivos = self.vivos()
        if not vivos:
            return
        self._hambre_t += dt
        hambriento = self._hambre_t >= LOBO_HAMBRE

        # Objetivo: la amenaza (jugador detectable o sombra) mas cercana a cualquier lobo.
        objetivo = None
        if amenazas:
            objetivo = min(amenazas, key=lambda o: min((o.posicion - l.posicion).length_squared() for l in vivos))
            dmin = min((objetivo.posicion - l.posicion).length() for l in vivos)
            if self.alertada:
                if dmin > LOBO_PIERDE:
                    self.alertada = False
                    objetivo = None
            elif dmin < LOBO_DETECCION:
                self.alertada = True
            else:
                objetivo = None
        else:
            self.alertada = False

        retirada = len(vivos) == 1

        presa = None
        if hambriento and not self.alertada and presas:
            c0 = vivos[0].posicion
            cand = min(presas, key=lambda a: (a.posicion - c0).length_squared())
            if (cand.posicion - c0).length() <= LOBO_RANGO_CAZA:
                presa = cand

        for l in vivos:
            l._tick_efectos(dt)
            if not l.vivo or l.controlado:
                continue
            l._cd_mordida -= dt
            if retirada:
                d = l.posicion - jugador.posicion
                if d.length() < 1:
                    d = pygame.Vector2(1, 0)
                l.posicion += d.normalize() * LOBO_VEL_RETIRADA * dt
                l.dir_mira = d.normalize()
            elif self.alertada and objetivo is not None:
                dist = l._mover_hacia(objetivo.posicion, LOBO_VEL, dt)
                if dist <= l.radio + getattr(objetivo, "radio", 10) + 2:
                    l._morder(objetivo)
            elif presa is not None:
                dist = l._mover_hacia(presa.posicion, LOBO_VEL, dt)
                if dist <= l.radio + presa.radio + 2:
                    presa.vivo = False
                    presa.muerto_por_fauna = True
                    self._hambre_t = 0.0      # una presa sacia a toda la manada
                    presa = None
            else:
                l._espera -= dt
                d = l.destino - l.posicion
                if l._espera <= 0:
                    ang = random.uniform(0, math.tau)
                    l.destino = l.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(40, 120)
                    l._espera = random.uniform(1.0, 3.0)
                elif d.length() > 3:
                    l.posicion += d.normalize() * LOBO_VEL_PASEO * dt
                    l.dir_mira = d.normalize()


class LoboSolitario(AnimalCombatible):
    """Lobo unico con la fuerza de un alfa; no forma manada. Ojos rojos siempre, 20% de
    desangrado al morder y una onda sonora (cada 10 s) que ralentiza 10% y hace dano magico."""
    XP = LOBO_SOL_XP
    MONEDAS = LOBO_SOL_MONEDAS

    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = LOBO_SOL_RADIO
        self.masa = LOBO_MASA
        self.color = LOBO_SOL_COLOR
        self.vida = LOBO_SOL_VIDA
        self.vida_max = LOBO_SOL_VIDA
        self.dano = LOBO_SOL_DANO
        self.prob_desangrado = LOBO_SOL_DESANGRADO
        self.vivo = True
        self.alertada = False
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self._cd_mordida = 0.0
        self._cd_onda = LOBO_SOL_ONDA_CD
        self._t_reaparicion = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.alertada = True
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def _mover_hacia(self, objetivo_pos, vel, dt):
        d = objetivo_pos - self.posicion
        if d.length() > 0:
            self.posicion += d.normalize() * vel * dt
            self.dir_mira = d.normalize()
        return d.length()

    def _morder(self, objetivo):
        if self._cd_mordida > 0:
            return
        self._cd_mordida = LOBO_MORDIDA_CD
        if not golpear_objetivo(self, objetivo, self.dano):
            return
        if random.random() < self.prob_desangrado and hasattr(objetivo, "desangrado"):
            aplicar_desangrado(objetivo)

    def actualizar(self, dt, jugador, amenazas, ondas):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        self._cd_mordida -= dt
        self._cd_onda -= dt
        if self.controlado:
            return
        # Objetivo: la amenaza (jugador detectable o sombra) mas cercana.
        objetivo = None
        if amenazas:
            cand = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())
            dmin = (cand.posicion - self.posicion).length()
            if self.alertada:
                if dmin > LOBO_SOL_PIERDE:
                    self.alertada = False
                else:
                    objetivo = cand
            elif dmin < LOBO_SOL_DETECCION:
                self.alertada = True
                objetivo = cand
        else:
            self.alertada = False
        if self.alertada and objetivo is not None:
            dist = self._mover_hacia(objetivo.posicion, LOBO_SOL_VEL, dt)
            if dist <= self.radio + getattr(objetivo, "radio", 10) + 2:
                self._morder(objetivo)
            if self._cd_onda <= 0:
                self._cd_onda = LOBO_SOL_ONDA_CD
                ondas.append(RugidoOnda(self.posicion, LOBO_SOL_ONDA_RADIO, LOBO_SOL_ONDA_VEL,
                                        LOBO_SOL_ONDA_RALENT, LOBO_SOL_ONDA_DUR,
                                        dano=LOBO_SOL_ONDA_DANO, color=(170, 90, 95)))
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(40, 120)
                self._espera = random.uniform(1.0, 3.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * LOBO_SOL_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        rr = self.radio
        for lx in (-rr + 2, rr - 2):
            pygame.draw.line(pantalla, (48, 46, 54), (px + lx, py + 2), (px + lx, py + rr), 2)
        pygame.draw.ellipse(pantalla, c, (px - rr, py - rr + 3, rr * 2, rr + 4))
        nx = px + s * rr
        pygame.draw.circle(pantalla, c, (nx, py - 1), rr - 3)
        pygame.draw.polygon(pantalla, c, [(nx - 2, py - 4), (nx - 1, py - 8), (nx + 2, py - 4)])
        pygame.draw.polygon(pantalla, c, [(nx + 1, py - 4), (nx + 3, py - 8), (nx + 4, py - 4)])
        pygame.draw.circle(pantalla, (230, 40, 40), (nx + s * 2, py - 1), 2)   # ojo rojo siempre
        pygame.draw.circle(pantalla, (225, 225, 230), (px - s * rr, py + 2), 2)
        pygame.draw.circle(pantalla, (170, 50, 55), (px, py - rr - 2), 2)      # marca de lobo solitario
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = self.radio * 2
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - self.radio, py - self.radio - 8, w, 3))
            pygame.draw.rect(pantalla, (200, 90, 90), (px - self.radio, py - self.radio - 8, fw, 3))


# =====================================================================
# OSO  (hostil tanque territorial; vive en una roca gigante = su cueva)
# =====================================================================
OSO_MIN = 12
OSO_MAX = 12
OSO_VIDA = 150
OSO_RADIO = 16
OSO_MASA = 80.0
OSO_DANO = (15, 25)
OSO_EMPUJE = 25
OSO_ESCUDO_EXTRA = 0.30          # 30% extra de dano directo al escudo
OSO_DETECCION = 180.0
OSO_TERRITORIO = 1000.0
OSO_VEL = 90.0                   # lento
OSO_VEL_PERSEC = 120.0
OSO_ZARPAZO_CD = 1.4
OSO_REGEN_CUEVA = 5.0            # pv/s en la cueva
OSO_CICLO_CUEVA = 60.0          # cada 60 s sale
OSO_SALIDA_DUR = 10.0           # sale 10 s a "pescar"
OSO_RUGIDO_CD = 10.0            # en combate
OSO_RUGIDO_RALENT = 0.30
OSO_RUGIDO_DUR = 2.0
OSO_RUGIDO_DANO = 10            # dano magico de la onda (lo frena el escudo magico)
OSO_RUGIDO_RADIO = 230.0
OSO_RUGIDO_VEL = 340.0
OSO_COLOR = [(92, 70, 54), (78, 58, 44), (70, 52, 40)]
LAGO_MIN_PESCA = 120
ORBE_CURA = 20
ORBE_RADIO = 9
ORBE_SEPARACION = 36    # px a cada lado del orbe de vida para los de XP / Gacha (en la boca de la cueva)
ORBE_AFUERA = 20        # y algo hacia afuera de la roca
ENTRADA_RADIO = 40      # a esta distancia de la entrada estas 'dentro' de la cueva


class RugidoOnda:
    """Onda de choque (anillo que se expande): ralentiza al jugador y, si lleva dano, le
    hace dano magico una sola vez al pasar por el. La usan el oso (rugido) y el lobo solitario."""
    def __init__(self, centro, radio_max=OSO_RUGIDO_RADIO, vel=OSO_RUGIDO_VEL,
                 ralent=OSO_RUGIDO_RALENT, dur=OSO_RUGIDO_DUR, dano=OSO_RUGIDO_DANO,
                 tipo_dano="magico", color=(210, 190, 130)):
        self.centro = pygame.Vector2(centro)
        self.radio = 12.0
        self.activa = True
        self._golpeo = False
        self.radio_max = radio_max
        self.vel = vel
        self.ralent = ralent
        self.dur = dur
        self.dano = dano
        self.tipo_dano = tipo_dano
        self.color = color

    def actualizar(self, dt, jugador):
        self.radio += self.vel * dt
        if not self._golpeo and getattr(jugador, "detectable", True):
            d = (jugador.posicion - self.centro).length()
            if self.radio - jugador.radio - 10 <= d <= self.radio + jugador.radio:
                jugador.ralentizacion = max(getattr(jugador, "ralentizacion", 0.0), self.ralent)
                if hasattr(jugador, "tiempo_ralentizacion"):
                    jugador.tiempo_ralentizacion = max(getattr(jugador, "tiempo_ralentizacion", 0.0), self.dur)
                if self.dano > 0 and hasattr(jugador, "recibir_dano"):
                    jugador.recibir_dano(self.dano, self.tipo_dano)     # sin empuje: solo dano + ralentizacion
                self._golpeo = True
        if self.radio >= self.radio_max:
            self.activa = False

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0]); py = round(self.centro.y - desplazamiento[1])
        grosor = max(1, 4 - int(3 * self.radio / self.radio_max))
        pygame.draw.circle(pantalla, self.color, (px, py), int(self.radio), grosor)


class OrbeCueva:
    """Orbe dentro de la cueva (aparece al morir el oso), un solo uso. tipo: "vida" (cura +20),
    "xp" (+5 XP) o "gacha" (ruleta gratis de anillos). La XP y la ruleta las entrega SistemaFauna."""
    COLORES = {"vida": ((60, 180, 90), (120, 240, 150)), "xp": ((60, 120, 200), (120, 200, 255)),
               "gacha": ((200, 150, 40), (255, 215, 90))}

    def __init__(self, centro, tipo="vida"):
        self.centro = pygame.Vector2(centro)
        self.tipo = tipo
        self.activo = True
        self._fase = 0.0

    def actualizar(self, dt, jugador):
        if not self.activo:
            return
        self._fase += dt
        if (jugador.posicion - self.centro).length() <= jugador.radio + ORBE_RADIO:
            if self.tipo == "vida" and hasattr(jugador, "curar"):
                jugador.curar(ORBE_CURA)
            self.activo = False

    def dibujar(self, pantalla, desplazamiento):
        if not self.activo:
            return
        px = round(self.centro.x - desplazamiento[0]); py = round(self.centro.y - desplazamiento[1])
        pulso = int(abs(math.sin(self._fase * 2.5)) * 3)
        oscuro, claro = self.COLORES[self.tipo]
        pygame.draw.circle(pantalla, oscuro, (px, py), ORBE_RADIO + 3 + pulso, 1)
        pygame.draw.circle(pantalla, claro, (px, py), ORBE_RADIO)
        if self.tipo == "gacha":
            # destellos que giran alrededor
            for k in range(4):
                ang = self._fase * 2.0 + k * math.pi / 2
                sx = px + round(math.cos(ang) * (ORBE_RADIO + 7)); sy = py + round(math.sin(ang) * (ORBE_RADIO + 7))
                pygame.draw.circle(pantalla, (190, 120, 255), (sx, sy), 2)
        elif self.tipo == "xp":
            pygame.draw.line(pantalla, (235, 245, 255), (px - 4, py - 4), (px + 4, py + 4), 2)
            pygame.draw.line(pantalla, (235, 245, 255), (px - 4, py + 4), (px + 4, py - 4), 2)
        pygame.draw.circle(pantalla, (240, 250, 255), (px - 2, py - 3), 2)


class Oso(AnimalCombatible):
    XP = XP_OSO
    MONEDAS = MONEDAS_OSO

    def __init__(self, roca):
        self.roca = roca
        self.cueva = pygame.Vector2(roca.rect.center)
        self.cueva_radio = roca.rect.width / 2.0
        ang = getattr(roca, "angulo_entrada", None)     # la marca el terreno (marcar_cuevas)
        if ang is None:
            ang = random.uniform(0, math.tau)
        self.entrada_dir = pygame.Vector2(math.cos(ang), math.sin(ang))
        # La roca es cuadrada: distancia del centro a su borde en la direccion de la entrada (en
        # diagonal es mayor que el medio lado; si no, la boca y los orbes quedarian dentro de la roca)
        self.cueva_borde = self.cueva_radio / max(abs(self.entrada_dir.x), abs(self.entrada_dir.y))
        self.entrada = self.cueva + self.entrada_dir * (self.cueva_borde + 12)
        self.posicion = pygame.Vector2(self.cueva)
        self.radio = OSO_RADIO
        self.masa = OSO_MASA
        self.color = random.choice(OSO_COLOR)
        self.vida = OSO_VIDA
        self.vida_max = OSO_VIDA
        self.vivo = True
        self.estado = "cueva"            # cueva / salida / regresa / ataca
        self._t_ciclo = random.uniform(0, OSO_CICLO_CUEVA)
        self._t_salida = 0.0
        self._cd_zarpazo = 0.0
        self._cd_rugido = 0.0
        self._destino_pesca = None
        self.dir_mira = pygame.Vector2(1, 0)
        self.orbe = None
        self.orbes_extra = []            # orbes de XP y Gacha (al morir)
        self._t_reaparicion = 0.0
        self._init_combate()

    @property
    def en_cueva(self):
        return self.estado == "cueva"

    def renacer(self):
        """Oso nuevo en la misma cueva (misma entrada), con la vida llena y dentro de ella."""
        nuevo = Oso(self.roca)
        nuevo.entrada_dir = pygame.Vector2(self.entrada_dir)
        nuevo.entrada = pygame.Vector2(self.entrada)
        nuevo.cueva_borde = self.cueva_borde
        return nuevo

    def _boca(self):
        return self.cueva + self.entrada_dir * (self.cueva_borde + self.radio + 6)

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo or self.estado == "cueva":
            return 0                      # intocable dentro de la cueva
        self.vida -= cantidad
        self.estado = "ataca"
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
            self.dejar_orbes()
        return cantidad

    def dejar_orbes(self):
        """Al morir: orbe de vida en la entrada, orbe de XP a un lado y, con un 50 %, un orbe
        Gacha al otro (todos dentro de la cueva, separados para recogerlos uno a uno)."""
        lado = pygame.Vector2(-self.entrada_dir.y, self.entrada_dir.x) * ORBE_SEPARACION
        fuera = self.entrada + self.entrada_dir * ORBE_AFUERA     # un poco hacia afuera de la roca
        self.orbe = OrbeCueva(self.entrada, "vida")
        self.orbes_extra = [OrbeCueva(fuera + lado, "xp")]
        if random.random() < PROB_ORBE_GACHA:
            self.orbes_extra.append(OrbeCueva(fuera - lado, "gacha"))

    def actualizar(self, dt, jugador, amenazas, charcos, rugidos):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.controlado:
            return
        self._cd_zarpazo -= dt
        self._cd_rugido -= dt

        amenaza = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared()) if amenazas else None
        if amenaza is not None:
            da = (amenaza.posicion - self.posicion).length()
            da_cueva = (amenaza.posicion - self.cueva).length()
        else:
            da = da_cueva = float("inf")

        # Emboscada: si detecta una amenaza cerca de el o de su cueva, sale y ataca.
        if self.estado != "ataca" and amenaza is not None and (da < OSO_DETECCION or da_cueva < OSO_DETECCION):
            if self.estado == "cueva":
                self.posicion = self._boca()
            self.estado = "ataca"
            self._cd_rugido = 0.0

        if self.estado == "ataca":
            if amenaza is None or da_cueva > OSO_TERRITORIO:
                self.estado = "regresa"
                return
            if self._cd_rugido <= 0:
                self._cd_rugido = OSO_RUGIDO_CD
                rugidos.append(RugidoOnda(self.posicion))
            d = amenaza.posicion - self.posicion
            dist = d.length()
            if dist <= self.radio + getattr(amenaza, "radio", 10) + 4:
                if self._cd_zarpazo <= 0:
                    self._cd_zarpazo = OSO_ZARPAZO_CD
                    dano = random.randint(*OSO_DANO)
                    if not golpear_objetivo(self, amenaza, dano, OSO_EMPUJE):
                        return
                    if hasattr(amenaza, "escudo"):
                        amenaza.escudo = max(0.0, amenaza.escudo - dano * OSO_ESCUDO_EXTRA)
            elif dist > 0:
                self.posicion += d.normalize() * OSO_VEL_PERSEC * dt
                self.dir_mira = d.normalize()
            return

        if self.estado == "cueva":
            if self.vida < self.vida_max:
                self.vida = min(self.vida_max, self.vida + OSO_REGEN_CUEVA * dt)
            self._t_ciclo -= dt
            if self._t_ciclo <= 0:
                self._destino_pesca = self._lago_cercano(charcos)
                self.posicion = self._boca()
                self.estado = "salida"
                self._t_salida = OSO_SALIDA_DUR
            return

        if self.estado == "salida":
            self._t_salida -= dt
            objetivo = self._destino_pesca if self._destino_pesca is not None else self.cueva
            d = objetivo - self.posicion
            if d.length() > self.radio + 8:
                self.posicion += d.normalize() * OSO_VEL * dt
                self.dir_mira = d.normalize()
            if self._t_salida <= 0:
                self.estado = "regresa"
            return

        if self.estado == "regresa":
            d = self.cueva - self.posicion
            if d.length() <= self.cueva_radio + 2:
                self.posicion.update(self.cueva)
                self.estado = "cueva"
                self._t_ciclo = OSO_CICLO_CUEVA
            else:
                self.posicion += d.normalize() * OSO_VEL * dt
                self.dir_mira = d.normalize()
                if self.vida < self.vida_max:
                    self.vida = min(self.vida_max, self.vida + OSO_REGEN_CUEVA * 0.5 * dt)

    def dibujar_entrada(self, pantalla, desplazamiento):
        mx = self.cueva.x + self.entrada_dir.x * (self.cueva_borde - 4)
        my = self.cueva.y + self.entrada_dir.y * (self.cueva_borde - 4)
        px = round(mx - desplazamiento[0]); py = round(my - desplazamiento[1])
        pygame.draw.circle(pantalla, (34, 28, 26), (px, py), 12)
        pygame.draw.circle(pantalla, (12, 10, 10), (px, py), 9)

    def _lago_cercano(self, charcos):
        grandes = [c for c in charcos if c.radio >= LAGO_MIN_PESCA]
        if not grandes:
            return None
        c = min(grandes, key=lambda ch: (ch.centro - self.cueva).length_squared())
        d = self.cueva - c.centro
        base = d.normalize() if d.length() > 1 else pygame.Vector2(1, 0)
        return c.centro + base * (c.radio + 10)

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo or self.estado == "cueva":
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-10, 10):
            pygame.draw.line(pantalla, (54, 40, 30), (px + lx, py + 4), (px + lx, py + 14), 3)
        pygame.draw.ellipse(pantalla, c, (px - 16, py - 9, 32, 20))
        nx = px + s * 15
        pygame.draw.circle(pantalla, c, (nx, py - 2), 8)
        pygame.draw.circle(pantalla, (60, 44, 34), (nx + s * 5, py - 1), 3)
        pygame.draw.circle(pantalla, c, (nx - 4, py - 9), 3)
        pygame.draw.circle(pantalla, c, (nx + 4, py - 9), 3)
        ojo = (230, 70, 55) if self.estado == "ataca" else (30, 22, 18)
        pygame.draw.circle(pantalla, ojo, (nx + s * 2, py - 3), 1)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 6, 1)
        if self.vida < self.vida_max:
            w = 32; fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 16, py - 22, w, 4))
            pygame.draw.rect(pantalla, (210, 110, 70), (px - 16, py - 22, fw, 4))


# =====================================================================
# COCODRILO  (depredador de emboscada acuatica; sumergido = intocable)
# =====================================================================
COCODRILO_VIDA = 70
COCODRILO_ESCUDO = 30            # escudo fisico, mismas reglas que el del jugador
COCODRILO_RADIO = 13
COCODRILO_MASA = 30.0
COCODRILO_DANO = (18, 30)
COCODRILO_EMPUJE = 20
COCODRILO_VEL_AGUA = 210.0       # muy veloz en el agua
COCODRILO_VEL_TIERRA = 65.0      # lento fuera del agua
COCODRILO_ORILLA = 40.0          # margen de orilla para detectarte
COCODRILO_PERSIGUE = 120.0       # cuanto sale a tierra tras de ti
COCODRILO_MORDIDA_CD = 1.2
COCODRILO_COLOR = (70, 92, 60)


# Cocodrilos: 2 por lago profundo; 3 si el lago es muy grande.
COCODRILO_POR_LAGO = 2
COCODRILO_POR_LAGO_GRANDE = 3
COCODRILO_LAGO_GRANDE = 600          # radio a partir del cual el lago lleva 3 cocodrilos


class Cocodrilo(AnimalCombatible):
    XP = XP_COCODRILO
    MONEDAS = MONEDAS_COCODRILO

    def __init__(self, charco):
        self.charco = charco
        self.centro_lago = pygame.Vector2(charco.centro)
        self.posicion = pygame.Vector2(charco.centro)
        self.radio = COCODRILO_RADIO
        self.masa = COCODRILO_MASA
        self.color = COCODRILO_COLOR
        self.vida = COCODRILO_VIDA
        self.vida_max = COCODRILO_VIDA
        self.escudo_max = float(COCODRILO_ESCUDO)
        self.tiempo_sin_dano_escudo = 0.0
        self.vivo = True
        self.estado = "acecho"       # acecho (sumergido, intocable) / ataca / regresa
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self._cd_mordida = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()
        self.escudo = float(COCODRILO_ESCUDO)   # tras _init_combate (que lo reinicia a 0)
        self._objetivo = None
        self._agredido = False
        self._desde = pygame.Vector2()

    @property
    def sumergido(self):
        return self.estado != "ataca"     # intocable salvo cuando emerge a morder

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo or self.sumergido:
            return 0
        d = max(0.0, float(cantidad))
        if d <= 0:
            return 0
        if tipo_dano == "magico":
            absorbido, dano_vida = 0.0, d          # no tiene escudo magico
        else:
            absorbido, dano_vida = repartir_dano(d, tipo_dano, self.escudo)
            self.escudo = max(0.0, round(self.escudo - absorbido, 2))
            self.tiempo_sin_dano_escudo = 0.0
        self.vida = max(0.0, round(self.vida - dano_vida, 2))
        self._agredido = True
        self._desde = pygame.Vector2(direccion_empuje) if (direccion_empuje is not None and direccion_empuje.length() > 0) else pygame.Vector2()
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return round(absorbido + dano_vida, 2)

    def _regen_escudo(self, dt):
        if self.escudo < self.escudo_max:
            self.tiempo_sin_dano_escudo += dt
            if self.tiempo_sin_dano_escudo >= REGEN_ESCUDO_RETRASO:
                self.escudo = min(self.escudo_max, round(self.escudo + REGEN_ESCUDO_POR_SEGUNDO * dt, 2))

    def _vel(self):
        return COCODRILO_VEL_AGUA if self.charco.contiene(self.posicion) else COCODRILO_VEL_TIERRA

    def actualizar(self, dt, jugador, amenazas=None):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.controlado:
            return
        self._cd_mordida -= dt
        self._regen_escudo(dt)
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()

        det = getattr(jugador, "detectable", True)

        # Emboscada: emerge si entras a la zona profunda peligrosa del lago.
        if self.estado != "ataca" and det and self.charco.en_zona_peligro(jugador.posicion):
            self.estado = "ataca"
            self._objetivo = None

        # Si lo atacan (p. ej. una mascota), cambia de objetivo al atacante.
        if self._agredido:
            self._agredido = False
            self.estado = "ataca"
            if amenazas:
                origen = self.posicion - self._desde
                self._objetivo = min(amenazas, key=lambda o: (o.posicion - origen).length_squared())

        if self.estado == "ataca":
            objetivo = self._objetivo
            if objetivo is None or not getattr(objetivo, "vivo", True):
                objetivo = jugador if det else None
                self._objetivo = None
            if objetivo is None:
                self.estado = "regresa"
                return
            if (objetivo.posicion - self.centro_lago).length() > self.charco.radio + COCODRILO_PERSIGUE:
                self.estado = "regresa"
                self._objetivo = None
                return
            d = objetivo.posicion - self.posicion
            dist = d.length()
            if dist <= self.radio + getattr(objetivo, "radio", 10) + 4:
                if self._cd_mordida <= 0:
                    self._cd_mordida = COCODRILO_MORDIDA_CD
                    dano = random.randint(*COCODRILO_DANO)
                    if not golpear_objetivo(self, objetivo, dano, COCODRILO_EMPUJE):
                        return
            elif dist > 0:
                self.posicion += d.normalize() * self._vel() * dt
                self.dir_mira = d.normalize()
            return

        if self.estado == "regresa":
            d = self.centro_lago - self.posicion
            if d.length() <= 8:
                self.estado = "acecho"
            else:
                self.posicion += d.normalize() * self._vel() * dt
                self.dir_mira = d.normalize()
            return

        # acecho: patrulla la zona del lago (tematico: "caza" fauna acuatica que reaparece)
        self._espera -= dt
        d = self.destino - self.posicion
        if self._espera <= 0:
            ang = random.uniform(0, math.tau)
            r = random.uniform(0, max(0.0, self.charco.radio * 0.5))
            self.destino = self.centro_lago + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
            self._espera = random.uniform(1.5, 4.0)
        elif d.length() > 3:
            self.posicion += d.normalize() * (COCODRILO_VEL_AGUA * 0.4) * dt
            self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        s = 1 if self.dir_mira.x >= 0 else -1
        if self.sumergido:
            # Sumergido: solo una sombra tenue y los ojos sobre el agua.
            pygame.draw.ellipse(pantalla, (40, 62, 56), (px - 12, py - 4, 24, 8))
            pygame.draw.circle(pantalla, (225, 225, 190), (px + s * 4, py - 2), 1)
            pygame.draw.circle(pantalla, (225, 225, 190), (px + s * 8, py - 2), 1)
            return
        c = self.color
        pygame.draw.polygon(pantalla, (60, 80, 52), [(px - s * 16, py), (px - s * 28, py - 4), (px - s * 28, py + 4)])  # cola
        pygame.draw.ellipse(pantalla, c, (px - 16, py - 6, 32, 12))         # cuerpo
        for lx in (-8, 6):
            pygame.draw.line(pantalla, (52, 70, 46), (px + lx, py + 5), (px + lx + s * 4, py + 9), 2)  # patas
        nx = px + s * 16
        pygame.draw.ellipse(pantalla, c, (nx - 6, py - 4, 16, 8))           # hocico
        pygame.draw.circle(pantalla, (225, 225, 170), (nx - 2, py - 5), 1)  # ojo
        for i in range(-4, 8, 3):
            pygame.draw.line(pantalla, (240, 240, 230), (nx + i, py + 1), (nx + i, py + 3), 1)  # dientes
        if self.vida < self.vida_max or self.escudo < self.escudo_max:
            w = 32
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 16, py - 16, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 16, py - 16, fw, 3))
            sw = int(w * self.escudo / self.escudo_max)
            pygame.draw.rect(pantalla, (45, 60, 80), (px - 16, py - 20, w, 2))
            pygame.draw.rect(pantalla, (120, 180, 240), (px - 16, py - 20, sw, 2))
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 6, 1)
