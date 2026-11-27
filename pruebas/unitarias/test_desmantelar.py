# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
from limite_mundo import LimiteMundo
pygame.init()
pygame.display.set_mode((10, 10))
import habilidades as H
from habilidades import (Cortar, CargaDeFuego, CuchillaCortante, SistemaCombustible, encender_combustible,
                         aplicar_quemadura, ProyectilFuego, resumen_habilidad)
from personaje import Personaje
from fauna import LoboSolitario
import gacha

fallos = []
def ok(c, m):
    if not c:
        fallos.append(m); print("FALLO:", m)

def cortar(n, pot=False):
    h = Cortar()
    if pot: h.desbloquear_potenciada()
    while h.nivel < n: assert h.subir_nivel()
    return h

def jug(habs, energia=200):
    j = Personaje("t", 0, 0, 1, 2, 30, 1, energia, 0, (255, 255, 255), habilidades=habs)
    return j

class Roca:
    def __init__(self, x, y, gigante=False, cueva=False):
        self.rect = pygame.Rect(x - 10, y - 10, 20, 20); self.gigante = gigante; self.es_cueva = cueva
class Arbol:
    def __init__(self, x, y):
        self.centro = pygame.Vector2(x, y); self.radio_copa = 20; self.radio_tronco = 6
class Charco:
    def __init__(self, x, y, r): self.c = pygame.Vector2(x, y); self.r = r
    def contiene(self, p): return (p - self.c).length() <= self.r

def lobo(x, y):
    l = LoboSolitario(x, y); l.vida = 1000; l.escudo_magico = 0
    return l

def correr_cuchillas(h, rocas, arbustos, arboles, enemigos, seg=3):
    destruidos = []
    for _ in range(int(seg * 60)):
        destruidos += h.actualizar_cuchillas(rocas, arbustos, arboles, enemigos, LimiteMundo(10 ** 7, centro=(0, 0)))
    return destruidos

# 1. Escalado Cortar
for n, d in ((1, 2), (5, 10), (10, 20), (19, 38), (20, 40)):
    h = cortar(n); ok(h.dano == d, f"dano nv{n} {h.dano}")
h = cortar(20); ok((h.velocidad_cuchilla, h.costo_energia, h.duracion_cooldown) == (24, 53, 10.0), "nv20 base")
# 2. Desmantelar
tabla = {20: (24, 60, 10, 1, 1), 22: (26, 70, 12, 2, 2), 24: (28, 80, 14, 4, 3), 26: (30, 90, 16, 6, 4), 28: (32, 100, 18, 8, 6), 30: (35, 120, 20, 10, 8)}
for n, (v, c, cd, comb, nc) in tabla.items():
    h = cortar(n, True)
    ok((h.velocidad_cuchilla, h.costo_energia, h.duracion_cooldown, h.duracion_combustible, len(h.direcciones), h.dano)
       == (v, c, cd, comb, nc, 40), f"desm nv{n}: {(h.velocidad_cuchilla, h.costo_energia, h.duracion_cooldown, h.duracion_combustible, len(h.direcciones))}")
h = cortar(21, True); ok((h.velocidad_cuchilla, h.costo_energia, h.duracion_combustible, len(h.direcciones)) == (25, 65, 1.5, 1), "nv21 lineal")
h = cortar(29, True); ok(len(h.direcciones) == 6 and h.costo_energia == 110, "nv29")
h = cortar(20); h.desbloquear_potenciada(); ok(h.costo_energia == 60 and h.nombre_mostrado == "Desmantelar", "desbloquear en nv20 recalcula")
ok(cortar(19, True).costo_energia == 51, "por debajo de 20 sigue normal")

# 3. Direcciones (norte = frente)
h = cortar(30, True); j = jug([h], 300); j.angulo = 90   # mira a la derecha
h.intentar_activar(j)
dirs = sorted((round(c.direccion.x, 2), round(c.direccion.y, 2)) for c in h.cuchillas)
ok(len(h.cuchillas) == 8 and (1.0, 0.0) in dirs and (-1.0, 0.0) in dirs and (0.0, 1.0) in dirs, f"8 direcciones: {dirs}")
h = cortar(24, True); j = jug([h], 300); j.angulo = 0; h.intentar_activar(j)
d3 = {(round(c.direccion.x, 2), round(c.direccion.y, 2)) for c in h.cuchillas}
ok(d3 == {(0.0, -1.0), (0.0, 1.0), (1.0, 0.0)}, f"n,s,e: {d3}")

