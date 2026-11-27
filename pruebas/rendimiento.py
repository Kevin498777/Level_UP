"""Medidor de rendimiento sin ventana (Fase 0 del plan de NPC).

Arranca el mundo real (mundo.iniciar_mundo) sin ventana, con el terreno fijo (SEMILLA_MUNDO) y el
resto del azar sembrado (SEMILLA_RENDIMIENTO), y recorre 4 escenarios midiendo cuanto tarda cada
fotograma (logica + dibujo) en una pantalla de 1920x1080:
- centro: dentro de la casa del spawn, sin combate.
- bosque: junto a una manada de lobos, peleando con arma y habilidades.
- lago:   en la orilla de un lago con cocodrilos.
- caos:   muchas habilidades a la vez (Palabras Malditas, Estrella Ignea, invocaciones) entre lobos.
- npc_lejos / npc_cerca: como "centro" con 19 NPC de prueba lejos de la camara (simulacion
  resumida) o con 8 paseando alrededor del jugador (Fase 3; sin inteligencia todavia).
El reloj del juego se simula a 60 fps (dt fijo de 16 ms), asi cada ejecucion hace exactamente el
mismo trabajo y solo cambia lo que tarda tu equipo en hacerlo.

Uso (desde la carpeta del proyecto):
    python -B pruebas/rendimiento.py                 mide y compara con la linea base
    python -B pruebas/rendimiento.py --base          mide y guarda la linea base
    python -B pruebas/rendimiento.py --segundos 10   escenarios mas cortos (por defecto 30 s)
"""
import json
import os
import platform
import random
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"      # nunca abre ventana
os.environ["SDL_AUDIODRIVER"] = "dummy"
CARPETA = os.path.dirname(os.path.abspath(__file__))
PROYECTO = os.path.dirname(CARPETA)
sys.path.insert(0, PROYECTO)
os.chdir(PROYECTO)

import pygame
import mundo
import fauna as F
import habilidades
import herramientas
from personaje import Personaje

ARCHIVO_BASE = os.path.join(CARPETA, "rendimiento_base.json")
SEMILLA_RENDIMIENTO = 2026          # fauna, cofres y botin repetibles entre ejecuciones
ANCHO, ALTO = 1920, 1080
DT_MS = 16
CALENTAMIENTO = 60                  # fotogramas que no se miden al empezar cada escenario
ESCENARIOS = ("centro", "npc_lejos", "npc_cerca", "bosque", "lago", "caos")
# Fase 3: NPC de prueba (sin inteligencia, solo pasean) y su presupuesto frente a "centro"
NPC_LEJOS, NPC_CERCA = 19, 8
PRESUPUESTO_NPC = {"npc_lejos": 1.0, "npc_cerca": 3.0}       # ms de mas como mucho (Anexo B)
NOMBRE_JUGADOR = "Medidor"
VIDA_INMORTAL = 100000              # el jugador no muere durante la medicion
MARGEN_AVISO = 0.10                 # +10 % sobre la linea base se marca como empeora


def percentil(valores, p):
    orden = sorted(valores)
    return orden[min(len(orden) - 1, int(round(p / 100.0 * (len(orden) - 1))))]


def resumen(tiempos_ms):
    return {"media_ms": round(sum(tiempos_ms) / len(tiempos_ms), 2),
            "p95_ms": round(percentil(tiempos_ms, 95), 2),
            "max_ms": round(max(tiempos_ms), 2),
            "fotogramas": len(tiempos_ms)}


