# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas del Gacha rediseñado (fase 1 + hueco de potenciadas). Uso: python -B test_gacha_v2.py <proyecto>
import os, sys, random, statistics as st, collections
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import gacha as G, talismanes as TL, herramientas, habilidades
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)

def nuevo(nivel=1):
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [habilidades.crear_habilidad("Cortar")],
                  herramientas.crear_herramienta("Espada Larga"), 0)
    for _ in range(nivel - 1): j.subir_nivel()
    return j
def todas_herr(j):
    for n in j.herramientas_faltantes(): j.agregar_herramienta(n)
def todas_hab(j):
    for n in j.habilidades_faltantes(): j.agregar_habilidad(n)
def anillos_max(j):
    for a, d in TL.ANILLOS.items(): j.talismanes.anillos[a] = d["nivel_max"]
def r(p): return {k: round(v * 100, 1) for k, v in p.items()}

# ---------------- 1. Constantes
print("--- constantes")
check(G.COSTO_TIRADA == 15 and G.COSTO_TIRADA_MEJORADO == 20 and G.DEVOLUCION == 10, "tirada 15, mejorada 20, devolución 10")
check(G.costo_tirada(nuevo(19)) == 15 and G.costo_tirada(nuevo(20)) == 20 and not G.gacha_mejorado(nuevo(19)) and G.gacha_mejorado(nuevo(20)), "el Gacha mejorado (20) se habilita al nivel 20")
j = nuevo(20); j.monedas = 19; check(G.tirar(j) is None, "a nivel 20 con 19 monedas no alcanza")
j = nuevo(); j.monedas = 15; G.tirar(j, random.Random(1)); check(j.monedas in (0, 10), "a nivel 1 cobra 15 (%d)" % j.monedas)
check(G.PROB_NADA == 0.15 and G.PROB_AGOTADA == 0.05 and G.GARANTIA_LEGENDARIO == 90, "nada 15 %, agotada 5 %, garantía a las 90")

# ---------------- 2. Tablas de probabilidad (regla proporcional)
print("--- probabilidades")
H, A, N, T, P, Z = G.HERRAMIENTA, G.HABILIDAD, G.ANILLO, G.TOTEM, G.POTENCIADA, G.NADA
def caso(nombre, j, esperado):
    p = r(G.probabilidades(j))
    ok = all(abs(p.get(k, 0) - v) < 0.06 for k, v in esperado.items()) and set(p) == set(esperado)
    check(ok and abs(sum(G.probabilidades(j).values()) - 1) < 1e-9, "%-34s %s" % (nombre, p))
caso("normal", nuevo(), {H: 22, A: 13, N: 41, T: 9, Z: 15})
j = nuevo(); todas_herr(j); caso("todas las herramientas", j, {H: 5, A: 16.5, N: 52.1, T: 11.4, Z: 15})
j = nuevo(); todas_hab(j); caso("todas las habilidades", j, {H: 24.4, A: 5, N: 45.6, T: 10, Z: 15})
j = nuevo(); todas_herr(j); todas_hab(j); caso("herramientas + habilidades", j, {H: 5, A: 5, N: 61.5, T: 13.5, Z: 15})
j = nuevo(); j.talismanes.totems = 5; caso("5 tótems", j, {H: 23.2, A: 13.7, N: 43.2, T: 5, Z: 15})
j = nuevo(); todas_herr(j); todas_hab(j); j.talismanes.totems = 5; caso("herr + hab + 5 tótems", j, {H: 5, A: 5, N: 70, T: 5, Z: 15})
j = nuevo(20); todas_herr(j); todas_hab(j); j.talismanes.totems = 5
caso("nv20: potenciada en lugar de habilidad", j, {H: 5, P: 24.6, N: 50.4, T: 5, Z: 15})
# Cortar tiene potenciada (Desmantelar) desde el 26/11: la categoria potenciada esta libre
j = nuevo(20); caso("nv20 con Cortar (Desmantelar libre)", j, {H: 85 * 22 / 105, A: 85 * 13 / 105, N: 85 * 41 / 105, T: 85 * 9 / 105, P: 85 * 20 / 105, Z: 15})
j = nuevo(20); j.agregar_habilidad("Destello"); caso("nv20 con Destello (Relámpago disponible)", j, {H: 22 * 85 / 105, A: 13 * 85 / 105, N: 41 * 85 / 105, T: 9 * 85 / 105, P: 20 * 85 / 105, Z: 15})
j = nuevo(20); todas_herr(j); todas_hab(j); j.talismanes.totems = 5; [j.potenciar_habilidad(h.nombre) for h in j.coleccion_habilidades]
caso("nv20 con todas potenciadas", j, {H: 5, P: 5, N: 70, T: 5, Z: 15})
j = nuevo(19); todas_hab(j); check(G.POTENCIADA not in G.probabilidades(j), "a nivel 19 no hay potenciadas")
j = nuevo(20); todas_herr(j); todas_hab(j); j.talismanes.totems = 5; anillos_max(j); [j.potenciar_habilidad(h.nombre) for h in j.coleccion_habilidades]
caso("todo conseguido (nada que ganar)", j, {H: 21.25, P: 21.25, N: 21.25, T: 21.25, Z: 15})

# ---------------- 3. Anillos: solo los que pueden subir, rareza redistribuida
print("--- anillos")
j = nuevo()
for a, d in TL.ANILLOS.items():
    if d["rareza"] == TL.COMUN: j.talismanes.anillos[a] = d["nivel_max"]
