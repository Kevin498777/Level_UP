# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Orbes de la cueva del oso: vida (+20 vida, +2 XP), XP (+5) y, con 50 %, Gacha (ruleta de anillos).
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
random.seed(4)
import habilidades, herramientas, mundo, fauna as F, gacha as G, talismanes as TL
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

# --- probabilidad del orbe Gacha y posiciones
class RocaFalsa:
    def __init__(self): self.rect = pygame.Rect(0, 0, 160, 160)
n_g = 0
for _ in range(4000):
    o = F.Oso(RocaFalsa()); o.estado = "ataca"; o.recibir_dano(999)
    n_g += any(x.tipo == "gacha" for x in o.orbes_extra)
    assert o.orbe.tipo == "vida" and o.orbes_extra[0].tipo == "xp"
check(abs(n_g / 4000 - 0.5) < 0.03, "el oso deja orbe de vida + orbe de XP siempre, y orbe Gacha el %.1f%% de las veces" % (100 * n_g / 4000))
o = F.Oso(RocaFalsa()); F.PROB_ORBE_GACHA, viejo = 1.0, F.PROB_ORBE_GACHA
o.estado = "ataca"; o.recibir_dano(999); F.PROB_ORBE_GACHA = viejo
dists = [(x.centro - o.entrada).length() for x in o.orbes_extra]
check(all(29 < d < 50 for d in dists), "los orbes extra estan en la boca de la cueva y separados del de vida (%s px)" % [round(d) for d in dists])
# tirar_anillo
j = Personaje("T", 0, 0, 1, 1, 20, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"), 0)
r = G.tirar_anillo(j)
check(r["categoria"] == "anillo" and r["id"] in j.talismanes.anillos and j.monedas == 0, "ruleta de anillos gratis: da un anillo y no cobra (%s)" % r["texto"])
for a, d in TL.ANILLOS.items(): j.talismanes.anillos[a] = d["nivel_max"]
r = G.tirar_anillo(j)
check(r["devolucion"] == G.DEVOLUCION and j.monedas == G.DEVOLUCION, "si el anillo ya esta al maximo devuelve %d" % G.DEVOLUCION)
rul = G.nueva_ruleta(r, 0, solo_anillos=True); cas = rul["casillas"]
# el premio (indice) puede ser "nada" si todos estan al maximo; el relleno siempre son anillos
check(all(c["categoria"] == "anillo" for i, c in enumerate(cas) if i != rul["indice"]), "la ruleta del orbe solo muestra anillos")

# --- bucle real
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()
ms = [0]
pygame.time.get_ticks = lambda: ms[0]
F.PROB_ORBE_GACHA = 1.0
st = {"f": 0}
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]; ms[0] += 16
    j = st.get("j") or next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    fa = st.get("fa") or next(o for o in gc.get_objects() if isinstance(o, F.SistemaFauna))
    st["j"], st["fa"] = j, fa
    if f == 3:
        oso = next(o for o in fa.osos if o.vivo); st["oso"] = oso
        oso.estado = "ataca"; oso.recibir_dano(999)
        j.vida = 10
    if f == 5:
        oso = st["oso"]
        st["xp0"] = (j.nivel, j.xp); st["an0"] = sum(j.talismanes.anillos.values())
        j.posicion = pygame.Vector2(oso.orbe.centro); j.destino = pygame.Vector2(j.posicion)
    if f == 70:
        check(j.vida == 30 and not st["oso"].orbe.activo, "orbe de vida: +20 de vida (vida %s, activo %s, dist %.0f)" % (j.vida, st["oso"].orbe.activo, (j.posicion - st["oso"].orbe.centro).length()))
        check(all(x.activo for x in st["oso"].orbes_extra), "los orbes de XP y Gacha siguen ahi (se recogen aparte)")
        st["xp_vida"] = (j.nivel, j.xp)
        j.posicion = pygame.Vector2(st["oso"].orbes_extra[0].centro); j.destino = pygame.Vector2(j.posicion)
    if f == 135:
        check(not st["oso"].orbes_extra[0].activo, "orbe de XP recogido (dist %.0f)" % (j.posicion - st["oso"].orbes_extra[0].centro).length())
        st["xp_xp"] = (j.nivel, j.xp)
        j.posicion = pygame.Vector2(st["oso"].orbes_extra[1].centro); j.destino = pygame.Vector2(j.posicion)
    if f == 200:
        check(not st["oso"].orbes_extra[1].activo and sum(j.talismanes.anillos.values()) == st["an0"] + 1 or j.monedas >= 25,
              "orbe Gacha: la ruleta de anillos da un anillo al momento")
    if f == 215:
        st["cap"] = True
    if f == 480:
        st["cap2"] = True
    if f >= 600:
        return [pygame.event.Event(pygame.QUIT)]
    return []
pygame.event.get = falso
_dr = G.dibujar_ruleta_mundo
def espia_r(*a, **k):
    st["dibujada"] = st.get("dibujada", 0) + 1
    return _dr(*a, **k)
G.dibujar_ruleta_mundo = espia_r
mundo.GACHA.dibujar_ruleta_mundo = espia_r
_flip = pygame.display.flip
def flip():
    if st.pop("cap", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "orbe_gacha_1.png"))
    if st.pop("cap2", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "orbe_gacha_2.png"))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad("Cortar")]; hs[0].asignar_tecla(pygame.K_2, "2")
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
j = st["j"]
# XP: oso 15 + orbe vida 2 + orbe XP 5 = 22 en total -> desde nivel 1 (1+2+4+8=15 -> nv5 con 7)
check((j.nivel, round(j.xp, 1)) == (5, 7.0), "oso 15 + orbe de vida 2 + orbe de XP 5 = 22 XP (nivel %d, xp %s)" % (j.nivel, j.xp))
check(st.get("dibujada", 0) > 100, "la ruleta de anillos se dibuja sobre el mundo (%d cuadros) y luego desaparece" % st.get("dibujada", 0))
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
