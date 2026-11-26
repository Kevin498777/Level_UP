"""Vendedores ambulantes de anillos (NPC).

- En el mapa hay VENDEDORES a la vez. Cada uno lleva ANILLOS_POR_VENDEDOR anillos distintos
  (dos vendedores si pueden repetir anillo): primero se sortea la rareza (PROB_RAREZA_TIENDA) y
  luego un anillo de esa rareza que el jugador aun pueda subir. Precio segun la rareza.
- Se compra con [E] a RANGO_TIENDA px: un anillo nuevo o +1 nivel (igual que el Gacha).
- Pasea despacio por el mapa. Si recibe dano (de ti o de la fauna) se vuelve invisible
  DURACION_PASO0 s y huye; al terminar se cura entero. Si muere, otro aparece a los
  REAPARICION s en un punto al azar con anillos nuevos. Si lo mata el jugador da XP y monedas.
- Sin nada que venderte camina hasta la casa del spawn, entra, y REAPARICION s despues sale
  otro en un punto al azar. Con todos tus anillos al maximo ya no abre tienda ni vuelve a casa:
  solo deambula (y se puede cazar).
"""
import math
import random
import pygame
import talismanes as TL

VENDEDORES = 3
ANILLOS_POR_VENDEDOR = 5
PRECIOS = {TL.COMUN: 100, TL.ESPECIAL: 200, TL.EPICO: 400, TL.LEGENDARIO: 1000}
PROB_RAREZA_TIENDA = {TL.COMUN: 0.50, TL.ESPECIAL: 0.30, TL.EPICO: 0.15, TL.LEGENDARIO: 0.05}
VIDA_VENDEDOR = 20
RADIO_VENDEDOR = 18
VELOCIDAD_PASEO = 45.0          # px/s
VELOCIDAD_HUIDA = 140.0
DURACION_PASO0 = 10.0           # s invisible y huyendo tras recibir dano
REAPARICION = 300.0             # s tras morir o tras entrar en la casa
PAUSA_PASEO = (2.0, 5.0)        # s parado entre paseos
ALCANCE_PASEO = 700             # px como mucho hasta el siguiente punto de paseo
DISTANCIA_MIN_CENTRO = 1500     # aparece y pasea lejos del spawn
MARGEN_BORDE = 300              # ... y lejos del borde del mapa
RANGO_TIENDA = 80               # px para comerciar con [E]
LLEGADA_PUERTA = 24             # px: a esta distancia de la puerta entra en la casa
XP_VENDEDOR = 20
MONEDAS_VENDEDOR = 20

COLOR_CUERPO = (196, 160, 112)
COLOR_BORDE = (120, 92, 60)
COLOR_GORRO = (200, 50, 50)
COLOR_MOCHILA = (70, 140, 70)
COLOR_NOMBRE = (255, 225, 140)
COLOR_BRUJULA = (255, 210, 90)


def todos_al_maximo(jugador):
    """True si el jugador tiene todos los anillos al maximo (no hay nada que vender)."""
    return all(jugador.talismanes.anillos.get(a, 0) >= d["nivel_max"] for a, d in TL.ANILLOS.items())


def puede_subir(jugador, id_anillo):
    return jugador.talismanes.anillos.get(id_anillo, 0) < TL.ANILLOS[id_anillo]["nivel_max"]


def generar_stock(jugador, rng=random):
    """ANILLOS_POR_VENDEDOR anillos distintos: rareza al azar (entre las que aun tienen anillos
    disponibles) y un anillo de esa rareza que el jugador pueda subir (si no queda ninguno, de todos)."""
    candidatos = [a for a in TL.ANILLOS if puede_subir(jugador, a)] or list(TL.ANILLOS)
    stock = []
    while len(stock) < ANILLOS_POR_VENDEDOR:
        por_rareza = {r: [a for a in candidatos if TL.ANILLOS[a]["rareza"] == r and a not in stock]
                      for r in PROB_RAREZA_TIENDA}
        rarezas = [r for r, lista in por_rareza.items() if lista]
        if not rarezas:
            break
        rareza = rng.choices(rarezas, weights=[PROB_RAREZA_TIENDA[r] for r in rarezas])[0]
        stock.append(rng.choice(por_rareza[rareza]))
    return [{"anillo": a, "precio": PRECIOS[TL.ANILLOS[a]["rareza"]], "vendido": False} for a in stock]