rz = r(G.probabilidades_rareza(j))
check(TL.COMUN not in rz and abs(rz[TL.ESPECIAL] - 75) < 0.1 and abs(rz[TL.EPICO] - 22.5) < 0.1 and abs(rz[TL.LEGENDARIO] - 2.5) < 0.1,
      "comunes al máximo: la rareza común pasa a las demás %s" % rz)
rng = random.Random(1); sal = collections.Counter()
for _ in range(3000):
    j.talismanes.anillos.pop("vida", None); res = {}
    G._dar_anillo(j, rng, res := G._nuevo_resultado(G.ANILLO)); sal[res["id"]] += 1
    j.talismanes.anillos = {a: (d["nivel_max"] if d["rareza"] == TL.COMUN else 0) for a, d in TL.ANILLOS.items()}
check(not any(TL.ANILLOS[a]["rareza"] == TL.COMUN for a in sal), "nunca sale un anillo que ya está al máximo")
j = nuevo(); anillos_max(j); j.monedas = 0
res = G.tirar_anillo(j)
check(res["agotada"] and j.monedas == 10, "orbe del oso con todos al máximo: +10 monedas")

# ---------------- 4. Garantía del legendario
print("--- garantía de legendario")
rng = random.Random(3)
def tiradas_hasta_legendario(j, rng):
    n = 0
    while True:
        j.monedas = G.costo_tirada(j); n += 1
        res = G.tirar(j, rng)
        if res.get("rareza") == TL.LEGENDARIO:
            return n, res["garantia"]
muestras = []
for k in range(4000):
    j = nuevo(); muestras.append(tiradas_hasta_legendario(j, rng))
ns = [m[0] for m in muestras]
check(max(ns) == 90, "nunca hacen falta más de 90 tiradas (máx. %d)" % max(ns))
por_suerte = sum(1 for n, g in muestras if not g)
check(all(g == (n == 90) for n, g in muestras), "solo la tirada 90 se marca como garantizada")
print("      tiradas hasta el 1er legendario: media %.1f, mediana %d | por suerte antes de la 90: %.1f %%"
      % (st.mean(ns), st.median(ns), 100 * por_suerte / len(ns)))
j = nuevo(); rng = random.Random(5)
n1, _ = tiradas_hasta_legendario(j, rng)
check(j.tiradas_sin_legendario == 0, "al salir el legendario la cuenta vuelve a 0")
n2, g2 = tiradas_hasta_legendario(j, rng)
check(n2 <= 90, "el segundo legendario también está garantizado en 90 (%d)" % n2)
j = nuevo(); j.tiradas_sin_legendario = 50
while True:
    res = G.tirar_anillo(j, random.Random(len(j.talismanes.anillos)))
    if res.get("rareza") == TL.LEGENDARIO or j.tiradas_sin_legendario != 50: break
check(j.tiradas_sin_legendario in (0, 50), "el orbe del oso no suma a la garantía y la reinicia si da legendario")
j = nuevo(); j.talismanes.anillos["regeneracion"] = TL.ANILLOS["regeneracion"]["nivel_max"]; j.tiradas_sin_legendario = 89; j.monedas = 15
res = G.tirar(j, random.Random(0))
check(not res["garantia"], "con el legendario al máximo no hay garantía (tirada normal)")

# ---------------- 5. Frecuencias reales = tabla
print("--- frecuencias medidas (100 000 tiradas por caso)")
for nombre, prep in (("normal", lambda j: None), ("herr+hab", lambda j: (todas_herr(j), todas_hab(j)))):
    j = nuevo(); prep(j); esperado = G.probabilidades(j)
    rng = random.Random(11); cnt = collections.Counter()
    for _ in range(100000):
        snap = (dict(j.talismanes.anillos), j.talismanes.totems, list(j.coleccion_herramientas), list(j.coleccion_habilidades))
        j.monedas = G.costo_tirada(j); j.tiradas_sin_legendario = 0
        res = G.tirar(j, rng)
        cnt[G.NADA if res["categoria"] == G.NADA else res["categoria"]] += 1
        j.talismanes.anillos, j.talismanes.totems = snap[0], snap[1]
        j.coleccion_herramientas, j.coleccion_habilidades = snap[2], snap[3]
    med = {k: round(100 * v / 100000, 1) for k, v in cnt.items()}
    check(all(abs(med.get(k, 0) - 100 * p) < 0.5 for k, p in esperado.items()), "%-9s esperado %s | medido %s" % (nombre, r(esperado), med))

# ---------------- 6. Sin monedas infinitas
print("--- economía")
j = nuevo(20); todas_herr(j); todas_hab(j); j.talismanes.totems = 5; anillos_max(j)
[j.potenciar_habilidad(h.nombre) for h in j.coleccion_habilidades]
j.monedas = 10 ** 6; rng = random.Random(2)
for _ in range(20000): G.tirar(j, rng)
neto = (j.monedas - 10 ** 6) / 20000
check(-12 < neto < -11, "con todo conseguido (Gacha mejorado, 20) cada tirada pierde %.2f monedas (20 - 0.85 x 10 = 11.5)" % neto)
j = nuevo(20); todas_hab(j); rng = random.Random(4); j.monedas = 10 ** 6
for _ in range(400): G.tirar(j, rng)
disenadas = {h.nombre for h in j.coleccion_habilidades if h.tiene_potenciada}
check(j.habilidades_potenciadas == disenadas, "a nivel 20 se consiguen todas las potenciadas disenadas (%s)" % sorted(j.habilidades_potenciadas))

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
