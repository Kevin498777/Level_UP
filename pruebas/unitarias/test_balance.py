"""Pruebas headless del rebalance (Escudo, Conejos, Disparo Veloz, Disparo Venenoso, Carga de Fuego).
Uso: python -B test_balance.py <carpeta_del_proyecto>"""
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
sys.path.insert(0, sys.argv[1])

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from herramientas import Escudo, EspadaLarga, ESCUDO_ARCO_BLOQUEO
from personaje import Personaje
from habilidades import (DisparoVeloz, DisparoVenenoso, InvocacionConejos, CargaDeFuego,
                         ProyectilEnergia, GolpeDeSuerte, aplicar_quemadura)
from mundo import Maniqui

fallos = []


def check(cond, msg):
    if not cond:
        fallos.append(msg)
        print("FALLO:", msg)


def cerca(a, b, tol=1e-6):
    return abs(a - b) <= tol


def nuevo_jugador(herr=None, escudo=0, escudo_m=0):
    return Personaje("T", 1000, 1000, 1, 1, 20, 2, 100, escudo, (0, 0, 255),
                     habilidades=[], herramienta=herr, escudo_magico=escudo_m)


# ---------------- ESCUDO ----------------
e = Escudo()
esperado_red = [0.20, 0.325, 0.45, 0.575, 0.70]
esperado_bon = [0.15, 0.1875, 0.225, 0.2625, 0.30]
for nv in range(1, 6):
    check(cerca(e.reduccion_desgaste, esperado_red[nv - 1]), f"reduccion nv{nv} = {e.reduccion_desgaste}")
    check(cerca(e.bonus_escudos, esperado_bon[nv - 1]), f"bonus nv{nv} = {e.bonus_escudos}")
    e.subir_nivel()
check(e.durabilidad_max == 300, "durabilidad nv5 300")

# Bonus solo multiplica la base: con 0 sigue en 0
j = nuevo_jugador(Escudo())
check(j.escudo_max == 0 and j.escudo_magico_max == 0, "escudos base 0 siguen en 0")
j.subir_stat("escudo"); j.subir_stat("escudo_magico")
check(cerca(j.escudo_max, 5.75) and cerca(j.escudo, 5.75), f"escudo 5 -> 5.75 ({j.escudo_max}, {j.escudo})")
check(cerca(j.escudo_magico_max, 5.75), "escudo magico 5 -> 5.75")
check(j.escudo_max_base == 5, "base sigue en 5")
# Progresion de puntos usa la base (+5 hasta 15, luego +2)
j.puntos_mejora = 10
for _ in range(3):
    j.subir_stat("escudo")
check(j.escudo_max_base == 17, f"base tras 4 mejoras = 17 ({j.escudo_max_base})")

# Escudos iniciales con bonus al entrar al mundo
j = nuevo_jugador(Escudo(), escudo=20, escudo_m=10)
check(cerca(j.escudo, 23.0) and cerca(j.escudo_magico, 11.5), f"inicio con bonus ({j.escudo}, {j.escudo_magico})")
# Sin Escudo: sin bonus
j2 = nuevo_jugador(EspadaLarga(), escudo=20)
check(j2.escudo_max == 20 and j2.bonus_escudos == 0, "otra herramienta sin bonus")

# Cobertura del arco frontal (angulo 0 = mirando arriba)
j = nuevo_jugador(Escudo())
j.angulo = 0.0
esc = j.herramienta
check(not esc.cubre(j, (1000, 900)), "enfundado no cubre")
esc.activa = True
check(esc.cubre(j, (1000, 900)), "frente cubre")
def punto_a(grados, dist=100):
    r = math.radians(grados)
    return (1000 + math.sin(r) * dist, 1000 - math.cos(r) * dist)
check(esc.cubre(j, punto_a(59)) and esc.cubre(j, punto_a(-59)), "59 grados cubre")
check(not esc.cubre(j, punto_a(61)) and not esc.cubre(j, punto_a(-61)), "61 grados no cubre")
check(not esc.cubre(j, punto_a(180)), "espalda no cubre")
check(ESCUDO_ARCO_BLOQUEO == 120, "arco 120")

# Bloqueo: ejemplo del usuario a nv5 (100 de daño -> 30 de durabilidad)
j = nuevo_jugador(Escudo(), escudo=20)
for _ in range(4):
    j.herramienta.subir_nivel()
