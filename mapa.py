"""Mapas fijos guardados en archivo (Fase 2 del plan de NPC).

Un mapa es un archivo JSON en mapas/ (mapas/principal.json; mas adelante 4 mapas extra) con todo
el terreno: lagos, rocas (y cuales son cuevas de oso), arboles, arbustos, bosques, praderas,
pastizales, pasto y flores, las zonas con nombre y los puntos de aparicion de cada raza. El juego
lo carga en vez de generarlo; si falta o esta roto, avisa y usa el generador con la semilla fija.

- generar(nombre, semilla): crea el mapa con las reglas de su diseno (diseno_mapa) y lo devuelve
  como datos (dict) listos para guardar.
- guardar / leer: archivo JSON (una linea por objeto: comodo de comparar entre versiones).
- construir(datos): crea los objetos del juego. Cada objeto lleva su propia semilla ("s"), asi
  su forma y sus detalles (lobulos, hojas, color) salen siempre iguales.
- validar(...): comprueba el Anexo E del plan (ver validacion.py... aqui mismo, mas abajo).
- rejilla de rutas, vista previa en PNG: mas abajo.
"""
import json
import math
import os
import random
import zlib
from collections import deque

import pygame

import mundo
import fauna as FAUNA
import vegetacion as V
from diseno_mapa import DISENOS
from limite_mundo import LIMITE, BORDE_LIBRE
from spawn import Casa

VERSION_FORMATO = 2             # v2: piedras de montaña, zonas con rects, puertas, sin_borde
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mapas")
SEMILLA_OBJETOS = 7919          # semilla para las semillas propias de cada objeto
# Puntos de aparicion
SEPARACION_APARICION = 400      # px minimos entre dos puntos de aparicion de la misma raza
SEPARACION_GUARDIANES = 160     # px de la puerta del norte a cada guardian
HOLGURA_APARICION = 40          # px libres alrededor de un punto de aparicion
# Rejilla de rutas y conectividad
CELDA_RUTAS = 20                # px por celda
RADIO_PERSONAJE = 20            # holgura de la rejilla de rutas (un personaje de tamano 1)
PASILLO_MINIMO = 80             # Anexo E: pasillos de al menos 80 px entre obstaculos solidos
BOLSA_GRANDE = 40000            # px^2: una zona aislada mas grande que esto es un error (200 x 200)
# Densidad maxima en una pantalla (Anexo E)
PANTALLA = (1370, 1080)
MAX_PANTALLA = {"rocas": 60, "arboles": 150, "arbustos": 80}


def ruta(nombre):
    return os.path.join(CARPETA, nombre + ".json")


def ruta_rutas(nombre):
    return os.path.join(CARPETA, nombre + "_rutas.bin")


# ------------------------------------------------------------------ Generar y guardar
def generar(nombre="principal", semilla=mundo.SEMILLA_MUNDO):
    """Genera el mapa con su diseno y lo devuelve como datos (aun sin guardar). Los objetos se
    reconstruyen desde los datos, asi lo que se valida y se ve es exactamente lo que se carga."""
    diseno = DISENOS[nombre]
    charcos, veg, rocas = mundo.generar_terreno(semilla, diseno)
    rng = random.Random(semilla * SEMILLA_OBJETOS)
    s = lambda: rng.randrange(1 << 30)
    r1 = lambda v: round(float(v), 1)
    datos = {
        "version": VERSION_FORMATO, "nombre": nombre, "diseno": diseno.nombre, "semilla": semilla,
        "lado": LIMITE.lado,
        "lagos": [[r1(c.centro.x), r1(c.centro.y), c.radio, s()] for c in charcos],
        "rocas": [[r.rect.x + r.rect.width / 2, r.rect.y + r.rect.height / 2, r.rect.width, s(), int(getattr(r, "es_cueva", False)),
                   round(getattr(r, "angulo_entrada", 0.0), 4), int(getattr(r, "indestructible", False))] for r in rocas],
        "arboles": [[r1(a.centro.x), r1(a.centro.y), a.tipo, round(a.escala, 3), a.radio_tronco, a.radio_copa, s()]
                    for a in veg.arboles],
        "arbustos": [[r1(a.centro.x), r1(a.centro.y), a.radio, a.tipo, s()] for a in veg.arbustos],
        "bosques": [[r1(c.x), r1(c.y), r, d, int(reg)] for (c, r), d, reg in zip(veg.bosques, veg.densidad_bosques, veg.de_region)],
        "praderas": [[r1(c.x), r1(c.y), r] for c, r in veg.praderas],
        "pastizales": [[r1(c.x), r1(c.y), r] for c, r in veg.pastizales],
        "pasto": [[r1(p.centro.x), r1(p.centro.y), round(p.escala, 3), s()] for p in veg.pasto],
        "flores": [[r1(f.centro.x), r1(f.centro.y), V.COLORES_FLOR.index(f.color), s()] for f in veg.flores],
    }
    datos["zonas"] = []
    for z in diseno.zonas:
        c = diseno.absoluto(LIMITE, z["u"], z["v"])
        zona = {"nombre": z["nombre"], "x": r1(c.x), "y": r1(c.y), "radio": z["radio"], "descripcion": z["descripcion"]}
        if "rects" in z:
            zona["rects"] = [list(diseno.rect_absoluto(LIMITE, r)) for r in z["rects"]]
        datos["zonas"].append(zona)
    datos["puertas"] = [{"nombre": n, "destino": dest, "lado": lado, "x": r1(diseno.absoluto(LIMITE, u, v).x),
                         "y": r1(diseno.absoluto(LIMITE, u, v).y), "activa": False}
                        for n, dest, lado, u, v in diseno.puertas]
    # regiones donde los obstaculos pueden llegar al borde (la montaña, el gran lago)
    datos["sin_borde"] = [list(diseno.rect_absoluto(LIMITE, r)) for r in diseno.sin_borde]
    charcos2, veg2, rocas2 = construir(datos)
    datos["aparicion"] = puntos_de_aparicion(datos, diseno, charcos2, veg2, rocas2, random.Random(semilla + 1))
    return datos