class Vendedor:
    """Un vendedor (un hueco del mapa): pasea, vende, huye invisible, vuelve a casa o muere y
    reaparece (el mismo objeto se reinicia con anillos nuevos)."""
    herramienta = None
    escudo = 0.0
    escudo_magico = 0.0
    masa = 1.0
    es_vendedor = True

    def __init__(self, sistema, jugador, rng=random):
        self.sistema = sistema
        self.rng = rng
        self.radio = RADIO_VENDEDOR
        self.posicion = pygame.Vector2(0, 0)
        self.nacer(jugador)

    def nacer(self, jugador):
        self.posicion.update(self.sistema.punto_al_azar(self.rng))
        self.vida = self.vida_max = VIDA_VENDEDOR
        self.vivo = True
        self.estado = "paseo"              # paseo | huida | a_casa | en_casa | muerto
        self.destino = None
        self.t_pausa = self.rng.uniform(*PAUSA_PASEO)
        self.t_estado = 0.0
        self.invisible = False
        self.huida_dir = pygame.Vector2(1, 0)
        self.muerto_por_fauna = False
        self._golpe_de_fauna = False       # lo pone fauna.golpear_objetivo mientras dura su golpe
        self.stock = generar_stock(jugador, self.rng)
        self.angulo = 0.0

    # ---- Estado
    @property
    def presente(self):
        """En el mapa (no muerto ni dentro de la casa)."""
        return self.estado not in ("en_casa", "muerto")

    @property
    def apuntable(self):
        return self.presente and self.vivo and not self.invisible

    def tiene_venta(self, jugador):
        return any(not s["vendido"] and puede_subir(jugador, s["anillo"]) for s in self.stock)

    def puede_comerciar(self, jugador):
        return (self.apuntable and self.estado == "paseo" and not todos_al_maximo(jugador)
                and (self.posicion - jugador.posicion).length() <= RANGO_TIENDA + self.radio + jugador.radio)

    # ---- Combate
    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        """Sin escudos. Si sobrevive: Paso 0 (invisible DURACION_PASO0 s) y huye del golpe."""
        if not self.apuntable or cantidad <= 0:
            return 0.0
        self.vida = max(0.0, round(self.vida - cantidad, 2))
        if self.vida <= 0:
            self.vivo = False
            self.muerto_por_fauna = self._golpe_de_fauna
            self.estado = "muerto"
            self.t_estado = REAPARICION
            self.sistema.registrar_muerte(self)
            return cantidad
        if direccion_empuje is not None and pygame.Vector2(direccion_empuje).length_squared() > 0:
            self.huida_dir = pygame.Vector2(direccion_empuje).normalize()
        else:
            lejos = self.posicion - self.sistema.pos_jugador
            ang = self.rng.uniform(0, math.tau)
            self.huida_dir = lejos.normalize() if lejos.length_squared() > 0 else pygame.Vector2(math.cos(ang), math.sin(ang))
        self.invisible = True
        self.estado = "huida"
        self.t_estado = DURACION_PASO0
        return cantidad

    def comprar(self, indice, jugador):
        """Compra el anillo 'indice'. Devuelve (texto, es_error)."""
        if not (0 <= indice < len(self.stock)):
            return None
        item = self.stock[indice]
        nombre = TL.ANILLOS[item["anillo"]]["nombre"]
        if item["vendido"]:
            return ("Ya lo vendió", True)
        if not puede_subir(jugador, item["anillo"]):
            return (f"{nombre}: ya lo tienes al máximo", True)
        if jugador.monedas < item["precio"]:
            return (f"Te faltan {item['precio'] - jugador.monedas} monedas", True)
        jugador.monedas -= item["precio"]
        resultado = jugador.talismanes.agregar_anillo(item["anillo"])
        jugador.recalcular_talismanes()
        item["vendido"] = True
        nivel = jugador.talismanes.anillos[item["anillo"]]
        return (f"{nombre} {'conseguido' if resultado == 'nuevo' else 'mejorado'} (nv{nivel})", False)

    # ---- Movimiento
    def actualizar(self, dt, jugador):
        if self.estado in ("muerto", "en_casa"):
            self.t_estado -= dt
            if self.t_estado <= 0:
                self.nacer(jugador)
            return
        if self.estado == "huida":
            self.t_estado -= dt
            self._mover(self.posicion + self.huida_dir * 200, VELOCIDAD_HUIDA, dt)
            if self.t_estado <= 0:
                self.invisible = False
                self.vida = self.vida_max            # se cura al salir del Paso 0
                self.estado = "paseo"
                self.destino = None
            return
        if self.estado == "paseo" and not todos_al_maximo(jugador) and not self.tiene_venta(jugador):
            self.estado = "a_casa"                   # ya no tiene nada que venderte
        if self.estado == "a_casa":
            puerta = self.sistema.casa.puerta
            self._mover(puerta, VELOCIDAD_PASEO, dt)
            if (self.posicion - puerta).length() <= LLEGADA_PUERTA:
                self.estado = "en_casa"
                self.t_estado = REAPARICION
            return
        # Paseo: ir a un punto cercano, pararse un rato, otro punto
        if self.destino is None:
            self.t_pausa -= dt
            if self.t_pausa <= 0:
                self.destino = self.sistema.punto_al_azar(self.rng, cerca_de=self.posicion)
            return
        self._mover(self.destino, VELOCIDAD_PASEO, dt)
        if (self.posicion - self.destino).length() < 4:
            self.destino = None
            self.t_pausa = self.rng.uniform(*PAUSA_PASEO)

    def _mover(self, objetivo, velocidad, dt):
        hacia = pygame.Vector2(objetivo) - self.posicion
        if hacia.length_squared() == 0:
            return
        paso = min(hacia.length(), velocidad * dt)
        self.posicion += hacia.normalize() * paso
        self.angulo = math.degrees(math.atan2(hacia.x, -hacia.y))
        self.posicion.update(self.sistema.dentro_del_mapa(self.posicion))

    # ---- Dibujo
    def dibujar(self, pantalla, desplazamiento, fuente, jugador):
        """Bolita como el personaje con gorrito rojo y mochila verde (invisible: no se ve)."""
        if not self.presente or self.invisible:
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        r = self.radio
        rad = math.radians(self.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        derecha = pygame.Vector2(math.cos(rad), math.sin(rad))
        # Mochila detras
        m = pygame.Vector2(px, py) - frente * (r * 0.75)
        caja = pygame.Rect(0, 0, r, r)
        caja.center = (round(m.x), round(m.y))
        pygame.draw.rect(pantalla, COLOR_MOCHILA, caja, border_radius=4)
        pygame.draw.rect(pantalla, (40, 90, 40), caja, 2, border_radius=4)
        # Cuerpo
        pygame.draw.circle(pantalla, COLOR_CUERPO, (px, py), r)
        pygame.draw.circle(pantalla, COLOR_BORDE, (px, py), r, 2)
        # Ojos hacia donde camina
        for lado in (-1, 1):
            ojo = pygame.Vector2(px, py) + frente * (r * 0.45) + derecha * (lado * r * 0.32)
            pygame.draw.circle(pantalla, (30, 30, 30), (round(ojo.x), round(ojo.y)), 3)
        # Gorrito (triangulo con borla) encima
        base_y = py - r + 4
        pygame.draw.polygon(pantalla, COLOR_GORRO, [(px - r * 0.7, base_y), (px + r * 0.7, base_y), (px + 2, base_y - r * 0.9)])
        pygame.draw.circle(pantalla, (245, 245, 245), (px + 2, round(base_y - r * 0.9)), 3)
        # Nombre y aviso de tienda
        txt = fuente.render("Vendedor", True, COLOR_NOMBRE)
        pantalla.blit(txt, (px - txt.get_width() // 2, py - r - 30))
        if self.puede_comerciar(jugador):
            aviso = fuente.render("[E] Comerciar", True, (230, 230, 230))
            pantalla.blit(aviso, (px - aviso.get_width() // 2, py + r + 4))
        if self.vida < self.vida_max:
            w = 30
            pygame.draw.rect(pantalla, (60, 20, 20), (px - w // 2, py - r - 12, w, 4))
            pygame.draw.rect(pantalla, (220, 70, 70), (px - w // 2, py - r - 12, round(w * self.vida / self.vida_max), 4))


class SistemaVendedores:
    def __init__(self, centro_mundo, radio_mundo, casa, charcos, jugador, rng=random):
        self.centro = pygame.Vector2(centro_mundo)
        self.radio_mundo = radio_mundo
        self.casa = casa
        self.charcos = charcos
        self.pos_jugador = pygame.Vector2(jugador.posicion)
        self._xp = 0
        self._monedas = 0
        self.vendedores = [Vendedor(self, jugador, rng) for _ in range(VENDEDORES)]

    def punto_al_azar(self, rng, cerca_de=None):
        """Punto en tierra, lejos del spawn y del borde (cerca de 'cerca_de' si se da)."""
        for _ in range(60):
            if cerca_de is None:
                ang = rng.uniform(0, math.tau)
                dist = rng.uniform(DISTANCIA_MIN_CENTRO, self.radio_mundo - MARGEN_BORDE)
                p = self.centro + pygame.Vector2(math.cos(ang), math.sin(ang)) * dist
            else:
                p = cerca_de + pygame.Vector2(rng.uniform(-ALCANCE_PASEO, ALCANCE_PASEO),
                                              rng.uniform(-ALCANCE_PASEO, ALCANCE_PASEO))
            d = (p - self.centro).length()
            if (DISTANCIA_MIN_CENTRO <= d <= self.radio_mundo - MARGEN_BORDE
                    and not any(c.contiene(p) for c in self.charcos)):
                return p
        return pygame.Vector2(cerca_de) if cerca_de is not None else self.centro + pygame.Vector2(DISTANCIA_MIN_CENTRO, 0)

    def dentro_del_mapa(self, p):
        d = p - self.centro
        limite = self.radio_mundo - RADIO_VENDEDOR
        return self.centro + d.normalize() * limite if d.length() > limite else p

    def registrar_muerte(self, vendedor):
        if not vendedor.muerto_por_fauna:
            self._xp += XP_VENDEDOR
            self._monedas += MONEDAS_VENDEDOR

    def tomar_recompensa(self):
        """(XP, monedas) de los vendedores que mataste desde la ultima llamada."""
        r = (self._xp, self._monedas)
        self._xp = self._monedas = 0
        return r

    def actualizar(self, dt, jugador):
        self.pos_jugador = pygame.Vector2(jugador.posicion)
        for v in self.vendedores:
            v.actualizar(dt, jugador)

    def objetivos(self):
        """Vendedores que se pueden golpear (visibles y en el mapa): para tus ataques y la fauna."""
        return [v for v in self.vendedores if v.apuntable]

    def cercano(self, jugador):
        """Vendedor con el que se puede comerciar ahora mismo (o None)."""
        cand = [v for v in self.vendedores if v.puede_comerciar(jugador)]
        return min(cand, key=lambda v: (v.posicion - jugador.posicion).length_squared(), default=None)

    def alguno_cerca(self, jugador):
        """True si hay un vendedor visible al alcance de [E] (aunque no pueda venderte nada)."""
        return any(v.apuntable and (v.posicion - jugador.posicion).length() <= RANGO_TIENDA + v.radio + jugador.radio
                   for v in self.vendedores)

    def brujula(self):
        return [("V", COLOR_BRUJULA, pygame.Vector2(v.posicion)) for v in self.vendedores if v.apuntable]

    def dibujar(self, pantalla, vista, desplazamiento, fuente, jugador):
        zona = vista.inflate(80, 80)
        for v in self.vendedores:
            if zona.collidepoint(v.posicion.x, v.posicion.y):
                v.dibujar(pantalla, desplazamiento, fuente, jugador)


# ------------------------------------------------------------------ Ventana de la tienda
ANCHO_TIENDA = 640
ALTO_TIENDA = 300
COLOR_FONDO_TIENDA = (18, 21, 29)
COLOR_TARJETA = (27, 31, 42)
COLOR_TARJETA_HOVER = (34, 40, 55)


def rect_tienda(area):
    r = pygame.Rect(0, 0, min(ANCHO_TIENDA, area.width - 40), min(ALTO_TIENDA, area.height - 40))
    r.center = area.center
    return r


def dibujar_tienda(pantalla, area, vendedor, jugador, fuentes, tiempo, mensaje=None):
    """Ventana de compra (no pausa). Devuelve botones {"__tienda__N", "__cerrar_tienda__",
    "__tienda_fondo__": Rect}."""
    raton = pygame.mouse.get_pos()
    botones = {}
    caja = rect_tienda(area)
    pygame.draw.rect(pantalla, COLOR_FONDO_TIENDA, caja, border_radius=12)
    pygame.draw.rect(pantalla, (150, 120, 60), caja, 2, border_radius=12)
    f_tit, f_nom, f_txt = fuentes["hab_contador"], fuentes["hab_nom"], fuentes["hab_mini"]
    pantalla.blit(f_tit.render("VENDEDOR AMBULANTE", True, (255, 215, 0)), (caja.x + 18, caja.y + 14))
    mon = f_nom.render(f"Monedas: {jugador.monedas}", True, (245, 200, 70))
    pantalla.blit(mon, (caja.right - mon.get_width() - 56, caja.y + 20))
    x_cerrar = pygame.Rect(caja.right - 40, caja.y + 14, 26, 26)
    pygame.draw.rect(pantalla, (90, 40, 40) if x_cerrar.collidepoint(raton) else (60, 30, 30), x_cerrar, border_radius=6)
    xt = f_nom.render("X", True, (255, 255, 255))
    pantalla.blit(xt, xt.get_rect(center=x_cerrar.center))
    botones["__cerrar_tienda__"] = x_cerrar

    n = max(1, len(vendedor.stock))
    margen = 14
    ancho = (caja.width - margen * (n + 1)) // n
    y0 = caja.y + 60
    for i, item in enumerate(vendedor.stock):
        datos = TL.ANILLOS[item["anillo"]]
        tarjeta = pygame.Rect(caja.x + margen + i * (ancho + margen), y0, ancho, caja.height - 110)
        nivel = jugador.talismanes.anillos.get(item["anillo"], 0)
        al_max = nivel >= datos["nivel_max"]
        bloqueado = item["vendido"] or al_max
        hover = tarjeta.collidepoint(raton) and not bloqueado
        pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER if hover else COLOR_TARJETA, tarjeta, border_radius=8)
        pygame.draw.rect(pantalla, TL.COLOR_RAREZA[datos["rareza"]], tarjeta, 2, border_radius=8)
        if not item["vendido"]:
            TL.dibujar_anillo(pantalla, (tarjeta.centerx, tarjeta.y + 40), 20, item["anillo"], tiempo)
        lineas = [(datos["nombre"].replace("Anillo ", ""), (230, 235, 245)),
                  (TL.NOMBRE_RAREZA[datos["rareza"]], TL.COLOR_RAREZA[datos["rareza"]]),
                  (f"Tienes nv{nivel}/{datos['nivel_max']}", (150, 160, 182))]
        y = tarjeta.y + 72
        for texto, color in lineas:
            sup = f_txt.render(texto, True, color)
            if sup.get_width() > tarjeta.width - 8:
                sup = pygame.transform.smoothscale(sup, (tarjeta.width - 8, sup.get_height()))
            pantalla.blit(sup, (tarjeta.centerx - sup.get_width() // 2, y))
            y += 18
        if item["vendido"]:
            estado, color = "VENDIDO", (150, 150, 150)
        elif al_max:
            estado, color = "Al máximo", (150, 150, 150)
        else:
            estado = f"{item['precio']} monedas"
            color = (245, 200, 70) if jugador.monedas >= item["precio"] else (230, 90, 90)
        sup = f_nom.render(estado, True, color)
        pantalla.blit(sup, (tarjeta.centerx - sup.get_width() // 2, tarjeta.bottom - 28))
        if not bloqueado:
            botones[f"__tienda__{i}"] = tarjeta
    if mensaje:
        texto, es_error = mensaje
        sup = f_nom.render(texto, True, (230, 90, 90) if es_error else (120, 255, 150))
        pantalla.blit(sup, (caja.centerx - sup.get_width() // 2, caja.bottom - 34))
    ayuda = f_txt.render("[E] o X para cerrar · el mundo sigue en marcha", True, (130, 140, 160))
    pantalla.blit(ayuda, (caja.x + 18, caja.bottom - 18))
    botones["__tienda_fondo__"] = caja      # el ultimo: los botones de dentro tienen prioridad
    return botones
