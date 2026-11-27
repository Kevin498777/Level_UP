"""Pruebas sin ventana de la Fase 2 del plan de NPC: mapa cuadrado guardado en archivo.

- Equivalencia: el mundo cargado del archivo es identico al guardado y dos cargas dan lo mismo.
- Arranque: cargar el mapa no tarda mas que generarlo.
- Validador: pasa con el mapa principal y falla, con un mensaje claro, en mapas rotos.
- Limite cuadrado: nada sale del cuadrado ni queda pegado al borde y las esquinas son accesibles.
- Respaldo: sin archivo, el juego genera el terreno con la semilla fija.
Uso: python -B pruebas/unitarias/test_mapa.py"""
import copy
import hashlib
import os
import sys
import time
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
import mundo
import mapa
import herramientas
import vendedores as VEND
from limite_mundo import LIMITE, BORDE_LIBRE
from personaje import Personaje
from spawn import Casa

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def huella(charcos, veg, rocas):
    h = hashlib.sha256()
    meter = lambda *v: h.update(repr(v).encode())
    for c in charcos:
        meter("lago", round(c.centro.x, 1), round(c.centro.y, 1), c.radio, [(round(p.x, 2), round(r, 2)) for p, r in c.circulos])
    for r in rocas:
        meter("roca", tuple(r.rect), r.color, getattr(r, "es_cueva", False), getattr(r, "angulo_entrada", None))
    for a in veg.arboles:
        meter("arbol", tuple(a.rect), a.tipo, a.lobulos, a.ramas)
    for a in veg.arbustos:
        meter("arbusto", round(a.centro.x, 1), a.radio, a.tipo, [(round(p.x, 2), round(r, 2)) for p, r in a.circulos])
    meter("pasto", [(round(p.centro.x, 1), p.briznas[0][1]) for p in veg.pasto])
    meter("flores", [(round(f.centro.x, 1), f.alto) for f in veg.flores])
    meter("zonas", veg.bosques and [(round(c.x, 1), r) for c, r in veg.bosques], [(round(c.x, 1), r) for c, r in veg.praderas])
    return h.hexdigest()


# ------------------------------------------------------------ 1. Archivo y equivalencia
print("--- Mapa guardado")
datos = mapa.leer("principal")
comprobar(datos["version"] == mapa.VERSION_FORMATO and datos["lado"] == LIMITE.lado, "mapas/principal.json existe, version %d, %d px" %
          (datos["version"], datos["lado"]))
t0 = time.perf_counter()
cargado = mapa.construir(datos)
t_carga = time.perf_counter() - t0
otra = mapa.construir(mapa.leer("principal"))
comprobar(huella(*cargado) == huella(*otra), "dos cargas del archivo dan exactamente el mismo mundo")
charcos, veg, rocas = cargado
comprobar(len(charcos) == len(datos["lagos"]) and len(rocas) == len(datos["rocas"]) and len(veg.arboles) == len(datos["arboles"])
          and len(veg.arbustos) == len(datos["arbustos"]) and len(veg.pasto) == len(datos["pasto"]),
          "se carga todo lo guardado (%d lagos, %d rocas, %d arboles, %d arbustos)" % (len(charcos), len(rocas), len(veg.arboles), len(veg.arbustos)))
iguales = all(r.rect.topleft == (round(x - lado / 2), round(y - lado / 2)) and r.rect.width == lado and bool(getattr(r, "es_cueva", False)) == bool(cueva)
              for r, (x, y, lado, _s, cueva, _a) in zip(rocas, datos["rocas"]))
iguales &= all((round(a.centro.x, 1), round(a.centro.y, 1), a.tipo, a.radio_copa) == (x, y, t, rc)
               for a, (x, y, t, _e, _rt, rc, _s) in zip(veg.arboles, datos["arboles"]))
comprobar(iguales, "posiciones, tamanos y tipos identicos a los del archivo")
# guardar y volver a leer no cambia nada
ruta_tmp = mapa.guardar(dict(datos, nombre="_prueba_tmp"), "_prueba_tmp")
try:
    comprobar(mapa.leer("_prueba_tmp") == dict(datos, nombre="_prueba_tmp"), "guardar y leer el archivo conserva todos los datos")
finally:
    os.remove(ruta_tmp)
t0 = time.perf_counter()
mundo.generar_terreno(1, mapa.DISENOS["principal"])
t_gen = time.perf_counter() - t0
comprobar(t_carga <= t_gen * 1.5, "cargar el mapa (%.2f s) no tarda mas que generarlo (%.2f s)" % (t_carga, t_gen))

# ------------------------------------------------------------ 2. Validador
print("--- Validador (Anexo E)")
errores, avisos, info = mapa.validar(datos, *cargado)
comprobar(not errores, "el mapa principal pasa el validador %s" % (errores or ""))
print("      %s" % {k: v for k, v in info.items() if not k.startswith("_")})


def roto(cambio, texto_esperado):
    d = copy.deepcopy(datos)
    cambio(d)
    e, _, _ = mapa.validar(d)
    comprobar(any(texto_esperado in x for x in e), "mapa roto -> '%s' (%s)" % (texto_esperado, "; ".join(e) or "sin errores"))


def pocas_cuevas(d):
    for r in d["rocas"][:]:
        if r[4] and sum(x[4] for x in d["rocas"]) > 5:
            r[4] = 0


def cerca_del_borde(d):
    d["rocas"].append([LIMITE.rect.left + 100, LIMITE.centro.y, 40, 1, 0, 0.0])


