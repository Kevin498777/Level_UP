"""Pruebas sin ventana: casa del spawn y vendedores ambulantes.
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_vendedores.py"""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os
import sys
import random
from collections import Counter
sys.path.insert(0, os.getcwd())
import pygame
from limite_mundo import LimiteMundo
pygame.init()

from personaje import Personaje
from herramientas import EspadaLarga
import talismanes as TL
import fauna
import vendedores as V
from spawn import Casa, RADIO_JARDIN, LADO_CASA, ANCHO_PUERTA
import mundo

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


CENTRO = pygame.Vector2(10000, 10000)
LIMITE_T = LimiteMundo(20000, centro=CENTRO)


def jugador():
    return Personaje(nombre="t", x=CENTRO.x, y=CENTRO.y, tamano=1, velocidad=3, vida=30, fuerza=3, energia=100,
                     escudo=0, escudo_magico=0, color=(0, 0, 0), habilidades=[], herramienta=EspadaLarga())


casa = Casa(CENTRO)

# 1. Casa: geometria, puerta y paredes indestructibles
comprobar(casa.contiene(CENTRO) and casa.rect.size == (LADO_CASA, LADO_CASA), "el centro del salón está dentro de la casa")
comprobar(all(p.es_cueva for p in casa.paredes) and len(casa.paredes) == 5, "5 tramos de pared indestructibles (es_cueva)")
hueco = pygame.Rect(round(CENTRO.x) - ANCHO_PUERTA // 2 + 1, casa.rect.bottom - 10, ANCHO_PUERTA - 2, 8)
comprobar(not any(p.rect.colliderect(hueco) for p in casa.paredes), "la puerta (60 px, al sur) queda libre")
comprobar(casa.punto_maniqui.y > casa.rect.bottom and casa.en_jardin(casa.punto_maniqui), "el maniquí está en el jardín, al sur")
j = jugador()
j.destino = pygame.Vector2(CENTRO.x, CENTRO.y - 400)             # intentar salir por la pared norte
for _ in range(200):
    j.mover((0, 0, 20000, 20000), LIMITE_T, casa.paredes, [])
comprobar(j.posicion.y > casa.rect.top, f"la pared norte bloquea al jugador (y={j.posicion.y:.0f})")
j = jugador()
j.destino = pygame.Vector2(CENTRO.x, CENTRO.y + 400)             # salir por la puerta
for _ in range(200):
    j.mover((0, 0, 20000, 20000), LIMITE_T, casa.paredes, [])
comprobar(j.posicion.y > casa.rect.bottom + 50, "se sale por la puerta")
comprobar(mundo.ZONA_SEGURA_SPAWN > RADIO_JARDIN, "sin rocas ni lagos en el jardín")

# 2. Fauna: ningún animal entra en el jardín
fauna.ZONA_PROHIBIDA = (CENTRO, RADIO_JARDIN)
lobo = fauna.Lobo.__new__(fauna.Lobo)
lobo.posicion, lobo.radio, lobo.vivo, lobo.vida = pygame.Vector2(CENTRO.x + 100, CENTRO.y), 12, True, 25
lobo._init_combate()
lobo._tick_efectos(1 / 60)
comprobar((lobo.posicion - CENTRO).length() >= RADIO_JARDIN + lobo.radio - 0.01, "un lobo dentro del jardín sale al borde")

# 3. Tienda: 5 anillos distintos, rarezas según probabilidad
rng = random.Random(4)
j = jugador()
conteo = Counter()
ok_distintos = True
for _ in range(4000):
    stock = V.generar_stock(j, rng)
    ok_distintos &= len(stock) == 5 and len({s["anillo"] for s in stock}) == 5
    for s in stock:
        conteo[TL.ANILLOS[s["anillo"]]["rareza"]] += 1
comprobar(ok_distintos, "cada vendedor lleva 5 anillos distintos")
total = sum(conteo.values())
reparto = {r: round(100 * c / total, 1) for r, c in conteo.items()}
comprobar(reparto[TL.COMUN] > reparto[TL.ESPECIAL] > reparto[TL.EPICO] > reparto[TL.LEGENDARIO] > 0,
          f"rarezas por anillo vendido: {reparto} (pesos 50/30/15/5, ajustados por anillos distintos)")
leg = sum(1 for _ in range(2000) if any(TL.ANILLOS[s['anillo']]['rareza'] == TL.LEGENDARIO for s in V.generar_stock(j, rng)))
comprobar(10 < leg / 20 < 40, f"un vendedor lleva el legendario en el {leg / 20:.0f} % de los casos")
comprobar(all(s["precio"] == V.PRECIOS[TL.ANILLOS[s["anillo"]]["rareza"]] for s in V.generar_stock(j, rng)),
          "precios: común 100, especial 200, épico 400, legendario 1000")
for a, d in TL.ANILLOS.items():
    if d["rareza"] != TL.COMUN:
        j.talismanes.anillos[a] = d["nivel_max"]
stock = V.generar_stock(j, rng)
comprobar(all(TL.ANILLOS[s["anillo"]]["rareza"] == TL.COMUN for s in stock) and len(stock) == 4,
          "solo ofrece anillos que puedes subir (con el resto al máximo: los 4 comunes)")

# 4. Compra
j = jugador()
sistema = V.SistemaVendedores(LIMITE_T, casa, [], j, random.Random(1))
v = sistema.vendedores[0]
v.posicion.update(j.posicion + pygame.Vector2(50, 0))
comprobar(len(sistema.vendedores) == 3 and all((x.posicion - CENTRO).length() >= V.DISTANCIA_MIN_CENTRO
                                                for x in sistema.vendedores[1:]), "3 vendedores lejos del spawn")
comprobar(v.puede_comerciar(j) and sistema.cercano(j) is v, "a 50 px se puede comerciar")
v.posicion.update(j.posicion + pygame.Vector2(200, 0))
comprobar(not v.puede_comerciar(j), "a 200 px no")
v.posicion.update(j.posicion + pygame.Vector2(50, 0))
item = v.stock[0]
j.monedas = item["precio"] - 1
texto, err = v.comprar(0, j)
comprobar(err and not item["vendido"], f"sin monedas no compra ({texto})")
j.monedas = 5000
texto, err = v.comprar(0, j)
comprobar(not err and item["vendido"] and j.talismanes.anillos[item["anillo"]] == 1 and j.monedas == 5000 - item["precio"],
          f"compra: {texto}")
comprobar(v.comprar(0, j)[1], "no se puede comprar dos veces")
for i in range(1, len(v.stock)):
    v.comprar(i, j)
v.actualizar(0.1, j)
comprobar(v.estado == "a_casa", "sin anillos que venderte se va a casa")
v.posicion.update(casa.puerta + pygame.Vector2(0, 30))
for _ in range(120):
    v.actualizar(1 / 60, j)
comprobar(v.estado == "en_casa" and not v.presente and v not in sistema.objetivos(), "entra en la casa y desaparece")
v.actualizar(V.REAPARICION + 1, j)
comprobar(v.estado == "paseo" and v.presente and (v.posicion - CENTRO).length() >= V.DISTANCIA_MIN_CENTRO
          and not any(s["vendido"] for s in v.stock), "a los 5 min sale otro lejos con anillos nuevos")

# 5. Daño: Paso 0, huida, curación; muerte por jugador vs por fauna
j = jugador()
sistema = V.SistemaVendedores(LIMITE_T, casa, [], j, random.Random(2))
v = sistema.vendedores[0]
p0 = pygame.Vector2(v.posicion)
v.recibir_dano(5, "fisico", pygame.Vector2(1, 0))
comprobar(v.invisible and v.estado == "huida" and v.vida == 15 and v not in sistema.objetivos(),
          "golpe: invisible 10 s, huye y nadie puede golpearlo")
comprobar(v.recibir_dano(50) == 0 and v.vida == 15, "invisible no recibe daño")
for _ in range(60):
    v.actualizar(1 / 60, j)
comprobar(v.posicion.x - p0.x > 100, f"huye del golpe ({v.posicion.x - p0.x:.0f} px en 1 s)")
v.actualizar(10, j)
comprobar(not v.invisible and v.vida == 20 and v.estado == "paseo", "al acabar el Paso 0 vuelve con 20 de vida")
v.recibir_dano(25)
comprobar(not v.vivo and v.estado == "muerto" and sistema.tomar_recompensa() == (20, 20), "lo matas tú: 20 XP y 20 monedas")
v.actualizar(V.REAPARICION + 1, j)
comprobar(v.vivo and v.vida == 20, "otro aparece a los 5 min")
oso = fauna.Lobo.__new__(fauna.Lobo)
oso.posicion, oso.radio, oso.vivo = pygame.Vector2(v.posicion) - pygame.Vector2(20, 0), 12, True
oso._init_combate()
fauna.golpear_objetivo(oso, v, 30)
comprobar(not v.vivo and sistema.tomar_recompensa() == (0, 0), "lo mata la fauna: sin recompensa")

# 6. Todos los anillos al máximo: no abre tienda ni vuelve a casa
j = jugador()
for a, d in TL.ANILLOS.items():
    j.talismanes.anillos[a] = d["nivel_max"]
sistema = V.SistemaVendedores(LIMITE_T, casa, [], j, random.Random(3))
v = sistema.vendedores[0]
v.posicion.update(j.posicion + pygame.Vector2(40, 0))
v.actualizar(0.5, j)
comprobar(V.todos_al_maximo(j) and not v.puede_comerciar(j) and v.estado == "paseo" and sistema.alguno_cerca(j),
          "todo al máximo: sin tienda, sigue paseando (se puede cazar)")

# 7. La fauna hostil persigue a los vendedores (presas_hostiles)
import inspect
comprobar("presas_hostiles" in inspect.signature(fauna.SistemaFauna.actualizar).parameters,
          "SistemaFauna.actualizar recibe los vendedores como objetivos de los hostiles")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
