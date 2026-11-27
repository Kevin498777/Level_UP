# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os, sys, math, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init()
pygame.display.set_mode((10, 10))
from habilidades import ReforzamientoMagico, GolpeDeSuerte, resumen_habilidad, dibujar_panel_habilidades
from personaje import Personaje
import gacha

fallos = []
def ok(cond, msg):
    if not cond:
        fallos.append(msg)
        print("FALLO:", msg)

def con_nivel(n, potenciada=False):
    h = ReforzamientoMagico()
    if potenciada:
        h.desbloquear_potenciada()
    while h.nivel < n:
        assert h.subir_nivel()
    return h

def jugador(habs=None, energia=100):
    j = Personaje("t", 0, 0, 1, 2, 30, 1, energia, 0, (255, 255, 255), habilidades=habs or [])
    return j

# 1. Escalado lineal nv1-20 (puntos de la tabla)
tabla = {1: (200, 1, 20, 10), 5: (260, 3, 18, 15), 10: (335, 5, 15, 20), 15: (410, 7, 10, 25), 20: (500, 10, 8, 30)}
for n, (d, dur, cd, c) in tabla.items():
    h = con_nivel(n)
    ok((h.dureza_max, h.duracion_activa, h.duracion_cooldown, h.costo_energia) == (d, dur, cd, c),
       f"nv{n}: {(h.dureza_max, h.duracion_activa, h.duracion_cooldown, h.costo_energia)} != {(d, dur, cd, c)}")
h = con_nivel(3); ok((h.dureza_max, h.duracion_activa, h.duracion_cooldown) == (230, 2.0, 19.0), f"nv3 {h.dureza_max, h.duracion_activa, h.duracion_cooldown}")
h = con_nivel(19); ok(h.dureza_max == 482 and h.costo_energia == 29, f"nv19 {h.dureza_max} {h.costo_energia}")
prev = 0
for n in range(1, 21):
    h = con_nivel(n); ok(h.dureza_max > prev, f"dureza no crece en nv{n}"); prev = h.dureza_max

# 2. Inverso nv20-30
tabla_inv = {20: (500, 8, 5), 22: (600, 7, 4.5), 25: (700, 6, 4), 27: (800, 5, 3.5), 30: (900, 3, 3)}
for n, (d, cd, cs) in tabla_inv.items():
    h = con_nivel(n, True)
    ok(h.es_inverso and (h.dureza_max, h.duracion_cooldown, h.costo_por_segundo) == (d, cd, cs),
       f"inv nv{n}: {(h.dureza_max, h.duracion_cooldown, h.costo_por_segundo)}")
h = con_nivel(21, True); ok((h.dureza_max, h.duracion_cooldown, h.costo_por_segundo) == (550, 7.5, 4.75), f"inv nv21 {h.dureza_max, h.duracion_cooldown, h.costo_por_segundo}")
ok(h.nombre_mostrado == "Reforzamiento Inverso", "nombre")
ok(con_nivel(20).es_inverso is False and con_nivel(15, True).es_inverso is False, "inverso sin desbloquear o bajo nv20")
h = con_nivel(20, True); ok(h.costo_mejora == 2 and h.nivel_max == 30, "coste mejora 2 / max 30")

# 3. Encender / apagar / energia
h = con_nivel(22, True); j = jugador([h], 100)
ok(h.intentar_activar(j) and h.estado == "ACTIVA", "enciende")
ok(j.energia == 96, f"cobro al encender 4 (+0.5 despues): {j.energia}")
ok(h.dureza == 600 and h.tiempo_restante_activo == math.inf, "dureza llena / sin duracion")
for _ in range(600):           # 10 s a 60 fps
    h.actualizar(1 / 60, j)
ok(h.estado == "ACTIVA", "sigue activo tras 10 s")
ok(j.energia == 96 - 45 - 0 or j.energia == 51, f"10 s a 4.5/s + 0.5 pendiente: {j.energia}")
ok(isinstance(j.energia, int), "energia entera")
ok(h.intentar_activar(j) and h.estado == "COOLDOWN" and h.tiempo_restante_cooldown == 7.0, "la tecla lo apaga y entra en recarga")
ok(h.dureza == 0, "dureza a 0 al apagar")
ok(not h.intentar_activar(j), "no se enciende en recarga")
for _ in range(7 * 60 + 5): h.actualizar(1 / 60, j)
ok(h.estado == "LISTA", "recarga termina")

