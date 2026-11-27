# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Pruebas de calidad: interacciones ENTRE sistemas (XP, monedas, Gacha, talismanes, totem,
# coleccion, herramientas, habilidades, muerte, fauna) sobre los objetos reales del juego.
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
import habilidades as H, herramientas as T, talismanes as TL, gacha as G, fauna as F, mundo
from personaje import Personaje, MONEDAS_POR_NIVEL, XP_POR_NIVEL, NIVEL_MAXIMO
from habilidades import aplicar_desangrado

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def nuevo(habs=("Disparo Veloz", "Invocar Lobos", "Cortar"), herr="Espada Larga", vida=20, escudo=0):
    hs = [H.crear_habilidad(n) for n in habs]
    for i, h in enumerate(hs): h.asignar_tecla([pygame.K_2, pygame.K_3, pygame.K_4][i], "234"[i])
    return Personaje("T", 0, 0, 1, 1, vida, 2, 100, escudo, (0, 0, 255), hs, T.crear_herramienta(herr), 0)
class Rng:
    """rng controlado: random() devuelve la secuencia dada y choice() elige el nombre pedido."""
    def __init__(self, seq, eleccion=None): self.seq, self.el = list(seq), eleccion
    def random(self): return self.seq.pop(0)
    def choice(self, l): return self.el if self.el in l else l[0]

print("--- 1. Monedas por nivel")
j = nuevo()
j.ganar_xp(1)
check(j.nivel == 2 and j.monedas == MONEDAS_POR_NIVEL == 20, "subir 1 nivel da +20 monedas")
j.ganar_xp(2 + 4 + 8)
check(j.nivel == 5 and j.monedas == 80, "varios niveles de golpe: +20 por cada uno (80)")
j.subir_nivel()
check(j.monedas == 100, "[L] (subir_nivel) tambien da +20")
j = nuevo(); j.ganar_xp(sum(XP_POR_NIVEL) + 500)
TOPE_MON = (NIVEL_MAXIMO - 1) * MONEDAS_POR_NIVEL
check(j.nivel == NIVEL_MAXIMO and j.monedas == TOPE_MON, "hasta el nivel %d: %d subidas = %d monedas" % (NIVEL_MAXIMO, NIVEL_MAXIMO - 1, TOPE_MON))
j.subir_nivel(); j.ganar_xp(100)
check(j.monedas == TOPE_MON, "en el nivel %d ya no se ganan monedas por nivel" % NIVEL_MAXIMO)

print("--- 2. Monedas de nivel -> Gacha")
j = nuevo(); j.ganar_xp(1 + 2)          # nivel 3 -> 40 monedas
check(j.monedas == 40, "llegar a nivel 3 da 40 monedas")
r = G.tirar(j, Rng([0.10], "Arco"))      # 0.10 -> herramienta
quedan = 40 - G.COSTO_TIRADA
check(r["categoria"] == "herramienta" and j.tiene_herramienta("Arco") and j.monedas == quedan, "con las monedas de nivel se paga una tirada (sale Arco, quedan %d)" % quedan)
j.monedas = G.COSTO_TIRADA - 1
check(G.tirar(j) is None, "con %d monedas no alcanza otra tirada" % j.monedas)

print("--- 3. Anillo del Gacha equipado + muerte con y sin totem")
j = nuevo(); j.monedas = 1000
G.tirar(j, Rng([0.5, 0.95], "vida"))     # anillo epico: vida
j.talismanes.equipar("vida"); j.recalcular_talismanes()
check(j.vida_max == 24, "anillo de vida del Gacha equipado: vida max 24")
G.tirar(j, Rng([0.5, 0.95], "vida"))
check(j.talismanes.anillos["vida"] == 2 and j.vida_max == 28, "otro anillo de vida del Gacha sube su nivel y el efecto al instante (28)")
G.tirar(j, Rng([0.80]))                   # totem (orden: herr .22, hab .13, anillo .41, totem .09, nada .15)
j.talismanes.equipar(TL.TOTEM)
nivel, mon = j.nivel, j.monedas
check(j.talismanes.usar_totem(), "el totem del Gacha equipado salva")
check(j.vida_max == 28 and j.talismanes.anillos["vida"] == 2 and j.monedas == mon, "tras salvarse: anillos, efectos y monedas intactos")
# muerte sin totem: un personaje nuevo (lo que hace reaparecer) no tiene nada del Gacha
j2 = nuevo()
check(j2.vida_max == 20 and not j2.talismanes.anillos and j2.monedas == 0 and len(j2.coleccion_herramientas) == 1,
      "morir sin totem: se pierden anillos, efectos, monedas y coleccion")

print("--- 4. Escudo (herramienta) + anillo de defensa fisica + cambio de herramienta")
j = nuevo(herr="Espada Larga", escudo=10)
esc = j.agregar_herramienta("Escudo")
for _ in range(7): j.talismanes.agregar_anillo("def_fisica")
j.talismanes.equipar("def_fisica"); j.recalcular_talismanes()
check(j.escudo_max == 30, "Espada + anillo nv7: 10 + 20 = 30")
j.equipar_herramienta(esc)
check(abs(j.escudo_max - (10 * (1 + esc.bonus_escudos) + 20)) < 1e-6, "con el Escudo: base x (1+pasiva) + anillo = %.1f" % j.escudo_max)
j.escudo = j.escudo_max
j.equipar_herramienta(j.coleccion_herramientas[0])
check(j.escudo == j.escudo_max == 30, "al volver a la espada el escudo se recorta a 30")

