"""
Vegetación del mundo: arbustos con forma de nube (igual que los charcos, pero más pequeños).

Hay 3 tipos, pero TODOS se ven iguales (mezcla de los mismos 3 verdes) para que no se puedan identificar:
- Escondite: sirve para ocultarse.
- Venenoso: también oculta, pero hace 1 de daño cada 2 segundos.
- Frutal: oculta y tiene 1 a 5 orbes rojos de curación dentro. Al consumirlos todos,
  el arbusto desaparece y 1 minuto después reaparece otro como brote (20px); crece a joven
  (1 fruta) tras 1 min y a maduro (frutas aleatorias) tras otro minuto.

Además existe un 10% de probabilidad de que el mundo tenga de 1 a 3 matorrales: conjuntos
densos de 5 a 8 arbustos de distintos tipos y tamaños, solapados formando una masa sin huecos.

Un personaje solo puede entrar si su diámetro cabe en el del arbusto; si no cabe, el arbusto es sólido.
Estando dentro no se le ve desde afuera (`personaje.oculto`) y él ve el mapa más oscuro.
"""
import math
import random
import pygame

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
TIPO_ESCONDITE = "Escondite"
TIPO_VENENOSO = "Venenoso"
TIPO_FRUTAL = "Frutal"

CANTIDADES = {
    TIPO_ESCONDITE: (110, 210),
    TIPO_VENENOSO: (60, 110),
    TIPO_FRUTAL: (20, 32),
}

DIAMETRO_MIN = 50
DIAMETRO_MAX = 150
DIAMETRO_MIN_FRUTAL = 50       # Los frutales siempre deben poder usarse (personaje tamaño 1 = 40 de diámetro)
DIAMETRO_BROTE = 20            # Tamaño del frutal recién reaparecido (brote)
DIAMETRO_ARBUSTO_GRANDE = 100  # A partir de este diámetro el arbusto es "grande" (Cortar solo lo corta a nivel 20)

DANO_VENENO = 1
INTERVALO_VENENO = 2.0         # Segundos entre cada punto de daño

ORBES_MIN = 1
ORBES_MAX = 5
CURACION_ORBE = 2              # Vida que recupera cada orbe (sin pasar de la vida máxima)
RADIO_ORBE = 4
TIEMPO_REAPARICION_FRUTAL = 60.0
TIEMPO_CRECIMIENTO_FRUTAL = 60.0   # Cada fase del frutal reaparecido dura 1 minuto

# Matorrales: conjuntos densos de arbustos
PROB_MATORRAL = 0.40
MATORRAL_MIN_ARBUSTOS = 5
MATORRAL_MAX_ARBUSTOS = 8

ALPHA_INTERIOR = 110           # Transparencia del arbusto en el que estás metido (para verte a ti mismo)
OSCURECIMIENTO = 95            # 0-255: cuánto se oscurece el mapa estando dentro de un arbusto

# Mismos 3 verdes para todos los tipos (no se distinguen a simple vista)
VERDES = [(44, 104, 50), (72, 142, 58), (112, 170, 74)]
VERDE_BORDE = (24, 58, 30)
COLOR_ORBE = (220, 36, 48)
COLOR_ORBE_BRILLO = (255, 150, 150)

# Colores solo para depuración [H] (ahí sí se revela el tipo)
COLOR_DEBUG = {
    TIPO_ESCONDITE: (120, 255, 120),
    TIPO_VENENOSO: (200, 80, 255),
    TIPO_FRUTAL: (255, 90, 90),
}


def circulos_nube(x, y, radio):
    """Devuelve los círculos (centro, radio) que forman una nube: núcleo + lóbulos alrededor."""
    circulos = [(pygame.Vector2(x, y), radio * 0.62)]
    lobulos = random.randint(5, 12)
    for i in range(lobulos):
        ang = (i / lobulos) * math.tau + random.uniform(-0.3, 0.3)
        r_lobulo = radio * random.uniform(0.32, 0.45)
        dist = (radio - r_lobulo) * random.uniform(0.85, 1.0)
        circulos.append((pygame.Vector2(x + math.cos(ang) * dist, y + math.sin(ang) * dist), r_lobulo))
    return circulos


