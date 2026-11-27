# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Fase 2: coleccion de herramientas y habilidades (logica + bucle real).
import os, sys, gc, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
random.seed(3)
import habilidades, herramientas, mundo, fauna, inventario, talismanes as TL
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

def nuevo(habs=("Disparo Veloz", "Invocar Lobos", "Cortar"), herr="Espada Larga"):
    hs = [habilidades.crear_habilidad(n) for n in habs]
    for i, h in enumerate(hs):
        h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
    return Personaje("T", 0, 0, 1, 3, 100, 10, 300, 10, (0, 0, 255), hs, herramientas.crear_herramienta(herr), 10)

pygame.display.set_mode((10, 10))
# ---------------- logica
j = nuevo()
check([h.nombre for h in j.huecos_habilidades] == ["Disparo Veloz", "Invocar Lobos", "Cortar"], "la creacion llena los 3 huecos en orden")
check(len(j.coleccion_herramientas) == 1 and len(j.herramientas_faltantes()) == 5, "empieza con 1 herramienta, faltan 5")
check(len(j.habilidades_faltantes()) == 12, "faltan 12 habilidades")
arco = j.agregar_herramienta("Arco")
check(arco is not None and arco.nivel == 1 and j.herramienta.nombre == "Espada Larga", "herramienta nueva a nivel 1, sin equiparla")
check(j.agregar_herramienta("Arco") is None, "no se repite una herramienta")
larga = j.herramienta
larga.subir_nivel(); larga.desgastar(30)
nv, dur = larga.nivel, larga.durabilidad
larga.activa = True
check(j.equipar_herramienta(arco) and j.herramienta is arco and not arco.activa, "equipar otra: la nueva empieza guardada")
check(larga.nivel == nv and larga.durabilidad == dur and not larga.activa, "la anterior conserva nivel y durabilidad")
esc = j.agregar_herramienta("Escudo")
j.subir_stat("escudo") if j.puntos_mejora else None
j.equipar_herramienta(esc); m_con = j.escudo_max
j.equipar_herramienta(larga)
check(j.escudo_max <= m_con and j.escudo <= j.escudo_max, "al quitar el Escudo se pierde su pasiva y el escudo se recorta")

# habilidades
paso = j.agregar_habilidad("Paso 0")
check(paso is not None and paso not in j.habilidades and paso in j.coleccion_habilidades, "habilidad nueva queda guardada si los huecos estan llenos")
lobos = j.huecos_habilidades[1]
j.energia = 300
lobos.intentar_activar(j)
check(lobos.estado == "INVOCADO" and len(lobos.criaturas) == 3, "lobos invocados")
crs = list(lobos.criaturas)
check(j.equipar_habilidad(paso, 1), "poner Paso 0 en [3]")
check(j.huecos_habilidades[1] is paso and paso.tecla == pygame.K_3 and paso.tecla_str == "3", "Paso 0 toma la tecla [3]")
check(all(not c.vivo for c in crs) and not lobos.criaturas, "los lobos de la habilidad quitada desaparecen")
check(lobos.estado == "COOLDOWN" and lobos.tiempo_restante_cooldown > 0, "la habilidad quitada pasa a su recarga (%.0f s)" % lobos.tiempo_restante_cooldown)
check(lobos in j.habilidades_guardadas() and lobos not in j.habilidades, "queda guardada en la coleccion")
cd0 = lobos.tiempo_restante_cooldown
for _ in range(50): lobos.actualizar(0.1, j)
check(abs(lobos.tiempo_restante_cooldown - (cd0 - 5)) < 0.01, "su recarga sigue corriendo guardada")
dv = j.huecos_habilidades[0]
check(j.equipar_habilidad(dv, 2) and j.huecos_habilidades[2] is dv and j.huecos_habilidades[0].nombre == "Cortar",
      "mover una equipada a otro hueco intercambia (Disparo Veloz <-> Cortar)")
check(dv.tecla == pygame.K_4 and j.huecos_habilidades[0].tecla == pygame.K_2, "las teclas siguen al hueco")
check([h.nombre for h in j.habilidades] == [h.nombre for h in j.huecos_habilidades], "jugador.habilidades = huecos en orden")
# activa al quitar
paso.intentar_activar(j)
check(j.invisible, "Paso 0 activo -> invisible")
j.equipar_habilidad(lobos, 1)
check(not j.invisible and paso.estado == "COOLDOWN", "quitar Paso 0 activo termina la invisibilidad y entra en recarga")
# hueco libre
j2 = nuevo(habs=("Destello",))
check(j2.huecos_habilidades[1] is None and j2.agregar_habilidad("Cortar") in j2.huecos_habilidades, "si hay hueco libre la nueva se equipa sola")

