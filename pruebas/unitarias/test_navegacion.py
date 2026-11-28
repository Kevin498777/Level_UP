"""Pruebas sin ventana de la navegacion de los bots (Fase 4 del plan de NPC).

- 200 bots salen de 200 puntos al azar del mapa principal hacia 200 destinos al azar (de la misma
  zona conectada, a 300-1500 px): al menos el 98 % llega, ninguno se queda atascado mas de 3 s
  seguidos y ninguno pisa nunca una roca.
- Las rutas solo pasan por celdas libres y sus tramos rectos no cruzan nada.
- Destruir una roca abre el paso en la rejilla de paso.
Uso: python -B pruebas/unitarias/test_navegacion.py"""
import os
import random
import sys
import time
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
pygame.display.set_mode((10, 10))
import mundo
import mapa
import fauna as F
import herramientas as T
from navegacion import ColaRutas, Navegador, CELDA_PASO
from personaje import Personaje
from spawn import Casa
from limite_mundo import LIMITE

fallos = []
RUTAS = 200
DT = 1 / 60


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


datos = mapa.leer("principal")
charcos, veg, rocas = mapa.construir(datos)
rocas.extend(Casa(mundo.CENTRO_MUNDO).paredes)
fauna = F.SistemaFauna(LIMITE, veg, charcos, rocas)
fauna.conejos, fauna.venados, fauna.jabalies, fauna.zorros = [], [], [], []
fauna.manadas, fauna.osos, fauna.cocodrilos, fauna.lobos_solitarios = [], [], [], []
ctx = mundo.Contexto(rocas, veg, charcos, fauna, (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO))
ctx.rejilla_paso = mundo.cargar_rejilla_paso("principal", charcos, veg, rocas)
ctx.cola_rutas = ColaRutas(ctx.rejilla_paso)
rej = ctx.rejilla_paso
jugador = Personaje("Lejos", -99999, -99999, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], None)
rng = random.Random(7)


def punto_libre_al_azar():
    while True:
        p = LIMITE.punto_al_azar(300, rng)
        i, j = rej.celda_de(p)
        if rej.libre(i, j):
            return rej.centro_de(i, j)


def tramo_libre(a, b):
    """La linea entre dos celdas solo pisa celdas libres (el agua se puede cruzar: cuesta mas)."""
    (i0, j0), (i1, j1) = a, b
    n = max(abs(i1 - i0), abs(j1 - j0)) * 2
    return all(rej.libre(round(i0 + (i1 - i0) * k / n), round(j0 + (j1 - j0) * k / n)) for k in range(1, n))


def dentro_de_roca(c):
    zona = pygame.Rect(round(c.posicion.x) - 2, round(c.posicion.y) - 2, 4, 4)
    return any(r.rect.collidepoint(c.posicion) for r in ctx.obstaculos.rocas_en(zona))


# ------------------------------------------------------------ 1. Rutas: solo celdas libres
print("--- Rutas")
malas = 0
for _ in range(100):
    a, b = punto_libre_al_azar(), punto_libre_al_azar()
    if not rej.misma_zona(rej.celda_de(a), rej.celda_de(b)):
        continue
    puntos = rej.ruta(a, b) or []
    previo = rej.centro_de(*rej.libre_cercana(*rej.celda_de(a)))
    for p in puntos:
        if not rej.libre(*rej.celda_de(p)) or not tramo_libre(rej.celda_de(previo), rej.celda_de(p)):
            malas += 1
            break
        previo = p
comprobar(malas == 0, "100 rutas al azar: solo pasan por celdas libres y sus tramos no cruzan nada (%d malas)" % malas)

# ------------------------------------------------------------ 2. 200 bots caminando
print("--- %d bots caminando" % RUTAS)
t0 = time.perf_counter()
llegaron, atascados, en_roca, max_atasco = 0, 0, 0, 0.0
for k in range(RUTAS):
    while True:
        a = punto_libre_al_azar()
        ang = rng.uniform(0, 6.2832)
        b = a + pygame.Vector2(1, 0).rotate_rad(ang) * rng.uniform(300, 1500)
        if LIMITE.dentro(b, 300):
            ib = rej.celda_de(b)
            if rej.libre(*ib) and rej.misma_zona(rej.celda_de(a), ib):
                b = rej.centro_de(*ib)
                break
    bot = Personaje("Bot", a.x, a.y, 1, 3, 30, 2, 100, 0, (200, 0, 0), [], T.crear_herramienta("Espada Ligera"))
    ctx.combatientes = [bot]
    nav = Navegador(ctx.cola_rutas)
    nav.ir_a(bot, b, forzar=True)
    quieto, control, toco_roca = 0.0, pygame.Vector2(bot.posicion), False
    limite_f = int((a - b).length() / (bot.velocidad * 60) * 60 * 3) + 600
    for f in range(limite_f):
        ctx.cola_rutas.procesar()
        nav.actualizar(bot, DT, ctx.salir_a_hueco)
        mundo.actualizar_combatiente(bot, ctx, DT, jugador, [])
        if dentro_de_roca(bot):
            toco_roca = True
        if (bot.posicion - control).length() >= 12:
            quieto, control = 0.0, pygame.Vector2(bot.posicion)
        else:
            quieto += DT
        if (bot.posicion - b).length() <= CELDA_PASO:
            llegaron += 1
            break
        max_atasco = max(max_atasco, quieto)
    atascados += quieto > 3.0
    en_roca += toco_roca
segs = time.perf_counter() - t0
comprobar(llegaron >= RUTAS * 0.98, "llegan al destino %d de %d (%.1f %%, minimo 98 %%)" % (llegaron, RUTAS, 100 * llegaron / RUTAS))
comprobar(max_atasco <= 3.0, "ninguno se queda atascado mas de 3 s seguidos (maximo %.2f s)" % max_atasco)
comprobar(en_roca == 0, "ninguno pisa una roca (%d)" % en_roca)
print("     (%.1f s de prueba)" % segs)

# ------------------------------------------------------------ 3. Destruir una roca abre el paso
print("--- Rejilla de paso al destruir")
roca = next(r for r in rocas if r.rect.width >= 80 and getattr(r, "destructible", True)
            and LIMITE.dentro(pygame.Vector2(r.rect.center), 600) and not rej.libre(*rej.celda_de(pygame.Vector2(r.rect.center))))
centro = pygame.Vector2(roca.rect.center)
rocas.remove(roca)
veg.liberar_obstaculos([roca])
ctx.actualizar_paso()
comprobar(rej.libre(*rej.celda_de(centro)), "la celda de una roca destruida pasa a ser libre")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
