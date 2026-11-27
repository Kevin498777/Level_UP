# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Estrella Ignea en el bucle real: cargar con [2], soltar, impacto, explosion, suelo en llamas y agua evaporada.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(8)
import habilidades, herramientas, mundo, fauna as F
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
pygame.mouse.get_pos = lambda: (800, 450)
fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def tecla(k, tipo=pygame.KEYDOWN): return pygame.event.Event(tipo, key=k, mod=0, unicode="", scancode=0)
st = {"f": 0}
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]; ms[0] += 16
    j = st.get("j") or next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    fa = st.get("fa") or next(o for o in gc.get_objects() if isinstance(o, F.SistemaFauna))
    st["j"], st["fa"] = j, fa
    h = j.habilidades[0]
    ev = []
    if f == 3:
        for _ in range(29): j.subir_nivel()
        j.potenciar_habilidad("Carga de Fuego")
        while h.nivel < 30:
            c = h.costo_mejora; h.subir_nivel(); j.puntos_mejora -= c
        j.energia = j.energia_max = 300
        j.posicion = pygame.Vector2(j.posicion.x, j.posicion.y + 700); j.destino = pygame.Vector2(j.posicion)
        j.angulo = 90.0
        st["lobos"] = []
        for dx, dy in ((260, 0), (300, 40), (300, -40), (330, 0)):
            l = F.LoboSolitario(j.posicion.x + dx, j.posicion.y + dy); l.vida = l.vida_max = 300
            l.actualizar = lambda *a, **k: None
            fa.lobos_solitarios.append(l); st["lobos"].append(l)
    if f == 5:
        mantenidas.add(pygame.K_2); ev.append(tecla(pygame.K_2))
    if f == 200:
        st["cap"] = "estrella_cargando.png"
        check(h.cargando and h._tier(h.tiempo_carga) >= 2, "cargando con [2] (%.1f s)" % h.tiempo_carga)
    if f == 6 + 330:                      # ~5.3 s de carga
        st["vidas"] = [l.vida for l in st["lobos"]]
        mantenidas.discard(pygame.K_2); ev.append(tecla(pygame.K_2, pygame.KEYUP))
    if f == 6 + 332:
        p = j.proyectiles[-1]
        check(p.al_impactar is not None and p.dano == 98, "suelta una Estrella Ígnea de 98 (5 s)")
    if f == 6 + 336 + 25:
        st["cap"] = "estrella_explosion.png"
    if f == 6 + 336 + 60:
        st["cap"] = "estrella_suelo.png"
        perdidas = [round(v - l.vida, 1) for v, l in zip(st["vidas"], st["lobos"])]
        st["perdidas"] = perdidas
        check(max(perdidas) >= 98 + 29.4 - 1 and sum(p >= 29 for p in perdidas) >= 2,
              "impacto + explosión en área: vida perdida por lobo %s" % perdidas)
        check(len(h.zonas_fuego) == 1, "queda el suelo en llamas")
    if f == 6 + 336 + 70:
        # agua: explosion programada en el borde del lago mas cercano
        lago = min(fa.charcos, key=lambda c: (c.centro - j.posicion).length())
        punto = max(lago.circulos, key=lambda cr: cr[1])[0]
        st["lago"], st["punto"] = lago, pygame.Vector2(punto)
        j.posicion = pygame.Vector2(punto) + pygame.Vector2(-250, 0); j.destino = pygame.Vector2(j.posicion)
        h.programar_explosion(pygame.Vector2(punto), 0)
    if f == 6 + 336 + 110:
        st["cap"] = "estrella_agua.png"
        print("      charcos", len(st["charcos"]), "evaporados", st["lago"].evaporados, "explosiones", h.explosiones, "zonas", len(h.zonas_fuego), "en lista", st["lago"] in st["charcos"])
        check(not st["lago"].contiene(st["punto"]), "el agua del círculo se evaporó")
    if f >= 6 + 336 + 115:
        return [pygame.event.Event(pygame.QUIT)]
    return ev
pygame.event.get = falso
_Charco = mundo.Charco
st["charcos"] = []
class CharcoEspia(_Charco):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); st["charcos"].append(self)
mundo.Charco = CharcoEspia
_flip = pygame.display.flip
def flip():
    n = st.pop("cap", None)
    if n: pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, n))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad(n) for n in ("Carga de Fuego", "Cortar", "Onda Sonora")]
for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 1, "vida": 300,
          "fuerza": 2, "energia": 300, "escudo": 0, "escudo_magico": 0,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
