"""Prueba de humo de la Fase 1 del plan de NPC: un segundo personaje en el bucle real del juego.

Un combatiente (config["combatientes"]) con Mandoble y Disparo Veloz, movido por guion con sus
intenciones, persigue y golpea al jugador; el jugador le devuelve los golpes hasta matarlo. Se
comprueba que el jugador recibe dano, que el combatiente se dibuja sin errores, que la fauna y
el bucle lo tratan como a un cuerpo mas y que al morir sale del mundo.
Uso: python -B pruebas/humo/humo_combatiente.py"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import random
import sys
import pygame
import mundo
import habilidades
import herramientas
from personaje import Personaje

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


random.seed(11)
st = {"f": 0, "vida_j0": None, "visto_vivo": 0, "dibujado": 0}
mantenidas = set()
npc = Personaje("Bandido", 0, 0, 1, 3, 60, 3, 200, 0, (200, 60, 60),
                [habilidades.crear_habilidad("Disparo Veloz")], herramientas.crear_herramienta("Mandoble"))
npc.habilidades[0].asignar_tecla(pygame.K_2, "2")
_dib = Personaje.dibujar


def dibujar_espia(self, *a, **k):
    if self is npc:
        st["dibujado"] += 1
    return _dib(self, *a, **k)


Personaje.dibujar = dibujar_espia
real_get = pygame.event.get


def get(*a, **k):
    real_get()
    L = sys._getframe(1).f_locals
    j, ctx = L["jugador"], L["ctx"]
    f = st["f"]; st["f"] += 1
    if f == 2:
        # los dos fuera del jardin de la casa (la fauna no entra en el), el bandido al este
        j.posicion = mundo.CENTRO_MUNDO + pygame.Vector2(0, 900); j.destino = pygame.Vector2(j.posicion)
        npc.posicion = j.posicion + pygame.Vector2(160, 0); npc.destino = pygame.Vector2(npc.posicion)
        L["camara"].update(j.posicion)
        # escena despejada: sin rocas, arboles, arbustos ni agua alrededor
        c = j.posicion
        cerca = lambda p: (pygame.Vector2(p) - c).length() < 450
        L["rocas"][:] = [r for r in L["rocas"] if not cerca(r.rect.center)]
        veg = L["vegetacion"]
        veg.arbustos[:] = [x for x in veg.arbustos if not cerca(x.centro)]
        veg.arboles[:] = [x for x in veg.arboles if not cerca(x.rect.center)]
        L["charcos"][:] = [x for x in L["charcos"] if (pygame.Vector2(x.centro) - c).length() > 450 + x.radio]
        st["vida_j0"] = j.vida
        npc.alternar_arma()
    if 2 < f < 460 and npc in ctx.combatientes:
        # "Inteligencia" de guion: mira al jugador, se acerca, golpea y dispara
        hacia = j.posicion - npc.posicion
        npc.angulo = (pygame.Vector2(0, -1).angle_to(hacia)) % 360.0
        npc.mover_a(j.posicion - hacia.normalize() * 40 if hacia.length() > 50 else npc.posicion)
        npc.mantiene_ataque = hacia.length() < 70
        if f % 90 == 10:
            npc.pulsar_habilidad(npc.habilidades[0])
        npc.energia = npc.energia_max
        st["visto_vivo"] += 1
    if f == 150:
        st["vida_j_mitad"] = j.vida
        # el jugador se defiende: saca el arma, mira al bandido y golpea sin parar
        j.alternar_arma()
        mantenidas.add(pygame.K_SPACE)
    if 150 <= f:
        if npc in ctx.combatientes:
            hacia = npc.posicion - j.posicion
            j.angulo = (pygame.Vector2(0, -1).angle_to(hacia)) % 360.0
        j.vida = max(j.vida, 50)                    # que el jugador no muera en la prueba
    if f == 460:
        st["sigue"] = npc in ctx.combatientes
    if f >= 480:
        return [pygame.event.Event(pygame.QUIT)]
    return []


pygame.event.get = get
pygame.key.get_pressed = lambda: type("Teclas", (), {"__getitem__": lambda s, k: k in mantenidas})()
pygame.display.Info = lambda: type("Info", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda tamano, flags=0: _sm(tamano)
pygame.time.Clock = lambda: type("Reloj", (), {"tick": lambda s, fps=0: 16})()
config = {"nombre": "Jugador", "vida": 200, "fuerza": 6, "energia": 100, "escudo": 0, "escudo_magico": 0,
          "habilidades": [], "herramienta": herramientas.crear_herramienta("Mandoble"),
          "combatientes": [npc]}
mundo.iniciar_mundo(config)

comprobar(st.get("vida_j_mitad", 999) < st["vida_j0"], "el bandido hiere al jugador (%s -> %s)" % (st["vida_j0"], st.get("vida_j_mitad")))
comprobar(st["dibujado"] > 100, "el bandido se dibuja con el mismo dibujo del personaje (%d fotogramas)" % st["dibujado"])
comprobar(npc.vida <= 0 and not st.get("sigue", True), "el jugador mata al bandido y sale del mundo (vida %s)" % npc.vida)

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
