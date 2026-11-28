"""Navegacion de los bots (Fase 4 del plan de NPC).

- RejillaPaso: el mapa en celdas de CELDA_PASO px (40). Sale de la rejilla de rutas guardada con
  el mapa (mapas/<nombre>_rutas.bin, celdas de 20 px ya con la holgura de un personaje): una celda
  de 40 px se puede pisar si al menos 2 de sus 4 celdas de 20 lo permiten. El agua normal se
  puede cruzar pero cuesta COSTE_AGUA; la zona profunda de los lagos ya viene bloqueada. Cuando se
  destruye un obstaculo, sus celdas se vuelven a calcular (actualizar_zona).
- ruta(desde, hasta): A* con 8 vecinos (sin cortar esquinas) y luego se quitan los puntos que
  sobran (si hay linea recta libre entre dos puntos, los de en medio no hacen falta).
- ColaRutas: como mucho MAX_RUTAS_POR_FOTOGRAMA rutas nuevas por fotograma.
- Navegador: lo lleva cada bot; sigue los puntos de su ruta y se desatasca (si en
  TIEMPO_ATASCO s no avanza, recalcula; si vuelve a pasar, sale al hueco libre mas cercano).
"""
import heapq
import math
import zlib
from collections import deque

import pygame

CELDA_PASO = 40                 # px por celda de la rejilla de paso
COSTE_AGUA = 3.0                # el agua normal cuesta 3 veces mas que la tierra
MAX_NODOS_ASTAR = 5000          # celdas exploradas como mucho por ruta (si no llega: ruta parcial)
PESO_HEURISTICA = 1.6           # A* algo "impaciente": rutas casi optimas y mucho mas rapidas
SUAVIZADO_ALCANCE = 24          # celdas que mira por delante al enderezar la ruta
MAX_RUTAS_POR_FOTOGRAMA = 2     # rutas nuevas por fotograma (el resto espera su turno)
LLEGADA_PUNTO = 24              # px a los que un punto de la ruta se da por alcanzado
TIEMPO_ATASCO = 1.0             # s sin avanzar para considerar que el bot esta atascado
AVANCE_MINIMO = 12              # px que tiene que avanzar en TIEMPO_ATASCO
RADIO_BOT = 20                  # holgura de un personaje de tamano 1


