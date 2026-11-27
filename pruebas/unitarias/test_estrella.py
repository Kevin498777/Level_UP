# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Carga de Fuego -> Estrella Ignea (cuarta potenciada). Uso: python -B test_estrella.py <proyecto>
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import habilidades as H, gacha as G, herramientas, fauna as F, mundo, vegetacion as V
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug(nv=20, pot=True):
    h = H.crear_habilidad("Carga de Fuego"); h.asignar_tecla(pygame.K_2, "2")
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [h], herramientas.crear_herramienta("Espada Larga"), 0)
    for _ in range(19): j.subir_nivel()
    j.puntos_mejora = 500; j.energia = j.energia_max = 1000; j.angulo = 90.0
    if pot: j.potenciar_habilidad("Carga de Fuego")
    while h.nivel < nv:
        c = h.costo_mejora; assert h.subir_nivel(); j.puntos_mejora -= c
    return j, h
def cargar(j, h, segundos):
    h.iniciar_carga(j)
    for _ in range(int(segundos * 60) + 2): h.actualizar(1 / 60, j)
    h.soltar_carga(j)
    return j.proyectiles[-1]

print("--- Carga de Fuego normal (sin cambios)")
j, h = jug(20, pot=False)
check(h.dano_base == 39 and h.tiempo_max_carga == 5 and h.nivel_max == 20, "nv20: base 39, carga máx 5 s, nivel máx 20")
e0 = j.energia; p = cargar(j, h, 7)
check(p.dano == 78 and p.radio == 22 and p.quemadura_duracion == 7 and e0 - j.energia == 45 and h.duracion_cooldown == 15 and p.al_impactar is None,
      "aunque mantengas 7 s se queda en 5 s: 78 de daño, 45 En., recarga 15 s, sin explosión")

print("--- Estrella Ígnea: escalado por carga (nv30, base 49)")
esperado = {0: (29.4, 3, 15, 8.0, 6), 1: (39.2, 4, 20, 9.4, 8), 2: (49, 5, 25, 10.8, 11), 5: (98, 8, 45, 15.0, 22),
            6: (107.8, 9, 53, 16.4, 25), 7: (117.6, 10, 62, 17.8, 28), 8: (127.4, 11, 70, 19.2, 32)}
for s, (dano, quem, costo, cd, radio) in esperado.items():
    j, h = jug(30)
    e0 = j.energia; p = cargar(j, h, s) if s else (h.iniciar_carga(j), h.soltar_carga(j), j.proyectiles[-1])[2]
    check(abs(p.dano - dano) < 1e-6 and p.quemadura_duracion == quem and e0 - j.energia == costo and abs(h.duracion_cooldown - cd) < 1e-6 and p.radio == radio,
          "carga %s: daño %g, quemadura %d s, coste %d, recarga %g s, radio %d" % ("toque" if s == 0 else "%d s" % s, dano, quem, costo, cd, radio))
j, h = jug(30); p = cargar(j, h, 12)
check(p.dano == 127.4 and h.tier_max == 8, "la carga se detiene en 8 s")
j, h = jug(21)
check(h.dano_base == 40 and h.nombre_mostrado == "Estrella Ígnea", "nv21: base 40 y se llama Estrella Ígnea")

print("--- explosión")
def escenario():
    j, h = jug(30)
    lobo_imp = F.LoboSolitario(200, 0); lobo_imp.vida = lobo_imp.vida_max = 500
    lobo_cerca = F.LoboSolitario(260, 0); lobo_cerca.vida = lobo_cerca.vida_max = 500
    lobo_lejos = F.LoboSolitario(400, 0); lobo_lejos.vida = lobo_lejos.vida_max = 500
    return j, h, [lobo_imp, lobo_cerca, lobo_lejos]
