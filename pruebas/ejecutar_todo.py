"""Ejecuta todas las pruebas del proyecto sin ventana y muestra un resumen N/N OK.

Uso (desde la carpeta del proyecto):
    python -B pruebas/ejecutar_todo.py              todas (unitarias + humo)
    python -B pruebas/ejecutar_todo.py unitarias    solo una carpeta
    python -B pruebas/ejecutar_todo.py veneno       solo las que contienen ese texto en el nombre
    (los textos se combinan: todos deben aparecer en el nombre)

- unitarias/: pruebas de la logica, sin el bucle del juego (rapidas).
- humo/: arrancan el bucle real (mundo.iniciar_mundo) con eventos simulados y sin ventana.
- pendientes/: no se ejecutan aqui (ver el plan de NPC, Fase 0).
Una prueba falla si termina con error o si escribe una linea que empieza por FALLO.
"""
import os
import re
import subprocess
import sys
import time

CARPETA = os.path.dirname(os.path.abspath(__file__))
PROYECTO = os.path.dirname(CARPETA)
GRUPOS = ("unitarias", "humo")
TIEMPO_MAXIMO = 300             # s por prueba
LINEA_FALLO = re.compile(r"^\s*\[?FALLO(?!S)", re.M)      # "FALLOS: 0" no es un fallo


def buscar_pruebas(filtros):
    grupos = [g for g in GRUPOS if g in filtros] or list(GRUPOS)
    textos = [f for f in filtros if f not in GRUPOS]
    pruebas = []
    for g in grupos:
        for nombre in sorted(os.listdir(os.path.join(CARPETA, g))):
            if nombre.endswith(".py") and all(t in nombre for t in textos):
                pruebas.append((g, nombre))
    return pruebas


def ejecutar(grupo, nombre):
    """Devuelve (ok, segundos, salida)."""
    entorno = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", PYTHONIOENCODING="utf-8")
    inicio = time.perf_counter()
    try:
        p = subprocess.run([sys.executable, "-B", os.path.join(CARPETA, grupo, nombre)], cwd=PROYECTO,
                           env=entorno, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIEMPO_MAXIMO)
        salida = p.stdout + p.stderr
        ok = p.returncode == 0 and not LINEA_FALLO.search(salida)
    except subprocess.TimeoutExpired:
        salida, ok = "Tiempo agotado (%d s)" % TIEMPO_MAXIMO, False
    return ok, time.perf_counter() - inicio, salida


def main():
    pruebas = buscar_pruebas(sys.argv[1:])
    if not pruebas:
        print("No hay pruebas que coincidan.")
        return 1
    fallidas = []
    inicio = time.perf_counter()
    for grupo, nombre in pruebas:
        ok, seg, salida = ejecutar(grupo, nombre)
        print("%-5s %-10s %-28s %5.1f s" % ("OK" if ok else "FALLO", grupo, nombre, seg), flush=True)
        if not ok:
            fallidas.append((grupo, nombre, salida))
    for grupo, nombre, salida in fallidas:
        print("\n=== %s/%s" % (grupo, nombre))
        lineas = [l for l in salida.splitlines() if LINEA_FALLO.match(l)] or salida.splitlines()[-15:]
        print("\n".join(lineas))
    total, bien = len(pruebas), len(pruebas) - len(fallidas)
    print("\n%d/%d OK en %.0f s%s" % (bien, total, time.perf_counter() - inicio,
                                     "  ->  TODO OK" if not fallidas else ""))
    return 0 if not fallidas else 1


if __name__ == "__main__":
    sys.exit(main())
