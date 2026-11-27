"""Prueba de humo del bucle real (sin ventana): sale de la casa, abre la tienda de un vendedor
con [E], compra con clic, lo golpea (Paso 0) y luego pone a otro vendedor junto a una manada."""
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
import fauna as F
import vendedores as V

capt = {}
_Pers = mundo.Personaje


class P(_Pers):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        capt["j"] = self


mundo.Personaje = P
_SV = V.SistemaVendedores.__init__


def _sv(self, *a, **k):
    _SV(self, *a, **k)
    capt["v"] = self


V.SistemaVendedores.__init__ = _sv
_SF = F.SistemaFauna.__init__


def _sf(self, *a, **k):
    _SF(self, *a, **k)
    capt["fauna"] = self


F.SistemaFauna.__init__ = _sf
_dt = V.dibujar_tienda


def _tienda(*a, **k):
    b = _dt(*a, **k)
    capt["botones"] = b
    return b


mundo.dibujar_tienda = _tienda
raton = [(0, 0)]
pygame.mouse.get_pos = lambda: raton[0]
frame = [0]
log = {}
_get = pygame.event.get


def tecla(k, tipo=pygame.KEYDOWN):
    return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)


def eventos():
    _get()
    f = frame[0]
    frame[0] += 1
    j, sv = capt.get("j"), capt.get("v")
    ev = []
    if j is None or sv is None:
        return ev
    if f == 2:
        log["dentro_inicio"] = mundo.Casa  # noqa (solo para comprobar que existe)
        j.destino = j.posicion + pygame.Vector2(0, 400)          # salir por la puerta
    if f == 150:
        log["salio"] = j.posicion.y - 10000
        j.monedas = 3000
        v = sv.vendedores[0]
        j.destino = pygame.Vector2(j.posicion)                    # quieto
        v.posicion.update(j.posicion + pygame.Vector2(50, 0))
        v.destino = None
        v.t_pausa = 999
        ev.append(tecla(pygame.K_e))
    if f == 152:
        log["tienda"] = "__tienda__0" in capt.get("botones", {})
        if log["tienda"]:
            r = capt["botones"]["__tienda__0"]
            raton[0] = r.center
            ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=r.center))
    if f == 154:
        log["comprado"] = sv.vendedores[0].stock[0]["vendido"]
        log["monedas"] = j.monedas
        ev.append(tecla(pygame.K_e))                              # cerrar
        raton[0] = (0, 0)
    if f == 156:
        j.herramienta.activa = True
        sv.vendedores[0].posicion.update(j.posicion + pygame.Vector2(0, -38))   # delante (norte), lejos del maniqui
        j.angulo = 0.0
        j.objetivo_apuntado = sv.vendedores[0]
        ev.append(tecla(pygame.K_SPACE))
        ev.append(tecla(pygame.K_SPACE, pygame.KEYUP))
    if f == 175:
        log["paso0"] = sv.vendedores[0].invisible
    if f == 180:
        lobos = [l for m in capt["fauna"].manadas for l in m.lobos if l.vivo]
        cerca = min(lobos, key=lambda l: (l.posicion - j.posicion).length())
        v2 = sv.vendedores[1]
        v2.posicion.update(cerca.posicion + pygame.Vector2(60, 0))
        j.posicion.update(cerca.posicion + pygame.Vector2(500, 0))  # la camara cerca para que la fauna actue
        j.destino = pygame.Vector2(j.posicion)
        j.invulnerable_prueba = True
    if f > 180:
        j.vida = j.vida_max
        lobos = [l for m in capt["fauna"].manadas for l in m.lobos if l.vivo]
        v2 = sv.vendedores[1]
        if f % 100 == 0:
            d = min((l.posicion - v2.posicion).length() for l in lobos)
            print("  f", f, "lobo mas cerca de v2:", round(d), "v2:", v2.estado, v2.vida, "alertadas:",
                  sum(m.alertada for m in capt["fauna"].manadas))
    if f == 700:
        v2 = sv.vendedores[1]
        log["v2"] = (v2.estado, v2.vida, v2.vivo)
        ev.append(tecla(pygame.K_ESCAPE))
    return ev


pygame.event.get = eventos
res = mundo.iniciar_mundo({"nombre": "humo", "habilidades": [], "energia": 100})
print("salida:", res, "| frames:", frame[0])
for k, v in log.items():
    print(" ", k, v)
ok = log.get("salio", 0) > 160 and log.get("tienda") and log.get("comprado") and log.get("paso0")
sys.exit(0 if ok else 1)
