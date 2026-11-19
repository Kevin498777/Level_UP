import pygame
import math
from herramientas import EspadaLigera
from habilidades import (combinar_buffs, factor_duplicado, PIXELES_POR_PUNTO_EMPUJE,
                         actualizar_anulacion_escudo_magico, actualizar_ralentizacion)

# Masa del personaje frente a otros cuerpos (conejo 1, lobo 3): apenas lo desplazan sus
# invocaciones, pero los cuerpos fijos (maniqui) si lo frenan.
MASA_PERSONAJE = 100.0

# --- Escudo del personaje (reserva que absorbe daño físico) ---
# Progresión del escudo: inicial 0, +5 por mejora hasta un máximo de 15 y, a partir
# de ahí, +2 por mejora. El escudo mágico (Fase 2) compartirá este mismo esquema.
ESCUDO_INICIAL = 0
ESCUDO_INCREMENTO_GRANDE = 5      # Incremento por mejora mientras el máximo sea < ESCUDO_TOPE_TRAMO
ESCUDO_TOPE_TRAMO = 15           # A partir de este máximo el incremento baja a +2
ESCUDO_INCREMENTO_NORMAL = 2     # Incremento por mejora una vez superado el tramo inicial

# Reparto del daño físico: se bloquea un 20% del daño total; del resto, el escudo
# absorbe el 70% y el 30% pasa a la vida. Si el escudo no alcanza, el sobrante va a vida.
ESCUDO_BLOQUEO_FISICO = 0.20
ESCUDO_REPARTO_ESCUDO = 0.70
ESCUDO_REPARTO_VIDA = 0.30

# Regeneración del escudo: tras REGEN_ESCUDO_RETRASO s sin recibir daño en el escudo,
# recupera REGEN_ESCUDO_POR_SEGUNDO por segundo hasta su máximo.
REGEN_ESCUDO_RETRASO = 10.0
REGEN_ESCUDO_POR_SEGUNDO = 1.0

# Reparto del daño mágico: se bloquea un 10% del daño total; del resto, el escudo mágico
# absorbe el 90% y el 10% pasa a la vida. El escudo mágico comparte la progresión y la
# regeneración del escudo físico (inicial 0, +5 hasta 15, luego +2; regen +1/s tras 10s).
ESCUDOM_BLOQUEO = 0.10
ESCUDOM_REPARTO_ESCUDO = 0.90
ESCUDOM_REPARTO_VIDA = 0.10


def repartir_dano(cantidad, tipo_dano, escudo_disp):
    """Reparto comun del dano entre escudo y vida (personaje, maniqui...).
    Devuelve (absorbido por el escudo, dano a la vida). Si la parte del escudo supera el
    escudo disponible, el sobrante pasa tambien a la vida."""
    if tipo_dano == "magico":
        bloqueo, reparto_escudo, reparto_vida = ESCUDOM_BLOQUEO, ESCUDOM_REPARTO_ESCUDO, ESCUDOM_REPARTO_VIDA
    else:
        bloqueo, reparto_escudo, reparto_vida = ESCUDO_BLOQUEO_FISICO, ESCUDO_REPARTO_ESCUDO, ESCUDO_REPARTO_VIDA
    reducido = cantidad * (1.0 - bloqueo)
    parte_escudo = reducido * reparto_escudo
    absorbido = min(parte_escudo, escudo_disp)
    dano_vida = reducido * reparto_vida + (parte_escudo - absorbido)
    return absorbido, dano_vida

