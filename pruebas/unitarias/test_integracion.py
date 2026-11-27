# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas headless de los puntos donde se cruzan master y feature/fauna.
import os, sys, random, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY = sys.argv[1]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
random.seed(3)

import mundo, fauna, vegetacion, habilidades, herramientas
from personaje import Personaje, AUTOAPUNTADO_RANGO

fallos = []
def check(cond, msg):
    print(("OK   " if cond else "FALLO"), msg)
    if not cond:
        fallos.append(msg)

def jugador(herr="Escudo"):
    j = Personaje("T", 5000, 5000, 1.0, 6, 100, 10, 100, 10, (0, 0, 255), [], herramientas.crear_herramienta(herr), 10)
    j.posicion = pygame.Vector2(5000, 5000); j.destino = pygame.Vector2(j.posicion)
    j.angulo = 90.0          # mirando a la derecha (+x)
    return j

# --- Mundo real generado (lagos, vegetacion, rocas, fauna) ---
charcos = mundo.generar_charcos() if hasattr(mundo, "generar_charcos") else None
src = open("mundo.py", encoding="utf-8").read()
idx = src.index("def iniciar_mundo")
# reconstruir la generacion tal como iniciar_mundo
bloque = [l.strip() for l in src[idx:].splitlines()[:40] if "charcos =" in l or "vegetacion =" in l or "rocas =" in l]
print("generacion:", bloque)
ns = dict(vars(mundo))
for l in bloque:
    exec(l, ns)
veg, charcos, rocas = ns["vegetacion"], ns["charcos"], ns["rocas"]
veg.registrar_obstaculos(rocas)
sf = fauna.SistemaFauna(mundo.CENTRO_MUNDO, mundo.RADIO_MUNDO, veg, charcos, rocas)

# 1. Pasto (incluido el alto de fauna) fuera de los lagos
en_agua = sum(1 for g in veg.pasto if veg._en_agua(g.centro.x, g.centro.y, 0))
check(en_agua == 0, "pasto/pasto alto fuera de lagos (en agua: %d de %d)" % (en_agua, len(veg.pasto)))
check(len(veg.pastizales) > 0, "existen pastizales (bioma de pasto alto) tras la union")

# 2. Escudo bloquea mordida de lobo frontal; por la espalda si dana
lobo = sf.manadas[0].lobos[0]
j = jugador("Escudo"); j.herramienta.activa = True
lobo.posicion = j.posicion + pygame.Vector2(30, 0); lobo._cd_mordida = 0
vida0, dur0, pos_lobo0 = j.vida, j.herramienta.durabilidad, pygame.Vector2(lobo.posicion)
lobo._morder(j)
check(j.vida == vida0 and j.escudo == j.escudo_max, "lobo de frente: escudo bloquea (sin dano)")
check(j.herramienta.durabilidad < dur0, "lobo de frente: el escudo se desgasta")
check((lobo.posicion - j.posicion).length() > (pos_lobo0 - j.posicion).length(), "lobo de frente: repelido por el escudo")
lobo.posicion = j.posicion + pygame.Vector2(-30, 0); lobo._cd_mordida = 0
v1, e1 = j.vida, j.escudo
lobo._morder(j)
check(j.vida + j.escudo < v1 + e1, "lobo por la espalda: si hace dano")
j2 = jugador("Espada Ligera")
lobo.posicion = j2.posicion + pygame.Vector2(30, 0); lobo._cd_mordida = 0
v2 = j2.vida + j2.escudo; lobo._morder(j2)
check(j2.vida + j2.escudo < v2, "sin escudo: la mordida dana")
j3 = jugador("Escudo"); j3.herramienta.activa = False
lobo.posicion = j3.posicion + pygame.Vector2(30, 0); lobo._cd_mordida = 0
v3 = j3.vida + j3.escudo; lobo._morder(j3)
check(j3.vida + j3.escudo < v3, "escudo enfundado: la mordida dana")

