"""Pruebas sin ventana de la Fase 3 del plan de NPC (rendimiento).

- Rejilla de obstaculos: da exactamente lo mismo que recorrer las listas (miles de posiciones al
  azar), tambien despues de destruir rocas y arboles y de que reaparezca un frutal.
- Fondo por trozos: la imagen es identica, pixel a pixel, a dibujar el fondo de una vez en varias
  posiciones de camara, y destruir una roca actualiza su trozo.
- Nivel de detalle: un NPC que entra y sale de la zona activa 100 veces nunca queda dentro de una
  roca ni pierde su nivel, vida o equipo; la simulacion resumida da la XP por minuto de su nivel.
- IA escalonada: cada NPC piensa a su ritmo, repartidos entre fotogramas; los intermedios menos.
Uso: python -B pruebas/unitarias/test_fase3.py"""
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
import herramientas as T
from espacial import RejillaObstaculos, FondoPorTrozos
from personaje import Personaje
from spawn import Casa
from limite_mundo import LIMITE

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


datos = mapa.leer("principal")
charcos, veg, rocas = mapa.construir(datos)
casa = Casa(mundo.CENTRO_MUNDO)
rocas.extend(casa.paredes)
rejilla = RejillaObstaculos(rocas, veg)
j = Personaje("T", 0, 0, 1, 3, 30, 2, 100, 0, (0, 0, 255), [], T.crear_herramienta("Espada Larga"))
rng = random.Random(3)


def comparar(n, texto):
    malos = 0
    for _ in range(n):
        p = LIMITE.punto_al_azar(0, rng)
        lado = rng.choice((100, 400, 800, 1500))
        zona = pygame.Rect(0, 0, lado, lado)
        zona.center = (round(p.x), round(p.y))
        bruto_rocas = [r for r in rocas if r.rect.colliderect(zona)]
        bruto_obs = veg.obstaculos_cerca(j, zona)
        bruto_arb = [a for a in veg.arboles if a.rect.colliderect(zona)]
        if (rejilla.rocas_en(zona) != bruto_rocas or rejilla.obstaculos_cerca(j, zona) != bruto_obs
                or rejilla.arboles_en(zona) != bruto_arb):
            malos += 1
    comprobar(malos == 0, "%s: rejilla = recorrer las listas en %d zonas al azar (%d distintas)" % (texto, n, malos))


# ------------------------------------------------------------ 1. Rejilla de obstaculos
print("--- Rejilla de obstaculos")
comparar(3000, "mapa principal")
destruidas = [rocas.pop(k) for k in (50, 10, 3)] + [veg.arboles.pop(k) for k in (200, 20)]
veg.liberar_obstaculos(destruidas)
comparar(1000, "tras destruir 3 rocas y 2 arboles")
veg.reapariciones_frutal.append(0.0)
antes = len(veg.arbustos)
veg.actualizar_frutales(0.1, evitar=pygame.Vector2(0, 0))
comparar(1000, "tras reaparecer un frutal (%d -> %d arbustos)" % (antes, len(veg.arbustos)))
comprobar(rejilla.reconstrucciones == 3, "la rejilla solo se rehace cuando cambia algo (%d veces)" % rejilla.reconstrucciones)

# ------------------------------------------------------------ 2. Fondo por trozos
print("--- Fondo por trozos")
charcos2, veg2, rocas2 = mapa.construir(datos)
rocas2.extend(Casa(mundo.CENTRO_MUNDO).paredes)
obst2 = RejillaObstaculos(rocas2, veg2)
dibujar_fondo = mundo.dibujo_del_fondo(Casa(mundo.CENTRO_MUNDO), charcos2, veg2, obst2)
fondo = FondoPorTrozos(dibujar_fondo)
ANCHO, ALTO = 1370, 1080


