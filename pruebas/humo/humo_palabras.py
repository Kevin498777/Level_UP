"""Prueba de humo del bucle real (sin ventana) con Palabras Malditas nv30: junto a una manada,
alterna pulsos y las 6 palabras (manteniendo la tecla y soltando con el raton en su casilla)."""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import math
sys.path.insert(0, os.getcwd())
import pygame
import mundo
import fauna as F
from habilidades import OndaSonora

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

h = OndaSonora()
while h.nivel < 20:
    h.subir_nivel()
h.desbloquear_potenciada()
while h.subir_nivel():
    pass

raton = [(0, 0)]
pygame.mouse.get_pos = lambda: raton[0]
frame = [0]
lanzadas = []
_get = pygame.event.get
plan = ["pulso"] + [p["clave"] for p in h.PALABRAS]      # 7 lanzamientos


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
    j.energia = j.energia_max = 300
    j.vida = max(j.vida, 20)
    if f == 5:
        lobos = [l for m in capt["fauna"].manadas for l in m.lobos if l.vivo]
        cerca = min(lobos, key=lambda l: (l.posicion - j.posicion).length())
        j.posicion = cerca.posicion + pygame.Vector2(70, 0)
        j.destino = pygame.Vector2(j.posicion)
    paso = (f - 20) // 90
    fase = (f - 20) % 90
    if f >= 20 and paso < len(plan):
        accion = plan[paso]
        soltar = 3 if accion == "pulso" else 30
        if fase == soltar + 1:
            lanzadas.append((accion, h.estado, round(h.tiempo_restante_cooldown, 1)))
        if fase == 0:
            h.estado = "LISTA"               # sin esperar recargas en la prueba
        if fase == 0:
            ev.append(tecla(h.tecla))
        if accion != "pulso" and h._pos_jugador is not None:
            i = [p["clave"] for p in h.PALABRAS].index(accion)
            ang = -math.pi / 2 + i * math.tau / 6
            centro = h._pos_jugador - pygame.Vector2(h._desplazamiento)
            raton[0] = (centro.x + math.cos(ang) * 95, centro.y + math.sin(ang) * 95)
        if fase == soltar:
            ev.append(tecla(h.tecla, pygame.KEYUP))
    if f >= 20 + 90 * len(plan) + 60:
        ev.append(tecla(pygame.K_ESCAPE))
    return ev


pygame.event.get = eventos
res = mundo.iniciar_mundo({"nombre": "humo", "habilidades": [h], "energia": 300})
print("salida:", res, "| frames:", frame[0])
for accion, estado, cd in lanzadas:
    print(f"  {accion:13s} -> {estado} (recarga {cd} s)")
ok = len(lanzadas) == len(plan) and all(e == "COOLDOWN" for _, e, _ in lanzadas)
sys.exit(0 if ok else 1)
