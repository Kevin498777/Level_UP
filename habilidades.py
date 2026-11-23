import pygame
import math
import random

# Pixeles de retroceso que provoca cada punto de empuje (compartido por personaje, invocaciones y maniqui)
PIXELES_POR_PUNTO_EMPUJE = 6

# Anulacion del escudo magico (pasiva de Cortar): el escudo queda en 0 y sin regenerar
# durante este tiempo; al terminar vuelve al valor que tenia justo despues del golpe.
DURACION_ANULACION_ESCUDOM = 8.0


def anular_escudo_magico(objetivo):
    """Anula el escudo magico del objetivo (si tiene). Si ya estaba anulado solo reinicia
    los 10 s y conserva el valor guardado."""
    if not hasattr(objetivo, "escudo_magico"):
        return
    if getattr(objetivo, "anulacion_escudo_magico", 0.0) <= 0:
        objetivo.escudo_magico_guardado = objetivo.escudo_magico
        objetivo.escudo_magico = 0.0
    objetivo.anulacion_escudo_magico = DURACION_ANULACION_ESCUDOM


# Ralentizacion (pasiva de Onda Sonora): resta un porcentaje de velocidad de movimiento.
# No se suma: se queda la mas fuerte y cada nuevo impacto reinicia la duracion.
DURACION_RALENTIZACION = 3.0


def aplicar_ralentizacion(objetivo, porcentaje):
    actual = getattr(objetivo, "ralentizacion", 0.0) if getattr(objetivo, "tiempo_ralentizacion", 0.0) > 0 else 0.0
    objetivo.ralentizacion = max(actual, porcentaje)
    objetivo.tiempo_ralentizacion = DURACION_RALENTIZACION


def actualizar_ralentizacion(objetivo, dt):
    """Descuenta la ralentizacion y la retira al terminar."""
    if getattr(objetivo, "tiempo_ralentizacion", 0.0) <= 0:
        return
    objetivo.tiempo_ralentizacion -= dt
    if objetivo.tiempo_ralentizacion <= 0:
        objetivo.tiempo_ralentizacion = 0.0
        objetivo.ralentizacion = 0.0


def actualizar_anulacion_escudo_magico(objetivo, dt):
    """Descuenta la anulacion; al terminar devuelve el escudo guardado. Devuelve True mientras
    el escudo siga anulado (en ese tiempo no debe regenerarse)."""
    if getattr(objetivo, "anulacion_escudo_magico", 0.0) <= 0:
        return False
    objetivo.anulacion_escudo_magico -= dt
    if objetivo.anulacion_escudo_magico <= 0:
        objetivo.anulacion_escudo_magico = 0.0
        objetivo.escudo_magico = min(objetivo.escudo_magico_max, objetivo.escudo_magico_guardado)
        return False
    return True

# -----------------------------
# CLASE PROYECTIL DE ENERGÍA (DISPARO VELOZ)
# -----------------------------
class ProyectilEnergia:
    def __init__(self, x, y, dx, dy, velocidad=10.0, dano=1.0, radio=6):
        self.posicion = pygame.Vector2(x, y)
        if dx != 0 or dy != 0:
            self.direccion = pygame.Vector2(dx, dy).normalize()
        else:
            self.direccion = pygame.Vector2(0, -1)

        self.velocidad = velocidad
        self.dano = dano
        self.tipo_dano = "magico"     # Daño mágico (consume energía)
        self.radio = radio
        self.activo = True
        self.hitbox = pygame.Rect(
            round(x - radio),
            round(y - radio),
            radio * 2,
            radio * 2
        )

    def actualizar(self, dt, limites_mundo):
        """Mueve la esfera en línea recta a velocidad 10 y actualiza su hitbox."""
        min_x, min_y, max_x, max_y = limites_mundo

        # Desplazamiento recto
        self.posicion += self.direccion * self.velocidad

        # Actualizar hitbox
        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)

        # Desactivar si sale de los límites del mundo
        if (self.posicion.x < min_x - self.radio or self.posicion.x > max_x + self.radio or
            self.posicion.y < min_y - self.radio or self.posicion.y > max_y + self.radio):
            self.activo = False

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        """Dibuja la esfera de energía con núcleo y resplandor (con offset de cámara)."""
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])

        # Resplandor exterior
        pygame.draw.circle(pantalla, (255, 235, 90), (px, py), self.radio + 2)
        # Núcleo blanco brillante
        pygame.draw.circle(pantalla, (255, 255, 255), (px, py), self.radio)
        # Centro energético dorado
        pygame.draw.circle(pantalla, (255, 175, 20), (px, py), max(2, self.radio - 2))


# -----------------------------
# CLASE PROYECTIL DE FUEGO (CARGA DE FUEGO)
# -----------------------------
class ProyectilFuego:
    """Esfera de fuego recta. Daño y radio dependen de la carga; al golpear aplica quemadura."""
    def __init__(self, x, y, dx, dy, velocidad, dano, radio, quemadura_dano=1, quemadura_duracion=5.0):
        self.posicion = pygame.Vector2(x, y)
        self.direccion = pygame.Vector2(dx, dy).normalize() if (dx != 0 or dy != 0) else pygame.Vector2(0, -1)
        self.velocidad = velocidad
        self.dano = dano
        self.tipo_dano = "magico"     # Daño mágico (consume energía)
        self.radio = radio
        self.quemadura_dano = quemadura_dano          # daño por segundo de la quemadura
        self.quemadura_duracion = quemadura_duracion  # segundos que dura la quemadura
        self.activo = True
        self.hitbox = pygame.Rect(round(x - radio), round(y - radio), radio * 2, radio * 2)

    def actualizar(self, dt, limites_mundo):
        min_x, min_y, max_x, max_y = limites_mundo
        self.posicion += self.direccion * self.velocidad
        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)
        if (self.posicion.x < min_x - self.radio or self.posicion.x > max_x + self.radio or
                self.posicion.y < min_y - self.radio or self.posicion.y > max_y + self.radio):
            self.activo = False

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        pygame.draw.circle(pantalla, (255, 110, 20), (px, py), self.radio + 2)          # resplandor
        pygame.draw.circle(pantalla, (255, 170, 55), (px, py), self.radio)              # cuerpo
        pygame.draw.circle(pantalla, (255, 240, 180), (px, py), max(2, self.radio - 3)) # núcleo


# -----------------------------
# CLASE PROYECTIL VENENOSO (DISPARO VENENOSO)
# -----------------------------
COLOR_VENENO = (90, 220, 90)          # Verde del disparo y del anillo de envenenado
COLOR_VENENO_NUCLEO = (150, 70, 200)  # Pequeña esfera morada en el centro del disparo


