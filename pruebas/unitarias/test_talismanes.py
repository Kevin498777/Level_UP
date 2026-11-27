# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
# Talismanes v2: anillos (rarezas y efectos nuevos), anillos de sombra y Tótem de vida.
import os, sys, random
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1]); os.chdir(sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((10, 10))
import talismanes as TL, herramientas, habilidades as H
from personaje import Personaje

fallos = []
def check(c, m):
    print(("OK   " if c else "FALLO"), m)
    if not c: fallos.append(m)
def jug(herr="Espada Larga"):
    return Personaje("T", 0, 0, 1, 2, 20, 2, 100, 0, (0, 0, 255), [], herramientas.crear_herramienta(herr), 0)
def subir(j, a, n):
    for _ in range(n): j.talismanes.agregar_anillo(a)

# --- rarezas y niveles maximos
esperado = dict(viento=(TL.COMUN, 10), fuerza=(TL.COMUN, 10), energia=(TL.COMUN, 10), sombra_conejo=(TL.COMUN, 10),
                def_magica=(TL.ESPECIAL, 7), def_fisica=(TL.ESPECIAL, 7),
                vida=(TL.EPICO, 5), cadencia=(TL.EPICO, 5), sombra_lobo=(TL.EPICO, 10), regeneracion=(TL.LEGENDARIO, 3))
check({a: (d["rareza"], d["nivel_max"]) for a, d in TL.ANILLOS.items()} == esperado,
      "rarezas y niveles: 4 comunes (10), 2 especiales (7), 3 epicos (5/5/10), legendario (3)")
c = TL.ColeccionTalismanes()
check(c.agregar_anillo("fuerza") == "nuevo" and c.agregar_anillo("fuerza") == "mejorado", "nuevo y repetido")
for _ in range(20): c.agregar_anillo("fuerza")
check(c.anillos["fuerza"] == 10 and c.agregar_anillo("fuerza") == "maximo", "fuerza tope 10; al maximo devuelve")
for _ in range(5): c.agregar_totem()
check(c.totems == 5 and c.agregar_totem() == "maximo", "totem hasta 5")

# --- limites de equipo
c = TL.ColeccionTalismanes()
for a in TL.ANILLOS: c.agregar_anillo(a)
check(c.equipar("vida")[0] and c.equipar("cadencia")[0], "2 epicos equipados")
ok, m = c.equipar("sombra_lobo")
check(not ok and "épico" in m, "un tercer epico no: " + str(m))
c.quitar(1)
check(c.equipar("regeneracion")[0] and c.equipar("def_fisica")[0], "legendario + especial")
ok, m = c.equipar("viento")
check(not ok and "huecos" in m, "un cuarto objeto no cabe")

# --- efectos
j = jug(); v0 = j.vida_max
subir(j, "vida", 1); j.talismanes.equipar("vida"); j.recalcular_talismanes()
check(j.vida_max == v0 + 4 and j.vida == 20, "vida nv1: +4 (no cura)")
subir(j, "vida", 4); j.recalcular_talismanes()
check(j.vida_max == v0 + 20, "vida nv5: +20")
j.talismanes.quitar(0); j.recalcular_talismanes()
check(j.vida_max == v0, "quitarlo resta exacto")
j = jug(); e0 = j.energia_max
subir(j, "energia", 10); subir(j, "cadencia", 5)
j.talismanes.equipar("energia"); j.talismanes.equipar("cadencia"); j.recalcular_talismanes()
check(j.energia_max == e0 + 25 and abs(j.cadencia - 1.5) < 1e-9, "energia nv10 +25, cadencia nv5 +1.5")
j = jug(); subir(j, "viento", 10); j.talismanes.equipar("viento"); j.recalcular_talismanes()
j.herramienta.activa = False; j.actualizar_velocidad()
check(abs(j.velocidad - round(j.velocidad_base * 1.10, 2)) < 1e-9, "viento nv10: +10%% (%.2f)" % j.velocidad)
j = jug(); d0 = j.herramienta.calcular_dano(j)
subir(j, "fuerza", 10); j.talismanes.equipar("fuerza"); j.recalcular_talismanes()
check(abs(j.herramienta.calcular_dano(j) - round(d0 * 1.10, 2)) < 0.011, "fuerza nv10: +10%% al arma (%.2f -> %.2f)" % (d0, j.herramienta.calcular_dano(j)))
j = jug()
for a in ("def_fisica", "def_magica"):
    subir(j, a, 7); j.talismanes.equipar(a)
j.recalcular_talismanes()
check(j.escudo_max == 20 and j.escudo_magico_max == 20, "defensas nv7: +20 (base 0)")
j2 = jug(); subir(j2, "def_fisica", 1); j2.talismanes.equipar("def_fisica"); j2.recalcular_talismanes()
check(abs(j2.escudo_max - 20 / 7) < 0.01, "defensa nv1: +%.2f" % j2.escudo_max)
j.escudo = 0; j.tiempo_sin_dano_escudo = 10; j.actualizar_regeneracion_escudo(1.0)
check(abs(j.escudo - 1.1) < 1e-9, "regeneracion del escudo +10% fijo")
for n in (1, 2, 3):
    j = jug(); j.vida = 5
    subir(j, "regeneracion", n); j.talismanes.equipar("regeneracion"); j.recalcular_talismanes()
    for _ in range(61): j.actualizar_talismanes(0.1)
    check(abs(j.vida - (5 + 0.3 * n * 6)) < 0.05, "regeneracion nv%d: +%.1f/s (6 s -> %.1f)" % (n, 0.3 * n, j.vida))

# --- anillos de sombra
s1 = TL.stats_sombra("conejo", 1); s10 = TL.stats_sombra("conejo", 10)
check(s1["dano"] == 1.0 and s10["dano"] == 7.7 and s1["reaparicion"] == 10 and s10["reaparicion"] == 5,
      "conejo: dano 1 -> 7.7, reaparece 10 s -> 5 s")
hc = H.InvocacionConejos()
check(s1["vida"] == hc.vida_conejo, "conejo nv1 = vida de la habilidad nv1")
l1 = TL.stats_sombra("lobo", 1); l10 = TL.stats_sombra("lobo", 10)
hl = H.InvocacionLobos()
while hl.subir_nivel(): pass
check(l1["dano"] == 4 and l10["dano"] == 30 and l10["vida"] == hl.vida_lobo and l1["reaparicion"] == 8 and l10["reaparicion"] == 4,
      "lobo: dano 4 -> 30, vida nv10 = habilidad nv20 (%d), reaparece 8 s -> 4 s" % l10["vida"])
check(TL.stats_sombra("lobo", 5)["reaparicion"] == round(8 - 4 * 4 / 9, 2), "reaparicion lineal (lobo nv5: %.2f s)" % TL.stats_sombra("lobo", 5)["reaparicion"])

j = jug(); j.posicion = pygame.Vector2(1000, 1000)
subir(j, "sombra_lobo", 1); j.talismanes.equipar("sombra_lobo"); j.recalcular_talismanes()
j.sombras_anillo.actualizar(0.016, j)
crs = j.sombras_anillo.criaturas
check(len(crs) == 1 and isinstance(crs[0], H.Lobo) and crs[0].dano == 4, "al equipar aparece 1 lobo sombra (dano 4)")
lobo = crs[0]
for _ in range(60): j.sombras_anillo.actualizar(0.016, j)
check((lobo.posicion - j.posicion).length() < 200, "te sigue sin objetivo")
class Enemigo:
    def __init__(self, pos): self.posicion = pygame.Vector2(pos); self.radio = 10; self.vida = 100; self.vivo = True
    def recibir_dano(self, d, t="fisico", dir=None):
        self.vida -= d; self.vivo = self.vida > 0; return d
en = Enemigo(j.posicion + pygame.Vector2(80, 0))
for _ in range(120): j.sombras_anillo.actualizar(0.016, j)
check(en.vida == 100, "no ataca a un enemigo que no te ha atacado")
TL.marcar_agresor(j, en)
for _ in range(240): j.sombras_anillo.actualizar(0.016, j)
check(en.vida < 100, "si el enemigo te ataca, la sombra lo ataca (vida %.0f)" % en.vida)
lobo.recibir_dano(999)
j.sombras_anillo.actualizar(0.016, j)
check(not j.sombras_anillo.criaturas, "muerta la sombra, no esta")
for _ in range(int(7.5 / 0.1)): j.sombras_anillo.actualizar(0.1, j)
check(not j.sombras_anillo.criaturas, "aun no reaparece a los 7.5 s (nv1: 8 s)")
for _ in range(10): j.sombras_anillo.actualizar(0.1, j)
check(len(j.sombras_anillo.criaturas) == 1, "reaparece a los 8 s")
viejo = j.sombras_anillo.criaturas[0]
j.talismanes.quitar(0); j.recalcular_talismanes()
check(not viejo.vivo and not j.sombras_anillo.criaturas, "quitar el anillo hace desaparecer la sombra")
j = jug(); subir(j, "sombra_conejo", 3); subir(j, "sombra_lobo", 2)
j.talismanes.equipar("sombra_conejo"); j.talismanes.equipar("sombra_lobo"); j.recalcular_talismanes()
j.sombras_anillo.actualizar(0.016, j)
check(len(j.sombras_anillo.criaturas) == 2 and j.sombras_anillo in j.fuentes_criaturas(), "conejo y lobo a la vez; cuentan como sombras del jugador")
j.sombras_anillo.matar_todas()
check(not j.sombras_anillo.criaturas and j.sombras_anillo.esperas, "matar_todas (totem/muerte): vuelven tras su tiempo")

# --- totem
j = jug(); j.talismanes.agregar_totem()
check(not j.talismanes.usar_totem(), "sin equipar no salva")
j.talismanes.equipar(TL.TOTEM)
check(j.talismanes.usar_totem() and TL.TOTEM not in j.talismanes.huecos, "equipado salva y libera el hueco al gastarse")
print("\nRESULTADO:", "TODO OK" if not fallos else "%d FALLOS" % len(fallos))
sys.exit(1 if fallos else 0)
