# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Inventario [I] en el bucle real: abrir/cerrar, X, clics dentro, [+], el mundo no se pausa, muerte.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(4)
import habilidades, herramientas, mundo, fauna, inventario
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
def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)
def clic(pos, b=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=b, pos=pos)

AREA = pygame.Rect(230, 0, 1600 - 230 - 320, 900)
CAJA = inventario.rect_inventario(AREA)
st = {"f": 0}
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]
    j = next(o for o in gc.get_objects() if isinstance(o, Personaje))
    fa = next(o for o in gc.get_objects() if isinstance(o, fauna.SistemaFauna))
    ev = []
    if f == 3:
        j.ganar_xp(10.4); j.monedas = 137
        ev.append(tecla(pygame.K_i))
    if f == 5:
        st["pos"] = pygame.Vector2(j.destino)
        st["vida"] = j.vida
        ev.append(clic((CAJA.x + 40, CAJA.bottom - 30)))          # clic en la descripcion (fondo)
    if f == 8:
        check(j.destino == st["pos"], "clic dentro del inventario no mueve al personaje")
        # [+] de vida dentro del inventario
        st["pts"] = j.puntos_mejora; st["vmax"] = j.vida_max
        st["boton_vida"] = True
    if f == 9:
        # Simular el mundo activo: un lobo muerde al jugador con el inventario abierto
        lobo = fa.manadas[0].lobos[1]
        lobo.posicion = j.posicion + pygame.Vector2(30, 0); lobo._cd_mordida = 0
        lobo._morder(j)
        st["vida_mordido"] = j.vida
    if f == 12:
        check(st["vida_mordido"] < st["vida"], "con el inventario abierto el mundo sigue: un lobo te hace dano (%.1f -> %.1f)" % (st["vida"], st["vida_mordido"]))
    if f == 20:
        raton[0] = (CAJA.x + 120, CAJA.y + 300)                   # hover sobre estadisticas
    if f == 24:
        raton[0] = (CAJA.right - 200, CAJA.y + 330)               # hover sobre una habilidad
    if f == 28:
        ev.append(clic(st["rect_x"].center))                      # la X cierra
    if f == 30:
        check(not st["abierto_29"], "la X cierra el inventario")
        ev.append(tecla(pygame.K_i))
    if f == 32:
        ev.append(tecla(pygame.K_i))                              # [I] otra vez cierra
    if f == 34:
        check(not st["abierto_33"], "[I] tambien lo cierra")
        ev.append(tecla(pygame.K_i))
    if f == 36:
        j.vida = 0
    if f == 40:
        check(not st["abierto_39"] and st.get("muerte_39"), "al morir se cierra y sale la pantalla de muerte")
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev
pygame.event.get = falso

_dib = inventario.dibujar_inventario
def espia(*a, **k):
    b = _dib(*a, **k)
    st["rect_x"] = b["__cerrar_inv__"]
    st.setdefault("dibujado", set()).add(st["f"])
    if st["f"] == 8 and "vida" in b:
        # pulsar el [+] de vida del inventario en el siguiente frame
        st["clic_vida"] = b["vida"].center
    return b
inventario.dibujar_inventario = espia
mundo.dibujar_inventario = espia
_dm = mundo.dibujar_pantalla_muerte
def espia_muerte(*a, **k):
    st["muerte_%d" % st["f"]] = True
    return _dm(*a, **k)
mundo.dibujar_pantalla_muerte = espia_muerte

_flip = pygame.display.flip
def flip():
    f = st["f"]
    st["abierto_%d" % f] = f in st.get("dibujado", set())
    if f in (6, 21, 25):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "inv_%02d.png" % f))
    _flip()
pygame.display.flip = flip

# el clic en [+] vida se inyecta tras el frame 8
_falso = pygame.event.get
def falso2(*a, **k):
    ev = _falso()
    if st["f"] == 10 and "clic_vida" in st:
        ev.append(clic(st["clic_vida"]))
    if st["f"] == 12:
        j = next(o for o in gc.get_objects() if isinstance(o, Personaje))
        check(j.vida_max == st["vmax"] + 2 and j.puntos_mejora == st["pts"] - 1, "el [+] de Vida del inventario gasta 1 punto y sube +2")
    return ev
pygame.event.get = falso2

habs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
for i, h in enumerate(habs):
    h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Prueba", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": habs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
check(all(st.get("abierto_%d" % f) for f in range(4, 27)), "el inventario queda abierto mientras no se cierre")
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
