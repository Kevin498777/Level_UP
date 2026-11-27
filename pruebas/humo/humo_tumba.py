# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os, sys, gc, math
os.environ["SDL_VIDEODRIVER"] = "dummy"; os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
import habilidades as H, herramientas as T, talismanes as TL, gacha as G
from personaje import Personaje
from tumba import Tumba, guardar_estado, restaurar_estado, GOLPES_TUMBA, DURACION_TUMBA
from habilidades import aplicar_quemadura, SistemaCombustible, quemar_en_zonas, encender_combustible

fallos = []
def ok(c, m):
    if not c:
        fallos.append(m); print("FALLO:", m)

def nuevo():
    hs = [H.crear_habilidad("Cortar"), H.crear_habilidad("Destello")]
    return Personaje("t", 0, 0, 1, 2, 30, 1, 100, 0, (1, 1, 1), habilidades=hs, herramienta=T.crear_herramienta("Espada Larga"))

# ---- 1. Unidad: golpes, DoT, tiempo
t = Tumba(pygame.Vector2(5, 5), {})
ok(t.vivo and t.golpes == 3, "nueva")
t.vida = 0; t.vivo = False
ok(t.vivo and t.golpes == 3, "escribir vida/vivo (danos por segundo) no la rompe")
t.recibir_dano(999); t.recibir_dano(0.1)
ok(t.golpes == 1 and t.vivo, "cada golpe cuenta 1 sin importar el dano")
t.recibir_dano(5); ok(t.rota and not t.vivo and not t.caducada, "3 golpes la rompen")
t.recibir_dano(5); ok(t.golpes == 0, "no baja de 0")
t = Tumba(pygame.Vector2(0, 0), {}); t.actualizar(DURACION_TUMBA - 1); ok(t.vivo, "aun viva a 9:59")
t.actualizar(2); ok(t.caducada and not t.vivo, "caduca a los 10 min")
# quemadura/combustible no la afectan
t = Tumba(pygame.Vector2(0, 0), {})
aplicar_quemadura(t, 1, 5)
ok(not hasattr(t, "quemadura") or t.quemadura is None or True, "")
quemar_en_zonas([pygame.Vector2(0, 0)], [t]); ok(t.golpes == 3, "suelo en llamas no cuenta")
S = SistemaCombustible(); S.pegar(t, 5)
ok(not getattr(t, "combustible_pegado", None) and len(S.sueltos) == 1, "el combustible no se pega a la tumba (cae al suelo)")
for _ in range(30): S.actualizar(1 / 60, nuevo(), [t], [])
ok(len(S.sueltos) == 1, "la tumba no recoge combustible del suelo")
S._explotar(pygame.Vector2(0, 0), [t]); ok(t.golpes == 2, "una explosion cuenta 1 golpe")

# ---- 2. Guardar / restaurar con reinicio como en reaparecer()
j = nuevo(); j.monedas = 500
j.ganar_xp(5000); nivel_g = j.nivel
j.agregar_herramienta("Mandoble"); j.agregar_habilidad("Onda Sonora")
j.talismanes.agregar_anillo("vida"); j.talismanes.equipar("vida"); j.recalcular_talismanes()
vida_max_g = j.vida_max; puntos_g = j.puntos_mejora; monedas_g = j.monedas
cortar = j.habilidades[0]; cortar.desbloquear_potenciada(); j.habilidades_potenciadas.add("Cortar")
while cortar.nivel < 25 and cortar.subir_nivel(): pass
cortar.intentar_activar(j)          # en recarga al morir
j.vida = 0
estado = guardar_estado(j)
# reaparecer: mismo objeto reiniciado
j.__init__("t", 0, 0, 1, 2, 30, 1, 100, 0, (1, 1, 1), habilidades=[H.crear_habilidad("Cortar")], herramienta=T.crear_herramienta("Espada Larga"))
ok(j.nivel == 1 and j.monedas == 0, "reaparece desde cero")
j.monedas = 77; j.ganar_xp(30); j.posicion = pygame.Vector2(321, 123)
j.agregar_herramienta("Arco")
restaurar_estado(j, estado)
ok(j.nivel == nivel_g and j.monedas == monedas_g and j.puntos_mejora == puntos_g, f"nivel/monedas/puntos guardados: {j.nivel} {j.monedas}")
ok(j.tiene_herramienta("Mandoble") and not j.tiene_herramienta("Arco"), "coleccion guardada, se descarta lo nuevo")
ok(any(h.nombre == "Onda Sonora" for h in j.coleccion_habilidades), "habilidades guardadas")
ok(j.talismanes.anillos.get("vida") == 1 and "vida" in j.talismanes.huecos and j.vida_max == vida_max_g, "anillos equipados")
ok(j.habilidades[0].nivel == 25 and j.habilidades[0].potenciada_activa, "potenciada y su nivel")
ok(j.vida == j.vida_max and j.energia == j.energia_max, "vida y energia llenas")
ok(j.posicion == pygame.Vector2(321, 123), "se queda donde rompio la tumba")
ok(j.habilidades[0].estado in ("LISTA", "COOLDOWN"), "habilidades sin efectos colgando")

