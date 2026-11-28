"""Prueba de humo de la inteligencia de los bots (Fase 4 del plan de NPC).

Bots con cerebro (como los Humanos) pelean contra fauna real con las 6 armas y las 15
habilidades, primero normales y luego potenciadas: comprueba que cada arma hace dano y que cada
habilidad se usa al menos una vez (Defenderse, Cazar, Huir y Curarse), sin errores.
Uso: python -B pruebas/humo/humo_bots.py"""
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
import habilidades as H
import herramientas as T
import talismanes as TL
import cerebro as CB
from navegacion import ColaRutas, Navegador
from personaje import Personaje
from spawn import Casa
from limite_mundo import LIMITE

fallos = []
DT = 1 / 60
SEGUNDOS = 45
# (arma, 3 habilidades): cubren las 6 armas y las 15 habilidades
EQUIPOS = (
    ("Espada Ligera", ("Destello", "Burst de Fuerza", "Disparo Veloz")),
    ("Espada Larga", ("Cortar", "Onda Sonora", "Invocar Conejos")),
    ("Mandoble", ("Invocar Lobos", "Carga de Fuego", "Aura Electrica")),
    ("Dagas Simples", ("Reforzamiento Mágico", "Regeneración Inversa", "Golpe de Suerte")),
    ("Escudo", ("Sombra Araña", "Paso 0", "Disparo Venenoso")),
    ("Arco", ("Disparo Veloz", "Carga de Fuego", "Onda Sonora")),
)


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


random.seed(3)
datos = mapa.leer("principal")
charcos, veg, rocas = mapa.construir(datos)
rocas.extend(Casa(mundo.CENTRO_MUNDO).paredes)
fauna = F.SistemaFauna(LIMITE, veg, charcos, rocas)
ctx = mundo.Contexto(rocas, veg, charcos, fauna, (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO))
ctx.rejilla_paso = mundo.cargar_rejilla_paso("principal", charcos, veg, rocas)
ctx.cola_rutas = ColaRutas(ctx.rejilla_paso)
rej = ctx.rejilla_paso
jugador = Personaje("Lejos", -99999, -99999, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], None)
jugador.inspector = True


def lugar_libre(rng):
    """Celda libre sin agua cerca, en zona de pradera."""
    while True:
        p = LIMITE.punto_al_azar(1500, rng)
        zona = pygame.Rect(0, 0, 500, 500)
        zona.center = (round(p.x), round(p.y))
        if rej.libre(*rej.celda_de(p)) and not any(r.rect.colliderect(zona) for r in ctx.obstaculos.rocas_en(zona)) \
                and not any(c.rect.colliderect(zona) for c in charcos):
            return pygame.Vector2(p)


def bot(arma, nombres, nivel, potenciadas, x, y, rng):
    habs = [H.crear_habilidad(n) for n in nombres]
    for h, (tecla, t) in zip(habs, ((pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4"))):
        h.asignar_tecla(tecla, t)
    p = Personaje("Bot " + arma, x, y, 1, 1, 30, 2, 100, 0, (200, 160, 120), habs, T.crear_herramienta(arma))
    p.toma_objetos = False
    cb = CB.CerebroBot(Navegador(ctx.cola_rutas), random.Random(rng.random()), estilo="equilibrado")
    cb.potenciada_elegida = True                # la prueba decide las potenciadas
    for _ in range(nivel - 1):
        p.subir_nivel()
    if potenciadas:
        for h in habs:
            p.potenciar_habilidad(h.nombre)
    cb._gastar_puntos(p)
    return ctx.agregar_combatiente(p, cb)


def ronda(potenciadas, semilla):
    rng = random.Random(semilla)
    ctx.combatientes = []
    usadas = {}
    danos = {}
    for k, (arma, nombres) in enumerate(EQUIPOS):
        base = lugar_libre(rng)
        b = bot(arma, nombres, 30 if potenciadas else 12, potenciadas, base.x, base.y, rng)
        usadas[id(b)] = set()
        danos[id(b)] = 0
        # Enemigos que le atacan: dos lobos solitarios y un jabali
        for dx in (-160, 160):
            ls = F.LoboSolitario(base.x + dx, base.y + 120)
            fauna.lobos_solitarios.append(ls)
        fauna.jabalies.append(F.Jabali(base.x, base.y - 180))
    vista = pygame.Rect(0, 0, 1, 1)
    fases = {CB.DEFENDERSE: set(), CB.CAZAR: set(), CB.HUIR: set(), CB.CURARSE: set()}
    for f in range(int(SEGUNDOS / DT)):
        if f == int(SEGUNDOS * 0.6 / DT):
            for c in ctx.combatientes:          # mitad de la pelea: muy heridos (huir y curarse)
                c.vida = max(1, c.vida_max * 0.2)
        zona = pygame.Rect(0, 0, 1, 1)
        for c in ctx.combatientes:
            zona.union_ip(pygame.Rect(round(c.posicion.x) - 900, round(c.posicion.y) - 900, 1800, 1800))
        vista = zona
        fauna.actualizar(DT, jugador, vista, (), ctx.combatientes)
        jugador.posicion = pygame.Vector2(vista.center)
        mundo.actualizar_otros_combatientes(ctx, DT, jugador, zona)
        for c in ctx.combatientes:
            fases.setdefault(c.cerebro.estado, set()).add(id(c))
            for h in c.habilidades:
                if h.estado != "LISTA" or getattr(h, "cargando", False) or getattr(h, "canalizando", False):
                    usadas[id(c)].add(h.nombre)
        for a in fauna.animales_con_vida(zona):
            por = getattr(a, "ultimo_golpe_por", None)
            if por is not None and id(por) in danos:
                danos[id(por)] += 1
        mundo.retirar_combatientes_muertos(ctx)
    return usadas, danos, fases


for potenciadas in (False, True):
    titulo = "potenciadas (nivel 30)" if potenciadas else "normales (nivel 12)"
    print("--- Habilidades %s" % titulo)
    todas, golpean = set(), 0
    for semilla in range(3):
        fauna.lobos_solitarios = fauna.lobos_solitarios[:6]
        fauna.jabalies = fauna.jabalies[:10]
        lista_bots = []
        usadas, danos, fases = ronda(potenciadas, semilla + (10 if potenciadas else 0))
        for v in usadas.values():
            todas |= v
        golpean = max(golpean, sum(1 for v in danos.values() if v > 0))
    faltan = sorted(set(n for _, ns in EQUIPOS for n in ns) - todas)
    comprobar(not faltan, "los bots usan las %d habilidades %s%s" % (len(set(n for _, ns in EQUIPOS for n in ns)), titulo,
                                                                    "" if not faltan else " (faltan: %s)" % ", ".join(faltan)))
    comprobar(golpean >= 5, "%d de 6 bots hacen dano a la fauna (el del Escudo puede no hacerlo)" % golpean)
    comprobar(all(fases.get(e) for e in (CB.DEFENDERSE, CB.HUIR, CB.CURARSE)),
              "pasan por Defenderse, Huir y Curarse")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
