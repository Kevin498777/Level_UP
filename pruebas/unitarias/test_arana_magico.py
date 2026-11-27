# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import sys, os
sys.path.insert(0, sys.argv[1]); os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pygame.display.set_mode((10,10))
import mundo
from habilidades import crear_habilidad, aplicar_inmovilizacion, EfectoInmovilizado
dt=1/60
def correr(m, seg):
    for _ in range(round(seg/dt)): m.actualizar(dt, None)
ar=crear_habilidad("Sombra Araña")
# 1) Nivel 1: sin daño
ar.nivel=1; ar._aplicar_nivel(); assert ar.dano_telarana==0
m=mundo.Maniqui(pygame.Vector2(0,0)); aplicar_inmovilizacion(m, ar.inmovilizacion, ar.dano_telarana)
correr(m, 5.5); assert m.vida==100 and m.escudo_magico==50, (m.vida, m.escudo_magico)
# 2) Nivel 20 con escudo magico: lo amortigua (vida baja menos de 1/s), fisico intacto
ar.nivel=20; ar._aplicar_nivel(); assert ar.dano_telarana==1 and EfectoInmovilizado.TIPO_DANO=="magico"
m=mundo.Maniqui(pygame.Vector2(0,0)); pos=pygame.Vector2(m.posicion)
aplicar_inmovilizacion(m, ar.inmovilizacion, ar.dano_telarana)
correr(m, 3.01)
print("3 ticks con escudo: vida", m.vida, "esc.mag", m.escudo_magico, "esc.fis", m.escudo)
assert m.vida > 97 and m.escudo_magico < 50 and m.escudo == 50
assert m.posicion == pos, "no debe empujarlo"
# 3) Sin escudo magico: el dano va entero a la vida
m=mundo.Maniqui(pygame.Vector2(0,0)); m.escudo_magico=0
aplicar_inmovilizacion(m, 20.0, 1); correr(m, 3.01)
print("3 ticks sin escudo: vida", m.vida); assert m.vida==97  # sin escudo no hay bloqueo (corregido)
# 4) Total en 20 s y fin del efecto
m=mundo.Maniqui(pygame.Vector2(0,0)); aplicar_inmovilizacion(m, 20.0, 1); correr(m, 21)
print("20 s con escudo: vida", m.vida, "esc.mag", m.escudo_magico, "inmovilizado", m.inmovilizado)
assert m.inmovilizado is None and round(100-m.vida + 50-m.escudo_magico,2)==18  # 20 ticks x 0.9 (10 % bloqueado)
print("OK")
