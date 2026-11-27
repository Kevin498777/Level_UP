"""Diseno del mapa: las "reglas" con las que el generador asistido reparte el terreno (Fase 2 del
plan de NPC). Cada regla es un numero con nombre, asi tus indicaciones se traducen en cambios
pequenos y se pueden repetir.

- Regiones: norte, sur, este y oeste se miden con coordenadas relativas (u hacia el este, v hacia
  el sur, de -1 a 1). Un factor de region multiplica la probabilidad de que algo aparezca ahi;
  crece de forma suave desde el centro (1) hasta el borde de esa region (el factor completo).
- Las posiciones fijas van en coordenadas relativas para que el diseno no dependa del tamano
  exacto del mapa. Las casillas de la vista previa (columnas A-J, filas 1-10) se pasan a
  coordenadas relativas con celdas("C10", "H10").
"""
import random

import pygame

REGIONES = ("norte", "sur", "este", "oeste")
COLUMNAS = "ABCDEFGHIJ"
CASILLAS = 10


def celdas(desde, hasta=None):
    """Rectangulo relativo (u0, v0, u1, v1) que cubre las casillas de 'desde' a 'hasta'
    (p. ej. celdas("C10", "H10")). Columnas A-J de oeste a este y filas 1-10 de norte a sur."""
    hasta = hasta or desde
    c0, f0 = COLUMNAS.index(desde[0]), int(desde[1:]) - 1
    c1, f1 = COLUMNAS.index(hasta[0]), int(hasta[1:]) - 1
    paso = 2.0 / CASILLAS
    return (-1 + min(c0, c1) * paso, -1 + min(f0, f1) * paso, -1 + (max(c0, c1) + 1) * paso, -1 + (max(f0, f1) + 1) * paso)


class Forma:
    """Circulo o rectangulo en coordenadas del mundo (zonas despejadas, regiones del diseno)."""

    def __init__(self, circulo=None, rect=None):
        self.circulo = circulo          # (centro Vector2, radio)
        self.rect = rect                # pygame.Rect

    def contiene(self, p, margen=0.0):
        """True si el punto esta dentro de la forma agrandada 'margen' px."""
        if self.circulo is not None:
            c, r = self.circulo
            return (pygame.Vector2(p) - c).length() < r + margen
        return self.rect.inflate(margen * 2, margen * 2).collidepoint(p)