j, h, (a, b, c) = escenario()
p = cargar(j, h, 5)                              # 98 de daño
p.posicion = pygame.Vector2(200, 0)
a.recibir_dano(p.dano, "magico"); p.impactar()   # el mundo hace esto al tocar al enemigo
check(len(h.explosiones) == 1 and not p.activo, "al tocar al enemigo la esfera se apaga y programa la explosión")
v = [x.vida for x in (a, b, c)]
for _ in range(20): h.actualizar_explosiones(1 / 60, j, [a, b, c], [], [], [], [])
check([x.vida for x in (a, b, c)] == v, "a los 0.33 s todavía no explota")
for _ in range(12): h.actualizar_explosiones(1 / 60, j, [a, b, c], [], [], [], [])
check(abs((v[0] - a.vida) - 29.4) < 1e-6 and abs((v[1] - b.vida) - 29.4) < 1e-6 and c.vida == v[2],
      "a los 0.5 s explota: 29.4 (30 %% de 98) al impactado y al de al lado; nada al lejano")
vj = j.vida; j.posicion = pygame.Vector2(210, 0)
j2, h2, _ = escenario(); h2.programar_explosion(pygame.Vector2(0, 0), 100)
for _ in range(40): h2.actualizar_explosiones(1 / 60, j2, [], [], [], [], [])
check(j2.vida == j2.vida_max, "la explosión no daña al jugador")

print("--- suelo en llamas")
j, h, (a, b, c) = escenario()
h.programar_explosion(pygame.Vector2(200, 0), 0)    # sin daño de explosión, solo suelo
for _ in range(31): h.actualizar_explosiones(1 / 60, j, [a, b, c], [], [], [], [])
v = [x.vida for x in (a, b, c)]
h.programar_explosion(pygame.Vector2(210, 0), 0)    # segunda zona superpuesta
for _ in range(31): h.actualizar_explosiones(1 / 60, j, [a, b, c], [], [], [], [])
v = [x.vida for x in (a, b, c)]
for _ in range(5 * 60): h.actualizar_explosiones(1 / 60, j, [a, b, c], [], [], [], [])
check(abs((v[0] - a.vida) - 5) <= 1 and c.vida == v[2], "dentro: 1 de daño por segundo aunque haya 2 zonas (%g en 5 s); fuera nada" % (v[0] - a.vida))
a.escudo = 50; vida0 = a.vida
for _ in range(2 * 60): h.actualizar_explosiones(1 / 60, j, [a], [], [], [], [])
check(a.vida < vida0 and a.escudo == 50, "el suelo ignora escudos")
for _ in range(10 * 60): h.actualizar_explosiones(1 / 60, j, [a], [], [], [], [])
check(not h.zonas_fuego, "el suelo se apaga a los 10 s")

print("--- destrucción de obstáculos")
class Roca:
    def __init__(self, x, y, lado, gigante=False, cueva=False):
        self.rect = pygame.Rect(0, 0, lado, lado); self.rect.center = (x, y); self.gigante = gigante
        if cueva: self.es_cueva = True
class Arbol:
    def __init__(self, x, y): self.centro = pygame.Vector2(x, y); self.radio_tronco = 8; self.radio_copa = 40
class Arbusto:
    def __init__(self, x, y, r): self.centro = pygame.Vector2(x, y); self.circulos = [(pygame.Vector2(x, y), r)]
    def contiene(self, p): return (p - self.centro).length() <= self.circulos[0][1]
j, h = jug(30); j.posicion = pygame.Vector2(-500, 0)
roca_c, roca_l = Roca(150, 0, 40), Roca(400, 0, 40)
gig, cueva = Roca(0, 120, 200, gigante=True), Roca(80, -60, 60, cueva=True)
rocas = [roca_c, roca_l, gig, cueva]
arboles = [Arbol(50, 50), Arbol(300, 0)]
esc = Arbusto(-500, 0, 40)
arbustos = [Arbusto(60, -40, 30), Arbusto(500, 0, 30), esc]
h.programar_explosion(pygame.Vector2(80, 0), 50)
for _ in range(31):
    d, ev = h.actualizar_explosiones(1 / 60, j, [], rocas, arbustos, arboles, [])
    if d: destruidos = d
