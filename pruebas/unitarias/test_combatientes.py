"""Pruebas sin ventana de la Fase 1 del plan de NPC: cualquier personaje es un combatiente.

- Dos combatientes: un segundo Personaje movido por guion golpea al jugador con cada arma y le
  lanza las habilidades de dano; el jugador recibe dano, empuje y efectos (veneno, quemadura,
  corrosion, inmovilizacion, sueno, huida) igual que de un enemigo.
- Terreno para todos: en el agua va mas lento, en la zona profunda pierde vida y dentro de un
  arbusto queda oculto (la fauna no lo detecta).
- Fauna: un lobo persigue al combatiente no jugador mas cercano y detectable.
- Intenciones: un combatiente controlado no ataca ni se mueve.
Uso: python -B pruebas/unitarias/test_combatientes.py"""
import math
import os
import random
import sys
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
pygame.display.set_mode((10, 10))
import mundo
import fauna as F
import habilidades as H
import herramientas as T
from personaje import Personaje

fallos = []
DT = 1 / 60


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


random.seed(4)
charcos, vegetacion, rocas = mundo.generar_terreno()
fauna = F.SistemaFauna(mundo.LIMITE, vegetacion, charcos, rocas)
LIMITES = (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO)


def lugar_libre():
    """Punto del mundo sin rocas, arboles, arbustos, agua ni animales cerca."""
    rng = random.Random(9)
    while True:
        p = mundo.CENTRO_MUNDO + pygame.Vector2(rng.uniform(-6000, 6000), rng.uniform(-6000, 6000))
        zona = pygame.Rect(p.x - 400, p.y - 400, 800, 800)
        if (not any(r.rect.colliderect(zona) for r in rocas)
                and not any(a.rect.colliderect(zona) for a in vegetacion.arbustos + vegetacion.arboles)
                and not any(c.rect.colliderect(zona) for c in charcos)
                and not fauna.animales_con_vida(zona.inflate(800, 800))):
            return p


BASE = lugar_libre()


def personaje(nombre, x, y, arma="Espada Larga", habs=(), vida=200):
    hs = [H.crear_habilidad(n) for n in habs]
    for i, h in enumerate(hs):
        h.asignar_tecla((pygame.K_2, pygame.K_3, pygame.K_4)[i], "234"[i])
    p = Personaje(nombre, x, y, 1, 3, vida, 4, 300, 0, (200, 80, 80), hs, T.crear_herramienta(arma))
    return p


def escena(arma="Espada Larga", habs=(), distancia=45, vida_jugador=200):
    """Jugador quieto y un combatiente al oeste mirandolo (hacia el este)."""
    ctx = mundo.Contexto(rocas, vegetacion, charcos, fauna, LIMITES)
    j = personaje("Jugador", BASE.x, BASE.y, vida=vida_jugador)
    npc = ctx.agregar_combatiente(personaje("NPC", BASE.x - distancia, BASE.y, arma, habs))
    npc.angulo = 90.0
    return ctx, j, npc


def correr(ctx, j, npc, segundos, antes=None):
    """Un fotograma = el NPC hace su turno y el jugador (sin intenciones) el suyo."""
    for i in range(int(segundos / DT)):
        if antes:
            antes(i)
        npc.energia = npc.energia_max
        mundo.actualizar_combatiente(npc, ctx, DT, j)
        mundo.actualizar_combatiente(j, ctx, DT, j)


# ------------------------------------------------------------ 1. Armas contra el jugador
print("--- Armas de un combatiente contra el jugador")
for arma in ("Espada Ligera", "Espada Larga", "Mandoble", "Dagas Simples"):
    ctx, j, npc = escena(arma, distancia=30 if arma == "Dagas Simples" else 45)
    npc.alternar_arma()
    npc.mantiene_ataque = True
    pos0 = pygame.Vector2(j.posicion)
    maximo = [0.0]
    # el jugador quieto vuelve andando a su destino: se mide el mayor desplazamiento
    correr(ctx, j, npc, 1.0, antes=lambda i: maximo.__setitem__(0, max(maximo[0], (j.posicion - pos0).length())))
    comprobar(j.vida < j.vida_max and maximo[0] > 1,
              "%-13s: el jugador pierde vida (%g) y sale empujado (%.0f px)" % (arma, j.vida_max - j.vida, maximo[0]))
