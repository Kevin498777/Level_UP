"""Prueba de humo del bucle real (sin ventana) con Corrosion nv30: dispara cada segundo, camina
entre la fauna con el humo y comprueba que no hay errores y que algo queda corroido."""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import random
sys.path.insert(0, os.getcwd())
import pygame
import mundo
import fauna as F
from habilidades import GolpeDeSuerte

capt = {}
_Pers = mundo.Personaje


class P(_Pers):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        capt["j"] = self


mundo.Personaje = P
_SF = F.SistemaFauna.__init__


def _sf(self, *a, **k):
    _SF(self, *a, **k)
    capt["fauna"] = self


F.SistemaFauna.__init__ = _sf

d = GolpeDeSuerte()
while d.nivel < 20:
    d.subir_nivel()
d.desbloquear_potenciada()
while d.subir_nivel():
    pass
orden = list(GolpeDeSuerte.AF_RESULTADOS) + [GolpeDeSuerte.NADA]
salidos = []
def sortear_ciclo():
    r = orden[len(salidos) % len(orden)]
    salidos.append(r)
    return r
d.sortear = sortear_ciclo

frame = [0]
vistos = {"corroidos_max": 0, "maniqui": False}
_get = pygame.event.get
random.seed(3)


def tecla(k, tipo=pygame.KEYDOWN):
    return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)


def eventos():
    _get()
    f = frame[0]
    frame[0] += 1
    j = capt.get("j")
    ev = []
    if j is None:
        return ev
    j.energia = j.energia_max
    if f == 5:
        # acercarse a una manada de lobos
        lobos = [l for m in getattr(capt["fauna"], "manadas", []) for l in getattr(m, "lobos", [])]
        objetivo = min(lobos, key=lambda l: (l.posicion - j.posicion).length()) if lobos else None
        if objetivo is not None:
            j.posicion = objetivo.posicion + pygame.Vector2(80, 0)
            j.destino = pygame.Vector2(j.posicion)
    if f % 60 == 0 and f > 5:
        d.estado = "LISTA"                    # sin esperar bloqueos/recargas en la prueba
        ev.append(tecla(d.tecla))
        ev.append(tecla(d.tecla, pygame.KEYUP))
    if f % 45 == 0 and f > 5:
        j.destino = j.posicion + pygame.Vector2(random.uniform(-120, 120), random.uniform(-120, 120))
    j.vida = j.vida_max                       # que no muera en la prueba
    vistos["corroidos_max"] = max(vistos["corroidos_max"], len(j.efectos_extra))
    if f >= 60 * 13:
        ev.append(tecla(pygame.K_ESCAPE))
    return ev


pygame.event.get = eventos
res = mundo.iniciar_mundo({"nombre": "humo", "habilidades": [d], "energia": 500})
print("salida:", res, "| frames:", frame[0], "| resultados:", salidos, "| efectos a la vez max:", vistos["corroidos_max"])
sys.exit(0 if vistos["corroidos_max"] > 0 else 1)
