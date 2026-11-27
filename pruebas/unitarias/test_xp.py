# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas headless del sistema de XP, reaparicion de fauna y muerte del jugador.
import os, sys, random, gc
os.environ["SDL_VIDEODRIVER"] = "dummy"
PROY = sys.argv[1]
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
random.seed(5)
import mundo, fauna, herramientas, habilidades
from personaje import Personaje, XP_POR_NIVEL, NIVEL_MAXIMO, PUNTOS_MEJORA_POR_NIVEL as PPN

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c:
        fallos.append(m)

def jugador():
    j = Personaje("T", 0, 0, 1.0, 3, 100, 10, 100, 10, (0, 0, 255), [], herramientas.crear_herramienta("Espada Ligera"), 10)
    return j

# ---------- 1. Personaje.ganar_xp ----------
check(len(XP_POR_NIVEL) == NIVEL_MAXIMO - 1, "tabla con %d saltos (1->%d)" % (NIVEL_MAXIMO - 1, NIVEL_MAXIMO))
PUNTOS0 = jugador().puntos_mejora
j = jugador()
for _ in range(10):
    j.ganar_xp(0.1)
check(j.nivel == 2 and j.xp == 0 and j.puntos_mejora == PUNTOS0 + PPN, "10 conejos (10 x 0.1) suben al nivel 2 exacto (+%d puntos)" % PPN)
j = jugador(); j.ganar_xp(4)          # 1 (->2) + 2 (->3) = 3, sobra 1
check(j.nivel == 3 and abs(j.xp - 1) < 1e-9, "sobrante pasa al siguiente nivel (4 XP en nv1 -> nv3 con 1 XP)")
j = jugador(); n = j.ganar_xp(10_000)
j = jugador(); n = j.ganar_xp(sum(XP_POR_NIVEL) + 10_000)
check(j.nivel == NIVEL_MAXIMO and j.xp == 0 and n == NIVEL_MAXIMO - 1 and j.puntos_mejora == PUNTOS0 + (NIVEL_MAXIMO - 1) * PPN,
      "tope en nivel %d, XP a 0, %d puntos extra" % (NIVEL_MAXIMO, (NIVEL_MAXIMO - 1) * PPN))
check(j.ganar_xp(50) == 0 and j.xp == 0 and j.xp_siguiente is None, "en el nivel maximo ya no acumula XP")
j = jugador()
for _ in range(NIVEL_MAXIMO + 10):
    j.subir_nivel()
check(j.nivel == NIVEL_MAXIMO, "[L] tambien se detiene en %d" % NIVEL_MAXIMO)

# ---------- mundo real ----------
charcos = mundo.generar_charcos()
veg = mundo.SistemaVegetacion(mundo.LIMITE, mundo.ZONA_SEGURA_SPAWN, charcos)
rocas = mundo.generar_rocas(list(charcos) + veg.arbustos + veg.arboles)
veg.registrar_obstaculos(rocas)
sf = fauna.SistemaFauna(mundo.LIMITE, veg, charcos, rocas)
lejos = pygame.Rect(-50000, -50000, 10, 10)     # vista fuera del mundo: nada se actualiza por IA
j = jugador(); j.posicion = pygame.Vector2(-40000, -40000)

def matar(a):
    a.recibir_dano(10_000, "fisico", pygame.Vector2(1, 0))

# 2. XP por especie
sf.tomar_xp()
for grupo, xp in ((sf.conejos, 0.5), (sf.venados, 2), (sf.zorros, 3), (sf.jabalies, 5), (sf.cocodrilos, 10)):
    if not grupo:
        continue
    a = grupo[0]
    if hasattr(a, "estado") and isinstance(a, fauna.Cocodrilo):
        a.estado = "ataca"
    matar(a)
    got = sf.tomar_xp()
    check(abs(got - xp) < 1e-9, "%s da %.1f XP (dio %.1f)" % (type(a).__name__, xp, got))
    check(sf.tomar_xp() == 0, "%s: la XP se cuenta una sola vez" % type(a).__name__)

# Conejo/venado cazado por un depredador salvaje: sin XP
c = [x for x in sf.conejos if x.vivo][0]
c.vivo = False; c.muerto_por_fauna = True
check(sf.tomar_xp() == 0, "conejo cazado por un zorro/lobo salvaje no da XP")

# 3. Manada: 3 lobos x2 + alfa 4 + bono 3 = 13
man = sf.manadas[0]
for l in man.lobos:
    matar(l)
check(abs(sf.tomar_xp() - 26) < 1e-9, "manada completa = 26 XP (3x5 + alfa 8 + bono 3)")
man2 = sf.manadas[1]
for l in man2.lobos[:2]:
    matar(l)
