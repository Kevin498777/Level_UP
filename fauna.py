# -*- coding: utf-8 -*-
"""
Fauna ambiental del mundo (FASE 1): sin colision, pura vida visual.

- Mariposas y luciernagas que revolotean sobre praderas y flores.
- Pajaros posados en los arboles que alzan vuelo si el jugador se acerca.
- Peces como sombras bajo el agua de los lagos.

Todo se actualiza y dibuja solo cerca de la camara (culling por 'vista') para
no afectar el rendimiento aunque el mundo sea enorme.
"""

import math
import random
import pygame
from habilidades import aplicar_desangrado

# Margen extra (px) alrededor de la vista para activar/mantener la fauna.
MARGEN_CULL = 90
PIXELES_POR_PUNTO_EMPUJE = 6   # igual que en el juego: puntos de arma -> px de empuje


# =====================================================================
# MARIPOSAS / LUCIERNAGAS  (poblacion dinamica alrededor de la camara)
# =====================================================================
MARIPOSA_MAX = 6              # tope de mariposas visibles a la vez
MARIPOSA_VEL = 26.0            # px/s de deambular
PROB_LUCIERNAGA = 0.22         # fraccion que son luciernagas (volando, sin noche)
MARIPOSA_COLORES = [
    (245, 245, 235), (250, 210, 70), (240, 140, 50),
    (95, 155, 230), (230, 120, 180), (250, 250, 250),
]

_GLOW = None


def _glow_luciernaga():
    """Halo ambar pre-renderizado para las luciernagas."""
    global _GLOW
    if _GLOW is None:
        r = 7
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for rad, a in ((7, 35), (5, 70), (3, 130)):
            pygame.draw.circle(s, (255, 220, 120, a), (r, r), rad)
        _GLOW = s
    return _GLOW


