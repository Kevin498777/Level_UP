"""Pruebas sin ventana de la Fase 4 del plan de NPC (inteligencia y Humanos).

- Fauna: lo que remata un NPC le da la XP a ese NPC (no al jugador), su especie se regenera 5
  veces mas rapido hasta reponerlo (sin pasar el maximo) y un oso rematado por un NPC no deja
  orbes.
- Humanos: estadisticas de nivel 1, arma y 3 habilidades al azar, no consumen los orbes de los
  frutales; reaparecen a los 5 min al nivel 1; recuerdan que especie les mato.
- Cerebro: reparte los puntos con su estilo; una sola potenciada desde el nivel 20; nivel maximo
  40; nunca ataca a un personaje que no le ha golpeado; se defiende si le golpean; fuera de pelea
  se regenera mas rapido.
- Jugador: matar a un humano da 2 x nivel de XP, 5 + nivel monedas y +10 de "asesino", que se
  conserva al morir (la tumba no lo revierte).
Uso: python -B pruebas/unitarias/test_fase4.py"""
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
import mapa
import fauna as F
import tumba as TB
import cerebro as CB
import humanos as HU
from navegacion import ColaRutas, Navegador
from personaje import Personaje, NIVEL_MAXIMO
from spawn import Casa
from limite_mundo import LIMITE

fallos = []
DT = 1 / 60


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


datos = mapa.leer("principal")
charcos, veg, rocas = mapa.construir(datos)
rocas.extend(Casa(mundo.CENTRO_MUNDO).paredes)
fauna = F.SistemaFauna(LIMITE, veg, charcos, rocas)
ctx = mundo.Contexto(rocas, veg, charcos, fauna, (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO))
ctx.rejilla_paso = mundo.cargar_rejilla_paso("principal", charcos, veg, rocas)
ctx.cola_rutas = ColaRutas(ctx.rejilla_paso)
rng = random.Random(11)

# ------------------------------------------------------------ 1. Fauna y NPC
print("--- Fauna rematada por un NPC")
npc = HU.crear_humano(0, LIMITE.centro, rng)
venado = fauna.venados[0]
xp_antes, pendiente_antes = npc.xp, fauna.xp_pendiente
venado.vida, venado.vivo = 0, False
venado.ultimo_golpe_npc, venado.ultimo_golpe_por = True, npc
fauna._recoger_muertes()
comprobar(abs(npc.xp - xp_antes - venado.xp) < 1e-9 or npc.nivel > 1, "la XP del venado es para el NPC que lo remato (+%g)" % venado.xp)
comprobar(fauna.xp_pendiente == pendiente_antes, "el jugador no gana nada")
comprobar(fauna.deuda_npc.get("Venado") == 1 and fauna._ritmo("Venado") == F.RITMO_TRAS_NPC,
          "la especie queda en deuda y se regenera x%d" % F.RITMO_TRAS_NPC)
comprobar(fauna._ritmo("Jabali") == 1, "las demas especies siguen a su ritmo")
fauna._pagar("Venado")
comprobar(fauna.deuda_npc.get("Venado") == 0 and fauna._ritmo("Venado") == 1, "al nacer uno se repone y vuelve al ritmo normal")

# Reproduccion x5 real: con deuda nace un venado en 60/5 s (sin pasar el maximo)
fauna.venados = [v for v in fauna.venados if v.vivo][:10]
fauna._t_repro_venado = 0.0
fauna.deuda_npc["Venado"] = 1
jugador = Personaje("Lejos", -99999, -99999, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], None)
vista = pygame.Rect(-100000, -100000, 10, 10)
n0 = len(fauna.venados)
for _ in range(int(F.VENADO_REPRO_INTERVALO / F.RITMO_TRAS_NPC / 0.5) + 2):
    fauna.actualizar(0.5, jugador, vista, (), [])
comprobar(len(fauna.venados) == n0 + 1 and fauna.deuda_npc["Venado"] == 0,
          "con deuda nace un venado en %g s (no en %g s) y la deuda se paga" % (F.VENADO_REPRO_INTERVALO / F.RITMO_TRAS_NPC, F.VENADO_REPRO_INTERVALO))
fauna.venados = fauna.venados + [F.Venado(v.posicion.x, v.posicion.y) for v in fauna.venados * 10][:F.VENADO_MAX - len(fauna.venados)]
fauna.deuda_npc["Venado"] = 3
fauna._t_repro_venado = 0.0
for _ in range(60):
    fauna.actualizar(0.5, jugador, vista, (), [])
