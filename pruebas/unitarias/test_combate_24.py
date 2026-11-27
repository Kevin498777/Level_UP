# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas del combate cuerpo a cuerpo (24/11): sin empuje doble, invulnerabilidad tras golpe,
# aturdimiento al golpear, vida inicial 30 y parpadeo rojo. Uso: python -B test_combate_24.py <proyecto>
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import fauna as F, herramientas, habilidades, mundo, main
import personaje as P
from personaje import Personaje
from habilidades import PIXELES_POR_PUNTO_EMPUJE as PX

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

def jug(herr="Espada Larga", escudo=0):
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, escudo, (0, 0, 255), [], herramientas.crear_herramienta(herr), 0)
    return j

class Roca:
    def __init__(self): self.rect = pygame.Rect(0, 0, 160, 160); self.rect.center = (300, 0)

# ---------- 1. Empuje: solo uno por golpe
print("--- empuje")
j = jug(); o = F.Oso(Roca()); o.posicion = pygame.Vector2(30, 0)
check(F.golpear_objetivo(o, j, 20, F.OSO_EMPUJE), "el zarpazo entra")
check(abs(j.empuje.length() - F.OSO_EMPUJE * PX) < 1e-6, "zarpazo: empuje solo del oso, %.0f px (antes %.0f)" % (j.empuje.length(), (F.OSO_EMPUJE + 20) * PX))
check(j.vida_max - j.vida > 0, "el zarpazo hace dano")
j = jug(); m = F.Manada(pygame.Vector2(30, 0)); lobo = m.lobos[1]; lobo.posicion = pygame.Vector2(30, 0)
F.golpear_objetivo(lobo, j, lobo.dano)
check(abs(j.empuje.length() - lobo.dano * PX) < 1e-6, "mordida de lobo (sin empuje propio): 1 punto por dano, %.0f px" % j.empuje.length())
j = jug(); jb = F.Jabali(30, 0); F.golpear_objetivo(jb, j, 15, F.JABALI_EMPUJE)
check(abs(j.empuje.length() - F.JABALI_EMPUJE * PX) < 1e-6, "embestida del jabali: solo su empuje (%.0f px)" % j.empuje.length())

# ---------- 2. Invulnerabilidad tras golpe
print("--- invulnerabilidad")
random.seed(3)
j = jug(); a = F.LoboSolitario(25, 0); b = F.LoboSolitario(-25, 0)
check(F.golpear_objetivo(a, j, 15) and j.invulnerable, "tras un golpe queda invulnerable")
v = j.vida
check(not F.golpear_objetivo(b, j, 15) and j.vida == v, "un segundo lobo en el mismo instante no hace dano")
for _ in range(29): j.actualizar_invulnerabilidad(1 / 60)
check(j.invulnerable, "sigue invulnerable a los 0.48 s")
for _ in range(2): j.actualizar_invulnerabilidad(1 / 60)
check(not j.invulnerable and F.golpear_objetivo(b, j, 15), "a los 0.5 s ya se le puede golpear")
# sin desangrado mientras es invulnerable
j = jug(); a = F.LoboSolitario(25, 0); a.prob_desangrado = 1.0; j.marcar_golpe()
a._cd_mordida = 0; a._morder(j)
check(j.desangrado is None and j.vida == j.vida_max, "mordida durante la invulnerabilidad: ni dano ni desangrado")
j.t_invulnerable = 0; a._cd_mordida = 0; a._morder(j)
check(j.desangrado is not None, "fuera de la invulnerabilidad si desangra")
# el Escudo no se desgasta si eres invulnerable
j = jug("Escudo"); j.herramienta.activa = True; j.angulo = 90; dur = j.herramienta.durabilidad; j.marcar_golpe()
F.golpear_objetivo(F.LoboSolitario(25, 0), j, 15)
check(j.herramienta.durabilidad == dur, "invulnerable: el Escudo no se desgasta")
# efectos, ondas y terreno siguen haciendo dano
j = jug(); j.marcar_golpe(); v = j.vida
F.RugidoOnda(j.posicion, dano=10).actualizar(0.0, j)
j.recibir_dano(5, "magico")
check(j.vida < v, "la invulnerabilidad no frena ondas ni dano magico de efectos")
check(jug().t_invulnerable == 0, "un personaje nuevo empieza sin invulnerabilidad")

# ---------- 3. Aturdimiento al golpear
print("--- aturdimiento")
l = F.LoboSolitario(0, 0); l._cd_mordida = 0
check(l.aturdir_ataque() and abs(l._cd_mordida - F.ATURDIR_GOLPE) < 1e-9, "golpearlo retrasa su mordida 0.3 s")
l._cd_mordida = 0
check(not l.aturdir_ataque() and l._cd_mordida == 0, "un segundo golpe enseguida no lo vuelve a aturdir")
for _ in range(61): l._tick_efectos(1 / 60)
check(l.aturdir_ataque(), "pasado 1 s se puede aturdir de nuevo")
l._cd_mordida = 1.5; l._t_inmune_aturdir = 0; l.aturdir_ataque()
check(l._cd_mordida == 1.5, "no acorta un ataque que ya estaba en recarga")
o = F.Oso(Roca()); o._cd_zarpazo = 0; o.aturdir_ataque(); jb = F.Jabali(0, 0); jb._cd_golpe = 0; jb.aturdir_ataque()
check(o._cd_zarpazo >= 0.3 and jb._cd_golpe >= 0.3, "funciona con oso (zarpazo) y jabali (embestida)")
check(all(hasattr(c, "aturdir_ataque") for c in (F.Lobo, F.Cocodrilo, F.Zorro, F.Venado)), "todos los animales combatibles lo tienen")

# ---------- 4. Vida inicial
print("--- vida inicial")
check(main.generar_estadisticas()["vida"] == 30, "la vida inicial es 30")

# ---------- 5. Parpadeo rojo
print("--- parpadeo")
class Ser:
    def __init__(self): self.vida = 10; self.posicion = pygame.Vector2(50, 50); self.radio = 12
s = Ser(); mundo.actualizar_parpadeos([s], 1 / 60)
check(getattr(s, "_t_parpadeo", 0) == 0, "sin perder vida no parpadea")
s.vida = 9; mundo.actualizar_parpadeos([s], 1 / 60)
check(s._t_parpadeo == mundo.PARPADEO_DURACION, "al perder 1 de vida empieza a parpadear")
sup = pygame.Surface((100, 100)); sup.fill((0, 0, 0))
mundo.dibujar_parpadeos(sup, [s], (0, 0))
r, g, b, _ = sup.get_at((50, 50))
check(r > 60 and g < 40, "fase encendida: tinte rojo sobre el cuerpo %s" % ((r, g, b),))
for _ in range(5): mundo.actualizar_parpadeos([s], 1 / 60)
sup.fill((0, 0, 0)); mundo.dibujar_parpadeos(sup, [s], (0, 0))
check(sup.get_at((50, 50))[0] == 0, "fase apagada (parpadeo, no tinte fijo)")
for _ in range(30): mundo.actualizar_parpadeos([s], 1 / 60)
check(s._t_parpadeo == 0, "se apaga a los 0.3 s")
s.vida = 15; mundo.actualizar_parpadeos([s], 1 / 60)
check(s._t_parpadeo == 0, "curarse no parpadea")
s.vida = 14; s.invisible = True; mundo.actualizar_parpadeos([s], 1 / 60)
sup.fill((0, 0, 0)); mundo.dibujar_parpadeos(sup, [s], (0, 0))
check(sup.get_at((50, 50))[0] == 0, "invisible (Paso 0) no delata con el parpadeo")
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
