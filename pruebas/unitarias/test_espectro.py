"""Pruebas sin ventana: rebalance de Paso 0 y potenciada Espectro.
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_espectro.py"""
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
from limite_mundo import LimiteMundo
pygame.init()

from personaje import Personaje
from herramientas import EspadaLarga, Arco
from habilidades import Paso0, DisparoVeloz, Destello, GolpeDeSuerte, OndaSonora
import mundo
from tumba import Tumba

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def nuevo_jugador(habs, arma=None):
    j = Personaje(nombre="t", x=0, y=0, tamano=1, velocidad=3, vida=30, fuerza=3, energia=500,
                  escudo=0, escudo_magico=0, color=(0, 0, 0), habilidades=habs,
                  herramienta=arma or EspadaLarga())
    j.energia = 500
    return j


def paso_nivel(n, potenciada=False):
    p = Paso0()
    while p.nivel < min(n, 10):
        p.subir_nivel()
    if potenciada:
        p.desbloquear_potenciada()
        while p.nivel < n:
            assert p.subir_nivel()
    return p


class Enemigo:
    def __init__(self, vida=100):
        self.vida, self.vivo, self.posicion, self.radio, self.escudo = vida, True, pygame.Vector2(50, 0), 10, 0.0
        self.recibido = []

    def recibir_dano(self, d, tipo="fisico", direccion=None):
        self.recibido.append(d)
        self.vida -= d
        if self.vida <= 0:
            self.vivo = False
        return d


# 1. Escalado de Paso 0 (nv1-10)
for n, dur, coste, cd in ((1, 6, 20, 8), (5, 10, 38, 11.56), (10, 15, 60, 16)):
    p = paso_nivel(n)
    comprobar((p.duracion_activa, p.costo_energia, p.duracion_cooldown) == (dur, coste, cd),
              f"Paso 0 nv{n}: {p.duracion_activa}s, {p.costo_energia} En., CD {p.duracion_cooldown}s")
comprobar(not paso_nivel(10).subir_nivel(), "Paso 0 sin potenciada no pasa del nivel 10")

# 2. Escalado de Espectro (nv11-15)
esperado = {11: (16, 64, 0.5), 12: (17, 68, 0.625), 13: (18, 72, 0.75), 14: (19, 76, 0.875), 15: (20, 80, 1.0)}
for n, (dur, coste, bono) in esperado.items():
    p = paso_nivel(n, True)
    comprobar((p.duracion_activa, p.costo_energia, p.duracion_cooldown, p.bono_emboscada) == (dur, coste, 16, bono)
              and p.nombre_mostrado == "Espectro" and p.tiene_ejecucion == (n == 15),
              f"Espectro nv{n}: {p.duracion_activa}s, {p.costo_energia} En., CD {p.duracion_cooldown}, "
              f"Emboscada +{p.bono_emboscada:.1%}, Ejecucion {p.tiene_ejecucion}")
p = paso_nivel(10)
p.desbloquear_potenciada()
comprobar(p.costo_mejora == 3 and p.nivel_max == 15, "Espectro: nivel max 15, 3 puntos por nivel")

# 3. Atacar con el arma cancela Paso 0
p = paso_nivel(1)
j = nuevo_jugador([p])
j.herramienta.activa = True
p.intentar_activar(j)
comprobar(j.invisible, "Paso 0 activo -> invisible")
j.herramienta.atacar(j)
comprobar(not j.invisible and p.estado == "COOLDOWN" and p.tiempo_restante_cooldown == 8,
          "golpe del arma cancela Paso 0 y empieza la recarga (8 s)")

# 4. Arco: disparar cancela; cargar no
p = paso_nivel(1)
arco = Arco()
j = nuevo_jugador([p], arco)
arco.activa = True
p.intentar_activar(j)
arco.iniciar_carga()
comprobar(j.invisible, "cargar el arco no cancela")
arco.tiempo_carga = 2.0
comprobar(arco.soltar_carga(j) is not None and not j.invisible, "disparar la flecha cancela Paso 0")

# 5. Habilidades: de dano cancelan, el resto no
for hab_cls, rompe in ((DisparoVeloz, True), (OndaSonora, True), (Destello, False), (GolpeDeSuerte, False)):
    p = paso_nivel(1)
    h = hab_cls()
    j = nuevo_jugador([p, h])
    p.intentar_activar(j)
    h.intentar_activar(j)
    comprobar(j.invisible != rompe, f"{h.nombre}: {'cancela' if rompe else 'no cancela'} Paso 0")

# 6. Espectro: atacar no cancela
p = paso_nivel(11, True)
j = nuevo_jugador([p, DisparoVeloz()])
j.herramienta.activa = True
p.intentar_activar(j)
j.herramienta.atacar(j)
j.habilidades[1].intentar_activar(j)
comprobar(j.invisible and p.estado == "ACTIVA", "Espectro: arma y habilidades no cancelan")

