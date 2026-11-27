# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init()
pygame.display.set_mode((10, 10))
from habilidades import (RegeneracionInversa, GolpeDeSuerte, InvocacionConejos, resumen_habilidad,
                         dibujar_panel_habilidades, texto_costo)
from personaje import Personaje
import gacha

fallos = []
def ok(c, m):
    if not c:
        fallos.append(m); print("FALLO:", m)

def hab(n, pot=False):
    h = RegeneracionInversa()
    if pot:
        h.desbloquear_potenciada()
    while h.nivel < n:
        assert h.subir_nivel(), n
    return h

def jug(h, vida=30, vida_max=30, energia=100):
    j = Personaje("t", 0, 0, 1, 2, vida_max, 1, energia, 0, (255, 255, 255), habilidades=[h] if h else [])
    j.vida = vida
    return j

def correr(h, j, seg):
    for _ in range(int(round(seg * 60))):
        h.actualizar(1 / 60, j)

# 1. Escalado base
esperado = {1: (2, 5, 4.0), 2: (2, 5, 4.0), 3: (4, 10, 3.5), 5: (4, 10, 3.5), 6: (8, 20, 3.0), 8: (8, 20, 3.0), 9: (10, 20, 2.5), 10: (12, 25, 2.0)}
for n, v in esperado.items():
    h = hab(n); ok((h.curacion, h.costo_energia, h.intervalo) == v and h.ralentizacion == 0.2, f"base nv{n}: {(h.curacion, h.costo_energia, h.intervalo)}")
ok(hab(10).nivel_max == 10 and hab(1).costo_mejora == 2, "max 10 / 2 puntos")

# 2. Potenciada
h = hab(1, True); ok(h.costo_mejora == 2, "1-10 sigue costando 2")
h = hab(10, True); ok(h.nivel_max == 15 and h.costo_mejora == 3, f"10->15 cuesta 3 ({h.costo_mejora})")
regen = {10: (12, 25), 11: (14, 28), 12: (16, 32), 13: (18, 36), 14: (20, 40), 15: (22, 44)}
inv = {10: (4, 5, 2), 11: (8, 10, 4), 12: (12, 14, 6), 13: (16, 19, 8), 14: (20, 24, 10), 15: (25, 30, 12)}
ral = {10: .2, 11: .16, 12: .12, 13: .08, 14: .04, 15: 0}
for n in range(10, 16):
    h = hab(n, True)
    ok((h.curacion, h.costo_energia) == regen[n] and (h.costo_vida, h.energia_ganada, h.curacion_onda) == inv[n]
       and abs(h.ralentizacion - ral[n]) < 1e-9 and h.intervalo == 2.0, f"potenciada nv{n}")
    # anti abuso: una vuelta pierde recursos
    vuelta = h.energia_ganada / h.costo_vida * h.curacion / h.costo_energia
    ok(vuelta < 0.75, f"nv{n}: vuelta {vuelta:.2f} >= 0.75")
ok(hab(9, True).potenciada_activa is False and hab(10, True).potenciada_activa, "activa desde nv10")

# 3. Base: curar, debuff, vida llena, sin energia
h = hab(1); j = jug(h, vida=20)
v0 = j.velocidad_base
h.iniciar_carga(j); j.actualizar_velocidad()
ok(abs(j.velocidad - v0 * 0.8) < 1e-6, f"-20% al mantener: {j.velocidad}")
correr(h, j, 4.05); ok(j.vida == 22 and j.energia == 95, f"cura +2/-5: {j.vida} {j.energia}")
h.soltar_carga(j); j.actualizar_velocidad(); ok(abs(j.velocidad - v0) < 1e-6, "sin debuff al soltar")
j.vida = 29.5; h.iniciar_carga(j); correr(h, j, 4.05); ok(j.vida == 30 and j.energia == 90, "falta 0.5: cura solo eso a coste normal")
correr(h, j, 8); ok(j.energia == 90, "vida llena no cobra")
j.vida = 10; j.energia = 4; h.soltar_carga(j); h.iniciar_carga(j); ok(not h.canalizando, "sin energia no empieza")

# 4. Cambio de modo
h = hab(9, True); ok(h.cambiar_modo(None) is False, "sin potenciada activa no cambia")
h = hab(12, True); j = jug(h, vida=60, vida_max=100, energia=50)
j.energia_max = 100
h.iniciar_carga(j); ok(h.canalizando, "canaliza")
ok(h.cambiar_modo(j) and h.modo_inversion and not h.canalizando, "cambia y corta la canalizacion")
ok(h.nombre_mostrado == "Inversión Vital" and texto_costo(h, j) == "12 vida", "nombre y coste en vida")
ok(h.cambiar_modo(j) is False, "espera de 4 s")
correr(h, j, 4.05); ok(h.puede_cambiar_modo, "tras 4 s se puede")

