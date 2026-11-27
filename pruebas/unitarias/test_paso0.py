# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import sys, os, random
sys.path.insert(0, sys.argv[1]); os.environ["SDL_VIDEODRIVER"]="dummy"
import pygame; pygame.init(); pantalla=pygame.display.set_mode((800,600))
import mundo, habilidades as H
from personaje import Personaje
from herramientas import crear_herramienta
dt=1/60
def pj(habs=None):
    return Personaje("t",0,0,1,1,20,2,100,0,(0,150,255),habs or [],crear_herramienta("Espada Ligera"))
# 1) Escalado por tramos
p=H.crear_habilidad("Paso 0"); tabla=[]
for n in range(1,11):
    p.nivel=n; p._aplicar_nivel(); tabla.append((n,p.duracion_activa,p.costo_energia,p.duracion_cooldown))
print(tabla)
# Escalado lineal nv1 -> nv10: duracion 6 -> 15 s, coste 20 -> 60, recarga 8 -> 16 s
assert tabla[0][1:]==(6.0,20,8.0) and tabla[-1][1:]==(15.0,60,16.0)
assert all(a[1]<=b[1] and a[2]<=b[2] and a[3]<=b[3] for a,b in zip(tabla,tabla[1:]))
p=H.crear_habilidad("Paso 0"); assert p.nivel_max==10 and p.costo_mejora==2
for _ in range(15): p.subir_nivel()
assert p.nivel==10
# 2) Activacion, invisibilidad, recarga al terminar, coste y combo
p=H.crear_habilidad("Paso 0"); j=pj([p])
assert j.detectable and not j.invisible
assert p.intentar_activar(j) and j.energia==80 and j.invisible and not j.detectable
for _ in range(round(5.9/dt)): p.actualizar(dt,j)
assert j.invisible
j.recibir_dano(5,"fisico"); assert j.invisible and j.vida<20      # recibe dano y sigue invisible
for _ in range(round(0.2/dt)): p.actualizar(dt,j)
assert not j.invisible and p.estado=="COOLDOWN" and abs(p.tiempo_restante_cooldown-8)<0.2
d=H.crear_habilidad("Destello"); j2=pj([d,H.crear_habilidad("Paso 0")]); d.intentar_activar(j2); e=j2.energia
j2.habilidades[1].intentar_activar(j2); print("combo cobra", e-j2.energia); assert e-j2.energia==j2.habilidades[1].costo_energia+round(e*0.05)
# 3) Maniqui no detecta invisible ni oculto; un golpe en marcha sigue
m=mundo.Maniqui(pygame.Vector2(0,0)); j=pj([H.crear_habilidad("Paso 0")]); j.posicion=pygame.Vector2(40,0)
m.angulo=0; j.habilidades[0].intentar_activar(j)
for _ in range(round(2.5/dt)): m.actualizar(dt,j)
print("invisible: angulo",m.angulo,"golpeando",m.herramienta.golpeando,"t",round(m.tiempo_desde_ataque,2))
assert m.angulo==0 and not m.herramienta.golpeando
j.habilidades[0].estado="COOLDOWN"
for _ in range(10): m.actualizar(dt,j)
assert round(m.angulo)==90
j.oculto=True; m.angulo=0
for _ in range(60): m.actualizar(dt,j)
assert m.angulo==0 ; j.oculto=False
# golpe en marcha
m2=mundo.Maniqui(pygame.Vector2(0,0)); j3=pj([H.crear_habilidad("Paso 0")]); j3.posicion=pygame.Vector2(30,0)
m2.tiempo_desde_ataque=5; m2.actualizar(dt,j3); assert m2.herramienta.golpeando
j3.habilidades[0].intentar_activar(j3); m2.actualizar(dt,j3); assert m2.herramienta.golpeando
# 4) Golpe de Suerte: Paso 0 en el sorteo, 30% nada, resto 8.75%
g=H.crear_habilidad("Golpe de Suerte"); pr=g.probabilidades()
print({k:round(v,5) for k,v in pr.items()})
assert abs(pr["Nada"]-0.30)<1e-9 and abs(pr["Paso 0"]-0.7/9)<1e-9 and abs(sum(pr.values())-1)<1e-9 and len(pr)==10
g.nivel=20; g._aplicar_nivel(); pr=g.probabilidades(); assert abs(pr["Nada"]-0.05)<1e-9 and abs(pr["Paso 0"]-0.95/9)<1e-9
j=pj([g]); txt=g.aplicar_resultado("Paso 0", j); print("otorgado:",txt, "dura", g.efecto_actual.duracion_activa)
assert j.invisible and g.efecto_actual.nivel==10 and txt=="Paso 0 nv10"
# 5) Dibujo: invisible no dibuja nombre/arma (salvo golpe); sin errores
j=pj([H.crear_habilidad("Paso 0")]); j.herramienta.toggle(); j.habilidades[0].intentar_activar(j)
f=pygame.font.SysFont("Segoe UI",11); pantalla.fill((0,0,0)); j.dibujar(pantalla,f,(-400,-300))
j.herramienta.atacar(j); j.herramienta.actualizar(dt,j); j.dibujar(pantalla,f,(-400,-300))
j.habilidades[0].estado="LISTA"; j.dibujar(pantalla,f,(-400,-300))
fuentes={k:pygame.font.SysFont("Segoe UI",12) for k in ("titulo","sub","texto","mini","valor","contador","nombre")}
H.dibujar_panel_habilidades(pantalla,480,0,320,600,j.habilidades,j,fuentes)
print("OK")
