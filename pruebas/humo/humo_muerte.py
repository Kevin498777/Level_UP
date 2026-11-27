# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Flujo real de iniciar_mundo: XP al matar, muerte, reaparecer y volver al menu.
import os, sys, random, gc
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
PROY = sys.argv[1]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(2)
import habilidades, herramientas, mundo
from personaje import Personaje
from fauna import SistemaFauna

class Reloj:
    def tick(self, fps=0):
        return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c:
        fallos.append(m)

def buscar(cls):
    return next((o for o in gc.get_objects() if isinstance(o, cls)), None)

st = {"f": 0, "j": None, "fa": None}
def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)

orig = pygame.event.get
def falso(*a, **k):
    orig()
    st["f"] += 1; f = st["f"]
    if st["j"] is None:
        st["j"] = buscar(Personaje); st["fa"] = buscar(SistemaFauna)
    j, fa = st["j"], st["fa"]
    W, H = pygame.display.get_surface().get_size()
    ev = []
    if f == 5:
        # Preparar: subir habilidades/arma, invocar lobos y llevar un venado al lado
        for h in j.habilidades:
            for _ in range(5): h.subir_nivel()
        j.energia = j.energia_max
        ev.append(tecla(pygame.K_3))          # Invocar Lobos
        st["v"] = v = fa.venados[0]
        v.posicion = pygame.Vector2(j.posicion) + pygame.Vector2(60, 0)
    if f == 10:
        st["v"].recibir_dano(1000, "fisico", pygame.Vector2(1, 0))
        st["lobo"] = fa.manadas[0].lobos[1]
        st["lobo"].recibir_dano(1000, "fisico", pygame.Vector2(1, 0))
    if f == 12:
        check(60 + 5 <= j.monedas <= 60 + 12, "lobo + venado: monedas de caza (5-12) + 3 subidas de nivel x 20 = %d" % j.monedas)
        check(j.xp == 0 and j.nivel == 4, "venado 2 + lobo 5 = 7 XP -> nv4 justo (xp=%s nv=%s)" % (j.xp, j.nivel))
        j.ganar_xp(20)                        # nivel 5
        st["nv_antes"] = j.nivel
        st["hab_ids"] = [id(h) for h in j.habilidades]
        lobos = [c for h in j.habilidades for c in getattr(h, "criaturas", ())]
        check(len(lobos) > 0, "hay sombras invocadas antes de morir (%d)" % len(lobos))
        st["sombras"] = lobos
        j.posicion = pygame.Vector2(j.posicion) + pygame.Vector2(300, 0)
        j.destino = pygame.Vector2(j.posicion)
        j.vida = 0
    if f == 14:
        st["pos_muerto"] = pygame.Vector2(j.posicion)
        ev.append(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(mundo_x_aprox(W) + 30, 40)))
        ev.append(tecla(pygame.K_l)); ev.append(tecla(pygame.K_SPACE))
    if f == 40:
        check(j.posicion == st["pos_muerto"] and j.nivel == st["nv_antes"], "muerto: el mundo y el jugador quedan congelados (clics y teclas ignorados)")
        ev.append(tecla(pygame.K_r))
    if f == 42:
        check(j.nivel == 1 and j.xp == 0 and j.puntos_mejora == 4, "reaparece a nivel 1, XP 0 y 4 puntos")
        check(j.monedas == 0, "al morir se pierden todas las monedas")
        check(j.vida == j.vida_max and j.energia == j.energia_max, "vida y energia llenas")
        check((j.posicion - mundo.CENTRO_MUNDO).length() < 40, "reaparece en el centro (spawn)")
        check(all(h.nivel == 1 for h in j.habilidades) and [id(h) for h in j.habilidades] != st["hab_ids"], "habilidades nuevas a nivel 1")
        check([h.tecla for h in j.habilidades] == [pygame.K_2, pygame.K_3, pygame.K_4], "conservan sus teclas 2/3/4")
        check(j.herramienta.nivel == 1, "arma a nivel 1")
        check(all(not c.vivo for c in st["sombras"]), "las sombras invocadas desaparecen")
        check(st["fa"] is buscar(SistemaFauna) and not st["v"].vivo, "el mundo sigue igual (misma fauna, el venado sigue muerto)")
    if f == 50:
        j.vida = 0
    if f == 55:
        ev.append(tecla(pygame.K_m))           # volver al menu principal desde la pantalla de muerte
    if f > 400:
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev

def mundo_x_aprox(W):
    return 230
pygame.event.get = falso
pygame.mouse.get_pos = lambda: (500, 400)

habs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
for i, h in enumerate(habs):
    h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Prueba", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 300, "escudo": 10, "escudo_magico": 10,
          "habilidades": habs, "herramienta": herramientas.crear_herramienta("Espada Ligera")}
r = mundo.iniciar_mundo(config)
check(r == "menu" and st["f"] < 60, "[M] en la pantalla de muerte vuelve al menu principal (frame %d)" % st["f"])
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
