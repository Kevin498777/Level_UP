"""Pruebas headless del Autoapuntado. Uso: python -B test_autoapuntado.py <carpeta_del_proyecto>"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import math

os.environ["SDL_VIDEODRIVER"] = "dummy"
raiz = sys.argv[1]
sys.path.insert(0, raiz)

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from personaje import Personaje, AUTOAPUNTADO_RANGO
from herramientas import Escudo, Arco, EspadaLarga
from habilidades import CargaDeFuego, RegeneracionInversa, DisparoVeloz
from mundo import Maniqui

fallos = []


def check(cond, msg):
    if not cond:
        fallos.append(msg)
        print("FALLO:", msg)


def jugador(herr=None, habs=()):
    j = Personaje("T", 1000, 1000, 1, 1, 20, 2, 100, 0, (0, 0, 255), habilidades=list(habs), herramienta=herr)
    return j


def angulo_a(j, punto):
    h = pygame.Vector2(punto) - j.posicion
    return math.degrees(math.atan2(h.x, -h.y)) % 360.0


LIMITES = (0, 0, 10000, 10000)

# Activar, mirar y desactivar
m = Maniqui((1300, 1000))
j = jugador()
check(j.alternar_autoapuntado(m), "se activa a 300")
check(j.objetivo_apuntado is m and abs(j.angulo - 90) < 1e-6, f"mira al objetivo ({j.angulo})")
check(not j.alternar_autoapuntado(m) and j.objetivo_apuntado is None, "clic sobre el mismo objetivo lo quita")
j.alternar_autoapuntado(m)
check(not j.alternar_autoapuntado(None) and j.objetivo_apuntado is None, "clic en terreno libre lo quita")

# Rango de activacion
lejos = Maniqui((1000 + AUTOAPUNTADO_RANGO + 1, 1000))
j = jugador()
check(not j.alternar_autoapuntado(lejos) and j.mensaje_apuntado, "fuera de rango no activa y avisa")
borde = Maniqui((1000 + AUTOAPUNTADO_RANGO, 1000))
check(j.alternar_autoapuntado(borde), "a 500 justos si activa")

# Cargas bloquean la activacion
cf = CargaDeFuego()
j = jugador(habs=[cf])
cf.iniciar_carga(j)
check(not j.alternar_autoapuntado(m) and "cargas" in j.mensaje_apuntado, "cargando Carga de Fuego no activa")
cf.soltar_carga(j)
arco = Arco(); arco.activa = True
j = jugador(herr=arco)
arco.iniciar_carga()
check(not j.alternar_autoapuntado(m), "tensando el arco no activa")
arco.cancelar_carga()
check(j.alternar_autoapuntado(m), "sin cargar el arco si activa")
# Ya activo: se puede cargar y sigue activo
check(arco.iniciar_carga() and j.objetivo_apuntado is m, "con autoapuntado se puede cargar el arco")
# La curacion mantenida no bloquea
reg = RegeneracionInversa()
j = jugador(habs=[reg])
j.vida = 10
reg.canalizando = True
check(j.alternar_autoapuntado(m), "Regeneración Inversa mantenida no bloquea")

# Debuff de velocidad -40 % (se suma a los demas)
j = jugador()
j.actualizar_velocidad(); v0 = j.velocidad
j.alternar_autoapuntado(m); j.actualizar_velocidad()
check(abs(v0 - 1.0) < 1e-9 and abs(j.velocidad - 0.6) < 1e-9, f"velocidad 1 -> 0.6 ({j.velocidad})")
esc = Escudo(); esc.activa = True
j = jugador(herr=esc)
j.velocidad_base = 2.0
j.alternar_autoapuntado(m); j.actualizar_velocidad()
check(abs(j.velocidad - 2.0 * (1 - 0.34 - 0.40)) < 1e-9, f"escudo + autoapuntado = -74% ({j.velocidad})")

# Moverse sin dejar de mirar al objetivo
j = jugador()
j.alternar_autoapuntado(m)
j.destino = pygame.Vector2(1000, 1200)          # camina hacia abajo
for _ in range(30):
    j.actualizar_autoapuntado(0.016)
    j.actualizar_velocidad()
    j.mover(LIMITES)
check(j.posicion.y > 1000, "se mueve")
check(abs(j.angulo - angulo_a(j, m.posicion)) < 1.0, f"sigue mirando al objetivo ({j.angulo})")

# Los disparos salen hacia el objetivo
dv = DisparoVeloz()
j = jugador(habs=[dv])
j.alternar_autoapuntado(Maniqui((1200, 800)))
dv.intentar_activar(j)
d = j.proyectiles[-1].direccion
check(abs(d.x - math.sqrt(0.5)) < 1e-3 and abs(d.y + math.sqrt(0.5)) < 1e-3, f"disparo hacia el objetivo ({d})")

# Se suelta al pasar de 500 o si el objetivo muere
j = jugador()
j.alternar_autoapuntado(m)
j.posicion = pygame.Vector2(1300 - AUTOAPUNTADO_RANGO - 1, 1000)
j.actualizar_autoapuntado(0.016)
check(j.objetivo_apuntado is None, "se suelta a mas de 500")
j.posicion = pygame.Vector2(1000, 1000)
j.alternar_autoapuntado(m)
m.vivo = False
j.actualizar_autoapuntado(0.016)
check(j.objetivo_apuntado is None, "se suelta si el objetivo muere")
j.actualizar_velocidad()
check(abs(j.velocidad - 1.0) < 1e-9, "sin autoapuntado no hay debuff")

# Sin autoapuntado el angulo sigue al movimiento (regresion)
j = jugador()
j.destino = pygame.Vector2(1000, 1300)
j.mover(LIMITES)
check(abs(j.angulo - 180) < 1e-6, f"angulo normal por movimiento ({j.angulo})")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