class Mariposa:
    def __init__(self, x, y):
        self.centro = pygame.Vector2(x, y)
        self.luciernaga = random.random() < PROB_LUCIERNAGA
        self.color = (255, 215, 120) if self.luciernaga else random.choice(MARIPOSA_COLORES)
        self.dir = random.uniform(0, math.tau)
        self.vel = MARIPOSA_VEL * random.uniform(0.7, 1.3)
        self.fase = random.uniform(0, math.tau)
        self._t_giro = random.uniform(0.3, 1.0)

    def actualizar(self, dt):
        self._t_giro -= dt
        if self._t_giro <= 0:
            self.dir += random.uniform(-1.2, 1.2)
            self._t_giro = random.uniform(0.3, 1.0)
        self.fase += dt * 13.0
        self.centro.x += math.cos(self.dir) * self.vel * dt
        self.centro.y += math.sin(self.dir) * self.vel * dt
        self.centro.y += math.sin(self.fase * 0.3) * 6 * dt  # flotar vertical

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        if self.luciernaga:
            glow = _glow_luciernaga()
            pantalla.blit(glow, (px - glow.get_width() // 2, py - glow.get_height() // 2))
            pygame.draw.circle(pantalla, self.color, (px, py), 2)
            return
        # Mariposa: dos alas cuyo ancho oscila (aleteo)
        ancho = 2 + int(abs(math.sin(self.fase)) * 3)
        pygame.draw.ellipse(pantalla, self.color, (px - ancho, py - 3, ancho, 6))
        pygame.draw.ellipse(pantalla, self.color, (px, py - 3, ancho, 6))
        pygame.draw.line(pantalla, (45, 38, 32), (px, py - 3), (px, py + 3), 1)


# =====================================================================
# PAJAROS  (anclados a un arbol; vuelan si te acercas y regresan)
# =====================================================================
PAJARO_PROB = 0.20             # fraccion de arboles con pajaro
PAJARO_SUSTO = 120.0           # px: distancia a la que alzan vuelo
PAJARO_VEL_VUELO = 150.0       # px/s
PAJARO_COLORES = [(45, 40, 38), (28, 28, 34), (95, 65, 45)]


class Pajaro:
    def __init__(self, arbol):
        self.arbol = arbol
        self.base = pygame.Vector2(arbol.centro.x, arbol.centro.y - arbol.radio_copa + 2)
        self.centro = pygame.Vector2(self.base)
        self.estado = "posado"   # posado / huyendo / regresando
        self.color = random.choice(PAJARO_COLORES)
        self.fase = random.uniform(0, math.tau)
        self.vel_vuelo = pygame.Vector2()
        self._t = 0.0

    def _huir(self, jugador):
        self.estado = "huyendo"
        hacia = self.centro - jugador.posicion
        if hacia.length() < 1:
            hacia = pygame.Vector2(0, -1)
        self.vel_vuelo = hacia.normalize() * PAJARO_VEL_VUELO
        self.vel_vuelo.y -= 50   # sesgo hacia arriba
        self._t = random.uniform(1.5, 2.5)

    def actualizar(self, dt, jugador):
        self.fase += dt * 15.0
        dist = (jugador.posicion - self.base).length()
        if self.estado == "posado":
            if dist < PAJARO_SUSTO:
                self._huir(jugador)
        elif self.estado == "huyendo":
            self.centro += self.vel_vuelo * dt
            self.vel_vuelo *= max(0.0, 1 - dt * 0.8)
            self._t -= dt
            if self._t <= 0 and dist > PAJARO_SUSTO * 1.6:
                self.estado = "regresando"
        elif self.estado == "regresando":
            if dist < PAJARO_SUSTO:
                self._huir(jugador)
            else:
                d = self.base - self.centro
                if d.length() <= 5:
                    self.centro.update(self.base)
                    self.estado = "posado"
                else:
                    self.centro += d.normalize() * PAJARO_VEL_VUELO * dt

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        if self.estado == "posado":
            pygame.draw.ellipse(pantalla, self.color, (px - 6, py - 4, 12, 8))
            pygame.draw.circle(pantalla, self.color, (px + 6, py - 4), 3)
        else:
            a = 4 + int(abs(math.sin(self.fase)) * 6)
            pygame.draw.line(pantalla, self.color, (px, py), (px - 9, py - a), 3)
            pygame.draw.line(pantalla, self.color, (px, py), (px + 9, py - a), 3)


# =====================================================================
# PECES  (sombras bajo el agua; se dispersan si entras al agua cerca)
# =====================================================================
PEZ_MIN_RADIO_LAGO = 120.0     # solo lagos de este radio o mas
PEZ_VEL = (16.0, 32.0)


class Pez:
    def __init__(self, charco):
        self.charco = charco
        ang = random.uniform(0, math.tau)
        r = random.uniform(0, max(0.0, charco.radio * 0.6))
        self.centro = pygame.Vector2(charco.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
        self.dir = random.uniform(0, math.tau)
        self.vel = random.uniform(*PEZ_VEL)
        self.largo = random.uniform(9, 16)
        self._t_giro = random.uniform(0.5, 1.5)

    def actualizar(self, dt, jugador):
        self._t_giro -= dt
        if self._t_giro <= 0:
            self.dir += random.uniform(-0.8, 0.8)
            self._t_giro = random.uniform(0.5, 1.5)
        vel = self.vel
        dist = (jugador.posicion - self.centro).length()
        if getattr(jugador, "en_agua", False) and dist < 95:
            self.dir = math.atan2(self.centro.y - jugador.posicion.y,
                                  self.centro.x - jugador.posicion.x)
            vel = self.vel * 2.3
        nuevo = pygame.Vector2(self.centro.x + math.cos(self.dir) * vel * dt,
                               self.centro.y + math.sin(self.dir) * vel * dt)
        if (nuevo - self.charco.centro).length() > self.charco.radio - 10:
            self.dir += math.pi   # rebote hacia dentro del lago
        else:
            self.centro.update(nuevo)

    def dibujar(self, pantalla, desplazamiento):
        px = self.centro.x - desplazamiento[0]
        py = self.centro.y - desplazamiento[1]
        L = max(6, int(self.largo))
        W = max(4, int(self.largo * 0.5))
        surf = pygame.Surface((L, W), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (10, 25, 40, 85), (0, 0, L, W))
        surf = pygame.transform.rotate(surf, -math.degrees(self.dir))
        pantalla.blit(surf, surf.get_rect(center=(round(px), round(py))))


# =====================================================================
# SISTEMA DE FAUNA
# =====================================================================

# =====================================================================
# RANAS  (orilla de lagos; saltitos y brinco al agua si te acercas)
# =====================================================================
RANA_SUSTO = 72.0              # px: distancia a la que saltan al agua
RANA_COLORES = [(70, 130, 60), (90, 155, 72), (58, 110, 55)]


class Rana:
    def __init__(self, charco):
        self.charco = charco
        self.color = random.choice(RANA_COLORES)
        self._colocar_en_orilla()
        self.estado = "quieta"          # quieta / saltando / sumergida
        self._espera = random.uniform(1.2, 3.5)
        self._origen = pygame.Vector2(self.centro)
        self._destino = pygame.Vector2(self.centro)
        self._tt = 0.0
        self._dur = 0.28
        self._sumergir = False

    def _colocar_en_orilla(self):
        nen = getattr(self.charco, "nenufares", None)
        if nen and random.random() < 0.5:
            c, _r = random.choice(nen)
            self.centro = pygame.Vector2(c)
            self.en_nenufar = True
            return
        ang = random.uniform(0, math.tau)
        r = max(0.0, self.charco.radio - random.uniform(4, 14))
        self.centro = pygame.Vector2(self.charco.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
        self.en_nenufar = False

    def _saltar(self, destino, sumergir=False):
        self._origen = pygame.Vector2(self.centro)
        self._destino = destino
        self._tt = 0.0
        self._sumergir = sumergir
        self.estado = "saltando"

    def actualizar(self, dt, jugador):
        dist = (jugador.posicion - self.centro).length()
        if self.estado == "sumergida":
            self._espera -= dt
            if self._espera <= 0 and dist > RANA_SUSTO * 1.6:
                self._colocar_en_orilla()
                self.estado = "quieta"
                self._espera = random.uniform(1.2, 3.5)
            return
        if self.estado == "quieta":
            if dist < RANA_SUSTO:
                hacia = self.charco.centro - self.centro
                paso = hacia.normalize() * 28 if hacia.length() > 1 else pygame.Vector2(0, -20)
                self._saltar(self.centro + paso, sumergir=True)
            else:
                self._espera -= dt
                if self._espera <= 0:
                    ang = random.uniform(0, math.tau)
                    destino = self.centro + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(6, 16)
                    if (destino - self.charco.centro).length() > self.charco.radio:
                        destino = pygame.Vector2(self.centro)
                    self._saltar(destino)
                    self._espera = random.uniform(1.2, 3.5)
        elif self.estado == "saltando":
            self._tt += dt
            t = min(1.0, self._tt / self._dur)
            self.centro = self._origen.lerp(self._destino, t)
            if t >= 1.0:
                if self._sumergir:
                    self.estado = "sumergida"
                    self._espera = random.uniform(2.5, 4.5)
                else:
                    self.estado = "quieta"

    def dibujar(self, pantalla, desplazamiento):
        if self.estado == "sumergida":
            return
        alto = 0.0
        if self.estado == "saltando":
            alto = math.sin(min(1.0, self._tt / self._dur) * math.pi) * 7
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1] - alto)
        pygame.draw.ellipse(pantalla, self.color, (px - 5, py - 3, 10, 6))
        pygame.draw.circle(pantalla, self.color, (px - 3, py - 4), 2)
        pygame.draw.circle(pantalla, self.color, (px + 3, py - 4), 2)
        pygame.draw.circle(pantalla, (15, 20, 15), (px - 3, py - 4), 1)
        pygame.draw.circle(pantalla, (15, 20, 15), (px + 3, py - 4), 1)


class SistemaFauna:
    def __init__(self, centro_mundo, radio_mundo, vegetacion, charcos):
        self.centro_mundo = pygame.Vector2(centro_mundo)
        self.radio_mundo = radio_mundo
        self.vegetacion = vegetacion
        self.charcos = charcos
        self.mariposas = []

        # Pajaros: una fraccion de los arboles existentes.
        self.pajaros = [Pajaro(a) for a in vegetacion.arboles if random.random() < PAJARO_PROB]

        # Peces: 2 a 5 por lago mediano/grande.
        self.peces = []
        for c in charcos:
            if c.radio >= PEZ_MIN_RADIO_LAGO:
                n = min(5, max(2, int(c.radio / 120)))
                self.peces.extend(Pez(c) for _ in range(n))

        # Ranas: 1 a 3 por lago mediano/grande.
        self.ranas = []
        for c in charcos:
            if c.radio >= PEZ_MIN_RADIO_LAGO:
                self.ranas.extend(Rana(c) for _ in range(random.randint(1, 3)))

        # Madrigueras de conejos salvajes en el pasto alto (10 a 15 en el mundo).
        self.madrigueras = []
        self.conejos = []
        zonas = list(getattr(vegetacion, "pastizales", [])) or list(getattr(vegetacion, "praderas", []))
        if zonas:
            for _ in range(random.randint(MADRIGUERAS_MIN, MADRIGUERAS_MAX)):
                centro_p, radio_p = random.choice(zonas)
                ang = random.uniform(0, math.tau)
                r = random.uniform(0, max(0.0, radio_p * 0.7))
                pos = pygame.Vector2(centro_p) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
                m = Madriguera(pos)
                self.madrigueras.append(m)
                for _ in range(random.randint(*CONEJOS_POR_MADRIGUERA)):
                    self.conejos.append(ConejoSalvaje(m))

        # Venados: poblacion global repartida por el mundo (hasta VENADO_MAX).
        self.venados = [self._nuevo_venado() for _ in range(VENADO_MAX)]
        self._t_repro_venado = 0.0

        # Jabalies y zorros: poblacion global repartida por el mundo.
        self.jabalies = [self._nuevo_jabali() for _ in range(JABALI_MAX)]
        self._t_repro_jabali = 0.0
        self.zorros = [self._nuevo_zorro() for _ in range(ZORRO_MAX)]

        # Manadas de lobos (7 por mundo), en los bosques.
        self.manadas = []
        bosques = list(getattr(vegetacion, "bosques", []))
        for _ in range(LOBO_MANADAS):
            if bosques:
                centro_b, radio_b = random.choice(bosques)
                ang = random.uniform(0, math.tau)
                r = random.uniform(0, max(0.0, radio_b * 0.6))
                centro = pygame.Vector2(centro_b) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r
            else:
                centro = self._punto_mundo()
            self.manadas.append(Manada(centro))

    def _punto_mariposa(self, zona):
        """Punto para generar una mariposa: sesgado hacia flores visibles."""
        flores = self.vegetacion.flores
        for _ in range(6):
            if flores:
                f = random.choice(flores)
                if zona.collidepoint(f.centro.x, f.centro.y):
                    return pygame.Vector2(f.centro.x + random.uniform(-25, 25),
                                          f.centro.y + random.uniform(-25, 25))
        for _ in range(6):
            p = pygame.Vector2(random.uniform(zona.left, zona.right),
                               random.uniform(zona.top, zona.bottom))
            if (p - self.centro_mundo).length() > self.radio_mundo:
                continue
            if any(c.contiene(p) for c in self.charcos):
                continue
            return p
        return None

    def actualizar(self, dt, jugador, vista):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)

        # Mariposas: cull de las que se alejan y repoblado alrededor de la camara.
        self.mariposas = [m for m in self.mariposas
                          if zona.collidepoint(m.centro.x, m.centro.y)]
        for m in self.mariposas:
            m.actualizar(dt)
        intentos = 0
        while len(self.mariposas) < MARIPOSA_MAX and intentos < 8:
            intentos += 1
            p = self._punto_mariposa(zona)
            if p is not None:
                self.mariposas.append(Mariposa(p.x, p.y))

        # Pajaros: solo los cercanos (por su arbol o en pleno vuelo).
        for pj in self.pajaros:
            if zona.collidepoint(pj.centro.x, pj.centro.y) or zona.collidepoint(pj.base.x, pj.base.y):
                pj.actualizar(dt, jugador)

        # Peces: solo los de lagos en vista.
        for pz in self.peces:
            if zona.collidepoint(pz.centro.x, pz.centro.y):
                pz.actualizar(dt, jugador)

        # Ranas: solo las de lagos en vista.
        for rn in self.ranas:
            if zona.collidepoint(rn.centro.x, rn.centro.y):
                rn.actualizar(dt, jugador)

        # Amenazas de las que huyen los animales: el jugador y sus sombras (invocaciones).
        amenazas = [jugador] if getattr(jugador, "detectable", True) else []
        for hab in getattr(jugador, "habilidades", ()):
            for cr in getattr(hab, "criaturas", ()):
                if getattr(cr, "vivo", True):
                    amenazas.append(cr)
        # Los zorros hambrientos y visibles tambien asustan a los conejos (depredador).
        for z in getattr(self, "zorros", ()):
            if z.vivo and z.hambriento and not z.invisible:
                amenazas.append(z)

        # Conejos salvajes: quitar muertos y actualizar los cercanos.
        self.conejos = [c for c in self.conejos if c.vivo]
        for cn in self.conejos:
            if zona.collidepoint(cn.posicion.x, cn.posicion.y) or zona.collidepoint(cn.madriguera.centro.x, cn.madriguera.centro.y):
                cn.actualizar(dt, jugador, amenazas)
        # Reproduccion por madriguera: cada 30 s nace +1 si hay >=2 y no supera el maximo.
        for m in self.madrigueras:
            m._t_repro += dt
            if m._t_repro >= CONEJO_REPRO_INTERVALO:
                m._t_repro -= CONEJO_REPRO_INTERVALO
                vivos = sum(1 for c in self.conejos if c.madriguera is m)
                if 2 <= vivos < m.max_conejos:
                    self.conejos.append(ConejoSalvaje(m))

        # Venados: quitar muertos y actualizar los cercanos.
        self.venados = [v for v in self.venados if v.vivo]
        for v in self.venados:
            if zona.collidepoint(v.posicion.x, v.posicion.y):
                v.actualizar(dt, jugador, amenazas)
        # Reproduccion: cada 60 s nace +1 si hay >=2 venados y no supera VENADO_MAX.
        self._t_repro_venado += dt
        if self._t_repro_venado >= VENADO_REPRO_INTERVALO:
            self._t_repro_venado -= VENADO_REPRO_INTERVALO
            if 2 <= len(self.venados) < VENADO_MAX:
                padre = random.choice(self.venados)
                off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
                self.venados.append(Venado(padre.posicion.x + off.x, padre.posicion.y + off.y))

        # Jabalies: quitar muertos, actualizar los cercanos, reproduccion.
        self.jabalies = [j for j in self.jabalies if j.vivo]
        for j in self.jabalies:
            if zona.collidepoint(j.posicion.x, j.posicion.y):
                j.actualizar(dt, jugador, amenazas)
        self._t_repro_jabali += dt
        if self._t_repro_jabali >= JABALI_REPRO_INTERVALO:
            self._t_repro_jabali -= JABALI_REPRO_INTERVALO
            if 2 <= len(self.jabalies) < JABALI_MAX:
                padre = random.choice(self.jabalies)
                off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
                self.jabalies.append(Jabali(padre.posicion.x + off.x, padre.posicion.y + off.y))

        # Zorros: quitar muertos, actualizar los cercanos (cazan conejos).
        self.zorros = [z for z in self.zorros if z.vivo]
        for z in self.zorros:
            if zona.collidepoint(z.posicion.x, z.posicion.y):
                z.actualizar(dt, jugador, amenazas, self.conejos)

        # Manadas de lobos: actualizar las que tienen algun lobo cerca de la camara.
        presas = [c for c in self.conejos if c.vivo] + [v for v in self.venados if v.vivo]
        for man in self.manadas:
            if any(l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y) for l in man.lobos):
                man.actualizar(dt, jugador, amenazas, presas)

    # ---- Dibujo por capas (llamados desde el render de mundo.py) ----
    def dibujar_peces(self, pantalla, vista, desplazamiento):
        for pz in self.peces:
            if vista.collidepoint(pz.centro.x, pz.centro.y):
                pz.dibujar(pantalla, desplazamiento)

    def dibujar_ranas(self, pantalla, vista, desplazamiento):
        for rn in self.ranas:
            if vista.collidepoint(rn.centro.x, rn.centro.y):
                rn.dibujar(pantalla, desplazamiento)

    def dibujar_pajaros(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for pj in self.pajaros:
            if zona.collidepoint(pj.centro.x, pj.centro.y):
                pj.dibujar(pantalla, desplazamiento)

    def dibujar_mariposas(self, pantalla, vista, desplazamiento):
        for m in self.mariposas:
            m.dibujar(pantalla, desplazamiento)

    def _punto_venado(self, zona, jugador):
        for _ in range(8):
            p = pygame.Vector2(random.uniform(zona.left, zona.right), random.uniform(zona.top, zona.bottom))
            if (p - self.centro_mundo).length() > self.radio_mundo:
                continue
            if any(c.contiene(p) for c in self.charcos):
                continue
            if (p - jugador.posicion).length() < VENADO_SUSTO * 1.1:
                continue
            return p
        return None

    def _punto_mundo(self):
        for _ in range(20):
            ang = random.uniform(0, math.tau)
            d = math.sqrt(random.random()) * self.radio_mundo * 0.95
            p = self.centro_mundo + pygame.Vector2(math.cos(ang), math.sin(ang)) * d
            if any(c.contiene(p) for c in self.charcos):
                continue
            return p
        return pygame.Vector2(self.centro_mundo)

    def _nuevo_venado(self):
        p = self._punto_mundo()
        return Venado(p.x, p.y)

    def _nuevo_jabali(self):
        p = self._punto_mundo()
        return Jabali(p.x, p.y)

    def _nuevo_zorro(self):
        p = self._punto_mundo()
        return Zorro(p.x, p.y)

    def cuerpos_solidos(self, vista):
        """Animales con colision solida cerca de la camara (para resolver_solapamientos)."""
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        solidos = []
        for cn in self.conejos:
            if cn.solido and zona.collidepoint(cn.posicion.x, cn.posicion.y):
                solidos.append(cn)
        for v in self.venados:
            if v.vivo and zona.collidepoint(v.posicion.x, v.posicion.y):
                solidos.append(v)
        for j in self.jabalies:
            if j.vivo and zona.collidepoint(j.posicion.x, j.posicion.y):
                solidos.append(j)
        for z in self.zorros:
            if z.vivo and not z.invisible and zona.collidepoint(z.posicion.x, z.posicion.y):
                solidos.append(z)
        for man in self.manadas:
            for l in man.lobos:
                if l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y):
                    solidos.append(l)
        return solidos

    def animales_con_vida(self, vista):
        """Animales que pueden recibir dano cerca de la camara (venados y conejos)."""
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        res = [v for v in self.venados if v.vivo and zona.collidepoint(v.posicion.x, v.posicion.y)]
        res += [c for c in self.conejos if c.vivo and c.estado != "escondido" and zona.collidepoint(c.posicion.x, c.posicion.y)]
        res += [j for j in self.jabalies if j.vivo and zona.collidepoint(j.posicion.x, j.posicion.y)]
        res += [z for z in self.zorros if z.vivo and not z.invisible and zona.collidepoint(z.posicion.x, z.posicion.y)]
        for man in self.manadas:
            res += [l for l in man.lobos if l.vivo and zona.collidepoint(l.posicion.x, l.posicion.y)]
        return res

    def dibujar_madrigueras(self, pantalla, vista, desplazamiento):
        for m in self.madrigueras:
            if vista.collidepoint(m.centro.x, m.centro.y):
                m.dibujar(pantalla, desplazamiento)

    def dibujar_conejos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for cn in self.conejos:
            if zona.collidepoint(cn.posicion.x, cn.posicion.y):
                cn.dibujar(pantalla, desplazamiento)

    def dibujar_venados(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for v in self.venados:
            if zona.collidepoint(v.posicion.x, v.posicion.y):
                v.dibujar(pantalla, desplazamiento)

    def dibujar_jabalies(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for j in self.jabalies:
            if zona.collidepoint(j.posicion.x, j.posicion.y):
                j.dibujar(pantalla, desplazamiento)

    def dibujar_zorros(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for z in self.zorros:
            if zona.collidepoint(z.posicion.x, z.posicion.y):
                z.dibujar(pantalla, desplazamiento)

    def dibujar_lobos(self, pantalla, vista, desplazamiento):
        zona = vista.inflate(MARGEN_CULL * 2, MARGEN_CULL * 2)
        for man in self.manadas:
            for l in man.lobos:
                if zona.collidepoint(l.posicion.x, l.posicion.y):
                    l.dibujar(pantalla, desplazamiento)


# =====================================================================
# CONEJOS SALVAJES Y MADRIGUERAS  (praderas; huyen a su madriguera)
# =====================================================================
MADRIGUERAS_MIN = 10
MADRIGUERAS_MAX = 10
CONEJOS_POR_MADRIGUERA = (2, 10)
CONEJO_RADIO = 7
CONEJO_MASA = 1.0
CONEJO_VISION = 100.0          # ve al jugador a esta distancia -> huye
CONEJO_VEL_PASEO = 45.0
CONEJO_VEL_HUIDA = 160.0
CONEJO_COLORES = [(150, 130, 110), (172, 150, 128), (132, 116, 98), (120, 120, 126)]
CONEJO_VIDA = (5, 20)
CONEJO_MAX_MADRIGUERA = 10
CONEJO_REPRO_INTERVALO = 30.0


class AnimalCombatible:
    """Interfaz minima de 'enemigo' para que armas, habilidades, mascotas y telaranas
    puedan danar/atrapar al animal (se mete en la lista 'enemigos' del juego).
    No tiene escudos: recibir_dano (definido en cada animal) baja la vida directo."""

    def _init_combate(self):
        self.escudo = 0.0
        self.escudo_magico = 0.0
        self.anulacion_escudo_magico = 0.0
        self.herramienta = None            # no ataca: los bucles de 'arma enemiga' lo saltan
        self.detectable = True
        self.desangrado = None
        self.veneno = None
        self.quemadura = None
        self.inmovilizado = None
        self.ralentizacion = 0.0

    def aplicar_empuje(self, direccion, puntos):
        if puntos <= 0 or direccion is None or direccion.length() == 0:
            return
        self.posicion += direccion.normalize() * min(float(puntos) * PIXELES_POR_PUNTO_EMPUJE, 96.0)

    def _tick_efectos(self, dt):
        if self.desangrado is not None:
            self.desangrado.actualizar(dt, self)
            if not self.desangrado.activo:
                self.desangrado = None
        if self.quemadura is not None:
            self.quemadura.actualizar(dt, self)
            if not self.quemadura.activo:
                self.quemadura = None
        if self.veneno is not None:
            self.veneno.actualizar(dt, self)
            if not self.veneno.activo:
                self.veneno = None
        if self.inmovilizado is not None:
            self.inmovilizado.actualizar(dt, self)
            if not self.inmovilizado.activo:
                self.inmovilizado = None
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False


class Madriguera:
    def __init__(self, centro):
        self.centro = pygame.Vector2(centro)
        self.radio_zona = random.uniform(180, 320)   # radio de deambular (separacion progresiva)
        self.max_conejos = CONEJO_MAX_MADRIGUERA
        self._t_repro = random.uniform(0, CONEJO_REPRO_INTERVALO)

    def dibujar(self, pantalla, desplazamiento):
        px = round(self.centro.x - desplazamiento[0])
        py = round(self.centro.y - desplazamiento[1])
        # Pasto alto alrededor (mechones mas altos que el pasto normal)
        for i in range(12):
            ang = (i / 12) * math.tau
            bx = px + round(math.cos(ang) * 17)
            by = py + round(math.sin(ang) * 11)
            pygame.draw.line(pantalla, (58, 118, 56), (bx, by), (bx - 2, by - 15), 2)
            pygame.draw.line(pantalla, (78, 142, 70), (bx + 2, by), (bx + 1, by - 18), 2)
        # Monticulo de tierra y agujero
        pygame.draw.ellipse(pantalla, (96, 74, 54), (px - 16, py - 8, 32, 18))
        pygame.draw.ellipse(pantalla, (74, 56, 40), (px - 16, py - 8, 32, 18), 1)
        pygame.draw.ellipse(pantalla, (26, 19, 15), (px - 8, py - 4, 16, 11))


class ConejoSalvaje(AnimalCombatible):
    def __init__(self, madriguera):
        self.madriguera = madriguera
        self.radio = CONEJO_RADIO
        self.masa = CONEJO_MASA
        self.color = random.choice(CONEJO_COLORES)
        self.vida = random.randint(*CONEJO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self._init_combate()
        self.vel_mult = 1.0
        self.posicion = self._punto_zona()
        self.destino = pygame.Vector2(self.posicion)
        self.estado = "deambula"          # deambula / huye / escondido
        self._espera = random.uniform(0.5, 2.5)
        self._t_esc = 0.0
        self.dir_mira = pygame.Vector2(1, 0)

    @property
    def solido(self):
        return self.vivo and self.estado != "escondido"

    def _punto_zona(self):
        ang = random.uniform(0, math.tau)
        r = random.uniform(0, self.madriguera.radio_zona)
        return pygame.Vector2(self.madriguera.centro) + pygame.Vector2(math.cos(ang), math.sin(ang)) * r

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.estado = "huye"          # al recibir dano huye a la madriguera
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self.posicion += direccion_empuje.normalize() * 4
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.inmovilizado is not None:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()
        if amenazas:
            cercana = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())
            dist_j = (cercana.posicion - self.posicion).length()
        else:
            dist_j = float("inf")

        if self.estado == "escondido":
            self._t_esc -= dt
            if self._t_esc <= 0 and dist_j > CONEJO_VISION * 1.4:
                self.posicion = pygame.Vector2(self.madriguera.centro)
                self.estado = "deambula"
                self._espera = random.uniform(0.5, 2.0)
            return

        # Si ve al jugador, huye a la madriguera.
        if dist_j < CONEJO_VISION:
            self.estado = "huye"

        if self.estado == "huye":
            if dist_j > CONEJO_VISION * 1.5:
                # Ya no lo persiguen: deja de huir y deambula donde este.
                self.estado = "deambula"
                self._espera = random.uniform(0.5, 2.0)
                return
            d = self.madriguera.centro - self.posicion
            if d.length() <= 10:
                self.estado = "escondido"
                self._t_esc = 60.0
                return
            self.posicion += d.normalize() * CONEJO_VEL_HUIDA * self.vel_mult * dt
            self.dir_mira = d.normalize()
            return

        # Deambula alrededor de su madriguera, con pausas.
        self._espera -= dt
        d = self.destino - self.posicion
        if self._espera <= 0:
            self.destino = self._punto_zona()
            self._espera = random.uniform(0.8, 2.6)
        elif d.length() > 3:
            self.posicion += d.normalize() * CONEJO_VEL_PASEO * self.vel_mult * dt
            self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if self.estado == "escondido":
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        der = self.dir_mira.x >= 0
        s = 1 if der else -1
        pygame.draw.ellipse(pantalla, c, (px - 7, py - 5, 14, 10))        # cuerpo
        hx = px + s * 5
        pygame.draw.circle(pantalla, c, (hx, py - 3), 4)                  # cabeza
        pygame.draw.ellipse(pantalla, c, (hx - 3, py - 13, 3, 9))         # orejas
        pygame.draw.ellipse(pantalla, c, (hx + 1, py - 13, 3, 9))
        pygame.draw.circle(pantalla, (235, 235, 230), (px - s * 6, py + 2), 2)   # cola
        pygame.draw.circle(pantalla, (20, 18, 16), (hx + s, py - 4), 1)   # ojo
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 4, 1)
        if self.vida < self.vida_max:
            w = 14
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 7, py - 16, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 7, py - 16, fw, 3))


