"""Pruebas sin ventana: el veneno nunca mata a un personaje, lo deja a 1 de vida (27/11/2026).
Cubre el veneno de Disparo Venenoso / Corrosion y el autoveneno de Golpe de Suerte.
Uso: python -B pruebas/unitarias/test_veneno_no_mata.py"""
import os
import sys
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
import habilidades as H
import herramientas
import mundo
from personaje import Personaje

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def jugador(vida=10):
    j = Personaje("T", 0, 0, 1, 1, vida, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"))
    return j


def envenenar(objetivo, total, duracion):
    H.aplicar_veneno(objetivo, total, duracion)
    for _ in range(int((duracion + 1) * 60)):
        objetivo.veneno.actualizar(1 / 60, objetivo)


j = jugador(10)
envenenar(j, 50, 10)
comprobar(j.vida == 1, "veneno de 50 a un personaje con 10 de vida: queda a 1 (%s)" % j.vida)
j = jugador(10)
envenenar(j, 4, 4)
comprobar(j.vida == 6, "un veneno que no llega a matar resta lo normal (10 - 4 = %s)" % j.vida)
j = jugador(10); j.vida = 1
envenenar(j, 5, 5)
comprobar(j.vida == 1, "a 1 de vida el veneno ya no baja mas (%s)" % j.vida)
j = jugador(10); j.vida = 0.5
H.aplicar_veneno(j, 5, 5); j.veneno.actualizar(1.01, j)
comprobar(j.vida <= 0.5, "si otra cosa ya lo dejo por debajo de 1, el veneno no lo cura (%s)" % j.vida)
# Autoveneno de Golpe de Suerte
g = H.crear_habilidad("Golpe de Suerte"); j = jugador(3); j.habilidades.append(g)
g.aplicar_resultado("Disparo Venenoso", j)
comprobar(j.veneno is not None, "Golpe de Suerte puede envenenar al propio jugador")
for _ in range(60 * 60):
    j.veneno.actualizar(1 / 60, j)
comprobar(j.vida >= 1, "el autoveneno de Golpe de Suerte no mata (vida %s)" % j.vida)
# Los enemigos si mueren por veneno
m = mundo.Maniqui(pygame.Vector2(0, 0)); m.escudo_magico = 0; m.escudo_magico_max = 0; m.vida = 3
envenenar(m, 50, 10)
comprobar(m.vida <= 0 or not m.vivo, "el veneno sigue pudiendo matar a los enemigos (maniqui %s)" % m.vida)

# Hierba venenosa (arbusto venenoso): tampoco mata
import vegetacion as V
veg = V.SistemaVegetacion(pygame.Vector2(5000, 5000), 3000, 300, [])
venenoso = next(a for a in veg.arbustos if a.tipo == V.TIPO_VENENOSO and a.puede_entrar(jugador()))
j = jugador(3)
j.posicion = pygame.Vector2(venenoso.centro)
for _ in range(60 * 30):
    veg.actualizar_personaje(1 / 60, j)
comprobar(j.vida == 1, "la hierba venenosa deja al personaje a 1 de vida (%s)" % j.vida)

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