def guardian_ocupado(d):
    g = next(z for z in d["zonas"] if z["nombre"] == "Guardian")
    d["rocas"].append([g["x"] + 100, g["y"], 60, 1, 0, 0.0])


def zona_aislada(d):
    # un anillo de rocas cerrado (sin huecos) alrededor de un claro: queda aislado
    zona = mapa.pygame.Vector2(LIMITE.centro.x + 2200, LIMITE.centro.y + 2200)
    for k in range(-6, 7):
        for x, y in ((zona.x + k * 100, zona.y - 600), (zona.x + k * 100, zona.y + 600),
                     (zona.x - 600, zona.y + k * 100), (zona.x + 600, zona.y + k * 100)):
            d["rocas"].append([round(x), round(y), 110, 1, 0, 0.0])


def pasillo_estrecho(d):
    # el mismo anillo con una entrada de 50 px: no llega a los 80 px de pasillo
    zona_aislada(d)
    zona = (LIMITE.centro.x + 2200, LIMITE.centro.y + 2200 + 600)
    d["rocas"][:] = [r for r in d["rocas"] if not (r[1] == round(zona[1]) and abs(r[0] - zona[0]) < 60)]
    d["rocas"].append([round(zona[0]) - 80, round(zona[1]), 110, 1, 0, 0.0])


roto(pocas_cuevas, "cuevas de oso")
roto(cerca_del_borde, "del borde")
roto(guardian_ocupado, "guardian no esta despejada")
roto(zona_aislada, "zonas grandes aisladas")
roto(pasillo_estrecho, "zonas grandes aisladas")

# ------------------------------------------------------------ 3. Limite cuadrado
print("--- Limite cuadrado")
dentro = all(LIMITE.dentro(r.rect.center, r.rect.width / 2) for r in rocas) and \
    all(LIMITE.dentro(a.centro, BORDE_LIBRE - 1) for a in veg.arboles + veg.arbustos) and \
    all(LIMITE.dentro(c.centro, c.radio) for c in charcos)
comprobar(dentro, "la generacion no coloca nada fuera del cuadrado (ni a menos de %d px del borde)" % BORDE_LIBRE)
j = Personaje("T", 0, 0, 1, 3, 20, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"))
lim = (0, 0, mundo.TAMANO_MUNDO, mundo.TAMANO_MUNDO)
for esquina in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
    j.posicion = LIMITE.centro + pygame.Vector2(esquina) * (LIMITE.mitad - 200)
    j.destino = LIMITE.centro + pygame.Vector2(esquina) * (LIMITE.mitad + 500)
    for _ in range(400):
        j.mover(lim, LIMITE, [], [])
    comprobar(LIMITE.dentro(j.posicion, j.radio - 0.01) and LIMITE.distancia_al_borde(j.posicion) < j.radio + 2,
              "el personaje llega a la esquina %s y no sale del cuadrado" % (esquina,))
j.posicion = LIMITE.centro + pygame.Vector2(LIMITE.mitad - 5, 0)
j.aplicar_empuje(pygame.Vector2(1, 0), 30)
for _ in range(60):
    j.actualizar_empuje(1 / 60, LIMITE)
comprobar(LIMITE.dentro(j.posicion, j.radio - 0.01), "el empuje no lo saca del cuadrado")
j.posicion = LIMITE.centro + pygame.Vector2(LIMITE.mitad + 50, 0)
mundo.sacar_a_hueco_libre(j, [], [], [], LIMITE)
comprobar(LIMITE.dentro(j.posicion, j.radio - 0.01), "sacar_a_hueco_libre deja dentro del cuadrado")
j.proyectiles = [type("P", (), {"posicion": LIMITE.centro + pygame.Vector2(LIMITE.mitad + 30, 0), "radio": 6})()]
comprobar(not [p for p in j.proyectiles if LIMITE.dentro(p.posicion, -p.radio)], "un proyectil fuera del cuadrado desaparece")
sv = VEND.SistemaVendedores(LIMITE, Casa(mundo.CENTRO_MUNDO), charcos, j)
puntos = [sv.punto_al_azar(mapa.random.Random(k)) for k in range(200)]
comprobar(all(LIMITE.dentro(p, VEND.MARGEN_BORDE) for p in puntos) and LIMITE.dentro(sv.dentro_del_mapa(LIMITE.centro + pygame.Vector2(99999, 0)), 1),
          "los vendedores pasean dentro del cuadrado")
rejilla = mapa.Rejilla(charcos, veg, rocas, mapa.RADIO_PERSONAJE)
alcanzado = rejilla.alcanzables(Casa(mundo.CENTRO_MUNDO).puerta + pygame.Vector2(0, 60))
esquinas = [LIMITE.centro + pygame.Vector2(sx, sy) * (LIMITE.mitad - 60) for sx in (-1, 1) for sy in (-1, 1)]
comprobar(all(alcanzado[rejilla.celda_de(p)[1] * rejilla.ancho + rejilla.celda_de(p)[0]] for p in esquinas),
          "las cuatro esquinas del mapa se alcanzan andando desde la casa")
comprobar(os.path.exists(mapa.ruta_rutas("principal")), "la rejilla de rutas esta guardada (mapas/principal_rutas.bin)")

# ------------------------------------------------------------ 4. Respaldo
print("--- Respaldo")
resultado, motivo = mapa.cargar_terreno("no_existe")
comprobar(resultado is None and motivo, "sin archivo: aviso (%s) y el juego genera con la semilla fija" % motivo[:40])

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
