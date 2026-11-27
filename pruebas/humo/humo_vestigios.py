# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Relampago en el bucle real: tecla [2], aura dibujada, dano al lobo, tarjetas con marco electrico.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(5)
import habilidades, herramientas, mundo, inventario, fauna as F
from personaje import Personaje
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
mantenidas = set()
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: k in mantenidas})()
ms = [0]; pygame.time.get_ticks = lambda: ms[0]
raton = [(800, 450)]; pygame.mouse.get_pos = lambda: raton[0]
fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def tecla(k, tipo=pygame.KEYDOWN): return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)
st = {"f": 0, "b": {}}
_dib = inventario.dibujar_inventario
def espia(*a, **k):
    b = _dib(*a, **k); st["b"] = dict(b); return b
mundo.dibujar_inventario = espia
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]; ms[0] += 16
    j = st.get("j") or next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    fa = st.get("fa") or next(o for o in gc.get_objects() if isinstance(o, F.SistemaFauna))
    st["j"], st["fa"] = j, fa
    d = next(h for h in j.habilidades if h.nombre == "Aura Electrica")
    ev = []
    if f == 3:
        for _ in range(24): j.subir_nivel()
        j.potenciar_habilidad("Aura Electrica")
        while d.nivel < 30:
            c = d.costo_mejora; d.subir_nivel(); j.puntos_mejora -= c
        j.energia = j.energia_max
        # fuera del jardin de la casa (la fauna no puede entrar en el)
        j.posicion = pygame.Vector2(j.posicion.x, j.posicion.y + 700); j.destino = pygame.Vector2(j.posicion)
        lobo = F.LoboSolitario(j.posicion.x + 100, j.posicion.y); fa.lobos_solitarios.append(lobo); st["lobo"] = lobo
        st["v0"] = lobo.vida
    if f == 5:
        ev.append(tecla(pygame.K_2)); mantenidas.add(pygame.K_2)
    if f == 6:
        mantenidas.discard(pygame.K_2); ev.append(tecla(pygame.K_2, pygame.KEYUP))
    if f == 8:
        check(d.estado == "ACTIVA" and d.nombre_mostrado == "Vestigios Míticos", "[2] activa Vestigios Míticos (estado %s)" % d.estado)
    if f == 70:
        st["cap"] = "vestigios_juego.png"
        check(st["lobo"].vida < st["v0"], "el aura daña al lobo de al lado (%g -> %g)" % (st["v0"], st["lobo"].vida))
    if f == 72:
        ev.append(tecla(pygame.K_i))
    if f == 75:
        st["cap"] = "vestigios_inventario.png"
    if f == 77:
        ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=st["b"]["__inv__tab__equipo"].center))
    if f == 80:
        st["cap"] = "vestigios_equipo.png"
    if f >= 82:
        return [pygame.event.Event(pygame.QUIT)]
    return ev
pygame.event.get = falso
_flip = pygame.display.flip
def flip():
    n = st.pop("cap", None)
    if n: pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, n))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad(n) for n in ("Aura Electrica", "Cortar", "Onda Sonora")]
for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 1, "vida": 300,
          "fuerza": 2, "energia": 100, "escudo": 0, "escudo_magico": 0,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