# -----------------------------
# CLASE PERSONAJE
# -----------------------------
class Personaje:
    def __init__(self, nombre, x, y, tamano, velocidad, vida, fuerza, energia, escudo, color, habilidades=None, herramienta=None, escudo_magico=0):
        self.nombre = nombre
        self.posicion = pygame.Vector2(x, y)
        self.destino = pygame.Vector2(x, y)

        # Ángulo de orientación en grados (0° = Arriba, 180° = Abajo)
        self.angulo = 0.0

        # Estadísticas principales
        self.tamano = tamano                       # Empieza estático en 1
        self.velocidad_base = float(velocidad)     # Velocidad base fija (1 a 4)
        self.velocidad = float(velocidad)          # Velocidad actual (afectada por buffs/debuffs)
        self.vida = vida                           # Vida (15 a 25)
        self.vida_max = vida                       # Tope de curación (orbes frutales)
        self.fuerza_base = float(fuerza)           # Fuerza base fija (1 a 5)
        self.fuerza = float(fuerza)                # Fuerza actual
        self.cadencia = 0.0                        # Bonus de cadencia de ataque (golpes/seg); se mejora con puntos
        self.energia_max = energia                 # Energía máxima inicial (1 a 100)
        self.energia = energia                     # Energía actual
        # Escudo físico: reserva que se gasta al recibir daño físico (reemplaza a la antigua Defensa).
        self.escudo_max = float(escudo)            # Máximo actual del escudo físico
        self.escudo = float(escudo)                # Escudo físico disponible
        self.tiempo_sin_dano_escudo = 0.0          # Segundos sin recibir daño en el escudo (para la regen)
        # Escudo mágico: reserva que absorbe daño mágico (habilidades que consumen energía).
        self.escudo_magico_max = float(escudo_magico)
        self.escudo_magico = float(escudo_magico)
        self.tiempo_sin_dano_escudo_magico = 0.0
        self.anulacion_escudo_magico = 0.0   # Segundos restantes de escudo magico anulado (Cortar)
        self.escudo_magico_guardado = 0.0    # Valor que recupera al terminar la anulacion
        self.color = color

        # Progresión: nivel del personaje y puntos de mejora (empieza con 3)
        self.nivel = 1
        self.puntos_mejora = 3
        self.habilidades = habilidades if habilidades is not None else []
        # Efectos temporales de habilidades no equipadas (ej. los que otorga Golpe de Suerte)
        self.efectos_extra = []
        self.herramienta = herramienta if herramienta is not None else EspadaLigera()

        # Proyectiles activos disparados por el personaje (Disparo Veloz)
        self.proyectiles = []

        # Temporizador para la regeneración global de energía
        self.tiempo_regen = 0.0

        # Terreno: True si el personaje está pisando un charco de agua (-50% vel)
        self.en_agua = False
        self.debuff_agua = 0.50
        # Zona profunda de los lagos grandes (-80% vel y daño por segundo)
        self.en_agua_profunda = False
        self.debuff_agua_profunda = 0.80
        self.tiempo_dano_lago = 0.0

        # Vegetación: arbusto en el que está metido (None si no está en ninguno)
        self.arbusto_actual = None
        self.oculto = False          # True = no puede ser visto desde afuera (pensado para futuros personajes)
        self.tiempo_veneno = 0.0     # Acumulador del daño de hierba venenosa
        self.desangrado = None       # Efecto de desangrado activo (None si no tiene)
        self.ralentizacion = 0.0     # Debuff de velocidad recibido (ej. Onda Sonora), 0.20 = -20%
        self.tiempo_ralentizacion = 0.0
        self.masa = MASA_PERSONAJE   # Al separar cuerpos solapados, las invocaciones le ceden el paso

        # Empuje acumulado pendiente de aplicar (retroceso por recibir daño)
        self.empuje = pygame.Vector2(0, 0)

        # Radio visual base escalado por el tamaño
        self.radio = int(20 * self.tamano)

        # Hitbox del personaje (coincide exactamente con el contorno físico exterior)
        self.hitbox = pygame.Rect(
            round(x - self.radio),
            round(y - self.radio),
            self.radio * 2,
            self.radio * 2
        )

    def habilidades_en_efecto(self):
        """Habilidades equipadas más los efectos temporales activos (ej. de Golpe de Suerte)."""
        return self.habilidades + self.efectos_extra

    def agregar_efecto(self, efecto):
        """Añade un efecto temporal ya activado; si hay otro con el mismo nombre, lo reemplaza."""
        for viejo in [e for e in self.efectos_extra if e.nombre == efecto.nombre]:
            viejo.estado = "COOLDOWN"
            viejo.aplicar_efecto_cooldown(self)
            self.efectos_extra.remove(viejo)
        self.efectos_extra.append(efecto)

    def actualizar_efectos(self, dt):
        """Actualiza los efectos temporales y quita los que ya terminaron (no tienen recarga)."""
        for efecto in self.efectos_extra:
            efecto.actualizar(dt, self)
        self.efectos_extra = [e for e in self.efectos_extra if e.estado == "ACTIVA"]

    def curar(self, cantidad):
        """Cura vida sin pasar de vida_max. Si hay desangrado activo, la curacion se reduce
        un 50%. Devuelve la vida realmente recuperada."""
        cantidad = max(0.0, float(cantidad))
        if self.desangrado is not None and self.desangrado.activo:
            cantidad *= (1.0 - self.desangrado.reduccion_curacion)
        nueva = min(self.vida_max, round(self.vida + cantidad, 2))
        curado = round(nueva - self.vida, 2)
        self.vida = nueva
        return curado

    def actualizar_desangrado(self, dt):
        """Tiquea el desangrado activo (resta vida por intervalo, ignora escudos) y lo retira
        cuando termina."""
        if self.desangrado is None:
            return
        self.desangrado.actualizar(dt, self)
        if not self.desangrado.activo:
            self.desangrado = None

    def actualizar_ralentizacion(self, dt):
        """Descuenta la ralentizacion recibida (ej. Onda Sonora) y la retira al terminar."""
        actualizar_ralentizacion(self, dt)

    def esta_en_movimiento(self):
        """Devuelve True si el personaje se está desplazando hacia su destino."""
        return (self.destino - self.posicion).length() > 2.0

    def calcular_dano_total(self):
        """Calcula el daño total actual considerando fuerza y herramienta equipada."""
        if self.herramienta and self.herramienta.activa:
            return self.herramienta.calcular_dano(self)
        return round(self.fuerza, 2)

    def subir_stat(self, nombre):
        """Gasta 1 punto de mejora en la estadística indicada (incrementos fijos)."""
        if self.puntos_mejora <= 0:
            return False
        if nombre == "vida":
            self.vida_max += 2
            self.vida += 2
        elif nombre == "fuerza":
            self.fuerza_base = round(self.fuerza_base + 0.2, 2)
            # Si no hay un Burst activo, reflejar el cambio en la fuerza actual
            if not any(h.nombre == "Burst de Fuerza" and h.estado == "ACTIVA" for h in self.habilidades_en_efecto()):
                self.fuerza = self.fuerza_base
        elif nombre == "velocidad":
            self.velocidad_base = round(self.velocidad_base + 0.1, 2)
        elif nombre == "cadencia":
            self.cadencia = round(self.cadencia + 0.1, 2)
        elif nombre == "energia":
            self.energia_max += 5
            self.energia = min(self.energia_max, self.energia + 5)
        elif nombre == "escudo":
            incremento = ESCUDO_INCREMENTO_GRANDE if self.escudo_max < ESCUDO_TOPE_TRAMO else ESCUDO_INCREMENTO_NORMAL
            self.escudo_max += incremento
            self.escudo = self.escudo_max          # Al mejorarlo, se rellena al nuevo máximo
        elif nombre == "escudo_magico":
            incremento = ESCUDO_INCREMENTO_GRANDE if self.escudo_magico_max < ESCUDO_TOPE_TRAMO else ESCUDO_INCREMENTO_NORMAL
            self.escudo_magico_max += incremento
            if self.anulacion_escudo_magico > 0:
                self.escudo_magico_guardado = self.escudo_magico_max   # se rellena al terminar la anulacion
            else:
                self.escudo_magico = self.escudo_magico_max
        else:
            return False
        self.puntos_mejora -= 1
        return True

    def subir_nivel(self):
        """(Debug) Sube de nivel al personaje y otorga 3 puntos de mejora."""
        self.nivel += 1
        self.puntos_mejora += 3
        return self.nivel

    def actualizar_regeneracion(self, dt):
        """
        Regeneración global de energía:
        - Parado: +1 de energía cada 3.0 segundos.
        - En movimiento: +1 de energía cada 6.0 segundos.
        """
        if self.energia < self.energia_max:
            intervalo = 6.0 if self.esta_en_movimiento() else 3.0
            self.tiempo_regen += dt
            if self.tiempo_regen >= intervalo:
                self.energia = min(self.energia_max, self.energia + 1)
                self.tiempo_regen -= intervalo
        else:
            self.tiempo_regen = 0.0

    def actualizar_regeneracion_escudo(self, dt):
        """
        Regeneración del escudo físico: tras REGEN_ESCUDO_RETRASO s sin recibir daño en
        el escudo, recupera REGEN_ESCUDO_POR_SEGUNDO por segundo hasta su máximo.
        Recibir daño reinicia el contador (ver recibir_dano).
        """
        if self.escudo >= self.escudo_max:
            self.escudo = self.escudo_max
            return
        self.tiempo_sin_dano_escudo += dt
        if self.tiempo_sin_dano_escudo >= REGEN_ESCUDO_RETRASO:
            self.escudo = min(self.escudo_max, round(self.escudo + REGEN_ESCUDO_POR_SEGUNDO * dt, 2))

    def actualizar_regeneracion_escudo_magico(self, dt):
        """
        Regeneración del escudo mágico: igual que el físico, tras REGEN_ESCUDO_RETRASO s
        sin recibir daño mágico, recupera REGEN_ESCUDO_POR_SEGUNDO por segundo hasta su máximo.
        Mientras está anulado (pasiva de Cortar) se queda en 0 y no se regenera.
        """
        if actualizar_anulacion_escudo_magico(self, dt):
            return
        if self.escudo_magico >= self.escudo_magico_max:
            self.escudo_magico = self.escudo_magico_max
            return
        self.tiempo_sin_dano_escudo_magico += dt
        if self.tiempo_sin_dano_escudo_magico >= REGEN_ESCUDO_RETRASO:
            self.escudo_magico = min(self.escudo_magico_max, round(self.escudo_magico + REGEN_ESCUDO_POR_SEGUNDO * dt, 2))

    def actualizar_velocidad(self):
        """
        Calcula la velocidad neta acumulando modificadores:
        - Destello activo: +50% (+0.50)
        - Destello cooldown (fatiga): -20% (-0.20)
        - Espada sacada: -20% (-0.20) acumulable (ej. cooldown -20% + espada -20% = -40% total)
        """
        modificador = 0.0

        # Modificadores de habilidades (equipadas y efectos temporales). Si la misma
        # habilidad está activa dos veces (equipada y de Golpe de Suerte), los buffs se
        # suman: la otorgada al 100% y la equipada al 50% (combinar_buffs). La fatiga no cambia.
        buffs_destello = []
        fatiga_destello = 0.0
        buffs_aura = []
        for hab in self.habilidades_en_efecto():
            if hab.nombre == "Destello":
                if hab.estado == "ACTIVA":
                    buffs_destello.append(hab)
                elif hab.estado == "COOLDOWN":
                    fatiga_destello = max(fatiga_destello, hab.porcentaje_debuff)
            elif hab.nombre == "Aura Electrica" and hab.estado == "ACTIVA":
                buffs_aura.append(hab)
        modificador += combinar_buffs(buffs_destello) - fatiga_destello + combinar_buffs(buffs_aura)

        # Modificador acumulable de herramienta activa
        if self.herramienta and self.herramienta.activa:
            modificador -= self.herramienta.debuff_velocidad
            # Arco tensando la cuerda: ralentizacion extra mientras carga
            modificador -= getattr(self.herramienta, "ralentizacion_carga", 0.0)

        # Ralentizacion recibida (ej. Onda Sonora)
        modificador -= self.ralentizacion

        # Charco de agua: -50% (zona profunda de un lago grande: -80%)
        if self.en_agua_profunda:
            modificador -= self.debuff_agua_profunda
        elif self.en_agua:
            modificador -= self.debuff_agua

        # Velocidad final con umbral mínimo seguro
        self.velocidad = max(0.4, round(self.velocidad_base * (1.0 + modificador), 2))

    def mover(self, limites_mundo, centro_mundo=None, radio_mundo=None, obstaculos=None, obstaculos_circulares=None):
        """
        Mueve al personaje hacia el destino, rota su orientación y actualiza su hitbox.
        - limites_mundo: rectángulo (min_x, min_y, max_x, max_y) de seguridad.
        - centro_mundo / radio_mundo: límite circular del mapa (opcional).
        - obstaculos: lista de rocas (pygame.Rect en .rect) que no se pueden atravesar.
        - obstaculos_circulares: lista de (centro, radio) sólidos, ej. arbustos demasiado pequeños para entrar.
        """
        min_x, min_y, max_x, max_y = limites_mundo
        posicion_previa = self.posicion.copy()

        direccion = self.destino - self.posicion
        distancia = direccion.length()

        # Actualizar ángulo de rotación:
        # 0° = Hacia arriba (0, -1), 180° = Hacia abajo (0, 1), 90° = Derecha (1, 0)
        if distancia > 0.1:
            self.angulo = math.degrees(math.atan2(direccion.x, -direccion.y)) % 360.0

        if distancia > self.velocidad:
            paso = direccion.normalize() * self.velocidad
        else:
            paso = direccion

        # Rocas cercanas a la trayectoria de este frame (para no revisar todas)
        cercanas = []
        if obstaculos:
            zona = pygame.Rect(0, 0, 0, 0)
            zona.center = (round(self.posicion.x), round(self.posicion.y))
            margen = round(paso.length() + self.radio * 2 + 2)
            zona.inflate_ip(margen * 2, margen * 2)
            cercanas = [obs.rect for obs in obstaculos if zona.colliderect(obs.rect)]

        alcance = paso.length() + self.radio * 2 + 2
        circulos_cercanos = [
            (c, r) for c, r in (obstaculos_circulares or [])
            if (c - self.posicion).length() <= alcance + r
        ]

        # Sub-pasos: a velocidades altas (ej. 99) el personaje avanza en tramos cortos
        # para no "atravesar" rocas pequeñas de un solo salto
        tramo_max = max(1.0, self.radio * 0.5)
        sub_pasos = max(1, math.ceil(paso.length() / tramo_max))
        sub_paso = paso / sub_pasos

        for _ in range(sub_pasos):
            self.posicion += sub_paso

            # Colisión con rocas (círculo vs rectángulo): empujar al personaje fuera de la roca
            for rect in cercanas:
                self._resolver_colision_rect(rect)

            # Colisión con obstáculos circulares (círculo vs círculo)
            for centro, radio in circulos_cercanos:
                separacion = self.posicion - centro
                dist = separacion.length()
                minimo = radio + self.radio
                if dist < minimo:
                    normal = separacion.normalize() if dist > 0.0001 else pygame.Vector2(1, 0)
                    self.posicion = centro + normal * minimo

        # Restringir posición dentro del mundo jugable
        self.posicion.x = max(min_x + self.radio, min(self.posicion.x, max_x - self.radio))
        self.posicion.y = max(min_y + self.radio, min(self.posicion.y, max_y - self.radio))

        # Límite circular del mapa: no puede salir del círculo
        if centro_mundo is not None and radio_mundo is not None:
            desde_centro = self.posicion - centro_mundo
            limite = radio_mundo - self.radio
            if desde_centro.length() > limite:
                self.posicion = centro_mundo + desde_centro.normalize() * limite

        # Si quedó bloqueado (destino dentro de una roca o fuera del círculo), detenerse
        if self.esta_en_movimiento() and (self.posicion - posicion_previa).length() < 0.05:
            self.destino = self.posicion.copy()

        # Actualizar hitbox rectangular
        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)

    def _resolver_colision_rect(self, rect):
        """Separa el círculo del personaje de un rectángulo sólido si se están solapando."""
        # Punto del rectángulo más cercano al centro del personaje
        cerca_x = max(rect.left, min(self.posicion.x, rect.right))
        cerca_y = max(rect.top, min(self.posicion.y, rect.bottom))
        separacion = pygame.Vector2(self.posicion.x - cerca_x, self.posicion.y - cerca_y)
        dist = separacion.length()

        if dist >= self.radio:
            return  # Sin colisión

        if dist > 0.0001:
            # Empujar en la dirección de la separación
            self.posicion += separacion.normalize() * (self.radio - dist)
        else:
            # El centro quedó dentro del rectángulo: sacar por el lado más cercano
            empujes = [
                (self.posicion.x - rect.left + self.radio, pygame.Vector2(-1, 0)),
                (rect.right - self.posicion.x + self.radio, pygame.Vector2(1, 0)),
                (self.posicion.y - rect.top + self.radio, pygame.Vector2(0, -1)),
                (rect.bottom - self.posicion.y + self.radio, pygame.Vector2(0, 1)),
            ]
            cantidad, normal = min(empujes, key=lambda e: e[0])
            self.posicion += normal * cantidad

    def aplicar_empuje(self, direccion, puntos):
        """Añade retroceso: 'puntos' de empuje en la dirección indicada (alejándose del atacante)."""
        if puntos <= 0:
            return
        d = pygame.Vector2(direccion)
        if d.length_squared() == 0:
            return
        self.empuje += d.normalize() * (puntos * PIXELES_POR_PUNTO_EMPUJE)

    def actualizar_empuje(self, dt, centro_mundo=None, radio_mundo=None):
        """Aplica progresivamente el retroceso acumulado (con decaimiento) y respeta el límite del mundo."""
        if self.empuje.length_squared() < 0.25:
            self.empuje.update(0, 0)
            return
        paso = self.empuje * min(1.0, dt * 14.0)
        self.posicion += paso
        self.empuje -= paso

        if centro_mundo is not None and radio_mundo is not None:
            desde_centro = self.posicion - centro_mundo
            limite = radio_mundo - self.radio
            if desde_centro.length() > limite:
                self.posicion = centro_mundo + desde_centro.normalize() * limite

        self.hitbox.x = round(self.posicion.x - self.radio)
        self.hitbox.y = round(self.posicion.y - self.radio)

    def recibir_dano(self, cantidad, tipo_dano="fisico", direccion_empuje=None):
        """
        Aplica daño al personaje según su tipo y devuelve el daño total aplicado.
        - "fisico" (armas, conejos): lo amortigua el escudo físico. Se bloquea un 20% del
          daño total; del resto, el 70% lo absorbe el escudo y el 30% pasa a la vida.
        - "magico" (habilidades que consumen energía): lo amortigua el escudo mágico. Se
          bloquea un 10% del daño total; del resto, el 90% lo absorbe el escudo mágico y
          el 10% pasa a la vida.
        En ambos casos, si la parte del escudo supera el escudo disponible, el sobrante
        pasa también a la vida. Por cada punto de daño aplicado se genera 1 punto de
        empuje (retroceso); 'direccion_empuje' va del atacante hacia este personaje.
        """
        cantidad = max(0.0, float(cantidad))
        if cantidad <= 0:
            return 0.0

        # Campos de fuerza activos (ej. Reforzamiento Mágico) absorben primero el daño
        # físico o mágico; solo el sobrante llega a los escudos y a la vida. Con dos campos
        # activos, absorbe primero el otorgado por Golpe de Suerte (100%) y luego el
        # equipado al 50% de eficacia (factor_duplicado).
        campos = sorted((h for h in self.habilidades_en_efecto()
                         if h.estado == "ACTIVA" and hasattr(h, "absorber_dano")),
                        key=lambda h: h.otorgada, reverse=True)
        for campo in campos:
            cantidad = campo.absorber_dano(cantidad, self, factor_duplicado(campo, campos))
        if cantidad <= 0:
            return 0.0

        escudo_disp = self.escudo_magico if tipo_dano == "magico" else self.escudo
        absorbido, dano_vida = repartir_dano(cantidad, tipo_dano, escudo_disp)
        dano_total = round(absorbido + dano_vida, 2)

        # Descontar del escudo correspondiente y cortar su regeneración
        if tipo_dano == "magico":
            self.escudo_magico = max(0.0, round(self.escudo_magico - absorbido, 2))
            self.tiempo_sin_dano_escudo_magico = 0.0
        else:
            self.escudo = max(0.0, round(self.escudo - absorbido, 2))
            self.tiempo_sin_dano_escudo = 0.0

        self.vida = max(0.0, round(self.vida - dano_vida, 2))

        if direccion_empuje is not None:
            self.aplicar_empuje(direccion_empuje, dano_total)
        return dano_total

    def actualizar_proyectiles(self, dt, limites_mundo, rocas=None):
        """Actualiza la posición y ciclo de vida de los proyectiles. Las balas chocan con las rocas."""
        for p in self.proyectiles:
            p.actualizar(dt, limites_mundo)
            # Las balas no atraviesan las rocas: se destruyen al impactar
            # (una flecha ya clavada en el suelo es solo decorado)
            if rocas and p.activo and not getattr(p, "clavada", False):
                for roca in rocas:
                    if p.hitbox.colliderect(roca.rect):
                        p.activo = False
                        break
        # Filtrar proyectiles inactivos (que salieron del mundo o chocaron)
        self.proyectiles = [p for p in self.proyectiles if p.activo]

    def dibujar(self, pantalla, fuente_nombre, desplazamiento=(0, 0)):
        """Dibuja al personaje. `desplazamiento` es el offset de la cámara (mundo -> pantalla)."""
        ox, oy = desplazamiento
        pos_x = round(self.posicion.x - ox)
        pos_y = round(self.posicion.y - oy)

        # Destino visual suave cuando se mueve
        if self.esta_en_movimiento():
            pygame.draw.circle(pantalla, (70, 85, 110), (round(self.destino.x - ox), round(self.destino.y - oy)), 5, 1)

        # Aura(s) activas alrededor del personaje (se dibujan detrás del cuerpo)
        en_efecto = self.habilidades_en_efecto()
        for hab in en_efecto:
            if hab.estado == "ACTIVA" and hasattr(hab, "dibujar_aura"):
                hab.dibujar_aura(pantalla, self, desplazamiento)

        # Círculo base del personaje
        pygame.draw.circle(pantalla, self.color, (pos_x, pos_y), self.radio)

        # Círculos de habilidad cambiados al INTERIOR del círculo (para no alterar la percepción del hitbox)
        destello_activo = any(h.nombre == "Destello" and h.estado == "ACTIVA" for h in en_efecto)
        burst_activo = any(h.nombre == "Burst de Fuerza" and h.estado == "ACTIVA" for h in en_efecto)
        destello_cd = any(h.nombre == "Destello" and h.estado == "COOLDOWN" for h in self.habilidades)

        if destello_activo and burst_activo:
            # Combo interior: anillo magenta y núcleo cian
            pygame.draw.circle(pantalla, (230, 80, 255), (pos_x, pos_y), max(4, self.radio - 4), 2)
            pygame.draw.circle(pantalla, (0, 220, 255), (pos_x, pos_y), max(2, self.radio - 8), 2)
        elif destello_activo:
            # Anillo cian interior
            pygame.draw.circle(pantalla, (0, 220, 255), (pos_x, pos_y), max(4, self.radio - 4), 2)
        elif burst_activo:
            # Anillo naranja rojizo interior
            pygame.draw.circle(pantalla, (255, 90, 60), (pos_x, pos_y), max(4, self.radio - 4), 2)
        elif destello_cd:
            # Anillo ámbar interior de fatiga
            pygame.draw.circle(pantalla, (240, 140, 40), (pos_x, pos_y), max(4, self.radio - 5), 1)

        # Borde exterior blanco exacto (delimitador físico del radio / hitbox)
        pygame.draw.circle(pantalla, (255, 255, 255), (pos_x, pos_y), self.radio, 2)

        # Ojos: dos puntos negros que siempre miran hacia donde se dirige el personaje
        rad = math.radians(self.angulo)
        frente_x = math.sin(rad)
        frente_y = -math.cos(rad)
        derecha_x = math.cos(rad)
        derecha_y = math.sin(rad)

        adelante = self.radio * 0.45      # Qué tan adelantados están los ojos
        separacion = self.radio * 0.32    # Distancia de cada ojo al eje central
        radio_ojo = max(2, round(self.radio * 0.14))

        for lado in (-1, 1):
            ojo_x = pos_x + frente_x * adelante + derecha_x * separacion * lado
            ojo_y = pos_y + frente_y * adelante + derecha_y * separacion * lado
            pygame.draw.circle(pantalla, (10, 10, 14), (round(ojo_x), round(ojo_y)), radio_ojo)

        # Dibujar herramienta rotada sincronizada con el personaje
        if self.herramienta:
            self.herramienta.dibujar(pantalla, self, desplazamiento)

        # Dibujar proyectiles activos
        for p in self.proyectiles:
            p.dibujar(pantalla, desplazamiento)

        # Etiqueta con el nombre flotando sobre el personaje (oculta si está dentro de un arbusto)
        if self.oculto:
            return
        texto_nombre = fuente_nombre.render(self.nombre, True, (255, 255, 255))
        rect_texto = texto_nombre.get_rect(center=(pos_x, pos_y - self.radio - 14))

        fondo_tag = pygame.Surface((rect_texto.width + 10, rect_texto.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(fondo_tag, (18, 22, 28, 210), fondo_tag.get_rect(), border_radius=4)
        pantalla.blit(fondo_tag, (rect_texto.x - 5, rect_texto.y - 2))
        pantalla.blit(texto_nombre, rect_texto)
