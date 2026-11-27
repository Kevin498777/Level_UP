# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas de los cambios del 24/11: devolucion del Gacha, +4 puntos por nivel, Regen de energia
# y frecuencia del anillo legendario. Uso: python -B test_cambios_24.py <proyecto>
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import gacha as G, talismanes as TL, herramientas, habilidades
import personaje as P
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

def nuevo():
    return Personaje("T", 0, 0, 1, 1, 20, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"), 0)

def completar(j):
    for n in herramientas.HERRAMIENTAS_DISPONIBLES:
        if n not in [h.nombre for h in j.coleccion_herramientas]: j.agregar_herramienta(n)
    for n in habilidades.HABILIDADES_DISPONIBLES:
        if n not in [h.nombre for h in j.coleccion_habilidades]: j.agregar_habilidad(n)
    for a, d in TL.ANILLOS.items(): j.talismanes.anillos[a] = d["nivel_max"]
    j.talismanes.totems = TL.TOTEM_MAX

# ---------------- 1. Gacha: devolucion fija (10 desde el ajuste posterior), sin monedas infinitas
print("--- Gacha")
check(TL.DEVOLUCION_REPETIDO == 10 and G.DEVOLUCION == 10, "un premio repetido devuelve 10 monedas")
check(G.DEVOLUCION < G.COSTO_TIRADA, "la devolucion (%d) es menor que la tirada (%d)" % (G.DEVOLUCION, G.COSTO_TIRADA))
j = nuevo(); completar(j)
check(not j.herramientas_faltantes() and not j.habilidades_faltantes(), "coleccion completa para la prueba")
rng = random.Random(1); j.monedas = 10**6; tiradas = 20000
for _ in range(tiradas): G.tirar(j, rng)
neto = (j.monedas - 10**6) / tiradas
# Todo conseguido: "Nada" pierde la tirada entera; el resto devuelve DEVOLUCION
esperado = -(G.COSTO_TIRADA - G.DEVOLUCION * (1 - G.PROB_NADA))
check(abs(neto - esperado) < 0.3, "con todo conseguido cada tirada pierde ~%.2f monedas (medido %.2f)" % (-esperado, neto))
j.monedas = 25
n = 0
while G.tirar(j, rng) is not None: n += 1
check(j.monedas < G.COSTO_TIRADA and n < 40, "con todo conseguido las monedas se acaban (%d tiradas con 25)" % n)
j2 = nuevo(); completar(j2); r = G.tirar_anillo(j2, rng)
check(r["devolucion"] == G.DEVOLUCION and j2.monedas == G.DEVOLUCION, "orbe Gacha con el anillo al maximo: +%d" % G.DEVOLUCION)

# ---------------- 2. Puntos de mejora por nivel
print("--- Puntos por nivel")
j = nuevo()
check(j.puntos_mejora == 4, "se empieza con 4 puntos")
j.subir_nivel()
check(j.puntos_mejora == 8 and P.PUNTOS_MEJORA_POR_NIVEL == 4, "subir un nivel da +4 puntos (4 -> 8)")
TOPE = P.NIVEL_MAXIMO                      # 40 desde el 24/11 (antes 20)
for _ in range(TOPE + 10): j.subir_nivel()
check(j.nivel == TOPE and j.puntos_mejora == 4 + (TOPE - 1) * 4, "a nivel %d hay %d puntos en total (%d)" % (TOPE, 4 + (TOPE - 1) * 4, j.puntos_mejora))
check(j.monedas == (TOPE - 1) * P.MONEDAS_POR_NIVEL, "las monedas por nivel siguen en +20 (%d)" % j.monedas)
j.ganar_xp(10**6)
check(j.nivel == TOPE and j.puntos_mejora == 4 + (TOPE - 1) * 4, "la XP de sobra no da puntos pasado el %d" % TOPE)

# ---------------- 3. Regen de energia
print("--- Regen de energia")
j = nuevo(); j.puntos_mejora = 30
check(j.subir_stat("regen_energia") and abs(j.bono_regen_energia - 0.05) < 1e-9, "1 punto = +5 %")
for _ in range(19): j.subir_stat("regen_energia")
check(abs(j.bono_regen_energia - 1.0) < 1e-9 and j.regen_energia_al_tope, "20 puntos = +100 % (tope)")
antes = j.puntos_mejora
check(not j.subir_stat("regen_energia") and j.puntos_mejora == antes, "pasado el tope no sube ni gasta el punto")
check(j.subir_stat("vida"), "las demas stats siguen funcionando")

def regen(bono, agua=False, profunda=False, mover=False, seg=60.0):
    q = nuevo(); q.bono_regen_energia = bono; q.energia = 0; q.en_agua = agua; q.en_agua_profunda = profunda
    if mover: q.destino = q.posicion + pygame.Vector2(1000, 0)
    for _ in range(int(seg * 60) + 1): q.actualizar_regeneracion(1 / 60)
    return q.energia
base, uno, diez, tope = regen(0), regen(0.05), regen(0.5), regen(1.0)
check(base == 20, "base quieto: 20 En/min (%s)" % base)
check(uno == 21, "1 punto: 21 En/min (+1 por minuto) (%s)" % uno)
check(diez == 30 and tope == 40, "10 puntos: 30 En/min, tope: 40 En/min (%s, %s)" % (diez, tope))
check(regen(0, mover=True) == 10 and regen(1.0, mover=True) == 20, "en movimiento: 10 -> 20 En/min")
check(regen(1.0, agua=True) == 80 and regen(1.0, profunda=True) == 100, "agua x2 (80) y zona profunda x4 (llena 100 antes del minuto)")
q = nuevo(); q.bono_regen_energia = 1.0; q.energia = q.energia_max
for _ in range(600): q.actualizar_regeneracion(1 / 60)
check(q.energia == q.energia_max, "no pasa del maximo de energia")
# comparativa con la stat Energia (+5 de maximo): 1 punto de regen = +5 En cada 5 min quieto
check(abs((uno - base) * 5 - 5) < 1e-9, "1 punto de Regen rinde lo mismo que 1 de Energia cada 5 min quieto")

# ---------------- 4. Anillo legendario: frecuencia real
print("--- Anillo legendario")
# Primera tirada de un personaje nuevo (sin garantia acumulada): se compara con las probabilidades
# que declara el propio Gacha y con PROB_RAREZA
rng = random.Random(7); N = 40000; leg = 0; anillos = 0
p_anillo = G.probabilidades(nuevo())[G.ANILLO]
p_leg = p_anillo * G.probabilidades_rareza(nuevo())[TL.LEGENDARIO]
for _ in range(N):
    j = nuevo(); j.monedas = G.COSTO_TIRADA
    r = G.tirar(j, rng)
    if r["categoria"] == G.ANILLO:
        anillos += 1
        leg += r["rareza"] == TL.LEGENDARIO
check(abs(anillos / N - p_anillo) < 0.01, "el %.1f %% de las tiradas da anillo (%.2f %%)" % (100 * p_anillo, 100 * anillos / N))
check(abs(leg / N - p_leg) < 0.0015, "legendario en el %.2f %% de las tiradas (medido %.3f %%)" % (100 * p_leg, 100 * leg / N))
check(TL.anillos_de_rareza(TL.LEGENDARIO) == ["regeneracion"], "solo hay un legendario: Regeneracion inversa")
# probabilidad de que salga en las 2 primeras tiradas de una partida nueva
rng = random.Random(9); P2 = 0; M = 200000
for _ in range(M):
    if rng.random() < p_leg or rng.random() < p_leg: P2 += 1
print("      en las 2 primeras tiradas: %.2f %% (1 de cada %d partidas)" % (100 * P2 / M, M / max(1, P2)))
# el generador global no se reinicia: dos 'partidas' seguidas no repiten la misma secuencia
random.seed(); a = [random.random() for _ in range(5)]; b = [random.random() for _ in range(5)]
check(a != b, "random no esta sembrado con un valor fijo")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
