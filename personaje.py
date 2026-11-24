import pygame
import math
from herramientas import EspadaLigera, HERRAMIENTAS_DISPONIBLES, crear_herramienta
from talismanes import ColeccionTalismanes, GestorSombras
from habilidades import (combinar_buffs, factor_duplicado, PIXELES_POR_PUNTO_EMPUJE,
                         actualizar_anulacion_escudo_magico, actualizar_ralentizacion, COLOR_VENENO)

# Masa del personaje frente a otros cuerpos (conejo 1, lobo 3): apenas lo desplazan sus
# invocaciones, pero los cuerpos fijos (maniqui) si lo frenan.
MASA_PERSONAJE = 100.0

# Huecos de habilidades: tecla de pygame y texto de cada uno ([2] [3] [4])
TECLAS_HUECOS = ((pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4"))

# Experiencia (Documentacion/sistema_xp.md). XP_POR_NIVEL[n - 1] = XP para pasar del nivel n
# al n + 1. Total 1048 XP: pensado para llegar al nivel 20 en unas 2 horas de caza.
NIVEL_MAXIMO = 20
XP_POR_NIVEL = (1, 2, 4, 8, 12, 16, 20, 25, 30, 40, 50, 60, 70, 80, 95, 110, 125, 140, 160)
PUNTOS_MEJORA_POR_NIVEL = 4
MONEDAS_POR_NIVEL = 20           # monedas que da cada subida de nivel

# Silueta del personaje invisible (Paso 0): transparencias 0-255 de relleno, contorno y ojos
ALFA_INVISIBLE_RELLENO = 25
ALFA_INVISIBLE_CONTORNO = 90
ALFA_INVISIBLE_OJOS = 140
# Paso 0: segundos que tarda el personaje en desvanecerse (y en volver a verse). Solo visual:
# la invisibilidad empieza y termina al instante para los enemigos.
DURACION_DESVANECER = 0.4
MARGEN_CAPA_DESVANECER = 190   # px alrededor del personaje que cubre la capa del fundido (arma y nombre)

# Autoapuntado (clic derecho sobre un enemigo, sin mantener la tecla de una invocación):
# el personaje mira siempre al objetivo. Se cancela si se aleja más de AUTOAPUNTADO_RANGO,
# si el objetivo muere o con otro clic derecho en terreno libre o sobre el mismo objetivo.
AUTOAPUNTADO_RANGO = 500
AUTOAPUNTADO_DEBUFF = 0.40          # -40 % de velocidad mientras está activo
AUTOAPUNTADO_MARGEN_CLIC = 30       # margen para considerar que el clic cae sobre un enemigo

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
# Tras recibir un golpe (mordida, zarpazo, embestida, espada) el personaje no puede recibir
# otro golpe durante este tiempo: una manada no puede encadenar mordidas.
INVULNERABILIDAD_TRAS_GOLPE = 0.5
# Aceleracion de regeneracion de energia (stat mejorable con puntos) y bonos del agua.
REGEN_ENERGIA_POR_PUNTO = 0.05       # +5% de velocidad de regen de energia por punto (~+1 En/min quieto)
REGEN_ENERGIA_TOPE = 1.0             # maximo +100% (20 puntos): regen al doble
REGEN_ENERGIA_AGUA = 2.0             # x2 en agua
REGEN_ENERGIA_AGUA_PROFUNDA = 4.0    # x4 en la zona profunda (peligrosa) del lago

# Reparto del daño mágico: se bloquea un 10% del daño total; del resto, el escudo mágico
# absorbe el 90% y el 10% pasa a la vida. El escudo mágico comparte la progresión y la
# regeneración del escudo físico (inicial 0, +5 hasta 15, luego +2; regen +1/s tras 10s).
ESCUDOM_BLOQUEO = 0.10
ESCUDOM_REPARTO_ESCUDO = 0.90
ESCUDOM_REPARTO_VIDA = 0.10

# El bloqueo porcentual solo existe si el escudo de ese tipo tiene al menos este valor.
# Sin escudo (o anulado por Cortar) el daño llega entero a la vida.
ESCUDO_MINIMO_PARA_BLOQUEO = 1.0


def repartir_dano(cantidad, tipo_dano, escudo_disp):
    """Reparto comun del dano entre escudo y vida (personaje, maniqui...).
    Devuelve (absorbido por el escudo, dano a la vida). Si la parte del escudo supera el
    escudo disponible, el sobrante pasa tambien a la vida. Con menos de
    ESCUDO_MINIMO_PARA_BLOQUEO de escudo no hay bloqueo y todo va a la vida."""
    if escudo_disp < ESCUDO_MINIMO_PARA_BLOQUEO:
        return 0.0, cantidad
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
        # El máximo efectivo (escudo_max) suma el bonus de la herramienta Escudo a esta base.
        self.escudo_max_base = float(escudo)       # Máximo del escudo físico sin bonus (sube con puntos)
        self.escudo = float(escudo)                # Escudo físico disponible
        self.tiempo_sin_dano_escudo = 0.0          # Segundos sin recibir daño en el escudo (para la regen)
        # Escudo mágico: reserva que absorbe daño mágico (habilidades que consumen energía).
        self.escudo_magico_max_base = float(escudo_magico)
        self.escudo_magico = float(escudo_magico)
        self.tiempo_sin_dano_escudo_magico = 0.0
        self.anulacion_escudo_magico = 0.0   # Segundos restantes de escudo magico anulado (Cortar)
        self.escudo_magico_guardado = 0.0    # Valor que recupera al terminar la anulacion
        self.color = color

        # Progresión: nivel del personaje y puntos de mejora (empieza con 3)
        self.nivel = 1
        self.puntos_mejora = 3
        self.xp = 0.0                    # XP acumulada hacia el siguiente nivel
        self.monedas = 0                 # monedas de la caza (por ahora no se gastan; se pierden al morir)
        # Talismanes (anillos y Tótem de vida): solo dan efecto los equipados en los 3 huecos.
        self.talismanes = ColeccionTalismanes()
        self._bonos_talismanes = {}      # bonos aditivos ya sumados a las stats (para poder quitarlos)
        self.bono_velocidad = 0.0        # +% sobre la velocidad base (anillo de viento)
        self.bono_dano = 0.0             # +% al daño del arma (anillo de fuerza)
        self.bono_escudo = 0.0           # escudo físico máximo extra (anillo de defensa física)
        self.bono_escudo_magico = 0.0    # escudo mágico máximo extra (anillo de defensa mágica)
        self.bono_regen_escudo = 0.0     # +% a la regeneración del escudo físico
        self.bono_regen_escudo_magico = 0.0
        self.regen_vida = None           # (vida, intervalo) del anillo de regeneración inversa
        self.sombras_anillo = GestorSombras()   # sombras de conejo / lobo de los anillos
        self.ultimo_agresor = None       # quien te atacó por última vez (lo usan esas sombras)
        self.t_agresor = 0.0
        self._t_regen_vida = 0.0
        self.habilidades = list(habilidades) if habilidades is not None else []
        # Coleccion (fase 2 del Gacha): todas las habilidades conseguidas; solo las de los 3
        # huecos ([2] [3] [4]) estan equipadas (self.habilidades, en orden de hueco).
        self.huecos_habilidades = [None] * len(TECLAS_HUECOS)
        for h in self.habilidades:
            i = next((k for k, (_, t) in enumerate(TECLAS_HUECOS) if t == getattr(h, "tecla_str", None)), None)
            if i is None or self.huecos_habilidades[i] is not None:
                i = self.huecos_habilidades.index(None)
            self.huecos_habilidades[i] = h
            h.asignar_tecla(*TECLAS_HUECOS[i])
        self.coleccion_habilidades = list(self.habilidades)
        # Efectos temporales de habilidades no equipadas (ej. los que otorga Golpe de Suerte)
        self.efectos_extra = []
        self.herramienta = herramienta if herramienta is not None else EspadaLigera()
        self.coleccion_herramientas = [self.herramienta]   # herramientas conseguidas (1 equipada)
        # Empieza con los escudos llenos incluyendo el bonus de la herramienta Escudo
        self.escudo = self.escudo_max
        self.escudo_magico = self.escudo_magico_max

        # Proyectiles activos disparados por el personaje (Disparo Veloz)
        self.proyectiles = []

        # Temporizador para la regeneración global de energía
        self.tiempo_regen = 0.0
        self.bono_regen_energia = 0.0              # +% a la velocidad de regen de energía (stat mejorable)

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
        self.veneno = None           # Veneno activo (ej. el que da Golpe de Suerte), None si no tiene
        self.ralentizacion = 0.0     # Debuff de velocidad recibido (ej. Onda Sonora), 0.20 = -20%
        self.tiempo_ralentizacion = 0.0
        self.masa = MASA_PERSONAJE   # Al separar cuerpos solapados, las invocaciones le ceden el paso

        # Empuje acumulado pendiente de aplicar (retroceso por recibir daño)
        self.empuje = pygame.Vector2(0, 0)
        # Segundos restantes de invulnerabilidad a golpes (tras recibir uno)
        self.t_invulnerable = 0.0

        # Autoapuntado: enemigo fijado (None si no está activo)
        self.objetivo_apuntado = None
        self.mensaje_apuntado = ""
        self.visibilidad = 1.0           # 1 = se ve normal, 0 = silueta de Paso 0 (fundido visual)         # aviso breve (ej. no se puede activar cargando)
        self.tiempo_mensaje_apuntado = 0.0

        # Radio visual base escalado por el tamaño
        self.radio = int(20 * self.tamano)

        # Hitbox del personaje (coincide exactamente con el contorno físico exterior)
        self.hitbox = pygame.Rect(
            round(x - self.radio),
            round(y - self.radio),
            self.radio * 2,
            self.radio * 2
        )

    @property
    def bonus_escudos(self):
        """Bonus a los máximos de escudo de la herramienta Escudo (0 si no la lleva o está rota)."""
        h = getattr(self, "herramienta", None)
        if h is not None and h.es_escudo and not h.roto:
            return h.bonus_escudos
        return 0.0

    @property
    def escudo_max(self):
        """Máximo efectivo del escudo físico: la base de los puntos más el bonus del Escudo, más
        lo que da el anillo de defensa física (se suma aunque la base sea 0)."""
        return round(self.escudo_max_base * (1.0 + self.bonus_escudos) + getattr(self, "bono_escudo", 0.0), 2)

    @property
    def escudo_magico_max(self):
        """Máximo efectivo del escudo mágico: la base de los puntos más el bonus del Escudo, más
        lo que da el anillo de defensa mágica."""
        return round(self.escudo_magico_max_base * (1.0 + self.bonus_escudos) + getattr(self, "bono_escudo_magico", 0.0), 2)

    def recalcular_talismanes(self):
        """Aplica los efectos de los talismanes equipados. Los aditivos (vida, energía y
        cadencia máximas) se suman a la stat y se recuerdan para poder quitarlos; al quitar un
        anillo la vida/energía actuales se recortan al nuevo máximo (equiparlo no cura)."""
        b = self.talismanes.bonos()
        for clave, attr in (("vida_max", "vida_max"), ("energia_max", "energia_max"), ("cadencia", "cadencia")):
            delta = b.get(clave, 0) - self._bonos_talismanes.get(clave, 0)
            if delta:
                setattr(self, attr, round(getattr(self, attr) + delta, 2))
        self.vida = min(self.vida, self.vida_max)
        self.energia = min(self.energia, self.energia_max)
        self.bono_velocidad = b.get("velocidad_pct", 0.0)
        self.bono_dano = b.get("dano_pct", 0.0)
        self.bono_escudo = b.get("escudo", 0.0)
        self.bono_escudo_magico = b.get("escudo_magico", 0.0)
        self.bono_regen_escudo = b.get("regen_escudo", 0.0)
        self.bono_regen_escudo_magico = b.get("regen_escudo_magico", 0.0)
        self.regen_vida = b.get("regen_vida")
        niveles_sombra = {}
        if b.get("sombra_conejo"):
            niveles_sombra["conejo"] = int(b["sombra_conejo"])
        if b.get("sombra_lobo"):
            niveles_sombra["lobo"] = int(b["sombra_lobo"])
        self.sombras_anillo.configurar(niveles_sombra, self)
        self.escudo = min(self.escudo, self.escudo_max)
        self.escudo_magico = min(self.escudo_magico, self.escudo_magico_max)
        self._bonos_talismanes = b

    def actualizar_talismanes(self, dt):
        """Anillo de regeneración inversa: cura su cantidad cada intervalo, en todo momento."""
        if not self.regen_vida:
            self._t_regen_vida = 0.0
            return
        cantidad, intervalo = self.regen_vida
        self._t_regen_vida += dt
        while self._t_regen_vida >= intervalo:
            self._t_regen_vida -= intervalo
            if self.vida < self.vida_max:
                self.curar(cantidad)

    def bloquear_con_escudo(self, cantidad, origen):
        """
        Si la herramienta Escudo está desenfundada y su arco frontal cubre el punto de origen
        del ataque, lo bloquea entero: no hay daño ni efectos, el escudo se desgasta y empuja
        al portador. Devuelve True si bloqueó. Solo lo consultan los ataques bloqueables
        (golpes de arma, proyectiles, mordidas); el terreno, el autodaño, los efectos ya
        aplicados, la Onda Sonora y el Aura Eléctrica no pasan por aquí.
        """
        escudo = self.herramienta
        if not (escudo and escudo.es_escudo and escudo.cubre(self, origen)):
            return False
        escudo.bloquear(self, cantidad, self.posicion - pygame.Vector2(origen))
        return True

    def esta_cargando(self):
        """True si mantiene una carga: Carga de Fuego o el Arco tensando. La curación que se
        mantiene pulsada (Regeneración Inversa) no cuenta."""
        if getattr(self.herramienta, "cargando", False):
            return True
        return any(getattr(h, "cargando", False) for h in self.habilidades)

    def alternar_autoapuntado(self, enemigo):
        """Clic derecho para autoapuntar. Sobre el objetivo actual o sin enemigo (terreno libre)
        lo desactiva; sobre otro enemigo lo fija si está a AUTOAPUNTADO_RANGO o menos y no se
        está cargando nada (se puede cargar después de activarlo). Devuelve True si queda activo."""
        if enemigo is None or enemigo is self.objetivo_apuntado:
            self.objetivo_apuntado = None
            return False
        if self.esta_cargando():
            self._avisar_apuntado("No puedes autoapuntar mientras cargas")
        elif (enemigo.posicion - self.posicion).length() > AUTOAPUNTADO_RANGO:
            self._avisar_apuntado("Objetivo fuera de rango")
        else:
            self.objetivo_apuntado = enemigo
            self._mirar_a(enemigo.posicion)
        return self.objetivo_apuntado is not None

    def _avisar_apuntado(self, texto):
        self.mensaje_apuntado = texto
        self.tiempo_mensaje_apuntado = 2.0

    def _mirar_a(self, punto):
        hacia = pygame.Vector2(punto) - self.posicion
        if hacia.length_squared() > 0:
            self.angulo = math.degrees(math.atan2(hacia.x, -hacia.y)) % 360.0

    def actualizar_autoapuntado(self, dt):
        """Mantiene la mirada en el objetivo y lo suelta si muere o pasa de AUTOAPUNTADO_RANGO."""
        if self.tiempo_mensaje_apuntado > 0:
            self.tiempo_mensaje_apuntado -= dt
            if self.tiempo_mensaje_apuntado <= 0:
                self.mensaje_apuntado = ""
        obj = self.objetivo_apuntado
        if obj is None:
            return
        if (not getattr(obj, "vivo", True) or not getattr(obj, "apuntable", True)
                or (obj.posicion - self.posicion).length() > AUTOAPUNTADO_RANGO):
            self.objetivo_apuntado = None
            return
        self._mirar_a(obj.posicion)

    # ---------------------------------------------------------------- Coleccion (fase 2)
    def _sincronizar_habilidades(self):
        """self.habilidades = las equipadas en orden de hueco, cada una con la tecla de su hueco."""
        for i, h in enumerate(self.huecos_habilidades):
            if h is not None:
                h.asignar_tecla(*TECLAS_HUECOS[i])
        self.habilidades[:] = [h for h in self.huecos_habilidades if h is not None]

    def tiene_herramienta(self, nombre):
        return any(h.nombre == nombre for h in self.coleccion_herramientas)

    def tiene_habilidad(self, nombre):
        return any(h.nombre == nombre for h in self.coleccion_habilidades)

    def herramientas_faltantes(self):
        return [n for n in HERRAMIENTAS_DISPONIBLES if not self.tiene_herramienta(n)]

    def habilidades_faltantes(self):
        from habilidades import HABILIDADES_DISPONIBLES
        return [n for n in HABILIDADES_DISPONIBLES if not self.tiene_habilidad(n)]

    def agregar_herramienta(self, nombre):
        """Añade una herramienta nueva a nivel 1 (sin equiparla). None si ya la tenías."""
        if self.tiene_herramienta(nombre):
            return None
        h = crear_herramienta(nombre)
        self.coleccion_herramientas.append(h)
        return h

    def agregar_habilidad(self, nombre):
        """Añade una habilidad nueva a nivel 1. Si hay un hueco libre se equipa ahí; si no,
        queda guardada en la coleccion. None si ya la tenías."""
        from habilidades import crear_habilidad
        if self.tiene_habilidad(nombre):
            return None
        h = crear_habilidad(nombre)
        if h is None:
            return None
        self.coleccion_habilidades.append(h)
        if None in self.huecos_habilidades:
            self.huecos_habilidades[self.huecos_habilidades.index(None)] = h
            self._sincronizar_habilidades()
        return h

    def equipar_herramienta(self, herramienta):
        """Cambia la herramienta equipada por otra de la coleccion. La anterior conserva su
        nivel y durabilidad; la nueva empieza guardada (se saca con [1])."""
        if herramienta is self.herramienta or herramienta not in self.coleccion_herramientas:
            return False
        vieja = self.herramienta
        vieja.activa = False
        vieja.hitbox = None
        if getattr(vieja, "cargando", False):
            vieja.cargando = False
            vieja.tiempo_carga = 0.0
        herramienta.activa = False
        self.herramienta = herramienta
        self.escudo = min(self.escudo, self.escudo_max)                 # la pasiva del Escudo cambia
        self.escudo_magico = min(self.escudo_magico, self.escudo_magico_max)
        return True

    def _retirar_habilidad(self, h):
        """Al quitar una habilidad del hueco: terminan sus efectos (invocaciones, telarañas,
        cuchillas, ondas, cargas, curación mantenida y lo que estuviera activo) y pasa a su
        recarga. Conserva nivel y recarga (no se puede 'resetear' cambiándola)."""
        for lista in ("lobos", "conejos", "aranas"):
            if hasattr(h, lista):
                for c in getattr(h, lista):
                    c.vivo = False
                setattr(h, lista, [])
        for lista in ("telaranas", "cuchillas", "emisiones"):
            if hasattr(h, lista):
                setattr(h, lista, [])
        if getattr(h, "cargando", False):
            h.cargando = False
            if hasattr(h, "tiempo_carga"):
                h.tiempo_carga = 0.0
        if getattr(h, "canalizando", False):
            h.canalizando = False
        if hasattr(h, "modo_combate"):
            h.modo_combate = False
        if h.estado == "ACTIVA":
            h.tiempo_restante_activo = 0.0
        h.actualizar(0.0, self)          # procesa el paso a recarga y el fin del efecto

    def equipar_habilidad(self, habilidad, hueco):
        """Pone una habilidad de la coleccion en el hueco 0-2 ([2] [3] [4]). Si ya estaba en
        otro hueco, intercambian sitio; si el hueco tenia otra, esa se guarda (y terminan sus
        efectos)."""
        if habilidad not in self.coleccion_habilidades or not 0 <= hueco < len(self.huecos_habilidades):
            return False
        actual = self.huecos_habilidades[hueco]
        if actual is habilidad:
            return False
        if habilidad in self.huecos_habilidades:
            otro = self.huecos_habilidades.index(habilidad)
            self.huecos_habilidades[otro], self.huecos_habilidades[hueco] = actual, habilidad
        else:
            if actual is not None:
                self._retirar_habilidad(actual)
            self.huecos_habilidades[hueco] = habilidad
        self._sincronizar_habilidades()
        return True

    def habilidades_guardadas(self):
        """Habilidades de la coleccion que no estan en ningun hueco (su recarga sigue corriendo)."""
        return [h for h in self.coleccion_habilidades if h not in self.huecos_habilidades]

    def fuentes_criaturas(self):
        """Todo lo que tiene 'criaturas' (sombras): las habilidades equipadas y los anillos de sombra."""
        return list(self.habilidades) + [self.sombras_anillo]

    def habilidades_en_efecto(self):
        """Habilidades equipadas más los efectos temporales activos (ej. de Golpe de Suerte)."""
        return self.habilidades + self.efectos_extra

    @property
    def invisible(self):
        """True mientras haya una habilidad de invisibilidad activa (Paso 0, equipada u otorgada)."""
        return any(getattr(h, "da_invisibilidad", False) and h.estado == "ACTIVA"
                   for h in self.habilidades_en_efecto())

    def actualizar_desvanecimiento(self, dt):
        """Lleva 'visibilidad' hacia 0 (invisible) o 1 (visible) en DURACION_DESVANECER."""
        objetivo = 0.0 if self.invisible else 1.0
        paso = dt / DURACION_DESVANECER
        if self.visibilidad < objetivo:
            self.visibilidad = min(objetivo, self.visibilidad + paso)
        else:
            self.visibilidad = max(objetivo, self.visibilidad - paso)

    @property
    def detectable(self):
        """Los enemigos no detectan al personaje oculto en un arbusto ni invisible (no lo miran
        ni inician ataques contra él), aunque lo que lo toque sí le hace daño."""
        return not (self.oculto or self.invisible)

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

    def actualizar_veneno(self, dt):
        """Tiquea el veneno activo (daño mágico por segundo, lo amortigua el escudo mágico)
        y lo retira cuando termina."""
        if self.veneno is None:
            return
        self.veneno.actualizar(dt, self)
        if not self.veneno.activo:
            self.veneno = None

    def actualizar_ralentizacion(self, dt):
        """Descuenta la ralentizacion recibida (ej. Onda Sonora) y la retira al terminar."""
        actualizar_ralentizacion(self, dt)

    def esta_en_movimiento(self):
        """Devuelve True si el personaje se está desplazando hacia su destino."""
        return (self.destino - self.posicion).length() > 2.0

    @property
    def regen_energia_al_tope(self):
        """True si la regeneracion de energia ya llego a su maximo (REGEN_ENERGIA_TOPE)."""
        return self.bono_regen_energia >= REGEN_ENERGIA_TOPE - 1e-9

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
            incremento = ESCUDO_INCREMENTO_GRANDE if self.escudo_max_base < ESCUDO_TOPE_TRAMO else ESCUDO_INCREMENTO_NORMAL
            self.escudo_max_base += incremento
            self.escudo = self.escudo_max          # Al mejorarlo, se rellena al nuevo máximo
        elif nombre == "escudo_magico":
            incremento = ESCUDO_INCREMENTO_GRANDE if self.escudo_magico_max_base < ESCUDO_TOPE_TRAMO else ESCUDO_INCREMENTO_NORMAL
            self.escudo_magico_max_base += incremento
            if self.anulacion_escudo_magico > 0:
                self.escudo_magico_guardado = self.escudo_magico_max   # se rellena al terminar la anulacion
            else:
                self.escudo_magico = self.escudo_magico_max
        elif nombre == "regen_energia":
            if self.regen_energia_al_tope:
                return False                       # ya esta en el maximo: no gasta el punto
            self.bono_regen_energia = round(min(REGEN_ENERGIA_TOPE, self.bono_regen_energia + REGEN_ENERGIA_POR_PUNTO), 4)
        else:
            return False
        self.puntos_mejora -= 1
        return True

    def subir_nivel(self):
        """Sube un nivel (hasta NIVEL_MAXIMO): +PUNTOS_MEJORA_POR_NIVEL puntos de mejora y +20 monedas. Tambien la usa [L]."""
        if self.nivel >= NIVEL_MAXIMO:
            return self.nivel
        self.nivel += 1
        self.puntos_mejora += PUNTOS_MEJORA_POR_NIVEL
        self.monedas += MONEDAS_POR_NIVEL
        if self.nivel >= NIVEL_MAXIMO:
            self.xp = 0.0
        return self.nivel

    @property
    def xp_siguiente(self):
        """XP necesaria para el siguiente nivel (None en el nivel maximo)."""
        if self.nivel >= NIVEL_MAXIMO:
            return None
        return XP_POR_NIVEL[self.nivel - 1]

    def ganar_xp(self, cantidad):
        """Suma XP; cada vez que llega a la necesaria sube de nivel y el sobrante pasa al
        siguiente. En el nivel maximo ya no acumula. Devuelve cuantos niveles subio."""
        if cantidad <= 0 or self.nivel >= NIVEL_MAXIMO:
            return 0
        self.xp = round(self.xp + cantidad, 2)   # redondeo: 10 x 0.1 llega justo a 1
        subidos = 0
        while self.xp_siguiente is not None and self.xp >= self.xp_siguiente:
            self.xp = round(self.xp - self.xp_siguiente, 2)
            self.subir_nivel()
            subidos += 1
        return subidos

    def actualizar_regeneracion(self, dt):
        """
        Regeneración global de energía:
        - Parado: +1 de energía cada 3.0 segundos.
        - En movimiento: +1 de energía cada 6.0 segundos.
        """
        if self.energia < self.energia_max:
            intervalo = 6.0 if self.esta_en_movimiento() else 3.0
            # Velocidad de regen: aceleracion mejorable + agua (x2) / zona profunda (x4).
            mult = 1.0 + self.bono_regen_energia
            if self.en_agua_profunda:
                mult *= REGEN_ENERGIA_AGUA_PROFUNDA
            elif self.en_agua:
                mult *= REGEN_ENERGIA_AGUA
            intervalo_efectivo = intervalo / mult
            self.tiempo_regen += dt
            while self.tiempo_regen >= intervalo_efectivo and self.energia < self.energia_max:
                self.energia = min(self.energia_max, self.energia + 1)
                self.tiempo_regen -= intervalo_efectivo
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
            self.escudo = min(self.escudo_max, round(self.escudo + REGEN_ESCUDO_POR_SEGUNDO * (1.0 + self.bono_regen_escudo) * dt, 2))

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
            self.escudo_magico = min(self.escudo_magico_max, round(self.escudo_magico + REGEN_ESCUDO_POR_SEGUNDO * (1.0 + self.bono_regen_escudo_magico) * dt, 2))

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

        # Anillo de viento: +% sobre la velocidad base
        modificador += self.bono_velocidad

        # Autoapuntado activo
        if self.objetivo_apuntado is not None:
            modificador -= AUTOAPUNTADO_DEBUFF

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
        # Con autoapuntado la orientación la fija el objetivo (ver actualizar_autoapuntado)
        if distancia > 0.1 and self.objetivo_apuntado is None:
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

    @property
    def invulnerable(self):
        """True durante INVULNERABILIDAD_TRAS_GOLPE s despues de recibir un golpe. Solo protege
        de golpes (fauna, espada del maniqui); efectos, ondas y terreno siguen haciendo dano."""
        return self.t_invulnerable > 0

    def marcar_golpe(self):
        """Lo llaman los ataques que golpean al personaje: empieza la invulnerabilidad breve."""
        self.t_invulnerable = INVULNERABILIDAD_TRAS_GOLPE

    def actualizar_invulnerabilidad(self, dt):
        if self.t_invulnerable > 0:
            self.t_invulnerable = max(0.0, self.t_invulnerable - dt)

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
            previa = pygame.Vector2(p.posicion)
            p.actualizar(dt, limites_mundo)
            # Las balas no atraviesan las rocas: se destruyen al impactar
            # (una flecha ya clavada en el suelo es solo decorado). Se revisa también el
            # trayecto del frame para que los proyectiles rápidos no salten rocas pequeñas.
            if rocas and p.activo and not getattr(p, "clavada", False):
                for roca in rocas:
                    if p.hitbox.colliderect(roca.rect) or roca.rect.clipline(previa, p.posicion):
                        p.activo = False
                        break
        # Filtrar proyectiles inactivos (que salieron del mundo o chocaron)
        self.proyectiles = [p for p in self.proyectiles if p.activo]

    def dibujar(self, pantalla, fuente_nombre, desplazamiento=(0, 0)):
        """Dibuja al personaje. `desplazamiento` es el offset de la cámara (mundo -> pantalla)."""
        ox, oy = desplazamiento
        pos_x = round(self.posicion.x - ox)
        pos_y = round(self.posicion.y - oy)

        # Invisible (Paso 0): solo un contorno tenue con los ojos para saber dónde está.
        # Se ocultan nombre, arma (salvo durante el golpe), auras y destino; los ataques sí se ven.
        if self.invisible and self.visibilidad <= 0:
            self._dibujar_invisible(pantalla, pos_x, pos_y)
            if self.herramienta and getattr(self.herramienta, "golpeando", False):
                self.herramienta.dibujar(pantalla, self, desplazamiento)
            for p in self.proyectiles:
                p.dibujar(pantalla, desplazamiento)
            return

        # Fundido de Paso 0 (al activarse o al terminar): la silueta debajo y el personaje
        # normal encima, cada vez más (o menos) transparente.
        if self.visibilidad < 1:
            self._dibujar_invisible(pantalla, pos_x, pos_y)
            m = MARGEN_CAPA_DESVANECER
            capa = pygame.Surface((m * 2, m * 2), pygame.SRCALPHA)
            self._dibujar_visible(capa, fuente_nombre, (ox + pos_x - m, oy + pos_y - m), m, m, False)
            capa.set_alpha(round(255 * self.visibilidad))
            pantalla.blit(capa, (pos_x - m, pos_y - m))
            for p in self.proyectiles:
                p.dibujar(pantalla, desplazamiento)
            return

        self._dibujar_visible(pantalla, fuente_nombre, desplazamiento, pos_x, pos_y, True)

    def _dibujar_visible(self, pantalla, fuente_nombre, desplazamiento, pos_x, pos_y, con_proyectiles):
        """Personaje normal: destino, auras, cuerpo, ojos, arma, proyectiles y nombre."""
        ox, oy = desplazamiento

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

        # Envenenado: anillo verde exterior (como en los enemigos)
        if self.veneno is not None:
            pygame.draw.circle(pantalla, COLOR_VENENO, (pos_x, pos_y), self.radio + 4, 2)

        # Ojos: dos puntos negros que siempre miran hacia donde se dirige el personaje
        self._dibujar_ojos(pantalla, pos_x, pos_y, (10, 10, 14))

        # Dibujar herramienta rotada sincronizada con el personaje
        if self.herramienta:
            self.herramienta.dibujar(pantalla, self, desplazamiento)

        # Dibujar proyectiles activos
        if con_proyectiles:
            for p in self.proyectiles:
                p.dibujar(pantalla, desplazamiento)

        # Etiqueta con el nombre flotando sobre el personaje (oculta si está dentro de un arbusto;
        # invisible ya salió antes)
        if self.oculto:
            return
        texto_nombre = fuente_nombre.render(self.nombre, True, (255, 255, 255))
        rect_texto = texto_nombre.get_rect(center=(pos_x, pos_y - self.radio - 14))

        fondo_tag = pygame.Surface((rect_texto.width + 10, rect_texto.height + 4), pygame.SRCALPHA)
        pygame.draw.rect(fondo_tag, (18, 22, 28, 210), fondo_tag.get_rect(), border_radius=4)
        pantalla.blit(fondo_tag, (rect_texto.x - 5, rect_texto.y - 2))
        pantalla.blit(texto_nombre, rect_texto)

    def _dibujar_ojos(self, pantalla, pos_x, pos_y, color):
        """Dos puntos que siempre miran hacia donde se dirige el personaje."""
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
            pygame.draw.circle(pantalla, color, (round(ojo_x), round(ojo_y)), radio_ojo)

    def _dibujar_invisible(self, pantalla, pos_x, pos_y):
        """Silueta casi transparente: relleno muy tenue, contorno suave y ojos."""
        r = self.radio
        capa = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        centro = (r + 2, r + 2)
        pygame.draw.circle(capa, (*self.color, ALFA_INVISIBLE_RELLENO), centro, r)
        pygame.draw.circle(capa, (255, 255, 255, ALFA_INVISIBLE_CONTORNO), centro, r, 1)
        self._dibujar_ojos(capa, centro[0], centro[1], (10, 10, 14, ALFA_INVISIBLE_OJOS))
        pantalla.blit(capa, (pos_x - r - 2, pos_y - r - 2))