# 7. Emboscada: una vez por enemigo y activacion; la tumba no cuenta
a, b = Enemigo(), Enemigo()
j.golpear_con_arma(a, 10, "fisico")
j.golpear_con_arma(a, 10, "fisico")
j.golpear_con_arma(b, 10, "fisico")
comprobar(a.recibido == [15, 10] and b.recibido == [15], f"Emboscada nv11 +50 % solo el primer golpe: {a.recibido} {b.recibido}")
t = Tumba((0, 0), {})
comprobar(p.emboscar(t) == 0, "la tumba no recibe Emboscada")
p.terminar_activo(j)
p.estado = "LISTA"
p.intentar_activar(j)
j.golpear_con_arma(a, 10, "fisico")
comprobar(a.recibido[-1] == 15, "nueva activacion: la Emboscada vuelve a valer")
p.terminar_activo(j)
j.golpear_con_arma(a, 10, "fisico")
comprobar(a.recibido[-1] == 10, "sin invisibilidad no hay Emboscada")

# 8. Ejecucion (nv15): +2 s por remate, maximo +6 s
p = paso_nivel(15, True)
j = nuevo_jugador([p])
p.intentar_activar(j)
inicio = p.tiempo_restante_activo
for _ in range(5):
    j.golpear_con_arma(Enemigo(vida=5), 10, "fisico")
comprobar(p.tiempo_restante_activo == inicio + 6, f"Ejecucion: +6 s maximo ({p.tiempo_restante_activo - inicio:g})")
e = Enemigo(vida=100)
j.golpear_con_arma(e, 10, "fisico")
comprobar(e.recibido == [20] and p.extra_ejecucion == 6, "nv15: Emboscada +100 %, sin remate no suma")
p11 = paso_nivel(14, True)
j2 = nuevo_jugador([p11])
p11.intentar_activar(j2)
ini = p11.tiempo_restante_activo
j2.golpear_con_arma(Enemigo(vida=5), 10, "fisico")
comprobar(p11.tiempo_restante_activo == ini, "nv14: aun sin Ejecucion")

# 9. Cuerpo de niebla: sin empuje mientras dura
comprobar(j.cuerpo_de_niebla, "Espectro activo -> cuerpo de niebla")
j.aplicar_empuje(pygame.Vector2(1, 0), 10)
comprobar(j.empuje.length() == 0, "cuerpo de niebla: no recibe empuje")
p.terminar_activo(j)
j.aplicar_empuje(pygame.Vector2(1, 0), 10)
comprobar(j.empuje.length() > 0 and not j.cuerpo_de_niebla, "al terminar vuelve el empuje")
comprobar(not nuevo_jugador([paso_nivel(10)]).cuerpo_de_niebla, "Paso 0 normal no da cuerpo de niebla")

# 10. Salir al hueco libre al terminar
centro = pygame.Vector2(0, 0)
j = nuevo_jugador([])
j.posicion = pygame.Vector2(5, 5)
roca = mundo.Roca(0, 0, 200)
movido = mundo.sacar_a_hueco_libre(j, [roca], [], [], LimiteMundo(20000, centro=centro))
comprobar(movido and not mundo.rect_circulo_colisionan(roca.rect, j.posicion, j.radio)
          and (j.posicion - pygame.Vector2(5, 5)).length() < 100 + j.radio + mundo.PASO_BUSQUEDA_HUECO * 2,
          f"dentro de una roca gigante -> sale al borde mas cercano ({j.posicion.x:.0f}, {j.posicion.y:.0f})")
j.posicion = pygame.Vector2(300, 300)
comprobar(not mundo.sacar_a_hueco_libre(j, [roca], [], [], LimiteMundo(20000, centro=centro)), "en un hueco libre no se mueve")
otro = Enemigo()
otro.posicion = pygame.Vector2(300, 300)
otro.radio = 30
tronco = (pygame.Vector2(340, 300), 20)
mundo.sacar_a_hueco_libre(j, [roca], [tronco], [otro], LimiteMundo(20000, centro=centro))
comprobar(mundo.punto_libre(j.posicion, j.radio, [roca], [tronco], [otro], LimiteMundo(20000, centro=centro)),
          "dentro de un animal junto a un tronco -> sale a un punto sin nada")
j.posicion = pygame.Vector2(9995, 0)
mundo.sacar_a_hueco_libre(j, [], [], [], LimiteMundo(20000, centro=centro))
comprobar(LimiteMundo(20000, centro=centro).dentro(j.posicion, j.radio - 0.01), "nunca queda fuera del mapa (cuadrado)")

# 11. Golpe de Suerte: el Paso 0 otorgado tambien se cancela al atacar
g = GolpeDeSuerte()
j = nuevo_jugador([g])
j.herramienta.activa = True
g.aplicar_resultado("Paso 0", j)
comprobar(j.invisible, "Golpe de Suerte otorga Paso 0")
j.herramienta.atacar(j)
j.actualizar_efectos(0.0)
comprobar(not j.invisible and not j.efectos_extra, "atacar cancela el Paso 0 otorgado")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