class ProyectilVeneno:
    """Esfera verde con núcleo morado. El impacto no hace daño ni empuja: solo envenena al
    primer enemigo que toca (veneno_total de daño mágico repartido en veneno_duracion s)."""
    def __init__(self, x, y, dx, dy, velocidad, veneno_total, veneno_duracion, radio=6):
        self.posicion = pygame.Vector2(x, y)
        self.direccion = pygame.Vector2(dx, dy).normalize() if (dx != 0 or dy != 0) else pygame.Vector2(0, -1)
        self.velocidad = velocidad
        self.dano = 0                     # El daño llega solo por el veneno
        self.tipo_dano = "magico"
        self.radio = radio
        self.veneno_total = veneno_total
        self.veneno_duracion = veneno_duracion
        self.activo = True
        self.hitbox = pygame.Rect(round(x - radio), round(y - radio), radio * 2, radio * 2)

    def actualizar(self, dt, limites_mundo):
        min_x, min_y, max_x, max_y = limites_mundo
        self.posicion += self.direccion * self.velocidad
        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)
        if (self.posicion.x < min_x - self.radio or self.posicion.x > max_x + self.radio or
                self.posicion.y < min_y - self.radio or self.posicion.y > max_y + self.radio):
            self.activo = False

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        pygame.draw.circle(pantalla, (40, 120, 40), (px, py), self.radio + 2)       # borde
        pygame.draw.circle(pantalla, COLOR_VENENO, (px, py), self.radio)            # cuerpo verde
        pygame.draw.circle(pantalla, COLOR_VENENO_NUCLEO, (px, py), max(2, self.radio // 2))  # núcleo morado


# -----------------------------
# CLASE BASE DE HABILIDADES
# -----------------------------
COSTO_MEJORA_HABILIDAD = 1   # Puntos de mejora que cuesta subir un nivel de habilidad (por defecto)

# Misma habilidad activa dos veces (equipada y otorgada por Golpe de Suerte): los efectos
# buenos se suman; la otorgada siempre aporta el 100% y la equipada solo este porcentaje
# (sin importar su nivel). Costes, recargas y efectos negativos (fatiga, autodaño) no cambian.
FACTOR_DUPLICADO = 0.5


def factor_duplicado(habilidad, activas):
    """
    Porcentaje que aporta 'habilidad' entre las 'activas' del mismo nombre: 1.0 si es la
    otorgada o la única; FACTOR_DUPLICADO si es la equipada y hay una otorgada activa.
    """
    if habilidad.otorgada:
        return 1.0
    hay_otorgada = any(h.otorgada for h in activas if h is not habilidad)
    return FACTOR_DUPLICADO if hay_otorgada else 1.0


def combinar_buffs(activas, atributo="porcentaje_buff"):
    """Suma el buff de las habilidades activas del mismo nombre aplicando factor_duplicado."""
    return sum(getattr(h, atributo) * factor_duplicado(h, activas) for h in activas)

class HabilidadBase:
    def __init__(self, nombre, descripcion, costo_energia, duracion_activa, duracion_cooldown, tecla, tecla_str):
        self.nombre = nombre
        self.descripcion = descripcion
        self.costo_energia = costo_energia
        self.duracion_activa = duracion_activa
        self.duracion_cooldown = duracion_cooldown
        self.tecla = tecla
        self.tecla_str = tecla_str

        # Estados posibles: "LISTA", "ACTIVA", "COOLDOWN"
        self.estado = "LISTA"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = 0.0
        self.mensaje_alerta = ""
        self.tiempo_alerta = 0.0

        # Progresión por nivel (máx 20). escalable=False -> no sube de nivel (ej. Disparo Veloz)
        self.nivel = 1
        self.nivel_max = 20
        self.escalable = True
        self.costo_mejora = COSTO_MEJORA_HABILIDAD   # Puntos de mejora por cada nivel
        self.otorgada = False   # True si es un efecto otorgado por Golpe de Suerte
        self._aplicar_nivel()

    def _aplicar_nivel(self):
        """Recalcula los valores que dependen del nivel. Las subclases lo sobrescriben."""
        pass

    def subir_nivel(self):
        """Sube la habilidad un nivel (máx nivel_max) y recalcula sus valores."""
        if not self.escalable or self.nivel >= self.nivel_max:
            return False
        self.nivel += 1
        self._aplicar_nivel()
        return True

    def asignar_tecla(self, tecla, tecla_str):
        """Asigna dinámicamente la tecla (2, 3 o 4) según la selección de habilidades."""
        self.tecla = tecla
        self.tecla_str = tecla_str

    def obtener_costo_base(self, jugador):
        return self.costo_energia

    def intentar_activar(self, jugador):
        """
        Intenta activar la habilidad.
        Si otra habilidad ya está en estado ACTIVA, se aplica un sobrecosto
        del 5% de la energía total actual del jugador (redondeada).
        """
        if self.estado != "LISTA":
            return False

        # Verificar si hay otra habilidad activa
        otra_activa = False
        if hasattr(jugador, "habilidades"):
            for h in jugador.habilidades:
                if h != self and h.estado == "ACTIVA":
                    otra_activa = True
                    break

        costo_base = self.obtener_costo_base(jugador)

        # Sobrecosto del 5% de la energía actual
        sobrecosto = 0
        if otra_activa:
            sobrecosto = int(round(jugador.energia * 0.05))
            if sobrecosto < 1 and jugador.energia > 0:
                sobrecosto = 1

        costo_total = costo_base + sobrecosto

        if jugador.energia < costo_total:
            self.mensaje_alerta = f"¡Falta energía! (Req. {costo_total})"
            self.tiempo_alerta = 2.5
            return False

        # Descontar energía
        jugador.energia -= costo_total

        # Ejecutar efecto específico
        self.ejecutar_activacion(jugador)

        if sobrecosto > 0:
            self.mensaje_alerta = f"¡Combo activo! (+{sobrecosto} En.)"
            self.tiempo_alerta = 2.0

        return True

    def ejecutar_activacion(self, jugador):
        """Por defecto activa la duración activa."""
        self.estado = "ACTIVA"
        self.tiempo_restante_activo = self.duracion_activa
        self.aplicar_efecto_activo(jugador)

    def aplicar_efecto_activo(self, jugador):
        pass

    def aplicar_efecto_cooldown(self, jugador):
        pass

    def restaurar_efecto(self, jugador):
        pass

    def actualizar(self, dt, jugador):
        """Actualiza temporizadores según delta time transcurrido (segundos)."""
        if self.tiempo_alerta > 0:
            self.tiempo_alerta -= dt
            if self.tiempo_alerta <= 0:
                self.mensaje_alerta = ""

        if self.estado == "ACTIVA":
            self.tiempo_restante_activo -= dt
            if self.tiempo_restante_activo <= 0:
                self.estado = "COOLDOWN"
                self.tiempo_restante_activo = 0.0
                self.tiempo_restante_cooldown = self.duracion_cooldown
                self.aplicar_efecto_cooldown(jugador)

        elif self.estado == "COOLDOWN":
            self.tiempo_restante_cooldown -= dt
            if self.tiempo_restante_cooldown <= 0:
                self.estado = "LISTA"
                self.tiempo_restante_cooldown = 0.0
                self.restaurar_efecto(jugador)


# -----------------------------
# HABILIDAD 1: DESTELLO
# -----------------------------
class Destello(HabilidadBase):
    def __init__(self):
        super().__init__(
            nombre="Destello",
            descripcion="Aumenta la velocidad un 50% (+0.5x) por 10s. Tras finalizar: 5s de enfriamiento con debuff (-20% velocidad).",
            costo_energia=10,
            duracion_activa=10.0,
            duracion_cooldown=5.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )

    def _aplicar_nivel(self):
        """
        Escalado de Destello (nivel 1 a 20):
        - buff velocidad: +50% +2% por nivel
        - duración: 10s, +2s cada 5 niveles
        - cooldown: 5s, -1s cada 5 niveles (mín. 1s)
        - debuff de fatiga: -20%, -5% cada 5 niveles (mín. 0)
        - costo: 10 energía, +5 cada 3 niveles
        """
        n = self.nivel
        self.porcentaje_buff = round(0.50 + 0.02 * n, 3)
        self.porcentaje_debuff = max(0.0, round(0.20 - 0.05 * (n // 5), 3))
        self.duracion_activa = 10.0 + 2.0 * (n // 5)
        self.duracion_cooldown = max(1.0, 5.0 - 1.0 * (n // 5))
        self.costo_energia = 10 + 5 * (n // 3)

    def aplicar_efecto_activo(self, jugador):
        jugador.velocidad = jugador.velocidad_base * (1.0 + self.porcentaje_buff)

    def aplicar_efecto_cooldown(self, jugador):
        jugador.velocidad = max(0.5, jugador.velocidad_base * (1.0 - self.porcentaje_debuff))

    def restaurar_efecto(self, jugador):
        jugador.velocidad = jugador.velocidad_base


# -----------------------------
# HABILIDAD 2: BURST DE FUERZA
# -----------------------------
class BurstDeFuerza(HabilidadBase):
    def __init__(self):
        super().__init__(
            nombre="Burst de Fuerza",
            descripcion="Aumenta la fuerza base un 20% (+0.2x) durante 6s. Enfriamiento de 12s.",
            costo_energia=15,
            duracion_activa=6.0,
            duracion_cooldown=12.0,
            tecla=pygame.K_3,
            tecla_str="3"
        )

    def _aplicar_nivel(self):
        """
        Escalado de Burst de Fuerza (nivel 1 a 20):
        - buff fuerza: +20% +1% por nivel
        - duración: 6s, +1s cada 5 niveles
        - cooldown: 12s, -1s cada 5 niveles (mín. 1s)
        - costo: 15 energía, +5 cada 5 niveles
        """
        n = self.nivel
        self.porcentaje_buff = round(0.20 + 0.01 * n, 3)
        self.duracion_activa = 6.0 + 1.0 * (n // 5)
        self.duracion_cooldown = max(1.0, 12.0 - 1.0 * (n // 5))
        self.costo_energia = 15 + 5 * (n // 5)

    def aplicar_efecto_activo(self, jugador):
        self._recalcular_fuerza(jugador)

    def aplicar_efecto_cooldown(self, jugador):
        self._recalcular_fuerza(jugador)

    def restaurar_efecto(self, jugador):
        self._recalcular_fuerza(jugador)

    def _recalcular_fuerza(self, jugador):
        """
        Combina los Burst activos (combinar_buffs): el de Golpe de Suerte al 100% y el
        equipado al 50% si coinciden. Si ninguno sigue activo, la fuerza vuelve a la base.
        """
        activos = [h for h in jugador.habilidades_en_efecto() if h.nombre == self.nombre and h.estado == "ACTIVA"]
        if self.estado == "ACTIVA" and self not in activos:
            activos.append(self)
        buff = combinar_buffs(activos)
        jugador.fuerza = round(jugador.fuerza_base * (1.0 + buff), 2)


# -----------------------------
# HABILIDAD 3: DISPARO VELOZ (NUEVA)
# -----------------------------
class DisparoVeloz(HabilidadBase):
    # Daño mágico fijo y velocidad del proyectil (su punto fuerte), lineales de nivel 1 a 20
    DANO_NV1, DANO_NV_MAX = 8.0, 30.0
    VELOCIDAD_NV1, VELOCIDAD_NV_MAX = 14.0, 40.0

    def __init__(self):
        super().__init__(
            nombre="Disparo Veloz",
            descripcion="Ataque a distancia: esfera de energía recta muy rápida. Daño mágico fijo; escala velocidad, daño y coste con el nivel (máx 20).",
            costo_energia=15,
            duracion_activa=0.0,
            duracion_cooldown=2.0,
            tecla=pygame.K_4,
            tecla_str="4"
        )

    def _aplicar_nivel(self):
        """
        Escalado de Disparo Veloz (nivel 1 a 20):
        - velocidad del proyectil: 14 -> 40 lineal (a 1 decimal)
        - daño mágico fijo: 8 -> 30 lineal (a 1 decimal); ya no depende del arma
        - coste: 15 energía, +5 cada 5 niveles (rediseño: coste fijo, ya no porcentaje)
        - recarga: 2s a nivel 1, baja de forma lineal hasta 0.5s a nivel máximo
        """
        n = self.nivel
        t = (n - 1) / (self.nivel_max - 1)
        self.velocidad_proyectil = round(self.VELOCIDAD_NV1 + (self.VELOCIDAD_NV_MAX - self.VELOCIDAD_NV1) * t, 1)
        self.dano = round(self.DANO_NV1 + (self.DANO_NV_MAX - self.DANO_NV1) * t, 1)
        self.costo_energia = 15 + 5 * (n // 5)
        self.duracion_cooldown = round(max(0.5, 2.0 - 1.5 * (n - 1) / (self.nivel_max - 1)), 2)

    def obtener_costo_base(self, jugador):
        """Coste fijo de energía según el nivel (rediseño: ya no es un porcentaje de la energía máxima)."""
        return self.costo_energia

    def ejecutar_activacion(self, jugador):
        """Dispara una esfera recta en la dirección a la que apunta el personaje."""
        rad = math.radians(jugador.angulo)
        frente_x = math.sin(rad)
        frente_y = -math.cos(rad)

        # Origen justo en el borde frontal del personaje
        origen_x = jugador.posicion.x + (frente_x * (jugador.radio + 8))
        origen_y = jugador.posicion.y + (frente_y * (jugador.radio + 8))

        proyectil = ProyectilEnergia(
            x=origen_x,
            y=origen_y,
            dx=frente_x,
            dy=frente_y,
            velocidad=self.velocidad_proyectil,
            dano=self.dano,
            radio=6
        )

        if hasattr(jugador, "proyectiles"):
            jugador.proyectiles.append(proyectil)

        # Pasa inmediatamente a su recarga
        self.estado = "COOLDOWN"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = self.duracion_cooldown


# -----------------------------
# HABILIDAD: DISPARO VENENOSO
# -----------------------------
class DisparoVenenoso(HabilidadBase):
    """
    Ataque mágico: dispara una esfera verde (núcleo morado) hacia donde mira el personaje.
    Se detiene en el primer enemigo (las rocas la bloquean) y lo envenena: daño mágico por
    segundo que amortigua el escudo mágico. El impacto no hace daño ni empuja. El veneno no
    se acumula: volver a envenenar reinicia el efecto con los valores del nuevo disparo.
    """
    VELOCIDAD_PROYECTIL = 12.0
    COSTO_NV1, COSTO_NV_MAX = 20, 45
    VENENO_NV1, VENENO_NV_MAX = 20.0, 40.0          # daño total del veneno
    DURACION_NV1, DURACION_NV_MAX = 20.0, 10.0      # segundos que dura el veneno
    RECARGA_NV1, RECARGA_NV_MAX = 30.0, 15.0

    def __init__(self):
        super().__init__(
            nombre="Disparo Venenoso",
            descripcion="Esfera venenosa: envenena al primer enemigo (daño mágico por segundo). El impacto no daña ni empuja.",
            costo_energia=self.COSTO_NV1,
            duracion_activa=0.0,
            duracion_cooldown=self.RECARGA_NV1,
            tecla=pygame.K_4,
            tecla_str="4"
        )

    def _aplicar_nivel(self):
        """
        Escalado lineal (nivel 1 a 20):
        - coste: 20 -> 45 En. (entero)
        - veneno: 20 de daño en 20 s (1/s) -> 40 de daño en 10 s (4/s), a 1 decimal
        - recarga: 30 s -> 15 s, a 1 decimal
        """
        t = (self.nivel - 1) / (self.nivel_max - 1)
        self.costo_energia = round(self.COSTO_NV1 + (self.COSTO_NV_MAX - self.COSTO_NV1) * t)
        self.veneno_total = round(self.VENENO_NV1 + (self.VENENO_NV_MAX - self.VENENO_NV1) * t, 1)
        self.veneno_duracion = round(self.DURACION_NV1 + (self.DURACION_NV_MAX - self.DURACION_NV1) * t, 1)
        self.duracion_cooldown = round(self.RECARGA_NV1 + (self.RECARGA_NV_MAX - self.RECARGA_NV1) * t, 1)

    def ejecutar_activacion(self, jugador):
        """Dispara la esfera venenosa y entra en recarga."""
        rad = math.radians(jugador.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        origen = jugador.posicion + frente * (jugador.radio + 8)
        jugador.proyectiles.append(ProyectilVeneno(origen.x, origen.y, frente.x, frente.y,
                                                   self.VELOCIDAD_PROYECTIL, self.veneno_total,
                                                   self.veneno_duracion))
        self.estado = "COOLDOWN"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = self.duracion_cooldown


# -----------------------------
# CUCHILLA CORTANTE (HABILIDAD CORTAR)
# -----------------------------
def _distancia_punto_segmento(p, a, b):
    ab = b - a
    largo2 = ab.length_squared()
    if largo2 == 0:
        return (p - a).length()
    t = max(0.0, min(1.0, (p - a).dot(ab) / largo2))
    return (p - (a + ab * t)).length()


class CuchillaCortante:
    """Cuchilla delgada (negra con contorno rojo) que avanza en linea recta, perpendicular a
    su trayectoria, del largo aproximado de la Espada Ligera. Dano magico.
    Se detiene en lo primero que toque:
    - Enemigo: le hace dano y, si llega a hacerlo, anula su escudo magico 10 s.
    - Roca o arbusto: lo destruye y se rompe con el (solo un objeto). Las rocas gigantes y los
      arbustos grandes solo se destruyen a nivel maximo; si no, la cuchilla se rompe sin danarlos.
      Lanzada desde dentro de un arbusto sale hacia afuera sin cortarlo.
    Avanza en sub-pasos cortos para no atravesar objetos pequenos a velocidades altas."""
    LARGO = 32          # aprox. el largo de la Espada Ligera (tamano 1)
    GROSOR = 4          # grosor maximo del cuerpo (en el centro)
    PASO_MAX = 6.0      # px por sub-paso al comprobar colisiones

    def __init__(self, x, y, dx, dy, velocidad, dano, corta_grandes, oculta_hasta=0.0):
        self.posicion = pygame.Vector2(x, y)
        # Sale desde el centro del lanzador (asi corta el arbusto en el que este escondido),
        # pero no se dibuja hasta salir de su cuerpo
        self.recorrido = 0.0
        self.oculta_hasta = oculta_hasta
        self.origen = pygame.Vector2(x, y)
        self._arbustos_origen = None   # arbustos donde se lanzo (no los corta: sale de dentro hacia afuera)
        d = pygame.Vector2(dx, dy)
        self.direccion = d.normalize() if d.length_squared() > 0 else pygame.Vector2(0, -1)
        self.lateral = pygame.Vector2(-self.direccion.y, self.direccion.x)
        self.velocidad = velocidad
        self.dano = dano
        self.tipo_dano = "magico"
        self.corta_grandes = corta_grandes
        self.activo = True
        self._actualizar_hitbox()

    def extremos(self):
        mitad = self.lateral * (self.LARGO / 2)
        return self.posicion - mitad, self.posicion + mitad

    def _actualizar_hitbox(self):
        a, b = self.extremos()
        self.hitbox = pygame.Rect(round(min(a.x, b.x)) - 2, round(min(a.y, b.y)) - 2,
                                  round(abs(a.x - b.x)) + 4, round(abs(a.y - b.y)) + 4)

    def avanzar(self, rocas, arbustos, arboles, enemigos, centro_mundo, radio_mundo):
        """Mueve la cuchilla un frame. Las rocas, arbustos y arboles destruidos se quitan de sus
        listas. Devuelve el obstaculo destruido (o None) para liberar su zona en la vegetacion."""
        if self._arbustos_origen is None:
            self._arbustos_origen = {id(arb) for arb in arbustos if arb.contiene(self.origen)}
        sub_pasos = max(1, math.ceil(self.velocidad / self.PASO_MAX))
        paso = self.direccion * (self.velocidad / sub_pasos)
        for _ in range(sub_pasos):
            self.posicion += paso
            self.recorrido += paso.length()
            a, b = self.extremos()
            self._actualizar_hitbox()

            for e in enemigos:
                if getattr(e, "vivo", True) and _distancia_punto_segmento(e.posicion, a, b) <= e.radio:
                    self._golpear(e)
                    return None

            for roca in rocas:
                if roca.rect.clipline(a, b):
                    self.activo = False
                    if not getattr(roca, "gigante", False) or self.corta_grandes:
                        rocas.remove(roca)
                        return roca
                    return None

            # Arbustos solapados (matorrales): se queda con el mas cercano a la cuchilla
            tocados = [arb for arb in arbustos
                       if id(arb) not in self._arbustos_origen
                       and any(_distancia_punto_segmento(c, a, b) <= r for c, r in arb.circulos)]
            if tocados:
                arbusto = min(tocados, key=lambda arb: (arb.centro - self.posicion).length())
                self.activo = False
                if not getattr(arbusto, "grande", False) or self.corta_grandes:
                    arbustos.remove(arbusto)
                    return arbusto
                return None

            # Arboles: se rompen al tocar CUALQUIER parte (la copa); la cuchilla se rompe con el
            arboles_tocados = [arb for arb in arboles
                               if _distancia_punto_segmento(arb.centro, a, b) <= arb.radio_copa]
            if arboles_tocados:
                arbol = min(arboles_tocados, key=lambda arb: (arb.centro - self.posicion).length())
                self.activo = False
                arboles.remove(arbol)
                return arbol

            if (self.posicion - centro_mundo).length() > radio_mundo:
                self.activo = False
                return None
        return None

    def _golpear(self, enemigo):
        self.activo = False
        if hasattr(enemigo, "recibir_dano"):
            aplicado = enemigo.recibir_dano(self.dano, self.tipo_dano, self.direccion)
        else:
            enemigo.vida = max(0.0, round(enemigo.vida - self.dano, 2))
            aplicado = self.dano
        if aplicado and aplicado > 0:
            anular_escudo_magico(enemigo)

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        """Media luna delgada: cuerpo negro con contorno rojo."""
        if self.recorrido < self.oculta_hasta:
            return
        ox, oy = desplazamiento
        a, b = self.extremos()
        frente = self.direccion * self.GROSOR
        atras = self.direccion * (self.GROSOR * 0.25)
        puntos = [a, self.posicion + frente, b, self.posicion - atras]
        puntos = [(round(p.x - ox), round(p.y - oy)) for p in puntos]
        pygame.draw.polygon(pantalla, (10, 10, 12), puntos)
        pygame.draw.polygon(pantalla, (220, 30, 40), puntos, 2)


# -----------------------------
# HABILIDAD: CORTAR (dano magico)
# -----------------------------
class Cortar(HabilidadBase):
    """Lanza en linea recta una cuchilla cortante (dano magico). Si llega a hacer dano, anula
    el escudo magico del enemigo 8 s. Destruye una roca o un arbusto al chocar (gigantes y
    arbustos grandes solo a nivel 20)."""
    DANO_NIVEL_1 = 5
    DANO_NIVEL_MAX = 40

    def __init__(self):
        super().__init__(
            nombre="Cortar",
            descripcion="Cuchilla recta de daño mágico. Anula el escudo mágico 8s y destruye una roca o arbusto.",
            costo_energia=15,
            duracion_activa=0.0,
            duracion_cooldown=2.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.cuchillas = []

    def _aplicar_nivel(self):
        """
        Escalado de Cortar (nivel 1 a 20):
        - Dano: 5 (nv1) -> 40 (nv20), lineal (redondeado a 1 decimal)
        - Velocidad de la cuchilla: 5 + 1 por nivel (nv20 = 24)
        - Coste: 15 + 2 por nivel (nv20 = 53)
        - Recarga: 2s + 2s cada 5 niveles (nv20 = 10s); sube a proposito
        - A nivel 20 corta rocas gigantes y arbustos grandes
        """
        n = self.nivel
        self.dano = round(self.DANO_NIVEL_1 + (self.DANO_NIVEL_MAX - self.DANO_NIVEL_1) * (n - 1) / (self.nivel_max - 1), 1)
        self.velocidad_cuchilla = 5 + (n - 1)
        self.costo_energia = 15 + 2 * (n - 1)
        self.duracion_cooldown = 2.0 + 2.0 * (n // 5)
        self.corta_grandes = n >= self.nivel_max

    def ejecutar_activacion(self, jugador):
        """Lanza la cuchilla hacia donde mira el personaje y entra en recarga."""
        rad = math.radians(jugador.angulo)
        frente = pygame.Vector2(math.sin(rad), -math.cos(rad))
        origen = jugador.posicion
        self.cuchillas.append(CuchillaCortante(origen.x, origen.y, frente.x, frente.y,
                                               self.velocidad_cuchilla, self.dano, self.corta_grandes,
                                               oculta_hasta=jugador.radio))
        self.estado = "COOLDOWN"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = self.duracion_cooldown

    def actualizar_cuchillas(self, rocas, arbustos, arboles, enemigos, centro_mundo, radio_mundo):
        """Mueve las cuchillas. Devuelve los obstaculos (rocas, arbustos, arboles) destruidos
        en este frame."""
        destruidas = []
        for c in self.cuchillas:
            obstaculo = c.avanzar(rocas, arbustos, arboles, enemigos, centro_mundo, radio_mundo)
            if obstaculo is not None:
                destruidas.append(obstaculo)
        self.cuchillas = [c for c in self.cuchillas if c.activo]
        return destruidas

    def dibujar_cuchillas(self, pantalla, desplazamiento=(0, 0)):
        for c in self.cuchillas:
            c.dibujar(pantalla, desplazamiento)


# -----------------------------
# ONDA SONORA: anillos que se expanden 360 grados desde el lanzador
# -----------------------------
class AnilloSonoro:
    """Un anillo de una Onda Sonora. Crece desde su centro hasta el radio maximo; golpea a
    cada objetivo una sola vez cuando su frente lo alcanza. Atraviesa rocas y arbustos sin
    destruirlos. Se desvanece al acercarse al borde."""
    def __init__(self, centro, radio_max, velocidad, dano, en_agua, emision):
        self.centro = pygame.Vector2(centro)
        self.radio = 0.0
        self.radio_max = radio_max
        self.velocidad = velocidad
        self.dano = dano
        self.en_agua = en_agua           # medio del lanzador al emitirla
        self.emision = emision           # lanzamiento al que pertenece (cuenta impactos)
        self.golpeados = set()
        self.activo = True

    def actualizar(self, dt, enemigos):
        previo = self.radio
        self.radio = min(self.radio_max, self.radio + self.velocidad * dt)
        for e in enemigos:
            if id(e) in self.golpeados or not getattr(e, "vivo", True):
                continue
            dist = (e.posicion - self.centro).length()
            # El frente del anillo cruzo el cuerpo del objetivo en este frame
            if dist - e.radio <= self.radio and dist + e.radio >= previo:
                self.golpeados.add(id(e))
                self.emision.impactar(self, e)
        if self.radio >= self.radio_max:
            self.activo = False

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        r = round(self.radio)
        if r < 2:
            return
        alpha = round(255 * max(0.0, 1.0 - self.radio / self.radio_max) ** 0.6)
        if alpha <= 0:
            return
        sup = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(sup, (255, 255, 255, alpha), (r + 2, r + 2), r, 2)
        pantalla.blit(sup, (round(self.centro.x - desplazamiento[0]) - r - 2,
                            round(self.centro.y - desplazamiento[1]) - r - 2))


class EmisionSonora:
    """Un lanzamiento de Onda Sonora: emite sus anillos uno tras otro desde el punto donde se
    lanzo (no sigue al personaje) y lleva la cuenta de cuantos golpean a cada objetivo
    (1, 2 o 3 => ralentizacion creciente). El medio (agua o tierra) es el del punto de lanzamiento."""
    INTERVALO = 0.8               # segundos entre anillos

    def __init__(self, habilidad, centro, en_agua):
        self.hab = habilidad
        self.centro = pygame.Vector2(centro)
        self.en_agua = en_agua
        self.pendientes = list(habilidad.danos_ondas)   # dano base de cada anillo por emitir
        self.timer = 0.0
        self.anillos = []
        self.impactos = {}        # id(objetivo) -> anillos que lo golpearon

    @property
    def activa(self):
        return bool(self.pendientes) or any(a.activo for a in self.anillos)

    def actualizar(self, dt, enemigos):
        self.timer -= dt
        while self.pendientes and self.timer <= 0:
            vel = OndaSonora.VELOCIDAD_AGUA if self.en_agua else OndaSonora.VELOCIDAD
            self.anillos.append(AnilloSonoro(self.centro, self.hab.radio, vel,
                                             self.pendientes.pop(0), self.en_agua, self))
            self.timer += self.INTERVALO
        for a in self.anillos:
            if a.activo:
                a.actualizar(dt, enemigos)
        self.anillos = [a for a in self.anillos if a.activo]

    def impactar(self, anillo, objetivo):
        """Dano magico y ralentizacion segun el medio y los anillos que ya lo golpearon."""
        factor = OndaSonora.factor_medio(anillo.en_agua, getattr(objetivo, "en_agua", False))
        n = self.impactos.get(id(objetivo), 0) + 1
        self.impactos[id(objetivo)] = n
        direccion = objetivo.posicion - anillo.centro
        if hasattr(objetivo, "recibir_dano"):
            objetivo.recibir_dano(anillo.dano * factor, "magico", direccion)
        else:
            objetivo.vida = max(0.0, round(objetivo.vida - anillo.dano * factor, 2))
        aplicar_ralentizacion(objetivo, OndaSonora.RALENTIZACION[n - 1] * factor)


class OndaSonora(HabilidadBase):
    """Dano magico en area: anillos que salen del personaje y se expanden 360 grados. Uno a
    nivel 1, dos desde nivel 10 y tres a nivel 20, separados 0.8 s. Atraviesan obstaculos sin
    destruir nada y solo afectan a enemigos. Ralentizan segun cuantos anillos golpeen.
    Medio (donde esta el lanzador al emitir / donde esta el objetivo al recibir):
    - tierra -> tierra: normal; agua -> agua: dano y ralentizacion x2.
    - cambio de medio (tierra <-> agua): la onda pierde energia, dano y ralentizacion x0.5.
    Desde el agua el anillo viaja al doble de velocidad."""
    DANOS = (10, 20, 30)                    # dano fijo de la 1a, 2a y 3a onda
    NIVEL_SEGUNDA = 10
    NIVEL_TERCERA = 20
    RALENTIZACION = (0.05, 0.10, 0.20)      # segun anillos que golpean al objetivo (1, 2, 3)
    VELOCIDAD = 300.0                       # px/s
    VELOCIDAD_AGUA = 600.0
    FACTOR_MISMO_AGUA = 2.0
    FACTOR_CAMBIO_MEDIO = 0.5

    def __init__(self):
        super().__init__(
            nombre="Onda Sonora",
            descripcion="Anillos sonoros 360 de daño mágico que ralentizan. Atraviesan obstáculos.",
            costo_energia=10,
            duracion_activa=0.0,
            duracion_cooldown=10.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.emisiones = []

    @classmethod
    def factor_medio(cls, lanzador_en_agua, objetivo_en_agua):
        if lanzador_en_agua != objetivo_en_agua:
            return cls.FACTOR_CAMBIO_MEDIO
        return cls.FACTOR_MISMO_AGUA if lanzador_en_agua else 1.0

    def _aplicar_nivel(self):
        """
        Escalado de Onda Sonora (nivel 1 a 20):
        - Ondas: 1 (dano 10); 2 desde nv10 (10 y 20); 3 a nv20 (10, 20 y 30)
        - Radio: 200 a 400 lineal
        - Recarga: 10s a 30s lineal (sube a proposito)
        - Coste: 10 + 5 cada 5 niveles (max 30)
        """
        n = self.nivel
        cantidad = 1 + (n >= self.NIVEL_SEGUNDA) + (n >= self.NIVEL_TERCERA)
        self.danos_ondas = self.DANOS[:cantidad]
        self.radio = round(200 + 200 * (n - 1) / 19, 1)
        self.duracion_cooldown = round(10.0 + 20.0 * (n - 1) / 19, 2)
        self.costo_energia = min(30, 10 + 5 * (n // 5))

    def ejecutar_activacion(self, jugador):
        self.emisiones.append(EmisionSonora(self, jugador.posicion, getattr(jugador, "en_agua", False)))
        self.estado = "COOLDOWN"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = self.duracion_cooldown

    def actualizar_ondas(self, dt, enemigos):
        for e in self.emisiones:
            e.actualizar(dt, enemigos)
        self.emisiones = [e for e in self.emisiones if e.activa]

    def dibujar_ondas(self, pantalla, desplazamiento=(0, 0)):
        for e in self.emisiones:
            for a in e.anillos:
                a.dibujar(pantalla, desplazamiento)


# -----------------------------
# HELPERS DE INTERFAZ: ICONO DE AYUDA (?) Y TOOLTIP
# -----------------------------
def dibujar_badge_ayuda(pantalla, cx, cy, fuente, activo=False):
    """Dibuja un pequeño icono circular '?'. Devuelve su Rect (zona clicable)."""
    r = 8
    color_fondo = (60, 110, 70) if activo else (45, 52, 68)
    color_borde = (120, 230, 150) if activo else (95, 105, 125)
    pygame.draw.circle(pantalla, color_fondo, (cx, cy), r)
    pygame.draw.circle(pantalla, color_borde, (cx, cy), r, 1)
    q = fuente.render("?", True, (210, 220, 235))
    pantalla.blit(q, q.get_rect(center=(cx, cy)))
    return pygame.Rect(cx - r, cy - r, r * 2, r * 2)


def _envolver_texto(texto, fuente, ancho_max):
    """Parte un texto en varias líneas que caben en ancho_max píxeles."""
    palabras = texto.split(" ")
    lineas = []
    actual = ""
    for p in palabras:
        prueba = p if not actual else actual + " " + p
        if fuente.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    return lineas


def dibujar_tooltip(pantalla, x, y, titulo, lineas, fuente_titulo, fuente_texto, ancho=250):
    """Dibuja una caja de información con texto envuelto, ajustada para no salir de la pantalla."""
    margen = 10
    ancho_texto = ancho - 2 * margen
    render = []
    for ln in lineas:
        if ln == "":
            render.append("")
            continue
        render.extend(_envolver_texto(ln, fuente_texto, ancho_texto))
    alto = margen + 22 + len(render) * 15 + margen

    sx, sy = pantalla.get_width(), pantalla.get_height()
    x = max(4, min(x, sx - ancho - 4))
    y = max(4, min(y, sy - alto - 4))

    caja = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    pygame.draw.rect(caja, (24, 28, 38, 245), caja.get_rect(), border_radius=8)
    pygame.draw.rect(caja, (90, 110, 140), caja.get_rect(), width=1, border_radius=8)
    pantalla.blit(caja, (x, y))

    t = fuente_titulo.render(titulo, True, (255, 215, 0))
    pantalla.blit(t, (x + margen, y + margen))
    yy = y + margen + 22
    for sub in render:
        if sub:
            pantalla.blit(fuente_texto.render(sub, True, (200, 210, 225)), (x + margen, yy))
        yy += 15


# -----------------------------
# DIBUJAR PANEL LATERAL DE HABILIDADES
# -----------------------------
# Habilidades cuya tarjeta activa se pinta en tono frío (cian) en lugar de rojizo
HABILIDADES_TONO_FRIO = ("Destello", "Aura Electrica", "Reforzamiento Mágico", "Paso 0")

def dibujar_panel_habilidades(pantalla, x, y, ancho, alto, habilidades, jugador, fuentes, info_abierta=None):
    """
    Renderiza la interfaz lateral derecha para las habilidades equipadas (teclas 2, 3, 4)
    y sus temporizadores. El manual se consulta con el icono '?' de la cabecera.
    Panel ancho y de alto contraste para que el detalle completo sea legible.
    """
    # Fuentes dedicadas (mas grandes) con respaldo a las antiguas si no existen
    fuente_titulo = fuentes.get("hab_nom", fuentes["titulo"])
    fuente_sub = fuentes.get("hab_sub", fuentes["sub"])
    fuente_det = fuentes.get("hab_det", fuentes.get("texto", fuentes["mini"]))
    fuente_mini = fuentes.get("hab_mini", fuentes["mini"])
    fuente_contador = fuentes.get("hab_contador", fuentes["contador"])

    panel = pygame.Surface((ancho, alto))
    panel.fill((20, 23, 30))
    pantalla.blit(panel, (x, y))

    pygame.draw.line(pantalla, (45, 52, 68), (x, y), (x, y + alto), 2)

    # Cabecera
    titulo = fuente_titulo.render("HABILIDADES", True, (255, 215, 0))
    pantalla.blit(titulo, (x + 16, y + 12))

    sub = fuente_sub.render(f"Equipadas ({len(habilidades)}/3)", True, (175, 185, 205))
    pantalla.blit(sub, (x + 16, y + 34))

    cur_y = y + 64
    botones = {}  # Botones (clave -> Rect): "__hab__<idx>" y "__info_hab__"

    # Icono de ayuda (?) en la cabecera -> abre el manual como tooltip
    botones["__info_hab__"] = dibujar_badge_ayuda(pantalla, x + ancho - 26, y + 20, fuente_sub, info_abierta == "hab")

    pygame.draw.line(pantalla, (45, 52, 68), (x + 16, y + 56), (x + ancho - 16, y + 56), 1)

    # Altura de tarjeta: mas compacta con 3 habilidades, mas holgada con menos
    tarjeta_h = 122 if len(habilidades) >= 3 else 144

    for idx, hab in enumerate(habilidades):
        tarjeta_w = ancho - 28
        tarjeta_x = x + 14
        pad = 12  # margen interno izquierdo

        if hab.estado == "ACTIVA":
            color_borde = (0, 220, 255) if hab.nombre in HABILIDADES_TONO_FRIO else (255, 100, 70)
            color_fondo = (22, 38, 50) if hab.nombre in HABILIDADES_TONO_FRIO else (48, 26, 26)
        elif hab.estado == "COOLDOWN":
            color_borde = (230, 140, 40)
            color_fondo = (40, 30, 24)
        else:
            color_borde = (55, 68, 90)
            color_fondo = (26, 30, 40)

        pygame.draw.rect(pantalla, color_fondo, (tarjeta_x, cur_y, tarjeta_w, tarjeta_h), border_radius=8)
        pygame.draw.rect(pantalla, color_borde, (tarjeta_x, cur_y, tarjeta_w, tarjeta_h), width=2, border_radius=8)

        # Nombre y tecla asignada
        txt_nom = fuente_sub.render(hab.nombre, True, (255, 255, 255))
        pantalla.blit(txt_nom, (tarjeta_x + pad, cur_y + 8))

        txt_tecla = fuente_mini.render(f"[{hab.tecla_str}]", True, (255, 220, 80))
        tecla_x = tarjeta_x + tarjeta_w - txt_tecla.get_width() - pad
        pantalla.blit(txt_tecla, (tecla_x, cur_y + 9))

        # Boton [+] para subir nivel (gasta un punto de mejora compartido)
        if hab.escalable and hab.nivel < hab.nivel_max and jugador.puntos_mejora >= hab.costo_mejora:
            bsize = 18
            rect_btn = pygame.Rect(tecla_x - bsize - 10, cur_y + 7, bsize, bsize)
            pygame.draw.rect(pantalla, (34, 78, 44), rect_btn, border_radius=4)
            pygame.draw.rect(pantalla, (100, 230, 130), rect_btn, width=1, border_radius=4)
            signo = fuente_sub.render("+", True, (150, 255, 180))
            pantalla.blit(signo, signo.get_rect(center=rect_btn.center))
            botones[f"__hab__{idx}"] = rect_btn

        # Nivel y costo
        if hab.escalable:
            color_nv = (255, 215, 120) if hab.nivel >= hab.nivel_max else (170, 205, 255)
            txt_nivel = fuente_mini.render(f"Nv {hab.nivel}/{hab.nivel_max}", True, color_nv)
        else:
            txt_nivel = fuente_mini.render("Nv —", True, (150, 160, 180))
        pantalla.blit(txt_nivel, (tarjeta_x + pad, cur_y + 32))

        costo_mostrado = hab.obtener_costo_base(jugador)
        txt_costo = fuente_mini.render(f"Costo: {costo_mostrado} En.", True, (200, 165, 255))
        pantalla.blit(txt_costo, (tarjeta_x + pad + 110, cur_y + 32))

        # Geometria comun de la barra de progreso
        bw = tarjeta_w - 2 * pad
        bar_y = cur_y + 78
        y_estado = cur_y + 52
        y_cont = cur_y + 44

        # Estado y cuenta regresiva
        if getattr(hab, "canalizando", False):
            txt_est = fuente_mini.render("REGENERANDO", True, (255, 160, 210))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            falta = max(0.0, hab.intervalo - hab.tiempo_tick)
            txt_tiempo = fuente_contador.render(f"{falta:.1f}s", True, (255, 200, 230))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - pad, y_cont))

            prog = hab.tiempo_tick / max(0.1, hab.intervalo)
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (50, 30, 42), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (255, 120, 190), (tarjeta_x + pad, bar_y, ancho_l, 7), border_radius=3)

        elif getattr(hab, "cargando", False):
            txt_est = fuente_mini.render(f"🔥 CARGANDO {hab.tiempo_carga:.1f}s", True, (255, 180, 80))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            txt_tiempo = fuente_contador.render(f"{hab.tiempo_carga:.1f}", True, (255, 220, 150))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - pad, y_cont))

            prog = hab.tiempo_carga / max(0.1, hab.TIEMPO_MAX_CARGA)
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (50, 40, 30), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (255, 150, 50), (tarjeta_x + pad, bar_y, ancho_l, 7), border_radius=3)

        elif hab.estado == "LISTA":
            txt_est = fuente_mini.render("LISTA (Disponible)", True, (120, 255, 160))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            pygame.draw.rect(pantalla, (40, 50, 45), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            pygame.draw.rect(pantalla, (100, 255, 140), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)

        elif hab.estado == "ACTIVA":
            txt_est = fuente_mini.render("⚡ ACTIVA", True, (0, 220, 255) if hab.nombre in HABILIDADES_TONO_FRIO else (255, 140, 100))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            seg = max(0.0, hab.tiempo_restante_activo)
            txt_tiempo = fuente_contador.render(f"{seg:.1f}s", True, (255, 255, 255))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - pad, y_cont))

            prog = seg / max(0.1, hab.duracion_activa)
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (35, 45, 55), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (0, 210, 255) if hab.nombre in HABILIDADES_TONO_FRIO else (255, 90, 60), (tarjeta_x + pad, bar_y, ancho_l, 7), border_radius=3)

        elif hab.estado == "COOLDOWN":
            txt_est = fuente_mini.render("⏳ ENFRIAMIENTO", True, (255, 165, 80))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            seg = max(0.0, hab.tiempo_restante_cooldown)
            txt_tiempo = fuente_contador.render(f"{seg:.1f}s", True, (255, 200, 140))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - pad, y_cont))

            prog = seg / max(0.1, hab.duracion_cooldown)
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (45, 35, 30), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (255, 140, 50), (tarjeta_x + pad, bar_y, ancho_l, 7), border_radius=3)

        elif hab.estado == "INVOCADO":
            criaturas = getattr(hab, "criaturas", None)
            if criaturas is None:
                criaturas = getattr(hab, "conejos", None) or getattr(hab, "lobos", [])
            n_inv = len(criaturas)
            txt_est = fuente_mini.render(f"⚡ ACTIVA ({n_inv} vivos)", True, (140, 240, 170))
            pantalla.blit(txt_est, (tarjeta_x + pad, y_estado))

            txt_tiempo = fuente_contador.render(f"{n_inv}", True, (255, 255, 255))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - pad, y_cont))

            tope = getattr(hab, "tope_criaturas", None) or getattr(hab, "max_conejos", None) or getattr(hab, "max_invocaciones", 50)
            prog = n_inv / float(tope)
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (35, 50, 40), (tarjeta_x + pad, bar_y, bw, 7), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (90, 220, 120), (tarjeta_x + pad, bar_y, ancho_l, 7), border_radius=3)

        # Resumen del efecto (valores reales segun el nivel)
        if hab.nombre == "Destello":
            detalles = f"{hab.duracion_activa:.0f}s (+{hab.porcentaje_buff * 100:.0f}% Vel) | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Burst de Fuerza":
            detalles = f"{hab.duracion_activa:.0f}s (+{hab.porcentaje_buff * 100:.0f}% Fza) | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Disparo Veloz":
            detalles = f"Daño {hab.dano:g} mág. · Vel {hab.velocidad_proyectil:g} | CD {hab.duracion_cooldown:.1f}s"
        elif hasattr(hab, "conejos"):
            detalles = f"Conejo: Vida {hab.vida_conejo} · Vel {hab.velocidad_conejo:.1f} · Daño {hab.dano_conejo:.1f}"
        elif hasattr(hab, "lobos"):
            detalles = f"Lobo: Vida {hab.vida_lobo} · Vel {hab.velocidad_lobo} · Daño {hab.dano_lobo:.1f} (33% desangrado)"
        elif hab.nombre == "Carga de Fuego":
            detalles = (f"Daño {round(hab.dano_base * hab.MULT_CARGA[0], 1):g}-{round(hab.dano_base * hab.MULT_CARGA[5], 1):g}"
                        f" · CD {hab.RECARGA_BASE:g}-{hab.RECARGA_BASE + hab.RECARGA_POR_SEGUNDO * 5:g}s")
        elif hab.nombre == "Cortar":
            detalles = f"Daño {hab.dano} mág. · Vel {hab.velocidad_cuchilla} | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Onda Sonora":
            detalles = f"{len(hab.danos_ondas)} onda(s) · R{hab.radio:.0f} | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Aura Electrica":
            detalles = f"{hab.duracion_activa:.0f}s (+{hab.porcentaje_buff * 100:.0f}% Vel) · {hab.dano_por_segundo}/s | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Golpe de Suerte":
            detalles = f"Azar nv{hab.nivel_efecto} · {hab.ultimo_resultado}"
        elif hab.nombre == "Regeneración Inversa":
            detalles = f"+{hab.curacion} vida / -{hab.costo_energia} En. cada {hab.intervalo:.0f}s (mantén)"
        elif hab.nombre == "Reforzamiento Mágico":
            dureza = hab.dureza if hab.estado == "ACTIVA" else hab.dureza_max
            detalles = f"Dureza {dureza:.0f}/{hab.dureza_max} · {hab.duracion_activa:.0f}s | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Disparo Venenoso":
            detalles = f"Veneno {hab.veneno_total:g} en {hab.veneno_duracion:g}s | CD {hab.duracion_cooldown:g}s"
        elif hab.nombre == "Paso 0":
            detalles = f"Invisible {hab.duracion_activa:.0f}s | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Sombra Araña":
            detalles = f"Inmoviliza {hab.inmovilizacion:.0f}s · Telarañas {len(hab.telaranas)}/{hab.MAX_TELARANAS}"
        else:
            detalles = hab.descripcion[:52]

        txt_det = fuente_det.render(detalles, True, (206, 214, 230))
        pantalla.blit(txt_det, (tarjeta_x + pad, cur_y + 92))

        if hab.mensaje_alerta:
            txt_ale = fuente_mini.render(hab.mensaje_alerta, True, (255, 90, 90))
            pantalla.blit(txt_ale, (tarjeta_x + pad, cur_y + 108))

        cur_y += tarjeta_h + 10

    # Manual de reglas: se muestra como tooltip al pulsar el icono '?' de la cabecera
    if info_abierta == "hab":
        lineas_manual = [
            "Regeneración de energía: +1 cada 3s parado, cada 6s en movimiento.",
            "Combo: +5% de la energía actual al lanzar una habilidad con otra ya activa.",
            "",
            "Mejora con el [+] verde: gasta puntos de nivel (compartidos con stats y arma).",
            "Hitboxes: tecla [H] activa o desactiva el visor.",
        ]
        dibujar_tooltip(pantalla, x - 258, y + 30, "Reglas de habilidades",
                        lineas_manual, fuente_sub, fuente_mini)

    return botones


# -----------------------------
# INVOCACIONES: CONEJO (entidad invocada)
# -----------------------------
_FUENTE_CARA = None

def _fuente_cara():
    """Fuente pequeña cacheada para dibujar la cara ':3' de los conejos."""
    global _FUENTE_CARA
    if _FUENTE_CARA is None:
        _FUENTE_CARA = pygame.font.SysFont("Consolas", 11, bold=True)
    return _FUENTE_CARA


def enemigo_en(punto, enemigos, margen):
    """Enemigo vivo mas cercano al punto marcado, dentro de su radio + margen (clic derecho
    sobre un enemigo => atacarlo). None si el clic cae en terreno libre."""
    cand = [e for e in (enemigos or []) if getattr(e, "vivo", True)]
    cand = [e for e in cand if (e.posicion - punto).length() <= getattr(e, "radio", 0) + margen]
    if not cand:
        return None
    return min(cand, key=lambda e: (e.posicion - punto).length())


class OrdenesSombrias:
    """Control del modo combate compartido por las invocaciones sombrias (conejos, lobos).
    - Mantener la tecla: en guardia (ojos encendidos), esperando la orden del clic derecho.
    - Clic derecho sobre un enemigo: lo persiguen y atacan aunque se mueva, hasta que muera.
    - Clic derecho en terreno libre: van a ese punto. Cerca del jugador: vuelven a seguirlo.
    - Con una orden en curso, volver a mantener la tecla y soltarla sin dar otra orden
      devuelve las criaturas al estado pasivo (seguir al jugador)."""
    RADIO_SELECCION = 30        # margen para considerar que el clic cae sobre un enemigo
    RADIO_LLAMADA = 50          # clic a esta distancia del jugador = llamarlas de vuelta

    def _iniciar_ordenes(self):
        self.modo_combate = False       # tecla mantenida (en guardia)
        self.objetivo = None            # None (seguir), Vector2 (punto) o enemigo (perseguir)
        self._pasivo_al_soltar = False

    def pulsar_tecla_combate(self):
        """Con una orden en curso, marcar la vuelta al estado pasivo al soltar la tecla."""
        self._pasivo_al_soltar = self.objetivo is not None

    def soltar_tecla_combate(self):
        if self._pasivo_al_soltar:
            self.objetivo = None
        self._pasivo_al_soltar = False

    def ordenar(self, punto, jugador, enemigos):
        """Orden del clic derecho (solo mientras se mantiene la tecla)."""
        self._pasivo_al_soltar = False   # una orden nueva sustituye a la vuelta al pasivo
        blanco = enemigo_en(punto, enemigos, self.RADIO_SELECCION)
        if blanco is not None:
            costo = getattr(self, "costo_orden_ataque", 0)
            if costo > 0:
                if jugador.energia < costo:
                    return                 # sin energia no puedes ordenar el ataque
                jugador.energia -= costo
            self.objetivo = blanco
        elif (punto - jugador.posicion).length() <= jugador.radio + self.RADIO_LLAMADA:
            self.objetivo = None
        else:
            self.objetivo = pygame.Vector2(punto)

    def _validar_objetivo(self):
        """Si el enemigo perseguido muere, las criaturas vuelven a seguir al jugador."""
        if self.objetivo is not None and not isinstance(self.objetivo, pygame.Vector2) \
                and not getattr(self.objetivo, "vivo", True):
            self.objetivo = None


class EntidadInvocada:
    """Base de las criaturas invocadas (conejos, lobos). En modo seguir acompanan al
    personaje; en modo combate van hacia un punto o persiguen al enemigo marcado y lo atacan
    por intervalo. Tienen hitbox circular (radio): reciben dano y no se solapan con otros
    cuerpos (ver mundo.resolver_solapamientos). Las subclases fijan radio, masa, aspecto y ataque."""
    INTERVALO_ATAQUE = 1.0      # segundos entre golpes en modo combate
    RANGO_SEGUIR = 90           # a mayor distancia, corre hacia el jugador
    MULT_SEGUIR = 30.0
    MULT_MERODEO = 15.0
    MULT_COMBATE = 30.0
    MERODEO_MIN = 12
    MERODEO_MAX = 45
    RETROCESO_ATAQUE = 3        # puntos de empuje que recibe el atacante al golpear (dano por intervalos)
    radio = 8
    masa = 1.0                  # reparto del empuje al separar cuerpos solapados

    def __init__(self, x, y, vida, velocidad, dano):
        self.posicion = pygame.Vector2(x, y)
        self.vida = vida
        self.vida_max = vida
        self.velocidad = velocidad
        self.dano = dano
        self.tipo_dano = "fisico"
        self.vivo = True
        self.modo_combate = False
        self.destino = pygame.Vector2(x, y)
        self._t_merodeo = random.uniform(0.0, 1.5)
        self._cd_ataque = 0.0
        self.empuje = pygame.Vector2(0, 0)
        self.desangrado = None

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        """Recibe dano directo a la vida y retrocede (1 punto de empuje por punto de dano).
        Devuelve el dano aplicado."""
        d = max(0.0, float(cantidad))
        if d <= 0 or not self.vivo:
            return 0.0
        self.vida = max(0.0, round(self.vida - d, 2))
        if direccion_empuje is not None:
            self.aplicar_empuje(direccion_empuje, d)
        if self.vida <= 0:
            self.vivo = False
        return d

    def atacar(self, objetivo):
        """Inflige dano fisico al objetivo (lo empuja) y retrocede a si mismo para espaciar
        el dano y evitar el dano explosivo en conjunto. Devuelve el dano aplicado."""
        direccion = objetivo.posicion - self.posicion
        if hasattr(objetivo, "recibir_dano"):
            aplicado = objetivo.recibir_dano(self.dano, "fisico", direccion)
        else:
            objetivo.vida = max(0.0, round(getattr(objetivo, "vida", 0) - self.dano, 2))
            aplicado = self.dano
        if aplicado and aplicado > 0:
            self.aplicar_empuje(-direccion, self.RETROCESO_ATAQUE)
        return aplicado

    def aplicar_empuje(self, direccion, puntos):
        """Anade retroceso en la direccion dada (se decae en _actualizar_empuje)."""
        if puntos <= 0:
            return
        d = pygame.Vector2(direccion)
        if d.length_squared() == 0:
            return
        self.empuje += d.normalize() * (puntos * PIXELES_POR_PUNTO_EMPUJE)

    def _actualizar_empuje(self, dt):
        if self.empuje.length_squared() < 0.25:
            self.empuje.update(0, 0)
            return
        paso = self.empuje * min(1.0, dt * 14.0)
        self.posicion += paso
        self.empuje -= paso

    def actualizar(self, dt, jugador, objetivo=None, en_guardia=False):
        """objetivo: None (seguir al jugador), Vector2 (ir al punto) o enemigo (perseguirlo
        y atacarlo). en_guardia: la tecla de la invocacion se esta manteniendo."""
        if self.desangrado is not None:
            self.desangrado.actualizar(dt, self)
            if not self.desangrado.activo:
                self.desangrado = None
        if self.vida <= 0:
            self.vivo = False
            return
        # Ojos encendidos mientras se mantiene la tecla o mientras tenga una orden (la orden
        # persiste aunque se suelte la tecla, para no quitarle movilidad al jugador).
        self.modo_combate = en_guardia or objetivo is not None
        self._cd_ataque = max(0.0, self._cd_ataque - dt)

        if objetivo is not None:
            if not isinstance(objetivo, pygame.Vector2):
                # Enemigo marcado: perseguirlo aunque se mueva y atacarlo al alcanzarlo
                hacia = objetivo.posicion - self.posicion
                rango = self.radio + getattr(objetivo, "radio", 0) + 4
                if hacia.length() <= rango:
                    if self._cd_ataque <= 0:
                        self.atacar(objetivo)
                        self._cd_ataque = self.INTERVALO_ATAQUE
                elif hacia.length() > 2:
                    self.posicion += hacia.normalize() * self.velocidad * dt * self.MULT_COMBATE
            else:
                hacia = objetivo - self.posicion
                if hacia.length() > 4:
                    self.posicion += hacia.normalize() * self.velocidad * dt * self.MULT_COMBATE
            self._actualizar_empuje(dt)
            return

        # Modo seguir: acompanan al personaje (lo siguen y merodean cerca)
        hacia = jugador.posicion - self.posicion
        if hacia.length() > self.RANGO_SEGUIR:
            self.posicion += hacia.normalize() * self.velocidad * dt * self.MULT_SEGUIR
        else:
            self._t_merodeo -= dt
            if self._t_merodeo <= 0:
                self._t_merodeo = random.uniform(0.6, 1.6)
                ang = random.uniform(0, math.tau)
                self.destino = self.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * random.uniform(self.MERODEO_MIN, self.MERODEO_MAX)
            d = self.destino - self.posicion
            if d.length() > 2:
                self.posicion += d.normalize() * self.velocidad * dt * self.MULT_MERODEO
        self._actualizar_empuje(dt)


# -----------------------------
# EFECTO: DESANGRADO (aplicable a cualquier personaje/enemigo)
# -----------------------------
class EfectoDesangrado:
    """Desangrado: 5 golpes de 1 de vida, uno cada 2 s (ignora escudos). El efecto sigue
    activo (y reduce la curacion recibida un 50%) hasta que cae el ultimo golpe. Se cuenta
    por golpes, no por tiempo, para que el dano total no dependa de los FPS. No es
    acumulable: volver a aplicarlo solo reinicia los golpes restantes."""
    DANO = 1
    INTERVALO = 2.0
    GOLPES = 5
    REDUCCION_CURACION = 0.5

    def __init__(self):
        self.dano = self.DANO
        self.intervalo = self.INTERVALO
        self.reduccion_curacion = self.REDUCCION_CURACION
        self.golpes_restantes = self.GOLPES
        self._acum = 0.0

    @property
    def activo(self):
        return self.golpes_restantes > 0

    def refrescar(self):
        """Reinicia los golpes restantes al maximo (sigue siendo un solo efecto, no acumula)."""
        self.golpes_restantes = self.GOLPES

    def actualizar(self, dt, objetivo):
        if self.golpes_restantes <= 0:
            return
        self._acum += dt
        while self._acum >= self.intervalo and self.golpes_restantes > 0:
            self._acum -= self.intervalo
            self.golpes_restantes -= 1
            objetivo.vida = max(0.0, round(objetivo.vida - self.dano, 2))


def aplicar_desangrado(objetivo):
    """Aplica o refresca el desangrado en un objetivo con atributo `desangrado`.
    Sirve para cualquier personaje/enemigo. No acumulable."""
    actual = getattr(objetivo, "desangrado", None)
    if actual is not None and actual.activo:
        actual.refrescar()
    else:
        objetivo.desangrado = EfectoDesangrado()


class EfectoQuemadura:
    """Quemadura: dano por segundo durante una duracion (ignora escudos, como el desangrado).
    No acumulable: volver a aplicarla reinicia la duracion y toma el mayor dano/seg."""
    def __init__(self, dano_por_segundo=1, duracion=5.0):
        self.dano = dano_por_segundo
        self.duracion = duracion
        self.restante = duracion
        self._acum = 0.0

    @property
    def activo(self):
        return self.restante > 0

    def refrescar(self, dano_por_segundo=None, duracion=None):
        if dano_por_segundo is not None:
            self.dano = max(self.dano, dano_por_segundo)
        self.restante = duracion if duracion is not None else self.duracion

    def actualizar(self, dt, objetivo):
        if self.restante <= 0:
            return
        self.restante -= dt
        self._acum += dt
        while self._acum >= 1.0:
            self._acum -= 1.0
            objetivo.vida = max(0.0, round(objetivo.vida - self.dano, 2))
        if self.restante < 0:
            self.restante = 0


class EfectoVeneno:
    """Veneno: `total` de daño MAGICO repartido en `duracion` s, un golpe por segundo
    (total / duracion) y el resto al terminar, para que siempre se aplique el total.
    Pasa por recibir_dano del objetivo, así que lo amortigua su escudo mágico (sin empuje).
    No acumulable: aplicarlo de nuevo lo reemplaza."""
    TIPO_DANO = "magico"

    def __init__(self, total, duracion):
        self.total = total
        self.duracion = duracion
        self.restante = duracion
        self.por_segundo = total / duracion if duracion > 0 else total
        self.aplicado = 0.0
        self._acum = 0.0

    @property
    def activo(self):
        return self.restante > 0

    def actualizar(self, dt, objetivo):
        if self.restante <= 0:
            return
        self.restante -= dt
        self._acum += dt
        while self._acum >= 1.0 and self.aplicado < self.total:
            self._acum -= 1.0
            self._golpear(objetivo, min(self.por_segundo, self.total - self.aplicado))
        if self.restante <= 0:
            self.restante = 0
            if self.total - self.aplicado >= 0.01:     # fracción final del último segundo
                self._golpear(objetivo, self.total - self.aplicado)

    def _golpear(self, objetivo, cantidad):
        # A 2 decimales (como la vida), para que la suma de golpes sea exactamente el total
        cantidad = round(cantidad, 2)
        self.aplicado = round(self.aplicado + cantidad, 2)
        objetivo.recibir_dano(cantidad, self.TIPO_DANO)


def aplicar_veneno(objetivo, total, duracion):
    """Envenena a un objetivo con atributo `veneno`. No acumulable: reinicia el efecto."""
    objetivo.veneno = EfectoVeneno(total, duracion)


def aplicar_quemadura(objetivo, dano_por_segundo=1, duracion=5.0):
    """Aplica o refresca la quemadura en un objetivo con atributo `quemadura`. No acumulable."""
    actual = getattr(objetivo, "quemadura", None)
    if actual is not None and actual.activo:
        actual.refrescar(dano_por_segundo, duracion)
    else:
        objetivo.quemadura = EfectoQuemadura(dano_por_segundo, duracion)


# -----------------------------
# INVOCACIONES: CONEJO (primera invocacion sombria)
# -----------------------------
class Conejo(EntidadInvocada):
    """Esfera verde oscuro con cara ':3' y ojos (los ':') rojos. Primera invocacion sombria.
    En modo combate los ojos brillan con un halo."""
    radio = 8
    masa = 1.0
    COLOR_OJOS = (220, 60, 60)
    COLOR_OJOS_COMBATE = (255, 70, 70)
    COLOR_HALO = (120, 20, 20)
    COLOR_BOCA = (200, 240, 205)

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        pygame.draw.circle(pantalla, (26, 66, 34), (px, py), self.radio)
        pygame.draw.circle(pantalla, (58, 116, 70), (px, py), self.radio, 1)
        fuente = _fuente_cara()
        col_ojos = self.COLOR_OJOS_COMBATE if self.modo_combate else self.COLOR_OJOS
        ojos = fuente.render(":", True, col_ojos)
        boca = fuente.render("3", True, self.COLOR_BOCA)
        x0 = px - (ojos.get_width() + boca.get_width()) // 2
        y0 = py + 1 - ojos.get_height() // 2
        if self.modo_combate:
            # Halo de los ojos (modo combate)
            halo = fuente.render(":", True, self.COLOR_HALO)
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                pantalla.blit(halo, (x0 + dx, y0 + dy))
        pantalla.blit(ojos, (x0, y0))
        pantalla.blit(boca, (x0 + ojos.get_width(), y0))


# -----------------------------
# HABILIDAD DE INVOCACION: CONEJOS
# -----------------------------
class InvocacionConejos(OrdenesSombrias, HabilidadBase):
    """
    Invoca 5 conejos detras del personaje. No puede volver a invocarse hasta que todos
    mueran, y al morir todos entra en 30s de recarga. Si hay 2 o mas vivos, nacen
    floor(vivos/2) conejos nuevos (max 50) cada intervalo, que se alarga cuantos mas haya:
    INTERVALO_REPRO * (1 + vivos / CONEJOS_POR_INTERVALO) (5 vivos 15 s, 20 vivos 30 s).
    Manten la tecla para el modo combate.
    """
    CANTIDAD_INICIAL = 5
    MAX_CONEJOS = 50
    INTERVALO_REPRO = 10.0
    CONEJOS_POR_INTERVALO = 10    # cada 10 conejos vivos suman otro INTERVALO_REPRO de espera
    COOLDOWN_MUERTE = 30.0

    def __init__(self):
        super().__init__(
            nombre="Invocar Conejos",
            descripcion="Invoca 5 conejos detras de ti. Se reproducen si hay 2 o mas vivos, mas lento cuantos mas hay (max 50). Manten la tecla para modo combate; 30s de recarga al morir todos.",
            costo_energia=80,
            duracion_activa=0.0,
            duracion_cooldown=self.COOLDOWN_MUERTE,
            tecla=pygame.K_4,
            tecla_str="4"
        )
        self.conejos = []
        self.timer_reproduccion = 0.0
        self.max_conejos = self.MAX_CONEJOS
        self._iniciar_ordenes()

    @property
    def criaturas(self):
        return self.conejos

    def _aplicar_nivel(self):
        """
        Escalado de los conejos invocados (habilidad nivel 1 a 20):
        - Vida: 5 + 3 cada 4 niveles
        - Velocidad: 3 + 0.5 por nivel
        - Dano: 0.1 + 0.4 por nivel
        - Coste de activacion: 80 de energia (fijo)
        """
        n = self.nivel
        self.vida_conejo = 5 + 3 * (n // 4)
        self.velocidad_conejo = round(3.0 + 0.5 * (n - 1), 2)
        self.dano_conejo = round(0.1 + 0.4 * (n - 1), 2)
        self.costo_energia = 80

    def intervalo_reproduccion(self):
        """Segundos entre camadas: crece con los conejos vivos (reproduccion mas lenta)."""
        return self.INTERVALO_REPRO * (1 + len(self.conejos) / self.CONEJOS_POR_INTERVALO)

    def _invocar(self, jugador, cantidad):
        disponibles = self.max_conejos - len(self.conejos)
        cantidad = min(cantidad, max(0, disponibles))
        if cantidad <= 0:
            return
        rad = math.radians(jugador.angulo)
        atras = pygame.Vector2(-math.sin(rad), math.cos(rad))  # opuesto al frente
        base = jugador.posicion + atras * (jugador.radio + 22)
        for _ in range(cantidad):
            off = pygame.Vector2(random.uniform(-28, 28), random.uniform(-28, 28))
            self.conejos.append(Conejo(base.x + off.x, base.y + off.y,
                                       self.vida_conejo, self.velocidad_conejo, self.dano_conejo))

    def ejecutar_activacion(self, jugador):
        # Estado propio: INVOCADO (no se puede volver a lanzar hasta que mueran todos)
        self.estado = "INVOCADO"
        self.timer_reproduccion = 0.0
        self.objetivo = None
        self._invocar(jugador, self.CANTIDAD_INICIAL)

    def actualizar(self, dt, jugador):
        super().actualizar(dt, jugador)  # alertas y temporizador de recarga

        self._validar_objetivo()
        for c in self.conejos:
            c.actualizar(dt, jugador, self.objetivo, self.modo_combate)
        self.conejos = [c for c in self.conejos if c.vivo]

        # Reproduccion: con 2+ vivos nacen floor(vivos/2) conejos (max 50) cada intervalo,
        # que se alarga cuantos mas conejos vivos hay
        if len(self.conejos) >= 2:
            self.timer_reproduccion += dt
            if self.timer_reproduccion >= self.intervalo_reproduccion():
                self.timer_reproduccion = 0.0
                self._invocar(jugador, len(self.conejos) // 2)
        else:
            self.timer_reproduccion = 0.0

        # Al morir todos: 30s de recarga antes de poder reinvocar
        if self.estado == "INVOCADO" and not self.conejos:
            self.estado = "COOLDOWN"
            self.tiempo_restante_cooldown = self.duracion_cooldown
            self.objetivo = None

    def dibujar_invocaciones(self, pantalla, desplazamiento=(0, 0)):
        for c in self.conejos:
            c.dibujar(pantalla, desplazamiento)


# -----------------------------
# INVOCACIONES: LOBO (segunda invocacion sombria)
# -----------------------------
class Lobo(EntidadInvocada):
    """Lobo invocado: cuerpo gris con orejas y ojos. Segunda invocacion sombria. Al hacer
    dano tiene un 33% de aplicar desangrado al objetivo. En modo combate le brillan los ojos."""
    PROB_DESANGRADO = 0.33
    RANGO_SEGUIR = 110
    MULT_SEGUIR = 26.0
    MULT_MERODEO = 13.0
    MULT_COMBATE = 28.0
    MERODEO_MIN = 18
    MERODEO_MAX = 55
    radio = 11
    masa = 3.0

    def atacar(self, objetivo):
        """Inflige dano fisico y, con 33% de probabilidad, aplica desangrado al objetivo."""
        aplicado = super().atacar(objetivo)
        if aplicado and aplicado > 0 and random.random() < self.PROB_DESANGRADO:
            aplicar_desangrado(objetivo)
        return aplicado

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        r = self.radio
        # Orejas (dos triangulos grises oscuros)
        pygame.draw.polygon(pantalla, (70, 74, 82), [(px - r + 2, py - r + 3), (px - 2, py - r - 4), (px - 2, py - 2)])
        pygame.draw.polygon(pantalla, (70, 74, 82), [(px + r - 2, py - r + 3), (px + 2, py - r - 4), (px + 2, py - 2)])
        # Cuerpo
        pygame.draw.circle(pantalla, (96, 101, 110), (px, py), r)
        pygame.draw.circle(pantalla, (60, 64, 72), (px, py), r, 1)
        # Ojos (brillan en modo combate)
        if self.modo_combate:
            pygame.draw.circle(pantalla, (120, 20, 20), (px - 4, py - 1), 4)
            pygame.draw.circle(pantalla, (120, 20, 20), (px + 4, py - 1), 4)
            col_ojo, r_ojo = (255, 70, 70), 3
        else:
            col_ojo, r_ojo = (220, 60, 60), 2
        pygame.draw.circle(pantalla, col_ojo, (px - 4, py - 1), r_ojo)
        pygame.draw.circle(pantalla, col_ojo, (px + 4, py - 1), r_ojo)


# -----------------------------
# HABILIDAD DE INVOCACION: LOBOS
# -----------------------------
class InvocacionLobos(OrdenesSombrias, HabilidadBase):
    """
    Invoca 3 lobos detras del personaje. No puede volver a invocarse hasta que todos mueran,
    y al morir todos entra en 30s de recarga. Segunda de las 10 Artes de las Sombras. Sus
    golpes tienen un 33% de aplicar desangrado. Manten la tecla para el modo combate.
    """
    CANTIDAD = 3
    MAX_INVOCACIONES = 3
    COOLDOWN_MUERTE = 30.0

    def __init__(self):
        super().__init__(
            nombre="Invocar Lobos",
            descripcion="Invoca 3 lobos detras de ti. Sus golpes tienen 33% de causar desangrado. Manten la tecla para modo combate; 30s de recarga al morir todos.",
            costo_energia=90,
            duracion_activa=0.0,
            duracion_cooldown=self.COOLDOWN_MUERTE,
            tecla=pygame.K_4,
            tecla_str="4"
        )
        self.lobos = []
        self.max_invocaciones = self.MAX_INVOCACIONES
        self._iniciar_ordenes()

    @property
    def criaturas(self):
        return self.lobos

    def _aplicar_nivel(self):
        """
        Escalado de los lobos invocados (habilidad nivel 1 a 20):
        - Vida: 10 + 3 por nivel            (nv1=10, nv20=67)
        - Velocidad: 10 + 2 cada 5 niveles  (nv1=10, nv20=18)
        - Dano: 8 a 30 lineal por nivel     (nv1=8, nv20=30)
        - Coste de activacion: 90 de energia (fijo)
        """
        n = self.nivel
        self.vida_lobo = 10 + 3 * (n - 1)
        self.velocidad_lobo = 10 + 2 * (n // 5)
        self.dano_lobo = round(min(30.0, 8.0 + (30.0 - 8.0) * (n - 1) / 19.0), 2)
        self.costo_energia = 90
        self.costo_orden_ataque = round(5 + 5 * (n - 1) / 19.0)   # orden de ataque: 5 -> 10

    def _invocar(self, jugador, cantidad):
        rad = math.radians(jugador.angulo)
        atras = pygame.Vector2(-math.sin(rad), math.cos(rad))  # opuesto al frente
        base = jugador.posicion + atras * (jugador.radio + 26)
        for _ in range(cantidad):
            off = pygame.Vector2(random.uniform(-34, 34), random.uniform(-34, 34))
            self.lobos.append(Lobo(base.x + off.x, base.y + off.y,
                                   self.vida_lobo, self.velocidad_lobo, self.dano_lobo))

    def ejecutar_activacion(self, jugador):
        # Estado propio: INVOCADO (no se puede relanzar hasta que mueran todos)
        self.estado = "INVOCADO"
        self.objetivo = None
        self._invocar(jugador, self.CANTIDAD)

    def actualizar(self, dt, jugador):
        super().actualizar(dt, jugador)  # alertas y temporizador de recarga

        self._validar_objetivo()
        for l in self.lobos:
            l.actualizar(dt, jugador, self.objetivo, self.modo_combate)
        self.lobos = [l for l in self.lobos if l.vivo]

        # Al morir todos: 30s de recarga antes de poder reinvocar
        if self.estado == "INVOCADO" and not self.lobos:
            self.estado = "COOLDOWN"
            self.tiempo_restante_cooldown = self.duracion_cooldown
            self.objetivo = None

    def dibujar_invocaciones(self, pantalla, desplazamiento=(0, 0)):
        for l in self.lobos:
            l.dibujar(pantalla, desplazamiento)


# -----------------------------
# HABILIDAD: CARGA DE FUEGO (disparo rápido o mantener para cargar)
# -----------------------------
class CargaDeFuego(HabilidadBase):
    """
    Esfera de fuego con dos modos: pulsar = disparo rápido; mantener = cargar (máx 5s)
    para más daño y mayor tamaño, soltando al liberar la tecla. Cada segundo completo de
    carga sube el multiplicador del daño base (x0.6 sin carga -> x2.0 a 5 s), alarga la
    quemadura (1 de daño por segundo, de 2 s a 7 s) y la recarga (8 s -> 15 s).

    La energía se cobra en tiempo real: al pulsar se paga el coste base y, cada segundo
    completo de carga, la diferencia hasta el coste de ese nivel de carga. Si no hay
    energía para el siguiente segundo, la carga se detiene en el nivel ya pagado.
    """
    # Por segundo completo de carga (0 = sin carga): multiplicador del daño base, segundos de
    # quemadura, coste de energía acumulado y radio visual
    MULT_CARGA = {0: 0.6, 1: 0.8, 2: 1.0, 3: 1.3, 4: 1.6, 5: 2.0}
    QUEMADURA_CARGA = {0: 2.0, 1: 3.0, 2: 4.0, 3: 5.0, 4: 6.0, 5: 7.0}
    QUEMADURA_DANO = 1                 # daño por segundo de la quemadura
    RECARGA_BASE = 8.0                 # recarga tras un disparo sin carga
    RECARGA_POR_SEGUNDO = 1.4          # cada segundo de carga suma recarga (5 s -> 15 s)
    COSTO_CARGA = {0: 15, 1: 20, 2: 25, 3: 30, 4: 35, 5: 45}
    RADIO_CARGA = {0: 6, 1: 8, 2: 11, 3: 14, 4: 17, 5: 22}
    TIEMPO_MAX_CARGA = 5.0
    VELOCIDAD = 10.0

    def __init__(self):
        super().__init__(
            nombre="Carga de Fuego",
            descripcion="Esfera de fuego: pulsa para disparo rápido o mantén para cargar (máx 5s). Más carga = más daño, quemadura y recarga.",
            costo_energia=15,
            duracion_activa=0.0,
            duracion_cooldown=self.RECARGA_BASE,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.cargable = True
        self.cargando = False
        self.tiempo_carga = 0.0
        self.tier_pagado = 0            # Nivel de carga cuya energía ya se cobró
        self.carga_detenida = False     # True si se quedó sin energía para seguir cargando
        self.pos_carga = pygame.Vector2(0, 0)

    def _aplicar_nivel(self):
        """Daño base: 20 + 1 por nivel (desde nivel 1). El coste base (sin carga) es 15."""
        self.dano_base = 20 + (self.nivel - 1)
        self.costo_energia = self.COSTO_CARGA[0]

    def _tier(self, tiempo):
        return max(0, min(5, int(tiempo)))

    def obtener_costo_base(self, jugador):
        return self.COSTO_CARGA[0]  # coste al pulsar; cada segundo de carga cobra su parte

    def iniciar_carga(self, jugador):
        """Al pulsar: cobra el coste base y comienza a cargar (si está lista y hay energía)."""
        if self.cargando or self.estado != "LISTA":
            return
        if jugador.energia < self.COSTO_CARGA[0]:
            self.mensaje_alerta = "Sin energía"
            self.tiempo_alerta = 1.5
            return
        jugador.energia -= self.COSTO_CARGA[0]
        self.cargando = True
        self.tiempo_carga = 0.0
        self.tier_pagado = 0
        self.carga_detenida = False

    def _cobrar_carga(self, jugador):
        """Cobra cada segundo completo de carga; si no alcanza la energía, detiene la carga."""
        while self.tier_pagado < self._tier(self.tiempo_carga):
            siguiente = self.tier_pagado + 1
            costo_extra = self.COSTO_CARGA[siguiente] - self.COSTO_CARGA[self.tier_pagado]
            if jugador.energia < costo_extra:
                self.carga_detenida = True
                self.tiempo_carga = float(self.tier_pagado)
                self.mensaje_alerta = f"Sin energía para cargar (Req. {costo_extra})"
                self.tiempo_alerta = 2.0
                return
            jugador.energia -= costo_extra
            self.tier_pagado = siguiente

    def soltar_carga(self, jugador):
        """Al soltar: dispara la esfera con el daño/tamaño de la carga ya pagada."""
        if not self.cargando:
            return
        self.cargando = False
        self.carga_detenida = False
        tier = self.tier_pagado

        dano = round(self.dano_base * self.MULT_CARGA[tier], 1)
        radio = self.RADIO_CARGA[tier]
        rad = math.radians(jugador.angulo)
        dx, dy = math.sin(rad), -math.cos(rad)
        origen = jugador.posicion + pygame.Vector2(dx, dy) * (jugador.radio + radio + 2)
        jugador.proyectiles.append(ProyectilFuego(origen.x, origen.y, dx, dy, self.VELOCIDAD, dano, radio,
                                                  self.QUEMADURA_DANO, self.QUEMADURA_CARGA[tier]))

        # La recarga depende de la carga disparada (8 s sin carga -> 15 s a 5 s)
        self.duracion_cooldown = round(self.RECARGA_BASE + self.RECARGA_POR_SEGUNDO * tier, 1)
        self.estado = "COOLDOWN"
        self.tiempo_restante_cooldown = self.duracion_cooldown

    def actualizar(self, dt, jugador):
        super().actualizar(dt, jugador)
        if self.cargando:
            if not self.carga_detenida:
                self.tiempo_carga = min(self.TIEMPO_MAX_CARGA, self.tiempo_carga + dt)
                self._cobrar_carga(jugador)
            rad = math.radians(jugador.angulo)
            dx, dy = math.sin(rad), -math.cos(rad)
            radio = self.RADIO_CARGA[self._tier(self.tiempo_carga)]
            self.pos_carga = jugador.posicion + pygame.Vector2(dx, dy) * (jugador.radio + radio + 2)

    def dibujar_invocaciones(self, pantalla, desplazamiento=(0, 0)):
        """Dibuja la esfera que se está cargando pegada al frente del personaje."""
        if not self.cargando:
            return
        radio = self.RADIO_CARGA[self._tier(self.tiempo_carga)]
        px = round(self.pos_carga.x - desplazamiento[0])
        py = round(self.pos_carga.y - desplazamiento[1])
        pygame.draw.circle(pantalla, (255, 110, 20), (px, py), radio + 2)
        pygame.draw.circle(pantalla, (255, 170, 55), (px, py), radio)
        pygame.draw.circle(pantalla, (255, 240, 180), (px, py), max(2, radio - 3))


# -----------------------------
# CATÁLOGO DE HABILIDADES DISPONIBLES
# -----------------------------
# -----------------------------
# HABILIDAD 6: AURA ELECTRICA
# -----------------------------
class AuraElectrica(HabilidadBase):
    """
    Aura electrica que rodea al personaje mientras esta activa:
    - Buff de velocidad sobre la velocidad base.
    - Dana por segundo a los enemigos que entren en su radio (pendiente de que existan).
    - Autodano al portador de 0.5/s (1 cada 2s) que cuenta como dano MAGICO
      (lo amortigua el escudo magico del propio personaje).
    """
    RADIO_AURA = 100  # Radio del aura en pixeles (alcance del dano por segundo)
    COSTO_BASE = 20       # Coste de energia en nivel 1
    COSTO_POR_NIVEL = 2   # Coste extra por cada nivel (siempre entero)

    def __init__(self):
        super().__init__(
            nombre="Aura Electrica",
            descripcion="Aura electrica que te sigue: +velocidad y dano por segundo a enemigos cercanos. Te cuesta 0.5 de vida/s (dano magico).",
            costo_energia=20,
            duracion_activa=10.0,
            duracion_cooldown=40.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self._t_autodano = 0.0  # Acumulador del autodano por segundo
        self._t_dano_enemigos = 0.0  # Acumulador del dano por segundo a enemigos

    def _aplicar_nivel(self):
        """
        Escalado (nivel 1 a 20):
        - coste: 20 En., +2 por nivel (entero: 20 -> 58 en nivel 20)
        - duracion: 10s, +2.5s cada 5 niveles (tope 20s en nivel 20)
        - cooldown: 40s, +5s cada 5 niveles (tope 60s en nivel 20)
        - buff de velocidad: +5%, +2.5% cada 5 niveles (tope +15% en nivel 20)
        - dano a enemigos: 1 + (nivel // 5) por segundo (1 -> 5)
        - autodano magico al portador: 0.5 por segundo (fijo)
        """
        n = self.nivel
        self.costo_energia = self.COSTO_BASE + self.COSTO_POR_NIVEL * (n - 1)
        self.duracion_activa = min(20.0, 10.0 + 2.5 * (n // 5))
        self.duracion_cooldown = min(60.0, 40.0 + 5.0 * (n // 5))
        self.porcentaje_buff = min(0.15, round(0.05 + 0.025 * (n // 5), 3))
        self.dano_por_segundo = 1 + (n // 5)
        self.autodano_por_segundo = 0.5

    def aplicar_efecto_activo(self, jugador):
        # El buff de velocidad se aplica en Personaje.actualizar_velocidad.
        self._t_autodano = 0.0

    def zona_dano(self, jugador):
        """Centro y radio del aura, para danar enemigos cuando existan."""
        return pygame.Vector2(jugador.posicion), AuraElectrica.RADIO_AURA

    def actualizar(self, dt, jugador):
        super().actualizar(dt, jugador)
        if self.estado == "ACTIVA":
            # Autodano magico al portador (lo amortigua su escudo magico)
            self._t_autodano += dt
            while self._t_autodano >= 1.0:
                self._t_autodano -= 1.0
                jugador.recibir_dano(self.autodano_por_segundo, "magico")
            # El dano a los enemigos se aplica en actualizar_dano_enemigos() (llamado desde el mundo).

    def actualizar_dano_enemigos(self, dt, enemigos, jugador):
        """Dano por segundo (magico) a los enemigos dentro del aura, mientras esta ACTIVA."""
        if self.estado != "ACTIVA" or not enemigos:
            return
        self._t_dano_enemigos += dt
        while self._t_dano_enemigos >= 1.0:
            self._t_dano_enemigos -= 1.0
            centro, radio = self.zona_dano(jugador)
            for enemigo in enemigos:
                if not getattr(enemigo, "vivo", True):
                    continue
                r_e = getattr(enemigo, "radio", 0)
                if (enemigo.posicion - centro).length() <= radio + r_e:
                    if hasattr(enemigo, "recibir_dano"):
                        enemigo.recibir_dano(self.dano_por_segundo, "magico",
                                             enemigo.posicion - jugador.posicion)

    def dibujar_aura(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Dibuja el aura electrica translucida con chispas en el borde."""
        ox, oy = desplazamiento
        cx = round(jugador.posicion.x - ox)
        cy = round(jugador.posicion.y - oy)
        r = AuraElectrica.RADIO_AURA

        capa = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
        pygame.draw.circle(capa, (80, 180, 255, 45), (r + 3, r + 3), r)
        pygame.draw.circle(capa, (130, 220, 255, 110), (r + 3, r + 3), r, 3)
        pantalla.blit(capa, (cx - r - 3, cy - r - 3))

        for _ in range(8):
            ang = random.uniform(0, math.tau)
            x1 = cx + math.cos(ang) * (r - 5)
            y1 = cy + math.sin(ang) * (r - 5)
            x2 = cx + math.cos(ang) * (r + 7)
            y2 = cy + math.sin(ang) * (r + 7)
            pygame.draw.line(pantalla, (200, 240, 255), (round(x1), round(y1)), (round(x2), round(y2)), 2)


# -----------------------------
# HABILIDAD 7: REFORZAMIENTO MÁGICO
# -----------------------------
def _valor_por_tramo(nivel, tramos):
    """Devuelve el valor del último tramo alcanzado. tramos = ((nivel_desde, valor), ...) en orden."""
    valor = tramos[0][1]
    for desde, v in tramos:
        if nivel >= desde:
            valor = v
    return valor


class ReforzamientoMagico(HabilidadBase):
    """
    Campo de fuerza alrededor del personaje que bloquea daño físico y mágico.
    Absorbe todo el daño recibido hasta agotar su dureza; si se agota antes de que
    termine la duración, el campo se rompe, entra en recarga y el daño sobrante pasa
    a los escudos del personaje y a su vida. El daño de terreno no lo atraviesa porque
    no pasa por recibir_dano (lago profundo y veneno van directo a la vida).
    """
    FACTOR_RADIO = 1.10                 # El campo es un 10% más grande que el personaje
    COLOR_CAMPO = (135, 206, 250)       # Azul celeste
    GROSOR_CAMPO = 2                    # Solo contorno, delgado (sin relleno)
    DUREZA_BASE = 200                   # Dureza en nivel 1
    DUREZA_POR_NIVEL = 15               # Dureza extra por cada nivel
    DUREZA_NIVEL_MAX = 500              # Bono final: en nivel 20 la dureza llega a 500
    # Valores por tramos de nivel: (nivel desde el que aplica, valor)
    TRAMOS_DURACION = ((1, 1.0), (5, 2.0), (10, 3.0), (15, 4.0), (20, 6.0))
    TRAMOS_COSTE = ((1, 25), (5, 30), (10, 35), (15, 40), (20, 50))
    TRAMOS_RECARGA = ((1, 10.0), (5, 15.0), (10, 20.0), (15, 25.0), (20, 35.0))

    def __init__(self):
        super().__init__(
            nombre="Reforzamiento Mágico",
            descripcion="Campo de fuerza que bloquea daño físico y mágico hasta agotar su dureza.",
            costo_energia=25,
            duracion_activa=1.0,
            duracion_cooldown=10.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.dureza = 0.0

    def _aplicar_nivel(self):
        """
        Escalado (nivel 1 a 20):
        - dureza: 200, +15 por nivel (470 en nivel 19) y 500 en nivel 20 (bono final)
        - duración: 1s (nv1), 2s (nv5), 3s (nv10), 4s (nv15), 6s (nv20)
        - coste: 25 (nv1), 30 (nv5), 35 (nv10), 40 (nv15), 50 (nv20)
        - recarga: 10s (nv1), 15s (nv5), 20s (nv10), 25s (nv15), 35s (nv20)
        """
        n = self.nivel
        if n >= self.nivel_max:
            self.dureza_max = self.DUREZA_NIVEL_MAX
        else:
            self.dureza_max = self.DUREZA_BASE + self.DUREZA_POR_NIVEL * (n - 1)
        self.duracion_activa = _valor_por_tramo(n, self.TRAMOS_DURACION)
        self.costo_energia = _valor_por_tramo(n, self.TRAMOS_COSTE)
        self.duracion_cooldown = _valor_por_tramo(n, self.TRAMOS_RECARGA)

    def aplicar_efecto_activo(self, jugador):
        self.dureza = float(self.dureza_max)

    def aplicar_efecto_cooldown(self, jugador):
        self.dureza = 0.0

    def absorber_dano(self, cantidad, jugador, eficacia=1.0):
        """
        Absorbe daño (físico o mágico) con la dureza del campo y devuelve el sobrante.
        Con eficacia < 1 (campo secundario cuando hay dos activos) cada punto absorbido
        gasta 1/eficacia de dureza. Si la dureza llega a 0, el campo se rompe y pasa a recarga.
        """
        if self.estado != "ACTIVA" or cantidad <= 0:
            return cantidad
        absorbido = min(cantidad, self.dureza * eficacia)
        self.dureza = max(0.0, round(self.dureza - absorbido / eficacia, 2))
        if self.dureza <= 0:
            self.estado = "COOLDOWN"
            self.tiempo_restante_activo = 0.0
            self.tiempo_restante_cooldown = self.duracion_cooldown
            self.aplicar_efecto_cooldown(jugador)
            self.mensaje_alerta = "¡Campo roto!"
            self.tiempo_alerta = 2.0
        return round(cantidad - absorbido, 2)

    def dibujar_aura(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Dibuja solo el contorno azul celeste del campo, un 10% más grande que el personaje."""
        cx = round(jugador.posicion.x - desplazamiento[0])
        cy = round(jugador.posicion.y - desplazamiento[1])
        radio = round(jugador.radio * self.FACTOR_RADIO)
        pygame.draw.circle(pantalla, self.COLOR_CAMPO, (cx, cy), radio, self.GROSOR_CAMPO)


# -----------------------------
# HABILIDAD 8: REGENERACIÓN INVERSA
# -----------------------------
class RegeneracionInversa(HabilidadBase):
    """
    Habilidad mágica que se mantiene presionada (sin recarga): mientras la tecla está
    pulsada, cada intervalo completo cobra energía y cura vida, como la carga de la
    Carga de Fuego. Si no hay energía para el siguiente intervalo, deja de curar hasta
    volver a pulsar. Con la vida al máximo no cobra ni cura.
    Usa la interfaz de habilidades cargables (iniciar_carga / soltar_carga) para que
    el bucle del mundo la active al pulsar y la detenga al soltar.
    """
    NIVEL_MAX = 10
    COSTO_MEJORA = 2                    # Sube de nivel como las armas: 2 puntos
    COLOR_AURA = (255, 105, 180)        # Rosa: mismo contorno que Reforzamiento Mágico
    # Tramos por nivel: (nivel desde el que aplica, (vida curada, energía gastada, intervalo en s))
    TRAMOS = ((1, (1, 10, 2.0)), (3, (2, 15, 2.0)), (6, (3, 20, 2.0)), (9, (4, 25, 2.0)), (10, (6, 40, 3.0)))

    def __init__(self):
        super().__init__(
            nombre="Regeneración Inversa",
            descripcion="Mantén pulsado: cura vida a cambio de energía en cada intervalo. Sin recarga.",
            costo_energia=10,
            duracion_activa=0.0,
            duracion_cooldown=0.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.nivel_max = self.NIVEL_MAX
        self.costo_mejora = self.COSTO_MEJORA
        self.cargable = True        # Se activa al pulsar y se detiene al soltar
        self.canalizando = False
        self.tiempo_tick = 0.0

    def _aplicar_nivel(self):
        """
        Escalado (nivel 1 a 10), por tramos:
        - nv1-2: +1 vida / -10 En. cada 2s
        - nv3-5: +2 vida / -15 En. cada 2s
        - nv6-8: +3 vida / -20 En. cada 2s
        - nv9:   +4 vida / -25 En. cada 2s
        - nv10:  +6 vida / -40 En. cada 3s
        """
        self.curacion, self.costo_energia, self.intervalo = _valor_por_tramo(self.nivel, self.TRAMOS)

    def iniciar_carga(self, jugador):
        """Al pulsar: empieza a regenerar si hay energía para al menos un intervalo."""
        if self.canalizando:
            return
        if jugador.energia < self.costo_energia:
            self.mensaje_alerta = f"¡Falta energía! (Req. {self.costo_energia})"
            self.tiempo_alerta = 2.0
            return
        self.canalizando = True
        self.estado = "ACTIVA"
        self.tiempo_tick = 0.0

    def soltar_carga(self, jugador):
        """Al soltar: deja de regenerar (el intervalo en curso no se cobra)."""
        self._detener()

    def _detener(self):
        self.canalizando = False
        self.estado = "LISTA"
        self.tiempo_tick = 0.0

    def actualizar(self, dt, jugador):
        # Solo temporizador de alertas: sin duración ni recarga (no usa el ciclo ACTIVA -> COOLDOWN)
        if self.tiempo_alerta > 0:
            self.tiempo_alerta -= dt
            if self.tiempo_alerta <= 0:
                self.mensaje_alerta = ""
        if not self.canalizando:
            return
        if jugador.vida >= jugador.vida_max:
            self.tiempo_tick = 0.0   # Vida llena: no cobra ni cura
            return
        self.tiempo_tick += dt
        while self.tiempo_tick >= self.intervalo:
            self.tiempo_tick -= self.intervalo
            if jugador.energia < self.costo_energia:
                self.mensaje_alerta = f"Sin energía para curar (Req. {self.costo_energia})"
                self.tiempo_alerta = 2.0
                self._detener()
                return
            jugador.energia -= self.costo_energia
            curacion = self.curacion * factor_regeneracion(self, jugador)
            jugador.curar(curacion)

    def dibujar_aura(self, pantalla, jugador, desplazamiento=(0, 0)):
        """Contorno rosa (mismo tamaño y grosor que Reforzamiento Mágico) mientras está activa."""
        cx = round(jugador.posicion.x - desplazamiento[0])
        cy = round(jugador.posicion.y - desplazamiento[1])
        radio = round(jugador.radio * ReforzamientoMagico.FACTOR_RADIO)
        pygame.draw.circle(pantalla, self.COLOR_AURA, (cx, cy), radio, ReforzamientoMagico.GROSOR_CAMPO)


# -----------------------------
# EFECTO: REGENERACIÓN DE GOLPE DE SUERTE
# -----------------------------
class RegeneracionSuerte(HabilidadBase):
    """
    Versión de Regeneración Inversa que otorga Golpe de Suerte: cura sola, sin pulsar
    nada ni gastar energía, durante su duración. Muestra el mismo contorno rosa.
    """
    COLOR_AURA = RegeneracionInversa.COLOR_AURA

    def __init__(self, duracion, curacion, intervalo):
        super().__init__(
            nombre="Regeneración Inversa",
            descripcion="Curación automática otorgada por Golpe de Suerte.",
            costo_energia=0,
            duracion_activa=duracion,
            duracion_cooldown=0.0,
            tecla=None,
            tecla_str=""
        )
        self.curacion = curacion
        self.intervalo = intervalo
        self.curaciones_hechas = 0
        self.otorgada = True

    def aplicar_efecto_activo(self, jugador):
        self.curaciones_hechas = 0

    def actualizar(self, dt, jugador):
        if self.estado == "ACTIVA":
            # Curaciones según el tiempo transcurrido (redondeado para no perder la última por decimales)
            transcurrido = min(self.duracion_activa, self.duracion_activa - self.tiempo_restante_activo + dt)
            debidas = int(round(transcurrido, 6) // self.intervalo)
            while self.curaciones_hechas < debidas:
                self.curaciones_hechas += 1
                curacion = self.curacion * factor_regeneracion(self, jugador)
                jugador.curar(curacion)
        super().actualizar(dt, jugador)

    def dibujar_aura(self, pantalla, jugador, desplazamiento=(0, 0)):
        RegeneracionInversa.dibujar_aura(self, pantalla, jugador, desplazamiento)


def factor_regeneracion(regen, jugador):
    """Con la otorgada activa, la Regeneración equipada cura al 50% (ver factor_duplicado)."""
    activas = [h for h in jugador.habilidades_en_efecto() if h.nombre == regen.nombre and h.estado == "ACTIVA"]
    return factor_duplicado(regen, activas)


# -----------------------------
# HABILIDAD: PASO 0 (potenciador de invisibilidad)
# -----------------------------
class Paso0(HabilidadBase):
    """
    Potenciador mágico: vuelve invisible al personaje (no a sus invocaciones) durante un
    tiempo. Invisible, los enemigos no lo detectan (no lo miran ni inician ataques contra él),
    pero lo que lo toque sí le hace daño. Su arma se oculta salvo durante el golpe y sus
    ataques (proyectiles, cuchillas, ondas...) sí se ven. Dura todo su tiempo aunque ataque
    o reciba daño; la recarga empieza al terminar. El mundo se ve oscurecido como dentro de
    un arbusto (sin oscurecerse el doble). Nivel máximo 10; cada mejora cuesta 2 puntos.
    """
    NIVEL_MAX = 10
    COSTO_MEJORA = 2                    # Como Regeneración Inversa
    da_invisibilidad = True             # Personaje.invisible lo consulta
    # Tramos por nivel: (nivel desde el que aplica, valor)
    TRAMOS_DURACION = ((1, 3.0), (3, 4.0), (5, 5.0), (8, 6.0), (10, 8.0))
    TRAMOS_COSTE = ((1, 30), (3, 35), (5, 40), (8, 50), (10, 60))
    TRAMOS_RECARGA = ((1, 6.0), (3, 8.0), (5, 10.0), (8, 12.0), (10, 16.0))

    def __init__(self):
        super().__init__(
            nombre="Paso 0",
            descripcion="Te vuelve invisible: los enemigos no te detectan, pero puedes recibir daño. Tus invocaciones y ataques sí se ven.",
            costo_energia=30,
            duracion_activa=3.0,
            duracion_cooldown=6.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.nivel_max = self.NIVEL_MAX
        self.costo_mejora = self.COSTO_MEJORA

    def _aplicar_nivel(self):
        """
        Escalado por tramos (nivel 1 a 10):
        - nv1-2: 3s invisible, 30 En., recarga 6s
        - nv3-4: 4s, 35 En., recarga 8s
        - nv5-7: 5s, 40 En., recarga 10s
        - nv8-9: 6s, 50 En., recarga 12s
        - nv10:  8s, 60 En., recarga 16s
        """
        n = self.nivel
        self.duracion_activa = _valor_por_tramo(n, self.TRAMOS_DURACION)
        self.costo_energia = _valor_por_tramo(n, self.TRAMOS_COSTE)
        self.duracion_cooldown = _valor_por_tramo(n, self.TRAMOS_RECARGA)


# -----------------------------
# HABILIDAD 9: GOLPE DE SUERTE
# -----------------------------
class GolpeDeSuerte(HabilidadBase):
    """
    Al lanzarla otorga un resultado aleatorio (sin coste extra de energía):
    Burst de Fuerza, Destello, Reforzamiento Mágico, Regeneración Inversa, Aura Eléctrica,
    Paso 0 (al nivel que marca el tramo de Golpe de Suerte, sin pasar del máximo de cada una),
    energía al máximo, escudos al máximo, Disparo Venenoso (resultado NEGATIVO: no dispara,
    envenena al portador con la mitad del daño del veneno de ese nivel y la misma duración)
    o nada (30%). Los 9 resultados que no son "nada" se reparten el resto a partes iguales
    (7.78% cada uno). En nivel 20 "nada" baja a 5% y el resto se reparte igual (10.56% cada uno).

    Bloqueo: Golpe de Suerte queda ACTIVA (no se puede volver a lanzar) mientras dure
    lo otorgado y solo al terminar empieza su recarga normal:
    - Habilidad otorgada: dura 5/10/15/20/30s según el tramo (la regeneración usa sus propios tiempos).
      Si termina antes (ej. el Reforzamiento se rompe), la recarga empieza en ese momento.
    - Resultado instantáneo (energía, escudos o nada): espera básica de 5s (2s en nivel 20).
    """
    NADA = "Nada"
    ENERGIA = "Energía al máximo"
    ESCUDOS = "Escudos al máximo"
    REGENERACION = "Regeneración Inversa"
    VENENO = "Disparo Venenoso"
    FACTOR_AUTOVENENO = 0.5              # El portador recibe la mitad del daño del veneno
    # Habilidades que puede otorgar (se activan como efecto temporal, sin recarga propia)
    EFECTOS = {
        "Burst de Fuerza": BurstDeFuerza,
        "Destello": Destello,
        "Reforzamiento Mágico": ReforzamientoMagico,
        "Aura Electrica": AuraElectrica,
        "Paso 0": Paso0,
    }
    RESULTADOS = ("Burst de Fuerza", "Destello", "Reforzamiento Mágico", REGENERACION,
                  ENERGIA, "Aura Electrica", ESCUDOS, "Paso 0", VENENO)
    PROB_NADA = 0.30
    PROB_NADA_NIVEL_MAX = 0.05
    # Tramos por nivel: (nivel desde el que aplica, valor)
    TRAMOS_COSTE = ((1, 15), (5, 20), (10, 25), (15, 30), (20, 50))
    TRAMOS_RECARGA = ((1, 5.0), (5, 8.0), (10, 12.0), (15, 15.0), (20, 20.0))
    TRAMOS_NIVEL_EFECTO = ((1, 1), (5, 5), (10, 10), (15, 15), (20, 20))
    # Duración de la habilidad otorgada (sustituye a la suya propia), en segundos
    TRAMOS_DURACION_EFECTO = ((1, 5.0), (5, 10.0), (10, 15.0), (15, 20.0), (20, 30.0))
    ESPERA_INSTANTANEO = 5.0             # Bloqueo tras energía, escudos o nada
    ESPERA_INSTANTANEO_NIVEL_MAX = 2.0   # En nivel 20 la espera básica baja a 2s
    # Regeneración otorgada: (duración s, vida curada, intervalo s)
    TRAMOS_REGENERACION = ((1, (4.0, 1, 2.0)), (5, (6.0, 1, 2.0)), (10, (8.0, 1, 2.0)),
                           (15, (10.0, 2, 2.0)), (20, (10.0, 2, 1.0)))

    def __init__(self):
        super().__init__(
            nombre="Golpe de Suerte",
            descripcion="Otorga un efecto aleatorio: una habilidad, energía o escudos al máximo, o nada.",
            costo_energia=15,
            duracion_activa=0.0,
            duracion_cooldown=5.0,
            tecla=pygame.K_2,
            tecla_str="2"
        )
        self.ultimo_resultado = "—"
        self.efecto_actual = None   # Efecto otorgado que mantiene bloqueada la habilidad

    def _aplicar_nivel(self):
        """
        Escalado por tramos (nivel 1 a 20):
        - coste: 15 (nv1), 20 (nv5), 25 (nv10), 30 (nv15), 50 (nv20)
        - recarga: 5s (nv1), 8s (nv5), 12s (nv10), 15s (nv15), 20s (nv20)
        - nivel de la habilidad otorgada: 1 (nv1-4), 5 (nv5-9), 10 (nv10-14), 15 (nv15-19), 20 (nv20)
        - duración de la habilidad otorgada: 5s, 10s, 15s, 20s, 30s (mismos tramos)
        - espera tras un resultado instantáneo: 5s (2s en nivel 20)
        - probabilidad de "nada": 30% (5% en nivel 20)
        """
        n = self.nivel
        self.costo_energia = _valor_por_tramo(n, self.TRAMOS_COSTE)
        self.duracion_cooldown = _valor_por_tramo(n, self.TRAMOS_RECARGA)
        self.nivel_efecto = _valor_por_tramo(n, self.TRAMOS_NIVEL_EFECTO)
        self.duracion_efecto = _valor_por_tramo(n, self.TRAMOS_DURACION_EFECTO)
        self.espera_instantaneo = self.ESPERA_INSTANTANEO_NIVEL_MAX if n >= self.nivel_max else self.ESPERA_INSTANTANEO
        self.regeneracion = _valor_por_tramo(n, self.TRAMOS_REGENERACION)
        self.prob_nada = self.PROB_NADA_NIVEL_MAX if n >= self.nivel_max else self.PROB_NADA

    def probabilidades(self):
        """Diccionario resultado -> probabilidad (suma 1.0)."""
        prob_resto = (1.0 - self.prob_nada) / len(self.RESULTADOS)
        probs = {r: prob_resto for r in self.RESULTADOS}
        probs[self.NADA] = self.prob_nada
        return probs

    def sortear(self):
        probs = self.probabilidades()
        return random.choices(list(probs), weights=list(probs.values()))[0]

    def aplicar_resultado(self, resultado, jugador):
        """Aplica el resultado al jugador y devuelve el texto a mostrar."""
        if resultado == self.ENERGIA:
            jugador.energia = jugador.energia_max
            return resultado
        if resultado == self.ESCUDOS:
            jugador.escudo = jugador.escudo_max
            jugador.escudo_magico = jugador.escudo_magico_max
            return resultado
        if resultado == self.VENENO:
            # Resultado negativo instantáneo: el veneno de ese nivel, a la mitad, sobre el portador
            disparo = DisparoVenenoso()
            while disparo.nivel < self.nivel_efecto and disparo.subir_nivel():
                pass
            aplicar_veneno(jugador, round(disparo.veneno_total * self.FACTOR_AUTOVENENO, 2), disparo.veneno_duracion)
            return f"{resultado} nv{disparo.nivel}: ¡te envenena!"
        if resultado == self.REGENERACION:
            efecto = RegeneracionSuerte(*self.regeneracion)   # Conserva sus propios tiempos
        elif resultado in self.EFECTOS:
            efecto = self.EFECTOS[resultado]()
            while efecto.nivel < self.nivel_efecto and efecto.subir_nivel():
                pass
            efecto.duracion_activa = self.duracion_efecto     # Duración según el tramo de Golpe de Suerte
            efecto.otorgada = True
        else:
            return self.NADA
        jugador.agregar_efecto(efecto)
        efecto.ejecutar_activacion(jugador)
        self.efecto_actual = efecto
        return f"{resultado} nv{efecto.nivel}" if resultado in self.EFECTOS else resultado

    def ejecutar_activacion(self, jugador):
        """Sortea y aplica el resultado; queda bloqueada (ACTIVA) hasta que termine lo otorgado."""
        self.efecto_actual = None
        self.ultimo_resultado = self.aplicar_resultado(self.sortear(), jugador)
        self.mensaje_alerta = f"¡{self.ultimo_resultado}!"
        self.tiempo_alerta = 2.5
        self.estado = "ACTIVA"
        if self.efecto_actual is not None:
            self.duracion_activa = self.efecto_actual.duracion_activa
        else:
            self.duracion_activa = self.espera_instantaneo
        self.tiempo_restante_activo = self.duracion_activa

    def actualizar(self, dt, jugador):
        """Con un efecto otorgado, el bloqueo dura lo que dure el efecto; después empieza la recarga."""
        if self.estado == "ACTIVA" and self.efecto_actual is not None:
            if self.tiempo_alerta > 0:
                self.tiempo_alerta -= dt
                if self.tiempo_alerta <= 0:
                    self.mensaje_alerta = ""
            efecto = self.efecto_actual
            if efecto.estado == "ACTIVA" and efecto in jugador.efectos_extra:
                self.tiempo_restante_activo = efecto.tiempo_restante_activo
                return
            # El efecto terminó (o se rompió): empieza la recarga normal
            self.efecto_actual = None
            self.estado = "COOLDOWN"
            self.tiempo_restante_activo = 0.0
            self.tiempo_restante_cooldown = self.duracion_cooldown
            return
        super().actualizar(dt, jugador)


# -----------------------------
# EFECTO: INMOVILIZADO (telarana de la Sombra Arana)
# -----------------------------
class EfectoInmovilizado:
    """Inmoviliza a un enemigo (no se mueve) durante una duracion. Puede hacer dano por
    segundo (telarana de nivel 20): es dano MAGICO, asi que lo amortigua el escudo magico
    del objetivo (sin empuje, porque esta inmovilizado). No acumulable: se sobreescribe."""
    TIPO_DANO = "magico"

    def __init__(self, duracion, dano_por_segundo=0):
        self.duracion = duracion
        self.restante = duracion
        self.dano = dano_por_segundo
        self._acum = 0.0

    @property
    def activo(self):
        return self.restante > 0

    def actualizar(self, dt, objetivo):
        if self.restante <= 0:
            return
        self.restante -= dt
        if self.dano > 0:
            self._acum += dt
            while self._acum >= 1.0:
                self._acum -= 1.0
                objetivo.recibir_dano(self.dano, self.TIPO_DANO)
        if self.restante < 0:
            self.restante = 0


def aplicar_inmovilizacion(objetivo, duracion, dano_por_segundo=0):
    """Inmoviliza a un objetivo con atributo `inmovilizado`. No acumulable."""
    objetivo.inmovilizado = EfectoInmovilizado(duracion, dano_por_segundo)


class Telarana:
    """Telarana en el suelo (trampa de un solo uso): inmoviliza al primer enemigo que la pisa.
    Invisible para los enemigos (no la evitan); visible para el jugador."""
    def __init__(self, x, y, radio, duracion_inmoviliza, dano_por_segundo=0):
        self.posicion = pygame.Vector2(x, y)
        self.radio = radio
        self.duracion = duracion_inmoviliza
        self.dano = dano_por_segundo
        self.activa = True

    def intentar_atrapar(self, enemigos):
        if not self.activa:
            return
        for enemigo in enemigos:
            if not getattr(enemigo, "vivo", True) or not hasattr(enemigo, "inmovilizado"):
                continue
            r_e = getattr(enemigo, "radio", 0)
            if (enemigo.posicion - self.posicion).length() <= self.radio + r_e:
                aplicar_inmovilizacion(enemigo, self.duracion, self.dano)
                self.activa = False   # un solo uso
                return

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        cx = round(self.posicion.x - desplazamiento[0])
        cy = round(self.posicion.y - desplazamiento[1])
        r = int(self.radio)
        col = (170, 185, 210)
        for frac in (1.0, 0.66, 0.33):
            pygame.draw.circle(pantalla, col, (cx, cy), max(1, int(r * frac)), 1)
        for i in range(8):
            ang = math.tau * i / 8
            ex = cx + int(math.cos(ang) * r)
            ey = cy + int(math.sin(ang) * r)
            pygame.draw.line(pantalla, col, (cx, cy), (ex, ey), 1)


class Arana(EntidadInvocada):
    """Sombra arana: esfera pequena con cara de arana y 8 patas. 1 HP, sin ataque.
    Al llegar al punto ordenado teje una telarana y desaparece (lo gestiona la habilidad)."""
    radio = 5
    masa = 0.6
    COLOR = (30, 26, 40)
    COLOR_BORDE = (72, 62, 92)
    COLOR_OJOS = (200, 60, 60)
    COLOR_OJOS_COMBATE = (255, 60, 60)
    COLOR_PATAS = (18, 16, 26)

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        px = round(self.posicion.x - desplazamiento[0])
        py = round(self.posicion.y - desplazamiento[1])
        r = self.radio
        for i in range(8):
            ang = math.tau * i / 8 + math.pi / 8
            mx = px + int(math.cos(ang) * (r + 2))
            my = py + int(math.sin(ang) * (r + 1))
            lx = px + int(math.cos(ang) * (r + 6))
            ly = py + int(math.sin(ang) * (r + 6))
            pygame.draw.line(pantalla, self.COLOR_PATAS, (px, py), (mx, my), 1)
            pygame.draw.line(pantalla, self.COLOR_PATAS, (mx, my), (lx, ly), 1)
        pygame.draw.circle(pantalla, self.COLOR, (px, py), r)
        pygame.draw.circle(pantalla, self.COLOR_BORDE, (px, py), r, 1)
        col = self.COLOR_OJOS_COMBATE if self.modo_combate else self.COLOR_OJOS
        pygame.draw.circle(pantalla, col, (px - 2, py - 1), 1)
        pygame.draw.circle(pantalla, col, (px + 2, py - 1), 1)


class InvocacionArana(OrdenesSombrias, HabilidadBase):
    """Sombra Arana (Arte de Sombra 3): invoca una arana (1 HP). Manten la tecla (ojos rojos)
    y marca un punto con clic derecho; al llegar teje una telarana (un solo uso) que inmoviliza
    al primer enemigo que la pise. Max 3 telaranas (la nueva quita la mas vieja). 5s de recarga."""
    MAX_TELARANAS = 3
    COOLDOWN = 5.0
    VELOCIDAD = 6.0

    def __init__(self):
        super().__init__(
            nombre="Sombra Araña",
            descripcion="Invoca una araña (1 HP). Mantén la tecla (ojos rojos) y marca un punto con clic derecho; al llegar teje una telaraña (un solo uso) que inmoviliza al primer enemigo que la pise. Máx 3 telarañas; 5s de recarga.",
            costo_energia=50,
            duracion_activa=0.0,
            duracion_cooldown=self.COOLDOWN,
            tecla=pygame.K_3,
            tecla_str="3"
        )
        self.aranas = []
        self.telaranas = []
        self.tope_criaturas = 1
        self._iniciar_ordenes()

    @property
    def criaturas(self):
        return self.aranas

    def _aplicar_nivel(self):
        """Escalado (nivel 1 a 20):
        - coste: 50 En. (nv1) -> 100 En. (nv20), progresivo
        - inmovilizacion: 5s (nv1) -> 20s (nv20), progresivo
        - dano de la telarana: 0, salvo nivel 20 (1 por segundo mientras dura la inmovilizacion)
        """
        n = self.nivel
        self.costo_energia = round(50 + (100 - 50) * (n - 1) / 19)
        self.inmovilizacion = round(5.0 + (20.0 - 5.0) * (n - 1) / 19, 1)
        self.dano_telarana = 1 if n >= self.nivel_max else 0

    def ejecutar_activacion(self, jugador):
        self.estado = "INVOCADO"
        self.objetivo = None
        rad = math.radians(jugador.angulo)
        atras = pygame.Vector2(-math.sin(rad), math.cos(rad))   # opuesto al frente
        base = jugador.posicion + atras * (jugador.radio + 16)
        self.aranas = [Arana(base.x, base.y, 1, self.VELOCIDAD, 0)]

    def ordenar(self, punto, jugador, enemigos):
        """La arana siempre va a un PUNTO (no persigue enemigos)."""
        self._pasivo_al_soltar = False
        self.objetivo = pygame.Vector2(punto)

    def _tejer(self, jugador, punto):
        radio = round(jugador.radio * 1.6)   # un poco mas grande que el jugador
        self.telaranas.append(Telarana(punto.x, punto.y, radio, self.inmovilizacion, self.dano_telarana))
        if len(self.telaranas) > self.MAX_TELARANAS:
            self.telaranas.pop(0)            # quita la mas vieja
        self.aranas = []
        self.objetivo = None
        self.estado = "COOLDOWN"
        self.tiempo_restante_cooldown = self.duracion_cooldown

    def actualizar(self, dt, jugador):
        super().actualizar(dt, jugador)
        if self.estado == "INVOCADO" and self.aranas:
            arana = self.aranas[0]
            arana.actualizar(dt, jugador, self.objetivo, self.modo_combate)
            if not arana.vivo:
                # Murio antes de tejer: recarga sin telarana
                self.aranas = []
                self.objetivo = None
                self.estado = "COOLDOWN"
                self.tiempo_restante_cooldown = self.duracion_cooldown
            elif isinstance(self.objetivo, pygame.Vector2):
                if (self.objetivo - arana.posicion).length() <= arana.radio + 6:
                    self._tejer(jugador, self.objetivo)

    def actualizar_telaranas(self, dt, enemigos):
        for t in self.telaranas:
            t.intentar_atrapar(enemigos)
        self.telaranas = [t for t in self.telaranas if t.activa]

    def dibujar_telaranas(self, pantalla, desplazamiento=(0, 0)):
        for t in self.telaranas:
            t.dibujar(pantalla, desplazamiento)

    def dibujar_invocaciones(self, pantalla, desplazamiento=(0, 0)):
        for a in self.aranas:
            a.dibujar(pantalla, desplazamiento)


HABILIDADES_DISPONIBLES = {
    "Destello": Destello,
    "Burst de Fuerza": BurstDeFuerza,
    "Disparo Veloz": DisparoVeloz,
    "Cortar": Cortar,
    "Onda Sonora": OndaSonora,
    "Invocar Conejos": InvocacionConejos,
    "Invocar Lobos": InvocacionLobos,
    "Carga de Fuego": CargaDeFuego,
    "Aura Electrica": AuraElectrica,
    "Reforzamiento Mágico": ReforzamientoMagico,
    "Regeneración Inversa": RegeneracionInversa,
    "Golpe de Suerte": GolpeDeSuerte,
    "Sombra Araña": InvocacionArana,
    "Paso 0": Paso0,
    "Disparo Venenoso": DisparoVenenoso
}

def crear_habilidad(nombre):
    cls = HABILIDADES_DISPONIBLES.get(nombre)
    if cls:
        return cls()
    return None