class Diseno:
    """Reglas por defecto = el generador de siempre (todo repartido al azar, sin regiones)."""
    nombre = "aleatorio"
    # Bosques pequenos/medianos repartidos y bosques fijos [(u, v, radio, densidad, nombre)]
    bosques = (10, 16)
    bosque_radio = (500, 1600)
    densidad_bosque = 0.22
    bosques_fijos = ()
    # Bosques con la forma de unas casillas: [(nombre, [rects relativos], densidad)]
    bosques_region = ()
    arboles_solitarios = 20
    # Praderas (pasto y flores), praderas fijas [(u, v, radio)] y pastizales (madrigueras)
    praderas = (8, 14)
    pradera_radio = (600, 1800)
    praderas_fijas = ()
    pastizales = (8, 12)
    # Lagos: 'lagunas' = lagos grandes que se colocan primero (radio > 300 = con zona profunda);
    # lagos fijos [(u, v, radio, nombre)] antes que todo (pueden llegar al borde)
    lagos = None                    # None = la escala por area de siempre (mundo.MIN/MAX_CHARCOS)
    lago_radio = None               # None = mundo.RADIO_CHARCO_MIN..MAX (lagos normales)
    lagunas = 0
    laguna_radio = (500, 750)
    lagos_fijos = ()
    # Rocas sueltas y montanas (grupos de rocas grandes) [(u, v, radio, n_rocas, prob_gigante)]
    rocas = None                    # None = la escala por area de siempre
    montanas = ()
    # Montanas de piedras especiales (indestructibles) que llenan una region:
    # [(nombre, rect relativo, (lado_min, lado_max))]
    montanas_region = ()
    # Cuevas de oso: cuantas, cuantas como minimo en cada region y separacion entre ellas
    cuevas = None                   # None = OSO_MIN..OSO_MAX al azar (como siempre)
    cuevas_por_region = {}
    separacion_cuevas = 0
    # Factores por region de cada elemento: {clave: {region: factor}}
    pesos = {}
    # Zonas despejadas (sin obstaculos): ("circulo", u, v, radio_px, nombre) o
    # ("rect", (u0, v0, u1, v1), nombre)
    zonas_libres = ()
    sin_vegetacion = ()             # rects relativos sin arboles ni arbustos (p. ej. la montana)
    sin_borde = ()                  # rects relativos donde se puede llegar hasta el borde del mapa
    # Zonas con nombre: dicts {nombre, u, v, radio, descripcion} y opcionalmente "rects"
    zonas = ()
    # Puertas a otros mapas (aun sin funcionar): [(nombre, destino, lado, u, v)]
    puertas = ()
    # Puntos de aparicion por raza: {raza: (zona, cantidad)}
    aparicion = {}

    def factor(self, clave, u, v):
        """Peso de 'clave' en el punto relativo (u, v): 1 en el centro, el factor de la region
        hacia su borde (interpolado; si un punto esta en dos regiones se suman los extras)."""
        regiones = self.pesos.get(clave)
        if not regiones:
            return 1.0
        pertenencia = {"este": max(0.0, u), "oeste": max(0.0, -u), "sur": max(0.0, v), "norte": max(0.0, -v)}
        return max(0.05, 1.0 + sum((f - 1.0) * pertenencia[r] for r, f in regiones.items()))

    def factor_maximo(self, clave):
        return max([1.0] + [1.0 + max(0.0, f - 1.0) for f in self.pesos.get(clave, {}).values()]) * 2

    def punto(self, limite, clave, margen=0.0, rng=random):
        """Punto al azar con la probabilidad repartida segun los factores de 'clave'."""
        maximo = self.factor_maximo(clave)
        for _ in range(200):
            p = limite.punto_al_azar(margen, rng)
            u, v = limite.relativo(p)
            if rng.random() * maximo <= self.factor(clave, u, v):
                return p
        return limite.punto_al_azar(margen, rng)

    def absoluto(self, limite, u, v):
        return pygame.Vector2(limite.centro.x + u * limite.mitad, limite.centro.y + v * limite.mitad)

    def rect_absoluto(self, limite, rel):
        u0, v0, u1, v1 = rel
        a, b = self.absoluto(limite, u0, v0), self.absoluto(limite, u1, v1)
        return pygame.Rect(round(a.x), round(a.y), round(b.x - a.x), round(b.y - a.y))

    def zonas_libres_abs(self, limite):
        """Formas (Forma) de las zonas despejadas, en coordenadas del mundo."""
        formas = []
        for z in self.zonas_libres:
            if z[0] == "circulo":
                formas.append(Forma(circulo=(self.absoluto(limite, z[1], z[2]), z[3])))
            else:
                formas.append(Forma(rect=self.rect_absoluto(limite, z[1])))
        return formas

    def formas_sin_vegetacion(self, limite):
        return [Forma(rect=self.rect_absoluto(limite, r)) for r in self.sin_vegetacion]

    def region_de(self, u, v):
        """Region dominante de un punto relativo (o 'centro' cerca del medio)."""
        if max(abs(u), abs(v)) < 0.25:
            return "centro"
        if abs(u) >= abs(v):
            return "este" if u > 0 else "oeste"
        return "sur" if v > 0 else "norte"


def _px(px):
    """px del mundo -> coordenada relativa (el mapa principal mide 17 700 px: mitad 8850)."""
    return px / 8850.0