def iguales(vista):
    """El dibujo directo se hace con un margen de 128 px (pygame dibuja distinto lo que corta el
    borde de la superficie) y se compara su centro con lo que pegan los trozos."""
    m = 128
    directo = pygame.Surface((ANCHO + 2 * m, ALTO + 2 * m))
    dibujar_fondo(directo, vista.inflate(2 * m, 2 * m), (vista.x - m, vista.y - m))
    trozos = pygame.Surface((ANCHO, ALTO))
    fondo.dibujar(trozos, vista, (vista.x, vista.y))
    return pygame.image.tobytes(directo.subsurface((m, m, ANCHO, ALTO)), "RGB") == pygame.image.tobytes(trozos, "RGB")


camaras = [mundo.CENTRO_MUNDO, pygame.Vector2(LIMITE.rect.left + 700, LIMITE.centro.y),
           pygame.Vector2(LIMITE.centro.x, LIMITE.rect.bottom - 900), pygame.Vector2(LIMITE.centro.x + 6200, LIMITE.centro.y + 4500),
           pygame.Vector2(LIMITE.centro.x - 3000, LIMITE.centro.y - 5000)]
for c in camaras:
    vista = pygame.Rect(round(c.x - ANCHO / 2) + 37, round(c.y - ALTO / 2) + 11, ANCHO, ALTO)   # no alineada a los trozos
    comprobar(iguales(vista), "fondo por trozos = fondo de una vez en (%d, %d)" % (c.x, c.y))
roca = next(r for r in rocas2 if r.rect.width > 60 and not getattr(r, "indestructible", False) and not getattr(r, "es_cueva", False))
vista = pygame.Rect(0, 0, ANCHO, ALTO)
vista.center = roca.rect.center
comprobar(iguales(vista), "con la roca en su sitio, iguales")
rocas2.remove(roca)
veg2.liberar_obstaculos([roca])
for r in veg2.cambios:
    fondo.invalidar(r.inflate(8, 8))
comprobar(iguales(vista), "destruir una roca redibuja su trozo (sigue igual al dibujo directo, ya sin la roca)")

# ------------------------------------------------------------ 3. Nivel de detalle
print("--- Nivel de detalle (cerca / lejos)")
fauna = F.SistemaFauna(LIMITE, veg, charcos, rocas)
ctx = mundo.Contexto(rocas, veg, charcos, fauna, (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO))
npc = ctx.agregar_combatiente(Personaje("NPC", 0, 0, 1, 3, 30, 2, 100, 0, (200, 0, 0), [], T.crear_herramienta("Mandoble")))
for _ in range(5):
    npc.subir_nivel()
estado0 = (npc.nivel, npc.vida, npc.herramienta.nombre, npc.puntos_mejora)
gigantes = [r for r in rocas if r.rect.width >= 150][:100]
jugador = Personaje("J", mundo.CENTRO_MUNDO.x, mundo.CENTRO_MUNDO.y, 1, 3, 30, 2, 100, 0, (0, 0, 255), [], T.crear_herramienta("Espada Larga"))
dentro_de_roca = 0
for k in range(100):
    roca = gigantes[k % len(gigantes)]
    lejos = pygame.Rect(-99999, -99999, 10, 10)            # zona activa en otra parte: queda resumido
    mundo.actualizar_otros_combatientes(ctx, 0.016, jugador, lejos)
    npc.posicion = pygame.Vector2(roca.rect.center)        # mientras esta lejos acaba dentro de una roca
    npc.destino = pygame.Vector2(npc.posicion)
    zona = pygame.Rect(0, 0, 3000, 3000)
    zona.center = roca.rect.center                          # la camara llega: se materializa
    mundo.actualizar_otros_combatientes(ctx, 0.016, jugador, zona)
    if any(mundo.rect_circulo_colisionan(r.rect, npc.posicion, npc.radio) for r in rocas):
        dentro_de_roca += 1
comprobar(dentro_de_roca == 0, "100 veces dentro de una roca al materializarse: nunca queda dentro (%d)" % dentro_de_roca)
comprobar((npc.nivel, npc.vida, npc.herramienta.nombre, npc.puntos_mejora) == estado0,
          "entrar y salir de la zona activa no cambia su nivel, vida ni equipo")
