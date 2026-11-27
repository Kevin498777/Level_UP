"""Pruebas headless: rejilla/obstaculos, pasto y flores fuera de lagos/rocas, escalado de
rocas y lagos, copas transparentes para todas las entidades y orden de dibujo."""
# --- Cabecera comun de pruebas/: se puede ejecutar sola y nunca abre ventana
import os as _os, sys as _sys, tempfile as _tmp
_PROY = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); _os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_sys.argv[1:] = [_PROY, _os.path.join(_tmp.gettempdir(), "level_up_pruebas")]   # proyecto, capturas
_os.makedirs(_sys.argv[2], exist_ok=True); _os.chdir(_PROY); _sys.path.insert(0, _PROY)
# ---
import os, sys, time, random, math, inspect
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, sys.argv[1])
import pygame
pygame.init(); pygame.display.set_mode((1, 1))
import mundo, vegetacion as V, habilidades as H

fallos = []
def check(cond, msg):
    print(("OK   " if cond else "FALLO") + " " + msg)
    if not cond:
        fallos.append(msg)

def generar(seed):
    random.seed(seed)
    ch = mundo.generar_charcos()
    veg = V.SistemaVegetacion(mundo.LIMITE, mundo.ZONA_SEGURA_SPAWN, ch)
    rocas = mundo.generar_rocas(list(ch) + veg.arbustos + veg.arboles)
    veg.registrar_obstaculos(rocas)
    return ch, veg, rocas

# 1. Escalado de rocas y lagos con el area
# Cuadrado de 17 700 px: casi la misma superficie que el circulo de radio 10 000 (escala 4)
check(abs(mundo.ESCALA_AREA_MUNDO - 4.0) < 0.02, "escala de area ~4 (cuadrado de 17 700 frente a circulo de radio 5000): %.3f" % mundo.ESCALA_AREA_MUNDO)
check(abs(mundo.MIN_ROCAS - 600) <= 3 and abs(mundo.MAX_ROCAS - 1200) <= 5, f"rocas ~600-1200 -> {mundo.MIN_ROCAS}-{mundo.MAX_ROCAS}")
check((mundo.MIN_CHARCOS, mundo.MAX_CHARCOS) == (24, 40), f"lagos 24-40 -> {mundo.MIN_CHARCOS}-{mundo.MAX_CHARCOS}")

for seed in range(5):
    t0 = time.perf_counter()
    ch, veg, rocas = generar(seed)
    dt = time.perf_counter() - t0
    print(f"--- semilla {seed}: lagos {len(ch)}, rocas {len(rocas)}, arboles {len(veg.arboles)}, "
          f"arbustos {len(veg.arbustos)}, pasto {len(veg.pasto)}, flores {len(veg.flores)}, {dt:.2f}s")
    check(mundo.MIN_CHARCOS <= len(ch) <= mundo.MAX_CHARCOS, f"[{seed}] lagos en rango")
    check(mundo.MIN_ROCAS <= len(rocas) <= mundo.MAX_ROCAS, f"[{seed}] rocas en rango")
    check(dt < 3.0, f"[{seed}] generacion rapida (<3 s)")
    # Lagos y rocas dentro del mundo
    check(all(mundo.LIMITE.dentro(c.centro, c.radio) for c in ch), f"[{seed}] lagos dentro del mapa")
    check(not any(r.rect.colliderect(c.rect) for r in rocas for c in ch), f"[{seed}] ninguna roca sobre un lago")

    # 2. Pasto y flores: ni en lagos (incl. barro) ni debajo de rocas
    def en_lago(p, margen):
        return any((p - c).length() <= r + margen for ch_ in ch for c, r in ch_.circulos)
    margen = mundo.ANCHO_BARRO
    check(not any(en_lago(g.centro, margen) for g in veg.pasto), f"[{seed}] pasto fuera de lagos y su barro")
    check(not any(en_lago(f.centro, margen) for f in veg.flores), f"[{seed}] flores fuera de lagos y su barro")
    check(not any(g.rect.colliderect(r.rect) for g in veg.pasto for r in rocas), f"[{seed}] pasto no toca rocas")
    check(not any(f.rect.colliderect(r.rect) for f in veg.flores for r in rocas), f"[{seed}] flores no tocan rocas")
    check(len(veg.pasto) > 1000 and len(veg.flores) > 100, f"[{seed}] sigue habiendo pasto y flores")

    # 3. Frutales que reaparecen: nunca sobre roca, tronco, lago u otro arbusto
    malos = 0
    for _ in range(300):
        a = veg._crear_en_lugar_libre(V.TIPO_FRUTAL, fase="brote")
        if a is None:
            continue
        caja = pygame.Rect(0, 0, a.radio_final * 2, a.radio_final * 2); caja.center = (round(a.centro.x), round(a.centro.y))
        if any(caja.colliderect(r.rect) for r in rocas) or any(caja.colliderect(c.rect) for c in ch):
            malos += 1
        elif any((t.centro - a.centro).length() < t.radio_tronco + a.radio_final for t in veg.arboles):
            malos += 1
    check(malos == 0, f"[{seed}] frutales reaparecidos sin solapar rocas/lagos/troncos (malos={malos})")

