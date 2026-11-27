"""Generador asistido de mapas (Fase 2 del plan de NPC). Nunca abre ventana.

Genera el mapa con las reglas de su diseno (diseno_mapa.py), lo valida (Anexo E del plan), y si
pasa lo guarda en mapas/<nombre>.json con su rejilla de rutas y su vista previa en PNG.

Uso (desde la carpeta del proyecto):
    python -B herramientas_mapa/generar_mapa.py                 mapa principal, semilla 1
    python -B herramientas_mapa/generar_mapa.py principal 7     otra semilla
    python -B herramientas_mapa/generar_mapa.py --forzar        guarda aunque no pase el validador
"""
import os
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROYECTO)
os.chdir(PROYECTO)
import pygame
pygame.init()
import mapa


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    nombre = args[0] if args else "principal"
    semilla = int(args[1]) if len(args) > 1 else 1
    t0 = time.perf_counter()
    datos = mapa.generar(nombre, semilla)
    objetos = mapa.construir(datos)
    errores, avisos, info = mapa.validar(datos, *objetos)
    bolsas = info.pop("_bolsas")
    print("Mapa '%s' (semilla %d) generado en %.1f s" % (nombre, semilla, time.perf_counter() - t0))
    for clave, valor in info.items():
        print("  %-24s %s" % (clave, valor))
    for a in avisos:
        print("AVISO", a)
    for e in errores:
        print("ERROR", e)
    png = mapa.vista_previa(datos, os.path.join(mapa.CARPETA, nombre + "_vista.png"), *objetos, bolsas=bolsas)
    print("Vista previa:", png)
    if errores and "--forzar" not in sys.argv:
        print("No se guarda: el mapa no pasa el validador (usa --forzar para guardarlo igualmente).")
        return 1
    print("Guardado:", mapa.guardar(datos))
    rejilla = mapa.Rejilla(*objetos, mapa.RADIO_PERSONAJE)
    rejilla.guardar(mapa.ruta_rutas(nombre))
    print("Rejilla de rutas:", mapa.ruta_rutas(nombre))
    return 0


if __name__ == "__main__":
    sys.exit(main())