# =====================================================================
# VENADOS  (timidos; huyen lejos y se regeneran si reciben dano)
# =====================================================================
VENADO_MAX = 50
VENADO_RADIO = 12
VENADO_MASA = 40.0
VENADO_VIDA = (20, 40)
VENADO_REGEN_INTERVALO = 2.0   # 1 pv cada 2 s tras recibir dano
VENADO_SUSTO = 160.0
VENADO_VEL_PASEO = 40.0
VENADO_VEL_HUIDA = 200.0
VENADO_REPRO_INTERVALO = 60.0
VENADO_COLORES = [(140, 96, 60), (120, 82, 52), (156, 110, 72)]


class Venado(AnimalCombatible):
    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = VENADO_RADIO
        self.masa = VENADO_MASA
        self.color = random.choice(VENADO_COLORES)
        self.vida = random.randint(*VENADO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.cornamenta = random.random() < 0.5
        self.estado = "pasta"             # pasta / huye
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.5, 4.0)
        self._t_huida = 0.0
        self._danado = False
        self._regen_t = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self._danado = True
        self.estado = "huye"
        self._t_huida = random.uniform(2.5, 4.0)
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self.posicion += direccion_empuje.normalize() * 6
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None):
        if not self.vivo:
            return
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.inmovilizado is not None:
            return
        # Regeneracion: 1 pv cada 2 s mientras este dañado.
        if self._danado and self.vida < self.vida_max:
            self._regen_t += dt
            while self._regen_t >= VENADO_REGEN_INTERVALO:
                self._regen_t -= VENADO_REGEN_INTERVALO
                self.vida = min(self.vida_max, self.vida + 1)
            if self.vida >= self.vida_max:
                self._danado = False
                self._regen_t = 0.0

        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()
        if amenazas:
            cercana = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())
            dist_j = (cercana.posicion - self.posicion).length()
        else:
            cercana = None
            dist_j = float("inf")
        if dist_j < VENADO_SUSTO:
            self.estado = "huye"
            self._t_huida = max(self._t_huida, 0.6)

        if self.estado == "huye":
            self._t_huida -= dt
            d = self.posicion - cercana.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * VENADO_VEL_HUIDA * dt
            self.dir_mira = d.normalize()
            if self._t_huida <= 0 and dist_j > VENADO_SUSTO:
                self.estado = "pasta"
                self._espera = random.uniform(1.5, 4.0)
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(30, 90)
                self._espera = random.uniform(1.5, 4.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * VENADO_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-6, 6):                                               # patas
            pygame.draw.line(pantalla, (92, 64, 42), (px + lx, py + 2), (px + lx, py + 11), 2)
        pygame.draw.ellipse(pantalla, c, (px - 11, py - 6, 22, 13))      # cuerpo
        nx = px + s * 11
        pygame.draw.line(pantalla, c, (px + s * 7, py - 4), (nx, py - 12), 4)   # cuello
        pygame.draw.circle(pantalla, c, (nx, py - 13), 4)               # cabeza
        pygame.draw.circle(pantalla, (70, 48, 32), (nx + s * 3, py - 12), 2)    # hocico
        if self.cornamenta:
            for dxh in (-2, 2):
                bx = nx + dxh
                pygame.draw.line(pantalla, (212, 192, 152), (bx, py - 16), (bx, py - 22), 2)
                pygame.draw.line(pantalla, (212, 192, 152), (bx, py - 20), (bx + dxh, py - 24), 2)
        pygame.draw.circle(pantalla, (236, 226, 216), (px - s * 11, py - 2), 2)  # cola
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self._danado and self.vida < self.vida_max:                 # barra de vida
            w = 22
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 11, py - 20, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 11, py - 20, fw, 3))


