"""Estructuras para el rendimiento (Fase 3 del plan de NPC).

- RejillaObstaculos: rocas, paredes, troncos y arbustos del mapa repartidos en celdas. Mover a un
  personaje o buscar lo que se ve solo pregunta por las celdas cercanas en vez de recorrer las
  ~1400 rocas y ~2100 arboles. Devuelve exactamente lo mismo que recorrer las listas (mismo orden),
  y se rehace sola cuando algo se destruye o reaparece (firma de las listas).
- RejillaDinamica: personajes y animales, rehecha una vez por fotograma, para "quien esta cerca".
- FondoPorTrozos: el fondo fijo (suelo, agua, rocas, troncos, pasto, flores, casa y puertas) se
  dibuja una vez en trozos de TROZO px y en cada fotograma solo se pegan los trozos visibles. Si
  algo del fondo cambia (roca destruida, lago evaporado) se redibujan solo sus trozos.
"""
from collections import OrderedDict

import pygame

CELDA_OBSTACULOS = 256          # px por celda de la rejilla de obstaculos
CELDA_DINAMICA = 256            # px por celda de la rejilla de personajes y animales
TROZO = 512                     # px de lado de cada trozo del fondo
TROZOS_EN_MEMORIA = 96          # trozos guardados a la vez (~1 MB cada uno); los mas viejos se tiran
MARGEN_TROZO = 128              # px dibujados de mas alrededor de cada trozo (luego se recortan)