class Guion:
    """Mueve al jugador por los escenarios y simula sus teclas desde pygame.event.get, que el
    bucle del juego llama una vez por fotograma; mide el tiempo entre dos llamadas."""

    def __init__(self, segundos):
        self.por_escenario = CALENTAMIENTO + int(segundos * 1000 / DT_MS)
        self.f = 0
        self.t_previo = None
        self.tiempos = {e: [] for e in ESCENARIOS}
        # Comprobacion de que cada escenario hace lo que dice (combate, habilidades, invocaciones)
        self.actividad = {e: {"enemigos_heridos": 0, "proyectiles_max": 0, "criaturas_max": 0,
                              "habilidades": []} for e in ESCENARIOS}
        self.mantenidas = set()
        self.j = self.fauna = self.camara = None

    # --- utilidades del juego
    def colocar(self, punto):
        self.j.posicion = pygame.Vector2(punto)
        self.j.destino = pygame.Vector2(punto)
        self.j.empuje.update(0, 0)
        self.camara.update(punto)

    def tecla(self, k, abajo=True):
        (self.mantenidas.add if abajo else self.mantenidas.discard)(k)
        return pygame.event.Event(pygame.KEYDOWN if abajo else pygame.KEYUP, key=k, mod=0,
                                  unicode="", scancode=0)

    def recargar(self):
        """Vida y energia llenas, y habilidades sin recarga (para que no paren de lanzarse)."""
        self.j.vida = self.j.vida_max
        self.j.energia = self.j.energia_max
        for h in self.j.habilidades:
            if h.estado == "COOLDOWN":
                h.estado = "LISTA"
                h.tiempo_restante_cooldown = 0

    def preparar_caos(self):
        """Nivel 30 con Estrella Ignea, Palabras Malditas e Invocar Lobos potenciadas."""
        j = self.j
        for _ in range(29):
            j.subir_nivel()
        for h in j.habilidades:
            while h.nivel < h.nivel_max:
                h.subir_nivel()
            if j.potenciar_habilidad(h.nombre):
                while h.nivel < h.nivel_max:
                    h.subir_nivel()

    # --- escenarios
    def manada_viva(self, indice):
        vivas = [m for m in self.fauna.manadas if any(l.vivo for l in m.lobos)]
        return vivas[indice % len(vivas)] if vivas else None

    def poner_npc(self, cantidad, distancia):
        """NPC de prueba que pasean cerca de su punto de partida ('distancia' px del jugador)."""
        rng = random.Random(cantidad)
        for k in range(cantidad):
            ang = 2 * 3.14159 * k / cantidad
            casa_npc = mundo.CENTRO_MUNDO + pygame.Vector2(distancia, 0).rotate_rad(ang)
            npc = Personaje("NPC %d" % k, casa_npc.x, casa_npc.y, 1, 2, 100, 3, 100, 0, (200, 120, 60), [],
                            herramientas.crear_herramienta("Espada Larga"))
            npc.casa_npc = casa_npc

            def pasear(c, ctx, jugador, rng=rng):
                c.mover_a(c.casa_npc + pygame.Vector2(rng.uniform(-120, 120), rng.uniform(-120, 120)))
            self.ctx.agregar_combatiente(npc, pasear)

    def iniciar_escenario(self, nombre):
        self.ctx.combatientes.clear()
        if nombre in ("centro", "npc_lejos", "npc_cerca"):
            self.colocar(mundo.CENTRO_MUNDO)
            if nombre == "npc_lejos":
                self.poner_npc(NPC_LEJOS, 5000)
            elif nombre == "npc_cerca":
                self.poner_npc(NPC_CERCA, 280)
        elif nombre in ("bosque", "caos"):
            manada = self.manada_viva(0 if nombre == "bosque" else 1)
            lobo = next(l for l in manada.lobos if l.vivo)
            self.colocar(lobo.posicion + pygame.Vector2(160, 0))
            if nombre == "caos":
                self.preparar_caos()
        elif nombre == "lago":
            charco = self.fauna.cocodrilos[0].charco
            self.colocar(pygame.Vector2(charco.centro) + pygame.Vector2(charco.radio + 60, 0))

    def eventos_escenario(self, nombre, f):
        """Teclas del escenario en el fotograma f (contado desde su inicio)."""
        ev = []
        if nombre == "bosque":
            if f == 1:
                ev += [self.tecla(pygame.K_1), self.tecla(pygame.K_1, False)]     # sacar el arma
            if f % 90 == 5:
                ev.append(self.tecla(pygame.K_SPACE))                            # golpes seguidos
            if f % 90 == 70:
                ev.append(self.tecla(pygame.K_SPACE, False))
            for k, desfase in ((pygame.K_2, 10), (pygame.K_3, 40), (pygame.K_4, 70)):
                if f % 120 == desfase:
                    ev += [self.tecla(k), self.tecla(k, False)]
        elif nombre == "caos":
            if f % 150 == 5:                       # Estrella Ignea: cargar 2 s y soltar
                ev.append(self.tecla(pygame.K_2))
            if f % 150 == 125:
                ev.append(self.tecla(pygame.K_2, False))
            if f % 60 == 20:                       # Palabras Malditas (pulsacion corta)
                ev += [self.tecla(pygame.K_3), self.tecla(pygame.K_3, False)]
            if f % 200 == 30:                      # Invocar Lobos
                ev += [self.tecla(pygame.K_4), self.tecla(pygame.K_4, False)]
        return ev

    def vista(self):
        return pygame.Rect(self.j.posicion.x - ANCHO, self.j.posicion.y - ALTO, ANCHO * 2, ALTO * 2)

    def anotar_actividad(self, nombre):
        a = self.actividad[nombre]
        a["proyectiles_max"] = max(a["proyectiles_max"], len(self.j.proyectiles))
        criaturas = sum(1 for h in self.j.fuentes_criaturas() for c in getattr(h, "criaturas", ()) if c.vivo)
        a["criaturas_max"] = max(a["criaturas_max"], criaturas)
        heridos = sum(1 for e in self.fauna.animales_con_vida(self.vista()) if e.vida < e.vida_max or not e.vivo)
        a["enemigos_heridos"] = max(a["enemigos_heridos"], heridos)
        a["habilidades"] = [h.nombre_mostrado for h in self.j.habilidades]

    # --- gancho del bucle
    def __call__(self, real_get):
        ahora = time.perf_counter()
        real_get()                          # vacia la cola de eventos de SDL (no se usa)
        if self.j is None:
            # El bucle del juego es quien llama: sus variables locales dan acceso a todo
            loc = sys._getframe(2).f_locals
            self.j, self.fauna, self.camara, self.ctx = loc["jugador"], loc["fauna"], loc["camara"], loc["ctx"]
        indice, f = divmod(self.f, self.por_escenario)
        self.f += 1
        if indice >= len(ESCENARIOS):
            return [pygame.event.Event(pygame.QUIT)]
        nombre = ESCENARIOS[indice]
        self.anotar_actividad(nombre)
        if f == 0:
            for k in list(self.mantenidas):
                self.mantenidas.discard(k)
            self.iniciar_escenario(nombre)
        elif f > CALENTAMIENTO:
            self.tiempos[nombre].append((ahora - self.t_previo) * 1000.0)
        self.recargar()
        eventos = self.eventos_escenario(nombre, f)
        # El tiempo del fotograma se cuenta desde aqui: lo que hace este guion no entra en la medida
        self.t_previo = time.perf_counter()
        return eventos


