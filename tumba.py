"""
Tumba: al morir sin Tótem queda una tumba donde caíste que guarda todo tu progreso durante
DURACION_TUMBA segundos. Si vuelves y la rompes (GOLPES_TUMBA golpes directos tuyos: arma,
flechas, proyectiles, cuchillas, ondas o explosiones; cada golpe cuenta 1, sin importar el daño)
recuperas el personaje guardado y se descarta lo de la vida nueva. Si mueres antes, la tumba
vieja desaparece y la nueva guarda la vida que llevabas.
"""
import math
import pygame

DURACION_TUMBA = 600.0          # s (10 min de juego, también con la pantalla de muerte abierta)
GOLPES_TUMBA = 3                # golpes directos para romperla
RADIO_TUMBA = 14                # px (cuerpo sólido)
AVISO_ULTIMO_MINUTO = 60.0      # s finales en los que parpadea
DURACION_DESTELLO_GOLPE = 0.15  # s del destello blanco al recibir un golpe
COLOR_TUMBA = (150, 150, 160)
COLOR_TUMBA_BORDE = (70, 70, 80)
COLOR_INDICADOR = (220, 220, 235)

# Atributos del personaje que son del momento (posición, proyectiles en vuelo...) y no se
# restauran desde la tumba: se conservan los actuales.
CAMPOS_TRANSITORIOS = (
    "posicion", "destino", "angulo", "proyectiles", "combustible", "empuje", "hitbox",
    "objetivo_apuntado", "mensaje_apuntado", "tiempo_mensaje_apuntado", "efectos_extra",
    "arbusto_actual", "oculto", "en_agua", "en_agua_profunda", "tiempo_dano_lago",
    "ultimo_agresor", "t_agresor", "visibilidad", "mantiene_ataque", "niebla_previa", "asesino",
)


def guardar_estado(jugador):
    """Foto del personaje al morir. Es una copia superficial: reaparecer reinicia el personaje
    con objetos nuevos (__init__), así que los de la foto quedan intactos."""
    return dict(jugador.__dict__)


def restaurar_estado(jugador, estado):
    """Devuelve al personaje el estado guardado en la tumba (se descarta la vida nueva). Queda
    donde está, con la vida, la energía y los escudos llenos y sin efectos."""
    actuales = {k: jugador.__dict__[k] for k in CAMPOS_TRANSITORIOS if k in jugador.__dict__}
    permanentes = jugador.talismanes.permanentes()   # anillo de brujula de la vida nueva
    jugador.__dict__.update(estado)
    jugador.__dict__.update(actuales)
    jugador.talismanes.conservar(permanentes)
    jugador.efectos_extra = []
    # Habilidades que estaban en marcha al morir: terminan y pasan a su recarga
    for h in jugador.coleccion_habilidades:
        if h.estado != "LISTA" or getattr(h, "canalizando", False) or getattr(h, "cargando", False):
            jugador._retirar_habilidad(h)
    jugador.sombras_anillo.matar_todas()        # vuelven tras su tiempo de reaparición
    jugador.recalcular_talismanes()
    jugador.vida = jugador.vida_max
    jugador.energia = jugador.energia_max
    jugador.escudo = jugador.escudo_max
    jugador.escudo_magico = jugador.escudo_magico_max
    jugador.desangrado = None
    jugador.veneno = None
    jugador.ralentizacion = 0.0
    jugador.tiempo_ralentizacion = 0.0
    jugador.t_invulnerable = 0.0


