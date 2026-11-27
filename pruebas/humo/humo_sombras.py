# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Anillos de sombra en el bucle real: aparecen, te siguen, defienden de un lobo salvaje que te
# muerde, la fauna las trata como sombras, el totem las resetea, y se dibujan.
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(9)
import habilidades, herramientas, mundo, fauna as F, talismanes as TL
from personaje import Personaje
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
st = {"f": 0}
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]
    j = st.get("j") or next(o for o in gc.get_objects() if isinstance(o, Personaje))
    fa = st.get("fa") or next(o for o in gc.get_objects() if isinstance(o, F.SistemaFauna))
    st["j"], st["fa"] = j, fa
    if f == 3:
        for _ in range(10): j.talismanes.agregar_anillo("sombra_lobo")
        for _ in range(10): j.talismanes.agregar_anillo("sombra_conejo")
        j.talismanes.equipar("sombra_lobo"); j.talismanes.equipar("sombra_conejo"); j.recalcular_talismanes()
        j.posicion = j.posicion + pygame.Vector2(2500, 0); j.destino = pygame.Vector2(j.posicion)
    if f == 5:
        crs = j.sombras_anillo.criaturas
        check(len(crs) == 2, "aparecen el lobo y el conejo sombra")
        st["sombras"] = list(crs)
    if f == 40:
        check(all((c.posicion - j.posicion).length() < 250 for c in st["sombras"]), "te siguen")
        # un lobo salvaje te muerde
        man = fa.manadas[0]
        lobo = man.lobos[1]; st["salvaje"] = lobo
        for l in man.lobos:
            if l is not lobo: l.vivo = False
        lobo.posicion = j.posicion + pygame.Vector2(25, 0); lobo._cd_mordida = 0
        lobo._morder(j)
        check(j.ultimo_agresor is lobo, "la mordida marca al lobo salvaje como agresor")
        st["vida_lobo"] = lobo.vida
        j.vida = j.vida_max = 500
    if f == 140:
        lobo = st["salvaje"]
        check(lobo.vida < st["vida_lobo"] or not lobo.vivo, "las sombras atacan al lobo que te mordio (%.0f -> %.0f)" % (st["vida_lobo"], lobo.vida))
        st["cap"] = True
    if f == 150:
        j.talismanes.agregar_totem(); j.talismanes.equipar(TL.TOTEM) if None in j.talismanes.huecos else None
        if TL.TOTEM not in j.talismanes.huecos:
            j.talismanes.quitar(0); j.talismanes.equipar(TL.TOTEM); j.recalcular_talismanes()
        j.vida = 0
    if f == 152:
        check(TL.TOTEM in j.talismanes.huecos or j.talismanes.totems == 0, "el totem salva")
        st["tras_totem"] = len(j.sombras_anillo.criaturas)
    if f == 160:
        check(st["tras_totem"] <= 1, "tras el totem las sombras desaparecen y vuelven con su tiempo")
    if f >= 520:
        check(len(j.sombras_anillo.criaturas) >= 1, "y reaparecen")
        return [pygame.event.Event(pygame.QUIT)]
    return []
pygame.event.get = falso
_flip = pygame.display.flip
def flip():
    if st.pop("cap", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "sombras.png"))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Cortar")]
for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3][i], "23"[i])
config = {"nombre": "Prueba", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