j.herramienta.activa = True
vida0, esc0 = j.vida, j.escudo
check(j.bloquear_con_escudo(100, punto_a(0)), "bloquea de frente")
check(cerca(j.herramienta.durabilidad, 270), f"durabilidad 300 -> 270 ({j.herramienta.durabilidad})")
check(j.vida == vida0 and j.escudo == esc0, "bloqueo no daña vida ni escudos")
check(j.empuje.length() > 0, "bloqueo empuja al portador")
check(not j.bloquear_con_escudo(100, punto_a(180)), "no bloquea por la espalda")
check(cerca(j.herramienta.durabilidad, 270), "por la espalda no gasta durabilidad")

# Nv1: 6.8 (espada larga del maniqui) -> 5.44 de desgaste
j = nuevo_jugador(Escudo())
j.herramienta.activa = True
j.bloquear_con_escudo(6.8, punto_a(0))
check(cerca(j.herramienta.durabilidad, 100 - 5.44), f"nv1 6.8 -> {j.herramienta.durabilidad}")

# Rotura: pierde el bonus y los escudos se recortan al maximo base
j = nuevo_jugador(Escudo(), escudo=20, escudo_m=20)
j.herramienta.activa = True
j.bloquear_con_escudo(1000, punto_a(0))
check(j.herramienta.roto and not j.herramienta.activa, "escudo roto")
check(j.bonus_escudos == 0 and j.escudo_max == 20, "roto sin bonus")
j.actualizar_regeneracion_escudo(0.016); j.actualizar_regeneracion_escudo_magico(0.016)
check(j.escudo == 20 and j.escudo_magico == 20, f"escudos recortados ({j.escudo}, {j.escudo_magico})")
check(not j.bloquear_con_escudo(5, punto_a(0)), "roto no bloquea")
j.herramienta.subir_nivel()
check(not j.herramienta.roto and cerca(j.bonus_escudos, 0.1875), "reparado recupera bonus (nv2)")

# ---------------- DISPARO VELOZ ----------------
dv = DisparoVeloz()
check(dv.dano == 8 and dv.velocidad_proyectil == 14, f"DV nv1 {dv.dano} {dv.velocidad_proyectil}")
check(dv.costo_energia == 15 and dv.duracion_cooldown == 4.0, f"DV nv1 coste/CD {dv.costo_energia} {dv.duracion_cooldown}")
for _ in range(9):
    dv.subir_nivel()
# Ajuste del 24/11/2026: dano 8 -> 25, velocidad 14 -> 35, recarga 4 -> 2 s
check(dv.dano == round(8 + 17 * 9 / 19, 1) and dv.velocidad_proyectil == round(14 + 21 * 9 / 19, 1), f"DV nv10 {dv.dano} {dv.velocidad_proyectil}")
for _ in range(10):
    dv.subir_nivel()
check(dv.nivel == 20 and dv.dano == 25 and dv.velocidad_proyectil == 35, f"DV nv20 {dv.dano} {dv.velocidad_proyectil}")
check(dv.costo_energia == 35 and dv.duracion_cooldown == 2.0, "DV nv20 coste/CD")
# Daño fijo: igual con o sin arma desenfundada
for herr in (None, EspadaLarga()):
    j = nuevo_jugador(herr)
    if herr:
        herr.activa = True
    d = DisparoVeloz()
    d.intentar_activar(j)
    check(j.proyectiles and j.proyectiles[-1].dano == 8, "DV daño fijo 8")
    check(j.energia == 85, "DV cobra 15")

# Proyectil rapido no atraviesa una roca pequeña entre dos frames
class RocaFalsa:
    def __init__(self, rect):
        self.rect = rect
j = nuevo_jugador()
p = ProyectilEnergia(1000, 1000, 1, 0, velocidad=40, dano=8, radio=6)
p.posicion.x = 1000; p.hitbox.x = 994
j.proyectiles = [p]
roca = RocaFalsa(pygame.Rect(1015, 990, 22, 22))   # queda entre x=1000 y x=1040
# Primer frame: la hitbox final (1034..1046) no toca la roca (1015..1037)? toca en 1034-1037; mover la roca
roca.rect.x = 1012; roca.rect.width = 20            # 1012..1032: fuera de la hitbox final
j.actualizar_proyectiles(0.016, (0, 0, 5000, 5000), [roca])
check(not j.proyectiles, "proyectil a 40 no salta la roca pequeña")

# ---------------- DISPARO VENENOSO ----------------
dven = DisparoVenenoso()
check(dven.costo_energia == 20, "veneno nv1 coste 20")
for _ in range(9):
    dven.subir_nivel()
