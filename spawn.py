"""Casa del spawn: una casa cuadrada en el centro del mapa con su jardin.

- El personaje empieza (y reaparece) en el centro del salon.
- Las paredes son solidas como las rocas (bloquean al jugador y los proyectiles) y nada las
  destruye: llevan `es_cueva`, igual que las rocas de las cuevas de oso (tampoco se cruzan con
  el Cuerpo de niebla de Espectro).
- El jardin es zona segura: ningun animal entra (fauna.ZONA_PROHIBIDA).
- El maniqui de pruebas esta en el jardin, al sur de la puerta.
- Los vendedores ambulantes vuelven aqui cuando se quedan sin anillos (entran por la puerta).
"""
import math
import pygame

LADO_CASA = 300                 # px de lado (exterior)
GROSOR_PARED = 16
ANCHO_PUERTA = 60               # hueco en la pared sur
RADIO_JARDIN = 350              # zona segura alrededor de la casa (sin fauna)
DISTANCIA_MANIQUI = 120         # px al sur de la pared sur
POSTES_VALLA = 72               # postes de la valla decorativa del jardin
ALFA_TECHO_DENTRO = 50          # el techo se vuelve casi transparente con el jugador dentro

COLOR_JARDIN = (44, 70, 46)
COLOR_JARDIN_BORDE = (60, 92, 58)
COLOR_VALLA = (140, 104, 64)
COLOR_CAMINO = (120, 108, 88)
COLOR_SUELO_CASA = (112, 82, 54)
COLOR_TABLAS = (96, 70, 46)
COLOR_PARED = (150, 128, 102)
COLOR_PARED_BORDE = (96, 78, 60)
COLOR_TECHO = (150, 58, 46)
COLOR_TECHO_TEJAS = (120, 44, 36)


class Pared:
    """Tramo de pared: rectangulo solido e indestructible (se trata como una roca de cueva)."""
    es_cueva = True             # nada la destruye y el Cuerpo de niebla no la atraviesa
    gigante = True

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)

    def dibujar(self, superficie, desplazamiento=(0, 0)):
        r = self.rect.move(-desplazamiento[0], -desplazamiento[1])
        pygame.draw.rect(superficie, COLOR_PARED, r)
        pygame.draw.rect(superficie, COLOR_PARED_BORDE, r, 2)


class Casa:
    def __init__(self, centro):
        self.centro = pygame.Vector2(centro)
        mitad = LADO_CASA // 2
        self.rect = pygame.Rect(round(self.centro.x) - mitad, round(self.centro.y) - mitad, LADO_CASA, LADO_CASA)
        self.interior = self.rect.inflate(-GROSOR_PARED * 2, -GROSOR_PARED * 2)
        r, g = self.rect, GROSOR_PARED
        hueco_izq = round(self.centro.x) - ANCHO_PUERTA // 2
        hueco_der = hueco_izq + ANCHO_PUERTA
        self.paredes = [
            Pared((r.left, r.top, r.width, g)),                                  # norte
            Pared((r.left, r.top, g, r.height)),                                 # oeste
            Pared((r.right - g, r.top, g, r.height)),                            # este
            Pared((r.left, r.bottom - g, hueco_izq - r.left, g)),                # sur (izquierda)
            Pared((hueco_der, r.bottom - g, r.right - hueco_der, g)),            # sur (derecha)
        ]
        self.puerta = pygame.Vector2(self.centro.x, r.bottom + 12)               # justo fuera de la puerta
        self.punto_maniqui = pygame.Vector2(self.centro.x, r.bottom + DISTANCIA_MANIQUI)
        self.radio_jardin = RADIO_JARDIN

    def contiene(self, punto):
        """True si el punto esta dentro del salon."""
        return self.interior.collidepoint(punto.x, punto.y)

    def en_jardin(self, punto, margen=0):
        return (pygame.Vector2(punto) - self.centro).length() <= self.radio_jardin + margen

    # ---- Dibujo
    def dibujar_suelo(self, pantalla, vista, desplazamiento):
        """Jardin (cesped, camino y valla) y suelo de tablas del salon (bajo todo lo demas)."""
        if not vista.colliderect(pygame.Rect(self.centro.x - RADIO_JARDIN, self.centro.y - RADIO_JARDIN,
                                             RADIO_JARDIN * 2, RADIO_JARDIN * 2)):
            return
        ox, oy = desplazamiento
        cx, cy = round(self.centro.x - ox), round(self.centro.y - oy)
        pygame.draw.circle(pantalla, COLOR_JARDIN, (cx, cy), RADIO_JARDIN)
        pygame.draw.circle(pantalla, COLOR_JARDIN_BORDE, (cx, cy), RADIO_JARDIN, 3)
        # Camino de piedras de la puerta al borde sur del jardin
        y = self.rect.bottom + 10
        while y < self.centro.y + RADIO_JARDIN - 10:
            pygame.draw.ellipse(pantalla, COLOR_CAMINO, (cx - 14, round(y - oy), 28, 14))
            y += 22
        # Valla baja decorativa (no bloquea): postes y travesanos, con un hueco frente al camino
        puntos = []
        for i in range(POSTES_VALLA):
            ang = i * math.tau / POSTES_VALLA
            if abs(math.atan2(math.sin(ang - math.pi / 2), math.cos(ang - math.pi / 2))) < 0.12:
                puntos.append(None)
                continue
            puntos.append((cx + math.cos(ang) * (RADIO_JARDIN - 4), cy + math.sin(ang) * (RADIO_JARDIN - 4)))
        for a, b in zip(puntos, puntos[1:] + puntos[:1]):
            if a is not None and b is not None:
                pygame.draw.line(pantalla, COLOR_VALLA, a, b, 2)
        for p in puntos:
            if p is not None:
                pygame.draw.circle(pantalla, COLOR_VALLA, (round(p[0]), round(p[1])), 3)
        # Suelo del salon
        interior = self.interior.move(-ox, -oy)
        pygame.draw.rect(pantalla, COLOR_SUELO_CASA, interior)
        for x in range(interior.left, interior.right, 24):
            pygame.draw.line(pantalla, COLOR_TABLAS, (x, interior.top), (x, interior.bottom), 1)

    def dibujar_techo(self, pantalla, vista, desplazamiento, jugador_dentro):
        """Techo encima de todo; casi transparente si el jugador esta dentro."""
        if not vista.colliderect(self.rect):
            return
        sup = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        alfa = ALFA_TECHO_DENTRO if jugador_dentro else 255
        sup.fill((*COLOR_TECHO, alfa))
        for y in range(0, self.rect.height, 18):
            pygame.draw.line(sup, (*COLOR_TECHO_TEJAS, alfa), (0, y), (self.rect.width, y), 2)
        pygame.draw.line(sup, (*COLOR_TECHO_TEJAS, alfa), (0, 0), (self.rect.width, self.rect.height), 3)
        pygame.draw.line(sup, (*COLOR_TECHO_TEJAS, alfa), (self.rect.width, 0), (0, self.rect.height), 3)
        pantalla.blit(sup, (self.rect.x - desplazamiento[0], self.rect.y - desplazamiento[1]))