check(abs(sf.tomar_xp() - 13) < 1e-9 and not man2.bono_dado, "2 lobos (alfa + 1) = 13 XP, sin bono todavia")

# 4. Oso: 6 XP + orbe 2 XP; por desangrado tambien deja orbe
oso = sf.osos[0]; oso.estado = "ataca"; matar(oso)
check(abs(sf.tomar_xp() - 15) < 1e-9 and oso.orbe is not None, "oso = 15 XP y deja orbe")
j.posicion = pygame.Vector2(oso.orbe.centro)
vista_oso = pygame.Rect(0, 0, 400, 400); vista_oso.center = (round(oso.cueva.x), round(oso.cueva.y))
sf.actualizar(1 / 60, j, vista_oso)
check(abs(sf.tomar_xp() - 2) < 1e-9 and not oso.orbe.activo, "recoger el orbe de la cueva = +2 XP")
j.posicion = pygame.Vector2(-40000, -40000)
oso2 = sf.osos[1]; oso2.vida = 0; oso2.vivo = False      # muerte por efecto (sin recibir_dano)
sf.tomar_xp()
check(oso2.orbe is not None, "oso muerto por un efecto tambien deja su orbe")

# 5. Reaparicion de osos (3 min) - no con el jugador dentro, no si la roca se destruyo
def avanzar(seg, paso=1.0):
    t = 0.0
    while t < seg:
        sf.actualizar(paso, j, lejos); t += paso

avanzar(170)
check(not sf.osos[0].vivo, "oso aun muerto a los 170 s")
j.posicion = pygame.Vector2(sf.osos[0].entrada)
avanzar(20)
check(not sf.osos[0].vivo, "no reaparece con el jugador dentro de la cueva")
j.posicion = pygame.Vector2(-40000, -40000)
avanzar(2)
nuevo = sf.osos[0]
check(nuevo.vivo and nuevo.estado == "cueva" and nuevo.vida == fauna.OSO_VIDA and nuevo.entrada == oso.entrada,
      "oso nuevo en su cueva tras 3 min (misma entrada, vida llena)")
oso3 = sf.osos[2]; oso3.estado = "ataca"; matar(oso3); sf.tomar_xp()
rocas.remove(oso3.roca)
avanzar(200)
check(not sf.osos[2].vivo, "si la roca (cueva) fue destruida no reaparece")

# 6. Manadas: tras exterminarla vuelven 2 lobos; +1/min hasta 4 y uno evoluciona a alfa
# (man ya fue exterminada y avanzamos ~390 s: debe estar llena)
vivos = man.vivos()
check(len(vivos) == 4 and sum(l.es_alfa for l in vivos) == 1, "manada exterminada se rehace a 4 con 1 alfa (%d vivos)" % len(vivos))
check(not man.bono_dado, "el bono de manada se puede volver a ganar")
alfa = [l for l in vivos if l.es_alfa][0]
check(alfa.vida_max == fauna.LOBO_VIDA_ALFA and alfa.dano == fauna.LOBO_DANO_ALFA and alfa.xp == fauna.XP_LOBO_ALFA,
      "el lobo evolucionado tiene stats y XP de alfa")
man3 = sf.manadas[2]
for l in man3.lobos:
    matar(l)
sf.tomar_xp()
man3._t_repro = 0.0
centro_viejo = pygame.Vector2(man3.centro)
avanzar(61)
check(len(man3.vivos()) == 2, "1 min despues de exterminarla se inicia otra manada con 2 lobos")
check((man3.centro - centro_viejo).length() >= fauna.MANADA_DIST_NUEVA and
      all((l.posicion - man3.centro).length() < 80 for l in man3.vivos()),
      "la manada nueva aparece en otro bosque (a %.0f px de la anterior)" % (man3.centro - centro_viejo).length())
check(len(sf.manadas) == fauna.LOBO_MANADAS, "siguen siendo 7 manadas")
check(not any(l.es_alfa for l in man3.vivos()), "los 2 que vuelven son normales (sin alfa)")
sf.tomar_xp()
for l in man3.vivos():
    matar(l)
check(abs(sf.tomar_xp() - 10) < 1e-9, "exterminar 2 lobos sin alfa = 10 XP, sin bono de manada completa")
man3._t_repro = 0.0
avanzar(61)
man3.alertada = True
man3.repoblar(); man3.repoblar()
check(len(man3.vivos()) == 2, "no crece mientras esta en combate (alertada)")
man3.alertada = True
avanzar(1)
check(not man3.alertada, "fuera de la vista la manada deja el combate")
man3.alertada = False
avanzar(130)
check(len(man3.vivos()) == 4 and any(l.es_alfa for l in man3.vivos()), "luego crece hasta 4 y aparece un alfa")
check(all(len(m.lobos) <= 8 for m in sf.manadas), "las listas de lobos no crecen sin limite")
check(all(len(m.vivos()) <= fauna.LOBO_POR_MANADA for m in sf.manadas), "ninguna manada pasa de 4")

