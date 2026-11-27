# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Fundido de Paso 0 (jugador y zorro): logica + capturas en el bucle real.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(4)
import habilidades, herramientas, mundo, fauna
from personaje import Personaje, DURACION_DESVANECER
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

st = {"f": 0, "vis": {}, "zvis": {}}
def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)
FIN = 500   # Paso 0 nv1 dura 6 s (~375 frames de 16 ms) + el fundido de vuelta
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]
    j = next(o for o in gc.get_objects() if isinstance(o, Personaje))
    fa = next(o for o in gc.get_objects() if isinstance(o, fauna.SistemaFauna))
    ev = []
    if f == 3:
        j.herramienta.activa = True
        z = fa.zorros[0]; st["z"] = z
        z.posicion = pygame.Vector2(j.posicion) + pygame.Vector2(70, 0)
        z._paso0_cd = 999
    if f == 5:
        ev.append(tecla(pygame.K_2))              # Paso 0
        st["z"].invisible = True; st["z"]._paso0_t = 2.0
    st["vis"][f] = j.visibilidad
    st["zvis"][f] = st["z"].visibilidad if "z" in st else 1
    if f >= FIN:
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev
pygame.event.get = falso
_flip = pygame.display.flip
def flip():
    if st["f"] in (5, 8, 11, 14, 20):
        sup = pygame.display.get_surface()
        pygame.image.save(sup.subsurface(pygame.Rect(650, 330, 300, 200)), os.path.join(OUT, "fade_%02d.png" % st["f"]))
    _flip()
pygame.display.flip = flip
habs = [habilidades.crear_habilidad(n) for n in ("Paso 0", "Disparo Veloz", "Cortar")]
for i, h in enumerate(habs):
    h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Prueba", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": habs, "herramienta": herramientas.crear_herramienta("Espada Ligera")}
mundo.iniciar_mundo(config)
v = st["vis"]; zv = st["zvis"]
check(v[5] == 1.0, "visible antes de Paso 0")
check(0 < v[10] < 1 and v[8] > v[10] > v[14], "el personaje se desvanece poco a poco (%.2f -> %.2f -> %.2f)" % (v[8], v[10], v[14]))
n_frames = sum(1 for f in range(6, 60) if 0 < v[f] < 1)
check(abs(n_frames * 0.016 - DURACION_DESVANECER) < 0.05, "el fundido dura ~%.1f s (%d frames)" % (DURACION_DESVANECER, n_frames))
check(v[40] == 0, "termina como silueta")
fin = [f for f in range(60, FIN) if v[f] > 0]
check(fin and v[FIN - 1] == 1.0, "al terminar Paso 0 vuelve a verse con fundido (desde el frame %s)" % (fin[0] if fin else None))
check(0 < zv[10] < 1 and zv[40] == 0, "el zorro se desvanece poco a poco (%.2f a los 5 frames)" % zv[10])
check(zv[FIN - 1] == 1.0, "el zorro vuelve a aparecer con fundido")
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
