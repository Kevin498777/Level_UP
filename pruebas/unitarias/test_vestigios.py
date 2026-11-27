# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Aura Electrica -> Vestigios Miticos (quinta potenciada). Uso: python -B test_vestigios.py <proyecto>
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import habilidades as H, gacha as G, herramientas, fauna as F
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug(nv=20, pot=True, herr="Espada Larga"):
    h = H.crear_habilidad("Aura Electrica"); h.asignar_tecla(pygame.K_2, "2")
    j = Personaje("T", 0, 0, 1, 1, 30, 2, 100, 0, (0, 0, 255), [h], herramientas.crear_herramienta(herr), 0)
    for _ in range(19): j.subir_nivel()
    j.puntos_mejora = 500; j.energia = j.energia_max = 1000
    if pot: j.potenciar_habilidad("Aura Electrica")
    while h.nivel < nv:
        c = h.costo_mejora; assert h.subir_nivel(); j.puntos_mejora -= c
    return j, h

print("--- Aura Eléctrica normal")
j, h = jug(20, pot=False)
check((h.radio_aura, h.porcentaje_buff, h.dano_por_segundo, h.autodano_por_segundo, h.duracion_activa, h.duracion_cooldown, h.costo_energia)
      == (100, 0.15, 5, 0.5, 20.0, 60.0, 58), "nv20: 100 px, +15 %, 5/s, 0.5/s, 20 s, 60 s, 58 En.")
h.intentar_activar(j)
check(h.bono_dano_arma == 0 and h.aturdimiento_golpe == 0 and h.nivel_max == 20, "sin potenciar: sin pasiva y máximo 20")

print("--- Vestigios Míticos: escalado lineal")
esperado = {21: (102, 0.185, 5.7, 0.55, 22, 62, 60, 0.01, 0.1), 25: (110, 0.325, 8.5, 0.75, 30, 70, 69, 0.05, 0.5),
            30: (120, 0.50, 12.0, 1.0, 40, 80, 80, 0.10, 1.0)}
for nv, v in esperado.items():
    j, h = jug(nv)
    real = (h.radio_aura, h.porcentaje_buff, h.dano_por_segundo, h.autodano_por_segundo, h.duracion_activa, h.duracion_cooldown,
            h.costo_energia, h.bono_arma, h.aturdimiento)
    check(all(abs(a - b) < 1e-6 for a, b in zip(real, v)),
          "nv%d: %d px, +%g %% vel, %g/s, autodaño %g/s, %g s, recarga %g s, %d En., arma +%g %%, aturde %g s" %
          (nv, v[0], v[1] * 100, v[2], v[4 - 1], v[4], v[5], v[6], v[7] * 100, v[8]))
j, h = jug(30)
check(h.nombre_mostrado == "Vestigios Míticos" and h.costo_mejora == 2 and not h.subir_nivel(), "se llama Vestigios Míticos, 2 puntos por nivel y para en el 30")

print("--- aura activa")
j, h = jug(30); j.velocidad_base = 1.0
h.intentar_activar(j); j.actualizar_velocidad()
check(abs(j.velocidad - 1.5 * (1 - j.herramienta.debuff_velocidad * 0) ) < 0.2, "velocidad con +50 %% (%.2f)" % j.velocidad)
dentro = F.LoboSolitario(115, 0); fuera = F.LoboSolitario(160, 0)
dentro.vida = fuera.vida = 500
for _ in range(61):
    h.actualizar(1 / 60, j); h.actualizar_dano_enemigos(1 / 60, [dentro, fuera], j)
check(abs((500 - dentro.vida) - 12) < 1e-6 and fuera.vida == 500, "12 de daño por segundo a 115 px (radio 120); nada a 160 px")
check(abs((j.vida_max - j.vida) - 1.0) < 1e-6, "autodaño 1 por segundo (%g)" % (j.vida_max - j.vida))

print("--- pasiva Golpes eléctricos")
j, h = jug(30)
d0 = j.herramienta.calcular_dano(j)
h.intentar_activar(j)
d1 = j.herramienta.calcular_dano(j)
check(abs(d1 - d0 * 1.10) < 0.02, "arma +10 %% con el aura activa (%g -> %g)" % (d0, d1))
j.talismanes.anillos["fuerza"] = 10; j.talismanes.equipar("fuerza"); j.recalcular_talismanes()
check(abs(j.herramienta.calcular_dano(j) - d0 * 1.20) < 0.02, "se suma al anillo de Fuerza (+10 % +10 % = +20 %)")
h.tiempo_restante_activo = 0.01; h.actualizar(0.05, j)
check(abs(j.herramienta.calcular_dano(j) - d0 * 1.10) < 0.02, "al acabar el aura se pierde el +10 % (queda el del anillo)")

print("--- aturdimiento")
j, h = jug(30); h.intentar_activar(j)
lobo = F.LoboSolitario(30, 0); lobo.vida = 500
j.golpear_con_arma(lobo, 5, "fisico")
check(lobo.inmovilizado is not None and abs(lobo.inmovilizado.restante - 1.0) < 1e-6, "nv30: el golpe lo aturde 1 s")
pos = pygame.Vector2(lobo.posicion); lobo._cd_mordida = 0; v0 = j.vida
for _ in range(30): lobo.actualizar(1 / 60, j, [j], [])
check(lobo.posicion == pos and j.vida == v0, "aturdido: ni se mueve ni muerde")
lobo.inmovilizado = None
j.golpear_con_arma(lobo, 5, "fisico")
check(lobo.inmovilizado is None, "otro golpe antes de 1.5 s no lo vuelve a aturdir")
j.actualizar_reloj(1.5)
j.golpear_con_arma(lobo, 5, "fisico")
check(lobo.inmovilizado is not None, "pasados 1.5 s se puede volver a aturdir")
otro = F.LoboSolitario(-30, 0); j.golpear_con_arma(otro, 5, "fisico")
check(otro.inmovilizado is not None, "la espera es por enemigo: otro enemigo se aturde enseguida")
telar = F.LoboSolitario(0, 30); H.aplicar_inmovilizacion(telar, 15)
j.actualizar_reloj(5); j.golpear_con_arma(telar, 5, "fisico")
check(abs(telar.inmovilizado.restante - 15) < 1e-6, "no acorta una telaraña más larga")
j, h = jug(21); h.intentar_activar(j); l2 = F.LoboSolitario(30, 0); j.golpear_con_arma(l2, 5, "fisico")
check(abs(l2.inmovilizado.restante - 0.1) < 1e-6, "nv21: aturde 0.1 s")
j, h = jug(30); l3 = F.LoboSolitario(30, 0); j.golpear_con_arma(l3, 5, "fisico")
check(l3.inmovilizado is None, "sin activar el aura no aturde")

print("--- Gacha y colores")
check("Aura Electrica" in G.potenciadas_disponibles(jug(20, pot=False)[0]), "Vestigios Míticos entra en el Gacha mejorado")
check(H.AuraElectrica.COLORES_MARCO == ((70, 150, 255), (255, 220, 60)), "marco azul y amarillo")

print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