# Simulacion resumida: 1 h de juego simulada. La XP que gana es la de la tabla de su nivel en cada
# paso. (Comparar con lo que gana un NPC cerca necesita que los NPC cacen: Fase 4.)
from personaje import XP_POR_NIVEL
xp_total = lambda p: sum(XP_POR_NIVEL[:p.nivel - 1]) + p.xp
sin_muerte = type("R", (), {"random": lambda s: 1.0})()
for nivel in (5, 12, 25):
    p = Personaje("R", LIMITE.centro.x, LIMITE.centro.y, 1, 3, 30, 2, 100, 0, (0, 0, 0), [], T.crear_herramienta("Espada Larga"))
    for _ in range(nivel - 1):
        p.subir_nivel()
    inicio, esperado = xp_total(p), 0.0
    for _ in range(int(3600 / mundo.RESUMEN_CADA)):
        esperado += mundo.xp_por_minuto_resumen(p.nivel) * mundo.RESUMEN_CADA / 60
        mundo.simular_resumido(p, mundo.RESUMEN_CADA, sin_muerte)
    ganado = xp_total(p) - inicio
    comprobar(abs(ganado - esperado) / esperado < 0.02 and p.vida > 0,
              "1 h lejos desde el nivel %d: %.0f XP (%.1f por minuto, segun la tabla), llega al %d" % (nivel, ganado, ganado / 60, p.nivel))
muertes = 0
for k in range(2000):
    p = Personaje("M", LIMITE.rect.left + 400, LIMITE.centro.y, 1, 3, 30, 2, 100, 0, (0, 0, 0), [], T.crear_herramienta("Espada Larga"))
    mundo.simular_resumido(p, 60.0, random.Random(k))
    muertes += p.vida <= 0
esperado = mundo.MUERTES_POR_MINUTO_RESUMEN * mundo.peligro_zona(pygame.Vector2(LIMITE.rect.left + 400, LIMITE.centro.y))
comprobar(abs(muertes / 2000 - esperado) < 0.02, "muertes lejos cerca del borde: %.3f por minuto (esperado %.3f)" % (muertes / 2000, esperado))

# ------------------------------------------------------------ 4. IA escalonada
print("--- IA escalonada")
ctx2 = mundo.Contexto(rocas, veg, charcos, fauna, (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO))
llamadas = {}
por_fotograma = []


def cerebro(c, ctx_, jug):
    llamadas[id(c)] = llamadas.get(id(c), 0) + 1


random.seed(8)
npcs = [ctx2.agregar_combatiente(Personaje("N%d" % k, LIMITE.centro.x + 600 + k * 50, LIMITE.centro.y + 600, 1, 3, 30, 2, 100, 0,
                                           (0, 0, 0), [], T.crear_herramienta("Espada Larga")), cerebro) for k in range(12)]
zona = pygame.Rect(0, 0, 4000, 4000)
zona.center = (round(LIMITE.centro.x), round(LIMITE.centro.y))
for f in range(600):                                        # 10 s a 60 fps
    total = sum(llamadas.values())
    mundo.actualizar_otros_combatientes(ctx2, 1 / 60, jugador, zona)
    por_fotograma.append(sum(llamadas.values()) - total)
activos = [c for c in npcs if c.modo == "activo"]
intermedios = [c for c in npcs if c.modo == "intermedio"]
comprobar(len(activos) == mundo.MAX_NPC_ACTIVOS and len(intermedios) == 4,
          "con 12 NPC en pantalla: %d activos y %d intermedios" % (len(activos), len(intermedios)))
ok_ritmo = all(abs(llamadas[id(c)] - 10 / c.pensar_cada) <= 2 for c in activos)
ok_inter = all(abs(llamadas[id(c)] - 10 / (c.pensar_cada * mundo.FACTOR_PENSAR_INTERMEDIO)) <= 2 for c in intermedios)
comprobar(ok_ritmo and ok_inter, "cada NPC piensa cada 0.2-0.5 s; los intermedios 3 veces menos")
comprobar(max(por_fotograma) <= 4, "no piensan todos en el mismo fotograma (como mucho %d a la vez de 12)" % max(por_fotograma))

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
