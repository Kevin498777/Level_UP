"""Pruebas sin ventana: potenciada Afortunado (Golpe de Suerte nv21-30).
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_afortunado.py"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import random
sys.path.insert(0, os.getcwd())
import pygame
pygame.init()

from personaje import Personaje
from herramientas import EspadaLarga
from habilidades import GolpeDeSuerte, Destello, AuraElectrica
import fauna

fallos = []
G = GolpeDeSuerte


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def suerte(n, potenciada=True):
    g = G()
    while g.nivel < min(n, 20):
        g.subir_nivel()
    if potenciada:
        g.desbloquear_potenciada()
        while g.nivel < n:
            assert g.subir_nivel()
    return g


def jugador(habs, energia=100, escudo=0):
    j = Personaje(nombre="t", x=0, y=0, tamano=1, velocidad=3, vida=100, fuerza=3, energia=energia, escudo=escudo,
                  escudo_magico=escudo, color=(0, 0, 0), habilidades=habs, herramienta=EspadaLarga())
    return j


def lanzar(g, j, resultado):
    g.sortear = lambda: resultado
    return g.intentar_activar(j)


def correr(j, g, segundos, dt=1 / 60):
    for _ in range(round(segundos / dt)):
        g.actualizar(dt, j)
        j.actualizar_efectos(dt)


# 1. Escalado por tramos
esperado = {20: ((20, 40), 20, (30, 30), (8.0, 8.0), (20, 20)), 21: ((20, 40), 20, (30, 30), (8.0, 8.0), (20, 20)),
            22: ((30, 60), 22, (32, 32), (8.0, 8.0), (22, 22)), 26: ((50, 100), 26, (36, 36), (8.0, 8.0), (26, 26)),
            28: ((60, 100), 28, (38, 38), (5.0, 5.0), (28, 28)), 30: ((77, 77), 30, (30, 50), (1.0, 5.0), (10, 40))}
for n, (coste, nv, dur, esp, rec) in esperado.items():
    g = suerte(n)
    real = (g.rango_coste, g.nivel_efecto, g.rango_duracion, g.rango_espera, g.rango_recarga)
    comprobar(real == (coste, nv, dur, esp, rec) and g.nombre_mostrado == "Afortunado",
              f"nv{n}: coste {coste}, nivel {nv}, duración {dur}, espera {esp}, recarga {rec}")
comprobar(suerte(20).costo_mejora == 2 and suerte(20).nivel_max == 30, "2 puntos por nivel, máximo 30")
p = suerte(25).probabilidades()
comprobar(abs(p[G.NADA] - 0.05) < 1e-9 and len(p) == 11 and abs(p[G.AF_ESPECTRO] - 0.095) < 1e-9
          and G.VENENO not in p, "nv25: nada 5 %, 10 resultados a 9.5 % y sin autoveneno")
p = suerte(30).probabilidades()
comprobar(abs(p[G.NADA] - 0.01) < 1e-9 and abs(p[G.AF_COLOSAL] - 0.099) < 1e-9, "nv30: nada 1 %, resto 9.9 %")
g = suerte(20, False)
comprobar(g.espera_instantaneo == 2.0 and g.prob_nada == 0.05 and not g.potenciada_activa,
          "Golpe de Suerte nv20 normal sin cambios (espera 2 s, nada 5 %)")
g = suerte(20, False)
g.desbloquear_potenciada()
comprobar(g.potenciada_activa and g.rango_coste == (20, 40), "desbloqueada en el 20 ya es Afortunado")

# 2. Coste aleatorio: mínimo para lanzar y el resto sin bajar de 0
random.seed(1)
costes = set()
for _ in range(200):
    g = suerte(20)
    j = jugador([g])
    j.energia = 80
    lanzar(g, j, G.NADA)
    costes.add(g.ultimo_coste)
    assert j.energia == 80 - g.ultimo_coste
comprobar(min(costes) == 20 and max(costes) == 40 and len(costes) > 15, f"coste al azar entre 20 y 40 ({min(costes)}-{max(costes)})")
g = suerte(20)
j = jugador([g])
j.energia = 30
g._al_azar = lambda r, entero=True: r[1]
lanzar(g, j, G.NADA)
comprobar(j.energia == 0, "con 30 de energía y coste 40 te quedas en 0")
g = suerte(20)
j = jugador([g])
j.energia = 19
comprobar(not lanzar(g, j, G.NADA) and j.energia == 19, "con menos del mínimo (20) no se lanza")
g = suerte(30)
j = jugador([g])
j.energia = 100
lanzar(g, j, G.NADA)
comprobar(j.energia == 23 and 1.0 <= g.espera_instantaneo <= 5.0 and 10 <= g.duracion_cooldown <= 40,
          f"nv30: 77 fijo; espera {g.espera_instantaneo} s y recarga {g.duracion_cooldown} s al azar")

# 3. Potenciadas otorgadas: nivel, duración y bloqueo
for res, nombre, nivel in ((G.AF_COLOSAL, "Burst de Fuerza", 26), (G.AF_RELAMPAGO, "Destello", 26),
                           (G.AF_INVERSO, "Reforzamiento Mágico", 26), (G.AF_VESTIGIOS, "Aura Electrica", 26),
                           (G.AF_ESPECTRO, "Paso 0", 15)):
    g = suerte(26)
    j = jugador([g])
    j.energia = 200
    lanzar(g, j, res)
    e = j.efectos_extra[-1]
    comprobar(e.nombre == nombre and e.nivel == nivel and e.potenciada_activa and e.otorgada
              and e.duracion_activa == 36 and g.estado == "ACTIVA" and g.efecto_actual is e,
              f"{res}: {nombre} nv{e.nivel} potenciada, 36 s y bloquea")
g = suerte(26)
j = jugador([g])
j.energia = 200
lanzar(g, j, G.AF_INVERSO)
e = j.efectos_extra[-1]
comprobar(e.dureza == e.dureza_max and e.dureza_max > 500 and not e.es_inverso, f"Reforzamiento Inverso otorgado: dureza {e.dureza_max}, sin gastar energía")
energia = j.energia
correr(j, g, 10)
comprobar(j.energia >= energia, "no cobra energía por segundo")
correr(j, g, 27)
comprobar(g.estado == "COOLDOWN" and not j.efectos_extra and g.tiempo_restante_cooldown <= 26,
          "al terminar lo otorgado empieza la recarga (26 s)")

# Relámpago otorgado: mantiene su autodaño
g = suerte(30)
j = jugador([g])
j.energia = 200
lanzar(g, j, G.AF_RELAMPAGO)
vida = j.vida
correr(j, g, 4)
comprobar(j.vida < vida, f"Relámpago otorgado mantiene el autodaño ({vida} -> {j.vida})")

# Espectro otorgado: atacar no lo cancela y da cuerpo de niebla
g = suerte(30)
j = jugador([g])
j.energia = 200
j.herramienta.activa = True
lanzar(g, j, G.AF_ESPECTRO)
j.herramienta.atacar(j)
comprobar(j.invisible and j.cuerpo_de_niebla, "Espectro otorgado: invisible, atacar no lo rompe, cuerpo de niebla")

# Vestigios otorgado: la pasiva del arma funciona sin tenerla equipada
g = suerte(30)
j = jugador([g])
j.energia = 200
lanzar(g, j, G.AF_VESTIGIOS)
comprobar(j.bono_dano_habilidades > 0, f"Vestigios otorgado: golpes eléctricos +{j.bono_dano_habilidades:.0%}")

# 4. No bloquean pero no se repiten: Energía +100 %, Escudos +100 %, Inversión Vital
g = suerte(20)
j = jugador([g], energia=100, escudo=20)
j.energia = 50
lanzar(g, j, G.AF_ENERGIA)
comprobar(j.energia_max == 200 and j.energia == 200 and g.efecto_actual is None, "Energía +100 %: máximo 200 y lleno; no bloquea")
comprobar(G.AF_ENERGIA not in g.probabilidades(), "mientras dura no vuelve a salir")
correr(j, g, 9)
comprobar(g.estado == "COOLDOWN", "tras la espera (8 s) pasa a recarga aunque el aumento siga")
correr(j, g, 32)
comprobar(j.energia_max == 100 and j.energia <= 100 and G.AF_ENERGIA in g.probabilidades(),
          "a los 40 s vuelve a 100 y puede volver a salir")
g = suerte(20)
j = jugador([g], escudo=20)
j.energia = 100
lanzar(g, j, G.AF_ESCUDOS)
comprobar(j.escudo_max == 40 and j.escudo == 40 and j.escudo_magico_max == 40, "Escudos +100 %: 20 -> 40 y llenos")
correr(j, g, 41)
comprobar(j.escudo_max == 20 and j.escudo == 20, "al terminar vuelven a 20")

g = suerte(24)
j = jugador([g])
j.energia = 100
j.vida = 50
lanzar(g, j, G.AF_VIDA)
correr(j, g, 15)
comprobar(j.vida == 78 and g.efecto_actual is None, f"Inversión Vital (vida) nv24: +2/s durante 14 s = 28 ({j.vida})")
g = suerte(30)
j = jugador([g])
j.energia = 100
lanzar(g, j, G.AF_ENERGIA_REGEN)
j.energia = 0
correr(j, g, 21)
comprobar(j.energia == 100, f"Inversión Vital (energía) nv30: +8/s durante 20 s, sin pasar del máximo ({j.energia})")
g = suerte(30)
j = jugador([g])
j.energia = 300
j.energia_max = 300
lanzar(g, j, G.AF_ENERGIA_REGEN)
j.energia = 0
correr(j, g, 21)
comprobar(j.energia == 160, f"... total 160 si cabe ({j.energia})")

# 5. Nube de Corrosión: corroe sin veneno con el tope del nivel
g = suerte(30)
j = jugador([g])
j.energia = 100
lanzar(g, j, G.AF_NUBE)
nube = j.efectos_extra[-1]
lobo = fauna.Lobo.__new__(fauna.Lobo)
lobo.posicion, lobo.radio, lobo.vivo, lobo.vida = pygame.Vector2(40, 0), 12, True, 25
lobo._init_combate()
nube.actualizar_dano_enemigos(1 / 60, [lobo], j)
comprobar(lobo.corrosion is not None and lobo.corrosion.tope == 0.30 and lobo.veneno is None and g.efecto_actual is nube,
          "Nube de Corrosión nv30: corroe (tope 30 %) sin veneno y bloquea")
comprobar(suerte(25).tope_nube == 0.20, "nv25: tope de la nube 20 %")

# 6. Misma habilidad dos veces: la equipada al 50 %
aura = AuraElectrica()
while aura.subir_nivel():
    pass
g = suerte(30)
j = jugador([aura, g])
j.energia = 300
aura.intentar_activar(j)
lanzar(g, j, G.AF_VESTIGIOS)
from habilidades import factor_duplicado
activas = [h for h in j.habilidades_en_efecto() if h.nombre == "Aura Electrica" and h.estado == "ACTIVA"]
comprobar(factor_duplicado(aura, activas) == 0.5 and factor_duplicado(j.efectos_extra[-1], activas) == 1.0,
          "Aura equipada + Vestigios otorgado: la equipada aporta 50 %")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
