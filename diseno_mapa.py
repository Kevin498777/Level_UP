"""Diseno del mapa: las "reglas" con las que el generador asistido reparte el terreno (Fase 2 del
plan de NPC). Cada regla es un numero con nombre, asi tus indicaciones se traducen en cambios
pequenos y se pueden repetir.

- Regiones: norte, sur, este y oeste se miden con coordenadas relativas (u hacia el este, v hacia
  el sur, de -1 a 1). Un factor de region multiplica la probabilidad de que algo aparezca ahi;
  crece de forma suave desde el centro (1) hasta el borde de esa region (el factor completo).
- Las posiciones fijas (bosque del sur, zona del guardian...) van en coordenadas relativas para
  que el diseno no dependa del tamano exacto del mapa.
"""
import random

import pygame

REGIONES = ("norte", "sur", "este", "oeste")


class Diseno:
    """Reglas por defecto = el generador de siempre (todo repartido al azar, sin regiones)."""
    nombre = "aleatorio"
    # Bosques pequenos/medianos repartidos y bosques fijos [(u, v, radio, densidad, nombre)]
    bosques = (10, 16)
    bosque_radio = (500, 1600)
    densidad_bosque = 0.22
    bosques_fijos = ()
    arboles_solitarios = 20
    # Praderas (pasto y flores) y pastizales (pasto alto, madrigueras)
    praderas = (8, 14)
    pradera_radio = (600, 1800)
    pastizales = (8, 12)
    # Lagos: 'lagunas' = lagos grandes que se colocan primero (radio > 300 = con zona profunda)
    lagos = None                    # None = la escala por area de siempre (mundo.MIN/MAX_CHARCOS)
    lago_radio = None               # None = mundo.RADIO_CHARCO_MIN..MAX (lagos normales)
    lagunas = 0
    laguna_radio = (500, 750)
    # Rocas sueltas y montanas (grupos de rocas grandes) [(u, v, radio, n_rocas, prob_gigante)]
    rocas = None                    # None = la escala por area de siempre
    montanas = ()
    # Cuevas de oso: cuantas, cuantas como minimo en cada region y separacion entre ellas
    cuevas = None                   # None = OSO_MIN..OSO_MAX al azar (como siempre)
    cuevas_por_region = {}
    separacion_cuevas = 0
    # Factores por region de cada elemento: {clave: {region: factor}}
    pesos = {}
    # Zonas despejadas (sin obstaculos) [(u, v, radio_px, nombre)] y zonas con nombre
    zonas_libres = ()
    zonas = ()                      # [(nombre, u, v, radio_px, descripcion)]
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

    def zonas_libres_abs(self, limite):
        return [(self.absoluto(limite, u, v), r) for u, v, r, _ in self.zonas_libres]

    def region_de(self, u, v):
        """Region dominante de un punto relativo (o 'centro' cerca del medio)."""
        if max(abs(u), abs(v)) < 0.25:
            return "centro"
        if abs(u) >= abs(v):
            return "este" if u > 0 else "oeste"
        return "sur" if v > 0 else "norte"


class DisenoPrincipal(Diseno):
    """Mapa principal, version 1 (tus indicaciones del 27/11/2026):
    - Bosques pequenos por todas partes y arboles casi por todo el mapa; praderas, rocas, lagos
      y lagunas (lagos grandes) repartidos.
    - Norte, en el centro y junto al limite: la zona del guardian (despejada). Los humanos
      aparecen en el norte.
    - Este: mas praderas; ahi aparecen los semihumanos.
    - Sur: un bosque mas denso; ahi aparecen los elfos.
    - Oeste: mas rocas y cuevas, como montanas; ahi aparecen los enanos.
    (Despues todos se reparten por el mapa, como la fauna.)"""
    nombre = "principal"
    bosques = (30, 38)
    bosque_radio = (300, 800)
    densidad_bosque = 0.24
    # Gran bosque del sur, mas denso que los demas
    bosques_fijos = ((0.0, 0.66, 2400, 0.34, "Bosque del sur"),)
    arboles_solitarios = 650
    praderas = (13, 18)
    pradera_radio = (600, 1600)
    pastizales = (9, 13)
    lagos = (24, 32)
    lago_radio = (150, 300)         # lagos normales sin zona profunda; los grandes son las lagunas
    lagunas = 8
    rocas = (620, 900)
    montanas = (
        (-0.82, -0.55, 750, 22, 0.35), (-0.70, -0.20, 850, 26, 0.35), (-0.85, 0.15, 800, 24, 0.35),
        (-0.66, 0.48, 750, 22, 0.35), (-0.86, 0.75, 650, 18, 0.35), (-0.52, -0.78, 650, 18, 0.30),
        (-0.48, 0.05, 600, 16, 0.30),
    )
    cuevas = 12
    cuevas_por_region = {"oeste": 7}
    separacion_cuevas = 1500
    pesos = {
        "bosque": {"sur": 1.8},
        "arbol": {"sur": 1.6, "oeste": 0.7},
        "arbusto": {"sur": 1.5},
        "pradera": {"este": 3.5, "oeste": 0.5},
        "pastizal": {"este": 2.5},
        "roca": {"oeste": 4.0, "este": 0.6},
    }
    # Zona del guardian: norte, en el centro, junto al limite (con 1000 px hasta el borde)
    zonas_libres = ((0.0, -0.887, 700, "Zona del guardian"),)
    zonas = (
        ("Guardian", 0.0, -0.887, 700, "Zona despejada del guardian, al norte junto al limite"),
        ("Humanos", 0.0, -0.55, 2600, "Norte: aparicion de los humanos"),
        ("Semihumanos", 0.62, 0.0, 2600, "Este: praderas, aparicion de los semihumanos"),
        ("Elfos", 0.0, 0.66, 2400, "Sur: bosque denso, aparicion de los elfos"),
        ("Enanos", -0.68, 0.0, 2800, "Oeste: montanas y cuevas, aparicion de los enanos"),
    )
    aparicion = {"Guardian": ("Guardian", 1), "Humanos": ("Humanos", 6), "Semihumanos": ("Semihumanos", 4),
                 "Elfos": ("Elfos", 4), "Enanos": ("Enanos", 4)}


DISENOS = {"aleatorio": Diseno(), "principal": DisenoPrincipal()}
