# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Fase 3: Gacha (logica, probabilidades, devoluciones y bucle real con la ruleta).
import os, sys, gc, random, collections
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
import habilidades, herramientas, mundo, inventario, gacha as G, talismanes as TL
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def nuevo():
    hs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
    for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
    return Personaje("T", 0, 0, 1, 3, 100, 10, 100, 10, (0, 0, 255), hs, herramientas.crear_herramienta("Espada Larga"), 10)

# ---------------- bucle real: [K], pestana Gacha, tirar, ruleta
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()
raton = [(800, 450)]
pygame.mouse.get_pos = lambda: raton[0]
reloj_ms = [0]
pygame.time.get_ticks = lambda: reloj_ms[0]
def tecla(k): return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)
def clic(pos): return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
st = {"f": 0, "b": {}}
_dib = inventario.dibujar_inventario
def espia(*a, **k):
    b = _dib(*a, **k); st["b"] = dict(b); st["estado"] = a[5] if len(a) > 5 else k.get("estado"); return b
mundo.dibujar_inventario = espia
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]; reloj_ms[0] += 16
    j = next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    ev = []
    if f == 3:
        ev += [tecla(pygame.K_k)]
    if f == 4:
        check(j.monedas == 100, "[K] da 100 monedas de prueba")
        for _ in range(19): j.subir_nivel()
        for n in j.habilidades_faltantes(): j.agregar_habilidad(n)
        j.monedas = 100
        ev.append(tecla(pygame.K_i))
    if f == 6:
        ev.append(clic(st["b"]["__inv__tab__gacha"].center))
    if f == 8:
        st["cap_idle"] = True
        check(G.POTENCIADA in G.probabilidades(j), "a nivel 20 con todas las habilidades aparece la potenciada")
    if f == 10:
        check("__inv__tirar" in st["b"], "boton TIRAR activo con 100 monedas")
        st["col0"] = (len(j.coleccion_herramientas), len(j.coleccion_habilidades), dict(j.talismanes.anillos), j.talismanes.totems)
        ev.append(clic(st["b"]["__inv__tirar"].center))
    if f == 12:
        e = st["estado"]
        check(e.get("ruleta") is not None and e.get("tiradas") == 1, "la tirada arranca la ruleta")
        check(j.monedas in (80, 90), "a nivel 20 se cobran 20 (+10 si estaba agotada): %d" % j.monedas)
        cambio = (len(j.coleccion_herramientas), len(j.coleccion_habilidades), dict(j.talismanes.anillos), j.talismanes.totems) != st["col0"]
        check(cambio or e["ruleta"]["resultado"]["categoria"] == "nada" or e["ruleta"]["resultado"]["devolucion"],
              "el premio ya esta aplicado: %s" % e["ruleta"]["resultado"]["texto"])
        check("__inv__tirar" not in st["b"], "mientras gira no se puede volver a tirar")
        st["m_antes"] = j.monedas
        ev.append(clic((800, 300)))   # clic dentro del inventario durante el giro
    if f == 40:
        st["cap_girando"] = True
    if f == 200:
        st["cap_fin"] = True
        check("__inv__tirar" in st["b"], "al parar la ruleta se puede tirar otra vez")
        ev.append(clic(st["b"]["__inv__tirar"].center))
        ev.append(tecla(pygame.K_i))      # cerrar en pleno giro
    if f == 206:
        check(j.monedas in (st["m_antes"] - 20, st["m_antes"] - 10), "segunda tirada cobrada aunque se cierre el inventario")
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev
pygame.event.get = falso
_flip = pygame.display.flip
def flip():
    for k, nombre in (("cap_idle", "gacha_v2_0.png"), ("cap_girando", "gacha_v2_1.png"), ("cap_fin", "gacha_v2_2.png")):
        if st.pop(k, False):
            pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, nombre))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
random.seed(11)
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))

sys.exit(1 if fallos else 0)