check(dven.costo_energia == round(20 + 25 * 9 / 19), f"veneno nv10 coste {dven.costo_energia}")
for _ in range(10):
    dven.subir_nivel()
# Veneno lento y largo (26/11/2026): el detalle de dano y duracion lo prueba test_veneno
check(dven.costo_energia == 45 and dven.duracion_cooldown == 10, "veneno nv20 coste 45 y recarga 10 s")

# ---------------- CONEJOS ----------------
inv = InvocacionConejos()
j = nuevo_jugador()
j.habilidades = [inv]
check(inv.intentar_activar(j), "conejos se invocan")
check(cerca(inv.intervalo_reproduccion(), 15.0), "intervalo con 5 vivos = 15 s")
t, dt, hitos = 0.0, 0.05, {}
while t < 400:
    inv.actualizar(dt, j)
    t += dt
    n = len(inv.conejos)
    for meta in (20, 50):
        if n >= meta and meta not in hitos:
            hitos[meta] = t
check(len(inv.conejos) == 50, f"tope 50 ({len(inv.conejos)})")
check(70 <= hitos.get(20, 0) <= 85, f"llega a 20 en ~77 s ({hitos.get(20)})")
check(195 <= hitos.get(50, 0) <= 225, f"llega a 50 en ~3.5 min ({hitos.get(50)})")
inv2 = InvocacionConejos(); inv2.conejos = [object()] * 20
check(cerca(inv2.intervalo_reproduccion(), 30.0), "intervalo con 20 vivos = 30 s")

# ---------------- CARGA DE FUEGO ----------------
def disparar_fuego(segundos, nivel=1):
    cf = CargaDeFuego()
    for _ in range(nivel - 1):
        cf.subir_nivel()
    j = nuevo_jugador()
    j.habilidades = [cf]
    cf.iniciar_carga(j)
    t = 0.0
    while t < segundos:
        cf.actualizar(0.01, j)
        t += 0.01
    cf.soltar_carga(j)
    return cf, j, j.proyectiles[-1]

esperado = {0: (12, 2, 8.0, 85), 1: (16, 3, 9.4, 80), 2: (20, 4, 10.8, 75),
            3: (26, 5, 12.2, 70), 4: (32, 6, 13.6, 65), 5: (40, 7, 15.0, 55)}
for seg, (dano, quem, cd, energia) in esperado.items():
    cf, j, p = disparar_fuego(seg + 0.05 if seg else 0)
    check(cerca(p.dano, dano), f"fuego {seg}s daño {p.dano} != {dano}")
    check(cerca(p.quemadura_duracion, quem), f"fuego {seg}s quemadura {p.quemadura_duracion} != {quem}")
    check(cerca(cf.duracion_cooldown, cd) and cerca(cf.tiempo_restante_cooldown, cd), f"fuego {seg}s CD {cf.duracion_cooldown} != {cd}")
    check(j.energia == energia, f"fuego {seg}s energia {j.energia} != {energia}")
cf, j, p = disparar_fuego(5.05, nivel=20)
check(cerca(p.dano, 78) and cerca(p.quemadura_duracion, 7), f"fuego nv20 5s {p.dano}")
cf, j, p = disparar_fuego(0, nivel=20)
check(cerca(p.dano, 23.4), f"fuego nv20 toque {p.dano}")
# Quemadura de 7 s quita 7 de vida al maniqui (ignora escudos)
m = Maniqui((3000, 3000))
aplicar_quemadura(m, 1, 7.0)
for _ in range(800):
    m.quemadura and m.quemadura.actualizar(0.01, m)
check(cerca(m.vida, 93) and m.escudo == 50, f"quemadura 7 s -> vida {m.vida}")

# ---------------- REGRESION ----------------
gs = GolpeDeSuerte()
j = nuevo_jugador(Escudo(), escudo=10, escudo_m=10)
j.habilidades = [gs]
for _ in range(30):
    gs.estado = "LISTA"; j.energia = 100
    gs.intentar_activar(j)
    for _ in range(5):
        gs.actualizar(0.5, j); j.actualizar_efectos(0.5)
check(j.escudo <= j.escudo_max and j.escudo_magico <= j.escudo_magico_max, "Golpe de Suerte respeta los maximos con bonus")
# Daño normal sin escudo desenfundado sigue igual
j = nuevo_jugador(EspadaLarga(), escudo=10)
j.recibir_dano(10, "fisico")
check(cerca(j.escudo, 10 - 5.6) and cerca(j.vida, 20 - 2.4), f"reparto fisico intacto ({j.escudo}, {j.vida})")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