# -----------------------------
# ARBUSTO
# -----------------------------
class Arbusto:
    def __init__(self, x, y, radio, tipo, fase="maduro", radio_final=None):
        self.centro = pygame.Vector2(x, y)
        self.radio = radio
        self.tipo = tipo
        # Fase de crecimiento (solo frutales reaparecidos): "brote" -> "joven" -> "maduro"
        self.fase = fase
        self.tiempo_fase = 0.0
        self.radio_final = radio_final if radio_final is not None else radio
        self.orbes = []

        self._reconstruir()

        if tipo == TIPO_FRUTAL:
            self._generar_orbes()

    def _reconstruir(self):
        """(Re)genera la forma y la superficie pre-renderizada según el radio actual."""
        x, y = self.centro.x, self.centro.y
        self.circulos = circulos_nube(x, y, self.radio)

        # Pre-renderizado: borde oscuro + lóbulos con los 3 verdes + manchas de hojas
        extension = self.radio + 4
        lado = int(extension * 2)
        origen = pygame.Vector2(x - extension, y - extension)
        self.rect = pygame.Rect(round(origen.x), round(origen.y), lado, lado)

        self.superficie = pygame.Surface((lado, lado), pygame.SRCALPHA)
        locales = [(c - origen, r) for c, r in self.circulos]
        for c, r in locales:
            pygame.draw.circle(self.superficie, VERDE_BORDE, (round(c.x), round(c.y)), round(r + 2))
        for c, r in locales:
            pygame.draw.circle(self.superficie, random.choice(VERDES), (round(c.x), round(c.y)), round(r))
        for c, r in locales:
            for _ in range(2):
                ang = random.uniform(0, math.tau)
                d = random.uniform(0, r * 0.5)
                hoja = (round(c.x + math.cos(ang) * d), round(c.y + math.sin(ang) * d))
                pygame.draw.circle(self.superficie, random.choice(VERDES), hoja, max(2, round(r * 0.3)))

        # Versión semitransparente (la que se ve cuando estás metido dentro)
        self.superficie_interior = self.superficie.copy()
        self.superficie_interior.fill((255, 255, 255, ALPHA_INTERIOR), special_flags=pygame.BLEND_RGBA_MULT)

    def _generar_orbes(self):
        """Genera los orbes según la fase: brote=0, joven=1, maduro=1-5 aleatorios."""
        self.orbes = []
        if self.fase == "brote":
            cantidad = 0
        elif self.fase == "joven":
            cantidad = 1
        else:
            cantidad = random.randint(ORBES_MIN, ORBES_MAX)
        for _ in range(cantidad):
            c, r = random.choice(self.circulos)
            ang = random.uniform(0, math.tau)
            d = random.uniform(0, max(0.0, r - RADIO_ORBE - 2))
            self.orbes.append(pygame.Vector2(c.x + math.cos(ang) * d, c.y + math.sin(ang) * d))

    def actualizar_crecimiento(self, dt):
        """Frutal reaparecido: brote (20px, 0 fruta) -> joven (tamaño final, 1 fruta) -> maduro (frutas aleatorias)."""
        if self.tipo != TIPO_FRUTAL or self.fase == "maduro":
            return
        self.tiempo_fase += dt
        if self.tiempo_fase < TIEMPO_CRECIMIENTO_FRUTAL:
            return
        self.tiempo_fase = 0.0
        if self.fase == "brote":
            self.fase = "joven"
            self.radio = self.radio_final
            self._reconstruir()
            self._generar_orbes()
        elif self.fase == "joven":
            self.fase = "maduro"
            self._generar_orbes()

    def contiene(self, punto):
        """True si el punto (centro del personaje) está dentro de la forma del arbusto."""
        return any((punto - c).length() <= r for c, r in self.circulos)

    @property
    def grande(self):
        """Arbusto grande: solo lo destruye Cortar a nivel maximo."""
        return self.radio * 2 > DIAMETRO_ARBUSTO_GRANDE

    def puede_entrar(self, personaje):
        """Solo entran los personajes cuyo diámetro cabe en el del arbusto."""
        return personaje.radio <= self.radio

    def dibujar(self, pantalla, desplazamiento, interior=False):
        sup = self.superficie_interior if interior else self.superficie
        pantalla.blit(sup, (self.rect.x - desplazamiento[0], self.rect.y - desplazamiento[1]))

    def dibujar_orbes(self, pantalla, desplazamiento):
        ox, oy = desplazamiento
        for o in self.orbes:
            p = (round(o.x - ox), round(o.y - oy))
            pygame.draw.circle(pantalla, COLOR_ORBE, p, RADIO_ORBE)
            pygame.draw.circle(pantalla, COLOR_ORBE_BRILLO, (p[0] - 1, p[1] - 1), max(1, RADIO_ORBE // 2))


# -----------------------------
# ARBOLES Y BIOMAS (bosques)
# -----------------------------
CELDA_REJILLA = 256            # Tamanio de celda para la rejilla espacial de colocacion

NUM_BOSQUES_MIN = 10
NUM_BOSQUES_MAX = 16
BOSQUE_RADIO_MIN = 500
BOSQUE_RADIO_MAX = 1600
PROB_ARBUSTO_EN_BOSQUE = 0.70  # sesgo de los arbustos hacia los bosques

TIPOS_ARBOL = ["frondoso", "pino", "seco"]
PESOS_ARBOL = [0.55, 0.35, 0.10]
ARBOL_ESCALA_MIN = 1.0
ARBOL_ESCALA_MAX = 1.9
ARBOL_COPA_BASE = 34           # radio de la copa a escala 1 (solo visual)
ARBOL_TRONCO_BASE = 7          # radio del tronco (solido) a escala 1
ARBOL_ESPACIADO = 110          # separacion objetivo entre arboles de un bosque
DENSIDAD_BOSQUE = 0.22         # fraccion del area del bosque que se llena de arboles
ARBOL_SOLITARIO_CADA = 500     # 1 arbol solitario por cada N px de radio del mundo

COLOR_SOMBRA_ARBOL = (20, 23, 29)
COLOR_TRONCO = (92, 66, 44)
COLOR_TRONCO_BORDE = (60, 42, 28)
COLOR_RAMA_SECA = (74, 56, 40)
COLOR_FRONDOSO = (64, 132, 62)
COLOR_FRONDOSO_BORDE = (30, 70, 36)
COLOR_PINO = (38, 92, 56)
COLOR_PINO_BORDE = (22, 58, 38)


class RejillaEspacial:
    """Rejilla espacial (hash por celdas) para consultar solapamientos de cajas en O(1)
    amortizado, en vez de recorrer todas las plantas (evita que generar miles sea lento)."""
    def __init__(self, celda):
        self.celda = celda
        self.celdas = {}

    def _rango(self, caja):
        return (int(caja.left // self.celda), int(caja.top // self.celda),
                int(caja.right // self.celda), int(caja.bottom // self.celda))

    def agregar(self, caja):
        x0, y0, x1, y1 = self._rango(caja)
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                self.celdas.setdefault((cx, cy), []).append(caja)

    def hay_colision(self, caja):
        x0, y0, x1, y1 = self._rango(caja)
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for r in self.celdas.get((cx, cy), ()):
                    if caja.colliderect(r):
                        return True
        return False

    def quitar(self, caja):
        x0, y0, x1, y1 = self._rango(caja)
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                lst = self.celdas.get((cx, cy))
                if lst and caja in lst:
                    lst.remove(caja)


CELDA_DIBUJO = 512             # Celda para el indice de dibujo de pasto/flores (culling por vista)


class IndiceDibujo:
    """Indexa objetos con atributo .rect por celda para dibujar solo los visibles sin recorrer
    toda la lista cada frame. Pensado para listas grandes y ESTATICAS (pasto, flores)."""
    def __init__(self, celda, objetos):
        self.celda = celda
        self.celdas = {}
        for o in objetos:
            r = o.rect
            x0, y0 = int(r.left // celda), int(r.top // celda)
            x1, y1 = int(r.right // celda), int(r.bottom // celda)
            for cx in range(x0, x1 + 1):
                for cy in range(y0, y1 + 1):
                    self.celdas.setdefault((cx, cy), []).append(o)

    def visibles(self, vista):
        """Objetos cuyas cajas tocan `vista`, sin duplicados (un objeto puede ocupar varias celdas)."""
        c = self.celda
        x0, y0 = int(vista.left // c), int(vista.top // c)
        x1, y1 = int(vista.right // c), int(vista.bottom // c)
        vistos = set()
        res = []
        for cx in range(x0, x1 + 1):
            for cy in range(y0, y1 + 1):
                for o in self.celdas.get((cx, cy), ()):
                    oid = id(o)
                    if oid not in vistos:
                        vistos.add(oid)
                        if o.rect.colliderect(vista):
                            res.append(o)
        return res


class Arbol:
    """Arbol del mundo: tronco solido (circulo) + copa visual mas grande dibujada encima.
    Tipos: 'frondoso' (copa redonda verde), 'pino' (mas oscuro y punteado), 'seco' (sin copa,
    ramas marrones). Se dibuja de forma procedural (sin pre-render) para no gastar memoria."""
    def __init__(self, x, y, tipo, escala, radio_tronco, radio_copa):
        self.centro = pygame.Vector2(x, y)
        self.tipo = tipo
        self.escala = escala
        self.radio_tronco = radio_tronco
        self.radio_copa = radio_copa
        ext = radio_copa + 6
        self.rect = pygame.Rect(round(x - ext), round(y - ext), ext * 2, ext * 2)
        # Lobulos de copa (estables, precomputados) para frondoso/pino
        self.lobulos = []
        if tipo != "seco":
            n = random.randint(4, 7)
            for i in range(n):
                a = (i / n) * math.tau + random.uniform(-0.3, 0.3)
                rl = radio_copa * random.uniform(0.45, 0.62)
                dd = (radio_copa - rl) * random.uniform(0.5, 0.9)
                self.lobulos.append((math.cos(a) * dd, math.sin(a) * dd, rl))
        # Ramas para el arbol seco
        self.ramas = []
        if tipo == "seco":
            for _ in range(random.randint(4, 6)):
                a = -math.pi / 2 + random.uniform(-1.2, 1.2)
                ln = radio_copa * random.uniform(0.6, 1.0)
                self.ramas.append((a, ln))

    def dibujar_base(self, pantalla, desplazamiento):
        """Sombra + tronco (y ramas del seco): va DEBAJO de las entidades."""
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        rc, rt = self.radio_copa, self.radio_tronco
        pygame.draw.circle(pantalla, COLOR_SOMBRA_ARBOL, (px + 3, py + 4), rc)
        pygame.draw.circle(pantalla, COLOR_TRONCO, (px, py), rt)
        if self.tipo == "seco":
            pygame.draw.circle(pantalla, COLOR_TRONCO_BORDE, (px, py), rt, 1)
            for a, ln in self.ramas:
                ex = px + int(math.cos(a) * ln)
                ey = py + int(math.sin(a) * ln)
                pygame.draw.line(pantalla, COLOR_RAMA_SECA, (px, py), (ex, ey), max(1, rt // 3))

    def _pintar_copa(self, target, cx, cy):
        rc = self.radio_copa
        base, borde = (COLOR_PINO, COLOR_PINO_BORDE) if self.tipo == "pino" else (COLOR_FRONDOSO, COLOR_FRONDOSO_BORDE)
        pygame.draw.circle(target, borde, (cx, cy), rc + 2)
        for ox, oy, rl in self.lobulos:
            pygame.draw.circle(target, base, (cx + int(ox), cy + int(oy)), int(rl))
        pygame.draw.circle(target, base, (cx, cy), int(rc * 0.7))
        if self.tipo == "pino":
            for i in range(6):
                a = math.tau * i / 6
                pygame.draw.line(target, borde, (cx, cy), (cx + int(math.cos(a) * rc), cy + int(math.sin(a) * rc)), 1)

    def dibujar_copa(self, pantalla, desplazamiento, desvanecer=False):
        """Copa (frondoso/pino) ENCIMA de las entidades (profundidad). Si el jugador esta
        debajo, se dibuja semitransparente para no ocultarlo (bajo un arbol no te escondes)."""
        if self.tipo == "seco":
            return
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        if not desvanecer:
            self._pintar_copa(pantalla, px, py)
            return
        ext = self.radio_copa + 4
        capa = pygame.Surface((ext * 2, ext * 2), pygame.SRCALPHA)
        self._pintar_copa(capa, ext, ext)
        capa.fill((255, 255, 255, ALFA_COPA_DESVANECIDA), special_flags=pygame.BLEND_RGBA_MULT)
        pantalla.blit(capa, (px - ext, py - ext))

    def dibujar(self, pantalla, desplazamiento):
        self.dibujar_base(pantalla, desplazamiento)
        self.dibujar_copa(pantalla, desplazamiento)


# -----------------------------
# PASTO (hierba) Y FLORES — cobertura de suelo decorativa (bajo las entidades)
# -----------------------------
ALFA_COPA_DESVANECIDA = 95     # Alfa de la copa de un arbol con una entidad debajo

NUM_PRADERAS_MIN = 8
NUM_PRADERAS_MAX = 14
PRADERA_RADIO_MIN = 600
PRADERA_RADIO_MAX = 1800

PASTO_ESPACIADO = 90
DENSIDAD_PRADERA_PASTO = 0.25
DENSIDAD_BOSQUE_PASTO = 0.10      # sotobosque mas ralo
PASTO_ALTURA_MIN = 12             # altura media (no tapa al personaje: va bajo las entidades)
PASTO_ALTURA_MAX = 22
PASTO_ESCALA_MIN = 0.8
PASTO_ESCALA_MAX = 1.4
# Bioma de pasto alto: zonas visuales de hierba mas alta (bajo las entidades, no tapan al jugador)
NUM_PASTIZALES_MIN = 8
NUM_PASTIZALES_MAX = 12
PASTIZAL_RADIO_MIN = 300
PASTIZAL_RADIO_MAX = 700
PASTO_ALTO_ESCALA_MIN = 1.8
PASTO_ALTO_ESCALA_MAX = 2.8
DENSIDAD_PASTIZAL = 0.45
COLORES_PASTO = [(70, 138, 66), (86, 156, 74), (58, 120, 56)]

FLORES_POR_PRADERA = (20, 60)
COLORES_FLOR = [(235, 92, 104), (240, 196, 72), (150, 120, 230), (240, 240, 245), (240, 140, 190)]
COLOR_TALLO_FLOR = (70, 130, 66)
COLOR_CENTRO_FLOR = (250, 220, 120)

# Pasto y flores no crecen en los lagos (ahi solo hay flora acuatica). El margen cubre el barro
# de la orilla y la altura de la hierba, que se dibuja hacia arriba desde su base.
MARGEN_COBERTURA_AGUA = 40


class Pasto:
    """Mechon de hierba de altura media. Decorativo: se dibuja BAJO las entidades (nunca tapa
    al personaje) y no tiene colision."""
    def __init__(self, x, y, escala):
        self.centro = pygame.Vector2(x, y)
        alto = random.randint(PASTO_ALTURA_MIN, PASTO_ALTURA_MAX) * escala
        self.briznas = []
        for _ in range(random.randint(3, 5)):
            ox = random.uniform(-5, 5) * escala
            h = alto * random.uniform(0.7, 1.0)
            curva = random.uniform(-0.3, 0.3) * h
            self.briznas.append((ox, h, curva, random.choice(COLORES_PASTO)))
        ext = int(alto) + 6
        self.rect = pygame.Rect(round(x - ext), round(y - ext), ext * 2, ext * 2)

    def dibujar(self, pantalla, desplazamiento):
        bx = round(self.centro.x - desplazamiento[0])
        by = round(self.centro.y - desplazamiento[1])
        for ox, h, curva, col in self.briznas:
            x0 = bx + int(ox)
            pygame.draw.line(pantalla, col, (x0, by), (x0 + int(curva), by - int(h)), 2)


class Flor:
    """Florecita decorativa (tallo + petalos). Bajo las entidades, sin colision."""
    def __init__(self, x, y, color):
        self.centro = pygame.Vector2(x, y)
        self.color = color
        self.alto = random.randint(8, 14)
        self.rect = pygame.Rect(round(x - 6), round(y - self.alto - 6), 12, self.alto + 12)

    def dibujar(self, pantalla, desplazamiento):
        bx = round(self.centro.x - desplazamiento[0])
        by = round(self.centro.y - desplazamiento[1])
        ty = by - self.alto
        pygame.draw.line(pantalla, COLOR_TALLO_FLOR, (bx, by), (bx, ty), 1)
        for i in range(5):
            a = math.tau * i / 5
            pygame.draw.circle(pantalla, self.color, (bx + int(math.cos(a) * 2), ty + int(math.sin(a) * 2)), 2)
        pygame.draw.circle(pantalla, COLOR_CENTRO_FLOR, (bx, ty), 1)


# -----------------------------
# SISTEMA DE VEGETACIÓN
# -----------------------------
class SistemaVegetacion:
    def __init__(self, centro_mundo, radio_mundo, zona_segura, zonas_ocupadas=()):
        self.centro_mundo = pygame.Vector2(centro_mundo)
        self.radio_mundo = radio_mundo
        self.zona_segura = zona_segura
        zonas_ocupadas = list(zonas_ocupadas)   # charcos u otros objetos con .rect
        # Lagos (objetos con .circulos): el pasto y las flores no crecen dentro
        self.charcos = [z for z in zonas_ocupadas if hasattr(z, "circulos")]
        self.arbustos = []
        self.arboles = []
        self.bosques = []               # (centro, radio) de cada bosque/bioma
        self.praderas = []              # (centro, radio) de cada pradera (pasto/flores)
        self.pastizales = []            # (centro, radio) de cada zona de pasto alto (visual)
        self.pasto = []
        self.flores = []
        self.reapariciones_frutal = []  # temporizadores (segundos restantes)
        # Rejilla de espacio ocupado: la consultan la generacion y la reaparicion de frutales
        self.rejilla = RejillaEspacial(CELDA_REJILLA)
        for z in zonas_ocupadas:
            self.rejilla.agregar(z.rect)
        self._idx_pasto = None      # indices de dibujo (se construyen perezosamente)
        self._idx_flores = None

        # Biomas: bosques (arboles) y praderas (pasto/flores), luego arbustos
        self._generar_bosques()
        self._generar_praderas()
        self._generar_pastizales()
        self._generar_arboles()
        self._generar_pasto()
        self._generar_pasto_alto()
        self._generar_flores()

        for tipo, (minimo, maximo) in CANTIDADES.items():
            for _ in range(random.randint(minimo, maximo)):
                arbusto = self._crear_en_lugar_libre(tipo)
                if arbusto:
                    self.arbustos.append(arbusto)

        if random.random() < PROB_MATORRAL:
            for _ in range(random.randint(1, 3)):
                self._crear_matorral()

    def registrar_obstaculos(self, objetos):
        """Añade a la rejilla obstáculos generados después (ej. rocas) para que los frutales
        que reaparecen no caigan encima, y quita el pasto/flores que quedaron debajo."""
        objetos = list(objetos)
        tapados = RejillaEspacial(CELDA_REJILLA)
        for o in objetos:
            self.rejilla.agregar(o.rect)
            tapados.agregar(o.rect)
        self.pasto = [g for g in self.pasto if not tapados.hay_colision(g.rect)]
        self.flores = [f for f in self.flores if not tapados.hay_colision(f.rect)]
        self._idx_pasto = None      # las listas cambiaron: forzar reconstruccion del indice
        self._idx_flores = None

    def liberar_obstaculos(self, objetos):
        """Libera en la rejilla el espacio de obstaculos destruidos (rocas, arbustos o arboles
        cortados, frutales consumidos). Usa la caja reservada al crearlos si la tienen."""
        for o in objetos:
            self.rejilla.quitar(getattr(o, "caja_rejilla", o.rect))

    def _en_agua(self, x, y, margen):
        """True si el punto esta dentro de un lago o a menos de `margen` de su borde."""
        for charco in self.charcos:
            if not charco.rect.inflate(margen * 2, margen * 2).collidepoint(x, y):
                continue
            if any(math.hypot(x - c.x, y - c.y) <= r + margen for c, r in charco.circulos):
                return True
        return False

    def _crear_en_lugar_libre(self, tipo, evitar=None, intentos=400, fase="maduro"):
        minimo = DIAMETRO_MIN_FRUTAL if tipo == TIPO_FRUTAL else DIAMETRO_MIN
        for _ in range(intentos):
            radio_final = random.randint(minimo, DIAMETRO_MAX) // 2
            # Sesgo hacia los bosques (vegetacion agrupada = mas natural)
            if self.bosques and evitar is None and random.random() < PROB_ARBUSTO_EN_BOSQUE:
                x, y = self._punto_en_bosque(random.choice(self.bosques))
            else:
                x, y = self._punto_en_mundo(radio_final)
            if not self._dentro_del_mapa(x, y, radio_final):
                continue
            if evitar is not None and (pygame.Vector2(x, y) - evitar).length() < 300:
                continue
            # La caja reserva el espacio del tamaño FINAL (aunque empiece como brote)
            caja = pygame.Rect(0, 0, radio_final * 2 + 30, radio_final * 2 + 30)
            caja.center = (round(x), round(y))
            if self.rejilla.hay_colision(caja):
                continue
            self.rejilla.agregar(caja)
            if fase == "brote":
                arbusto = Arbusto(x, y, DIAMETRO_BROTE // 2, tipo, fase="brote", radio_final=radio_final)
            else:
                arbusto = Arbusto(x, y, radio_final, tipo)
            arbusto.caja_rejilla = caja   # para liberar su espacio si se destruye o se consume
            return arbusto
        return None

    def _crear_matorral(self, intentos=300):
        """Matorral: conjunto denso de 5 a 8 arbustos de tipos y tamaños distintos, solapados sin huecos."""
        cantidad = random.randint(MATORRAL_MIN_ARBUSTOS, MATORRAL_MAX_ARBUSTOS)
        radio_cluster = random.randint(80, 160)
        for _ in range(intentos):
            ang = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * (self.radio_mundo - radio_cluster - 20)
            if dist - radio_cluster < self.zona_segura:
                continue
            cx = self.centro_mundo.x + math.cos(ang) * dist
            cy = self.centro_mundo.y + math.sin(ang) * dist

            caja = pygame.Rect(0, 0, radio_cluster * 2 + 40, radio_cluster * 2 + 40)
            caja.center = (round(cx), round(cy))
            if self.rejilla.hay_colision(caja):
                continue
            self.rejilla.agregar(caja)

            # Colocar los arbustos solapados para formar una masa densa sin huecos
            for i in range(cantidad):
                a = (i / cantidad) * math.tau + random.uniform(-0.4, 0.4)
                d = random.uniform(0, radio_cluster * 0.6)
                ax = cx + math.cos(a) * d
                ay = cy + math.sin(a) * d
                radio_arb = random.randint(DIAMETRO_MIN, DIAMETRO_MAX) // 2
                tipo = random.choice([TIPO_ESCONDITE, TIPO_VENENOSO, TIPO_FRUTAL])
                self.arbustos.append(Arbusto(ax, ay, radio_arb, tipo))
            return True
        return False

    # ---- Biomas (bosques) y arboles --------------------------------------
    def _generar_bosques(self):
        n = random.randint(NUM_BOSQUES_MIN, NUM_BOSQUES_MAX)
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * (self.radio_mundo * 0.9)
            cx = self.centro_mundo.x + math.cos(ang) * dist
            cy = self.centro_mundo.y + math.sin(ang) * dist
            radio = random.randint(BOSQUE_RADIO_MIN, BOSQUE_RADIO_MAX)
            self.bosques.append((pygame.Vector2(cx, cy), radio))

    def _punto_en_mundo(self, margen):
        ang = random.uniform(0, math.tau)
        dist = math.sqrt(random.random()) * max(0.0, self.radio_mundo - margen - 20)
        return self.centro_mundo.x + math.cos(ang) * dist, self.centro_mundo.y + math.sin(ang) * dist

    def _punto_en_bosque(self, bosque):
        centro, radio = bosque
        ang = random.uniform(0, math.tau)
        dist = math.sqrt(random.random()) * radio
        return centro.x + math.cos(ang) * dist, centro.y + math.sin(ang) * dist

    def _dentro_del_mapa(self, x, y, margen):
        d = (pygame.Vector2(x, y) - self.centro_mundo).length()
        return d - margen >= self.zona_segura and d + margen <= self.radio_mundo - 20

    def _generar_arboles(self):
        # Arboles densos dentro de cada bosque + algunos solitarios por el mundo
        for centro, radio in self.bosques:
            n = int(math.pi * radio * radio / (ARBOL_ESPACIADO ** 2) * DENSIDAD_BOSQUE)
            for _ in range(n):
                self._crear_arbol(zona=(centro, radio))
        for _ in range(int(self.radio_mundo / ARBOL_SOLITARIO_CADA)):
            self._crear_arbol()

    def _crear_arbol(self, zona=None, intentos=14):
        for _ in range(intentos):
            tipo = random.choices(TIPOS_ARBOL, weights=PESOS_ARBOL)[0]
            escala = random.uniform(ARBOL_ESCALA_MIN, ARBOL_ESCALA_MAX)
            radio_copa = round(ARBOL_COPA_BASE * escala)
            radio_tronco = round(ARBOL_TRONCO_BASE * escala)
            if zona is not None:
                x, y = self._punto_en_bosque(zona)
            else:
                x, y = self._punto_en_mundo(radio_copa)
            if not self._dentro_del_mapa(x, y, radio_copa):
                continue
            # Solo reservamos el TRONCO (solido): las copas pueden solaparse (bosque tupido)
            caja = pygame.Rect(0, 0, radio_tronco * 2 + 16, radio_tronco * 2 + 16)
            caja.center = (round(x), round(y))
            if self.rejilla.hay_colision(caja):
                continue
            self.rejilla.agregar(caja)
            arbol = Arbol(x, y, tipo, escala, radio_tronco, radio_copa)
            arbol.caja_rejilla = caja     # para liberar su espacio si Cortar lo rompe
            self.arboles.append(arbol)
            return True
        return False

    def dibujar_arboles_base(self, pantalla, vista, desplazamiento):
        for a in self.arboles:
            if a.rect.colliderect(vista):
                a.dibujar_base(pantalla, desplazamiento)

    def dibujar_arboles_copas(self, pantalla, vista, desplazamiento, entidades=()):
        """Copas encima de todo. Si alguna entidad (jugador, maniqui, invocaciones) esta
        debajo, aunque sea en parte, la copa se ve semitransparente para no ocultarla."""
        for a in self.arboles:
            if a.rect.colliderect(vista):
                desv = any((e.posicion - a.centro).length() <= a.radio_copa + e.radio for e in entidades)
                a.dibujar_copa(pantalla, desplazamiento, desv)

    # ---- Praderas: pasto y flores (cobertura decorativa) -----------------
    def _generar_praderas(self):
        n = random.randint(NUM_PRADERAS_MIN, NUM_PRADERAS_MAX)
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * (self.radio_mundo * 0.92)
            cx = self.centro_mundo.x + math.cos(ang) * dist
            cy = self.centro_mundo.y + math.sin(ang) * dist
            radio = random.randint(PRADERA_RADIO_MIN, PRADERA_RADIO_MAX)
            self.praderas.append((pygame.Vector2(cx, cy), radio))

    def _soltar_pasto(self, zona):
        x, y = self._punto_en_bosque(zona)   # punto aleatorio dentro de la zona
        if self._dentro_del_mapa(x, y, 4) and not self._en_agua(x, y, MARGEN_COBERTURA_AGUA):
            self.pasto.append(Pasto(x, y, random.uniform(PASTO_ESCALA_MIN, PASTO_ESCALA_MAX)))

    def _generar_pasto(self):
        for centro, radio in self.praderas:       # praderas: hierba densa
            n = int(math.pi * radio * radio / (PASTO_ESPACIADO ** 2) * DENSIDAD_PRADERA_PASTO)
            for _ in range(n):
                self._soltar_pasto((centro, radio))
        for centro, radio in self.bosques:         # bosques: sotobosque ralo
            n = int(math.pi * radio * radio / (PASTO_ESPACIADO ** 2) * DENSIDAD_BOSQUE_PASTO)
            for _ in range(n):
                self._soltar_pasto((centro, radio))

    def _generar_pastizales(self):
        n = random.randint(NUM_PASTIZALES_MIN, NUM_PASTIZALES_MAX)
        for _ in range(n):
            ang = random.uniform(0, math.tau)
            dist = math.sqrt(random.random()) * (self.radio_mundo * 0.9)
            cx = self.centro_mundo.x + math.cos(ang) * dist
            cy = self.centro_mundo.y + math.sin(ang) * dist
            radio = random.randint(PASTIZAL_RADIO_MIN, PASTIZAL_RADIO_MAX)
            self.pastizales.append((pygame.Vector2(cx, cy), radio))

    def _generar_pasto_alto(self):
        for centro, radio in self.pastizales:
            n = int(math.pi * radio * radio / (PASTO_ESPACIADO ** 2) * DENSIDAD_PASTIZAL)
            for _ in range(n):
                x, y = self._punto_en_bosque((centro, radio))
                if self._dentro_del_mapa(x, y, 4) and not self._en_agua(x, y, MARGEN_COBERTURA_AGUA):
                    self.pasto.append(Pasto(x, y, random.uniform(PASTO_ALTO_ESCALA_MIN, PASTO_ALTO_ESCALA_MAX)))

    def _generar_flores(self):
        for centro, radio in self.praderas:
            for _ in range(random.randint(*FLORES_POR_PRADERA)):
                x, y = self._punto_en_bosque((centro, radio))
                if self._dentro_del_mapa(x, y, 4) and not self._en_agua(x, y, MARGEN_COBERTURA_AGUA):
                    self.flores.append(Flor(x, y, random.choice(COLORES_FLOR)))

    def dibujar_cobertura(self, pantalla, vista, desplazamiento):
        """Pasto y flores: cobertura de suelo bajo las entidades (nunca tapa al personaje).
        Usa un indice espacial para dibujar solo lo visible sin recorrer toda la lista."""
        if self._idx_pasto is None:
            self._idx_pasto = IndiceDibujo(CELDA_DIBUJO, self.pasto)
            self._idx_flores = IndiceDibujo(CELDA_DIBUJO, self.flores)
        for g in self._idx_pasto.visibles(vista):
            g.dibujar(pantalla, desplazamiento)
        for f in self._idx_flores.visibles(vista):
            f.dibujar(pantalla, desplazamiento)

    def obstaculos_para(self, personaje, con_troncos=True):
        """Solidos para el personaje: arbustos en los que no cabe + troncos de arboles (sin
        troncos con el Cuerpo de niebla de Espectro)."""
        solidos = [(a.centro, a.radio) for a in self.arbustos if not a.puede_entrar(personaje)]
        if con_troncos:
            solidos.extend((t.centro, t.radio_tronco) for t in self.arboles)
        return solidos

    def actualizar(self, dt, jugador):
        # ¿En qué arbusto está metido?
        jugador.arbusto_actual = None
        for a in self.arbustos:
            if a.puede_entrar(jugador) and a.contiene(jugador.posicion):
                jugador.arbusto_actual = a
                break
        jugador.oculto = jugador.arbusto_actual is not None
        arbusto = jugador.arbusto_actual

        # Hierba venenosa: 1 de daño cada 2 segundos
        if arbusto and arbusto.tipo == TIPO_VENENOSO:
            jugador.tiempo_veneno += dt
            while jugador.tiempo_veneno >= INTERVALO_VENENO:
                jugador.tiempo_veneno -= INTERVALO_VENENO
                jugador.vida = max(0, jugador.vida - DANO_VENENO)
        else:
            jugador.tiempo_veneno = 0.0

        # Arbusto frutal: consumir orbes al tocarlos
        if arbusto and arbusto.tipo == TIPO_FRUTAL:
            restantes = []
            for o in arbusto.orbes:
                if (o - jugador.posicion).length() <= jugador.radio + RADIO_ORBE:
                    jugador.curar(CURACION_ORBE)
                else:
                    restantes.append(o)
            arbusto.orbes = restantes

            # Sin orbes (solo si ya estaba maduro): desaparece y se programa uno nuevo en 1 minuto
            if not arbusto.orbes and arbusto.fase == "maduro":
                self.arbustos.remove(arbusto)
                self.liberar_obstaculos([arbusto])
                self.reapariciones_frutal.append(TIEMPO_REAPARICION_FRUTAL)
                jugador.arbusto_actual = None
                jugador.oculto = False

        # Crecimiento de los frutales reaparecidos (brote -> joven -> maduro)
        for a in self.arbustos:
            a.actualizar_crecimiento(dt)

        # Reaparición de frutales (reaparecen como brote de 20px)
        pendientes = []
        for t in self.reapariciones_frutal:
            t -= dt
            if t <= 0:
                nuevo = self._crear_en_lugar_libre(TIPO_FRUTAL, evitar=jugador.posicion, fase="brote")
                if nuevo:
                    self.arbustos.append(nuevo)
                else:
                    pendientes.append(1.0)  # Reintentar en 1 segundo si no hubo espacio
            else:
                pendientes.append(t)
        self.reapariciones_frutal = pendientes

    def dibujar(self, pantalla, vista, desplazamiento, jugador):
        for a in self.arbustos:
            if a.rect.colliderect(vista):
                a.dibujar(pantalla, desplazamiento, interior=(a is jugador.arbusto_actual))

    def dibujar_interior(self, pantalla, desplazamiento, jugador):
        """Lo que solo ve el personaje desde dentro: los orbes de su arbusto."""
        if jugador.arbusto_actual:
            jugador.arbusto_actual.dibujar_orbes(pantalla, desplazamiento)

    def dibujar_hitboxes(self, pantalla, vista, desplazamiento, fuente):
        ox, oy = desplazamiento
        for t in self.arboles:
            if t.rect.colliderect(vista):
                pygame.draw.circle(pantalla, (150, 110, 70), (round(t.centro.x - ox), round(t.centro.y - oy)), t.radio_tronco, 1)
                pygame.draw.circle(pantalla, (90, 150, 90), (round(t.centro.x - ox), round(t.centro.y - oy)), t.radio_copa, 1)
        for a in self.arbustos:
            if not a.rect.colliderect(vista):
                continue
            color = COLOR_DEBUG[a.tipo]
            for c, r in a.circulos:
                pygame.draw.circle(pantalla, color, (round(c.x - ox), round(c.y - oy)), round(r), 1)
            etiqueta = fuente.render(f"{a.tipo} Ø{a.radio * 2}", True, color)
            pantalla.blit(etiqueta, (round(a.centro.x - ox - etiqueta.get_width() / 2), round(a.centro.y - oy - a.radio - 14)))
            for o in a.orbes:
                pygame.draw.circle(pantalla, COLOR_ORBE, (round(o.x - ox), round(o.y - oy)), RADIO_ORBE, 1)