def guardar(datos, nombre=None):
    """JSON con una linea por objeto (las versiones se comparan bien con git)."""
    nombre = nombre or datos["nombre"]
    os.makedirs(CARPETA, exist_ok=True)
    partes = []
    for clave, valor in datos.items():
        if isinstance(valor, list):
            filas = ",\n".join("    " + json.dumps(x, ensure_ascii=False) for x in valor)
            partes.append('  "%s": [\n%s\n  ]' % (clave, filas) if valor else '  "%s": []' % clave)
        else:
            partes.append('  "%s": %s' % (clave, json.dumps(valor, ensure_ascii=False)))
    with open(ruta(nombre), "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n" + ",\n".join(partes) + "\n}\n")
    return ruta(nombre)


def leer(nombre):
    with open(ruta(nombre), encoding="utf-8") as f:
        datos = json.load(f)
    if datos.get("version") != VERSION_FORMATO:
        raise ValueError("version de formato %s no soportada (se espera %d)" % (datos.get("version"), VERSION_FORMATO))
    if datos.get("lado") != LIMITE.lado:
        raise ValueError("el mapa es de %s px y el mundo de %s px" % (datos.get("lado"), LIMITE.lado))
    return datos


# ------------------------------------------------------------------ Construir los objetos
def construir(datos):
    """Crea (charcos, vegetacion, rocas) desde los datos. Cada objeto usa su propia semilla para
    sus detalles; el azar global queda como estaba."""
    estado = random.getstate()
    try:
        charcos = []
        for x, y, radio, s in datos["lagos"]:
            random.seed(s)
            charcos.append(mundo.Charco(x, y, radio))
        veg = V.SistemaVegetacion(LIMITE, mundo.ZONA_SEGURA_SPAWN, charcos, DISENOS.get(datos.get("diseno")),
                                  generar=False)
        for x, y, r, d, de_region in datos["bosques"]:
            veg.bosques.append((pygame.Vector2(x, y), r))
            veg.densidad_bosques.append(d)
            veg.regiones_bosques.append(None)
            veg.de_region.append(bool(de_region))
        veg.praderas = [(pygame.Vector2(x, y), r) for x, y, r in datos["praderas"]]
        veg.pastizales = [(pygame.Vector2(x, y), r) for x, y, r in datos["pastizales"]]
        for x, y, tipo, escala, rt, rc, s in datos["arboles"]:
            random.seed(s)
            arbol = V.Arbol(x, y, tipo, escala, rt, rc)
            arbol.caja_rejilla = pygame.Rect(0, 0, rt * 2 + 16, rt * 2 + 16)
            arbol.caja_rejilla.center = (round(x), round(y))
            veg.rejilla.agregar(arbol.caja_rejilla)
            veg.arboles.append(arbol)
        for x, y, radio, tipo, s in datos["arbustos"]:
            random.seed(s)
            arbusto = V.Arbusto(x, y, radio, tipo)
            arbusto.caja_rejilla = pygame.Rect(0, 0, radio * 2 + 30, radio * 2 + 30)
            arbusto.caja_rejilla.center = (round(x), round(y))
            veg.rejilla.agregar(arbusto.caja_rejilla)
            veg.arbustos.append(arbusto)
        for x, y, escala, s in datos["pasto"]:
            random.seed(s)
            veg.pasto.append(V.Pasto(x, y, escala))
        for x, y, color, s in datos["flores"]:
            random.seed(s)
            veg.flores.append(V.Flor(x, y, V.COLORES_FLOR[color]))
        rocas = []
        for x, y, lado, s, cueva, angulo, montana in datos["rocas"]:
            random.seed(s)
            roca = (mundo.PiedraMontana if montana else mundo.Roca)(x, y, lado)
            if cueva:
                roca.es_cueva = True
                roca.angulo_entrada = angulo
            rocas.append(roca)
        veg.registrar_obstaculos(rocas, quitar_cobertura=False)
    finally:
        random.setstate(estado)
    return charcos, veg, rocas