print("--- 5. Anillos de energia / cadencia al quitar y daño del arma")
j = nuevo()
for _ in range(10): j.talismanes.agregar_anillo("energia")
j.talismanes.equipar("energia"); j.recalcular_talismanes()
j.energia = j.energia_max
j.talismanes.quitar(0); j.recalcular_talismanes()
check(j.energia_max == 100 and j.energia == 100, "quitar el anillo de energia recorta la energia al maximo base")
for _ in range(5): j.talismanes.agregar_anillo("cadencia")
for _ in range(10): j.talismanes.agregar_anillo("fuerza")
j.talismanes.equipar("cadencia"); j.talismanes.equipar("fuerza"); j.recalcular_talismanes()
check(abs(j.herramienta.cadencia_efectiva(j) - (j.herramienta.cadencia + 1.5)) < 1e-9, "anillo de cadencia suma a la cadencia del arma")
arco = j.agregar_herramienta("Arco"); j.equipar_herramienta(arco)
check(abs(arco.calcular_dano(j) - round(j.fuerza * arco.multiplicador_dano * 1.10, 2)) < 0.011, "anillo de fuerza tambien sube el arco")

print("--- 6. Regeneracion legendaria con desangrado (-50% curacion)")
j = nuevo(); j.vida = 5
for _ in range(3): j.talismanes.agregar_anillo("regeneracion")
j.talismanes.equipar("regeneracion"); j.recalcular_talismanes()
aplicar_desangrado(j)
v = j.vida
j.actualizar_talismanes(1.0)
check(abs((j.vida - v) - 0.45) < 0.01, "nv3 cura 0.9/s, con desangrado la mitad (0.45): %.2f" % (j.vida - v))

print("--- 7. Habilidad del Gacha con huecos llenos + cambio en mitad de invocacion")
j = nuevo(); j.monedas = 30; j.energia = 300; j.energia_max = 300
G.tirar(j, Rng([0.30], "Paso 0"))
paso = next(h for h in j.coleccion_habilidades if h.nombre == "Paso 0")
check(paso not in j.habilidades, "con los 3 huecos llenos la habilidad del Gacha queda guardada")
lob = j.huecos_habilidades[1]; lob.intentar_activar(j)
crs = list(lob.criaturas)
j.equipar_habilidad(paso, 1)
check(all(not c.vivo for c in crs) and lob.estado == "COOLDOWN", "cambiar Invocar Lobos por Paso 0: los lobos desaparecen y queda en recarga")
j.equipar_habilidad(lob, 1)
check(lob.estado == "COOLDOWN" and lob in j.habilidades, "volver a ponerla no reinicia su recarga")

print("--- 8. Velocidad: anillo de viento + Destello + arma + autoapuntado")
j = nuevo(habs=("Destello",), herr="Espada Larga")
for _ in range(10): j.talismanes.agregar_anillo("viento")
j.talismanes.equipar("viento"); j.recalcular_talismanes()
j.herramienta.activa = True
j.actualizar_velocidad(); v1 = j.velocidad
check(abs(v1 - max(0.4, round(1 * (1 + 0.10 - j.herramienta.debuff_velocidad), 2))) < 1e-9, "viento +10%% se suma al debuff del arma (%.2f)" % v1)

print("--- 9. Totem: la pila y el hueco")
j = nuevo()
for _ in range(2): j.talismanes.agregar_totem()
j.talismanes.equipar(TL.TOTEM)
j.talismanes.usar_totem()
check(j.talismanes.totems == 1 and TL.TOTEM in j.talismanes.huecos, "gastar 1 de 2: el tótem sigue equipado (x1)")
j.talismanes.usar_totem()
check(j.talismanes.totems == 0 and TL.TOTEM not in j.talismanes.huecos and not j.talismanes.usar_totem(), "gastar el ultimo libera el hueco; sin tótems no salva")
j.monedas = 30
G.tirar(j, Rng([0.80]))
check(j.talismanes.totems == 1 and TL.TOTEM not in j.talismanes.huecos, "un totem nuevo del Gacha hay que volver a equiparlo")

print("--- 10. Fauna: XP + monedas de caza + monedas de nivel en un solo combate")
random.seed(2)
charcos = mundo.generar_charcos()
veg = mundo.SistemaVegetacion(mundo.CENTRO_MUNDO, mundo.RADIO_MUNDO, mundo.ZONA_SEGURA_SPAWN, charcos)
rocas = mundo.generar_rocas(list(charcos) + veg.arbustos + veg.arboles); veg.registrar_obstaculos(rocas)
sf = F.SistemaFauna(mundo.CENTRO_MUNDO, mundo.RADIO_MUNDO, veg, charcos, rocas)
sf.tomar_xp(); sf.tomar_monedas()
j = nuevo()
for l in sf.manadas[0].lobos: l.recibir_dano(999)
xp = sf.tomar_xp(); mon = sf.tomar_monedas()
niveles = j.ganar_xp(xp); j.monedas += mon
check(xp == 26 and niveles == 4 and 4 * 20 + 3 * 5 + 7 <= j.monedas <= 4 * 20 + 40, "manada completa: 26 XP -> 4 niveles (+80) + %d de caza = %d monedas" % (mon, j.monedas))
check(j.monedas >= 30 * 3, "una manada al inicio paga 3 tiradas o mas")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