comprobar(len(fauna.venados) <= F.VENADO_MAX, "nunca pasa del maximo de venados (%d de %d)" % (len(fauna.venados), F.VENADO_MAX))

# Oso rematado por un NPC: sin orbes; reaparece 5 veces antes
oso = fauna.osos[0]
oso.estado = "ataca"
oso.recibir_dano(oso.vida + 10)
oso.ultimo_golpe_npc, oso.ultimo_golpe_por = True, npc
fauna._recoger_muertes()
comprobar(oso.orbe is None and not oso.orbes_extra, "un oso rematado por un NPC no deja orbes")
oso2 = fauna.osos[1]
oso2.estado = "ataca"
oso2.recibir_dano(oso2.vida + 10)
fauna._recoger_muertes()
comprobar(oso2.orbe is not None, "el que mata el jugador si los deja")
oso._t_reaparicion = 0.0
for _ in range(int(F.OSO_REAPARICION / F.RITMO_TRAS_NPC / 0.5) + 2):
    fauna.actualizar(0.5, jugador, vista, (), [])
comprobar(fauna.osos[0] is not oso and fauna.osos[0].vivo, "el oso reaparece en %g s (no en %g s)" % (F.OSO_REAPARICION / F.RITMO_TRAS_NPC, F.OSO_REAPARICION))

# ------------------------------------------------------------ 2. Humanos
print("--- Humanos")
puntos = datos.get("aparicion", {}).get("Humanos", [])
comprobar(len(puntos) == HU.HUMANOS_CANTIDAD, "el mapa tiene %d puntos de aparicion de Humanos al norte" % len(puntos))
comprobar(all(p[1] < LIMITE.centro.y for p in puntos), "todos en la mitad norte")
pob = HU.PoblacionHumanos(ctx, puntos, random.Random(5))
humanos = [c for c in ctx.combatientes if getattr(c, "raza", "") == "Humanos"]
comprobar(len(humanos) == HU.HUMANOS_CANTIDAD, "aparecen %d humanos" % len(humanos))
h = humanos[0]
comprobar((h.nivel, h.vida_max, h.fuerza, h.energia_max) == (1, 30, 2, 100), "nivel 1 con las estadisticas iniciales del jugador")
comprobar(all(len(c.habilidades) == 3 and c.herramienta is not None for c in humanos), "cada uno con un arma y 3 habilidades")
comprobar(len(set((c.herramienta.nombre, tuple(x.nombre for x in c.habilidades)) for c in humanos)) > 1, "el equipo es al azar")
comprobar(len(set(c.cerebro.estilo for c in humanos)) > 1 and all(c.cerebro.estilo in CB.ESTILOS for c in humanos),
          "estilos de reparto al azar: %s" % sorted(set(c.cerebro.estilo for c in humanos)))

# No consumen los orbes de un frutal
import vegetacion as V
frutal = next(a for a in veg.arbustos if a.tipo == V.TIPO_FRUTAL)
frutal.orbes = [pygame.Vector2(frutal.rect.center)]
orbes = len(frutal.orbes)
h.vida = 10
h.posicion = pygame.Vector2(frutal.orbes[0])
veg.actualizar_personaje(DT, h, [frutal])
comprobar(len(frutal.orbes) == orbes and h.vida == 10, "un humano no consume los orbes de un frutal")

# Muerte y reaparicion
lobo = fauna.manadas[0].lobos[0]
h.ultimo_agresor, h.t_agresor = lobo, 5.0
h.vida = 0
for caido in mundo.retirar_combatientes_muertos(ctx):
    pob.murio(caido)
comprobar(h not in ctx.combatientes and len(pob.vivos) == HU.HUMANOS_CANTIDAD - 1, "muere y deja el mundo")
pob.actualizar(HU.REAPARICION - 1)
comprobar(len(pob.vivos) == HU.HUMANOS_CANTIDAD - 1, "a los %g s todavia no ha vuelto" % (HU.REAPARICION - 1))
pob.actualizar(1.5)
nuevo = pob.vivos.get(h.indice_humano)
comprobar(nuevo is not None and nuevo is not h and nuevo.nivel == 1, "a los %g s reaparece al nivel 1" % HU.REAPARICION)
comprobar(nuevo is not None and any((nuevo.posicion - pygame.Vector2(p)).length() < 1 for p in puntos), "en uno de los puntos de aparicion")
comprobar(nuevo is not None and nuevo.cerebro.temidos.get("Lobo") == 1, "recuerda que le mato un lobo")
comprobar(nuevo is not None and nuevo.cerebro.nivel_presa(lobo) == CB.NIVEL_PRESA["Lobo"] + CB.EVITAR_SI_MATO,
          "y ahora los evita hasta %d niveles mas" % CB.EVITAR_SI_MATO)

