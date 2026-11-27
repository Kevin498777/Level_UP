"""Limite del mundo: un cuadrado (Fase 2 del plan de NPC, decision del 26/11/2026).

El mapa es un cuadrado de LADO_MUNDO px (la misma superficie que el antiguo circulo de radio
10 000) con la casa del spawn en el centro y una franja oscura de MARGEN_MUNDO px alrededor.
Todo lo que antes miraba el circulo (movimiento, empuje, proyectiles, cuchillas, generacion,
fauna, vendedores, sacar_a_hueco_libre, dibujo del borde) pregunta aqui: es el unico sitio que
define la forma del mundo.
"""
import random

import pygame

LADO_MUNDO = 17700          # px: 17 700^2 ~ pi * 10 000^2 (misma superficie que el circulo antiguo)
MARGEN_MUNDO = 150          # franja oscura fuera del mapa (se ve al llegar al borde)
BORDE_LIBRE = 300           # sin obstaculos a menos de esto del borde (Anexo E del plan de NPC)


class LimiteMundo:
    """Cuadrado de lado 'lado' centrado en 'centro' (coordenadas del mundo)."""

    def __init__(self, lado=LADO_MUNDO, margen=MARGEN_MUNDO, centro=None):
        self.lado = lado
        self.mitad = lado / 2.0
        self.tamano = lado + margen * 2                     # lienzo completo (mapa + franja)
        # Por defecto el mapa empieza en (0, 0) con su franja; las pruebas pueden fijar el centro
        self.centro = pygame.Vector2(centro) if centro is not None else pygame.Vector2(self.tamano / 2.0, self.tamano / 2.0)
        self.rect = pygame.Rect(round(self.centro.x - self.mitad), round(self.centro.y - self.mitad), lado, lado)

    @property
    def area(self):
        return self.lado * self.lado

    def dentro(self, p, margen=0.0):
        """True si el punto esta dentro del cuadrado con 'margen' px de holgura hasta el borde
        (un margen negativo deja salir un poco: p. ej. el radio de un proyectil)."""
        limite = self.mitad - margen
        return abs(p[0] - self.centro.x) <= limite and abs(p[1] - self.centro.y) <= limite

    def acotar(self, p, margen=0.0):
        """El punto mas cercano dentro del cuadrado con 'margen' de holgura (un Vector2 nuevo)."""
        limite = max(0.0, self.mitad - margen)
        return pygame.Vector2(min(max(p[0], self.centro.x - limite), self.centro.x + limite),
                              min(max(p[1], self.centro.y - limite), self.centro.y + limite))

    def distancia_al_borde(self, p):
        return self.mitad - max(abs(p[0] - self.centro.x), abs(p[1] - self.centro.y))

    def punto_al_azar(self, margen=0.0, rng=random):
        """Punto uniforme dentro del cuadrado, a 'margen' px o mas del borde."""
        limite = max(0.0, self.mitad - margen)
        return pygame.Vector2(self.centro.x + rng.uniform(-limite, limite),
                              self.centro.y + rng.uniform(-limite, limite))

    def relativo(self, p):
        """Coordenadas normalizadas (-1..1): u hacia el este, v hacia el sur."""
        return (p[0] - self.centro.x) / self.mitad, (p[1] - self.centro.y) / self.mitad


LIMITE = LimiteMundo()
