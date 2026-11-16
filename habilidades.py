import pygame
import math

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
# CLASE BASE DE HABILIDADES
# -----------------------------
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
        jugador.fuerza = round(jugador.fuerza_base * (1.0 + self.porcentaje_buff), 2)

    def aplicar_efecto_cooldown(self, jugador):
        jugador.fuerza = jugador.fuerza_base

    def restaurar_efecto(self, jugador):
        jugador.fuerza = jugador.fuerza_base


# -----------------------------
# HABILIDAD 3: DISPARO VELOZ (NUEVA)
# -----------------------------
class DisparoVeloz(HabilidadBase):
    def __init__(self):
        super().__init__(
            nombre="Disparo Veloz",
            descripcion="Ataque a distancia: dispara una esfera de energía recta (vel 10) con 20% del daño total del personaje. Cuesta 15% de energía total. Cooldown de 2s.",
            costo_energia=15,  # Valor base referencial; se calcula con 15% de energía total
            duracion_activa=0.0,
            duracion_cooldown=2.0,
            tecla=pygame.K_4,
            tecla_str="4"
        )
        self.velocidad_proyectil = 10.0
        self.porcentaje_dano = 0.20  # 20% del daño total del personaje
        self.escalable = False       # Disparo Veloz no escala con nivel (por ahora)

    def obtener_costo_base(self, jugador):
        """Cuesta exactamente el 15% de la energía total del personaje (redondeada)."""
        return max(1, int(round(jugador.energia_max * 0.15)))

    def ejecutar_activacion(self, jugador):
        """Dispara una esfera recta en la dirección a la que apunta el personaje."""
        rad = math.radians(jugador.angulo)
        frente_x = math.sin(rad)
        frente_y = -math.cos(rad)

        # Origen justo en el borde frontal del personaje
        origen_x = jugador.posicion.x + (frente_x * (jugador.radio + 8))
        origen_y = jugador.posicion.y + (frente_y * (jugador.radio + 8))

        # Daño: 20% del daño total actual del personaje
        dano_total = jugador.calcular_dano_total() if hasattr(jugador, "calcular_dano_total") else (jugador.fuerza * 2.0)
        dano_proyectil = max(0.5, round(dano_total * self.porcentaje_dano, 2))

        proyectil = ProyectilEnergia(
            x=origen_x,
            y=origen_y,
            dx=frente_x,
            dy=frente_y,
            velocidad=self.velocidad_proyectil,
            dano=dano_proyectil,
            radio=6
        )

        if hasattr(jugador, "proyectiles"):
            jugador.proyectiles.append(proyectil)

        # Pasa inmediatamente a cooldown de 2 segundos
        self.estado = "COOLDOWN"
        self.tiempo_restante_activo = 0.0
        self.tiempo_restante_cooldown = self.duracion_cooldown


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
def dibujar_panel_habilidades(pantalla, x, y, ancho, alto, habilidades, jugador, fuentes, info_abierta=None):
    """
    Renderiza la interfaz lateral derecha para las habilidades equipadas (teclas 2, 3, 4)
    y sus temporizadores. El manual se consulta con el icono '?' de la cabecera.
    """
    fuente_titulo = fuentes["titulo"]
    fuente_sub = fuentes["sub"]
    fuente_contador = fuentes["contador"]
    fuente_mini = fuentes["mini"]

    panel = pygame.Surface((ancho, alto))
    panel.fill((20, 23, 30))
    pantalla.blit(panel, (x, y))

    pygame.draw.line(pantalla, (45, 52, 68), (x, y), (x, y + alto), 2)

    # Cabecera
    titulo = fuente_titulo.render("HABILIDADES", True, (255, 215, 0))
    pantalla.blit(titulo, (x + 15, y + 12))

    sub = fuente_sub.render(f"Equipadas ({len(habilidades)}/3)", True, (130, 140, 160))
    pantalla.blit(sub, (x + 15, y + 33))

    cur_y = y + 60
    botones = {}  # Botones (clave -> Rect): "__hab__<idx>" y "__info_hab__"

    # Icono de ayuda (?) en la cabecera -> abre el manual como tooltip
    botones["__info_hab__"] = dibujar_badge_ayuda(pantalla, x + ancho - 24, y + 20, fuente_sub, info_abierta == "hab")

    pygame.draw.line(pantalla, (45, 52, 68), (x + 15, y + 54), (x + ancho - 15, y + 54), 1)

    # Altura ajustada dinámicamente si hay 3 habilidades
    tarjeta_h = 105 if len(habilidades) >= 3 else 125

    for idx, hab in enumerate(habilidades):
        tarjeta_w = ancho - 26
        tarjeta_x = x + 13

        if hab.estado == "ACTIVA":
            color_borde = (0, 220, 255) if hab.nombre == "Destello" else (255, 100, 70)
            color_fondo = (22, 38, 50) if hab.nombre == "Destello" else (48, 26, 26)
        elif hab.estado == "COOLDOWN":
            color_borde = (230, 140, 40)
            color_fondo = (40, 30, 24)
        else:
            color_borde = (55, 68, 90)
            color_fondo = (26, 30, 40)

        pygame.draw.rect(pantalla, color_fondo, (tarjeta_x, cur_y, tarjeta_w, tarjeta_h), border_radius=6)
        pygame.draw.rect(pantalla, color_borde, (tarjeta_x, cur_y, tarjeta_w, tarjeta_h), width=2, border_radius=6)

        # Nombre y Tecla asignada dinámicamente
        txt_nom = fuente_sub.render(hab.nombre, True, (255, 255, 255))
        pantalla.blit(txt_nom, (tarjeta_x + 10, cur_y + 6))

        txt_tecla = fuente_mini.render(f"[{hab.tecla_str}]", True, (255, 220, 80))
        tecla_x = tarjeta_x + tarjeta_w - txt_tecla.get_width() - 10
        pantalla.blit(txt_tecla, (tecla_x, cur_y + 7))

        # Botón [+] para subir nivel (gasta un punto de mejora compartido)
        if hab.escalable and hab.nivel < hab.nivel_max and jugador.puntos_mejora > 0:
            bsize = 16
            rect_btn = pygame.Rect(tecla_x - bsize - 8, cur_y + 6, bsize, bsize)
            pygame.draw.rect(pantalla, (34, 78, 44), rect_btn, border_radius=4)
            pygame.draw.rect(pantalla, (100, 230, 130), rect_btn, width=1, border_radius=4)
            signo = fuente_sub.render("+", True, (150, 255, 180))
            pantalla.blit(signo, signo.get_rect(center=rect_btn.center))
            botones[f"__hab__{idx}"] = rect_btn

        # Nivel y Costo
        if hab.escalable:
            color_nv = (255, 215, 120) if hab.nivel >= hab.nivel_max else (160, 200, 255)
            txt_nivel = fuente_mini.render(f"Nv {hab.nivel}/{hab.nivel_max}", True, color_nv)
        else:
            txt_nivel = fuente_mini.render("Nv —", True, (120, 130, 150))
        pantalla.blit(txt_nivel, (tarjeta_x + 10, cur_y + 26))

        costo_mostrado = hab.obtener_costo_base(jugador)
        txt_costo = fuente_mini.render(f"Costo: {costo_mostrado} En.", True, (180, 140, 255))
        pantalla.blit(txt_costo, (tarjeta_x + 92, cur_y + 26))

        # Estado y Cuenta Regresiva
        if hab.estado == "LISTA":
            txt_est = fuente_mini.render("LISTA (Disponible)", True, (100, 255, 140))
            pantalla.blit(txt_est, (tarjeta_x + 10, cur_y + 46))

            bw = tarjeta_w - 20
            pygame.draw.rect(pantalla, (40, 50, 45), (tarjeta_x + 10, cur_y + 64, bw, 6), border_radius=3)
            pygame.draw.rect(pantalla, (100, 255, 140), (tarjeta_x + 10, cur_y + 64, bw, 6), border_radius=3)

        elif hab.estado == "ACTIVA":
            txt_est = fuente_mini.render("⚡ ACTIVA", True, (0, 220, 255) if hab.nombre == "Destello" else (255, 120, 80))
            pantalla.blit(txt_est, (tarjeta_x + 10, cur_y + 44))

            seg = max(0.0, hab.tiempo_restante_activo)
            txt_tiempo = fuente_contador.render(f"{seg:.1f}s", True, (255, 255, 255))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - 10, cur_y + 38))

            prog = seg / max(0.1, hab.duracion_activa)
            bw = tarjeta_w - 20
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (35, 45, 55), (tarjeta_x + 10, cur_y + 64, bw, 6), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (0, 210, 255) if hab.nombre == "Destello" else (255, 90, 60), (tarjeta_x + 10, cur_y + 64, ancho_l, 6), border_radius=3)

        elif hab.estado == "COOLDOWN":
            txt_est = fuente_mini.render("⏳ ENFRIAMIENTO", True, (255, 150, 60))
            pantalla.blit(txt_est, (tarjeta_x + 10, cur_y + 44))

            seg = max(0.0, hab.tiempo_restante_cooldown)
            txt_tiempo = fuente_contador.render(f"{seg:.1f}s", True, (255, 200, 140))
            pantalla.blit(txt_tiempo, (tarjeta_x + tarjeta_w - txt_tiempo.get_width() - 10, cur_y + 38))

            prog = seg / max(0.1, hab.duracion_cooldown)
            bw = tarjeta_w - 20
            ancho_l = int(bw * max(0.0, min(1.0, prog)))
            pygame.draw.rect(pantalla, (45, 35, 30), (tarjeta_x + 10, cur_y + 64, bw, 6), border_radius=3)
            if ancho_l > 0:
                pygame.draw.rect(pantalla, (255, 140, 50), (tarjeta_x + 10, cur_y + 64, ancho_l, 6), border_radius=3)

        # Resumen del efecto (valores reales según el nivel)
        if hab.nombre == "Destello":
            detalles = f"{hab.duracion_activa:.0f}s (+{hab.porcentaje_buff * 100:.0f}% Vel) | CD {hab.duracion_cooldown:.0f}s"
        elif hab.nombre == "Burst de Fuerza":
            detalles = f"{hab.duracion_activa:.0f}s (+{hab.porcentaje_buff * 100:.0f}% Fza) | CD {hab.duracion_cooldown:.0f}s"
        else:
            detalles = "Disparo recto vel 10 | CD 2s"

        txt_det = fuente_mini.render(detalles, True, (160, 170, 190))
        pantalla.blit(txt_det, (tarjeta_x + 10, cur_y + 75))

        if hab.mensaje_alerta:
            txt_ale = fuente_mini.render(hab.mensaje_alerta, True, (255, 80, 80))
            pantalla.blit(txt_ale, (tarjeta_x + 10, cur_y + 88))

        cur_y += tarjeta_h + 8

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
# CATÁLOGO DE HABILIDADES DISPONIBLES
# -----------------------------
HABILIDADES_DISPONIBLES = {
    "Destello": Destello,
    "Burst de Fuerza": BurstDeFuerza,
    "Disparo Veloz": DisparoVeloz
}

def crear_habilidad(nombre):
    cls = HABILIDADES_DISPONIBLES.get(nombre)
    if cls:
        return cls()
    return None