# Invulnerabilidad: dos golpes seguidos dentro de INVULNERABILIDAD_TRAS_GOLPE no cuentan dos veces
ctx, j, npc = escena("Dagas Simples", distancia=30)
npc.alternar_arma(); npc.mantiene_ataque = True
golpes = []
_rd = j.recibir_dano
j.recibir_dano = lambda *a, **k: golpes.append(1) or _rd(*a, **k)
correr(ctx, j, npc, 0.45)
comprobar(len(golpes) == 1, "tras un golpe el jugador es invulnerable un momento (%d golpes en 0.45 s)" % len(golpes))
# Escudo desenfundado: bloquea y repele al atacante
ctx, j, npc = escena("Espada Larga")
j.equipar_herramienta(j.agregar_herramienta("Escudo")); j.alternar_arma(); j.angulo = 270.0   # mira al oeste
npc.alternar_arma(); npc.mantiene_ataque = True
p_npc = pygame.Vector2(npc.posicion)
correr(ctx, j, npc, 0.5)
comprobar(j.vida == j.vida_max and (npc.posicion - p_npc).length() > 1,
          "el Escudo del jugador bloquea el golpe y repele al combatiente")
# Arco: cargar y soltar
ctx, j, npc = escena("Arco", distancia=90)
npc.alternar_arma()
npc.pulsar_ataque()
correr(ctx, j, npc, 1.6)
npc.soltar_ataque()
correr(ctx, j, npc, 1.0)
comprobar(j.vida < j.vida_max, "Arco: la flecha del combatiente hiere al jugador (%g)" % (j.vida_max - j.vida))
# Corroido: pega menos
ctx, j, npc = escena("Mandoble")
npc.alternar_arma(); npc.mantiene_ataque = True
H.aplicar_corrosion(npc, 0.30, 60)
npc.corrosion.nivel = 0.30
correr(ctx, j, npc, 0.3)
ctx2, j2, npc2 = escena("Mandoble")
npc2.alternar_arma(); npc2.mantiene_ataque = True
correr(ctx2, j2, npc2, 0.3)
d1, d2 = j.vida_max - j.vida, j2.vida_max - j2.vida
comprobar(d2 > 0 and abs(d1 - d2 * 0.7) < 0.05, "corroido al 30 %%: su golpe hace un 30 %% menos (%g frente a %g)" % (d1, d2))

# ------------------------------------------------------------ 2. Habilidades contra el jugador
print("--- Habilidades de un combatiente contra el jugador")


def usar(nombre, distancia=120, mantener=0.0, potenciada=False, segundos=1.5, antes=None):
    ctx, j, npc = escena("Espada Ligera", (nombre,), distancia)
    hab = npc.habilidades[0]
    if potenciada:
        for _ in range(29):
            npc.subir_nivel()
        while hab.nivel < hab.nivel_max and hab.subir_nivel():
            pass
        npc.potenciar_habilidad(hab.nombre)
        while hab.nivel < hab.nivel_max and hab.subir_nivel():
            pass
    if antes:
        antes(ctx, j, npc, hab)
    else:
        npc.pulsar_habilidad(hab)
        if mantener:
            correr(ctx, j, npc, mantener)
        npc.soltar_habilidad(hab)
    correr(ctx, j, npc, segundos)
    return ctx, j, npc, hab


_, j, _, _ = usar("Disparo Veloz")
comprobar(j.vida < j.vida_max, "Disparo Veloz hiere al jugador (%g)" % (j.vida_max - j.vida))
_, j, _, _ = usar("Carga de Fuego", mantener=1.2)
comprobar(j.quemadura is not None or j.vida < j.vida_max - 5, "Carga de Fuego hiere y quema al jugador (%g)" % (j.vida_max - j.vida))
_, j, _, _ = usar("Disparo Venenoso", segundos=3.0)
comprobar(j.veneno is not None and j.vida < j.vida_max, "Disparo Venenoso envenena al jugador (%g)" % (j.vida_max - j.vida))
_, j, _, _ = usar("Disparo Venenoso", potenciada=True, segundos=3.0)
comprobar(j.corrosion is not None and j.corrosion.nivel > 0, "Corrosion corroe al jugador (nivel %.2f)" %
          (j.corrosion.nivel if j.corrosion else 0))
v_corr = j.velocidad
_, j, _, _ = usar("Cortar")
comprobar(j.vida < j.vida_max, "Cortar: la cuchilla hiere al jugador (%g)" % (j.vida_max - j.vida))
_, j, _, _ = usar("Onda Sonora", segundos=0.8)
comprobar(j.vida < j.vida_max and j.ralentizacion > 0, "Onda Sonora hiere y ralentiza al jugador (-%d %%)" % round(j.ralentizacion * 100))
_, j, _, _ = usar("Aura Electrica", distancia=40, segundos=2.0)
comprobar(j.vida < j.vida_max, "Aura Electrica hiere al jugador de al lado (%g)" % (j.vida_max - j.vida))