# =====================================================================
# JABALI  (neutral; si lo golpean entra en RABIA y embiste al atacante)
# =====================================================================
JABALI_MAX = 20
JABALI_RADIO = 14
JABALI_MASA = 60.0
JABALI_VIDA = (40, 70)
JABALI_DANO = (10, 18)
JABALI_EMPUJE = 40               # empuje muy alto
JABALI_VEL_PASEO = 30.0
JABALI_VEL_RABIA = 195.0
JABALI_VEL_HUIDA = 175.0
JABALI_RABIA_DUR = 6.0
JABALI_GOLPE_CD = 1.0
JABALI_REPRO_INTERVALO = 60.0
JABALI_COLORES = [(92, 72, 56), (76, 58, 46), (106, 82, 62)]


class Jabali(AnimalCombatible):
    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = JABALI_RADIO
        self.masa = JABALI_MASA
        self.color = random.choice(JABALI_COLORES)
        self.vida = random.randint(*JABALI_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.estado = "deambula"          # deambula / rabia / huye
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.5, 4.0)
        self._t_rabia = 0.0
        self._t_huida = 0.0
        self._cd_golpe = 0.0
        self._objetivo_pos = None
        self._jitter = pygame.Vector2()
        self._t_jitter = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.estado = "rabia"
        self._t_rabia = JABALI_RABIA_DUR
        if direccion_empuje is not None and direccion_empuje.length() > 0:
            self._objetivo_pos = self.posicion - direccion_empuje   # hacia quien lo golpeo
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def _elegir_objetivo(self, jugador, amenazas):
        if not amenazas:
            return None
        if self._objetivo_pos is not None:
            return min(amenazas, key=lambda o: (o.posicion - self._objetivo_pos).length_squared())
        return min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared())

    def actualizar(self, dt, jugador, amenazas=None):
        self._tick_efectos(dt)
        if not self.vivo:
            return
        if self.inmovilizado is not None:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()

        if self.estado == "rabia":
            self._t_rabia -= dt
            self._cd_golpe -= dt
            objetivo = self._elegir_objetivo(jugador, amenazas)
            if objetivo is None:
                if self._t_rabia <= 0:
                    self.estado = "huye"
                    self._t_huida = random.uniform(2.5, 4.0)
                    self._objetivo_pos = None
                return
            self._t_jitter -= dt
            if self._t_jitter <= 0:
                ang = random.uniform(-1.0, 1.0)
                self._jitter = pygame.Vector2(math.cos(ang), math.sin(ang))
                self._t_jitter = random.uniform(0.15, 0.35)
            d = objetivo.posicion - self.posicion
            base = d.normalize() if d.length() > 0 else pygame.Vector2(1, 0)
            dir_mov = base + self._jitter * 0.6
            if dir_mov.length() > 0:
                dir_mov = dir_mov.normalize()
                self.posicion += dir_mov * JABALI_VEL_RABIA * dt
                self.dir_mira = dir_mov
            if d.length() <= self.radio + getattr(objetivo, "radio", 10) + 4 and self._cd_golpe <= 0:
                self._cd_golpe = JABALI_GOLPE_CD
                dano = random.randint(*JABALI_DANO)
                hacia = objetivo.posicion - self.posicion
                if hasattr(objetivo, "recibir_dano"):
                    objetivo.recibir_dano(dano, "fisico", hacia)
                if hasattr(objetivo, "aplicar_empuje"):
                    objetivo.aplicar_empuje(hacia, JABALI_EMPUJE)
            if self._t_rabia <= 0:
                self.estado = "huye"
                self._t_huida = random.uniform(2.5, 4.0)
                self._objetivo_pos = None
        elif self.estado == "huye":
            self._t_huida -= dt
            d = self.posicion - jugador.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * JABALI_VEL_HUIDA * dt
            self.dir_mira = d.normalize()
            if self._t_huida <= 0:
                self.estado = "deambula"
                self._espera = random.uniform(1.5, 4.0)
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(30, 90)
                self._espera = random.uniform(1.5, 4.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * JABALI_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-8, 8):
            pygame.draw.line(pantalla, (60, 46, 36), (px + lx, py + 3), (px + lx, py + 12), 2)
        pygame.draw.ellipse(pantalla, c, (px - 13, py - 7, 26, 15))
        nx = px + s * 13
        pygame.draw.circle(pantalla, c, (nx, py - 1), 6)
        pygame.draw.circle(pantalla, (40, 30, 24), (nx + s * 4, py - 1), 2)
        pygame.draw.line(pantalla, (225, 220, 205), (nx + s * 3, py + 1), (nx + s * 7, py - 3), 2)
        ojo = (230, 60, 50) if self.estado == "rabia" else (25, 20, 16)
        pygame.draw.circle(pantalla, ojo, (nx, py - 3), 1)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = 26; fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 13, py - 20, w, 3))
            pygame.draw.rect(pantalla, (210, 120, 70), (px - 13, py - 20, fw, 3))


