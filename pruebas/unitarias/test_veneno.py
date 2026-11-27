"""Pruebas sin ventana: rebalance de Disparo Venenoso (veneno lento y largo) y autoveneno.
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_veneno.py"""
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
from habilidades import DisparoVenenoso, GolpeDeSuerte, EfectoVeneno, ProyectilVeneno

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def nivel(cls, n):
    h = cls()
    while h.nivel < n:
        h.subir_nivel()
    return h


# 1. Escalado en niveles 1, intermedios y 20
esperado = {1: (20, 1.0, 20, 20, 15), 5: (25, 1.32, 24.2, 31.9, 13.9), 10: (32, 1.71, 29.5, 50.4, 12.6),
            15: (38, 2.11, 34.7, 73.2, 11.3), 20: (45, 2.5, 40, 100, 10)}
for n, valores in esperado.items():
    d = nivel(DisparoVenenoso, n)
    real = (d.costo_energia, d.veneno_por_segundo, d.veneno_duracion, d.veneno_total, d.duracion_cooldown)
    comprobar(real == valores, f"nv{n}: coste {real[0]}, {real[1]}/s x {real[2]} s = {real[3]}, CD {real[4]} s")

# 2. Monotonia y recarga siempre menor que la duracion
prev = None
ok_mono = ok_cd = True
for n in range(1, 21):
    d = nivel(DisparoVenenoso, n)
    ok_cd &= d.duracion_cooldown < d.veneno_duracion
    if prev:
        ok_mono &= (d.veneno_por_segundo >= prev.veneno_por_segundo and d.veneno_duracion > prev.veneno_duracion
                    and d.veneno_total > prev.veneno_total and d.duracion_cooldown < prev.duracion_cooldown)
    prev = d
comprobar(ok_mono, "daño/s, duración y total suben y la recarga baja en cada nivel")
comprobar(ok_cd, "la recarga siempre es menor que la duración (varios envenenados a la vez)")
comprobar(not nivel(DisparoVenenoso, 20).subir_nivel(), "nivel máximo 20")


# 3. El veneno aplica exactamente el total, un golpe por segundo, en su duración
class Objetivo:
    def __init__(self):
        self.recibido = []

    def recibir_dano(self, cantidad, tipo="fisico"):
        self.recibido.append((cantidad, tipo))
        return cantidad


for n in (1, 20):
    d = nivel(DisparoVenenoso, n)
    ef, obj = EfectoVeneno(d.veneno_total, d.veneno_duracion), Objetivo()
    t = 0.0
    while ef.activo:
        ef.actualizar(1 / 60, obj)
        t += 1 / 60
    total = round(sum(c for c, _ in obj.recibido), 2)
    comprobar(total == d.veneno_total and abs(t - d.veneno_duracion) < 0.05
              and all(tp == "magico" for _, tp in obj.recibido)
              and max(c for c, _ in obj.recibido) <= d.veneno_por_segundo + 0.01,
              f"nv{n}: {len(obj.recibido)} golpes mágicos, total {total} en {t:.1f} s")

# 4. El disparo lleva los valores del nivel y entra en recarga
d = nivel(DisparoVenenoso, 10)
j = Personaje(nombre="t", x=0, y=0, tamano=1, velocidad=3, vida=30, fuerza=3, energia=500, escudo=0,
              escudo_magico=0, color=(0, 0, 0), habilidades=[d], herramienta=EspadaLarga())
j.energia = 500
comprobar(d.intentar_activar(j), "se lanza con energía suficiente")
p = j.proyectiles[-1]
comprobar(isinstance(p, ProyectilVeneno) and (p.veneno_total, p.veneno_duracion) == (50.4, 29.5)
          and p.dano == 0, "la esfera lleva 50.4 en 29.5 s y no hace daño de impacto")
comprobar(d.estado == "COOLDOWN" and d.tiempo_restante_cooldown == 12.6 and j.energia == 500 - 32,
          "recarga 12.6 s y coste 32 En.")

# 5. Autoveneno de Golpe de Suerte: mitad del total en la mitad de la duracion
for n_golpe in (1, 20):
    gs = nivel(GolpeDeSuerte, n_golpe)
    j.veneno = None
    gs.aplicar_resultado(GolpeDeSuerte.VENENO, j)
    ref = nivel(DisparoVenenoso, gs.nivel_efecto)
    comprobar(j.veneno is not None and j.veneno.total == round(ref.veneno_total / 2, 2)
              and j.veneno.duracion == round(ref.veneno_duracion / 2, 2),
              f"Golpe de Suerte nv{n_golpe}: autoveneno {j.veneno.total} en {j.veneno.duracion} s")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