def poner_telarana(ctx, j, npc, hab):
    npc.pulsar_habilidad(hab)            # invoca la arana
    correr(ctx, j, npc, 0.2)
    npc.pulsar_habilidad(hab)            # tecla mantenida: modo combate
    hab.modo_combate = True
    npc.ordenar_sombras(pygame.Vector2(j.posicion), [j])
    npc.soltar_habilidad(hab)
    hab.modo_combate = False


ctx, j, npc, hab = usar("Sombra Araña", distancia=80, segundos=1.5, antes=poner_telarana)
comprobar(j.inmovilizado is not None, "Sombra Araña: la telarana inmoviliza al jugador")
j.mover_a(j.posicion + pygame.Vector2(300, 0))
p0 = pygame.Vector2(j.posicion)
correr(ctx, j, npc, 0.5)
comprobar((j.posicion - p0).length() < 1, "inmovilizado no se mueve aunque quiera (intencion mover_a)")


def palabra(clave):
    def antes(ctx, j, npc, hab):
        comprobar(npc.elegir_palabra(clave), "Palabras Malditas sin ruleta: el combatiente pronuncia '%s'" % clave)
    return antes


_, j, _, _ = usar("Onda Sonora", potenciada=True, segundos=0.8, antes=palabra("duerme"))
comprobar(j.dormido is not None and j.controlado, "Duerme: el jugador se queda dormido (no actua)")
_, j, npc, _ = usar("Onda Sonora", potenciada=True, segundos=0.8, antes=palabra("huye"))
lejos0 = (j.posicion - npc.posicion).length()
comprobar(j.huida is not None, "Huye: el jugador queda asustado")
ctx3 = mundo.Contexto(rocas, vegetacion, charcos, fauna, LIMITES)
for _ in range(60):
    mundo.combatiente_estado(j, ctx3, DT, [], [])
comprobar((j.posicion - npc.posicion).length() > lejos0 + 20, "Huye: el jugador se aleja de quien lo asusto")
j.alternar_arma(); j.pulsar_ataque()
comprobar(not j.herramienta.golpeando, "asustado no puede atacar (intencion pulsar_ataque)")


def lobos(ctx, j, npc, hab):
    npc.pulsar_habilidad(hab)
    correr(ctx, j, npc, 0.3)
    hab.modo_combate = True
    npc.ordenar_sombras(pygame.Vector2(j.posicion), [j])
    hab.modo_combate = False


_, j, _, _ = usar("Invocar Lobos", distancia=150, segundos=4.0, antes=lobos)
comprobar(j.vida < j.vida_max, "Invocar Lobos: las sombras del combatiente atacan al jugador (%g)" % (j.vida_max - j.vida))

# ------------------------------------------------------------ 3. Terreno para todos
print("--- Terreno para un combatiente no jugador")
ctx, j, npc = escena()
lago = next(c for c in charcos if getattr(c, "es_lago_profundo", False))
borde = pygame.Vector2(lago.centro) + pygame.Vector2(lago.radio * 0.75, 0)
while not lago.contiene(borde) or lago.en_zona_peligro(borde):
    borde.x -= 5
npc.posicion = pygame.Vector2(borde); npc.destino = pygame.Vector2(borde)
mundo.combatiente_estado(npc, ctx, DT, [], [])
v_agua = npc.velocidad
npc.posicion = pygame.Vector2(BASE); npc.destino = pygame.Vector2(BASE)
mundo.combatiente_estado(npc, ctx, DT, [], [])
comprobar(npc.en_agua is False and v_agua < npc.velocidad, "en el agua va mas lento (%.2f frente a %.2f)" % (v_agua, npc.velocidad))
centro = pygame.Vector2(lago.centro)
npc.posicion = pygame.Vector2(centro); npc.destino = pygame.Vector2(centro)
v0 = npc.vida
for _ in range(int(2.1 / DT)):
    mundo.combatiente_estado(npc, ctx, DT, [], [])
    npc.posicion.update(centro); npc.destino.update(centro)
comprobar(npc.en_agua_profunda and v0 - npc.vida == 2 * mundo.DANO_LAGO_PROFUNDO,
          "en la zona profunda pierde %d de vida por segundo" % mundo.DANO_LAGO_PROFUNDO)
