"""Prueba de humo de ShadowGOD (personaje de inspeccion del mapa, Fase 2 del plan de NPC).

En el bucle real y sin ventana: se teletransporta al clic, lo atraviesa todo (rocas, lagos), no
recibe dano ni lo detectan, acerca y aleja la vista con la rueda, las teclas + / - y los botones,
y muestra las capas con [V]. Ademas: el zoom es solo vista (el mundo evoluciona igual con y sin
zoom) y se mide lo que cuesta dibujar cada nivel de zoom.
Uso: python -B pruebas/humo/humo_inspector.py"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import hashlib
import os
import random
import sys
import time
import pygame
import mundo
import herramientas

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


pygame.display.Info = lambda: type("Info", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda tamano, flags=0: _sm(tamano)
pygame.time.Clock = lambda: type("Reloj", (), {"tick": lambda s, fps=0: 16})()
pygame.key.get_pressed = lambda: type("Teclas", (), {"__getitem__": lambda s, k: False})()
real_get = pygame.event.get


def jugar(guion, fotogramas, inspector=True):
    """Ejecuta el bucle real con 'guion(f, L)' (L = variables del bucle) y devuelve el estado."""
    random.seed(21)
    st = {"f": 0, "t": None, "tiempos": {}}

    def get(*a, **k):
        ahora = time.perf_counter()
        real_get()
        L = sys._getframe(1).f_locals
        f = st["f"]; st["f"] += 1
        if st["t"] is not None and inspector:
            z = L["zoom_actual"]()
            st["tiempos"].setdefault(z, []).append((ahora - st["t"]) * 1000)
        st["L"] = L
        ev = [pygame.event.Event(pygame.QUIT)] if f >= fotogramas else guion(f, L)
        st["t"] = time.perf_counter()
        return ev

    pygame.event.get = get
    config = {"nombre": "ShadowGOD", "inspector": inspector, "vida": 30, "habilidades": [],
              "herramienta": herramientas.crear_herramienta("Espada Ligera")}
    try:
        mundo.iniciar_mundo(config)
    finally:
        pygame.event.get = real_get
    return st


res = {}


def guion(f, L):
    j = L["jugador"]
    ev = []
    if f == 2:
        # 1) teletransporte con clic izquierdo
        res["destino"] = L["raton_a_mundo"](L["mundo_x"] + 150, 120)
        ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(L["mundo_x"] + 150, 120)))
    if f == 3:
        res["tele"] = (j.posicion - res["destino"]).length()
        # 2) dentro de una roca: no lo saca (lo atraviesa todo)
        roca = next(r for r in L["rocas"] if r.rect.width > 60 and not getattr(r, "es_cueva", False))
        res["roca"] = pygame.Vector2(roca.rect.center)
        j.mover_a(res["roca"], mundo.LIMITE)
    if f == 30:
        res["en_roca"] = (j.posicion - res["roca"]).length()
        # 3) en la zona profunda de un lago: no pierde vida
        lago = next(c for c in L["charcos"] if c.es_lago_profundo)
        j.mover_a(lago.centro, mundo.LIMITE)
        res["vida0"] = j.vida
    if f == 150:
        res["profundo"] = j.en_agua_profunda
        res["vida_lago"] = j.vida
        res["dano"] = j.recibir_dano(50, "fisico")
        res["detectable"] = j.detectable
        # 4) zoom: la rueda aleja hasta ver el mapa entero
        ev += [pygame.event.Event(pygame.MOUSEWHEEL, x=0, y=-1, flipped=False) for _ in range(10)]
    if f == 152:
        res["zoom_min"] = L["zoom_actual"]()
        ev.append(tecla(pygame.K_PLUS))
    if f == 154:
        res["zoom_mas"] = L["zoom_actual"]()
        ev.append(tecla(pygame.K_MINUS))
    if f == 156:
        res["zoom_menos"] = L["zoom_actual"]()
        boton = L["botones_stats"]["__zoom_mas__"]
        ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=boton.center))
    if f == 158:
        res["zoom_boton"] = L["zoom_actual"]()
        ev.append(tecla(pygame.K_v))
    if f == 160:
        res["capas"] = L["mostrar_capas"]
        # teletransporte con la vista alejada: el clic cae en el punto del mapa bajo el raton
        res["destino_lejos"] = L["raton_a_mundo"](L["mundo_x"] + 600, 300)
        ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(L["mundo_x"] + 600, 300)))
    if f == 161:
        res["tele_lejos"] = (j.posicion - res["destino_lejos"]).length()
    # 5) recorrer todos los niveles de zoom (cada 40 fotogramas) para medir el dibujo
    if 200 <= f < 200 + 40 * len(mundo.NIVELES_ZOOM) and (f - 200) % 40 == 0:
        L["zoom_inspector"][0] = (f - 200) // 40
    return ev


st = jugar(guion, 200 + 40 * len(mundo.NIVELES_ZOOM))
print("--- ShadowGOD")
comprobar(res["tele"] < 0.5, "se teletransporta al punto del clic (a %.1f px)" % res["tele"])
comprobar(res["en_roca"] < 0.5, "puede quedarse dentro de una roca: lo atraviesa todo (%.1f px)" % res["en_roca"])
comprobar(res["profundo"] and res["vida_lago"] == res["vida0"], "en la zona profunda de un lago no pierde vida")
comprobar(res["dano"] == 0 and not res["detectable"], "no recibe dano y nadie lo detecta (invisible)")
comprobar(res["zoom_min"] == min(mundo.NIVELES_ZOOM), "la rueda del raton aleja la vista (x%.2f)" % res["zoom_min"])
comprobar(res["zoom_mas"] > res["zoom_min"] and res["zoom_menos"] == res["zoom_min"],
          "las teclas + y - acercan y alejan (x%.2f / x%.2f)" % (res["zoom_mas"], res["zoom_menos"]))
comprobar(res["zoom_boton"] > res["zoom_menos"], "el boton + de la interfaz acerca la vista")
comprobar(res["capas"], "[V] muestra las capas del mapa")
comprobar(res["tele_lejos"] < 0.5, "con la vista alejada el clic tambien lo teletransporta (a %.1f px)" % res["tele_lejos"])
print("      tiempo de cada fotograma segun el zoom (ms, mediana):")
for z, t in sorted(st["tiempos"].items(), reverse=True):
    t = sorted(t)[3:]                       # los primeros de cada nivel construyen cosas
    if t:
        print("        x%-5.2f %6.1f" % (z, t[len(t) // 2]))


# ------------------------------------------------------------ El zoom es solo vista
def huella_mundo(L):
    h = hashlib.sha256()
    for a in L["fauna"].animales_con_vida(pygame.Rect(0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO)):
        h.update(repr((type(a).__name__, round(a.posicion.x, 3), round(a.posicion.y, 3), round(a.vida, 3))).encode())
    for v in L["vendedores"].vendedores:
        h.update(repr((round(v.posicion.x, 3), round(v.posicion.y, 3), v.estado)).encode())
    return h.hexdigest()


def sin_zoom(f, L):
    return []


def con_zoom(f, L):
    if f % 30 == 0:
        L["zoom_inspector"][0] = (f // 30) % len(mundo.NIVELES_ZOOM)
    if f % 45 == 0:
        L["mostrar_capas"] = True
    return []


a = jugar(sin_zoom, 240)
b = jugar(con_zoom, 240)
comprobar(huella_mundo(a["L"]) == huella_mundo(b["L"]), "el zoom y las capas son solo vista: el mundo evoluciona igual")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