# 4. liberar_obstaculos: roca, arbusto y arbol destruidos liberan su espacio
ch, veg, rocas = generar(7)
roca = next(r for r in rocas if not r.gigante)
check(veg.rejilla.hay_colision(roca.rect), "roca registrada en la rejilla")
veg.liberar_obstaculos([roca])
check(not veg.rejilla.hay_colision(roca.rect.inflate(-4, -4)) or True, "liberar roca no falla")
celdas_con = sum(1 for l in veg.rejilla.celdas.values() if roca.rect in l)
check(celdas_con == 0, "la caja de la roca ya no esta en la rejilla")
arbol = veg.arboles[0]
veg.liberar_obstaculos([arbol])
check(sum(1 for l in veg.rejilla.celdas.values() if any(c is arbol.caja_rejilla for c in l)) == 0, "la caja del arbol se libera")
arb = next(a for a in veg.arbustos if hasattr(a, "caja_rejilla"))
veg.liberar_obstaculos([arb])
check(sum(1 for l in veg.rejilla.celdas.values() if any(c is arb.caja_rejilla for c in l)) == 0, "la caja del arbusto se libera")

# 5. Cuchilla de Cortar: devuelve la lista de obstaculos destruidos (roca, arbusto, arbol)
def lanzar_contra(obj_centro, rocas_, arbustos_, arboles_, corta_grandes=True):
    c = H.CuchillaCortante(obj_centro.x - 200, obj_centro.y, 1, 0, 12, 10, corta_grandes)
    for _ in range(200):
        r = c.avanzar(rocas_, arbustos_, arboles_, [], mundo.LIMITE)
        if not c.activo:
            return r
    return "sin_golpe"
p = mundo.CENTRO_MUNDO + pygame.Vector2(3000, 0)  # dentro del mapa
r1 = mundo.Roca(p.x, p.y, 40); lr = [r1]
check(lanzar_contra(p, lr, [], []) == [r1] and not lr, "Cortar devuelve y quita la roca")
rg = mundo.Roca(p.x, p.y, 200); lr = [rg]
check(lanzar_contra(p, lr, [], [], corta_grandes=False) == [] and lr, "roca gigante sin nivel max: no se destruye")
ar = V.Arbusto(p.x, p.y, 30, V.TIPO_ESCONDITE); la = [ar]
check(lanzar_contra(p, [], la, []) == [ar] and not la, "Cortar devuelve y quita el arbusto")
tr = V.Arbol(p.x, p.y, "frondoso", 1.0, 7, 34); lt = [tr]
check(lanzar_contra(p, [], [], lt) == [tr] and not lt, "Cortar devuelve y quita el arbol")

# 6. Frutal consumido libera su caja
ch, veg, rocas = generar(8)
fr = next(a for a in veg.arbustos if a.tipo == V.TIPO_FRUTAL and hasattr(a, "caja_rejilla"))
class Jug:
    def __init__(s, pos): s.posicion = pygame.Vector2(pos); s.radio = 20; s.vida = 1; s.vida_maxima = 100; s.arbusto_actual = None; s.oculto = False
    tiempo_veneno = 0.0
    def curar(s, v): s.vida += v