def _celdas(rect, celda):
    """Celdas (i, j) que toca un rect."""
    i0, i1 = int(rect.left // celda), int((rect.right - 1) // celda)
    j0, j1 = int(rect.top // celda), int((rect.bottom - 1) // celda)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            yield i, j


def _caja_circulo(centro, radio):
    r = int(radio) + 1
    return pygame.Rect(int(centro.x) - r, int(centro.y) - r, r * 2 + 1, r * 2 + 1)


class RejillaObstaculos:
    """Indice espacial de los obstaculos del mapa (rocas y paredes, arbustos, arboles)."""

    def __init__(self, rocas, vegetacion, celda=CELDA_OBSTACULOS):
        self.rocas = rocas
        self.veg = vegetacion
        self.celda = celda
        self._firma = None
        self.reconstrucciones = 0

    def _firma_actual(self):
        return (len(self.rocas), len(self.veg.arbustos), len(self.veg.arboles), self.veg.version)

    def _asegurar(self):
        firma = self._firma_actual()
        if firma == self._firma:
            return
        self._firma = firma
        self.reconstrucciones += 1
        self._rocas, self._arbustos, self._arboles = {}, {}, {}
        for k, r in enumerate(self.rocas):
            for c in _celdas(r.rect, self.celda):
                self._rocas.setdefault(c, []).append(k)
        for k, a in enumerate(self.veg.arbustos):
            # el arbusto puede crecer (frutal): se reserva su tamano final
            for c in _celdas(_caja_circulo(a.centro, max(a.radio, getattr(a, "radio_final", a.radio))), self.celda):
                self._arbustos.setdefault(c, []).append(k)
        for k, t in enumerate(self.veg.arboles):
            for c in _celdas(t.rect, self.celda):            # la copa cubre al tronco
                self._arboles.setdefault(c, []).append(k)

    def _indices(self, tabla, zona):
        vistos = set()
        for c in _celdas(zona, self.celda):
            vistos.update(tabla.get(c, ()))
        return sorted(vistos)

    def rocas_en(self, zona):
        """Rocas y paredes que tocan 'zona' (mismo orden que la lista de rocas)."""
        self._asegurar()
        return [self.rocas[k] for k in self._indices(self._rocas, zona) if self.rocas[k].rect.colliderect(zona)]

    def arboles_en(self, zona):
        """Arboles cuya caja (copa) toca 'zona', en el orden de la lista."""
        self._asegurar()
        return [self.veg.arboles[k] for k in self._indices(self._arboles, zona) if self.veg.arboles[k].rect.colliderect(zona)]

    def arbustos_en(self, zona):
        """Arbustos cuya caja (con su tamano final) toca 'zona', en el orden de la lista."""
        self._asegurar()
        return [self.veg.arbustos[k] for k in self._indices(self._arbustos, zona)]

    def obstaculos_cerca(self, personaje, zona, con_troncos=True):
        """Igual que SistemaVegetacion.obstaculos_cerca (arbustos en los que no cabe y troncos que
        tocan 'zona', en ese orden) pero preguntando solo a las celdas de la zona."""
        self._asegurar()
        x0, y0, x1, y1 = zona.left, zona.top, zona.right, zona.bottom
        arbustos = self.veg.arbustos
        solidos = []
        for k in self._indices(self._arbustos, zona):
            a = arbustos[k]
            if (x0 - a.radio <= a.centro.x <= x1 + a.radio and y0 - a.radio <= a.centro.y <= y1 + a.radio
                    and not a.puede_entrar(personaje)):
                solidos.append((a.centro, a.radio))
        if con_troncos:
            arboles = self.veg.arboles
            for k in self._indices(self._arboles, zona):
                t = arboles[k]
                if (x0 - t.radio_tronco <= t.centro.x <= x1 + t.radio_tronco
                        and y0 - t.radio_tronco <= t.centro.y <= y1 + t.radio_tronco):
                    solidos.append((t.centro, t.radio_tronco))
        return solidos


class RejillaDinamica:
    """Personajes, animales y sombras por celdas; se rehace cada fotograma con 'rehacer'."""

    def __init__(self, celda=CELDA_DINAMICA):
        self.celda = celda
        self._celdas = {}

    def rehacer(self, entidades):
        self._celdas = {}
        for e in entidades:
            clave = (int(e.posicion.x // self.celda), int(e.posicion.y // self.celda))
            self._celdas.setdefault(clave, []).append(e)

    def cerca_de(self, punto, radio):
        """Entidades a 'radio' px o menos del punto."""
        res = []
        zona = pygame.Rect(int(punto[0] - radio), int(punto[1] - radio), int(radio * 2) + 1, int(radio * 2) + 1)
        p = pygame.Vector2(punto)
        for c in _celdas(zona, self.celda):
            for e in self._celdas.get(c, ()):
                if (e.posicion - p).length() <= radio:
                    res.append(e)
        return res


class FondoPorTrozos:
    """Fondo fijo pre-dibujado en trozos. 'dibujar_fondo(superficie, vista, desplazamiento)' es la
    misma funcion que dibuja ese fondo directamente en la pantalla."""

    def __init__(self, dibujar_fondo, trozo=TROZO, maximo=TROZOS_EN_MEMORIA):
        self.dibujar_fondo = dibujar_fondo
        self.trozo = trozo
        self.maximo = maximo
        self._trozos = OrderedDict()
        self._lienzo = None             # superficie de trabajo (trozo + margen), se reutiliza
        self.dibujados = 0              # trozos dibujados desde el principio (para las pruebas)

    def _trozo(self, i, j):
        clave = (i, j)
        sup = self._trozos.get(clave)
        if sup is None:
            # Se dibuja con MARGEN_TROZO de mas por cada lado y se queda el centro: asi nada se
            # recorta en el borde del trozo (pygame dibuja distinto un circulo cortado por el borde)
            m = MARGEN_TROZO
            if self._lienzo is None:
                self._lienzo = pygame.Surface((self.trozo + 2 * m, self.trozo + 2 * m))
            vista = pygame.Rect(i * self.trozo - m, j * self.trozo - m, self.trozo + 2 * m, self.trozo + 2 * m)
            self.dibujar_fondo(self._lienzo, vista, (vista.x, vista.y))
            sup = self._lienzo.subsurface((m, m, self.trozo, self.trozo)).copy()
            self.dibujados += 1
            self._trozos[clave] = sup
            if len(self._trozos) > self.maximo:
                self._trozos.popitem(last=False)
        else:
            self._trozos.move_to_end(clave)
        return sup

    def dibujar(self, pantalla, vista, desplazamiento):
        """Pega los trozos que tocan 'vista' (mundo) con el mismo 'desplazamiento' de siempre."""
        ox, oy = desplazamiento
        t = self.trozo
        for i in range(int(vista.left // t), int((vista.right - 1) // t) + 1):
            for j in range(int(vista.top // t), int((vista.bottom - 1) // t) + 1):
                pantalla.blit(self._trozo(i, j), (i * t - ox, j * t - oy))

    def invalidar(self, rect):
        """Algo del fondo cambio en 'rect' (mundo): sus trozos se redibujaran al verse."""
        if rect.width <= 0 or rect.height <= 0:
            return
        for c in _celdas(rect, self.trozo):
            self._trozos.pop(c, None)