# 7. Zorros: reaparecen (3 min) y se reproducen (2 min) sin pasar el maximo
for z in sf.zorros[:10]:
    matar(z)
sf.tomar_xp()
sf._t_reap_zorro = 0.0; sf._t_repro_zorro = 0.0
avanzar(1)
n0 = len(sf.zorros)
avanzar(360)
check(len(sf.zorros) == n0 + 2 + 3, "en 6 min: +2 reaparecidos y +3 nacidos (%d -> %d)" % (n0, len(sf.zorros)))
avanzar(3600)
check(len(sf.zorros) == fauna.ZORRO_MAX, "los zorros no pasan del maximo (%d)" % len(sf.zorros))

# 8. Madriguera vacia: se destruye y aparece otra en otro sitio
m = sf.madrigueras[0]
n_mad = len(sf.madrigueras)
for c in [c for c in sf.conejos if c.madriguera is m]:
    matar(c)
avanzar(1)
check(m not in sf.madrigueras and len(sf.madrigueras) == n_mad, "madriguera vacia reemplazada (siguen %d)" % n_mad)
nueva = sf.madrigueras[-1]
nc = sum(1 for c in sf.conejos if c.madriguera is nueva)
check(2 <= nc <= 10, "la nueva madriguera trae 2-10 conejos (%d)" % nc)
check(all(any(c.madriguera is mm for c in sf.conejos) for mm in sf.madrigueras), "ninguna madriguera queda vacia")

# 10. Monedas
TABLA = {fauna.ConejoSalvaje: (0.05, 1, 1), fauna.Venado: (0.25, 1, 2), fauna.Zorro: (0.40, 1, 3),
         fauna.Jabali: (0.70, 2, 5), fauna.Oso: (1.0, 8, 12), fauna.Cocodrilo: (1.0, 6, 12)}
GRUPOS = {fauna.ConejoSalvaje: sf.conejos, fauna.Venado: sf.venados, fauna.Zorro: sf.zorros,
          fauna.Jabali: sf.jabalies, fauna.Oso: sf.osos, fauna.Cocodrilo: sf.cocodrilos}
N = 20000
for cls, (prob, mn, mx) in TABLA.items():
    if not GRUPOS[cls]:
        continue
    a = GRUPOS[cls][0]
    tiros = [a.tirar_monedas() for _ in range(N)]
    con = [t for t in tiros if t > 0]
    frac = len(con) / N
    check(abs(frac - prob) < 0.015 and con and min(con) == mn and max(con) == mx,
          "%s: %.0f%% de soltar %d-%d monedas (medido %.1f%%, rango %s-%s)" % (cls.__name__, prob * 100, mn, mx, frac * 100,
          min(con) if con else "-", max(con) if con else "-"))
lob = [l for m in sf.manadas for l in m.vivos()]
normal = [l for l in lob if not l.es_alfa][0]; alfa = [l for l in lob if l.es_alfa][0]
tn = [normal.tirar_monedas() for _ in range(5000)]; ta = [alfa.tirar_monedas() for _ in range(5000)]
check(min(tn) == 5 and max(tn) == 10, "lobo: siempre 5-10 monedas")
check(min(ta) == 7 and max(ta) == 10, "lobo alfa: siempre 7-10 monedas")
check(normal.xp == 5 and alfa.xp == 8, "XP: lobo 5, alfa 8")
sf.tomar_xp(); sf.tomar_monedas()
m = [l for l in sf.manadas[3].vivos()]
for l in m:
    matar(l)
mon = sf.tomar_monedas()
check(len(m) * 5 <= mon <= len(m) * 10, "matar %d lobos entrega %d monedas" % (len(m), mon))
check(sf.tomar_monedas() == 0, "las monedas se entregan una sola vez")
c = [x for x in sf.conejos if x.vivo][0]; c.vivo = False; c.muerto_por_fauna = True
v2 = [x for x in sf.venados if x.vivo][0]; v2.vivo = False; v2.muerto_por_fauna = True
sf.tomar_xp()
check(sf.tomar_monedas() == 0, "lo cazado por depredadores salvajes no da monedas")

# 9. olvidar_objetivos
z = [z for z in sf.zorros if z.vivo][0]
z._robar_de(j)
sf.manadas[0].alertada = True
sf.olvidar_objetivos([j])
check(z.presa is None and j.vel_mult == 1.0 if hasattr(j, "vel_mult") else z.presa is None, "zorro suelta al jugador muerto")
check(not sf.manadas[0].alertada, "las manadas dejan de perseguir")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