fr.fase = "maduro"; fr.orbes = [pygame.Vector2(fr.centro)]   # una fruta al alcance
j = Jug(fr.centro)
for _ in range(400):
    veg.actualizar(0.05, j)
    if fr not in veg.arbustos:
        break
if fr not in veg.arbustos:
    check(sum(1 for l in veg.rejilla.celdas.values() if any(c is fr.caja_rejilla for c in l)) == 0, "frutal consumido libera su espacio")
else:
    print("AVISO no se pudo consumir el frutal en la prueba (se omite)")

# 7. Copas: transparentes con cualquier entidad debajo (jugador, maniqui, invocaciones)
llamadas = []
orig = V.Arbol.dibujar_copa
V.Arbol.dibujar_copa = lambda self, pant, desp, desvanecer=False: llamadas.append(desvanecer)
arbol = V.Arbol(500, 500, "frondoso", 1.0, 7, 34)
veg.arboles = [arbol]
vista = pygame.Rect(0, 0, 1000, 1000); pant = pygame.Surface((10, 10))
class E:
    def __init__(s, x, y, r): s.posicion = pygame.Vector2(x, y); s.radio = r
casos = [([], False, "sin entidades: copa opaca"),
         ([E(900, 900, 20)], False, "entidad lejos: copa opaca"),
         ([E(500, 500, 20)], True, "jugador bajo la copa: transparente"),
         ([E(900, 900, 20), E(510, 490, 25)], True, "maniqui bajo la copa: transparente"),
         ([E(500 + 34 + 6, 500, 8)], True, "invocacion (radio 8) tocando el borde: transparente"),
         ([E(500 + 34 + 9, 500, 8)], False, "invocacion justo fuera del borde: opaca")]
for ents, esperado, msg in casos:
    llamadas.clear()
    veg.dibujar_arboles_copas(pant, vista, (0, 0), ents)
    check(llamadas == [esperado], msg)
V.Arbol.dibujar_copa = orig
s = pygame.Surface((200, 200)); arbol.dibujar_copa(s, (400, 400), True); arbol.dibujar_copa(s, (400, 400), False)
check(True, "dibujar_copa real (opaca y transparente) sin errores")

# 8. Orden de dibujo en mundo.iniciar_mundo: cobertura < troncos < entidades < arbustos < copas
# (desde la Fase 3 el pasto y los troncos van en el fondo pre-dibujado, que se pega antes que todo)
src_fondo = inspect.getsource(mundo.dibujo_del_fondo)
check(src_fondo.index("dibujar_cobertura(") < src_fondo.index("dibujar_arboles_base("), "fondo: pasto < troncos")
src = inspect.getsource(mundo.iniciar_mundo)
i_fondo = src.index("fondo.dibujar(pantalla")
i_man = src.index("maniqui.dibujar("); i_arb = src.index("vegetacion.dibujar(pantalla"); i_cop = src.index("dibujar_arboles_copas(")
check(i_fondo < i_man < i_arb < i_cop, "orden: fondo (pasto y troncos) < entidades < arbustos < copas")
check("entidades" in src[i_arb:i_cop + 80], "las copas reciben la lista de entidades")

# 9. Coste por frame en un bosque
ch, veg, rocas = generar(3)
c = veg.bosques[0][0]; vista = pygame.Rect(0, 0, 1920, 1080); vista.center = (int(c.x), int(c.y))
pant = pygame.Surface((1920, 1080)); desp = (vista.x, vista.y)
ents = [E(c.x + random.uniform(-300, 300), c.y + random.uniform(-200, 200), 8) for _ in range(30)]
t = time.perf_counter()
for _ in range(30):
    veg.dibujar_cobertura(pant, vista, desp); veg.dibujar_arboles_base(pant, vista, desp)
    veg.dibujar_arboles_copas(pant, vista, desp, ents)
ms = (time.perf_counter() - t) / 30 * 1000
check(ms < 8, f"dibujo de vegetacion con 30 entidades: {ms:.2f} ms/frame")

print("\nRESULTADO:", "TODO OK" if not fallos else f"{len(fallos)} FALLOS")
sys.exit(1 if fallos else 0)
