"""Pruebas sin ventana de la boca de las cuevas de oso: la roca es cuadrada, asi que en diagonal
la entrada, la salida del oso y los orbes deben quedar fuera del cuadrado (antes quedaban dentro
de la roca y el orbe de vida no se podia recoger).
Uso: python -B pruebas/unitarias/test_cuevas.py"""
import math
import os
import sys
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
import mundo
import fauna as F

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def fuera(rect, punto, margen):
    """True si un circulo de radio 'margen' en ese punto no toca el cuadrado."""
    return not mundo.rect_circulo_colisionan(rect, pygame.Vector2(punto), margen)


roca = mundo.Roca(5000, 5000, 200)
for grados in (0, 30, 45, 90, 135, 200, 225, 315):
    roca.angulo_entrada = math.radians(grados)
    oso = F.Oso(roca)
    oso.dejar_orbes()
    comprobar(fuera(roca.rect, oso.entrada, 5) and fuera(roca.rect, oso._boca(), oso.radio),
              "%3d grados: la entrada y la salida del oso quedan fuera de la roca" % grados)
    comprobar(all(fuera(roca.rect, o.centro, 5) for o in [oso.orbe] + oso.orbes_extra),
              "%3d grados: los orbes quedan fuera de la roca" % grados)
nuevo = oso.renacer()
comprobar(nuevo.entrada == oso.entrada and nuevo.cueva_borde == oso.cueva_borde, "el oso que renace usa la misma boca")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