# =====================================================================
# ZORRO  (neutral; muerde si lo acorralan/golpean; caza conejos; Paso 0)
# =====================================================================
ZORRO_MAX = 15
ZORRO_RADIO = 9
ZORRO_MASA = 6.0
ZORRO_VIDA = (15, 30)
ZORRO_DANO = (5, 10)
ZORRO_DIST = 120.0
ZORRO_ACORRALA = 45.0
ZORRO_VEL_PASEO = 42.0
ZORRO_VEL = 150.0
ZORRO_HAMBRE = 300.0             # 5 min
ZORRO_RANGO_CAZA = 450.0
ZORRO_ROBO = 0.30
ZORRO_PASO0_PROB = 0.30
ZORRO_PASO0_DUR = 5.0
ZORRO_PASO0_CD = 10.0            # recarga de Paso 0
ZORRO_VISTA = 500.0             # a esta distancia dejas de ser su objetivo (sales de su pantalla)
ZORRO_MORDIDA_CD = 1.2
ZORRO_COLORES = [(192, 110, 55), (172, 96, 46), (206, 126, 66)]


class Zorro(AnimalCombatible):
    def __init__(self, x, y):
        self.posicion = pygame.Vector2(x, y)
        self.radio = ZORRO_RADIO
        self.masa = ZORRO_MASA
        self.color = random.choice(ZORRO_COLORES)
        self.vida = random.randint(*ZORRO_VIDA)
        self.vida_max = self.vida
        self.vivo = True
        self.estado = "ronda"            # ronda / caza / muerde
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self.vel_mult = 1.0
        self._hambre_t = random.uniform(0, ZORRO_HAMBRE)
        self.hambriento = False
        self.presa = None
        self.invisible = False
        self._paso0_t = 0.0
        self._paso0_cd = 0.0
        self._presa_es_conejo = False
        self._agredido = False
        self._cd_mordida = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def _robar_de(self, objetivo, es_conejo=False):
        if self.presa is objetivo:
            return
        self._liberar_robo()
        self.presa = objetivo
        self._presa_es_conejo = es_conejo
        self.vel_mult = 1.0 + ZORRO_ROBO
        if hasattr(objetivo, "vel_mult"):
            objetivo.vel_mult = 1.0 - ZORRO_ROBO

    def _mantener_robo(self, objetivo):
        if not hasattr(objetivo, "vel_mult") and hasattr(objetivo, "ralentizacion"):
            objetivo.ralentizacion = max(getattr(objetivo, "ralentizacion", 0.0), ZORRO_ROBO)
            if hasattr(objetivo, "tiempo_ralentizacion"):
                objetivo.tiempo_ralentizacion = max(getattr(objetivo, "tiempo_ralentizacion", 0.0), 0.3)

    def _liberar_robo(self):
        if self.presa is not None and hasattr(self.presa, "vel_mult"):
            self.presa.vel_mult = 1.0
        self.presa = None
        self._presa_es_conejo = False
        self.vel_mult = 1.0

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self._agredido = True
        self._cd_mordida = 0.0
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
            self._liberar_robo()
        return cantidad

    def actualizar(self, dt, jugador, amenazas=None, conejos=()):
        self._tick_efectos(dt)
        if not self.vivo:
            self._liberar_robo()
            return
        if self.inmovilizado is not None:
            return
        if amenazas is None:
            amenazas = (jugador,) if getattr(jugador, "detectable", True) else ()

        # Paso 0: invisibilidad activa y recarga (CD de 10 s).
        if self.invisible:
            self._paso0_t -= dt
            if self._paso0_t <= 0:
                self.invisible = False
                self._paso0_cd = ZORRO_PASO0_CD
        else:
            self._paso0_cd -= dt

        self._hambre_t += dt
        self.hambriento = self._hambre_t >= ZORRO_HAMBRE
        self._cd_mordida -= dt

        amenaza = min(amenazas, key=lambda o: (o.posicion - self.posicion).length_squared()) if amenazas else None
        d_amen = (amenaza.posicion - self.posicion).length() if amenaza is not None else float("inf")

        # El robo es permanente: la presa se mantiene hasta morir, esconderse o salir de la vista.
        if self.presa is not None:
            viva = getattr(self.presa, "vivo", True)
            escondida = getattr(self.presa, "estado", None) == "escondido"
            lejos = (self.presa.posicion - self.posicion).length() > ZORRO_VISTA
            indetectable = (not self._presa_es_conejo) and (not getattr(self.presa, "detectable", True))
            if (not viva) or escondida or lejos or indetectable:
                mad = getattr(self.presa, "madriguera", None) if self._presa_es_conejo else None
                self._liberar_robo()
                if mad is not None:
                    away = self.posicion - mad.centro
                    paso = away.normalize() * 160 if away.length() > 1 else pygame.Vector2(1, 0) * 160
                    self.destino = self.posicion + paso
                    self._espera = random.uniform(2.0, 3.5)
                    self.estado = "ronda"

        # Conejo-presa (cuando tiene hambre).
        presa_conejo = None
        if self.hambriento and conejos:
            vivos = [c for c in conejos if c.vivo and c.estado != "escondido"]
            if vivos:
                cand = min(vivos, key=lambda c: (c.posicion - self.posicion).length_squared())
                if (cand.posicion - self.posicion).length() <= ZORRO_RANGO_CAZA:
                    presa_conejo = cand

        # Paso 0: un tiro del 30% al detectar algo si el CD esta listo; si falla, reinicia los 10 s.
        detecta = (d_amen < ZORRO_DIST * 1.5) or (presa_conejo is not None) or (self.presa is not None)
        if not self.invisible and self._paso0_cd <= 0 and detecta:
            if random.random() < ZORRO_PASO0_PROB:
                self.invisible = True
                self._paso0_t = ZORRO_PASO0_DUR
            else:
                self._paso0_cd = ZORRO_PASO0_CD

        # Si lo acorralan o lo golpearon, esa amenaza pasa a ser su objetivo (robo permanente).
        if amenaza is not None and (d_amen < ZORRO_ACORRALA or self._agredido):
            self._robar_de(amenaza, es_conejo=False)
        self._agredido = False

        # 1) Objetivo-amenaza (jugador/sombra): muerde si esta cerca, huye y sigue robando.
        if self.presa is not None and not self._presa_es_conejo:
            self._mantener_robo(self.presa)
            dp = (self.presa.posicion - self.posicion).length()
            if self._cd_mordida <= 0 and dp < ZORRO_ACORRALA + 6:
                self._cd_mordida = ZORRO_MORDIDA_CD
                dano = random.randint(*ZORRO_DANO)
                if hasattr(self.presa, "recibir_dano"):
                    self.presa.recibir_dano(dano, "fisico", self.presa.posicion - self.posicion)
            d = self.posicion - self.presa.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * ZORRO_VEL * self.vel_mult * dt
            self.dir_mira = d.normalize()
            return

        # 2) Hambriento: caza al conejo (lo mata al contacto y se llena).
        if presa_conejo is not None:
            self.estado = "caza"
            self._robar_de(presa_conejo, es_conejo=True)
            d = presa_conejo.posicion - self.posicion
            dist = d.length()
            if dist <= self.radio + presa_conejo.radio + 2:
                presa_conejo.vivo = False
                self._liberar_robo()
                self._hambre_t = 0.0
                self.hambriento = False
                self.estado = "ronda"
            elif dist > 0:
                self.posicion += d.normalize() * ZORRO_VEL * self.vel_mult * dt
                self.dir_mira = d.normalize()
            return

        # 3) Ronda: mantiene distancia de la amenaza o deambula.
        if d_amen < ZORRO_DIST:
            d = self.posicion - amenaza.posicion
            if d.length() < 1:
                d = pygame.Vector2(1, 0)
            self.posicion += d.normalize() * ZORRO_VEL_PASEO * 1.4 * dt
            self.dir_mira = d.normalize()
        else:
            self._espera -= dt
            d = self.destino - self.posicion
            if self._espera <= 0:
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(40, 120)
                self._espera = random.uniform(1.0, 3.0)
            elif d.length() > 3:
                self.posicion += d.normalize() * ZORRO_VEL_PASEO * dt
                self.dir_mira = d.normalize()

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo or self.invisible:     # Paso 0: completamente invisible
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        for lx in (-5, 5):
            pygame.draw.line(pantalla, (120, 70, 35), (px + lx, py + 2), (px + lx, py + 9), 2)
        pygame.draw.ellipse(pantalla, c, (px - 9, py - 4, 18, 9))
        nx = px + s * 9
        pygame.draw.circle(pantalla, c, (nx, py - 2), 4)
        pygame.draw.polygon(pantalla, c, [(nx - 2, py - 5), (nx - 1, py - 9), (nx + 2, py - 5)])
        pygame.draw.polygon(pantalla, c, [(nx + 1, py - 5), (nx + 3, py - 9), (nx + 4, py - 5)])
        pygame.draw.circle(pantalla, (20, 16, 12), (nx + s * 2, py - 2), 1)
        pygame.draw.circle(pantalla, (245, 240, 235), (px - s * 9, py), 3)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = 18; fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - 9, py - 14, w, 3))
            pygame.draw.rect(pantalla, (120, 200, 90), (px - 9, py - 14, fw, 3))


