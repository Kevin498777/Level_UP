# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Destello -> Relampago (primera habilidad potenciada). Uso: python -B test_relampago.py <proyecto>
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import habilidades as H, gacha as G, herramientas, fauna as F
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug(nivel=20, habs=("Destello",), escudo_m=0):
    hs = [H.crear_habilidad(n) for n in habs]
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), hs, herramientas.crear_herramienta("Espada Larga"), escudo_m)
    for _ in range(nivel - 1): j.subir_nivel()
    j.puntos_mejora = 500; j.energia = j.energia_max = 1000
    return j
def destello(j): return next(h for h in j.coleccion_habilidades if h.nombre == "Destello")
def subir(j, hab, hasta):
    while hab.nivel < hasta:
        c = hab.costo_mejora
        assert hab.subir_nivel(); j.puntos_mejora -= c

# ---------- 1. Destello normal sin cambios
print("--- Destello nv20 (sin potenciar)")
j = jug(); d = destello(j); subir(j, d, 20)
check((d.porcentaje_buff, d.duracion_activa, d.duracion_cooldown, d.porcentaje_debuff, d.costo_energia) == (0.9, 18.0, 1.0, 0.0, 40),
      "nv20: 90 %, 18 s, 1 s, 0 % fatiga, 40 En.")
check(d.nivel_max == 20 and not d.subir_nivel() and d.nombre_mostrado == "Destello", "sin potenciar se queda en el 20 y se llama Destello")

# ---------- 2. Desbloqueo con la habilidad por debajo del 20
print("--- desbloqueo")
j = jug(); d = destello(j); subir(j, d, 12)
check(j.potenciar_habilidad("Destello") and d.potenciada_desbloqueada, "el Gacha la desbloquea aunque esté en Nv 12")
check(not d.potenciada_activa and d.nombre_mostrado == "Destello" and d.costo_mejora == 1, "hasta el 20 sigue siendo Destello y cuesta 1 punto")
check(d.nivel_max == 30, "nivel máximo 30")
antes = j.puntos_mejora
subir(j, d, 20)
check(antes - j.puntos_mejora == 8, "del 12 al 20 cuesta 8 puntos (1 por nivel)")
check(d.potenciada_activa and d.nombre_mostrado == "Relámpago" and d.costo_mejora == 2, "en el 20 pasa a Relámpago y el siguiente nivel cuesta 2")
antes = j.puntos_mejora; subir(j, d, 30)
check(antes - j.puntos_mejora == 20 and not d.subir_nivel(), "del 20 al 30 cuesta 20 puntos (2 por nivel) y para en el 30")
check(not j.potenciar_habilidad("Destello"), "no se puede desbloquear dos veces")

# ---------- 3. Escalado 21-30
print("--- escalado")
esperado = {21: (1.00, 19.2, 42), 25: (1.40, 24.0, 50), 29: (1.80, 28.8, 58), 30: (2.00, 30.0, 60)}
for nv, (buff, dur, costo) in esperado.items():
    j = jug(); d = destello(j); j.potenciar_habilidad("Destello"); subir(j, d, nv)
    check(abs(d.porcentaje_buff - buff) < 1e-9 and abs(d.duracion_activa - dur) < 1e-9 and d.costo_energia == costo
          and d.duracion_cooldown == 1.0 and d.porcentaje_debuff == 0.0,
          "nv%d: +%d %% vel, %g s, %d En., recarga 1 s, sin fatiga" % (nv, round(buff * 100), dur, costo))
j = jug(); d = destello(j); j.potenciar_habilidad("Destello"); subir(j, d, 30)
d.asignar_tecla(pygame.K_2, "2"); j.velocidad_base = 1.0
d.intentar_activar(j); j.actualizar_velocidad()
check(abs(j.velocidad - 3.0) < 0.05, "nv30 activo: velocidad x3 (+200 %%) -> %.2f" % j.velocidad)

