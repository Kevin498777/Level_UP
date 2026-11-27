"""Prueba de equivalencia del bucle del juego (Fase 1 del plan de NPC).

Juega con guion fijo (reloj simulado a 60 fps, azar sembrado, terreno fijo) 10 partidas cortas que
cubren las 6 armas y las 15 habilidades (y sus potenciadas): pelea contra el maniqui y luego junto
a una manada de lobos. En cada fotograma resume el estado del jugador, del maniqui y de los
animales cercanos en una "huella" y al final la compara con la guardada antes de cambiar el
bucle (`equivalencia_base.json`): si el bucle hace exactamente lo mismo, la huella es identica.

Uso: python -B pruebas/humo/humo_equivalencia.py            compara con la huella guardada
     python -B pruebas/humo/humo_equivalencia.py --guardar  guarda la huella actual (solo si el
                                                            cambio de comportamiento es a proposito)
"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_GUARDAR = "--guardar" in _sys.argv
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import hashlib
import json
import os
import random
import sys
import pygame
import mundo
import habilidades
import herramientas

ARCHIVO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "equivalencia_base.json")
ANCHO, ALTO = 1600, 900
FOTOGRAMAS = 480                    # 240 contra el maniqui y 240 junto a una manada
PARTIDAS = (
    ("Espada Ligera", ("Destello", "Burst de Fuerza", "Disparo Veloz"), False),
    ("Espada Larga", ("Cortar", "Onda Sonora", "Invocar Conejos"), False),
    ("Mandoble", ("Invocar Lobos", "Carga de Fuego", "Aura Electrica"), False),
    ("Dagas Simples", ("Reforzamiento Mágico", "Regeneración Inversa", "Golpe de Suerte"), False),
    ("Escudo", ("Sombra Araña", "Paso 0", "Disparo Venenoso"), False),
    ("Arco", ("Disparo Veloz", "Carga de Fuego", "Invocar Lobos"), False),
    ("Espada Larga", ("Carga de Fuego", "Onda Sonora", "Cortar"), True),
    ("Mandoble", ("Destello", "Disparo Venenoso", "Paso 0"), True),
    ("Dagas Simples", ("Burst de Fuerza", "Aura Electrica", "Golpe de Suerte"), True),
    ("Escudo", ("Reforzamiento Mágico", "Regeneración Inversa", "Disparo Veloz"), True),
)
TECLAS = (pygame.K_2, pygame.K_3, pygame.K_4)


def r(v):
    return round(float(v), 3)


def jugar(arma, nombres, potenciadas, semilla):
    random.seed(semilla)
    st = {"f": 0, "huella": hashlib.sha256(), "j": None}
    mantenidas = set()

    def tecla(k, abajo=True):
        (mantenidas.add if abajo else mantenidas.discard)(k)
        return pygame.event.Event(pygame.KEYDOWN if abajo else pygame.KEYUP, key=k, mod=0, unicode="", scancode=0)

    def a_pantalla(L, punto):
        cam = L["camara"]
        return (round(L["mundo_x"] + punto.x - (cam.x - L["mundo_w"] / 2)),
                round(L["mundo_y"] + punto.y - (cam.y - L["mundo_h"] / 2)))

    real_get = pygame.event.get

    def get(*a, **k):
        real_get()
        L = sys._getframe(1).f_locals
        j, man, fauna = L["jugador"], L["maniqui"], L["fauna"]
        f = st["f"]; st["f"] += 1
        if f > 0:
            # Huella del fotograma anterior (despues de toda su logica)
            h = st["huella"]
            h.update(repr((r(j.posicion.x), r(j.posicion.y), r(j.vida), r(j.energia), r(j.escudo),
                           r(j.escudo_magico), len(j.proyectiles), j.nivel, r(j.xp),
                           tuple(h_.estado for h_ in j.habilidades))).encode())
            h.update(repr((man.vivo, r(man.vida), r(man.escudo), r(man.escudo_magico),
                           r(man.posicion.x), r(man.posicion.y))).encode())
            vista = pygame.Rect(round(j.posicion.x) - 900, round(j.posicion.y) - 600, 1800, 1200)
            for a in fauna.animales_con_vida(vista):
                h.update(repr((type(a).__name__, r(a.posicion.x), r(a.posicion.y), r(a.vida))).encode())
            for hab in j.fuentes_criaturas():
                for cr in getattr(hab, "criaturas", ()):
                    h.update(repr((r(cr.posicion.x), r(cr.posicion.y), cr.vivo)).encode())
        if f >= FOTOGRAMAS:
            return [pygame.event.Event(pygame.QUIT)]
        j.energia = j.energia_max                      # energia de sobra: las habilidades no paran
        ev = []
        if f == 1:
            if potenciadas:
                for _ in range(29):
                    j.subir_nivel()
                for hab in j.habilidades:
                    while hab.nivel < hab.nivel_max and hab.subir_nivel():
                        pass
                    if j.potenciar_habilidad(hab.nombre):
                        while hab.nivel < hab.nivel_max and hab.subir_nivel():
                            pass
            # frente al maniqui (al norte, mirando hacia el)
            j.posicion = pygame.Vector2(man.posicion.x, man.posicion.y - 70); j.destino = pygame.Vector2(j.posicion)
            j.angulo = 180.0
        if f == 3:
            ev += [tecla(pygame.K_1), tecla(pygame.K_1, False)]
        if f == FOTOGRAMAS // 2:
            # junto a la primera manada con lobos vivos
            manada = next(m for m in fauna.manadas if any(l.vivo for l in m.lobos))
            lobo = next(l for l in manada.lobos if l.vivo)
            j.posicion = lobo.posicion + pygame.Vector2(120, 0); j.destino = pygame.Vector2(j.posicion)
            L["camara"].update(j.posicion)
        fase = f % 120
        if fase == 10:
            ev.append(tecla(pygame.K_SPACE))
        if fase == 70:
            ev.append(tecla(pygame.K_SPACE, False))
        for i, k in enumerate(TECLAS[:len(j.habilidades)]):
            if fase == 15 + 30 * i:
                ev.append(tecla(k))
            if fase == 15 + 30 * i + 20:
                ev.append(tecla(k, False))
        # Clic derecho: con la tecla de la habilidad 2 mantenida (orden) o sin nada (autoapuntado)
        objetivos = L["enemigos_sin_tumba"]
        if objetivos and fase in (25, 100):
            obj = min(objetivos, key=lambda e: (e.posicion - j.posicion).length())
            ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=a_pantalla(L, obj.posicion)))
        if fase == 110:
            ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                         pos=a_pantalla(L, j.posicion + pygame.Vector2(60, 40))))
        return ev

    pygame.event.get = get
    pygame.key.get_pressed = lambda: type("Teclas", (), {"__getitem__": lambda s, k: k in mantenidas})()
    pygame.mouse.get_pos = lambda: (ANCHO // 2 + 40, ALTO // 2 - 50)
    pygame.display.Info = lambda: type("Info", (), {"current_w": ANCHO, "current_h": ALTO})()
    pygame.time.Clock = lambda: type("Reloj", (), {"tick": lambda s, fps=0: 16})()
    pygame.time.get_ticks = lambda: st["f"] * 16
    habs = [habilidades.crear_habilidad(n) for n in nombres]
    for i, h in enumerate(habs):
        h.asignar_tecla(TECLAS[i], "234"[i])
    config = {"nombre": "Equivalencia", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 5000,
              "fuerza": 4, "energia": 300, "escudo": 10, "escudo_magico": 10,
              "habilidades": habs, "herramienta": herramientas.crear_herramienta(arma)}
    try:
        mundo.iniciar_mundo(config)
    finally:
        pygame.event.get = real_get
    return st["huella"].hexdigest()


set_mode = pygame.display.set_mode
pygame.display.set_mode = lambda tamano, flags=0: set_mode(tamano)
huellas = {}
for i, (arma, nombres, potenciadas) in enumerate(PARTIDAS):
    clave = "%d %s + %s%s" % (i + 1, arma, ", ".join(nombres), " (potenciadas)" if potenciadas else "")
    huellas[clave] = jugar(arma, nombres, potenciadas, 100 + i)

if _GUARDAR:
    with open(ARCHIVO, "w", encoding="utf-8") as fh:
        json.dump(huellas, fh, indent=2, ensure_ascii=False)
    print("Huella guardada en", ARCHIVO)
    sys.exit(0)

with open(ARCHIVO, encoding="utf-8") as fh:
    base = json.load(fh)
fallos = 0
for clave, huella in huellas.items():
    igual = base.get(clave) == huella
    fallos += not igual
    print(("OK    " if igual else "FALLO ") + clave + ("" if igual else "  (el bucle ya no hace lo mismo)"))
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % fallos)
sys.exit(1 if fallos else 0)