# =====================================================================
# LOBOS EN MANADA  (hostiles; cazan al jugador/sombras y, con hambre, presas)
# =====================================================================
LOBO_MANADAS = 7
LOBO_POR_MANADA = 4
LOBO_VIDA = 25
LOBO_VIDA_ALFA = 40
LOBO_DANO = 8
LOBO_DANO_ALFA = 15
LOBO_DESANGRADO = 0.10
LOBO_DESANGRADO_ALFA = 0.30
LOBO_DETECCION = 250.0
LOBO_PIERDE = 600.0              # pierde el rastro si te alejas mas
LOBO_RANGO_CAZA = 450.0
LOBO_HAMBRE = 360.0             # 6 min
LOBO_RADIO = 10
LOBO_RADIO_ALFA = 12
LOBO_MASA = 8.0
LOBO_VEL = 165.0
LOBO_VEL_RETIRADA = 210.0
LOBO_VEL_PASEO = 40.0
LOBO_MORDIDA_CD = 1.0
LOBO_COLOR = [(90, 92, 100), (76, 78, 86), (108, 110, 118)]
LOBO_COLOR_ALFA = (58, 60, 70)


class Lobo(AnimalCombatible):
    def __init__(self, x, y, manada, alfa=False):
        self.posicion = pygame.Vector2(x, y)
        self.manada = manada
        self.es_alfa = alfa
        self.radio = LOBO_RADIO_ALFA if alfa else LOBO_RADIO
        self.masa = LOBO_MASA
        self.color = LOBO_COLOR_ALFA if alfa else random.choice(LOBO_COLOR)
        self.vida = LOBO_VIDA_ALFA if alfa else LOBO_VIDA
        self.vida_max = self.vida
        self.dano = LOBO_DANO_ALFA if alfa else LOBO_DANO
        self.prob_desangrado = LOBO_DESANGRADO_ALFA if alfa else LOBO_DESANGRADO
        self.vivo = True
        self.destino = pygame.Vector2(self.posicion)
        self._espera = random.uniform(1.0, 3.0)
        self._cd_mordida = 0.0
        self.dir_mira = pygame.Vector2(1, 0)
        self._init_combate()

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        if not self.vivo:
            return 0
        self.vida -= cantidad
        self.manada.alertada = True      # al ser agredido, la manada se alerta
        if self.vida <= 0:
            self.vida = 0
            self.vivo = False
        return cantidad

    def _mover_hacia(self, objetivo_pos, vel, dt):
        d = objetivo_pos - self.posicion
        if d.length() > 0:
            self.posicion += d.normalize() * vel * dt
            self.dir_mira = d.normalize()
        return d.length()

    def _morder(self, objetivo):
        if self._cd_mordida > 0:
            return
        self._cd_mordida = LOBO_MORDIDA_CD
        if hasattr(objetivo, "recibir_dano"):
            objetivo.recibir_dano(self.dano, "fisico", objetivo.posicion - self.posicion)
        if random.random() < self.prob_desangrado and hasattr(objetivo, "desangrado"):
            aplicar_desangrado(objetivo)

    def dibujar(self, pantalla, desplazamiento):
        if not self.vivo:
            return
        px = round(self.posicion.x - desplazamiento[0]); py = round(self.posicion.y - desplazamiento[1])
        c = self.color
        s = 1 if self.dir_mira.x >= 0 else -1
        rr = self.radio
        for lx in (-rr + 2, rr - 2):
            pygame.draw.line(pantalla, (58, 60, 68), (px + lx, py + 2), (px + lx, py + rr), 2)
        pygame.draw.ellipse(pantalla, c, (px - rr, py - rr + 3, rr * 2, rr + 4))
        nx = px + s * rr
        pygame.draw.circle(pantalla, c, (nx, py - 1), rr - 3)
        pygame.draw.polygon(pantalla, c, [(nx - 2, py - 4), (nx - 1, py - 8), (nx + 2, py - 4)])
        pygame.draw.polygon(pantalla, c, [(nx + 1, py - 4), (nx + 3, py - 8), (nx + 4, py - 4)])
        ojo = (235, 200, 60) if self.es_alfa else (210, 210, 225)
        pygame.draw.circle(pantalla, ojo, (nx + s * 2, py - 1), 1)
        pygame.draw.circle(pantalla, (235, 235, 240), (px - s * rr, py + 2), 2)
        if self.es_alfa:
            pygame.draw.circle(pantalla, (235, 200, 60), (px, py - rr - 2), 2)
        if self.inmovilizado is not None:
            pygame.draw.circle(pantalla, (200, 200, 210), (px, py), self.radio + 5, 1)
        if self.vida < self.vida_max:
            w = self.radio * 2
            fw = int(w * self.vida / self.vida_max)
            pygame.draw.rect(pantalla, (40, 30, 25), (px - self.radio, py - self.radio - 8, w, 3))
            col = (235, 160, 60) if self.es_alfa else (120, 200, 90)
            pygame.draw.rect(pantalla, col, (px - self.radio, py - self.radio - 8, fw, 3))


