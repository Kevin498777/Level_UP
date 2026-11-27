# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Disparo Veloz (ajuste) -> Rafaga Veloz (tercera potenciada). Uso: python -B test_rafaga.py <proyecto>
import os, sys, math, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import habilidades as H, gacha as G, herramientas
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug():
    h = H.crear_habilidad("Disparo Veloz"); h.asignar_tecla(pygame.K_2, "2")
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [h], herramientas.crear_herramienta("Espada Larga"), 0)
    for _ in range(19): j.subir_nivel()
    j.puntos_mejora = 500; j.energia = j.energia_max = 1000; j.angulo = 90.0   # mira a la derecha (+x)
    return j, h
def subir(j, h, nv):
    while h.nivel < nv:
        c = h.costo_mejora; assert h.subir_nivel(); j.puntos_mejora -= c

print("--- ajuste de Disparo Veloz (1-20)")
for nv, (vel, dano, costo, cd) in {1: (14, 8, 15, 4), 10: (23.9, 16.1, 25, 3.05), 20: (35, 25, 35, 2)}.items():
    j, h = jug(); subir(j, h, nv)
    check((h.velocidad_proyectil, h.dano, h.costo_energia, h.duracion_cooldown) == (vel, dano, costo, cd),
          "nv%d: velocidad %g, daño %g, coste %d, recarga %g s" % (nv, vel, dano, costo, cd))
j, h = jug(); subir(j, h, 20); h.intentar_activar(j)
check(len(j.proyectiles) == 1 and h.estado == "COOLDOWN" and h.nivel_max == 20, "sin potenciar: 1 disparo recto, recarga inmediata, máximo 20")
check(abs(j.proyectiles[0].direccion.angle_to(pygame.Vector2(1, 0))) < 1e-6, "el Disparo Veloz normal sale recto")

print("--- Ráfaga Veloz: escalado")
esperado = {21: (2, 0, 36, 25.5, 37, 1.85), 25: (6, 0, 40, 27.5, 43, 1.25), 29: (10, 0, 44, 29.5, 49, 0.65), 30: (10, 2, 45, 30, 50, 0.5)}
for nv, (n, rojas, vel, dano, costo, cd) in esperado.items():
    j, h = jug(); j.potenciar_habilidad("Disparo Veloz"); subir(j, h, nv)
    check((h.disparos, h.rojas, h.velocidad_proyectil, h.dano, h.costo_energia, h.duracion_cooldown) == (n, rojas, vel, dano, costo, cd),
          "nv%d: %d disparos (%d rojos), vel %g, daño %g, coste %d, recarga %g s" % (nv, n, rojas, vel, dano, costo, cd))
j, h = jug(); subir(j, h, 15); j.potenciar_habilidad("Disparo Veloz")
antes = j.puntos_mejora; subir(j, h, 30)
check(antes - j.puntos_mejora == 5 + 20 and h.nombre_mostrado == "Ráfaga Veloz", "15 -> 20 cuesta 5 y 20 -> 30 cuesta 20; se llama Ráfaga Veloz")

print("--- Ráfaga Veloz: disparos en el tiempo")
random.seed(4)
j, h = jug(); j.potenciar_habilidad("Disparo Veloz"); subir(j, h, 30)
e0 = j.energia
h.intentar_activar(j)
check(j.energia == e0 - 50 and len(j.proyectiles) == 1 and h.estado == "ACTIVA", "al activar: cobra 50 una vez y sale el 1er disparo")
tiempos = []; t = 0.0
while h.estado == "ACTIVA" and t < 10:
    n0 = len(j.proyectiles); h.actualizar(1 / 60, j); t += 1 / 60
    if len(j.proyectiles) > n0: tiempos.append(round(t, 2))
check(len(j.proyectiles) == 10, "salen 10 disparos en total (%d)" % len(j.proyectiles))
difs = [round(b - a, 2) for a, b in zip([0.0] + tiempos, tiempos)]
check(all(abs(d - 0.5) <= 0.025 for d in difs), "uno cada 0.5 s (±1 cuadro) %s" % difs)
check(h.estado == "COOLDOWN" and abs(h.tiempo_restante_cooldown - 0.5) < 0.02, "tras el último empieza la recarga (0.5 s)")
check(j.energia == e0 - 50, "no cobra más durante la ráfaga")
angulos = [p.direccion.angle_to(pygame.Vector2(1, 0)) for p in j.proyectiles]
check(all(abs(a) <= 7.5 + 1e-6 for a in angulos) and max(angulos) - min(angulos) > 3,
      "cono de 15° en total: desvíos entre %.1f° y %.1f°" % (min(angulos), max(angulos)))
rojos = [p for p in j.proyectiles if p.roja]
check(len(rojos) == 2 and all(p.dano == 35 for p in rojos) and all(p.dano == 30 for p in j.proyectiles if not p.roja),
      "nv30: 2 rojos de 35 y 8 normales de 30")
pos_rojas = []
for s in range(200):
    random.seed(s); j, h = jug(); j.potenciar_habilidad("Disparo Veloz"); subir(j, h, 30); h.intentar_activar(j)
    for _ in range(300): h.actualizar(1 / 60, j)
    pos_rojas += [i for i, p in enumerate(j.proyectiles) if p.roja]
check(len(set(pos_rojas)) == 10, "los rojos salen en posiciones al azar dentro de la ráfaga")
# sigue la mira: girar a mitad de ráfaga
random.seed(1); j, h = jug(); j.potenciar_habilidad("Disparo Veloz"); subir(j, h, 25); h.intentar_activar(j)
j.angulo = 180.0
for _ in range(200): h.actualizar(1 / 60, j)
ultimo = j.proyectiles[-1].direccion
check(abs(ultimo.angle_to(pygame.Vector2(0, 1))) <= 7.5 + 1e-6, "si giras durante la ráfaga, los siguientes disparos salen hacia donde miras")
# no se puede relanzar durante la ráfaga
random.seed(2); j, h = jug(); j.potenciar_habilidad("Disparo Veloz"); subir(j, h, 30); h.intentar_activar(j)
check(not h.intentar_activar(j), "durante la ráfaga no se puede volver a lanzar")
# guardarla a mitad: se cancelan los que faltan
h.actualizar(0.6, j); n = len(j.proyectiles)
j._retirar_habilidad(h)
for _ in range(300): h.actualizar(1 / 60, j)
check(len(j.proyectiles) == n and h.estado != "ACTIVA", "al guardarla a mitad se cancelan los disparos que faltan (%d)" % n)

print("--- Gacha")
j, h = jug()
check("Disparo Veloz" in G.potenciadas_disponibles(j), "Ráfaga Veloz entra en el Gacha mejorado")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