class Tumba:
    """Lápida sólida que se rompe con GOLPES_TUMBA golpes directos. Entra en la lista de
    enemigos de los ataques directos; los daños por segundo escriben 'vida' y no le afectan."""
    es_tumba = True
    masa = math.inf          # nada la desplaza
    herramienta = None       # no ataca
    escudo = 0.0
    escudo_magico = 0.0
    apuntable = True

    def __init__(self, posicion, estado):
        self.posicion = pygame.Vector2(posicion)
        self.radio = RADIO_TUMBA
        self.estado = estado
        self.golpes = GOLPES_TUMBA
        self.restante = DURACION_TUMBA
        self._t_golpe = 0.0

    @property
    def vivo(self):
        return self.golpes > 0 and self.restante > 0

    @vivo.setter
    def vivo(self, valor):
        pass                 # solo la rompen los golpes o el tiempo

    @property
    def rota(self):
        return self.golpes <= 0

    @property
    def caducada(self):
        return self.restante <= 0 and not self.rota

    @property
    def vida(self):
        return float(self.golpes)

    @vida.setter
    def vida(self, valor):
        pass                 # quemadura, suelo en llamas y otros daños por segundo no la rompen

    @property
    def vida_max(self):
        return float(GOLPES_TUMBA)

    def recibir_dano(self, cantidad=0, tipo_dano=None, direccion=None):
        """Cada golpe directo quita 1, haga el daño que haga. Devuelve 0 (no tiene vida)."""
        if self.vivo:
            self.golpes -= 1
            self._t_golpe = DURACION_DESTELLO_GOLPE
        return 0.0

    def aplicar_empuje(self, direccion, puntos):
        pass                 # no se mueve

    def actualizar(self, dt):
        self.restante = max(0.0, self.restante - dt)
        self._t_golpe = max(0.0, self._t_golpe - dt)

    def dibujar(self, pantalla, desplazamiento, fuente):
        """Lápida gris con cruz, los golpes que faltan y el tiempo que le queda."""
        if self.restante < AVISO_ULTIMO_MINUTO and (pygame.time.get_ticks() // 250) % 2 == 0:
            return
        cx = round(self.posicion.x - desplazamiento[0])
        cy = round(self.posicion.y - desplazamiento[1])
        r = self.radio
        color = (255, 255, 255) if self._t_golpe > 0 else COLOR_TUMBA
        cuerpo = pygame.Rect(cx - r, cy - r, r * 2, r * 2 + 4)
        pygame.draw.ellipse(pantalla, (40, 40, 45), (cx - r - 2, cy + r - 2, r * 2 + 4, 8))   # sombra
        pygame.draw.rect(pantalla, color, cuerpo, border_top_left_radius=r, border_top_right_radius=r)
        pygame.draw.rect(pantalla, COLOR_TUMBA_BORDE, cuerpo, 2, border_top_left_radius=r, border_top_right_radius=r)
        pygame.draw.line(pantalla, COLOR_TUMBA_BORDE, (cx, cy - r + 6), (cx, cy + 6), 2)
        pygame.draw.line(pantalla, COLOR_TUMBA_BORDE, (cx - 5, cy - 3), (cx + 5, cy - 3), 2)
        texto = fuente.render(f"{self.golpes}/{GOLPES_TUMBA}", True, COLOR_INDICADOR)
        pantalla.blit(texto, (cx - texto.get_width() // 2, cy - r - texto.get_height() - 2))

    def dibujar_indicador(self, pantalla, area, jugador, fuente):
        """Flecha en el borde del área del mundo apuntando a la tumba, con distancia y tiempo."""
        d = self.posicion - jugador.posicion
        dist = d.length()
        minutos, segundos = divmod(int(self.restante), 60)
        texto = fuente.render(f"Tumba {int(dist)} px · {minutos}:{segundos:02d}", True, COLOR_INDICADOR)
        if dist < 1:
            return
        dn = d / dist
        centro = pygame.Vector2(area.center)
        # Punto del borde (con margen) en la dirección de la tumba
        mx, my = area.width / 2 - 40, area.height / 2 - 40
        escala = min(mx / abs(dn.x) if dn.x else math.inf, my / abs(dn.y) if dn.y else math.inf)
        punta = centro + dn * min(escala, max(60.0, dist))
        perp = pygame.Vector2(-dn.y, dn.x)
        p1 = punta + dn * 10
        p2 = punta - dn * 6 + perp * 7
        p3 = punta - dn * 6 - perp * 7
        pygame.draw.polygon(pantalla, COLOR_INDICADOR, [p1, p2, p3])
        pygame.draw.polygon(pantalla, COLOR_TUMBA_BORDE, [p1, p2, p3], 1)
        pos_t = punta - dn * 24
        pantalla.blit(texto, (round(pos_t.x - texto.get_width() / 2), round(pos_t.y - texto.get_height() / 2)))