# 5. Inversion Vital
vida0, en0 = j.vida, j.energia
j.escudo = 50; j.escudo_magico = 50
h.iniciar_carga(j); j.actualizar_velocidad()
ok(abs(j.velocidad - j.velocidad_base * 0.88) < 1e-6, "debuff -12% en inversion")
correr(h, j, 2.02)
ok(j.vida == vida0 - 12 and j.energia == en0 + 14 and j.escudo == 50, f"-12 vida directa +14 En.: {j.vida} {j.energia} {j.escudo}")
j.energia = 95; correr(h, j, 2.0); ok(j.energia == 100, "no pasa del maximo")
v = j.vida; correr(h, j, 4); ok(j.vida == v, "energia llena no cobra")
j.energia = 0; j.vida = 20
correr(h, j, 2.02); ok(j.vida == 8, f"20 -> 8: {j.vida}")
correr(h, j, 2.02); ok(j.vida == 8 and not h.canalizando, "se detiene antes de bajar de 5")
j.vida = 16; h.iniciar_carga(j); ok(not h.canalizando, "no empieza si el cobro deja < 5")
j.vida = 17; h.iniciar_carga(j); ok(h.canalizando, "empieza con 17 (deja 5)")
h.soltar_carga(j)

# 6. Onda a sombras (incluido anillo) y no al portador
con = InvocacionConejos()
h = hab(15, True); h.cambiar_modo(None) if False else None
j = jug(h, vida=100, vida_max=100, energia=0); j.energia_max = 100
h.modo = h.MODO_INVERSION
j.habilidades.append(con)
con.ejecutar_activacion(j)
crs = list(con.criaturas)
ok(len(crs) > 0, "hay conejos")
for c in crs:
    c.vida = 1
    c.posicion = j.posicion + pygame.Vector2(100, 0)
lejos = crs[-1]; lejos.posicion = j.posicion + pygame.Vector2(400, 0)
h.iniciar_carga(j); correr(h, j, 2.02)
cerca = crs[0]
ok(cerca.vida == min(cerca.vida_max, 13), f"conejo cerca curado: {cerca.vida}/{cerca.vida_max}")
ok(lejos.vida == 1 or len(crs) == 1, "conejo lejos no")
ok(j.vida == 75, f"el portador no se cura con la onda: {j.vida}")
ok(len(h.ondas) == 1, "onda visual")

# 7. Golpe de Suerte: regeneracion otorgada sin debuff
gs = GolpeDeSuerte(); j = jug(gs, vida=10)
gs.aplicar_resultado(gs.REGENERACION, j); j.actualizar_velocidad()
ok(abs(j.velocidad - j.velocidad_base) < 1e-6, "GS sin debuff")

# 8. Gacha / resumen / panel / aura
j = jug(RegeneracionInversa()); j.coleccion_habilidades = list(j.habilidades)
ok("Regeneración Inversa" in gacha.potenciadas_disponibles(j), "gacha la ofrece")
h = hab(15, True); h.modo = h.MODO_INVERSION
ok("Sombras +12" in resumen_habilidad(h) and "Vel" not in resumen_habilidad(h), resumen_habilidad(h))
ok("Vel -20%" in resumen_habilidad(hab(3)), resumen_habilidad(hab(3)))
pant = pygame.Surface((800, 900)); f = pygame.font.Font(None, 18)
fuentes = {k: f for k in ("titulo", "sub", "mini", "det", "hab_nom", "contador", "normal", "texto")}
j = jug(h, vida=100, vida_max=100, energia=0)
b = dibujar_panel_habilidades(pant, 0, 0, 320, 900, [h], j, fuentes)
ok("__modo__0" in b, f"boton modo en panel: {list(b)}")
h.cambiar_modo(j); b = dibujar_panel_habilidades(pant, 0, 0, 320, 900, [h], j, fuentes)
ok("__modo__0" not in b, "boton deshabilitado en espera")
h.modo = h.MODO_INVERSION; h.iniciar_carga(j); h.ondas = [0.2]; h.dibujar_aura(pant, j)
from inventario import dibujar_inventario
print("FALLOS:", len(fallos))