# ---------- 4. Aura: dano a enemigos y autodano
print("--- aura")
j = jug(); d = destello(j); j.potenciar_habilidad("Destello"); subir(j, d, 20); j.posicion = pygame.Vector2(0, 0)
cerca = F.LoboSolitario(60, 0); lejos = F.LoboSolitario(120, 0); vc, vl = cerca.vida, lejos.vida
d.intentar_activar(j)
for _ in range(61):                     # 1 s (+1 cuadro por redondeo)
    d.actualizar(1 / 60, j); d.actualizar_dano_enemigos(1 / 60, [cerca, lejos], j)
check(abs((vc - cerca.vida) - 10) < 1e-6, "enemigo dentro (70 px + su radio): 10 de daño en 1 s (%g)" % (vc - cerca.vida))
check(lejos.vida == vl, "enemigo fuera del aura: sin daño")
check(abs(j.vida_max - j.vida - 0.5) < 1e-6, "autodaño: 0.5 por segundo (%g)" % (j.vida_max - j.vida))
j2 = jug(escudo_m=20); d2 = destello(j2); j2.potenciar_habilidad("Destello"); subir(j2, d2, 20)
d2.intentar_activar(j2)
for _ in range(600): d2.actualizar(1 / 60, j2)
check(abs((j2.vida_max - j2.vida) - 0.5) < 1e-6 and j2.escudo_magico < 20, "el autodaño es mágico: de 5 en 10 s el escudo mágico frena 4.5 (vida -%g)" % (j2.vida_max - j2.vida))
# sin potenciar o inactivo: no hay aura
j = jug(); d = destello(j); subir(j, d, 20); e = F.LoboSolitario(40, 0); v = e.vida
d.intentar_activar(j)
for _ in range(120): d.actualizar(1 / 60, j); d.actualizar_dano_enemigos(1 / 60, [e], j)
check(e.vida == v and j.vida == j.vida_max, "Destello sin potenciar: ni aura ni autodaño")
j = jug(); d = destello(j); j.potenciar_habilidad("Destello"); subir(j, d, 20); e = F.LoboSolitario(40, 0); v = e.vida
for _ in range(120): d.actualizar(1 / 60, j); d.actualizar_dano_enemigos(1 / 60, [e], j)
check(e.vida == v and j.vida == j.vida_max, "Relámpago sin activar: el aura no hace nada")
# Golpe de Suerte: su Destello otorgado es el normal
g = H.crear_habilidad("Destello"); g.otorgada = True
check(not g.potenciada_activa and not g.tiene_potenciada is False, "el Destello que da Golpe de Suerte es el normal")

# ---------- 5. Gacha: solo potenciadas disenadas
print("--- Gacha")
j = jug(habs=("Cortar", "Onda Sonora", "Destello"))
check("Destello" in G.potenciadas_disponibles(j), "sale Relámpago (las demás habilidades también tienen potenciada desde el 26/11)")
j2 = jug(habs=("Cortar", "Onda Sonora"))
for n in j2.habilidades_faltantes():
    if n != "Destello": j2.agregar_habilidad(n)
check("Destello" not in G.potenciadas_disponibles(j2), "sin Destello en la colección no sale Relámpago")
j3 = jug(); [j3.agregar_habilidad(n) for n in j3.habilidades_faltantes()]; [j3.agregar_herramienta(n) for n in j3.herramientas_faltantes()]
j3.talismanes.totems = 5; j3.monedas = 10 ** 5; rng = random.Random(1); dio = None
for _ in range(5000):
    r = G.tirar(j3, rng)
    if r["categoria"] == G.POTENCIADA and not r["agotada"] and "Relámpago" in r["texto"]: dio = r; break
check(dio is not None and destello(j3).potenciada_desbloqueada and "Relámpago" in dio["texto"], "el Gacha mejorado da Relámpago: %s" % (dio or {}).get("texto"))
check("Destello" not in G.potenciadas_disponibles(j3), "después Relámpago ya no vuelve a salir")
# muerte sin totem: se pierde
j3.__init__("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [H.crear_habilidad("Destello")], herramientas.crear_herramienta("Espada Larga"), 0)
check(not destello(j3).potenciada_desbloqueada and not j3.habilidades_potenciadas, "al morir sin tótem se pierde")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