check(roca_c not in rocas and roca_l in rocas, "destruye las rocas dentro del radio y no las de fuera")
check(gig in rocas and cueva in rocas, "no destruye rocas gigantes ni cuevas de oso")
check(len(arboles) == 1 and len(arbustos) == 2 and esc in arbustos, "destruye árboles y arbustos dentro; no el arbusto donde estás escondido")
j, h = jug(30); j.posicion = pygame.Vector2(-40, 0)
esc2 = Arbusto(-40, 0, 60); arbs = [esc2]
h.programar_explosion(pygame.Vector2(0, 0), 50)
for _ in range(31): h.actualizar_explosiones(1 / 60, j, [], [], arbs, [], [])
check(esc2 in arbs, "aunque la explosión toque tu arbusto, no lo quema mientras estás dentro")
# Cortar a nivel 20 tampoco rompe la cueva
cort = H.crear_habilidad("Cortar")
while cort.subir_nivel(): pass
cu = H.CuchillaCortante(0, 0, 1, 0, 10, 5, True)
rs = [Roca(30, 0, 40, gigante=True, cueva=True)]
for _ in range(10): cu.avanzar(rs, [], [], [], pygame.Vector2(0, 0), 10 ** 6)
check(len(rs) == 1 and not cu.activo, "Cortar a nivel 20 se rompe contra la cueva sin destruirla")

print("--- la esfera choca con troncos y arbustos")
j, h = jug(30); p = cargar(j, h, 0)
p.posicion = pygame.Vector2(300, 0)
h.actualizar_explosiones(1 / 60, j, [], [], [], [Arbol(305, 0)], [])
check(not p.activo and len(h.explosiones) == 1, "al tocar un tronco explota")
j, h = jug(20, pot=False); p = cargar(j, h, 0)
check(p.al_impactar is None, "la Carga de Fuego normal no explota")

print("--- agua evaporada")
random.seed(3)
lago = mundo.Charco(1000, 1000, 400)
punto_agua = next(c for c, r in lago.circulos if (c - lago.centro).length() > 50)
check(lago.contiene(punto_agua) and lago.en_zona_peligro(lago.centro), "antes: agua y zona profunda")
j, h = jug(30); h.programar_explosion(pygame.Vector2(punto_agua), 30)
for _ in range(31): d, ev = h.actualizar_explosiones(1 / 60, j, [], [], [], [], [lago]) if True else None
check(not lago.contiene(punto_agua), "el círculo de la explosión deja de ser agua")
lejos = next((pygame.Vector2(c) for c, r in lago.circulos if (c - punto_agua).length() > 250), None)
check(lejos is None or lago.contiene(lejos), "el resto del lago sigue siendo agua")
h.programar_explosion(pygame.Vector2(lago.centro), 30)
for _ in range(31): h.actualizar_explosiones(1 / 60, j, [], [], [], [], [lago])
check(not lago.en_zona_peligro(lago.centro), "evaporar el centro reduce la zona profunda")
class FaunaFalsa:
    pass
sf = F.SistemaFauna.__new__(F.SistemaFauna)
sf.peces = [F.Pez(lago), F.Pez(lago)]; sf.ranas = []
sf.peces[0].centro = pygame.Vector2(lago.centro); sf.peces[1].centro = pygame.Vector2(lago.centro) + pygame.Vector2(300, 0)
sf.quitar_fauna_acuatica(pygame.Vector2(lago.centro), 100)
check(len(sf.peces) == 1, "los peces del círculo evaporado desaparecen")

print("--- Gacha")
check("Carga de Fuego" in G.potenciadas_disponibles(jug(20, pot=False)[0]), "Estrella Ígnea entra en el Gacha mejorado")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