import vegetacion as V
arbusto = next(a for a in vegetacion.arbustos if a.tipo == V.TIPO_ESCONDITE and a.puede_entrar(npc))
npc.posicion = pygame.Vector2(arbusto.centro)
vegetacion.actualizar_personaje(DT, npc)
comprobar(npc.oculto and not npc.detectable, "dentro de un arbusto queda oculto y no es detectable")

# ------------------------------------------------------------ 4. Fauna
print("--- Fauna contra un combatiente no jugador")
ctx, j, npc = escena()
j.posicion = pygame.Vector2(BASE.x + 3000, BASE.y)             # el jugador, lejos
lobo = F.LoboSolitario(BASE.x - 200, BASE.y)       # a 155 px: dentro de su deteccion (200)
fauna.lobos_solitarios.append(lobo)
vista = mundo.vista_de(npc)
d0 = (lobo.posicion - npc.posicion).length()
for _ in range(90):
    fauna.actualizar(DT, j, vista, (), ctx.combatientes)
comprobar((lobo.posicion - npc.posicion).length() < d0 - 30,
          "un lobo solitario persigue al combatiente detectable (%.0f -> %.0f px)" % (d0, (lobo.posicion - npc.posicion).length()))
for _ in range(240):
    fauna.actualizar(DT, j, vista, (), ctx.combatientes)
comprobar(npc.vida < npc.vida_max, "y le hace dano (%g)" % (npc.vida_max - npc.vida))
fauna.lobos_solitarios.remove(lobo)
# Oculto: no lo detecta
ctx, j, npc = escena()
j.posicion = pygame.Vector2(BASE.x + 3000, BASE.y)
npc.oculto = True
lobo = F.LoboSolitario(BASE.x - 200, BASE.y)       # a 155 px: dentro de su deteccion (200)
fauna.lobos_solitarios.append(lobo)
d0 = (lobo.posicion - npc.posicion).length()
for _ in range(90):
    fauna.actualizar(DT, j, mundo.vista_de(npc), (), ctx.combatientes)
comprobar(npc.vida == npc.vida_max and (lobo.posicion - npc.posicion).length() > d0 - 30,
          "al combatiente oculto en un arbusto el lobo no lo persigue")
fauna.lobos_solitarios.remove(lobo)

# ------------------------------------------------------------ 5. Recompensas
print("--- Lo que mata un NPC no da XP ni monedas al jugador")


def cazar(quien_remata):
    """Un venado de 1 de vida junto a los dos; lo golpea quien_remata ('npc' o 'jugador')."""
    ctx, j, npc = escena("Espada Larga")
    fauna.tomar_xp(); fauna.tomar_monedas()
    atacante = npc if quien_remata == "npc" else j
    venado = F.Venado(atacante.posicion.x, atacante.posicion.y + 20)     # justo al sur del atacante
    venado.vida = 1
    fauna.venados.append(venado)
    atacante.alternar_arma()
    atacante.angulo = 180.0                                     # mira al sur (al venado)
    atacante.mantiene_ataque = True
    for _ in range(40):
        if quien_remata == "npc":
            mundo.actualizar_combatiente(npc, ctx, DT, j)
        else:
            enemigos = fauna.animales_con_vida(mundo.vista_de(j))
            antes = mundo.salud_de(enemigos)
            mundo.combatiente_golpes(j, DT, enemigos)
            mundo.marcar_autor(antes, False)
    fauna.actualizar(DT, j, mundo.vista_de(j))                 # cuenta las muertes
    if venado in fauna.venados:
        fauna.venados.remove(venado)
    return venado.vivo, fauna.tomar_xp()


vivo, xp = cazar("npc")
comprobar(not vivo and xp == 0, "venado muerto por un NPC: el jugador no gana XP (%g)" % xp)
vivo, xp = cazar("jugador")
comprobar(not vivo and xp > 0, "venado muerto por el jugador: si gana XP (%g)" % xp)
import vendedores as VEND
sv = VEND.SistemaVendedores.__new__(VEND.SistemaVendedores)
falso = lambda npc_: type("V", (), {"muerto_por_fauna": False, "ultimo_golpe_npc": npc_})()
sv._muertos = [falso(True), falso(False)]
comprobar(sv.tomar_recompensa() == (VEND.XP_VENDEDOR, VEND.MONEDAS_VENDEDOR),
          "vendedor rematado por un NPC: sin recompensa (solo cuenta el que mato el jugador)")

# ------------------------------------------------------------ 6. Muerte de un combatiente
print("--- Muerte")
ctx, j, npc = escena()
npc.vida = 0
retirados = mundo.retirar_combatientes_muertos(ctx)
comprobar(retirados == [npc] and not ctx.combatientes, "un combatiente sin vida sale del mundo")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