# ---------------- bucle real: [Y], pestana Equipo, clics, teclas, muerte y totem
pygame.display.Info = lambda: type("I", (), {"current_w": 1600, "current_h": 900})()
_sm = pygame.display.set_mode
pygame.display.set_mode = lambda size, flags=0: _sm(size)
class Reloj:
    def tick(self, fps=0): return 16
pygame.time.Clock = Reloj
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda self, k: False})()
raton = [(800, 450)]
pygame.mouse.get_pos = lambda: raton[0]
def tecla(k): return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)
def clic(pos): return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
st = {"f": 0, "b": {}}
_dib = inventario.dibujar_inventario
def espia(*a, **k):
    b = _dib(*a, **k); st["b"] = dict(b); return b
mundo.dibujar_inventario = espia
orig = pygame.event.get
def falso(*a, **k):
    orig(); st["f"] += 1; f = st["f"]
    j = next(o for o in gc.get_objects() if isinstance(o, Personaje) and o.nombre == "Juego")
    ev = []
    if f == 3:
        ev += [tecla(pygame.K_y)] * 30
    if f == 5:
        check(len(j.coleccion_herramientas) + len(j.coleccion_habilidades) > 12, "[Y] da herramientas y habilidades (%d + %d)" % (len(j.coleccion_herramientas), len(j.coleccion_habilidades)))
        ev.append(tecla(pygame.K_i))
    if f == 7:
        ev.append(clic(st["b"]["__inv__tab__equipo"].center))
    if f == 9:
        b = st["b"]
        k_herr = next(k for k in b if k.startswith("__inv__herr__"))
        st["herr_obj"] = j.coleccion_herramientas[int(k_herr.split("__")[3])]
        ev.append(clic(b[k_herr].center))
    if f == 11:
        check(j.herramienta is st["herr_obj"], "clic en Equipar cambia la herramienta (%s)" % j.herramienta.nombre)
        b = st["b"]
        k_hab = next(k for k in b if k.startswith("__inv__hab__") and j.coleccion_habilidades[int(k.split("__")[3])] not in j.huecos_habilidades and k.endswith("__0"))
        st["hab_obj"] = j.coleccion_habilidades[int(k_hab.split("__")[3])]
        raton[0] = b[k_hab].center
        ev.append(clic(b[k_hab].center))
    if f == 13:
        check(j.huecos_habilidades[0] is st["hab_obj"] and st["hab_obj"].tecla == pygame.K_2, "clic en [2] pone %s en el hueco [2]" % st["hab_obj"].nombre)
        st["cap"] = True
        ev.append(tecla(pygame.K_i))
    if f == 15:
        h = st["hab_obj"]; j.energia = j.energia_max
        st["estado_antes"] = h.estado
        ev.append(tecla(pygame.K_2))      # la tecla [2] activa la nueva habilidad
    if f == 17:
        h = st["hab_obj"]
        check(h.estado != "LISTA" or getattr(h, "cargando", False) or h.nombre in ("Regeneración Inversa", "Disparo Venenoso", "Golpe de Suerte", "Carga de Fuego", "Sombra Araña"),
              "la tecla [2] usa la habilidad nueva (%s -> %s)" % (h.nombre, h.estado))
        # totem: no se pierde la coleccion
        j.talismanes.agregar_totem(); j.talismanes.equipar(TL.TOTEM)
        st["col"] = (len(j.coleccion_herramientas), len(j.coleccion_habilidades), j.herramienta.nombre)
        j.vida = 0
    if f == 19:
        check((len(j.coleccion_herramientas), len(j.coleccion_habilidades), j.herramienta.nombre) == st["col"], "con totem se conserva toda la coleccion")
        j.vida = 0
    if f == 21:
        ev.append(tecla(pygame.K_r))      # reaparecer sin totem
    if f == 23:
        check([h.nombre for h in j.habilidades] == ["Disparo Veloz", "Invocar Lobos", "Cortar"] and j.herramienta.nombre == "Espada Larga",
              "sin totem: vuelves al equipo de la creacion")
        check(len(j.coleccion_herramientas) == 1 and len(j.coleccion_habilidades) == 3 and all(h.nivel == 1 for h in j.habilidades),
              "y se pierde todo lo demas")
        ev.append(pygame.event.Event(pygame.QUIT))
    return ev
pygame.event.get = falso
_flip = pygame.display.flip
def flip():
    if st.pop("cap", False):
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "equipo.png"))
    _flip()
pygame.display.flip = flip
hs = [habilidades.crear_habilidad(n) for n in ("Disparo Veloz", "Invocar Lobos", "Cortar")]
for i, h in enumerate(hs):
    h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
config = {"nombre": "Juego", "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3, "vida": 100,
          "fuerza": 10, "energia": 100, "escudo": 10, "escudo_magico": 10,
          "habilidades": hs, "herramienta": herramientas.crear_herramienta("Espada Larga")}
mundo.iniciar_mundo(config)
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