# 3. Helper con los demas atacantes (jabali/oso/cocodrilo/zorro) no rompe con objetivos sin escudo
for a in (sf.jabalies[:1] + sf.osos[:1] + sf.cocodrilos[:1] + sf.zorros[:1]):
    j = jugador("Escudo"); j.herramienta.activa = True
    a.posicion = j.posicion + pygame.Vector2(30, 0)
    check(fauna.bloqueado_por_escudo(a, j, 10) is True, "%s de frente bloqueado" % type(a).__name__)
    conejo = sf.conejos[0]
    check(fauna.bloqueado_por_escudo(a, conejo, 10) is False, "%s contra conejo: no hay escudo" % type(a).__name__)

# 4. Autoapuntado suelta animales que dejan de estar al alcance
j = jugador("Espada Ligera")
casos = []
if sf.zorros: casos.append((sf.zorros[0], "invisible", False, True))
if sf.osos: casos.append((sf.osos[0], "estado", "deambula", "cueva"))
if sf.cocodrilos: casos.append((sf.cocodrilos[0], "estado", "ataca", "regresa"))
casos.append((sf.conejos[0], "estado", "deambula", "escondido"))
for a, attr, visible, val in casos:
    viejo = getattr(a, attr)
    setattr(a, attr, visible)
    a.vivo = True
    a.posicion = j.posicion + pygame.Vector2(100, 0)
    check(j.alternar_autoapuntado(a), "%s: autoapuntado se fija" % type(a).__name__)
    j.actualizar_autoapuntado(0.016)
    check(j.objetivo_apuntado is a, "%s: se mantiene visible" % type(a).__name__)
    setattr(a, attr, val)
    j.actualizar_autoapuntado(0.016)
    check(j.objetivo_apuntado is None, "%s: se suelta al quedar %s=%s" % (type(a).__name__, attr, val))
    setattr(a, attr, viejo)
check(getattr(mundo.Maniqui(mundo.CENTRO_MUNDO), "apuntable", True), "maniqui sigue siendo apuntable (sin atributo)")

# 5. Copas semitransparentes con un animal debajo
arbol = veg.arboles[0]
venado = sf.venados[0]; venado.posicion = pygame.Vector2(arbol.centro)
desv = any((e.posicion - arbol.centro).length() <= arbol.radio_copa + e.radio for e in [venado])
check(desv, "copa se desvanece con un venado debajo (tiene .radio)")
for a in sf.cuerpos_solidos(pygame.Rect(-10**6, -10**6, 2 * 10**6, 2 * 10**6)):
    assert hasattr(a, "posicion") and hasattr(a, "radio")
check(True, "todos los cuerpos solidos tienen posicion y radio")

# 6. Coste de la orden de ataque de lobos (fauna) con master
hl = habilidades.InvocacionLobos()
check(hl.costo_orden_ataque == 5, "orden de ataque lobos nv1 = 5")
while hl.subir_nivel(): pass
check(hl.costo_orden_ataque == 10 and hl.nivel == 20, "orden de ataque lobos nv20 = 10")

# 7. Disparo Veloz (dano fijo de master) dana a un animal de la fauna
dv = habilidades.DisparoVeloz()
v = sf.venados[1]; v.vivo = True; vida = v.vida
v.recibir_dano(dv.dano, "magico", pygame.Vector2(1, 0))
check(abs((vida - v.vida) - min(vida, dv.dano)) < 1e-6, "Disparo Veloz nv1 quita %.1f a un venado" % dv.dano)

# 8. Muchos frames de simulacion de fauna sin errores con el jugador real
j = jugador("Escudo"); j.herramienta.activa = True
vista = pygame.Rect(0, 0, 1600, 900)
for i in range(3000):
    if i % 300 == 0:
        objs = fauna_objs = sf.animales_con_vida(pygame.Rect(-10**6, -10**6, 2 * 10**6, 2 * 10**6))
        if objs:
            j.posicion = pygame.Vector2(random.choice(objs).posicion) + pygame.Vector2(40, 0)
    vista.center = (round(j.posicion.x), round(j.posicion.y))
    sf.actualizar(1 / 60, j, vista)
    j.actualizar_autoapuntado(1 / 60)
check(True, "3000 frames de fauna con jugador con escudo sin excepciones")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