class DisenoPrincipal(Diseno):
    """Mapa principal, version 2 (tus indicaciones del 27/11/2026).
    v1: bosques pequenos por todas partes y arboles casi por todo el mapa; praderas, rocas, lagos
    y lagunas repartidos; norte = humanos, este = praderas y semihumanos, sur = bosque denso y
    elfos, oeste = rocas y cuevas y enanos. (Despues todos se reparten por el mapa.)
    v2: el gran bosque ocupa C10-H10 y la mitad de abajo de D9-G9 con un camino a la puerta de la
    Aldea Elfica (borde sur, entre E10 y F10); un lago enorme con cocodrilos en I8-J9 que llega al
    borde; una montana de piedras especiales en A4-A7 con un paso a la puerta de la Gran Montana
    Antigua (borde oeste, entre A5 y A6); J5-J6 todo pradera con la puerta de la Aldea Semihumana
    (borde este); la puerta de la Ciudad Humana en el borde norte, entre E1 y F1, protegida por
    dos guardianes con Mandoble, uno a cada lado. Las puertas aun no funcionan."""
    nombre = "principal"
    bosques = (30, 38)
    bosque_radio = (300, 800)
    densidad_bosque = 0.24
    # Gran bosque del sur (elfos): C10-H10 y la mitad de abajo de D9-G9
    BOSQUE_SUR = (celdas("C10", "H10"), (celdas("D9")[0], 0.7, celdas("G9")[2], 0.8))
    bosques_region = (("Bosque de los elfos", BOSQUE_SUR, 0.20),)   # los circulos se solapan: ~0.34 real
    arboles_solitarios = 650
    praderas = (13, 18)
    pradera_radio = (600, 1600)
    praderas_fijas = ((0.9, -0.1, 1300), (0.9, 0.1, 1300))           # J5 y J6 toda pradera
    pastizales = (9, 13)
    lagos = (24, 32)
    lago_radio = (150, 300)         # lagos normales sin zona profunda; los grandes son las lagunas
    lagunas = 7
    # Lago enorme en I8-J9 (llega al borde este)
    LAGO_ESTE = celdas("I8", "J9")
    lagos_fijos = ((0.8, 0.6, 1770, "Gran lago del este"),)
    rocas = (620, 900)
    montanas = (
        (-0.70, -0.55, 750, 22, 0.35), (-0.62, -0.15, 800, 24, 0.35), (-0.64, 0.15, 750, 22, 0.35),
        (-0.66, 0.55, 750, 22, 0.35), (-0.86, 0.75, 650, 18, 0.35), (-0.52, -0.78, 650, 18, 0.30),
        (-0.86, -0.72, 600, 16, 0.30),
    )
    # Gran Montana Antigua: A4-A7, piedras especiales grandes e indestructibles, hasta el borde
    MONTANA_OESTE = celdas("A4", "A7")
    montanas_region = (("Gran Montaña Antigua", MONTANA_OESTE, (300, 500)),)
    cuevas = 12
    cuevas_por_region = {"oeste": 7}
    separacion_cuevas = 1500
    pesos = {
        "bosque": {"sur": 1.4},
        "arbol": {"sur": 1.3, "oeste": 0.7},
        "arbusto": {"sur": 1.5},
        "pradera": {"este": 3.5, "oeste": 0.5},
        "pastizal": {"este": 2.5},
        "roca": {"oeste": 4.0, "este": 0.6},
    }
    zonas_libres = (
        # Guardianes de la Ciudad Humana: despejado alrededor de la puerta norte
        ("circulo", 0.0, -1 + _px(700), 700, "Puerta de la Ciudad Humana"),
        # Paso de 250 px por la montana hasta la puerta de la Gran Montana Antigua
        ("rect", (-1.0, -_px(125), MONTANA_OESTE[2] + _px(150), _px(125)), "Paso de la Gran Montana Antigua"),
        # Camino de 200 px por el bosque hasta la puerta de la Aldea Elfica
        ("rect", (-_px(100), 0.66, _px(100), 1.0), "Camino a la Aldea Elfica"),
        ("circulo", 0.0, 1 - _px(250), 300, "Puerta de la Aldea Elfica"),
        ("circulo", 1 - _px(250), 0.0, 300, "Puerta de la Aldea Semihumana"),
    )
    sin_vegetacion = (MONTANA_OESTE,)
    sin_borde = (MONTANA_OESTE, LAGO_ESTE)
    zonas = (
        {"nombre": "Guardian", "u": 0.0, "v": -1 + _px(700), "radio": 700,
         "descripcion": "Dos guardianes con Mandoble protegen la puerta de la Ciudad Humana"},
        {"nombre": "Humanos", "u": 0.0, "v": -0.55, "radio": 2600, "descripcion": "Norte: aparicion de los humanos"},
        {"nombre": "Semihumanos", "u": 0.62, "v": 0.0, "radio": 2600,
         "descripcion": "Este: praderas, aparicion de los semihumanos"},
        {"nombre": "Elfos", "u": 0.0, "v": 0.85, "radio": 2600, "rects": BOSQUE_SUR,
         "descripcion": "Sur: el gran bosque, aparicion de los elfos"},
        {"nombre": "Enanos", "u": -0.68, "v": 0.0, "radio": 2800,
         "descripcion": "Oeste: montanas y cuevas, aparicion de los enanos"},
    )
    puertas = (
        ("Ciudad Humana", "ciudad_humana", "norte", 0.0, -1.0),
        ("Entrada a la Aldea Élfica", "aldea_elfica", "sur", 0.0, 1.0),
        ("Gran Montaña Antigua", "gran_montana_antigua", "oeste", -1.0, 0.0),
        ("Aldea Semihumana", "aldea_semihumana", "este", 1.0, 0.0),
    )
    aparicion = {"Guardian": ("Guardian", 2), "Humanos": ("Humanos", 6), "Semihumanos": ("Semihumanos", 4),
                 "Elfos": ("Elfos", 4), "Enanos": ("Enanos", 4)}


DISENOS = {"aleatorio": Diseno(), "principal": DisenoPrincipal()}
