"""Pruebas sin ventana de la semilla fija del mundo (Fase 0 del plan de NPC):
- con SEMILLA_MUNDO, dos arranques (dos procesos) dan exactamente el mismo terreno (lagos, rocas,
  arbustos, arboles, cuevas de oso, bosques y praderas);
- otra semilla da otro terreno;
- la semilla solo fija el terreno: el azar de despues (fauna, cofres...) sigue siendo libre.
Uso: python -B pruebas/unitarias/test_semilla_mundo.py"""
import os
import sys
import hashlib
import random
import subprocess
PROY = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, PROY); os.chdir(PROY)
import pygame
pygame.init()
import mundo

fallos = []


def comprobar(cond, texto):
    print(("OK   " if cond else "FALLO ") + texto)
    if not cond:
        fallos.append(texto)


def huella(charcos, vegetacion, rocas):
    """Resumen (hash) de todo el terreno: lagos, rocas, arbustos, arboles, pasto, flores y zonas."""
    h = hashlib.sha256()
    def meter(*valores):
        h.update(repr(tuple(round(v, 3) if isinstance(v, float) else v for v in valores)).encode())
    for c in charcos:
        meter("lago", c.centro.x, c.centro.y, c.radio, len(c.circulos))
    for r in rocas:
        meter("roca", tuple(r.rect), getattr(r, "es_cueva", False), getattr(r, "angulo_entrada", None))
    for a in vegetacion.arbustos:
        meter("arbusto", a.centro.x, a.centro.y, a.radio, a.tipo)
    for a in vegetacion.arboles:
        meter("arbol", tuple(a.rect), a.tipo)
    meter("pasto", len(vegetacion.pasto), "flores", len(vegetacion.flores))
    for zonas in (vegetacion.bosques, vegetacion.praderas):
        for c, r in zonas:
            meter("zona", c[0], c[1], r)
    return h.hexdigest(), (len(charcos), len(rocas), len(vegetacion.arbustos), len(vegetacion.arboles))


if len(sys.argv) > 1 and sys.argv[1] == "--huella":
    # Modo auxiliar: imprime la huella del terreno de este proceso (semilla opcional)
    semilla = int(sys.argv[2]) if len(sys.argv) > 2 else mundo.SEMILLA_MUNDO
    print(huella(*mundo.generar_terreno(semilla))[0])
    sys.exit(0)


def huella_en_proceso(semilla=None):
    args = [sys.executable, "-B", os.path.abspath(__file__), "--huella"] + ([str(semilla)] if semilla is not None else [])
    p = subprocess.run(args, cwd=PROY, capture_output=True, text=True,
                       env=dict(os.environ, SDL_VIDEODRIVER="dummy"))
    return p.stdout.strip().splitlines()[-1] if p.stdout.strip() else "error: " + p.stderr[-300:]


print("--- Semilla fija del terreno")
comprobar(isinstance(mundo.SEMILLA_MUNDO, int), "SEMILLA_MUNDO definida (%s)" % mundo.SEMILLA_MUNDO)
comprobar(mundo.NPC_ACTIVOS is False, "NPC_ACTIVOS existe y esta apagado")
a = huella_en_proceso()
b = huella_en_proceso()
comprobar(len(a) == 64 and a == b, "dos arranques dan exactamente el mismo terreno")
random.seed(12345)                      # el estado previo del azar no influye en el terreno
terreno = mundo.generar_terreno()
local, cuenta = huella(*terreno)
cuevas = [r for r in terreno[2] if getattr(r, "es_cueva", False)]
comprobar(mundo.FAUNA.OSO_MIN <= len(cuevas) <= mundo.FAUNA.OSO_MAX and all(r.gigante for r in cuevas),
          "el terreno trae sus cuevas de oso (%d, en rocas gigantes)" % len(cuevas))
sf = mundo.FAUNA.SistemaFauna(mundo.LIMITE, terreno[1], terreno[0], terreno[2])
comprobar(sorted(tuple(o.cueva) for o in sf.osos) == sorted(tuple(r.rect.center) for r in cuevas), "la fauna pone un oso en cada cueva del terreno")
comprobar(sorted(round(o.entrada_dir.angle_to((1, 0)), 3) for o in sf.osos) ==
          sorted(round(pygame.Vector2(1, 0).rotate_rad(r.angulo_entrada).angle_to((1, 0)), 3) for r in cuevas),
          "la entrada de cada cueva tambien es fija")
comprobar(local == a, "el terreno no depende del azar previo (mismo mapa dentro de este proceso)")
print("      lagos %d, rocas %d, arbustos %d, arboles %d" % cuenta)
comprobar(huella_en_proceso(mundo.SEMILLA_MUNDO + 1) != a, "otra semilla da otro terreno")

print("--- Lo demas sigue siendo aleatorio")
random.seed(777); esperado = [random.random() for _ in range(5)]
random.seed(777); mundo.generar_terreno(); despues = [random.random() for _ in range(5)]
comprobar(despues == esperado, "generar el terreno deja el azar global como estaba")
random.seed()
x = [random.random() for _ in range(3)]; mundo.generar_terreno(); y = [random.random() for _ in range(3)]
mundo.generar_terreno(); z = [random.random() for _ in range(3)]
comprobar(x != y != z, "tras el terreno, las tiradas siguientes no se repiten (fauna, cofres, botin)")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
