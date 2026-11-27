"""Pruebas sin ventana: potenciada Palabras Malditas (Onda Sonora nv21-30).
Uso: cd al proyecto y  SDL_VIDEODRIVER=dummy python -B ruta/test_palabras.py"""
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
from habilidades import OndaSonora, Paso0
import fauna
import mundo

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def onda(n, potenciada=True):
    h = OndaSonora()
    while h.nivel < min(n, 20):
        h.subir_nivel()
    if potenciada:
        h.desbloquear_potenciada()
        while h.nivel < n:
            assert h.subir_nivel()
    return h


def jugador(habs, vida=100):
    j = Personaje(nombre="t", x=0, y=0, tamano=1, velocidad=3, vida=vida, fuerza=3, energia=500, escudo=0,
                  escudo_magico=0, color=(0, 0, 0), habilidades=habs, herramienta=EspadaLarga())
    j.energia = 500
    j.vida_max = vida
    j.vida = vida
    return j


def lobo(x, y=0, vida=None):
    l = fauna.Lobo.__new__(fauna.Lobo)
    l.posicion, l.radio, l.vivo = pygame.Vector2(x, y), 12, True
    l._init_combate()
    l.vida = l.vida_max = vida or fauna.LOBO_VIDA
    l.recibir_dano = lambda c, t="fisico", d=None, l=l: _dano(l, c)
    return l


def _dano(l, c):
    l.vida = max(0.0, round(l.vida - c, 2))
    if l.vida <= 0:
        l.vivo = False
    return c


def correr(h, enemigos, segundos=2.0, dt=1 / 60):
    for _ in range(round(segundos / dt)):
        h.actualizar_ondas(dt, enemigos)


def lanzar(h, j, clave=None):
    h.palabra_pendiente = next((p for p in h.PALABRAS if p["clave"] == clave), None)
    ok = h.intentar_activar(j)
    h.palabra_pendiente = None
    return ok


# 1. Escalado y desbloqueos
for n, obj, nombres in ((20, 3, []), (21, 3, ["Huye", "Sal volado"]), (23, 4, ["Huye", "Sal volado", "No te muevas"]),
                        (25, 4, ["Huye", "Sal volado", "No te muevas", "Duerme"]), (27, 5, ["Huye", "Sal volado", "No te muevas", "Duerme", "Explota"]),
                        (30, 6, ["Huye", "Sal volado", "No te muevas", "Duerme", "Explota", "Muere"])):
    h = onda(n)
    comprobar(h.max_objetivos == obj and [p["nombre"] for p in h.palabras_disponibles()] == nombres
              and h.danos_ondas == (30,) and h.radio == 480 and h.duracion_cooldown == 8 and h.costo_energia == 30,
              f"nv{n}: {h.max_objetivos} objetivo(s), palabras {len(nombres)}, anillo 30, radio 480, pulso 30 En./8 s")
h = onda(30)
valores = {p["clave"]: h.valor_palabra(p) for p in h.PALABRAS if p["efecto"]}
comprobar(valores == {"huye": 5.0, "sal_volado": 60, "no_te_muevas": 3.0, "duerme": 10.0, "explota": 40},
          f"nv30: {valores}")
h = onda(23)
comprobar(h.valor_palabra(h.PALABRAS[2]) == 1.5 and h.valor_palabra(h.PALABRAS[0]) == 2.67,
          "al desbloquearse empiezan en su mínimo (No te muevas nv23 1.5 s; Huye nv23 2.67 s)")
comprobar(onda(20).nombre_mostrado == "Palabras Malditas" and onda(20).cargable and not onda(20, False).cargable,
          "nv20 desbloqueada ya es Palabras Malditas (mantener = ruleta); la normal no")
comprobar(onda(20, False).max_objetivos is None and onda(20, False).danos_ondas == (10, 20, 30),
          "Onda Sonora normal sin cambios")

# 2. Pulso: un anillo de 30 a los N más cercanos, sin coste de vida
h = onda(20)
j = jugador([h])
cerca, medio, lejos = lobo(60, vida=100), lobo(120, vida=100), lobo(200, vida=100)
otro = lobo(90, vida=100)
comprobar(lanzar(h, j) and j.vida == 100 and j.energia == 470 and h.tiempo_restante_cooldown == 8,
          "pulso: 30 En., sin vida, 8 s de recarga")
correr(h, [lejos, medio, cerca, otro])
comprobar(cerca.vida == 70 and otro.vida == 70 and medio.vida == 70 and lejos.vida == 100,
          f"nv20: solo los 3 más cercanos reciben 30 ({cerca.vida}, {otro.vida}, {medio.vida}, {lejos.vida})")
comprobar(abs(cerca.ralentizacion - 0.20) < 1e-9, "ralentiza 20 %")

# 3. Huye, Sal volado, No te muevas, Duerme
h = onda(30)
j = jugador([h])
l = lobo(100, vida=100)
lanzar(h, j, "huye")
correr(h, [l], 1.0)
comprobar(l.huida is not None and l.controlado and j.vida == 99, "Huye: el lobo huye y te cuesta 1 de vida")
x0 = l.posicion.x
l._tick_efectos(1.0)
comprobar(l.posicion.x > x0 + 100, f"huye alejándose ({l.posicion.x - x0:.0f} px en 1 s)")
l._tick_efectos(5.0)
comprobar(l.huida is None and not l.controlado, "a los 5 s deja de huir")