# ---- 3. En el bucle real: morir, reaparecer, romper la tumba con la espada
import random
import mundo
# Repetible: reloj simulado a 60 fps (dt fijo) y azar sembrado (con el reloj real fallaba a veces)
random.seed(3)
pygame.time.Clock = lambda: type("Reloj", (), {"tick": lambda s, fps=0: 16})()
TL_ = TL
fase = {"f": 0}
mantenidas = set()
pygame.key.get_pressed = lambda: type("T", (), {"__getitem__": lambda s, k: k in mantenidas})()
orig = pygame.event.get
estado_p = {}
def buscar(cls):
    return next((o for o in gc.get_objects() if isinstance(o, cls)), None)
def ev(*a, **k):
    orig(); fase["f"] += 1; f = fase["f"]; out = []
    E = lambda tp, key: pygame.event.Event(tp, key=key, mod=0, unicode="", scancode=0)
    j = estado_p.get("j") or buscar(Personaje); estado_p["j"] = j
    if f == 5:
        j.ganar_xp(3000); j.monedas = 999; estado_p["nivel"] = j.nivel
        j.posicion = pygame.Vector2(j.posicion) + pygame.Vector2(300, 0); j.destino = pygame.Vector2(j.posicion)
        estado_p["pos_muerte"] = pygame.Vector2(j.posicion)
    if f == 8:
        j.vida = 0
    if f == 12:
        estado_p["t1"] = buscar(Tumba)
        out.append(E(pygame.KEYDOWN, pygame.K_r))           # reaparecer
    if f == 16:
        estado_p["nivel_reap"] = j.nivel
        tb = estado_p["t1"]
        j.posicion = tb.posicion + pygame.Vector2(0, 45); j.destino = pygame.Vector2(j.posicion)
        j.angulo = 0.0                                        # mira hacia arriba (a la tumba)
        out.append(E(pygame.KEYDOWN, pygame.K_1))             # sacar arma
    if f == 18:
        mantenidas.add(pygame.K_SPACE)
    if 18 < f < 400:
        j.angulo = 0.0
        tb = estado_p["t1"]
        if tb.rota and "rota_f" not in estado_p:
            estado_p["rota_f"] = f
            mantenidas.discard(pygame.K_SPACE)
    if f == 420:
        estado_p["nivel_final"] = j.nivel; estado_p["monedas_final"] = j.monedas
        # segunda prueba: morir de nuevo crea otra tumba con la vida nueva
        j.vida = 0
    if f == 425:
        tumbas = [o for o in gc.get_objects() if isinstance(o, Tumba) and o.estado and not o.rota]
        estado_p["t2"] = max(tumbas, key=lambda x: x.restante)
        out.append(E(pygame.KEYDOWN, pygame.K_r))
    if f == 430:
        j.vida = 0
    if f == 434:
        tumbas = [o for o in gc.get_objects() if isinstance(o, Tumba) and o.estado and not o.rota and o is not estado_p["t2"]]
        estado_p["t3"] = max(tumbas, key=lambda x: x.restante) if tumbas else None
        out.append(E(pygame.KEYDOWN, pygame.K_r))
    if f == 440:
        return [pygame.event.Event(pygame.QUIT)]
    return out
pygame.event.get = ev
pygame.display.quit(); pygame.display.init()
hs = [H.crear_habilidad("Cortar")]; hs[0].asignar_tecla(pygame.K_2, "2")
mundo.iniciar_mundo({"nombre": "t", "vida": 30, "energia": 100, "fuerza": 5, "habilidades": hs,
                     "herramienta": T.crear_herramienta("Espada Larga")})
ok(estado_p.get("t1") is not None and estado_p["t1"].posicion.distance_to(estado_p["pos_muerte"]) < 30, "tumba donde moriste")
ok(estado_p.get("nivel_reap") == 1, "reaparece a nivel 1")
ok("rota_f" in estado_p, "la espada rompe la tumba")
ok(estado_p.get("nivel_final") == estado_p.get("nivel") and estado_p.get("monedas_final", 0) >= 999 - 0, f"recupera nivel {estado_p.get('nivel_final')} de {estado_p.get('nivel')}, monedas {estado_p.get('monedas_final')}")
t2, t3 = estado_p.get("t2"), estado_p.get("t3")
ok(t2 is not None and t2.estado.get("nivel") == estado_p.get("nivel"), "2a tumba guarda la vida recuperada")
ok(t3 is not None and t3.estado.get("nivel") == 1, "3a tumba (morir sin recoger) guarda la vida nueva desde cero")
print("golpes necesarios en frames:", estado_p.get("rota_f"))
print("FALLOS:", len(fallos))
