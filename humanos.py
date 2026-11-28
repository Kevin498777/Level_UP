"""Humanos: la primera raza de NPC (Fase 4 del plan de NPC).

- HUMANOS_CANTIDAD (6) en el mapa, en los puntos de aparicion del norte (mapa principal).
- Estadisticas iniciales normales (las del jugador al crearlo), un arma y 3 habilidades al azar;
  nivel maximo 40 (el del jugador) y una sola potenciada desde el nivel 20 (cerebro.py).
- Sin odio: no empiezan peleas con otros personajes; si les golpean se defienden.
- Suben de nivel con la XP real de lo que cazan; no usan monedas, Gacha ni vendedores y no tocan
  nada del jugador (frutales, cofres, orbes).
- Si mueren reaparecen REAPARICION s despues, al nivel 1, en uno de los puntos de aparicion.
- Matar a un humano da al jugador XP (2 x nivel) y monedas (5 + nivel) y suma ASESINO_POR_HUMANO a
  su estadistica oculta "asesino" (servira para la Ciudad Humana: con 100 no se podra entrar).
"""
import random

import pygame

import habilidades as H
import herramientas as T
from cerebro import CerebroBot
from navegacion import Navegador
from personaje import Personaje

HUMANOS_CANTIDAD = 6
REAPARICION = 300.0             # s (como los vendedores)
ASESINO_POR_HUMANO = 10
XP_POR_NIVEL_HUMANO = 2         # XP que da al jugador matar a un humano: 2 x su nivel
MONEDAS_BASE_HUMANO = 5         # monedas: 5 + su nivel
ESTADISTICAS_INICIALES = {"vida": 30, "fuerza": 2, "velocidad": 1, "energia": 100, "escudo": 0,
                          "escudo_magico": 0, "tamano": 1}       # las de main.generar_estadisticas
COLORES_HUMANOS = ((214, 176, 120), (190, 150, 110), (226, 196, 150), (170, 132, 96), (240, 210, 170), (200, 160, 130))
TECLAS = ((pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4"))


def crear_humano(indice, punto, rng):
    """Un humano de nivel 1 con un arma y 3 habilidades al azar."""
    arma = T.crear_herramienta(rng.choice(sorted(T.HERRAMIENTAS_DISPONIBLES)))
    nombres = rng.sample(sorted(H.HABILIDADES_DISPONIBLES), 3)
    habs = [H.crear_habilidad(n) for n in nombres]
    for h, (tecla, texto) in zip(habs, TECLAS):
        h.asignar_tecla(tecla, texto)
    e = ESTADISTICAS_INICIALES
    p = Personaje("Humano %d" % (indice + 1), punto[0], punto[1], e["tamano"], e["velocidad"], e["vida"], e["fuerza"],
                  e["energia"], e["escudo"], COLORES_HUMANOS[indice % len(COLORES_HUMANOS)], habs, arma, e["escudo_magico"])
    p.raza = "Humanos"
    p.toma_objetos = False          # no toca nada del jugador: frutales, cofres ni orbes
    return p


class PoblacionHumanos:
    """Mantiene a los humanos en el mundo: los crea, los cuenta y los hace reaparecer."""

    def __init__(self, ctx, puntos, rng=None, cantidad=HUMANOS_CANTIDAD):
        self.ctx = ctx
        self.rng = rng or random.Random()
        self.puntos = [pygame.Vector2(p) for p in puntos] or [pygame.Vector2(ctx.limite.centro)]
        self.cerebros = {}              # indice -> cerebro (recuerda lo que le mato entre vidas)
        self.esperas = {}               # indice -> segundos para reaparecer
        self.vivos = {}                 # indice -> personaje
        self._temidos = {}              # indice -> especies que le mataron (se conserva al reaparecer)
        for k in range(cantidad):
            self._nacer(k, self.puntos[k % len(self.puntos)])

    def _nacer(self, k, punto):
        humano = crear_humano(k, punto, self.rng)
        cerebro = self.cerebros.get(k)
        if cerebro is None:
            cerebro = CerebroBot(Navegador(self.ctx.cola_rutas), random.Random(self.rng.random()), odio=False)
            self.cerebros[k] = cerebro
        else:
            cerebro.__init__(Navegador(self.ctx.cola_rutas), cerebro.rng, odio=False)   # otra vida, otro estilo
            cerebro.temidos = dict(self._temidos.get(k, {}))
        humano.indice_humano = k
        self.ctx.agregar_combatiente(humano, cerebro)
        self.vivos[k] = humano

    def murio(self, humano):
        """El mundo lo retiro (vida 0): recuerda quien le mato y espera para reaparecer."""
        k = getattr(humano, "indice_humano", None)
        if k is None or self.vivos.get(k) is not humano:
            return
        cerebro = self.cerebros[k]
        asesino = getattr(humano, "ultimo_agresor", None)
        if asesino is not None and not isinstance(asesino, Personaje):
            cerebro.recordar_muerte(asesino)
        self._temidos[k] = dict(cerebro.temidos)
        del self.vivos[k]
        self.esperas[k] = REAPARICION

    def actualizar(self, dt):
        for k in list(self.esperas):
            self.esperas[k] -= dt
            if self.esperas[k] <= 0:
                del self.esperas[k]
                self._nacer(k, self.rng.choice(self.puntos))


def recompensa_por_humano(humano):
    """(XP, monedas) que gana el jugador al matar a un humano."""
    return XP_POR_NIVEL_HUMANO * humano.nivel, MONEDAS_BASE_HUMANO + humano.nivel