h.estado = "LISTA"
l = lobo(100, vida=100)
lanzar(h, j, "sal_volado")
correr(h, [l], 2.0)
comprobar(l.posicion.x > 100 + 300, f"Sal volado: sale despedido ({l.posicion.x - 100:.0f} px)")

h.estado = "LISTA"
l = lobo(100, vida=100)
lanzar(h, j, "no_te_muevas")
correr(h, [l], 1.0)
comprobar(l.inmovilizado is not None and abs(l.inmovilizado.restante - 3.0) < 0.8 and l.controlado,
          "No te muevas: paralizado ~3 s")

h.estado = "LISTA"
l = lobo(100, vida=100)
lanzar(h, j, "duerme")
correr(h, [l], 1.0)
comprobar(l.dormido is not None and l.controlado, "Duerme: dormido")
l._tick_efectos(0.1)
comprobar(l.dormido is not None, "sigue dormido sin recibir daño")
l.vida -= 1
l._tick_efectos(0.1)
comprobar(l.dormido is None, "se despierta al recibir daño")

# 4. Explota: daño extra, área y te alcanza si estás cerca
h.estado = "LISTA"
j = jugador([h])
obj, vecino, ajeno = lobo(40, vida=200), lobo(80, vida=200), lobo(600, vida=200)
lanzar(h, j, "explota")
correr(h, [obj, vecino, ajeno], 2.0)
# Cada objetivo alcanzado explota: 30 del anillo + 40 propios + 20 del area del otro
comprobar(obj.vida == 200 - 30 - 40 - 20 and vecino.vida == 200 - 30 - 40 - 20,
          f"Explota: cada alcanzado recibe 30 + 40 y 20 del área del vecino ({obj.vida}, {vecino.vida})")
comprobar(ajeno.vida == 200, "fuera del radio no recibe nada")
comprobar(j.vida == 100 - 8 - 20 - 20, f"a ti: 8 de coste + 20 por cada explosión a 60 px ({j.vida})")

# 5. Muere: solo el más fuerte; mata bajo el 30 %, si no quita el 90 %
h.estado = "LISTA"
j = jugador([h])
debil, fuerte = lobo(50, vida=100), lobo(150, vida=100)
fuerte.vida = 90
debil.vida = 50
lanzar(h, j, "muere")
correr(h, [debil, fuerte], 2.0)
comprobar(debil.vida == 50 and fuerte.vida == 6, f"Muere al más fuerte: (90-30)=60 -> 6; el otro intacto ({fuerte.vida}, {debil.vida})")
comprobar(j.vida == 50 and j.energia == 400 and h.tiempo_restante_cooldown <= 60,
          f"te cuesta el 50 % de tu vida y 100 En. ({j.vida}, {j.energia})")
h.estado = "LISTA"
j.vida = 25                     # bajo el 30 % de tu vida máxima (100)
f2 = lobo(50, vida=100)
f2.vida = 55                    # 55 - 30 del anillo = 25 < 30 % -> muere
lanzar(h, j, "muere")
correr(h, [f2], 2.0)
comprobar(not f2.vivo, "bajo el 30 % de su vida máxima: muere al instante")
comprobar(j.vida == 2.5, f"tú bajo el 30 %: te quita el 90 % ({j.vida})")

# 6. Eco: si no alcanza a nadie, se cobra otra vez la vida
h.estado = "LISTA"
j = jugador([h])
lanzar(h, j, "explota")
correr(h, [lobo(2000)], 3.0)
comprobar(j.vida == 100 - 16, f"Eco: falló y pagaste 8 dos veces ({j.vida})")
h.estado = "LISTA"
j.vida = 1
lanzar(h, j, "sal_volado")
correr(h, [], 3.0)
comprobar(j.vida == 1, "pronunciar nunca baja tu vida de 1")

# 7. Ruleta: casillas por ángulo
h = onda(30)
h._pos_jugador = pygame.Vector2(500, 500)
h._desplazamiento = (0, 0)
casos = {(500, 400): 0, (590, 450): 1, (590, 550): 2, (500, 600): 3, (410, 550): 4, (410, 450): 5, (505, 505): None}
reales = {p: h._indice_ruleta(p) for p in casos}
comprobar(reales == casos, f"ruleta: arriba Huye y en sentido horario; el centro no elige ({reales})")
h = onda(21)
h._pos_jugador, h._desplazamiento = pygame.Vector2(500, 500), (0, 0)
pygame.mouse.set_pos = None
comprobar(h.PALABRAS[5] not in h.palabras_disponibles(), "Muere bloqueada en nv21")

# 8. Mantener y soltar: pulsación corta = pulso; lanzar rompe Paso 0
h = onda(30)
p = Paso0()
j = jugador([h, p])
p.intentar_activar(j)
h.iniciar_carga(j)
h.actualizar(0.1, j)
h.soltar_carga(j)
comprobar(h.estado == "COOLDOWN" and h.tiempo_restante_cooldown == 8 and not j.invisible,
          "pulsación corta: pulso sin palabra (y cancela Paso 0)")

# 9. Maniquí: dormido o paralizado no ataca
m = mundo.Maniqui(pygame.Vector2(0, 0))
comprobar(not m.controlado, "maniquí libre")
from habilidades import aplicar_sueno
aplicar_sueno(m, 5.0)
comprobar(m.controlado, "maniquí dormido: controlado (no ataca)")

print()
print("TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