def medir(segundos):
    random.seed(SEMILLA_RENDIMIENTO)
    guion = Guion(segundos)
    real_get = pygame.event.get
    pygame.event.get = lambda *a, **k: guion(real_get)
    pygame.key.get_pressed = lambda: type("Teclas", (), {"__getitem__": lambda s, k: k in guion.mantenidas})()
    pygame.mouse.get_pos = lambda: (ANCHO // 2, ALTO // 2)
    pygame.display.Info = lambda: type("Info", (), {"current_w": ANCHO, "current_h": ALTO})()
    set_mode = pygame.display.set_mode
    pygame.display.set_mode = lambda tamano, flags=0: set_mode(tamano)
    pygame.time.Clock = lambda: type("Reloj", (), {"tick": lambda s, fps=0: DT_MS})()

    hab = [habilidades.crear_habilidad(n) for n in ("Carga de Fuego", "Onda Sonora", "Invocar Lobos")]
    for i, h in enumerate(hab):
        h.asignar_tecla((pygame.K_2, pygame.K_3, pygame.K_4)[i], "234"[i])
    config = {"nombre": NOMBRE_JUGADOR, "color": (0, 150, 255), "tamano": 1.0, "velocidad": 3,
              "vida": VIDA_INMORTAL, "fuerza": 5, "energia": 500, "escudo": 0, "escudo_magico": 0,
              "habilidades": hab, "herramienta": herramientas.crear_herramienta("Espada Larga")}
    t0 = time.perf_counter()
    mundo.iniciar_mundo(config)
    total = time.perf_counter() - t0
    return {e: dict(resumen(guion.tiempos[e]), actividad=guion.actividad[e]) for e in ESCENARIOS}, total


def main():
    args = sys.argv[1:]
    segundos = float(args[args.index("--segundos") + 1]) if "--segundos" in args else 30.0
    resultados, total = medir(segundos)
    base = None
    if os.path.exists(ARCHIVO_BASE):
        with open(ARCHIVO_BASE, encoding="utf-8") as f:
            base = json.load(f)
    print("Escenario   media    p95     max    (ms por fotograma; 16.7 ms = 60 fps)")
    for e in ESCENARIOS:
        r = resultados[e]
        linea = "%-9s %6.2f  %6.2f  %6.2f" % (e, r["media_ms"], r["p95_ms"], r["max_ms"])
        if base and e in base.get("escenarios", {}):
            b = base["escenarios"][e]["media_ms"]
            cambio = (r["media_ms"] - b) / b
            linea += "   base %6.2f  (%+.0f %%)%s" % (b, cambio * 100, "  EMPEORA" if cambio > MARGEN_AVISO else "")
        print(linea)
    for e in ESCENARIOS:
        a = resultados[e]["actividad"]
        print("  %-7s enemigos heridos %d, proyectiles %d, invocaciones %d | %s" % (
            e, a["enemigos_heridos"], a["proyectiles_max"], a["criaturas_max"], ", ".join(a["habilidades"])))
    base_npc = resultados["centro"]["media_ms"]
    for e, maximo in PRESUPUESTO_NPC.items():
        extra = resultados[e]["media_ms"] - base_npc
        print("  %-9s %+.2f ms frente a centro (presupuesto <= +%.0f ms): %s" % (e, extra, maximo, "OK" if extra <= maximo else "EXCEDE"))
    print("Duracion total: %.0f s" % total)
    if "--base" in args:
        datos = {"fecha": time.strftime("%Y-%m-%d"), "segundos_por_escenario": segundos,
                 "pantalla": [ANCHO, ALTO], "python": platform.python_version(),
                 "pygame": pygame.version.ver, "escenarios": resultados}
        with open(ARCHIVO_BASE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print("Linea base guardada en", os.path.relpath(ARCHIVO_BASE, PROYECTO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
