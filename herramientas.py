import pygame
import math

# -----------------------------
# CLASE BASE DE HERRAMIENTAS
# -----------------------------
class HerramientaBase:
    """
    Base de todas las herramientas (espadas).

    Escalado por nivel (1 a nivel_max):
    - multiplicador de daño = mult_dano_base + mult_dano_por_nivel * nivel
    - debuff de velocidad   = debuff_base - debuff_reduccion_por_nivel * nivel  (magnitud, mínimo 0)
    - durabilidad máxima     = durabilidad_base + durabilidad_por_nivel * nivel

    Durabilidad: cada golpe que hace daño gasta 1 punto. Al llegar a 0 la herramienta
    se ROMPE: pierde todos sus niveles (vuelve a nivel 1) y queda inutilizable hasta
    que se sube de nivel, momento en el que recupera toda su durabilidad.
    """

    def __init__(self, nombre, tecla, tecla_str,
                 mult_dano_base, mult_dano_por_nivel,
                 debuff_base, debuff_reduccion_por_nivel,
                 durabilidad_base, durabilidad_por_nivel,
                 inclinacion, factor_largo, factor_ancho=1.0, nivel_max=5):
        self.nombre = nombre
        self.tecla = tecla
        self.tecla_str = tecla_str
        self.activa = False
        self.cooldown_toggle = 0.5  # 0.5s de tiempo entre sacar y guardar
        self.tiempo_transcurrido_toggle = 0.5
        self.hitbox = None          # Hitbox de colisión (pygame.Rect)

        # Progresión
        self.nivel = 1
        self.nivel_max = nivel_max
        self.roto = False
        self.es_escudo = False       # True solo en el Escudo (protege, no golpea)
        self.empuje_al_bloquear = 0  # Puntos de empuje que recibe el portador al bloquear con él

        # Parámetros de escalado
        self.mult_dano_base = mult_dano_base
        self.mult_dano_por_nivel = mult_dano_por_nivel
        self.debuff_base = debuff_base                          # magnitud positiva (0.20 = -20%)
        self.debuff_reduccion_por_nivel = debuff_reduccion_por_nivel
        self.durabilidad_base = durabilidad_base
        self.durabilidad_por_nivel = durabilidad_por_nivel

        # Geometría y colores de la hoja
        self.inclinacion = inclinacion          # Grados de apertura de la punta
        self.factor_largo = factor_largo        # 1.0 = largo base de la Espada Ligera
        self.factor_ancho = factor_ancho        # 1.0 = grosor base de la hoja (solo estético)
        self.color_hoja = (175, 182, 195)       # Gris acero
        self.color_empunadura = (95, 102, 115)  # Gris oscuro
        self.color_filo = (225, 230, 242)       # Brillo metálico

        # Valores derivados del nivel (daño, debuff, durabilidad)
        self._aplicar_nivel(reparar=True)

    # -----------------------------
    # PROGRESIÓN Y DURABILIDAD
    # -----------------------------
    def _aplicar_nivel(self, reparar=False):
        """Recalcula daño, debuff y durabilidad máxima según el nivel actual."""
        self.multiplicador_dano = round(self.mult_dano_base + self.mult_dano_por_nivel * self.nivel, 3)
        # Si el valor es negativo, deja de ser debuff y pasa a ser un buff de velocidad (ej. dagas a nivel máx)
        self.debuff_velocidad = round(self.debuff_base - self.debuff_reduccion_por_nivel * self.nivel, 3)
        self.durabilidad_max = round(self.durabilidad_base + self.durabilidad_por_nivel * self.nivel)
        if reparar:
            self.durabilidad = self.durabilidad_max

    def subir_nivel(self):
        """
        Sube la herramienta un nivel y recupera toda su durabilidad.
        Si estaba rota, esto la repara (sube desde nivel 1).
        Devuelve True si cambió de nivel.
        """
        if self.roto:
            self.roto = False
            self.nivel = min(self.nivel + 1, self.nivel_max)
            self._aplicar_nivel(reparar=True)
            return True
        if self.nivel < self.nivel_max:
            self.nivel += 1
            self._aplicar_nivel(reparar=True)
            return True
        # Ya está a nivel máximo: al menos repara la durabilidad
        self._aplicar_nivel(reparar=True)
        return False

    def desgastar(self, cantidad=1):
        """Gasta durabilidad (llamar una vez por cada golpe que hace daño). Rompe al llegar a 0."""
        if self.roto:
            return
        self.durabilidad -= cantidad
        if self.durabilidad <= 0:
            self.durabilidad = 0
            self._romper()

    def _romper(self):
        """La herramienta se rompe: pierde todos los niveles y queda inutilizable hasta repararla."""
        self.roto = True
        self.nivel = 1
        self.activa = False
        self.hitbox = None

    def nivel_maximo(self):
        return self.nivel >= self.nivel_max and not self.roto

    # -----------------------------
    # USO
    # -----------------------------
    def toggle(self):
        """Alterna entre sacar y guardar la herramienta si ha pasado el cooldown de 0.5s."""
        if self.roto:
            return False  # Una herramienta rota no se puede sacar
        if self.tiempo_transcurrido_toggle >= self.cooldown_toggle:
            self.activa = not self.activa
            self.tiempo_transcurrido_toggle = 0.0
            if not self.activa:
                self.hitbox = None
            return True
        return False

    def actualizar(self, dt, jugador=None):
        """Actualiza el temporizador de cooldown y la hitbox."""
        if self.tiempo_transcurrido_toggle < self.cooldown_toggle:
            self.tiempo_transcurrido_toggle += dt

        if jugador and self.activa and not self.roto:
            self.actualizar_hitbox(jugador)
        else:
            self.hitbox = None

    def calcular_dano(self, jugador):
        """Daño proporcional a la fuerza actual del personaje por el multiplicador del nivel."""
        if self.roto:
            return 0.0
        return round(jugador.fuerza * self.multiplicador_dano, 2)

    # -----------------------------
    # GEOMETRÍA DE LA HOJA (común a todas las espadas)
    # -----------------------------
    def obtener_segmento(self, jugador, lado=1):
        """Calcula los extremos (pomo y punta) de la hoja en el flanco indicado (lado=1 derecha, -1 izquierda)."""
        pos_x = jugador.posicion.x
        pos_y = jugador.posicion.y
        radio = jugador.radio
        rad = math.radians(jugador.angulo)

        frente_x = math.sin(rad)
        frente_y = -math.cos(rad)
        derecha_x = math.cos(rad)
        derecha_y = math.sin(rad)

        distancia_flanco = radio + 6.0
        centro_esp_x = pos_x + (derecha_x * distancia_flanco * lado)
        centro_esp_y = pos_y + (derecha_y * distancia_flanco * lado)

        # Inclinar la hoja hacia afuera del flanco correspondiente
        inc = math.radians(self.inclinacion * lado)
        cos_i, sin_i = math.cos(inc), math.sin(inc)
        frente_x, frente_y, derecha_x, derecha_y = (
            frente_x * cos_i + derecha_x * sin_i,
            frente_y * cos_i + derecha_y * sin_i,
            derecha_x * cos_i - frente_x * sin_i,
            derecha_y * cos_i - frente_y * sin_i,
        )

        # El largo depende del factor de cada espada (Ligera=1.0, Larga=1.5, Mandoble=2.2)
        largo_hoja = max(24.0, radio * 1.35) * self.factor_largo
        mitad_largo = largo_hoja / 2.0

        punta_x = centro_esp_x + (frente_x * mitad_largo)
        punta_y = centro_esp_y + (frente_y * mitad_largo)

        pomo_x = centro_esp_x - (frente_x * mitad_largo)
        pomo_y = centro_esp_y - (frente_y * mitad_largo)

        return (pomo_x, pomo_y), (punta_x, punta_y), (frente_x, frente_y), (derecha_x, derecha_y), largo_hoja

    def actualizar_hitbox(self, jugador):
        """Calcula el área de colisión (hitbox rectangular) de la herramienta."""
        (pomo_x, pomo_y), (punta_x, punta_y), _, _, _ = self.obtener_segmento(jugador, 1)
        min_x = min(pomo_x, punta_x) - 4
        min_y = min(pomo_y, punta_y) - 4
        max_x = max(pomo_x, punta_x) + 4
        max_y = max(pomo_y, punta_y) + 4
        self.hitbox = pygame.Rect(
            round(min_x),
            round(min_y),
            round(max_x - min_x),
            round(max_y - min_y)
        )

    def obtener_hitboxes(self):
        """Lista de hitboxes activas de la herramienta (las dagas tienen dos)."""
        return [self.hitbox] if self.hitbox else []

    def _colores_actuales(self):
        """A nivel máximo la hoja toma un tono ligeramente dorado (sutil, sin brillar)."""
        if self.nivel_maximo():
            oro = (205, 175, 90)
            mezcla = lambda c: tuple(round(c[i] * 0.7 + oro[i] * 0.3) for i in range(3))
            return mezcla(self.color_hoja), mezcla(self.color_empunadura), mezcla(self.color_filo)
        return self.color_hoja, self.color_empunadura, self.color_filo

    def dibujar(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Dibuja la herramienta en el flanco derecho, girando con la dirección del personaje."""
        if not self.activa or self.roto:
            return
        self._dibujar_hoja(pantalla, jugador, 1, desplazamiento, self._colores_actuales())

    def _dibujar_hoja(self, pantalla, jugador, lado, desplazamiento, colores):
        """Dibuja una hoja en el flanco indicado (lado=1 derecha, -1 izquierda)."""
        color_hoja, color_empunadura, color_filo = colores

        (pomo_x, pomo_y), (punta_x, punta_y), (frente_x, frente_y), (derecha_x, derecha_y), largo_hoja = self.obtener_segmento(jugador, lado)
        pomo_x -= desplazamiento[0]
        pomo_y -= desplazamiento[1]
        punta_x -= desplazamiento[0]
        punta_y -= desplazamiento[1]

        # Grosores escalados por el factor de ancho (solo estético)
        fa = self.factor_ancho
        w_borde = max(1, round(4 * fa))
        w_hoja = max(1, round(3 * fa))
        w_filo = max(1, round(1 * fa))
        w_guarda = max(1, round(2 * fa))
        ancho_guarda = 3.5 * fa

        # 1. Borde de la hoja
        pygame.draw.line(
            pantalla,
            (18, 22, 28),
            (round(pomo_x + derecha_x), round(pomo_y + derecha_y)),
            (round(punta_x + derecha_x), round(punta_y + derecha_y)),
            w_borde
        )

        # 2. Hoja principal
        pygame.draw.line(
            pantalla,
            color_hoja,
            (round(pomo_x), round(pomo_y)),
            (round(punta_x), round(punta_y)),
            w_hoja
        )

        # 3. Filo con brillo metálico fino
        filo_inicio_x = pomo_x + (frente_x * 4.0)
        filo_inicio_y = pomo_y + (frente_y * 4.0)
        pygame.draw.line(
            pantalla,
            color_filo,
            (round(filo_inicio_x), round(filo_inicio_y)),
            (round(punta_x), round(punta_y)),
            w_filo
        )

        # 4. Empuñadura / Guarda
        guarda_centro_x = pomo_x + (frente_x * (largo_hoja * 0.25))
        guarda_centro_y = pomo_y + (frente_y * (largo_hoja * 0.25))

        g_izq_x = guarda_centro_x - (derecha_x * ancho_guarda)
        g_izq_y = guarda_centro_y - (derecha_y * ancho_guarda)
        g_der_x = guarda_centro_x + (derecha_x * ancho_guarda)
        g_der_y = guarda_centro_y + (derecha_y * ancho_guarda)

        pygame.draw.line(
            pantalla,
            color_empunadura,
            (round(g_izq_x), round(g_izq_y)),
            (round(g_der_x), round(g_der_y)),
            w_guarda
        )


# -----------------------------
# HERRAMIENTA: ESPADA LIGERA
# -----------------------------
class EspadaLigera(HerramientaBase):
    def __init__(self):
        super().__init__(
            nombre="Espada Ligera",
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=2.0, mult_dano_por_nivel=0.2,      # Daño = Fuerza x (2.2 a 3.0)
            debuff_base=0.20, debuff_reduccion_por_nivel=0.03,  # -17% a -5% de velocidad
            durabilidad_base=200, durabilidad_por_nivel=20,     # 220 a 300 de durabilidad
            inclinacion=15.0,
            factor_largo=1.2,    # 20% más grande
            factor_ancho=1.0,
        )


# -----------------------------
# HERRAMIENTA: ESPADA LARGA
# -----------------------------
class EspadaLarga(HerramientaBase):
    def __init__(self):
        super().__init__(
            nombre="Espada Larga",
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=3.0, mult_dano_por_nivel=0.4,      # Daño = Fuerza x (3.4 a 5.0)
            debuff_base=0.40, debuff_reduccion_por_nivel=0.06,  # -34% a -10% de velocidad
            durabilidad_base=180, durabilidad_por_nivel=10,     # 190 a 230 de durabilidad
            inclinacion=20.0,
            factor_largo=1.8,   # 50% base + 20% extra
            factor_ancho=1.10,  # 10% más ancha
        )


# -----------------------------
# HERRAMIENTA: MANDOBLE
# -----------------------------
class Mandoble(HerramientaBase):
    def __init__(self):
        super().__init__(
            nombre="Mandoble",
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=6.0, mult_dano_por_nivel=0.6,      # Daño = Fuerza x (6.6 a 9.0)
            debuff_base=0.80, debuff_reduccion_por_nivel=0.10,  # -70% a -30% de velocidad
            durabilidad_base=140, durabilidad_por_nivel=8,      # 148 a 180 de durabilidad
            inclinacion=20.0,
            factor_largo=2.64,  # 120% base + 20% extra
            factor_ancho=1.30,  # 30% más ancha
        )


# -----------------------------
# HERRAMIENTA: DAGAS SIMPLES (dos hojas, una por flanco)
# -----------------------------
class DagasSimples(HerramientaBase):
    def __init__(self):
        super().__init__(
            nombre="Dagas Simples",
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=1.25, mult_dano_por_nivel=0.25,       # Daño = Fuerza x (1.5 a 2.5)
            debuff_base=0.275, debuff_reduccion_por_nivel=0.075,  # -20% (nv1) ... +10% buff (nv5)
            durabilidad_base=87.5, durabilidad_por_nivel=62.5,    # 150 a 400 (compartida por las dos dagas)
            inclinacion=15.0,
            factor_largo=0.84,   # 30% más pequeñas que la Espada Ligera (1.2 * 0.7)
            factor_ancho=0.9,
        )
        self.hitbox_extra = None  # Segunda hoja (flanco izquierdo)

    def dibujar(self, pantalla, jugador, desplazamiento=(0, 0)):
        if not self.activa or self.roto:
            return
        colores = self._colores_actuales()
        self._dibujar_hoja(pantalla, jugador, 1, desplazamiento, colores)   # daga derecha
        self._dibujar_hoja(pantalla, jugador, -1, desplazamiento, colores)  # daga izquierda

    def _hitbox_lado(self, jugador, lado):
        (pomo_x, pomo_y), (punta_x, punta_y), _, _, _ = self.obtener_segmento(jugador, lado)
        min_x = min(pomo_x, punta_x) - 4
        min_y = min(pomo_y, punta_y) - 4
        max_x = max(pomo_x, punta_x) + 4
        max_y = max(pomo_y, punta_y) + 4
        return pygame.Rect(round(min_x), round(min_y), round(max_x - min_x), round(max_y - min_y))

    def actualizar_hitbox(self, jugador):
        self.hitbox = self._hitbox_lado(jugador, 1)
        self.hitbox_extra = self._hitbox_lado(jugador, -1)

    def obtener_hitboxes(self):
        return [h for h in (self.hitbox, self.hitbox_extra) if h]


# -----------------------------
# HERRAMIENTA: ESCUDO (protege, no golpea)
# -----------------------------
class Escudo(HerramientaBase):
    def __init__(self):
        super().__init__(
            nombre="Escudo",
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=0.0, mult_dano_por_nivel=0.0,         # No inflige daño
            debuff_base=0.40, debuff_reduccion_por_nivel=0.06,   # -34% a -10% de velocidad
            durabilidad_base=50, durabilidad_por_nivel=50,       # 100 a 300 de durabilidad
            inclinacion=0.0,
            factor_largo=2.64,   # mismo largo que el Mandoble
            factor_ancho=1.45,   # un poco más ancho que el Mandoble
        )
        self.es_escudo = True
        self.empuje_al_bloquear = 2   # El portador retrocede 2 de empuje al ser golpeado en el escudo
        self.color_hoja = (150, 158, 172)
        self.color_empunadura = (90, 97, 110)
        self.color_filo = (205, 212, 225)

    def calcular_dano(self, jugador):
        return 0.0  # El escudo protege, no golpea

    def recibir_golpe(self, jugador, direccion_desde_atacante):
        """Al ser golpeado en el escudo: se desgasta y empuja al portador hacia atrás."""
        if self.roto:
            return
        self.desgastar(1)
        jugador.aplicar_empuje(direccion_desde_atacante, self.empuje_al_bloquear)

    def dibujar(self, pantalla, jugador, desplazamiento=(0, 0)):
        if not self.activa or self.roto:
            return
        color_cara, color_borde_emp, color_brillo = self._colores_actuales()
        (pomo_x, pomo_y), (punta_x, punta_y), (frente_x, frente_y), (derecha_x, derecha_y), largo = self.obtener_segmento(jugador, 1)
        cx = (pomo_x + punta_x) / 2 - desplazamiento[0]
        cy = (pomo_y + punta_y) / 2 - desplazamiento[1]
        h = largo / 2.0
        w = 10.0 * self.factor_ancho

        def pt(f, d):
            return (round(cx + frente_x * f + derecha_x * d), round(cy + frente_y * f + derecha_y * d))

        puntos = [pt(h, 0), pt(h * 0.45, w), pt(-h * 0.2, w), pt(-h, 0), pt(-h * 0.2, -w), pt(h * 0.45, -w)]
        pygame.draw.polygon(pantalla, color_cara, puntos)
        pygame.draw.polygon(pantalla, (18, 22, 28), puntos, max(1, round(2 * self.factor_ancho)))
        # Umbo central (jefe del escudo)
        pygame.draw.circle(pantalla, color_brillo, (round(cx), round(cy)), max(2, round(w * 0.35)))


# -----------------------------
# CATÁLOGO DE HERRAMIENTAS DISPONIBLES
# -----------------------------
HERRAMIENTAS_DISPONIBLES = {
    "Espada Ligera": EspadaLigera,
    "Espada Larga": EspadaLarga,
    "Mandoble": Mandoble,
    "Dagas Simples": DagasSimples,
    "Escudo": Escudo,
}

def crear_herramienta(nombre):
    cls = HERRAMIENTAS_DISPONIBLES.get(nombre)
    if cls:
        return cls()
    return EspadaLigera()
