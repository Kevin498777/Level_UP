"""Prueba en el bucle real del mundo (~3 min): Autoapuntado con cada habilidad y cada herramienta,
maniqui en movimiento (orbita) y personaje con +5 de velocidad.
Uso: python -B pruebas/humo/humo_autoapuntado_total.py  (PRUEBA_CASOS="Invocar Lobos,Arco" filtra casos)"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import math
import random
import traceback

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
import mundo
from habilidades import HABILIDADES_DISPONIBLES, crear_habilidad
from herramientas import HERRAMIENTAS_DISPONIBLES, crear_herramienta
from personaje import AUTOAPUNTADO_RANGO

VEL_BASE = 1.0
VEL_PRUEBA = VEL_BASE + 5          # +5 de velocidad
DT_MS = 16
ORBITA_RADIO = 160                 # el maniqui orbita el centro del mapa
ORBITA_VEL = 0.9                   # rad/s (~145 px/s)
CAPTURAS = {"Carga de Fuego": 400, "Invocar Lobos": 400, "Cortar": 400}
# Escena lejos de la casa del spawn (sus paredes y el jardin estan en el centro del mapa)
RADIO_DESPEJE = 650               # se quitan rocas, arbustos, arboles y lagos de la escena


def angulo_hacia(desde, hasta):
    h = pygame.Vector2(hasta) - pygame.Vector2(desde)
    return math.degrees(math.atan2(h.x, -h.y)) % 360.0


def dif_ang(a, b):
    return abs((a - b + 180) % 360 - 180)


class RelojFalso:
    def tick(self, *_):
        return DT_MS


class Teclas:
    def __init__(self):
        self.mantenidas = set()

    def __getitem__(self, k):
        return k in self.mantenidas


# --- Maniqui en movimiento: el ancla orbita el centro (salvo que la prueba la fije) ---
_act_orig = mundo.Maniqui.actualizar
ESTADO_MANIQUI = {"t": 0.0, "fija": None, "obj": None}


def centro_prueba():
    return mundo.CENTRO_MUNDO + pygame.Vector2(0, -1500)


def despejar(L, c):
    """Quita de la escena todo lo que pueda estorbar (obstaculos, agua y fauna cercana)."""
    def cerca(o):
        p = getattr(o, "centro", None) or getattr(o, "posicion", None) or o.rect.center
        return (pygame.Vector2(p) - c).length() < RADIO_DESPEJE
    L["rocas"][:] = [o for o in L["rocas"] if not cerca(o)]
    veg = L["vegetacion"]
    for lista in (veg.arbustos, veg.arboles):
        lista[:] = [o for o in lista if not cerca(o)]
    L["charcos"][:] = [o for o in L["charcos"] if (pygame.Vector2(o.centro) - c).length() > RADIO_DESPEJE + o.radio]


def act_movil(self, dt, jugador=None):
    ESTADO_MANIQUI["obj"] = self
    ESTADO_MANIQUI["t"] += dt
    if ESTADO_MANIQUI["fija"] is not None:
        self.ancla.update(ESTADO_MANIQUI["fija"])
    else:
        a = ESTADO_MANIQUI["t"] * ORBITA_VEL
        c = centro_prueba()
        self.ancla.update(c.x + math.cos(a) * ORBITA_RADIO,
                          c.y + math.sin(a) * ORBITA_RADIO)
    _act_orig(self, dt, jugador)


mundo.Maniqui.actualizar = act_movil
mundo.pygame.time.Clock = RelojFalso


class InfoPantalla:                 # pantalla 1920x1080 (el driver dummy da 1024x768)
    current_w = 1920
    current_h = 1080


mundo.pygame.display.Info = lambda: InfoPantalla


def correr(nombre_herr, nombre_hab):
    random.seed(5)                      # repetible: la fauna cercana no cambia entre ejecuciones
    ESTADO_MANIQUI.update(t=0.0, fija=None, obj=None)
    teclas = Teclas()
    mundo.pygame.key.get_pressed = lambda: teclas
    hab = crear_habilidad(nombre_hab) if nombre_hab else None
    if hab:
        hab.asignar_tecla(pygame.K_2, "2")
    herr = crear_herramienta(nombre_herr)
    r = {"errores": [], "fallos": [], "frames_apuntado": 0, "max_desvio": 0.0,
         "proy": 0, "proy_mal": 0, "vel_on": set(), "vel_off": set(), "dano": 0.0,
         "bloqueos_ok": [], "golpes_jugador": 0}
    vistos = set()
    real_get = pygame.event.get
    n = {"f": 0}
    L = {}

    def a_pantalla(p):
        cam = L["camara"]
        vx = round(cam.x - L["mundo_w"] / 2)
        vy = round(cam.y - L["mundo_h"] / 2)
        return (round(L["mundo_x"] + p.x - vx), round(L["mundo_y"] + p.y - vy))

    def clic(boton, punto):
        if boton == 3:
            r.setdefault("log", []).append((n["f"], L["jugador"].objetivo_apuntado is not None,
                                            round((L["maniqui"].posicion - L["jugador"].posicion).length()),
                                            a_pantalla(pygame.Vector2(punto)), L["mundo_x"], L["mundo_w"], L["mundo_h"]))
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=boton, pos=a_pantalla(pygame.Vector2(punto)))

    def tecla(tipo, k):
        teclas.mantenidas.add(k) if tipo == pygame.KEYDOWN else teclas.mantenidas.discard(k)
        return pygame.event.Event(tipo, key=k)

    def get_falso(*a, **k):
        n["f"] += 1
        f = n["f"]
        ev = list(real_get(*a, **k))
        L.update(sys._getframe(1).f_locals)
        j = L["jugador"]
        man = L["maniqui"]
        j.energia = j.energia_max                     # energia infinita para la prueba
        c = centro_prueba()
        tecla_hab = pygame.K_2
        es_cargable = hab is not None and getattr(hab, "cargable", False) and hasattr(hab, "cargando")
        es_invocacion = hab is not None and hasattr(hab, "ordenar")
        es_arco = hasattr(herr, "iniciar_carga")

        # --- Comprobaciones continuas ---
        obj = j.objetivo_apuntado
        if obj is not None:
            r["frames_apuntado"] += 1
            d = dif_ang(j.angulo, angulo_hacia(j.posicion, obj.posicion))
            r["max_desvio"] = max(r["max_desvio"], d)
            r["vel_on"].add(j.velocidad)
            if (obj.posicion - j.posicion).length() > AUTOAPUNTADO_RANGO + 8:
                r["fallos"].append(f"f{f}: sigue apuntando a {round((obj.posicion - j.posicion).length())} px")
        else:
            r["vel_off"].add(j.velocidad)
        nuevos = list(j.proyectiles)
        if hab is not None and hasattr(hab, "cuchillas"):
            nuevos += hab.cuchillas
        for p in nuevos:
            if id(p) in vistos or not hasattr(p, "direccion"):
                continue
            vistos.add(id(p))
            if obj is not None:
                r["proy"] += 1
                ang_p = math.degrees(math.atan2(p.direccion.x, -p.direccion.y)) % 360.0
                if dif_ang(ang_p, angulo_hacia(j.posicion, obj.posicion)) > 10:
                    r["proy_mal"] += 1
        if man.vivo:
            r["dano"] = max(r["dano"], (100 + 50 + 50) - (man.vida + man.escudo + man.escudo_magico))

        # --- Guion ---
        if f == 2:
            despejar(L, c)
            man.posicion.update(c.x + ORBITA_RADIO, c.y)
            L["camara"].update(c)
        if f == 3:
            j.posicion.update(c.x + 320, c.y)
            j.destino = pygame.Vector2(j.posicion)
        if f == 8:
            ev.append(tecla(pygame.KEYDOWN, pygame.K_1))   # desenfundar el arma
            ev.append(tecla(pygame.KEYUP, pygame.K_1))
            if hab is not None and es_invocacion:
                ev.append(tecla(pygame.KEYDOWN, tecla_hab))  # invocar
                ev.append(tecla(pygame.KEYUP, tecla_hab))
        if f == 20:
            ev.append(clic(3, man.posicion))
        if f == 21:
            if j.objetivo_apuntado is not man:
                r["fallos"].append(f"no se activo con clic derecho (aviso: '{j.mensaje_apuntado}')")
        # paseo: un destino nuevo cada 45 frames en un circulo de 300 alrededor del centro
        if 30 <= f < 680 and f % 45 == 0:
            a = math.radians((f // 45) * 70)
            ev.append(clic(1, (c.x + math.cos(a) * 300, c.y + math.sin(a) * 300)))
        # uso de la habilidad: pulsar, mantener 50 frames y soltar, cada 120 frames
        if hab is not None and 60 <= f < 660:
            fase = (f - 60) % 120
            if fase == 0:
                ev.append(tecla(pygame.KEYDOWN, tecla_hab))
            if fase == 20 and es_invocacion:
                r["combate_al_clic"] = hab.modo_combate
                ev.append(clic(3, man.posicion))             # orden con la tecla mantenida
            if fase == 21 and es_invocacion and r["combate_al_clic"] and j.objetivo_apuntado is None:
                r["fallos"].append(f"f{f}: la orden a las invocaciones quito el autoapuntado")
            if fase == 50:
                ev.append(tecla(pygame.KEYUP, tecla_hab))
        # golpe / disparo del arma: mantener [Espacio] 70 frames cada 120
        if 90 <= f < 660:
            fase = (f - 90) % 120
            if fase == 0:
                ev.append(tecla(pygame.KEYDOWN, pygame.K_SPACE))
            if fase == 70:
                ev.append(tecla(pygame.KEYUP, pygame.K_SPACE))
        # --- Bloqueo por carga / modo combate ---
        # Preparacion (cambios posteriores a esta prueba): la Carga de Fuego recarga 8-15 s, los
        # lobos empujan al maniqui lejos y la telarana de la Arana lo inmoviliza. Antes de cada
        # prueba de activacion se deja la habilidad lista y el maniqui libre y al alcance.
        if f in (699, 755, 765, 875, 955):
            if es_cargable and hab.estado != "ACTIVA" and not getattr(hab, "cargando", False):
                hab.estado = "LISTA"; hab.tiempo_restante_cooldown = 0
            if hasattr(man, "inmovilizado"):
                man.inmovilizado = None
        if f in (755, 955):
            if not man.vivo:                 # los lobos de sombra pueden haberlo matado
                man._reiniciar()
            man.posicion.update(man.ancla)
            if (man.posicion - j.posicion).length() > AUTOAPUNTADO_RANGO - 100:
                j.posicion.update(man.posicion + pygame.Vector2(200, 0)); j.destino = pygame.Vector2(j.posicion)
        if f == 690:
            lejos = (j.posicion - man.posicion)
            lejos = lejos.normalize() if lejos.length_squared() else pygame.Vector2(1, 0)
            ev.append(clic(3, j.posicion + lejos * 150))     # terreno libre visible: quitar
        if f == 691 and j.objetivo_apuntado is not None:
            r["fallos"].append("clic en terreno libre no lo quito")
        prueba_bloqueo = None
        if es_cargable:
            prueba_bloqueo = ("carga", tecla_hab)
        elif es_invocacion:
            prueba_bloqueo = ("invocacion", tecla_hab)
        elif es_arco:
            prueba_bloqueo = ("arco", pygame.K_SPACE)
        if prueba_bloqueo:
            tipo, k = prueba_bloqueo
            if f == 700:
                ev.append(tecla(pygame.KEYDOWN, k))
            if f == 730:
                r["estado_bloqueo"] = (getattr(hab, "cargando", None), getattr(hab, "modo_combate", None),
                                       getattr(herr, "cargando", None), getattr(hab, "estado", None))
                ev.append(clic(3, man.posicion))
            if f == 731:
                bloqueado = j.objetivo_apuntado is None
                if tipo == "invocacion" and not r["estado_bloqueo"][1]:
                    tipo = "invocacion sin modo combate (recarga), no aplica"
                    bloqueado = True
                    j.objetivo_apuntado = None
                r["bloqueos_ok"].append((tipo, bloqueado, j.mensaje_apuntado))
            if f == 740:
                ev.append(tecla(pygame.KEYUP, k))
        if f == 760:
            ev.append(clic(3, man.posicion))
        if f == 761 and j.objetivo_apuntado is not man:
            r["fallos"].append(f"no se reactivo tras soltar (aviso '{j.mensaje_apuntado}', dist {round((man.posicion - j.posicion).length())})")
        # ya activo, se puede cargar
        if prueba_bloqueo and prueba_bloqueo[0] != "invocacion":
            if f == 770:
                ev.append(tecla(pygame.KEYDOWN, prueba_bloqueo[1]))
            if f == 790:
                cargando = getattr(hab, "cargando", False) or getattr(herr, "cargando", False)
                if not cargando or j.objetivo_apuntado is None:
                    r["fallos"].append(f"con autoapuntado activo no pudo cargar (cargando={cargando})")
            if f == 800:
                ev.append(tecla(pygame.KEYUP, prueba_bloqueo[1]))
        # objetivo se aleja mas de 500
        if f == 820:
            dirx = (man.posicion - j.posicion)
            dirx = dirx.normalize() if dirx.length_squared() else pygame.Vector2(1, 0)
            j.destino = pygame.Vector2(j.posicion)
            ESTADO_MANIQUI["fija"] = j.posicion + dirx * (AUTOAPUNTADO_RANGO + 150)
        if f == 900 and j.objetivo_apuntado is not None:
            r["fallos"].append(f"no se solto a {round((man.posicion - j.posicion).length())} px")
        if f == 901:
            ESTADO_MANIQUI["fija"] = None
            j.destino = pygame.Vector2(c.x + 300, c.y)
        if f == 960:
            ev.append(clic(3, man.posicion))
        if f == 970:
            if j.objetivo_apuntado is man:
                man.recibir_dano(10000)
            else:
                r["fallos"].append("no se pudo reactivar para la prueba de muerte")
        if f == 972 and j.objetivo_apuntado is not None:
            r["fallos"].append("no se solto al morir el objetivo")
        if nombre_hab in CAPTURAS and f == CAPTURAS[nombre_hab]:
            pygame.image.save(pygame.display.get_surface(),
                              os.path.join(sys.argv[2],                       # carpeta temporal de capturas
                                           f"cap_{nombre_hab.replace(' ', '_')}.png"))
        if f >= 980:
            ev.append(pygame.event.Event(pygame.QUIT))
        return ev

    mundo.pygame.event.get = get_falso
    cfg = {"nombre": "T", "vida": 200, "fuerza": 2, "velocidad": VEL_PRUEBA, "energia": 100,
           "escudo": 0, "escudo_magico": 0, "herramienta": herr, "habilidades": [hab] if hab else []}
    try:
        mundo.iniciar_mundo(cfg)
    except Exception:
        r["errores"].append(traceback.format_exc())
    finally:
        mundo.pygame.event.get = real_get
    r["vida_jugador"] = L.get("jugador").vida if L.get("jugador") else None
    r["herr_durab"] = getattr(herr, "durabilidad", None)
    return r


herramientas = list(HERRAMIENTAS_DISPONIBLES)
casos = [(herramientas[i % len(herramientas)], h) for i, h in enumerate(HABILIDADES_DISPONIBLES)]
casos += [(h, None) for h in herramientas]
# Filtro opcional: PRUEBA_CASOS="Invocar Lobos,Sombra Araña" ejecuta solo esas habilidades
if os.environ.get("PRUEBA_CASOS"):
    _sel = [x.strip() for x in os.environ["PRUEBA_CASOS"].split(",")]
    casos = [c for c in casos if c[1] in _sel or c[0] in _sel]
total_fallos = 0
for herr, hab in casos:
    res = correr(herr, hab)
    malos = res["fallos"] + [e.strip().splitlines()[-1] for e in res["errores"]]
    total_fallos += len(malos)
    bloq = "; ".join(f"{t}: {'bloquea' if b else 'NO BLOQUEA'} '{m}'" for t, b, m in res["bloqueos_ok"])
    print(f"[{'OK' if not malos else 'FALLO'}] {herr:14s} + {hab or '-':22s} apuntado {res['frames_apuntado']:4d} fr | "
          f"desvio max {res['max_desvio']:.1f}° | proyectiles {res['proy']} (mal {res['proy_mal']}) | "
          f"vel on {sorted(res['vel_on'])[:4]} off {sorted(res['vel_off'])[:4]} | dano maniqui {res['dano']:.1f} | "
          f"vida jug {res['vida_jugador']} | durab {res['herr_durab']}" + (f" | {bloq}" if bloq else ""))
    if res.get("estado_bloqueo") and not all(b for _, b, _ in res["bloqueos_ok"]):
        print("     estado al clic (hab.cargando, hab.modo_combate, herr.cargando, hab.estado):", res["estado_bloqueo"])
    for m in malos:
        print("     -", m)
    if malos:
        print("     clics der (frame, apuntado_antes, dist, pantalla, mx, mw, mh):", [x for x in res.get("log", []) if x[0] >= 680])
    for e in res["errores"]:
        print(e)
print()
print("TODO OK" if not total_fallos else f"{total_fallos} FALLOS")