class Manada:
    def __init__(self, centro):
        self.centro = pygame.Vector2(centro)
        self.alertada = False
        self._hambre_t = random.uniform(0, LOBO_HAMBRE)
        self.lobos = []
        for i in range(LOBO_POR_MANADA):
            off = pygame.Vector2(random.uniform(-45, 45), random.uniform(-45, 45))
            self.lobos.append(Lobo(centro.x + off.x, centro.y + off.y, self, alfa=(i == 0)))

    def vivos(self):
        return [l for l in self.lobos if l.vivo]

    def actualizar(self, dt, jugador, amenazas, presas):
        vivos = self.vivos()
        if not vivos:
            return
        self._hambre_t += dt
        hambriento = self._hambre_t >= LOBO_HAMBRE

        # Objetivo: la amenaza (jugador detectable o sombra) mas cercana a cualquier lobo.
        objetivo = None
        if amenazas:
            objetivo = min(amenazas, key=lambda o: min((o.posicion - l.posicion).length_squared() for l in vivos))
            dmin = min((objetivo.posicion - l.posicion).length() for l in vivos)
            if self.alertada:
                if dmin > LOBO_PIERDE:
                    self.alertada = False
                    objetivo = None
            elif dmin < LOBO_DETECCION:
                self.alertada = True
            else:
                objetivo = None
        else:
            self.alertada = False

        retirada = len(vivos) == 1

        presa = None
        if hambriento and not self.alertada and presas:
            c0 = vivos[0].posicion
            cand = min(presas, key=lambda a: (a.posicion - c0).length_squared())
            if (cand.posicion - c0).length() <= LOBO_RANGO_CAZA:
                presa = cand

        for l in vivos:
            l._tick_efectos(dt)
            if not l.vivo or l.inmovilizado is not None:
                continue
            l._cd_mordida -= dt
            if retirada:
                d = l.posicion - jugador.posicion
                if d.length() < 1:
                    d = pygame.Vector2(1, 0)
                l.posicion += d.normalize() * LOBO_VEL_RETIRADA * dt
                l.dir_mira = d.normalize()
            elif self.alertada and objetivo is not None:
                dist = l._mover_hacia(objetivo.posicion, LOBO_VEL, dt)
                if dist <= l.radio + getattr(objetivo, "radio", 10) + 2:
                    l._morder(objetivo)
            elif presa is not None:
                dist = l._mover_hacia(presa.posicion, LOBO_VEL, dt)
                if dist <= l.radio + presa.radio + 2:
                    presa.vivo = False
                    self._hambre_t = 0.0      # una presa sacia a toda la manada
                    presa = None
            else:
                l._espera -= dt
                d = l.destino - l.posicion
                if l._espera <= 0:
                    ang = random.uniform(0, math.tau)
                    l.destino = l.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(40, 120)
                    l._espera = random.uniform(1.0, 3.0)
                elif d.length() > 3:
                    l.posicion += d.normalize() * LOBO_VEL_PASEO * dt
                    l.dir_mira = d.normalize()
