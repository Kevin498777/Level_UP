"""Prueba de humo del bucle real (sin ventana) con Espectro nv15: atraviesa una roca, termina
dentro de ella y comprueba que sale a un hueco libre; ataca y recibe eventos sin errores."""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
sys.path.insert(0, os.getcwd())
import pygame
import mundo
from habilidades import Paso0

capt = {}
_gen = mundo.generar_rocas
mundo.generar_rocas = lambda *a, **k: capt.setdefault("rocas", _gen(*a, **k))
_Pers = mundo.Personaje


class P(_Pers):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        capt["j"] = self


mundo.Personaje = P

paso = Paso0()
while paso.nivel < 10:
    paso.subir_nivel()
paso.desbloquear_potenciada()
while paso.subir_nivel():
    pass

frame = [0]
estado = {"fase": "ir", "dentro": False, "fuera_ok": None}
_get = pygame.event.get


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


def eventos():
    _get()
    f = frame[0]
    frame[0] += 1
    j = capt.get("j")
    ev = []
    if f == 2:
        ev.append(tecla(pygame.K_1))
    if f == 3:
        j.energia = 500
        ev.append(tecla(paso.tecla))
    if f == 5:
        # roca normal (no cueva) mas cercana: caminar hacia su centro
        rocas = [r for r in capt["rocas"] if not getattr(r, "es_cueva", False)]
        roca = min(rocas, key=lambda r: (pygame.Vector2(r.rect.center) - j.posicion).length())
        estado["roca"] = roca
        j.posicion = pygame.Vector2(roca.rect.centerx - roca.rect.width, roca.rect.centery)
        j.destino = pygame.Vector2(roca.rect.center)
        j.velocidad_base = getattr(j, "velocidad_base", j.velocidad)
    if f % 7 == 0 and f > 3:
        ev.append(tecla(pygame.K_SPACE))
        ev.append(pygame.event.Event(pygame.KEYUP, key=pygame.K_SPACE, mod=0, unicode="", scancode=0))
    if f > 5 and estado["fase"] == "ir":
        roca = estado["roca"]
        if mundo.rect_circulo_colisionan(roca.rect, j.posicion, 1) and (j.posicion - pygame.Vector2(roca.rect.center)).length() < 3:
            estado["dentro"] = paso.estado == "ACTIVA"
            paso.tiempo_restante_activo = 0.01          # termina dentro de la roca
            estado["fase"] = "fin"
            estado["f_fin"] = f
        elif f > 900:
            estado["fase"] = "fin"
            estado["f_fin"] = f
    if estado["fase"] == "fin" and f == estado["f_fin"] + 3:
        estado["fuera_ok"] = not any(mundo.rect_circulo_colisionan(r.rect, j.posicion, j.radio - 0.5)
                                     for r in capt["rocas"])
        estado["pos"] = (round(j.posicion.x), round(j.posicion.y))
    if estado["fase"] == "fin" and f == estado["f_fin"] + 60:
        ev.append(tecla(pygame.K_ESCAPE))
    return ev


pygame.event.get = eventos
res = mundo.iniciar_mundo({"nombre": "humo", "habilidades": [paso], "energia": 500})
print("salida:", res, "| frames:", frame[0])
print("llego al centro de la roca siendo Espectro:", estado["dentro"])
print("al terminar quedo fuera de toda roca:", estado["fuera_ok"], estado.get("pos"))
sys.exit(0 if estado["dentro"] and estado["fuera_ok"] else 1)
