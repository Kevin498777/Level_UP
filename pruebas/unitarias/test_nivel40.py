# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Nivel maximo 40 (fase 3, parte 1). Uso: python -B test_nivel40.py <proyecto>
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import personaje as P, gacha as G, herramientas
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def nuevo():
    return Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"), 0)

check(P.NIVEL_MAXIMO == 40 and len(P.XP_POR_NIVEL) == 39, "nivel maximo 40 con 39 saltos de XP")
check(sum(P.XP_POR_NIVEL[:19]) == 1048, "1 -> 20 sigue costando 1048 XP")
check(sum(P.XP_POR_NIVEL[19:29]) == 2780 and sum(P.XP_POR_NIVEL[29:]) == 5630 and sum(P.XP_POR_NIVEL) == 9458,
      "20 -> 30: 2780, 30 -> 40: 5630, total 9458")
check(all(b > a for a, b in zip(P.XP_POR_NIVEL, P.XP_POR_NIVEL[1:])), "cada salto cuesta mas que el anterior")
# Subir por XP desde el 1 hasta el 40
j = nuevo()
j.ganar_xp(1048)
check(j.nivel == 20 and j.xp == 0 and j.xp_siguiente == 180, "con 1048 XP justo nivel 20 y faltan 180 (no MAX)")
check(j.puntos_mejora == 4 + 19 * 4 and j.monedas == 19 * 20, "nivel 20: 80 puntos y 380 monedas")
check(G.gacha_mejorado(j) and G.costo_tirada(j) == 20, "en el 20 se habilita el Gacha mejorado")
j.ganar_xp(2780)
check(j.nivel == 30 and j.xp == 0, "con 2780 mas llega justo al 30")
j.ganar_xp(5629)
check(j.nivel == 39 and j.xp == 719, "a 1 XP del 40 sigue en el 39 (719/720)")
j.ganar_xp(1)
check(j.nivel == 40 and j.xp_siguiente is None and j.xp == 0, "con la ultima XP llega al 40 (MAX)")
check(j.puntos_mejora == 4 + 39 * 4 and j.monedas == 39 * 20, "nivel 40: 160 puntos y 780 monedas")
check(j.ganar_xp(10 ** 6) == 0 and j.nivel == 40 and j.puntos_mejora == 160, "en el 40 la XP ya no suma ni da puntos")
# varios niveles de golpe y sobrante
j = nuevo(); j.ganar_xp(1048 + 180 + 50)
check(j.nivel == 21 and j.xp == 50, "XP de golpe: sube varios niveles y guarda el sobrante (nv21, 50)")
# [L]
j = nuevo()
for _ in range(60): j.subir_nivel()
check(j.nivel == 40 and j.puntos_mejora == 160, "[L] sube hasta el 40 y se detiene")
# muerte: vuelve al 1
j = nuevo(); j.ganar_xp(5000); j.__init__("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta("Espada Larga"), 0)
check(j.nivel == 1 and j.puntos_mejora == 4 and not G.gacha_mejorado(j), "al reaparecer (sin totem) vuelve al nivel 1 y al Gacha normal")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
