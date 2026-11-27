# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Fase 1 en el bucle real: [T], pestaña Talismanes, equipar/quitar con clics, totem al morir.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(7)
import habilidades, herramientas, mundo, fauna, inventario, talismanes as TL
from personaje import Personaje
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()
raton = [(800, 450)]
pygame.mouse.get_pos = lambda: raton[0]

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def tecla(k): return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)
def clic(pos): return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)

st = {"f": 0, "botones": {}}
_dib = inventario.dibujar_inventario
def espia(*a, **k):
    b = _dib(*a, **k)
    st["botones"] = dict(b)
    return b
mundo.dibujar_inventario = espia

orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]
    j = next(o for o in gc.get_objects() if isinstance(o, Personaje))
    ev = []
    if f == 3:
        for _ in range(40):
            ev.append(tecla(pygame.K_t))          # muchos talismanes de prueba
    if f == 5:
        st["n_anillos"] = len(j.talismanes.anillos); st["totems"] = j.talismanes.totems
        check(st["n_anillos"] >= 3, "[T] da anillos (%d distintos, %d totems)" % (st["n_anillos"], st["totems"]))
        if j.talismanes.totems == 0:
            j.talismanes.agregar_totem()
        ev.append(tecla(pygame.K_i))
    if f == 7:
        ev.append(clic(st["botones"]["__inv__tab__talismanes"].center))
    if f == 9:
        b = st["botones"]
        check(any(k.startswith("__inv__equipar__") for k in b), "la pestana Talismanes muestra botones Equipar")
        st["vmax0"] = j.vida_max
        ev.append(clic(b["__inv__equipar__" + TL.TOTEM].center))
    if f == 11:
        check(TL.TOTEM in j.talismanes.huecos, "clic en Equipar del totem lo equipa")
        b = st["botones"]
        if "__inv__equipar__vida" not in b:
            j.talismanes.agregar_anillo("vida")
    if f == 13:
        ev.append(clic(st["botones"]["__inv__equipar__vida"].center))
    if f == 15:
        check(j.vida_max == st["vmax0"] + 4 * j.talismanes.anillos["vida"], "equipar el anillo de vida sube la vida maxima")
        raton[0] = st["botones"]["__inv__quitar__1"].center if "__inv__quitar__1" in st["botones"] else raton[0]
    if f == 17:
        st["captura"] = True
    if f == 19:
        ev.append(clic(st["botones"]["__inv__quitar__1"].center))
    if f == 21:
        check(j.vida_max == st["vmax0"], "Quitar resta la vida maxima")
        st["antes"] = (j.nivel, j.monedas, dict(j.talismanes.anillos), j.talismanes.totems)
        j.ganar_xp(30); j.monedas = 77
        st["antes"] = (j.nivel, j.monedas, dict(j.talismanes.anillos), j.talismanes.totems)
        j.posicion = j.posicion + pygame.Vector2(900, 0)
        j.vida = 0
    if f == 23:
        n, m, an, t = st["antes"]
        check(j.vida == j.vida_max and j.nivel == n and j.monedas == m and j.talismanes.anillos == an,
              "el totem te salva: vida llena, mismo nivel, monedas y anillos")
        check(j.talismanes.totems == t - 1, "se gasta 1 totem (%d -> %d)" % (t, j.talismanes.totems))
        check((j.posicion - mundo.CENTRO_MUNDO).length() < 60, "vuelves al centro")
    if f == 30:
        st["cap_totem"] = True
    if f == 32:
        # sin totems equipados -> muerte normal
        while j.talismanes.usar_totem():
            pass
        j.vida = 0
    if f == 35:
        check(st.get("muerte"), "sin totem equipado: pantalla de muerte normal")
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev
pygame.event.get = falso
_dm = mundo.dibujar_pantalla_muerte
def espia_m(*a, **k):
    st["muerte"] = True
    return _dm(*a, **k)
mundo.dibujar_pantalla_muerte = espia_m
_flip = pygame.display.flip
def flip():
    if st.pop("captura", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "tal_inv.png"))
    if st.pop("cap_totem", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "tal_totem.png"))
    _flip()
pygame.display.flip = flip

habs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
for i, h in enumerate(habs):
    h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Prueba", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": habs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
