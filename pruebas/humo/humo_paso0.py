# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import sys, os
sys.path.insert(0, sys.argv[1]); os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame, mundo, habilidades as H
from herramientas import crear_herramienta
real_get=pygame.event.get; frame=[0]; estados=[]
class T:
    def __getitem__(self,k): return False
pygame.key.get_pressed=lambda: T()
def ev(t,k): return pygame.event.Event(t,key=k,mod=0,unicode="",scancode=0)
p0=H.crear_habilidad("Paso 0")
def get(*a,**k):
    real_get(); f=frame[0]; frame[0]+=1; out=[]
    if f==10: out.append(ev(pygame.KEYDOWN,pygame.K_2))
    if f in (20,): estados.append(("activo",p0.estado))
    if f==299: out.append(ev(pygame.KEYDOWN,pygame.K_ESCAPE))
    return out
pygame.event.get=get
r=mundo.iniciar_mundo({"nombre":"t","habilidades":[p0],"herramienta":crear_herramienta("Espada Ligera")})
print(r, estados, "estado final", p0.estado)
assert r == "salir" and estados and estados[0][1] == "ACTIVA", "Paso 0 no se activo en el bucle real"
print("TODO OK")