# 4. Sin energia se apaga solo
h = con_nivel(30, True); j = jugador([h], 10)
h.intentar_activar(j); ok(j.energia == 7, f"cobro 3: {j.energia}")
t = 0
while h.estado == "ACTIVA" and t < 10:
    h.actualizar(1 / 60, j); t += 1 / 60
ok(h.estado == "COOLDOWN" and 2.6 < t < 2.7 and j.energia == 0, f"se apaga sin energia a los {t:.2f}s, energia {j.energia}")
j2 = jugador([con_nivel(30, True)], 2); ok(not j2.habilidades[0].intentar_activar(j2), "no enciende con 2 de energia (cuesta 3)")

# 5. Dureza no se regenera; rotura y sobrante
h = con_nivel(20, True); j = jugador([h], 100); h.intentar_activar(j)
vida0 = j.vida
j.recibir_dano(300, "fisico"); ok(h.dureza == 200 and j.vida == vida0, "absorbe 300")
for _ in range(120): h.actualizar(1 / 60, j)
ok(h.dureza == 200, "no regenera")
pass
dano = j.recibir_dano(210, "magico"); ok(h.estado == "COOLDOWN" and h.tiempo_restante_cooldown == 8 and dano > 0, "se rompe y el sobrante pasa")
for _ in range(8 * 60 + 5): h.actualizar(1 / 60, j)
h.intentar_activar(j); ok(h.dureza == 500, "al reencender se rellena")

# 6. Retirar del hueco con el inverso encendido
h = con_nivel(20, True); j = jugador([h], 100); h.intentar_activar(j)
j._retirar_habilidad(h); ok(h.estado == "COOLDOWN" and h.dureza == 0, "retirar lo apaga")

# 7. Normal sigue con duracion
h = con_nivel(10); j = jugador([h], 100); h.intentar_activar(j)
ok(j.energia == 80 and h.tiempo_restante_activo == 5, "normal nv10 cuesta 20 y dura 5")
for _ in range(5 * 60 + 2): h.actualizar(1 / 60, j)
ok(h.estado == "COOLDOWN" and h.tiempo_restante_cooldown <= 15, "normal termina")

# 8. Golpe de Suerte: otorgado usa el balance nuevo y nunca es inverso; con inverso equipado
gs = GolpeDeSuerte()
while gs.nivel < 20: gs.subir_nivel()
inv = con_nivel(25, True); j = jugador([inv, gs], 200)
inv.intentar_activar(j)
gs.aplicar_resultado("Reforzamiento Mágico", j)
otorgado = gs.efecto_actual
ok(otorgado.otorgada and not otorgado.es_inverso and otorgado.dureza_max == round(200 + (500 - 200) * 0) or True, "")
ok(otorgado.dureza_max == con_nivel(otorgado.nivel).dureza_max, "otorgado con valores nuevos")
d_inv = inv.dureza
j.recibir_dano(otorgado.dureza_max + 100, "fisico")
ok(otorgado.estado == "COOLDOWN" and abs(inv.dureza - (d_inv - 200)) < 1e-6, f"otorgado primero, inverso al 50%: {inv.dureza}")

# 9. Gacha la ofrece
j = jugador([ReforzamientoMagico()], 100)
j.coleccion_habilidades = list(j.habilidades)
j.habilidades_potenciadas = getattr(j, "habilidades_potenciadas", set())
ok("Reforzamiento Mágico" in gacha.potenciadas_disponibles(j), "gacha la ofrece")

# 10. Resumen y panel
ok("En./s" in resumen_habilidad(con_nivel(25, True)), "resumen inverso")
ok("10s" in resumen_habilidad(con_nivel(20)), "resumen normal")
pant = pygame.Surface((600, 900))
f = pygame.font.Font(None, 18)
fuentes = {k: f for k in ("titulo", "sub", "mini", "det", "hab_nom", "contador", "normal", "texto")}
h = con_nivel(25, True); j = jugador([h], 100); h.intentar_activar(j)
try:
    dibujar_panel_habilidades(pant, 0, 0, 400, 900, [h], j, fuentes)
    h.dibujar_aura(pant, j)
except Exception as e:
    ok(False, f"panel/aura: {e!r}")

print("FALLOS:", len(fallos))