# 4. Alcance 600 -> combustible en el suelo
h = cortar(20, True); j = jug([h]); j.angulo = 0; h.intentar_activar(j)
correr_cuchillas(h, [], [], [], [])
s = j.combustible.sueltos
ok(not h.cuchillas and len(s) == 1 and abs(s[0][0].y + 600) < 30, f"combustible a 600 px: {[x[0] for x in s]}")

# 5. Atraviesa 3 objetos y se rompe en el tercero dejando carga
h = cortar(20, True); j = jug([h]); j.angulo = 0; h.intentar_activar(j)
rocas = [Roca(0, -100, gigante=True), Roca(0, -200)]; arboles = [Arbol(0, -300), Arbol(0, -400)]
dest = correr_cuchillas(h, rocas, [], arboles, [])
ok(len(dest) == 3 and len(arboles) == 1 and not rocas, f"3 objetos (incluida gigante y arbol): {len(dest)}")
ok(len(j.combustible.sueltos) == 1 and abs(j.combustible.sueltos[0][0].y + 300) < 40, "carga donde se rompio")
# cueva: se rompe sin destruir ni contar
h = cortar(20, True); j = jug([h]); j.angulo = 0; h.intentar_activar(j)
rocas = [Roca(0, -100, cueva=True)]
dest = correr_cuchillas(h, rocas, [], [], [])
ok(not dest and len(rocas) == 1 and len(j.combustible.sueltos) == 1, "cueva la rompe")
# Cortar normal: 1 objeto
h = cortar(10); j = jug([h]); j.angulo = 0; h.intentar_activar(j)
rocas = [Roca(0, -100), Roca(0, -200)]
dest = correr_cuchillas(h, rocas, [], [], [])
ok(len(dest) == 1 and len(rocas) == 1 and not j.combustible.sueltos, "Cortar normal: 1 objeto, sin combustible")
h = cortar(10); j = jug([h]); j.angulo = 0; h.intentar_activar(j)
rocas = [Roca(0, -100, gigante=True)]
ok(not correr_cuchillas(h, rocas, [], [], []) and rocas, "Cortar <20 no rompe gigante")

# 6. Golpea enemigo: se para, dano, anula escudo, carga pegada
h = cortar(30, True); j = jug([h], 300); j.angulo = 0; h.intentar_activar(j)
e = lobo(0, -150); e2 = lobo(0, -250)
correr_cuchillas(h, [], [], [], [e, e2])
ok(e.vida == 960 and e2.vida == 1000, f"se detiene en el primero: {e.vida} {e2.vida}")
ok(len(e.combustible_pegado) == 1 and e in j.combustible.portadores, "carga pegada")
ok(e.combustible_pegado[0] == 10, "con el tiempo del nivel")

# 7. Explosion por golpe de fuego: +50 % por carga
S = j.combustible
S.pegar(e, 10); S.pegar(e, 10); S.pegar(e, 10)
ok(len(e.combustible_pegado) == 3, "max 3")
v = e.vida
d = encender_combustible(e, 127.4)
ok(abs(d - 191.1) < 0.2 and abs(e.vida - (v - 191.1)) < 0.2 and not e.combustible_pegado, f"3 cargas: +150 % = {d}")
otro = lobo(50, -150)
S.actualizar(1 / 60, j, [e, otro], [])
ok(otro.vida == 980 and len(S.zonas) == 1, f"explosion de area 20 a otros y suelo: {otro.vida}")
ok(e.vida > v - 191.1 - 1, "el portador no recibe el 20 extra")

# 8. Quemadura (tick) -> fijo 20 y cadenas acotadas
e = lobo(0, 0); f = lobo(60, 0); S = SistemaCombustible()
S.pegar(e, 10); S.pegar(f, 10)
aplicar_quemadura(e, 1, 5.0)
for _ in range(61): e.quemadura.actualizar(1 / 60, e)
ok(e.vida == 1000 - 1 - 20 and not e.combustible_pegado, f"tick de quemadura: {e.vida}")
S.actualizar(1 / 60, jug([]), [e, f], [])
ok(f.vida == 1000 - 20 - 20 and not f.combustible_pegado, f"cadena: f recibe 20 y su carga explota fija: {f.vida}")
S.actualizar(1 / 60, jug([]), [e, f], [])
ok(len(S.zonas) == 2 and not S.pendientes, "cadena termina")

# 9. Suelo en llamas: tick 1 y explota carga (fijo)
e = lobo(0, 0); S = SistemaCombustible(); S.zonas.append([pygame.Vector2(0, 0), 5.0]); S.pegar(e, 10)
for _ in range(61): S.actualizar(1 / 60, jug([]), [e], [])
ok(e.vida == 1000 - 1 - 20, f"suelo en llamas prende la carga: {e.vida}")