def cargar_terreno(nombre="principal"):
    """(charcos, vegetacion, rocas, datos) del mapa guardado, o None (con el motivo) si falta o
    esta roto: entonces el juego usa el generador con la semilla fija."""
    try:
        datos = leer(nombre)
        return construir(datos) + (datos,), None
    except (OSError, ValueError, KeyError, TypeError) as e:
        return None, "%s: %s" % (type(e).__name__, e)


# ------------------------------------------------------------------ Puntos de aparicion
def _obstaculos(charcos, veg, rocas):
    return rocas + Casa(mundo.CENTRO_MUNDO).paredes, [(a.centro, a.radio_tronco) for a in veg.arboles] + \
        [(a.centro, a.radio) for a in veg.arbustos]


def punto_transitable(p, charcos, rocas, circulares, holgura=HOLGURA_APARICION):
    """Tierra firme, dentro del mapa y sin obstaculos a menos de 'holgura' px."""
    if not LIMITE.dentro(p, BORDE_LIBRE) or any(c.contiene(p) for c in charcos):
        return False
    return mundo.punto_libre(p, holgura, rocas, circulares, [])


def puntos_de_aparicion(datos, diseno, charcos, veg, rocas, rng):
    """Puntos de aparicion por raza dentro de su zona (los enanos, en la boca de las cuevas)."""
    rocas_obs, circulares = _obstaculos(charcos, veg, rocas)
    zonas = {z["nombre"]: z for z in datos["zonas"]}
    res = {}
    for raza, (nombre_zona, cantidad) in diseno.aparicion.items():
        z = zonas[nombre_zona]
        centro = pygame.Vector2(z["x"], z["y"])
        puntos = []
        if raza == "Guardian":
            # uno a cada lado de la puerta del norte (o en el centro de su zona si no hay puerta)
            norte = next((p for p in datos.get("puertas", []) if p["lado"] == "norte"), None)
            if norte is None:
                puntos.append(centro)
            else:
                for k in range(cantidad):
                    lado = -1 if k % 2 == 0 else 1
                    puntos.append(pygame.Vector2(norte["x"] + lado * SEPARACION_GUARDIANES * (k // 2 + 1),
                                                 norte["y"] + mundo.FONDO_PUERTA_MAPA + 60))
        elif raza == "Enanos":
            cuevas = sorted((r for r in rocas if getattr(r, "es_cueva", False)),
                            key=lambda r: (pygame.Vector2(r.rect.center) - centro).length())
            for r in cuevas[:cantidad]:
                oso = FAUNA.Oso(r)
                puntos.append(oso.entrada + oso.entrada_dir * 40)
        else:
            rects = [pygame.Rect(r) for r in z.get("rects", [])]
            for _ in range(4000):
                if len(puntos) >= cantidad:
                    break
                if rects:                       # zona con forma de casillas (el bosque de los elfos)
                    r = rng.choice(rects)
                    p = pygame.Vector2(rng.uniform(r.left, r.right), rng.uniform(r.top, r.bottom))
                else:
                    ang, dist = rng.uniform(0, math.tau), math.sqrt(rng.random()) * z["radio"]
                    p = centro + pygame.Vector2(math.cos(ang), math.sin(ang)) * dist
                if (punto_transitable(p, charcos, rocas_obs, circulares)
                        and all((p - q).length() >= SEPARACION_APARICION for q in puntos)):
                    puntos.append(p)
        res[raza] = [[round(p.x, 1), round(p.y, 1)] for p in puntos]
    return res


# ------------------------------------------------------------------ Rejilla de rutas
class Rejilla:
    """Rejilla del mapa en celdas de CELDA_RUTAS px: 1 = bloqueada para un circulo de radio
    'holgura' (rocas, paredes, troncos, arbustos en los que no se cabe y zona profunda)."""

    def __init__(self, charcos, veg, rocas, holgura, casa=True):
        self.celda = CELDA_RUTAS
        self.origen = pygame.Vector2(LIMITE.rect.topleft)
        self.ancho = self.alto = math.ceil(LIMITE.lado / CELDA_RUTAS)
        self.bloqueo = bytearray(self.ancho * self.alto)
        h = holgura
        solidos = rocas + (Casa(mundo.CENTRO_MUNDO).paredes if casa else [])
        for r in solidos:
            self._rect(r.rect.inflate(h * 2, h * 2))
        for a in veg.arboles:
            self._circulo(a.centro, a.radio_tronco + h)
        for a in veg.arbustos:
            if a.radio < RADIO_PERSONAJE:          # no se cabe dentro: es solido
                self._circulo(a.centro, a.radio + h)
        for c in charcos:
            if c.es_lago_profundo:
                self._circulo(c.centro, c.radio_peligro + h)
        # borde del mapa
        for i in range(self.ancho):
            for j in range(self.alto):
                if min(i, j, self.ancho - 1 - i, self.alto - 1 - j) * CELDA_RUTAS < h:
                    self.bloqueo[j * self.ancho + i] = 1

    def _rango(self, a, b, n):
        return max(0, int(a // self.celda)), min(n - 1, int(b // self.celda))

    def _rect(self, rect):
        i0, i1 = self._rango(rect.left - self.origen.x, rect.right - self.origen.x, self.ancho)
        j0, j1 = self._rango(rect.top - self.origen.y, rect.bottom - self.origen.y, self.alto)
        for j in range(j0, j1 + 1):
            self.bloqueo[j * self.ancho + i0: j * self.ancho + i1 + 1] = b"\x01" * (i1 - i0 + 1)

    def _circulo(self, c, r):
        cx, cy = c.x - self.origen.x, c.y - self.origen.y
        i0, i1 = self._rango(cx - r, cx + r, self.ancho)
        j0, j1 = self._rango(cy - r, cy + r, self.alto)
        r2 = r * r
        for j in range(j0, j1 + 1):
            py = (j + 0.5) * self.celda - cy
            for i in range(i0, i1 + 1):
                px = (i + 0.5) * self.celda - cx
                if px * px + py * py <= r2:
                    self.bloqueo[j * self.ancho + i] = 1

    def celda_de(self, p):
        return int((p[0] - self.origen.x) // self.celda), int((p[1] - self.origen.y) // self.celda)

    def centro_de(self, i, j):
        return pygame.Vector2(self.origen.x + (i + 0.5) * self.celda, self.origen.y + (j + 0.5) * self.celda)

    def alcanzables(self, desde):
        """Celdas libres alcanzables andando desde el punto 'desde' (bytearray 1/0)."""
        visto = bytearray(len(self.bloqueo))
        i, j = self.celda_de(desde)
        inicio = j * self.ancho + i
        if self.bloqueo[inicio]:
            return visto
        cola = deque([inicio])
        visto[inicio] = 1
        w, bloqueo = self.ancho, self.bloqueo
        while cola:
            k = cola.popleft()
            x = k % w
            for n in (k - w, k + w, k - 1 if x > 0 else -1, k + 1 if x < w - 1 else -1):
                if 0 <= n < len(bloqueo) and not visto[n] and not bloqueo[n]:
                    visto[n] = 1
                    cola.append(n)
        return visto

    def bolsas(self, alcanzado):
        """Zonas libres que no se alcanzan: lista de (area_px2, centro) de mayor a menor."""
        w = self.ancho
        marcado = bytearray(alcanzado)
        res = []
        for k in range(len(self.bloqueo)):
            if self.bloqueo[k] or marcado[k]:
                continue
            cola, marcado[k], celdas, sx, sy = deque([k]), 1, 0, 0, 0
            while cola:
                q = cola.popleft()
                celdas += 1
                sx += q % w
                sy += q // w
                x = q % w
                for n in (q - w, q + w, q - 1 if x > 0 else -1, q + 1 if x < w - 1 else -1):
                    if 0 <= n < len(self.bloqueo) and not marcado[n] and not self.bloqueo[n]:
                        marcado[n] = 1
                        cola.append(n)
            res.append((celdas * self.celda * self.celda, self.centro_de(sx / celdas, sy / celdas)))
        return sorted(res, key=lambda b: -b[0])

    def guardar(self, ruta_archivo):
        """Cabecera (RUTAS1, celda, ancho, alto) y las celdas comprimidas con zlib (1 = bloqueada)."""
        with open(ruta_archivo, "wb") as f:
            f.write(b"RUTAS1")
            f.write(self.celda.to_bytes(2, "little") + self.ancho.to_bytes(4, "little") + self.alto.to_bytes(4, "little"))
            f.write(zlib.compress(bytes(self.bloqueo), 9))


# ------------------------------------------------------------------ Validador (Anexo E)
def validar(datos, charcos=None, veg=None, rocas=None):
    """Comprueba las caracteristicas obligatorias del Anexo E. Devuelve (errores, avisos, info).
    Un mapa con errores no se usa."""
    if charcos is None:
        charcos, veg, rocas = construir(datos)
    errores, avisos, info = [], [], {}
    centro = mundo.CENTRO_MUNDO

    # Forma, borde y jardin
    sin_borde = [pygame.Rect(r) for r in datos.get("sin_borde", [])]
    exento = lambda p: any(r.collidepoint(p) for r in sin_borde)      # montaña, gran lago
    fuera = [r for r in rocas if not exento(r.rect.center) and not LIMITE.dentro(r.rect.center, r.rect.width / 2 + BORDE_LIBRE - 1)]
    fuera += [a for a in veg.arboles + veg.arbustos if not exento(a.centro) and not LIMITE.dentro(a.centro, BORDE_LIBRE - 1)]
    fuera += [c for c in charcos if not exento(c.centro) and not LIMITE.dentro(c.centro, c.radio + BORDE_LIBRE - 1)]
    fuera += [r for r in rocas if not LIMITE.dentro(r.rect.center, r.rect.width / 2 - 1)]      # nada sale del mapa
    if fuera:
        errores.append("%d obstaculos a menos de %d px del borde del mapa" % (len(fuera), BORDE_LIBRE))
    en_jardin = [r for r in rocas if (pygame.Vector2(r.rect.center) - centro).length() < mundo.ZONA_SEGURA_SPAWN]
    en_jardin += [a for a in veg.arboles + veg.arbustos if (a.centro - centro).length() < mundo.ZONA_SEGURA_SPAWN]
    if en_jardin:
        errores.append("%d obstaculos dentro del jardin de la casa" % len(en_jardin))

    # Zona del guardian: espacio abierto de 600 px o mas
    zonas = {z["nombre"]: z for z in datos.get("zonas", [])}
    if "Guardian" not in zonas:
        errores.append("falta la zona del guardian (norte)")
    else:
        g = zonas["Guardian"]
        cg = pygame.Vector2(g["x"], g["y"])
        if cg.y >= centro.y:
            errores.append("la zona del guardian no esta al norte del centro")
        cerca = sum(1 for r in rocas if (pygame.Vector2(r.rect.center) - cg).length() < 600)
        cerca += sum(1 for a in veg.arboles + veg.arbustos if (a.centro - cg).length() < 600)
        cerca += sum(1 for c in charcos if (c.centro - cg).length() < 600 + c.radio)
        if cerca:
            errores.append("la zona del guardian no esta despejada (%d obstaculos a menos de 600 px)" % cerca)

    # Cuevas, lagos, praderas, bosques
    cuevas = [r for r in rocas if getattr(r, "es_cueva", False)]
    info["cuevas"] = len(cuevas)
    if len(cuevas) < 12:
        errores.append("hay %d cuevas de oso (minimo 12)" % len(cuevas))
    juntas = sum(1 for i, a in enumerate(cuevas) for b in cuevas[i + 1:]
                 if (pygame.Vector2(a.rect.center) - pygame.Vector2(b.rect.center)).length() < 1500)
    if juntas:
        errores.append("%d pares de cuevas a menos de 1500 px" % juntas)
    profundos = sum(c.es_lago_profundo for c in charcos)
    info["lagos"], info["lagos_profundos"] = len(charcos), profundos
    if profundos < 6:
        errores.append("hay %d lagos con zona profunda (minimo 6)" % profundos)
    info["praderas"], info["pastizales"] = len(veg.praderas), len(veg.pastizales)
    if len(veg.praderas) < 8 and len(veg.pastizales) < 8:
        errores.append("faltan praderas para las madrigueras (minimo 8)")
    lejos = [b for b in veg.bosques_fauna if (b[0] - centro).length() > 1500]
    info["bosques"] = len(veg.bosques_fauna)
    if len(lejos) < 8:
        errores.append("hay %d bosques a mas de 1500 px del centro (minimo 8, para las manadas)" % len(lejos))
    con_escondite = sum(1 for c, r in veg.bosques
                        if any(a.tipo == V.TIPO_ESCONDITE and (a.centro - c).length() <= r for a in veg.arbustos))
    if con_escondite < 4:
        errores.append("hay %d bosques con arbustos de escondite (minimo 4, para los elfos)" % con_escondite)

    # Puntos de aparicion
    for raza, puntos in datos.get("aparicion", {}).items():
        _, cantidad = DISENOS[datos["diseno"]].aparicion.get(raza, (None, len(puntos)))
        if len(puntos) < cantidad:
            errores.append("%s: %d puntos de aparicion de %d" % (raza, len(puntos), cantidad))

    # Densidad por pantalla
    info["rocas"], info["arboles"], info["arbustos"] = len(rocas), len(veg.arboles), len(veg.arbustos)
    for clave, posiciones in (("rocas", [r.rect.center for r in rocas]), ("arboles", [a.centro for a in veg.arboles]),
                              ("arbustos", [a.centro for a in veg.arbustos])):
        maximo = densidad_maxima(posiciones)
        info["max_%s_pantalla" % clave] = maximo
        if maximo > MAX_PANTALLA[clave]:
            errores.append("hasta %d %s en una pantalla (maximo %d)" % (maximo, clave, MAX_PANTALLA[clave]))

    # Conectividad: pasillos de PASILLO_MINIMO px desde la puerta de la casa
    rejilla = Rejilla(charcos, veg, rocas, PASILLO_MINIMO // 2)
    alcanzado = rejilla.alcanzables(Casa(centro).puerta + pygame.Vector2(0, 60))
    bolsas = rejilla.bolsas(alcanzado)
    grandes = [b for b in bolsas if b[0] > BOLSA_GRANDE]
    info["bolsas"] = len(bolsas)
    info["bolsas_grandes"] = [(round(a), round(c.x), round(c.y)) for a, c in grandes]
    libres = len(rejilla.bloqueo) - sum(rejilla.bloqueo)
    info["tierra_alcanzable_%"] = round(100.0 * sum(alcanzado) / max(1, libres), 2)
    if grandes:
        errores.append("%d zonas grandes aisladas (no se llega con pasillos de %d px)" % (len(grandes), PASILLO_MINIMO))
    # Cada puerta se alcanza andando desde la casa (por su camino o su paso)
    for p in datos.get("puertas", []):
        dentro = {"norte": (0, 1), "sur": (0, -1), "oeste": (1, 0), "este": (-1, 0)}[p["lado"]]
        frente = pygame.Vector2(p["x"], p["y"]) + pygame.Vector2(dentro) * (PASILLO_MINIMO // 2 + mundo.FONDO_PUERTA_MAPA)
        i, j = rejilla.celda_de(frente)
        if not (0 <= i < rejilla.ancho and 0 <= j < rejilla.alto) or not alcanzado[j * rejilla.ancho + i]:
            errores.append("no se llega andando a la puerta '%s'" % p["nombre"])
    if bolsas and not grandes:
        avisos.append("%d huecos pequenos aislados entre obstaculos (menores de 200 x 200 px)" % len(bolsas))
    info["_bolsas"] = bolsas
    return errores, avisos, info


def densidad_maxima(posiciones, ventana=PANTALLA):
    """Mayor numero de objetos dentro de una ventana del tamano de una pantalla (ventanas que
    se solapan a media pantalla)."""
    pw, ph = ventana
    mitad_w, mitad_h = pw / 2, ph / 2
    cuenta = {}
    x0, y0 = LIMITE.rect.topleft
    for p in posiciones:
        i, j = int((p[0] - x0) // mitad_w), int((p[1] - y0) // mitad_h)
        cuenta[(i, j)] = cuenta.get((i, j), 0) + 1
    maximo = 0
    for (i, j) in cuenta:
        total = sum(cuenta.get((i + a, j + b), 0) for a in (0, 1) for b in (0, 1))
        maximo = max(maximo, total)
    return maximo


# ------------------------------------------------------------------ Vista previa (PNG)
ESCALA_PREVIA = 0.1             # 17 700 px -> 1770 px
COLOR_TERRENO_PREVIA = (52, 60, 50)
CUADROS = 10                    # cuadricula de referencia A-J / 1-10
COLORES_RAZA = {"Guardian": (255, 215, 0), "Humanos": (90, 170, 255), "Semihumanos": (255, 150, 60),
                "Elfos": (120, 255, 140), "Enanos": (230, 90, 230)}
COLORES_ARBUSTO = {V.TIPO_ESCONDITE: (110, 200, 110), V.TIPO_VENENOSO: (190, 110, 220), V.TIPO_FRUTAL: (240, 90, 90)}


def dibujar_terreno(img, a_img, r_img, charcos, veg, rocas):
    """Terreno visto desde arriba (vista previa y vista lejana de ShadowGOD): praderas,
    pastizales, bosques, lagos, arboles, arbustos, rocas y cuevas. 'a_img' pasa un punto del
    mundo a la imagen y 'r_img' un radio."""
    for c, r in veg.praderas:
        pygame.draw.circle(img, (80, 104, 58), a_img(c), r_img(r))
    for c, r in veg.pastizales:
        pygame.draw.circle(img, (92, 118, 62), a_img(c), r_img(r))
    for c, r in veg.bosques:
        pygame.draw.circle(img, (38, 66, 40), a_img(c), r_img(r))
    for ch in charcos:
        for c, r in ch.circulos:
            pygame.draw.circle(img, (60, 120, 200), a_img(c), r_img(r))
        if ch.es_lago_profundo:
            pygame.draw.circle(img, (20, 50, 110), a_img(ch.centro), r_img(ch.radio_peligro))
    for a in veg.arboles:
        pygame.draw.circle(img, (30, 110, 45) if a.tipo != "seco" else (120, 96, 60), a_img(a.centro), 2)
    for a in veg.arbustos:
        pygame.draw.circle(img, COLORES_ARBUSTO[a.tipo], a_img(a.centro), max(2, r_img(a.radio)))
    for r in rocas:
        rect = pygame.Rect(a_img(r.rect.topleft), (max(2, r_img(r.rect.width)), max(2, r_img(r.rect.height))))
        color = (90, 60, 40) if getattr(r, "es_cueva", False) else (125, 130, 145) if getattr(r, "indestructible", False) else (175, 160, 135)
        pygame.draw.rect(img, color, rect)
        if getattr(r, "es_cueva", False):
            pygame.draw.circle(img, (255, 255, 255), rect.center, max(6, rect.width), 2)


def imagen_terreno(charcos, veg, rocas, escala):
    """Superficie con todo el mapa a 'escala' (la cuadricula y la leyenda no van)."""
    lado = round(LIMITE.lado * escala)
    img = pygame.Surface((lado, lado))
    img.fill(COLOR_TERRENO_PREVIA)
    x0, y0 = LIMITE.rect.topleft
    dibujar_terreno(img, lambda p: (round((p[0] - x0) * escala), round((p[1] - y0) * escala)),
                    lambda r: max(1, round(r * escala)), charcos, veg, rocas)
    return img


def vista_previa(datos, ruta_png, charcos=None, veg=None, rocas=None, bolsas=()):
    """Dibuja el mapa entero en un PNG con zonas, cuevas, lagos, puntos de aparicion y una
    cuadricula de referencia (columnas A-J, filas 1-10) para describir cambios ("en C4...")."""
    if charcos is None:
        charcos, veg, rocas = construir(datos)
    if not pygame.font.get_init():
        pygame.font.init()
    e = ESCALA_PREVIA
    lado = round(LIMITE.lado * e)
    margen, leyenda = 40, 330
    img = pygame.Surface((lado + margen * 2 + leyenda, lado + margen * 2))
    img.fill((22, 24, 30))
    x0, y0 = LIMITE.rect.topleft
    a_img = lambda p: (round(margen + (p[0] - x0) * e), round(margen + (p[1] - y0) * e))
    r_img = lambda r: max(1, round(r * e))
    pygame.draw.rect(img, COLOR_TERRENO_PREVIA, (margen, margen, lado, lado))
    img.set_clip(pygame.Rect(margen, margen, lado, lado))          # lo que pase del borde no se ve
    dibujar_terreno(img, a_img, r_img, charcos, veg, rocas)
    for area, c in bolsas:
        if area > BOLSA_GRANDE:
            pygame.draw.circle(img, (255, 40, 40), a_img(c), max(4, r_img(math.sqrt(area))), 2)
    img.set_clip(None)
    # Casa y jardin
    pygame.draw.circle(img, (70, 110, 70), a_img(mundo.CENTRO_MUNDO), r_img(mundo.ZONA_SEGURA_SPAWN))
    pygame.draw.rect(img, (150, 58, 46), pygame.Rect(0, 0, r_img(300), r_img(300)).move(
        a_img(mundo.CENTRO_MUNDO)[0] - r_img(150), a_img(mundo.CENTRO_MUNDO)[1] - r_img(150)))
    # Cuadricula de referencia
    fuente = pygame.font.SysFont("Segoe UI", 16, bold=True)
    paso = lado / CUADROS
    for k in range(CUADROS + 1):
        pygame.draw.line(img, (255, 255, 255), (margen + k * paso, margen), (margen + k * paso, margen + lado), 1)
        pygame.draw.line(img, (255, 255, 255), (margen, margen + k * paso), (margen + lado, margen + k * paso), 1)
    for k in range(CUADROS):
        letra = fuente.render("ABCDEFGHIJ"[k], True, (230, 230, 230))
        img.blit(letra, letra.get_rect(center=(margen + (k + 0.5) * paso, margen // 2)))
        num = fuente.render(str(k + 1), True, (230, 230, 230))
        img.blit(num, num.get_rect(center=(margen // 2, margen + (k + 0.5) * paso)))
    # Zonas y puntos de aparicion
    for p in datos.get("puertas", []):
        rp = mundo.rect_puerta(p)
        rect = pygame.Rect(a_img(rp.topleft), (max(8, r_img(rp.width) * 3), max(8, r_img(rp.height) * 3)))
        rect.center = a_img(rp.center)
        pygame.draw.rect(img, (240, 220, 160), rect)
        pygame.draw.rect(img, (40, 30, 20), rect, 2)
        txt = fuente.render(p["nombre"], True, (240, 220, 160))
        sitio = {"norte": (0, 22), "sur": (0, -22), "oeste": (txt.get_width() // 2 + 14, 0),
                 "este": (-txt.get_width() // 2 - 14, 0)}[p["lado"]]
        img.blit(txt, txt.get_rect(center=(rect.centerx + sitio[0], rect.centery + sitio[1])))
    for z in datos.get("zonas", []):
        for r in z.get("rects", []):
            rr = pygame.Rect(a_img((r[0], r[1])), (r_img(r[2]), r_img(r[3])))
            pygame.draw.rect(img, COLORES_RAZA.get(z["nombre"], (255, 255, 255)), rr, 2)
        color = COLORES_RAZA.get(z["nombre"], (255, 255, 255))
        if z.get("rects"):                      # zona con forma de casillas: solo sus rects
            txt = fuente.render(z["nombre"], True, color)
            r = z["rects"][-1]
            img.blit(txt, txt.get_rect(center=a_img((r[0] + r[2] / 2, r[1] - 120))))
            continue
        pygame.draw.circle(img, color, a_img((z["x"], z["y"])), r_img(z["radio"]), 2)
        txt = fuente.render(z["nombre"], True, color)
        # el nombre arriba del circulo, o abajo si el circulo toca el borde norte
        arriba = z["y"] - z["radio"] > LIMITE.rect.top
        img.blit(txt, txt.get_rect(center=a_img((z["x"], z["y"] + (-0.8 if arriba else 0.8) * z["radio"]))))
    for raza, puntos in datos.get("aparicion", {}).items():
        color = COLORES_RAZA.get(raza, (255, 255, 255))
        for p in puntos:
            pygame.draw.circle(img, (0, 0, 0), a_img(p), 7)
            pygame.draw.circle(img, color, a_img(p), 5)
    pygame.draw.rect(img, (200, 200, 210), (margen, margen, lado, lado), 2)
    # Norte arriba
    norte = fuente.render("N", True, (255, 255, 255))
    img.blit(norte, (margen + lado + 14, margen))
    # Leyenda
    lx, ly = margen * 2 + lado + 10, margen + 40
    chica = pygame.font.SysFont("Segoe UI", 15)
    filas = [("Mapa %s (v%d)" % (datos["nombre"], datos["version"]), None),
             ("Cuadro = %d px" % round(LIMITE.lado / CUADROS), None), ("", None),
             ("Pradera", (80, 104, 58)), ("Pastizal (madrigueras)", (92, 118, 62)), ("Bosque", (38, 66, 40)),
             ("Arbol", (30, 110, 45)), ("Lago / zona profunda", (60, 120, 200)), ("", (20, 50, 110)),
             ("Roca", (175, 160, 135)), ("Cueva de oso (circulo)", (90, 60, 40)),
             ("Arbusto escondite", COLORES_ARBUSTO[V.TIPO_ESCONDITE]), ("Arbusto venenoso", COLORES_ARBUSTO[V.TIPO_VENENOSO]),
             ("Arbusto frutal", COLORES_ARBUSTO[V.TIPO_FRUTAL]), ("Casa y jardin", (150, 58, 46)), ("", None)]
    filas += [("Aparicion: %s (%d)" % (r, len(p)), COLORES_RAZA.get(r)) for r, p in datos.get("aparicion", {}).items()]
    filas += [("", None), ("Circulo rojo: zona aislada", (255, 40, 40))]
    for texto, color in filas:
        if color is not None:
            pygame.draw.rect(img, color, (lx, ly + 3, 16, 14))
        img.blit(chica.render(texto, True, (225, 225, 230)), (lx + (24 if color else 0), ly))
        ly += 24
    os.makedirs(os.path.dirname(os.path.abspath(ruta_png)), exist_ok=True)
    pygame.image.save(img, ruta_png)
    return ruta_png
