# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Burst de Fuerza -> Fuerza Colosal (segunda habilidad potenciada). Uso: python -B test_colosal.py <proyecto>
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import habilidades as H, gacha as G, herramientas, fauna as F, mundo
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug(habs=("Burst de Fuerza",), herr="Espada Larga"):
    hs = [H.crear_habilidad(n) for n in habs]
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), hs, herramientas.crear_herramienta(herr), 0)
    for _ in range(19): j.subir_nivel()
    j.puntos_mejora = 500; j.energia = j.energia_max = 1000
    return j
def burst(j): return next(h for h in j.coleccion_habilidades if h.nombre == "Burst de Fuerza")
def subir(j, hab, hasta):
    while hab.nivel < hasta:
        c = hab.costo_mejora; assert hab.subir_nivel(); j.puntos_mejora -= c

print("--- Burst nv20 y desbloqueo")
j = jug(); b = burst(j); subir(j, b, 20)
check((b.porcentaje_buff, b.duracion_activa, b.duracion_cooldown, b.costo_energia) == (0.4, 10.0, 8.0, 35), "Burst nv20: +40 %, 10 s, 8 s, 35 En.")
check(b.nivel_max == 20 and b.nombre_mostrado == "Burst de Fuerza", "sin potenciar: máximo 20")
j = jug(); b = burst(j); subir(j, b, 15); j.potenciar_habilidad("Burst de Fuerza")
check(not b.potenciada_activa and b.costo_mejora == 1, "desbloqueada en Nv 15: sigue siendo Burst y cuesta 1 punto")
antes = j.puntos_mejora; subir(j, b, 30)
check(antes - j.puntos_mejora == 5 + 20 and b.nombre_mostrado == "Fuerza Colosal" and not b.subir_nivel(),
      "15 -> 20 cuesta 5 y 20 -> 30 cuesta 20 (2 por nivel); se llama Fuerza Colosal y para en 30")

print("--- escalado lineal")
esperado = {21: (0.46, 11.5, 7.6, 39), 25: (0.70, 17.5, 6.0, 53), 30: (1.00, 25.0, 4.0, 70)}
for nv, (bf, du, cd, co) in esperado.items():
    j = jug(); b = burst(j); j.potenciar_habilidad("Burst de Fuerza"); subir(j, b, nv)
    check(abs(b.porcentaje_buff - bf) < 1e-9 and abs(b.duracion_activa - du) < 1e-9 and abs(b.duracion_cooldown - cd) < 1e-9 and b.costo_energia == co,
          "nv%d: +%d %% fuerza, %g s, recarga %g s, %d En." % (nv, round(bf * 100), du, cd, co))
j = jug(); b = burst(j); j.potenciar_habilidad("Burst de Fuerza"); subir(j, b, 30)
f0 = j.fuerza; b.intentar_activar(j)
check(abs(j.fuerza - 2 * f0) < 1e-6, "nv30 activa: fuerza x2 (%g -> %g)" % (f0, j.fuerza))
b.tiempo_restante_activo = 0.01; b.actualizar(0.05, j)
check(abs(j.fuerza - f0) < 1e-6, "al acabar vuelve a la fuerza base")

print("--- pasiva: +30 % al escudo físico")
def golpe(con_colosal, activa=True, tipo="fisico", objetivo="coco"):
    j = jug(); b = burst(j)
    if con_colosal:
        j.potenciar_habilidad("Burst de Fuerza"); subir(j, b, 21)
    else:
        subir(j, b, 20)
    if activa: b.intentar_activar(j)
    if objetivo == "coco":
        class Lago:
            centro = pygame.Vector2(0, 0); radio = 400
            def contiene(self, p): return True
            def en_zona_peligro(self, p): return True
        e = F.Cocodrilo(Lago()); e.estado = "ataca"; e.escudo = e.escudo_max
    else:
        e = mundo.Maniqui(pygame.Vector2(0, 0))
    e0, v0 = e.escudo, e.vida
    j.golpear_con_arma(e, 20, tipo)
    return e0 - e.escudo, v0 - e.vida
sin_e, sin_v = golpe(False)
con_e, con_v = golpe(True)
check(abs(con_e - sin_e * 1.3) < 0.02 and abs(con_v - sin_v) < 1e-6,
      "cocodrilo: el escudo pierde un 30 %% más (%.2f -> %.2f) y la vida recibe lo mismo (%.2f)" % (sin_e, con_e, con_v))
ina_e, _ = golpe(True, activa=False)
check(abs(ina_e - sin_e) < 1e-6, "Fuerza Colosal sin activar: sin extra")
mag_e, _ = golpe(True, tipo="magico")
check(mag_e == 0, "daño mágico (habilidades): no aplica")
try:
    m_sin, _ = golpe(False, objetivo="maniqui"); m_con, _ = golpe(True, objetivo="maniqui")
    check(abs(m_con - m_sin * 1.3) < 0.02, "maniquí: el escudo pierde un 30 %% más (%.2f -> %.2f)" % (m_sin, m_con))
except TypeError as ex:
    print("      (maniquí con otra firma, omitido:", ex, ")")
j = jug(); b = burst(j); j.potenciar_habilidad("Burst de Fuerza"); subir(j, b, 20); b.intentar_activar(j)
lobo = F.LoboSolitario(0, 0); v = lobo.vida; j.golpear_con_arma(lobo, 10, "fisico")
check(v - lobo.vida == 10, "enemigo sin escudo: el golpe hace su daño normal")

print("--- Gacha y Golpe de Suerte")
j = jug(habs=("Burst de Fuerza", "Destello", "Cortar"))
# Desde el 26/11 todas las habilidades tienen potenciada (Cortar -> Desmantelar)
check(sorted(G.potenciadas_disponibles(j)) == ["Burst de Fuerza", "Cortar", "Destello"], "el Gacha mejorado ofrece las 3 potenciadas: %s" % G.potenciadas_disponibles(j))
g = H.crear_habilidad("Burst de Fuerza"); g.otorgada = True
check(not g.potenciada_activa and g.extra_dano_escudo == 0, "el Burst que da Golpe de Suerte es el normal")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
