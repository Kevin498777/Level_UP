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
                 inclinacion, factor_largo, factor_ancho=1.0,
                 cadencia_base=1.0, cadencia_por_nivel=0.1, puntos_empuje=2, nivel_max=5):
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
        self.tipo_dano = "fisico"    # Las armas infligen daño físico
        self.empuje_al_bloquear = 0  # Puntos de empuje que recibe el portador al bloquear con él

        # Parámetros de escalado
        self.mult_dano_base = mult_dano_base
        self.mult_dano_por_nivel = mult_dano_por_nivel
        self.debuff_base = debuff_base                          # magnitud positiva (0.20 = -20%)
        self.debuff_reduccion_por_nivel = debuff_reduccion_por_nivel
        self.durabilidad_base = durabilidad_base
        self.durabilidad_por_nivel = durabilidad_por_nivel
        # Cadencia de ataque (golpes/seg): escala con el nivel del arma
        self.cadencia_base = cadencia_base
        self.cadencia_por_nivel = cadencia_por_nivel
        self.puntos_empuje = puntos_empuje          # Empuje fijo que inflige al golpear
        # Estado del golpe cuerpo a cuerpo
        self.tiempo_desde_golpe = 999.0             # Tiempo desde el ultimo golpe (recarga)
        self.golpeando = False                      # True durante la ventana activa del golpe
        self.tiempo_ventana_golpe = 0.0             # Cuenta atras de la ventana activa
        self.DURACION_VENTANA_GOLPE = 0.18          # Dura el golpe/animacion; la hitbox esta activa todo ese tiempo
        self.angulo_swing = 0.0                     # Grados de barrido del arco durante el golpe (0 = reposo)
        self.SWING_INICIO = 70.0                    # Angulo inicial del arco (grados)
        self.SWING_FIN = -40.0                      # Angulo final del arco (grados)
        self.enemigos_golpeados = set()             # ids de enemigos ya tocados en este golpe

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
        # Cadencia (golpes/seg) y recarga entre golpes (seg). Mas nivel = mas rapido.
        self.cadencia = round(self.cadencia_base + self.cadencia_por_nivel * self.nivel, 3)
        self.recarga_ataque = (1.0 / self.cadencia) if self.cadencia > 0 else float("inf")
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
        self.durabilidad = round(self.durabilidad - cantidad, 2)
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

        # Recarga de ataque y ventana activa del golpe
        self.tiempo_desde_golpe += dt
        if self.golpeando:
            self.tiempo_ventana_golpe -= dt
            if self.tiempo_ventana_golpe <= 0:
                self.golpeando = False
                self.angulo_swing = 0.0
                self.enemigos_golpeados.clear()
            else:
                # Progreso del arco (0 -> 1): la hoja barre de SWING_INICIO a SWING_FIN
                p = 1.0 - (self.tiempo_ventana_golpe / self.DURACION_VENTANA_GOLPE)
                p = max(0.0, min(1.0, p))
                self.angulo_swing = self.SWING_INICIO + (self.SWING_FIN - self.SWING_INICIO) * p

        if jugador and self.activa and not self.roto:
            self.actualizar_hitbox(jugador)
        else:
            self.hitbox = None

    def calcular_dano(self, jugador):
        """Daño proporcional a la fuerza actual del personaje por el multiplicador del nivel."""
        if self.roto:
            return 0.0
        # Anillo de fuerza y habilidades (Golpes electricos de Vestigios Miticos): +% al daño del arma
        bono = getattr(jugador, "bono_dano", 0.0) + getattr(jugador, "bono_dano_habilidades", 0.0)
        return round(jugador.fuerza * self.multiplicador_dano * (1.0 + bono), 2)

    def cadencia_efectiva(self, jugador=None):
        """Cadencia real (golpes/seg): la del arma por nivel mas el bonus del personaje."""
        bonus = getattr(jugador, "cadencia", 0.0) if jugador else 0.0
        return self.cadencia + bonus

    def recarga_efectiva(self, jugador=None):
        """Segundos entre golpes segun la cadencia efectiva."""
        ce = self.cadencia_efectiva(jugador)
        return (1.0 / ce) if ce > 0 else float("inf")

    def puede_atacar(self, jugador=None):
        """True si el arma puede iniciar un golpe (desenfundada, no rota, no escudo, recargada)."""
        return (self.activa and not self.roto and not self.es_escudo
                and self.cadencia_efectiva(jugador) > 0
                and self.tiempo_desde_golpe >= self.recarga_efectiva(jugador))

    def atacar(self, jugador=None):
        """Inicia un golpe si la cadencia lo permite. Abre la ventana activa de la hitbox."""
        if not self.puede_atacar(jugador):
            return False
        self.golpeando = True
        self.tiempo_ventana_golpe = self.DURACION_VENTANA_GOLPE
        self.tiempo_desde_golpe = 0.0
        self.angulo_swing = self.SWING_INICIO
        self.enemigos_golpeados.clear()
        return True

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

        # Barrido del arco (Fase 2): rota posicion y orientacion de la hoja durante el golpe
        if self.angulo_swing:
            sw = math.radians(self.angulo_swing * lado)
            cos_s, sin_s = math.cos(sw), math.sin(sw)
            frente_x, frente_y, derecha_x, derecha_y = (
                frente_x * cos_s + derecha_x * sin_s,
                frente_y * cos_s + derecha_y * sin_s,
                derecha_x * cos_s - frente_x * sin_s,
                derecha_y * cos_s - frente_y * sin_s,
            )

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

        # Destello breve al golpear (Fase 1; el arco llega en Fase 2)
        if self.golpeando:
            pygame.draw.line(
                pantalla,
                (255, 255, 255),
                (round(filo_inicio_x), round(filo_inicio_y)),
                (round(punta_x), round(punta_y)),
                max(1, w_filo + 1)
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
            cadencia_base=1.4, cadencia_por_nivel=0.075, puntos_empuje=8,
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
            cadencia_base=1.0, cadencia_por_nivel=0.06, puntos_empuje=12,
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
            cadencia_base=0.6, cadencia_por_nivel=0.04, puntos_empuje=20,
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
            cadencia_base=2.0, cadencia_por_nivel=0.125, puntos_empuje=4,
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
# Arco frontal que cubre el escudo desenfundado (grados totales, mitad a cada lado del frente)
ESCUDO_ARCO_BLOQUEO = 120.0
# Reducción del desgaste: del daño bloqueado, solo (1 - reducción) se resta a la durabilidad
ESCUDO_REDUCCION_NV1, ESCUDO_REDUCCION_NV_MAX = 0.20, 0.70
# Bonus pasivo a los máximos de escudo físico y mágico del portador (mientras no esté roto)
ESCUDO_BONUS_NV1, ESCUDO_BONUS_NV_MAX = 0.15, 0.30
# Empuje que el escudo aplica al atacante en cada bloqueo (mayor que el de cualquier arma: máx. 25)
ESCUDO_EMPUJE_BLOQUEO = 40
# Dibujo del escudo: banda curva delante del personaje que ocupa exactamente el arco de bloqueo
ESCUDO_SEPARACION = 7      # px entre el borde del cuerpo y el centro de la banda
ESCUDO_GROSOR = 6          # grosor de la banda en px


class Escudo(HerramientaBase):
    """
    Desenfundado, bloquea por completo los ataques que llegan por su arco frontal
    (ESCUDO_ARCO_BLOQUEO): golpes de arma, proyectiles y mordidas, físicos o mágicos. El
    portador no recibe daño ni efectos; el escudo pierde de durabilidad el daño bloqueado
    menos su reducción (20 % a nivel 1 -> 70 % a nivel 5), empuja al portador y repele al
    atacante con ESCUDO_EMPUJE_BLOQUEO. Se dibuja como una banda curva que ocupa justo su
    arco de bloqueo, para ver dónde cubre.
    No bloquea la Onda Sonora, el Aura Eléctrica, el terreno, el autodaño ni los efectos
    ya aplicados (esos ataques no consultan al escudo).
    Pasiva: mientras sea la herramienta del personaje y no esté roto (enfundado o no),
    sube sus escudos físico y mágico un 15 % (nivel 1) -> 30 % (nivel 5).
    """
    def __init__(self):
        super().__init__(
            nombre="Escudo",
            cadencia_base=0.0, cadencia_por_nivel=0.0, puntos_empuje=ESCUDO_EMPUJE_BLOQUEO,  # empuje al atacante al bloquear
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

    def _aplicar_nivel(self, reparar=False):
        super()._aplicar_nivel(reparar)
        t = (self.nivel - 1) / (self.nivel_max - 1)
        self.reduccion_desgaste = round(ESCUDO_REDUCCION_NV1 + (ESCUDO_REDUCCION_NV_MAX - ESCUDO_REDUCCION_NV1) * t, 4)
        self.bonus_escudos = round(ESCUDO_BONUS_NV1 + (ESCUDO_BONUS_NV_MAX - ESCUDO_BONUS_NV1) * t, 4)

    def calcular_dano(self, jugador):
        return 0.0  # El escudo protege, no golpea

    def actualizar_hitbox(self, jugador):
        self.hitbox = None   # su hitbox es el arco frontal (ver cubre), no un rectángulo de hoja

    def radio_arco(self, jugador):
        """Distancia del centro del personaje al centro de la banda del escudo."""
        return jugador.radio + ESCUDO_SEPARACION

    def cubre(self, jugador, punto):
        """True si el escudo, desenfundado y sin romper, cubre el punto (arco frontal)."""
        if not self.activa or self.roto:
            return False
        hacia = pygame.Vector2(punto) - jugador.posicion
        if hacia.length_squared() == 0:
            return True
        rad = math.radians(jugador.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        return frente.dot(hacia.normalize()) >= math.cos(math.radians(ESCUDO_ARCO_BLOQUEO / 2))

    def bloquear(self, jugador, cantidad, direccion_desde_atacante):
        """Bloquea un ataque entero: se desgasta el daño menos su reducción y empuja al portador."""
        if self.roto:
            return
        self.desgastar(round(cantidad * (1.0 - self.reduccion_desgaste), 2))
        jugador.aplicar_empuje(direccion_desde_atacante, self.empuje_al_bloquear)

    def puntos_arco(self, jugador, radio, pasos=12):
        """Puntos (mundo) del arco frontal que cubre el escudo a la distancia 'radio'."""
        mitad = ESCUDO_ARCO_BLOQUEO / 2
        puntos = []
        for i in range(pasos + 1):
            ang = math.radians(jugador.angulo - mitad + ESCUDO_ARCO_BLOQUEO * i / pasos)
            puntos.append((jugador.posicion.x + math.sin(ang) * radio, jugador.posicion.y - math.cos(ang) * radio))
        return puntos

    def dibujar(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Banda curva delante del personaje que ocupa exactamente el arco de bloqueo."""
        if not self.activa or self.roto:
            return
        color_cara, _, color_brillo = self._colores_actuales()
        ox, oy = desplazamiento
        r = self.radio_arco(jugador)
        exterior = [(x - ox, y - oy) for x, y in self.puntos_arco(jugador, r + ESCUDO_GROSOR / 2)]
        interior = [(x - ox, y - oy) for x, y in self.puntos_arco(jugador, r - ESCUDO_GROSOR / 2)]
        banda = exterior + interior[::-1]
        pygame.draw.polygon(pantalla, color_cara, banda)
        pygame.draw.polygon(pantalla, (18, 22, 28), banda, 2)
        pygame.draw.lines(pantalla, color_brillo, False, exterior, 1)   # brillo del borde exterior
        # Umbo (jefe del escudo) en el centro del frente
        rad = math.radians(jugador.angulo)
        umbo = (jugador.posicion.x + math.sin(rad) * r - ox, jugador.posicion.y - math.cos(rad) * r - oy)
        pygame.draw.circle(pantalla, color_brillo, (round(umbo[0]), round(umbo[1])), 3)
        pygame.draw.circle(pantalla, (18, 22, 28), (round(umbo[0]), round(umbo[1])), 3, 1)


# -----------------------------
# PROYECTIL: FLECHA DE ENERGÍA (ARCO)
# -----------------------------
class Flecha:
    """Flecha del Arco: proyectil recto de daño FISICO con aspecto de energia. El mundo la
    detiene en el primer enemigo que toca y las rocas la bloquean; atraviesa los arbustos.
    Si no choca con nada, al llegar al final de su alcance se queda clavada en el suelo
    TIEMPO_CLAVADA segundos solo como ambientacion (ya no hace daño)."""
    VELOCIDAD = 12.0        # px por frame (como los demas proyectiles)
    LARGO = 16              # largo dibujado de la flecha
    TIEMPO_CLAVADA = 3.0    # segundos que queda en el suelo al final del alcance
    radio = 3

    def __init__(self, x, y, direccion, dano, alcance, puntos_empuje, arco):
        self.posicion = pygame.Vector2(x, y)
        self.origen = pygame.Vector2(x, y)
        d = pygame.Vector2(direccion)
        self.direccion = d.normalize() if d.length_squared() > 0 else pygame.Vector2(0, -1)
        self.velocidad = self.VELOCIDAD
        self.dano = dano
        self.tipo_dano = "fisico"
        self.alcance = alcance
        self.puntos_empuje = puntos_empuje   # empuje fijo del arma al acertar
        self.arco = arco                     # se desgasta cuando la flecha hace daño
        self.activo = True
        self.clavada = False
        self.tiempo_clavada = 0.0
        self.hitbox = pygame.Rect(round(x - self.radio), round(y - self.radio), self.radio * 2, self.radio * 2)

    def actualizar(self, dt, limites_mundo):
        if self.clavada:
            self.tiempo_clavada -= dt
            if self.tiempo_clavada <= 0:
                self.activo = False
            return
        restante = self.alcance - (self.posicion - self.origen).length()
        paso = max(0.0, min(self.velocidad, restante))
        self.posicion += self.direccion * paso
        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)
        if paso >= restante:
            self.clavada = True
            self.tiempo_clavada = self.TIEMPO_CLAVADA
        min_x, min_y, max_x, max_y = limites_mundo
        if not (min_x <= self.posicion.x <= max_x and min_y <= self.posicion.y <= max_y):
            self.activo = False

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        punta = self.posicion - pygame.Vector2(desplazamiento)
        cola = punta - self.direccion * self.LARGO
        lateral = pygame.Vector2(-self.direccion.y, self.direccion.x)
        base_punta = punta - self.direccion * 5
        if self.clavada:
            col_cuerpo, col_punta = (90, 140, 160), (120, 175, 195)
        else:
            col_cuerpo, col_punta = (120, 230, 255), (235, 255, 255)
            pygame.draw.line(pantalla, (40, 120, 170), cola, punta, 4)    # resplandor de energia
        pygame.draw.line(pantalla, col_cuerpo, cola, punta, 2)
        pygame.draw.polygon(pantalla, col_punta, [punta, base_punta + lateral * 3, base_punta - lateral * 3])
        pygame.draw.line(pantalla, col_cuerpo, cola, cola - self.direccion * 3 + lateral * 3, 1)   # plumas
        pygame.draw.line(pantalla, col_cuerpo, cola, cola - self.direccion * 3 - lateral * 3, 1)


# -----------------------------
# HERRAMIENTA: ARCO (daño físico a distancia, dispara flechas cargadas)
# -----------------------------
class Arco(HerramientaBase):
    """Arco: no golpea cuerpo a cuerpo. Manteniendo [Espacio] se carga la flecha y al soltar
    se dispara segun los segundos COMPLETOS de carga (menos de 1 s no dispara, para evitar el
    spam; a partir de 5 s se queda al 100 % hasta soltar). Mientras carga, el portador va un
    10 % mas lento. Las flechas salen de un carcaj que se rellena comprando lotes de 10 con
    energia; las que no caben se pierden (y la energia se cobra entera)."""
    # Segundos completos de carga -> (alcance en px, porcentaje del daño del arma)
    TRAMOS_CARGA = {1: (100, 0.20), 2: (150, 0.40), 3: (200, 0.60), 4: (250, 0.80), 5: (300, 1.00)}
    CARGA_MAX = 5.0
    RALENTIZACION_CARGA = 0.10
    DURABILIDAD_POR_NIVEL = (100, 110, 120, 130, 150)
    CAPACIDAD_CARCAJ = (10, 15, 20, 25, 30)     # flechas maximas por nivel
    COSTO_LOTE_FLECHAS = (10, 15, 20, 25, 30)   # energia por cada lote de 10 flechas, por nivel
    FLECHAS_POR_LOTE = 10

    def __init__(self):
        self.flechas = 0   # se llena al final; _aplicar_nivel lo ajusta a la capacidad
        super().__init__(
            nombre="Arco",
            cadencia_base=0.0, cadencia_por_nivel=0.0, puntos_empuje=25,   # no golpea cuerpo a cuerpo
            tecla=pygame.K_1,
            tecla_str="1",
            mult_dano_base=3.75, mult_dano_por_nivel=1.25,      # Daño = Fuerza x (5.0 a 10.0)
            debuff_base=0.18, debuff_reduccion_por_nivel=0.03,  # -15% a -3% de velocidad
            durabilidad_base=0, durabilidad_por_nivel=0,        # usa DURABILIDAD_POR_NIVEL
            inclinacion=0.0,
            factor_largo=1.0,
        )
        self.cargando = False
        self.tiempo_carga = 0.0
        self.flechas = self.capacidad_carcaj   # empieza con el carcaj lleno
        self.color_hoja = (150, 105, 60)        # madera
        self.color_empunadura = (225, 225, 210) # cuerda
        self.color_filo = (120, 230, 255)       # flecha de energia

    def _aplicar_nivel(self, reparar=False):
        super()._aplicar_nivel(reparar=False)
        self.durabilidad_max = self.DURABILIDAD_POR_NIVEL[self.nivel - 1]
        if reparar:
            self.durabilidad = self.durabilidad_max
        self.capacidad_carcaj = self.CAPACIDAD_CARCAJ[self.nivel - 1]
        self.costo_flechas = self.COSTO_LOTE_FLECHAS[self.nivel - 1]
        self.flechas = min(self.flechas, self.capacidad_carcaj)

    def _romper(self):
        super()._romper()
        self.cancelar_carga()
        self._aplicar_nivel()   # vuelve a nivel 1: el carcaj se reduce a su capacidad

    def toggle(self):
        cambiado = super().toggle()
        if not self.activa:
            self.cancelar_carga()
        return cambiado

    def actualizar_hitbox(self, jugador):
        self.hitbox = None   # sin hitbox cuerpo a cuerpo (no golpea ni choca con espadas)

    # --- Carga y disparo ---
    @property
    def tramo_carga(self):
        """Segundos completos de carga (0 a 5)."""
        return int(min(self.tiempo_carga, self.CARGA_MAX))

    @property
    def ralentizacion_carga(self):
        return self.RALENTIZACION_CARGA if self.cargando else 0.0

    def iniciar_carga(self):
        """Empieza a tensar si esta desenfundado, sin romper y con flechas."""
        if self.activa and not self.roto and self.flechas > 0:
            self.cargando = True
            self.tiempo_carga = 0.0
            return True
        return False

    def cancelar_carga(self):
        self.cargando = False
        self.tiempo_carga = 0.0

    def actualizar(self, dt, jugador=None):
        super().actualizar(dt, jugador)
        if self.cargando:
            if not self.activa or self.roto:
                self.cancelar_carga()
            else:
                self.tiempo_carga = min(self.CARGA_MAX, self.tiempo_carga + dt)

    def soltar_carga(self, jugador):
        """Al soltar [Espacio]: devuelve la Flecha disparada, o None si la carga no llego a 1 s."""
        if not self.cargando:
            return None
        tramo = self.tramo_carga
        self.cancelar_carga()
        if tramo < 1 or self.flechas <= 0:
            return None
        alcance, porcentaje = self.TRAMOS_CARGA[tramo]
        self.flechas -= 1
        rad = math.radians(jugador.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        salida = jugador.posicion + frente * (jugador.radio + 4)
        dano = round(self.calcular_dano(jugador) * porcentaje, 2)
        return Flecha(salida.x, salida.y, frente, dano, alcance, self.puntos_empuje, self)

    def comprar_flechas(self, jugador):
        """Compra un lote de 10 flechas con energia. Las que no caben en el carcaj se pierden.
        No compra si el carcaj esta lleno o no hay energia suficiente."""
        if self.flechas >= self.capacidad_carcaj or jugador.energia < self.costo_flechas:
            return False
        jugador.energia -= self.costo_flechas
        self.flechas = min(self.capacidad_carcaj, self.flechas + self.FLECHAS_POR_LOTE)
        return True

    def dibujar(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Arco delante del personaje; la cuerda se tensa con la carga y muestra la flecha."""
        if not self.activa or self.roto:
            return
        color_madera, color_cuerda, color_flecha = self._colores_actuales()
        rad = math.radians(jugador.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        derecha = pygame.Vector2(math.cos(rad), math.sin(rad))
        centro = jugador.posicion - pygame.Vector2(desplazamiento) + frente * (jugador.radio + 4)
        media = max(12.0, jugador.radio * 0.9)   # media longitud del arco
        curva = media * 0.45
        puntos = []
        for i in range(9):
            t = -1.0 + 2.0 * i / 8
            puntos.append(centro + derecha * (t * media) + frente * (curva * (1 - t * t)))
        pygame.draw.lines(pantalla, (18, 22, 28), False, puntos, 5)
        pygame.draw.lines(pantalla, color_madera, False, puntos, 3)
        tension = (self.tiempo_carga / self.CARGA_MAX) * media * 0.6 if self.cargando else 0.0
        culata = centro - frente * tension
        pygame.draw.line(pantalla, color_cuerda, puntos[0], culata, 1)
        pygame.draw.line(pantalla, color_cuerda, culata, puntos[-1], 1)
        if self.cargando:
            punta = culata + frente * (Flecha.LARGO + curva + 4)
            pygame.draw.line(pantalla, color_flecha, culata, punta, 2)
            lateral = derecha * 3
            base = punta - frente * 5
            pygame.draw.polygon(pantalla, (235, 255, 255), [punta, base + lateral, base - lateral])


# -----------------------------
# CATÁLOGO DE HERRAMIENTAS DISPONIBLES
# -----------------------------
HERRAMIENTAS_DISPONIBLES = {
    "Espada Ligera": EspadaLigera,
    "Espada Larga": EspadaLarga,
    "Mandoble": Mandoble,
    "Dagas Simples": DagasSimples,
    "Escudo": Escudo,
    "Arco": Arco,
}

def crear_herramienta(nombre):
    cls = HERRAMIENTAS_DISPONIBLES.get(nombre)
    if cls:
        return cls()
    return EspadaLigera()