# 10. Suelto: prende por esfera de fuego, explota a los 2 s aunque su tiempo sea menor
S = SistemaCombustible(); j = jug([]); j.combustible = S
S.soltar(pygame.Vector2(0, -100), 1.0)
p = ProyectilFuego(0, -100, 0, -1, 0, 10, 6); j.proyectiles = [p]
S.actualizar(1 / 60, j, [], []); j.proyectiles = []
ok(S.sueltos[0][3] is not None, "prendido por esfera")
e = lobo(50, -100)
for _ in range(int(1.9 * 60)): S.actualizar(1 / 60, j, [e], [])
ok(S.sueltos and e.vida == 1000, "aun no explota (y no se pega estando prendido)")
for _ in range(10): S.actualizar(1 / 60, j, [e], [])
ok(not S.sueltos and e.vida == 980, f"explota a los 2 s: {e.vida}")
# expira sin fuego
S = SistemaCombustible(); S.soltar(pygame.Vector2(0, 0), 1.0)
for _ in range(62): S.actualizar(1 / 60, j, [], [])
ok(not S.sueltos, "expira")
# pisado: se pega con tiempo nuevo
S = SistemaCombustible(); S.soltar(pygame.Vector2(0, 0), 6.0)
for _ in range(60): S.actualizar(1 / 60, j, [], [])
e = lobo(1000, 0); S.actualizar(1 / 60, j, [e], [])
e.posicion = pygame.Vector2(0, 0); S.actualizar(1 / 60, j, [e], [])
ok(not S.sueltos and len(e.combustible_pegado) == 1 and e.combustible_pegado[0] > 5.9, f"pisado se pega con tiempo desde 0: {e.combustible_pegado}")
# lago lo quita
S.actualizar(1 / 60, j, [e], [Charco(0, 0, 50)])
ok(not e.combustible_pegado and not S.portadores, "agua quita")
# tiempos independientes
e = lobo(0, 0); S = SistemaCombustible(); S.pegar(e, 2);
for _ in range(60): S.actualizar(1 / 60, j, [e], [])
S.pegar(e, 2)
for _ in range(61): S.actualizar(1 / 60, j, [e], [])
ok(len(e.combustible_pegado) == 1, f"tiempos independientes: {e.combustible_pegado}")
# muerte quita
e.vivo = False; S.actualizar(1 / 60, j, [e], []); ok(not e.combustible_pegado, "muerto pierde cargas")

# 11. Estrella: explosion con golpe multiplicado y prende sueltos; jugador nunca recibe dano
cf = CargaDeFuego(); cf.desbloquear_potenciada()
while cf.nivel < 30: cf.subir_nivel()
j = jug([cf], 300); vida_j = j.vida
e = lobo(0, -50); j.combustible.pegar(e, 10); j.combustible.soltar(pygame.Vector2(30, -50), 10)
cf.programar_explosion(pygame.Vector2(0, -50), 100)
v = e.vida
for _ in range(40): cf.actualizar_explosiones(1 / 60, j, [e], [], [], [], [])
ok(abs(e.vida - (v - 30 - 15)) < 0.5, f"explosion 30 + carga 50% de 30: {v - e.vida}")
ok(j.combustible.sueltos[0][3] is not None, "explosion prende suelto")
for _ in range(200): j.combustible.actualizar(1 / 60, j, [e], [])
ok(j.vida == vida_j, "jugador sin dano")

# 12. Gacha, resumen, dibujo
j = jug([Cortar()]); j.coleccion_habilidades = list(j.habilidades)
ok("Cortar" in gacha.potenciadas_disponibles(j), "gacha")
ok("cuchilla" in resumen_habilidad(cortar(26, True)), resumen_habilidad(cortar(26, True)))
pant = pygame.Surface((400, 400))
S = SistemaCombustible(); S.soltar(pygame.Vector2(10, 10), 5); e = lobo(50, 50); S.pegar(e, 5)
S.zonas.append([pygame.Vector2(0, 0), 3]); S.destellos.append([pygame.Vector2(0, 0), 0.2])
S.dibujar(pant); S.dibujar_suelo(pant)
h = cortar(30, True); j = jug([h], 300); h.intentar_activar(j)
for _ in range(5): h.actualizar_cuchillas([], [], [], [], LimiteMundo(10 ** 7, centro=(0, 0)))
h.dibujar_cuchillas(pant, (-200, -200))
# reaparecer limpia
e = lobo(0, 0); j.combustible.pegar(e, 10); j.__init__("t", 0, 0, 1, 2, 30, 1, 100, 0, (1, 1, 1), habilidades=[])
ok(not e.combustible_pegado, "reaparecer limpia")
print("FALLOS:", len(fallos))
