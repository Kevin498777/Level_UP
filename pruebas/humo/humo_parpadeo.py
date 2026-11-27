# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Parpadeo rojo en el bucle real: jugador, un animal y una sombra pierden vida y se comprueba
# que el tinte rojo aparece en pantalla sobre cada uno. Uso: python -B test_parpadeo_juego.py <proyecto> <carpeta_capturas>
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(2)
import habilidades, herramientas, mundo, talismanes as TL, fauna as F
from personaje import Personaje
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()
ms = [0]; pygame.time.get_ticks = lambda: ms[0]
fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
st = {"f": 0, "vistos": {}}
_dib = mundo.dibujar_parpadeos
def espia(pantalla, entidades, desp):
    _dib(pantalla, entidades, desp)
    for e in entidades:
        t = getattr(e, "_t_parpadeo", 0)
        if t > 0 and int((mundo.PARPADEO_DURACION - t) / mundo.PARPADEO_PERIODO) % 2 == 0:
            px = (round(e.posicion.x - desp[0]), round(e.posicion.y - desp[1]))
            if pantalla.get_rect().collidepoint(px):
                c = pantalla.get_at(px)
                clase = type(e).__name__
                st["vistos"].setdefault(clase, []).append(c[0] - max(c[1], c[2]))
    if st.pop("cap", False):
        pygame.image.save(pantalla, os.path.join(OUT, "parpadeo.png"))
mundo.dibujar_parpadeos = espia
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]; ms[0] += 16
    j = st.get("j") or next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    fa = st.get("fa") or next(o for o in gc.get_objects() if isinstance(o, F.SistemaFauna))
    st["j"], st["fa"] = j, fa
    if f == 3:
        j.talismanes.anillos["sombra_conejo"] = 1
        j.talismanes.equipar("sombra_conejo"); j.recalcular_talismanes()
        # fuera del jardin de la casa (la fauna no puede entrar en el)
        j.posicion = pygame.Vector2(j.posicion.x, j.posicion.y + 700); j.destino = pygame.Vector2(j.posicion)
    if f == 60:
        lobo = F.LoboSolitario(j.posicion.x + 90, j.posicion.y + 40)
        fa.lobos_solitarios.append(lobo); st["lobo"] = lobo
    if f == 62:
        j.recibir_dano(3, "fisico")
        st["lobo"].recibir_dano(1)
        crs = [c for h in j.fuentes_criaturas() for c in getattr(h, "criaturas", ())]
        st["n_sombras"] = len(crs)
        for c in crs: c.recibir_dano(0.5)
        st["cap"] = True
    if f >= 90:
        return [pygame.event.Event(pygame.QUIT)]
    return []
pygame.event.get = falso
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 1, "vida": 30,
          "fuerza": 2, "energia": 100, "escudo": 0, "escudo_magico": 0,
          "habilidades": [], "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
v = st["vistos"]
print("      entidades que parpadearon:", {k: len(x) for k, x in v.items()}, "| sombras:", st.get("n_sombras"))
check("Personaje" in v and max(v["Personaje"]) > 40, "el jugador parpadea en rojo")
check("LoboSolitario" in v and max(v["LoboSolitario"]) > 40, "el animal parpadea en rojo")
otros = [k for k in v if k not in ("Personaje", "LoboSolitario")]
check(st.get("n_sombras", 0) > 0 and otros and max(max(v[k]) for k in otros) > 40, "la sombra parpadea en rojo (%s)" % otros)
print("\\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