class RejillaPaso:
    """Celdas pisables del mapa. 'bloqueo' y 'agua' son bytearrays de ancho x alto (1 = si)."""

    def __init__(self, origen, ancho, alto, bloqueo, agua):
        self.origen = pygame.Vector2(origen)
        self.ancho, self.alto = ancho, alto
        self.bloqueo = bloqueo
        self.agua = agua
        self._componentes = None

    # ------------------------------------------------------------ construccion
    @classmethod
    def desde_rutas(cls, origen, celda_fina, ancho_fino, alto_fino, bloqueo_fino, charcos):
        """Reduce la rejilla de rutas (celdas de 20 px) a celdas de CELDA_PASO px."""
        factor = CELDA_PASO // celda_fina
        ancho, alto = math.ceil(ancho_fino / factor), math.ceil(alto_fino / factor)
        bloqueo = bytearray(ancho * alto)
        for j in range(alto):
            for i in range(ancho):
                libres = 0
                for dj in range(factor):
                    for di in range(factor):
                        x, y = i * factor + di, j * factor + dj
                        if x < ancho_fino and y < alto_fino and not bloqueo_fino[y * ancho_fino + x]:
                            libres += 1
                bloqueo[j * ancho + i] = 0 if libres * 2 >= factor * factor else 1
        rejilla = cls(origen, ancho, alto, bloqueo, bytearray(ancho * alto))
        rejilla.marcar_agua(charcos)
        return rejilla

    @classmethod
    def cargar(cls, ruta_archivo, origen, charcos):
        """Desde mapas/<nombre>_rutas.bin (cabecera RUTAS1, celda, ancho, alto + zlib)."""
        with open(ruta_archivo, "rb") as f:
            datos = f.read()
        if datos[:6] != b"RUTAS1":
            raise ValueError("no es un archivo de rutas")
        celda = int.from_bytes(datos[6:8], "little")
        ancho = int.from_bytes(datos[8:12], "little")
        alto = int.from_bytes(datos[12:16], "little")
        return cls.desde_rutas(origen, celda, ancho, alto, zlib.decompress(datos[16:]), charcos)

    def marcar_agua(self, charcos):
        for c in charcos:                       # solo las celdas de la caja de cada lago
            i0, j0 = self.celda_de(c.rect.topleft)
            i1, j1 = self.celda_de(c.rect.bottomright)
            for j in range(max(0, j0), min(self.alto - 1, j1) + 1):
                for i in range(max(0, i0), min(self.ancho - 1, i1) + 1):
                    if c.contiene(self.centro_de(i, j)):
                        self.agua[j * self.ancho + i] = 1

    def actualizar_zona(self, rect, obstaculos, personaje, punto_libre):
        """Vuelve a calcular las celdas de 'rect' (algo se destruyo): pisable si un personaje cabe
        en el centro de la celda. 'punto_libre(p, radio, rocas, circulares)' es mundo.punto_libre."""
        i0, j0 = self.celda_de(rect.topleft)
        i1, j1 = self.celda_de(rect.bottomright)
        zona = rect.inflate(CELDA_PASO * 2, CELDA_PASO * 2)
        rocas = obstaculos.rocas_en(zona)
        circulares = obstaculos.obstaculos_cerca(personaje, zona)
        for j in range(max(0, j0), min(self.alto - 1, j1) + 1):
            for i in range(max(0, i0), min(self.ancho - 1, i1) + 1):
                libre = punto_libre(self.centro_de(i, j), RADIO_BOT, rocas, circulares)
                self.bloqueo[j * self.ancho + i] = 0 if libre else 1
        self._componentes = None                # se recalculan al pedir la siguiente ruta

    def componentes(self):
        """Etiqueta de zona conectada de cada celda libre (las celdas de dos zonas distintas no se
        pueden unir andando: la ruta ni se busca). Se calcula al pedirla tras un cambio."""
        if self._componentes is not None:
            return self._componentes
        w, n = self.ancho, self.ancho * self.alto
        etiqueta = [0] * n
        actual = 0
        bloqueo = self.bloqueo
        for k in range(n):
            if bloqueo[k] or etiqueta[k]:
                continue
            actual += 1
            etiqueta[k] = actual
            cola = [k]
            while cola:
                q = cola.pop()
                x = q % w
                for v in (q - w, q + w, q - 1 if x > 0 else -1, q + 1 if x < w - 1 else -1):
                    if 0 <= v < n and not bloqueo[v] and not etiqueta[v]:
                        etiqueta[v] = actual
                        cola.append(v)
        self._componentes = etiqueta
        return etiqueta

    def misma_zona(self, a, b):
        comp = self.componentes()
        return comp[a[1] * self.ancho + a[0]] == comp[b[1] * self.ancho + b[0]]

    # ------------------------------------------------------------ consultas
    def celda_de(self, p):
        return int((p[0] - self.origen.x) // CELDA_PASO), int((p[1] - self.origen.y) // CELDA_PASO)

    def centro_de(self, i, j):
        return pygame.Vector2(self.origen.x + (i + 0.5) * CELDA_PASO, self.origen.y + (j + 0.5) * CELDA_PASO)

    def dentro(self, i, j):
        return 0 <= i < self.ancho and 0 <= j < self.alto

    def libre(self, i, j):
        return self.dentro(i, j) and not self.bloqueo[j * self.ancho + i]

    def libre_cercana(self, i, j, radio=12):
        """La celda libre mas cercana a (i, j) (o None)."""
        if self.libre(i, j):
            return i, j
        for r in range(1, radio + 1):
            mejor = None
            for di in range(-r, r + 1):
                for dj in (-r, r) if abs(di) != r else range(-r, r + 1):
                    if self.libre(i + di, j + dj):
                        d = di * di + dj * dj
                        if mejor is None or d < mejor[0]:
                            mejor = (d, i + di, j + dj)
            if mejor:
                return mejor[1], mejor[2]
        return None

    def ruta(self, desde, hasta):
        """Lista de puntos del mundo de 'desde' a 'hasta' (sin el punto de salida), o None si no
        hay camino. A* sobre indices planos (rapido en Python); si la busqueda pasa de
        MAX_NODOS_ASTAR celdas, devuelve la ruta hasta la celda mas cercana al destino."""
        inicio = self.libre_cercana(*self.celda_de(desde))
        fin = self.libre_cercana(*self.celda_de(hasta))
        if inicio is None or fin is None:
            return None
        if inicio == fin:
            return [pygame.Vector2(hasta)]
        if not self.misma_zona(inicio, fin):
            return None                         # destino encerrado: no hay camino posible
        w, h_total = self.ancho, self.alto
        bloqueo, agua = self.bloqueo, self.agua
        n = w * h_total
        k_ini, k_fin = inicio[1] * w + inicio[0], fin[1] * w + fin[0]
        fi, fj = fin
        raiz2 = math.sqrt(2)

        def heur(k):
            di, dj = abs(k % w - fi), abs(k // w - fj)
            return PESO_HEURISTICA * (di + dj + (raiz2 - 2) * (di if di < dj else dj))

        coste = {k_ini: 0.0}
        padre = {k_ini: -1}
        abiertos = [(heur(k_ini), 0.0, k_ini)]
        mejor_h, mejor = heur(k_ini), k_ini
        explorados = 0
        objetivo = k_fin
        while abiertos:
            _, g, k = heapq.heappop(abiertos)
            if k == objetivo:
                break
            if g > coste[k]:
                continue
            explorados += 1
            hk = heur(k)
            if hk < mejor_h:
                mejor_h, mejor = hk, k
            if explorados > MAX_NODOS_ASTAR:
                objetivo = mejor                # ruta parcial: hasta lo mas cerca encontrado
                break
            x = k % w
            libre_d = x < w - 1 and not bloqueo[k + 1]
            libre_i = x > 0 and not bloqueo[k - 1]
            libre_ab = k + w < n and not bloqueo[k + w]
            libre_ar = k - w >= 0 and not bloqueo[k - w]
            vecinos = []
            if libre_d:
                vecinos.append((k + 1, 1.0))
            if libre_i:
                vecinos.append((k - 1, 1.0))
            if libre_ab:
                vecinos.append((k + w, 1.0))
            if libre_ar:
                vecinos.append((k - w, 1.0))
            # diagonales sin cortar esquinas: los dos lados tienen que estar libres
            if libre_d and libre_ab and not bloqueo[k + w + 1]:
                vecinos.append((k + w + 1, raiz2))
            if libre_d and libre_ar and not bloqueo[k - w + 1]:
                vecinos.append((k - w + 1, raiz2))
            if libre_i and libre_ab and not bloqueo[k + w - 1]:
                vecinos.append((k + w - 1, raiz2))
            if libre_i and libre_ar and not bloqueo[k - w - 1]:
                vecinos.append((k - w - 1, raiz2))
            for v, paso in vecinos:
                nuevo = g + (paso * COSTE_AGUA if agua[v] else paso)
                if nuevo < coste.get(v, 1e18):
                    coste[v] = nuevo
                    padre[v] = k
                    heapq.heappush(abiertos, (nuevo + heur(v), nuevo, v))
        if objetivo not in padre:
            return None
        celdas = []
        k = objetivo
        while k != -1:
            celdas.append((k % w, k // w))
            k = padre[k]
        celdas.reverse()
        puntos = [self.centro_de(i, j) for i, j in self._suavizar(celdas)][1:]
        if puntos and objetivo == k_fin and self.libre(*self.celda_de(hasta)):
            puntos[-1] = pygame.Vector2(hasta)
        return puntos or [pygame.Vector2(hasta)]

    def _recta_libre(self, a, b):
        """True si la linea entre las celdas a y b solo pisa celdas libres (y sin agua si una de
        las dos no es agua: asi el camino no se mete en un lago para acortar)."""
        (i0, j0), (i1, j1) = a, b
        n = max(abs(i1 - i0), abs(j1 - j0)) * 2
        agua_extremos = self.agua[j0 * self.ancho + i0] and self.agua[j1 * self.ancho + i1]
        for k in range(1, n):
            t = k / n
            i, j = round(i0 + (i1 - i0) * t), round(j0 + (j1 - j0) * t)
            if not self.libre(i, j) or (self.agua[j * self.ancho + i] and not agua_extremos):
                return False
        return True

    def _suavizar(self, celdas):
        """Quita los puntos intermedios que se pueden saltar en linea recta (mirando como mucho
        SUAVIZADO_ALCANCE celdas por delante, para que no cueste demasiado en rutas largas)."""
        res = [celdas[0]]
        k = 0
        while k < len(celdas) - 1:
            siguiente = k + 1
            for m in range(min(len(celdas) - 1, k + SUAVIZADO_ALCANCE), k + 1, -1):
                if self._recta_libre(celdas[k], celdas[m]):
                    siguiente = m
                    break
            res.append(celdas[siguiente])
            k = siguiente
        return res


class ColaRutas:
    """Peticiones de ruta de los bots: como mucho MAX_RUTAS_POR_FOTOGRAMA por fotograma."""

    def __init__(self, rejilla):
        self.rejilla = rejilla
        self.pendientes = deque()

    def pedir(self, navegador, desde, hasta):
        if navegador not in self.pendientes:
            self.pendientes.append(navegador)
        navegador.peticion = (pygame.Vector2(desde), pygame.Vector2(hasta))

    def procesar(self):
        for _ in range(min(MAX_RUTAS_POR_FOTOGRAMA, len(self.pendientes))):
            nav = self.pendientes.popleft()
            if nav.peticion is None:
                continue
            desde, hasta = nav.peticion
            nav.peticion = None
            nav.recibir_ruta(self.rejilla.ruta(desde, hasta), hasta)


class Navegador:
    """Lleva a un bot por su ruta: fija su destino en el siguiente punto y vigila si se atasca."""

    def __init__(self, cola):
        self.cola = cola
        self.objetivo = None            # punto final al que va
        self.puntos = []                # puntos de la ruta que faltan
        self.peticion = None
        self.sin_ruta = False           # la ultima peticion no encontro camino
        self._t_atasco = 0.0
        self._pos_control = None
        self.atascos = 0                # veces seguidas que se atasco (1 = recalcular, 2 = hueco libre)

    def ir_a(self, c, destino, forzar=False):
        """Pide ruta hacia 'destino' (solo si cambia bastante o si se fuerza)."""
        destino = pygame.Vector2(destino)
        if not forzar and self.objetivo is not None and (destino - self.objetivo).length() < CELDA_PASO * 2 and \
                (self.puntos or self.peticion):
            return
        self.objetivo = destino
        self.puntos = []
        self.sin_ruta = False
        self.cola.pedir(self, c.posicion, destino)

    def parar(self, c):
        self.objetivo = None
        self.puntos = []
        self.peticion = None
        c.mover_a(c.posicion)

    def recibir_ruta(self, puntos, hasta):
        if puntos is None:
            self.sin_ruta = True
            self.puntos = []
        else:
            self.puntos = puntos

    @property
    def llegado(self):
        return self.objetivo is not None and not self.puntos and self.peticion is None and not self.sin_ruta

    def actualizar(self, c, dt, salir_a_hueco):
        """Un paso de navegacion (cada fotograma): sigue la ruta y se desatasca."""
        if self.objetivo is None:
            return
        while self.puntos and (self.puntos[0] - c.posicion).length() <= LLEGADA_PUNTO:
            self.puntos.pop(0)
        if self.puntos:
            c.mover_a(self.puntos[0])
        elif self.peticion is None:
            c.mover_a(c.posicion)
        # Antiatascos: si quiere moverse y no avanza
        if not self.puntos:
            self._t_atasco = 0.0
            self._pos_control = None
            return
        if self._pos_control is None:
            self._pos_control = pygame.Vector2(c.posicion)
        self._t_atasco += dt
        if self._t_atasco >= TIEMPO_ATASCO:
            if (c.posicion - self._pos_control).length() < AVANCE_MINIMO:
                self.atascos += 1
                if self.atascos >= 2:
                    salir_a_hueco(c)
                    self.atascos = 0
                self.ir_a(c, self.objetivo, forzar=True)
            else:
                self.atascos = 0
            self._t_atasco = 0.0
            self._pos_control = pygame.Vector2(c.posicion)
