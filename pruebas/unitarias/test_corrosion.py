"""Pruebas sin ventana: potenciada Corrosion (Disparo Venenoso nv21-30).
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_corrosion.py"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
sys.path.insert(0, os.getcwd())
import pygame
pygame.init()

from personaje import Personaje
from herramientas import EspadaLarga
from habilidades import (DisparoVenenoso, EfectoCorrosion, aplicar_corrosion, factor_dano_corrosion,
                         COLORES_DISPARO_CORROSION, COLORES_DISPARO_VENENO)
import fauna
import mundo

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def disparo(n, potenciada=False):
    d = DisparoVenenoso()
    while d.nivel < min(n, 20):
        d.subir_nivel()
    if potenciada:
        d.desbloquear_potenciada()
        while d.nivel < n:
            assert d.subir_nivel()
    return d


def correr(efecto, obj, segundos, dt=1 / 60):
    for _ in range(round(segundos / dt)):
        efecto.actualizar(dt, obj)


# 1. Escalado
esperado = {20: (2.5, 150, 45, 0.10), 21: (2.55, 153, 47, 0.12), 25: (2.75, 165, 53, 0.20), 30: (3.0, 180, 60, 0.30)}
for n, (dps, total, coste, tope) in esperado.items():
    d = disparo(n, True)
    real = (d.veneno_por_segundo, d.veneno_total, d.costo_energia, d.tope_corrosion)
    comprobar(real == (dps, total, coste, tope) and d.veneno_duracion == 60 and d.duracion_cooldown == 10
              and d.nombre_mostrado == "Corrosión",
              f"Corrosión nv{n}: {dps}/s x 60 s = {real[1]}, {real[2]} En., tope {real[3]:.0%}, CD 10 s")
d = disparo(20, True)
comprobar(d.costo_mejora == 2 and d.nivel_max == 30, "2 puntos por nivel, máximo 30")
comprobar(disparo(20).tope_corrosion == 0 and disparo(20).veneno_total == 100, "sin potenciada no cambia nada")
d = disparo(10)
d.desbloquear_potenciada()
comprobar(not d.potenciada_activa and d.veneno_total == 50.4, "desbloqueada en nv10 sigue normal hasta el 20")
while d.nivel < 20:
    d.subir_nivel()
comprobar(d.potenciada_activa and d.tope_corrosion == 0.10, "al llegar al 20 ya es Corrosión")


# 2. Efecto sobre un objetivo con todo (escudos, energia, arma)
class Objetivo:
    def __init__(self):
        self.posicion = pygame.Vector2(0, 0)
        self.escudo = self.escudo_max = 50.0
        self.escudo_magico = self.escudo_magico_max = 50.0
        self.energia = self.energia_max = 100.0
        self.tiempo_sin_dano_escudo = 9.0
        self.tiempo_sin_dano_escudo_magico = 9.0
        self.herramienta = EspadaLarga()
        self.corrosion = None


o = Objetivo()
dur0 = o.herramienta.durabilidad
aplicar_corrosion(o, 0.12, 60, impacto=True)
comprobar(o.herramienta.durabilidad == dur0 - 1, "impacto: 1 de durabilidad al arma")
correr(o.corrosion, o, 5.0)
comprobar(abs(o.corrosion.nivel - 0.05) < 1e-9 and abs(factor_dano_corrosion(o) - 0.95) < 1e-9,
          f"5 s: corrosión 5 % -> daño x{factor_dano_corrosion(o):.2f}")
comprobar(o.escudo == 47.5 and o.escudo_magico == 47.5, f"escudos -1 % del máximo por segundo ({o.escudo})")
comprobar(o.energia == 95, f"energía -1 %/s ({o.energia})")
comprobar(o.tiempo_sin_dano_escudo == 0 and o.tiempo_sin_dano_escudo_magico == 0, "escudos sin regenerar")
o.corrosion.actualizar(1 / 60, o)      # el reloj de 5 s se cumple en este frame (redondeo de dt)
comprobar(o.herramienta.durabilidad == dur0 - 2, "arma: 1 más a los 5 s")
correr(o.corrosion, o, 15.0)
comprobar(o.corrosion.nivel == 0.12 and o.escudo == 44.0, f"tope 12 %: no pasa ({o.corrosion.nivel:.0%}, escudo {o.escudo})")
comprobar(o.energia == 80, "la energía sigue bajando sin tope")
aplicar_corrosion(o, 0.12, 3.0)
comprobar(o.corrosion.nivel == 0.12 and o.corrosion.restante > 30, "refrescar conserva el nivel y la duración mayor")
correr(o.corrosion, o, 41.0)
comprobar(not o.corrosion.activo, "termina al acabar su duración")

# 3. Velocidad (fauna): se recorta el desplazamiento; con Onda Sonora se queda la mas fuerte
from habilidades import aplicar_ralentizacion


def lobo_prueba():
    l = fauna.Lobo.__new__(fauna.Lobo)
    l.posicion, l.radio, l.vivo, l.vida = pygame.Vector2(0, 0), 12, True, 25
    l._init_combate()
    return l


l = lobo_prueba()
l.corrosion = EfectoCorrosion(0.30, 60)
l.corrosion.nivel = 0.30
l._tick_efectos(1 / 60)
l.posicion += pygame.Vector2(10, 0)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - 7.0) < 1e-6, f"corrosión 30 %: avanza 7 de 10 px ({l.posicion.x:.2f})")
aplicar_ralentizacion(l, 0.20)
x0 = l.posicion.x
l.posicion += pygame.Vector2(10, 0)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - x0 - 7.0) < 1e-6, "con Onda 20 % y corrosión 30 % se queda el 30 % (no se suman)")
x0 = l.posicion.x
l.posicion += pygame.Vector2(500, 0)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - x0 - 500) < 1e-6, "un salto grande (reaparición) no se frena")
x0 = l.posicion.x
l.aplicar_empuje(pygame.Vector2(1, 0), 10)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - x0 - 60) < 1e-6, "el empuje recibido no se frena")

l = lobo_prueba()
aplicar_ralentizacion(l, 0.20)
l._tick_efectos(1 / 60)
l.posicion += pygame.Vector2(10, 0)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - 8.0) < 1e-6, f"Onda Sonora ya frena a la fauna: 20 % -> 8 de 10 px ({l.posicion.x:.2f})")
l._tick_efectos(3.1)
x0 = l.posicion.x
l.posicion += pygame.Vector2(10, 0)
l._tick_efectos(1 / 60)
comprobar(abs(l.posicion.x - x0 - 10) < 1e-6 and l.ralentizacion == 0, "a los 3 s la ralentización termina")

# 4. Fauna: el lobo corroído muerde menos; el humo corroe sin veneno
lobo = fauna.Lobo.__new__(fauna.Lobo)
lobo.posicion, lobo.radio, lobo.vivo = pygame.Vector2(30, 0), 12, True
lobo._init_combate()
lobo.corrosion = EfectoCorrosion(0.30, 60)
lobo.corrosion.nivel = 0.25
j = Personaje(nombre="t", x=0, y=0, tamano=1, velocidad=3, vida=30, fuerza=3, energia=500, escudo=0,
              escudo_magico=0, color=(0, 0, 0), habilidades=[], herramienta=EspadaLarga())
vida0 = j.vida
fauna.golpear_objetivo(lobo, j, 8)
comprobar(vida0 - j.vida == 6, f"mordida de 8 con 25 % -> {vida0 - j.vida}")

d = disparo(30, True)
j.huecos_habilidades = [d]
lejos = fauna.Lobo.__new__(fauna.Lobo)
lejos.posicion, lejos.radio, lejos.vivo = pygame.Vector2(300, 0), 12, True
lejos._init_combate()
cerca = fauna.Lobo.__new__(fauna.Lobo)
cerca.posicion, cerca.radio, cerca.vivo = pygame.Vector2(65, 0), 12, True
cerca._init_combate()
d.actualizar_dano_enemigos(1 / 60, [lejos, cerca], j)
comprobar(cerca.corrosion is not None and cerca.corrosion.tope == 0.30 and cerca.corrosion.restante == 3.0
          and cerca.veneno is None and lejos.corrosion is None,
          "humo 60 px: corroe al cercano 3 s, sin veneno; el lejano nada")
comprobar(d.corroidos == [cerca], "el cercano lleva el anillo de corroído")

# 5. El disparo de Corrosión y el normal
j.energia = 500
d.estado = "LISTA"
d.intentar_activar(j)
p = j.proyectiles[-1]
comprobar(p.corrosion_tope == 0.30 and p.colores == COLORES_DISPARO_CORROSION and p.veneno_total == 180,
          "el disparo de Corrosión lleva tope 30 %, 180 de veneno y sus colores")
n = disparo(20)
n.intentar_activar(j)
p = j.proyectiles[-1]
comprobar(p.corrosion_tope is None and p.colores == COLORES_DISPARO_VENENO, "Disparo Venenoso normal no corroe")

# 6. Maniqui: su espada pega menos corroido y su escudo se corroe
m = mundo.Maniqui(pygame.Vector2(0, 0))
comprobar(m.corrosion is None, "el maniquí tiene hueco de corrosión")
aplicar_corrosion(m, 0.30, 60, impacto=True)
for _ in range(60 * 10):
    m.actualizar(1 / 60, None)
comprobar(abs(m.corrosion.nivel - 0.10) < 1e-9 and m.escudo == m.escudo_max * 0.9,
          f"maniquí 10 s: corrosión 10 %, escudo {m.escudo}/{m.escudo_max}")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