# ------------------------------------------------------------ 3. Cerebro
print("--- Cerebro")
for estilo in CB.ESTILOS:
    p = HU.crear_humano(1, LIMITE.centro, random.Random(estilo))
    b = CB.CerebroBot(Navegador(ctx.cola_rutas), random.Random(1), estilo=estilo)
    for _ in range(60):
        p.subir_nivel()
    b._gastar_puntos(p)
    potenciadas = sum(1 for x in p.habilidades if getattr(x, "potenciada_desbloqueada", False))
    comprobar(p.nivel == NIVEL_MAXIMO and p.puntos_mejora < 4 and potenciadas == 1,
              "estilo %-11s: nivel %d, puntos sin gastar %d, %d potenciada (vida %d, fuerza %d, energia %d)"
              % (estilo, p.nivel, p.puntos_mejora, potenciadas, p.vida_max, p.fuerza, p.energia_max))
p19 = HU.crear_humano(2, LIMITE.centro, random.Random(3))
b19 = CB.CerebroBot(Navegador(ctx.cola_rutas), random.Random(2))
for _ in range(18):
    p19.subir_nivel()
b19._gastar_puntos(p19)
comprobar(p19.nivel == 19 and not any(getattr(x, "potenciada_desbloqueada", False) for x in p19.habilidades),
          "antes del nivel %d no tiene potenciada" % CB.NIVEL_POTENCIADA)

# Nunca ataca al jugador si no le golpea; si le golpea, se defiende
ctx.combatientes = []
yo = Personaje("Jugador", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], None)
bot = HU.crear_humano(3, (0, 0), random.Random(8))
ctx.agregar_combatiente(bot, CB.CerebroBot(Navegador(ctx.cola_rutas), random.Random(4)))
punto = None
for p in puntos:
    zona = pygame.Rect(0, 0, 1600, 1600)
    zona.center = (round(p[0]), round(p[1]))
    if not fauna.animales_con_vida(zona):
        punto = pygame.Vector2(p)
        break
punto = punto or pygame.Vector2(puntos[0])
bot.posicion = pygame.Vector2(punto)
yo.posicion = punto + pygame.Vector2(60, 0)
vida_yo = yo.vida
for f in range(600):
    bot.cerebro(bot, ctx, yo)
    bot.cerebro.fotograma(bot, ctx, DT)
    ctx.cola_rutas.procesar()
    mundo.actualizar_combatiente(bot, ctx, DT, yo, [])
    yo.posicion = bot.posicion + pygame.Vector2(60, 0)
comprobar(yo.vida == vida_yo and bot.cerebro.estado != CB.DEFENDERSE, "10 s junto al jugador sin que le golpee: no le ataca")
import talismanes as TL
TL.marcar_agresor(bot, yo)
bot.vida -= 3
bot.cerebro(bot, ctx, yo)
comprobar(bot.cerebro.estado == CB.DEFENDERSE and bot.cerebro.agresor is yo, "si el jugador le golpea, se defiende de el")

# Regeneracion fuera de pelea
r = HU.crear_humano(4, (0, 0), random.Random(9))
r.vida = 10
cb = CB.CerebroBot(Navegador(ctx.cola_rutas), random.Random(6))
cb.t_sin_pelea = CB.FUERA_DE_PELEA_TRAS
for _ in range(60):
    cb.fotograma(r, ctx, DT)
comprobar(abs(r.vida - (10 + r.vida_max * CB.REGEN_VIDA_FUERA)) < 0.05,
          "fuera de pelea recupera el %d %% de su vida por segundo (10 -> %.2f)" % (CB.REGEN_VIDA_FUERA * 100, r.vida))

# ------------------------------------------------------------ 4. Recompensa y asesino
print("--- Asesino")
victima = HU.crear_humano(5, (0, 0), random.Random(1))
for _ in range(7):
    victima.subir_nivel()
comprobar(HU.recompensa_por_humano(victima) == (16, 13), "matar a un humano de nivel 8: 16 XP y 13 monedas")
comprobar(getattr(Personaje("X", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 0), [], None), "asesino", None) == 0, "el jugador empieza con asesino 0")
comprobar("asesino" in TB.CAMPOS_TRANSITORIOS, "la tumba no revierte el asesino")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
