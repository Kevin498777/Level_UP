"""
Talismanes: anillos y Tótem de vida (fase 1 del sistema de Gacha).

- Los anillos se consiguen (más adelante, en el Gacha) y se mejoran al conseguir uno repetido,
  hasta su nivel máximo. Solo dan su efecto si están EQUIPADOS en uno de los 3 huecos
  (máximo 1 legendario y 2 épicos equipados a la vez).
- El Tótem de vida se acumula (hasta 5) y ocupa UN hueco con toda su pila. Si mueres con él
  equipado, gastas uno, vuelves al centro y no pierdes nada.
- Todo esto se pierde al morir sin tótem (vive dentro del Personaje).
"""
import math
import pygame

# ---------------------------------------------------------------- Rarezas
COMUN, ESPECIAL, EPICO, LEGENDARIO = "comun", "especial", "epico", "legendario"
NOMBRE_RAREZA = {COMUN: "Común", ESPECIAL: "Especial", EPICO: "Épico", LEGENDARIO: "Legendario"}
COLOR_RAREZA = {COMUN: (170, 176, 188), ESPECIAL: (90, 170, 255), EPICO: (190, 110, 255), LEGENDARIO: (255, 190, 60)}
# Probabilidad de cada rareza cuando el Gacha da un anillo (fase 3)
PROB_RAREZA = {COMUN: 0.60, ESPECIAL: 0.30, EPICO: 0.09, LEGENDARIO: 0.01}
# Máximo de anillos equipados a la vez por rareza (None = sin límite propio)
MAX_EQUIPADOS_RAREZA = {LEGENDARIO: 1, EPICO: 2}

HUECOS = 3                       # huecos de equipamiento (anillos y tótem)
DEVOLUCION_REPETIDO = 5          # monedas que devuelve un premio repetido (menos que la tirada: sin monedas infinitas)

# ---------------------------------------------------------------- Colores de cada anillo
BLANCO = (238, 238, 242)
NARANJA = (255, 140, 40)
AZUL_MARINO = (32, 52, 150)
ROSA = (255, 130, 185)
AMARILLO = (250, 220, 60)
GRIS = (150, 152, 162)
CELESTE = (120, 210, 255)
CAFE = (135, 88, 52)
DORADO = (245, 195, 60)
OSCURO = (52, 50, 66)
MORADO = (140, 70, 200)
AZUL = (70, 130, 235)
ROJO = (215, 50, 60)

# Efectos por nivel
VIENTO_VEL_POR_NIVEL = 0.01            # +1 % de velocidad base por nivel (máx. +10 %)
FUERZA_DANO_POR_NIVEL = 0.01           # +1 % de daño del arma por nivel (máx. +10 %)
ENERGIA_POR_NIVEL = 2.5
VIDA_POR_NIVEL = 4                     # épico: +4 por nivel (máx. +20)
CADENCIA_POR_NIVEL = 0.3               # épico: +0.3 golpes/s por nivel (máx. +1.5)
DEFENSA_MAXIMA = 20                    # especiales: +20 de escudo repartido en 7 niveles
DEFENSA_NIVEL_MAX = 7
REGEN_ESCUDO_ANILLO = 0.10             # +10 % fijo a la regeneración de ese escudo
REGEN_VIDA_POR_NIVEL = 0.3             # legendario: vida por segundo por nivel
REGEN_VIDA_INTERVALO = 1.0             # se aplica cada segundo

# Anillos de sombra: el nivel del anillo (1-10) usa la vida y la velocidad de la habilidad
# de invocación a este nivel (1-20); el daño y la reaparición van en línea recta.
NIVEL_HABILIDAD_SOMBRA = (1, 3, 5, 7, 9, 12, 14, 16, 18, 20)
SOMBRA_NIVEL_MAX = 10
SOMBRA_CONEJO_DANO = (1.0, 7.7)        # daño del conejo en nivel 1 y 10 del anillo
SOMBRA_CONEJO_REAPARICION = (10.0, 5.0)
SOMBRA_LOBO_DANO = (4.0, 30.0)
SOMBRA_LOBO_REAPARICION = (8.0, 4.0)
AGRESION_MEMORIA = 6.0                 # s que la sombra recuerda a quien te atacó

TOTEM = "totem_vida"
TOTEM_MAX = 5
COLOR_TOTEM = (90, 200, 120)


def _lineal(par, n, n_max=SOMBRA_NIVEL_MAX):
    a, b = par
    return round(a + (b - a) * (n - 1) / (n_max - 1), 2)


def _defensa(n):
    return round(DEFENSA_MAXIMA * n / DEFENSA_NIVEL_MAX, 2)


def stats_sombra(tipo, n):
    """Vida, velocidad, daño y segundos de reaparición de la sombra de un anillo de nivel n."""
    import habilidades as H
    nivel_hab = NIVEL_HABILIDAD_SOMBRA[n - 1]
    if tipo == "conejo":
        h = H.InvocacionConejos()
        while h.nivel < nivel_hab and h.subir_nivel():
            pass
        return dict(vida=h.vida_conejo, velocidad=h.velocidad_conejo, dano=_lineal(SOMBRA_CONEJO_DANO, n),
                    reaparicion=_lineal(SOMBRA_CONEJO_REAPARICION, n))
    h = H.InvocacionLobos()
    while h.nivel < nivel_hab and h.subir_nivel():
        pass
    return dict(vida=h.vida_lobo, velocidad=h.velocidad_lobo, dano=_lineal(SOMBRA_LOBO_DANO, n),
                reaparicion=_lineal(SOMBRA_LOBO_REAPARICION, n))


def _efecto_viento(n): return {"velocidad_pct": round(VIENTO_VEL_POR_NIVEL * n, 4)}
def _efecto_fuerza(n): return {"dano_pct": round(FUERZA_DANO_POR_NIVEL * n, 4)}
def _efecto_energia(n): return {"energia_max": ENERGIA_POR_NIVEL * n}
def _efecto_vida(n): return {"vida_max": VIDA_POR_NIVEL * n}
def _efecto_cadencia(n): return {"cadencia": round(CADENCIA_POR_NIVEL * n, 2)}
def _efecto_def_magica(n): return {"escudo_magico": _defensa(n), "regen_escudo_magico": REGEN_ESCUDO_ANILLO}
def _efecto_def_fisica(n): return {"escudo": _defensa(n), "regen_escudo": REGEN_ESCUDO_ANILLO}
def _efecto_regeneracion(n): return {"regen_vida": (round(REGEN_VIDA_POR_NIVEL * n, 2), REGEN_VIDA_INTERVALO)}
def _efecto_sombra_conejo(n): return {"sombra_conejo": n}
def _efecto_sombra_lobo(n): return {"sombra_lobo": n}


def _txt_viento(n): return f"+{VIENTO_VEL_POR_NIVEL * n * 100:g}% de velocidad base"
def _txt_fuerza(n): return f"+{FUERZA_DANO_POR_NIVEL * n * 100:g}% de daño del arma"
def _txt_energia(n): return f"+{ENERGIA_POR_NIVEL * n:g} de energía máxima"
def _txt_vida(n): return f"+{VIDA_POR_NIVEL * n:g} de vida máxima"
def _txt_cadencia(n): return f"+{CADENCIA_POR_NIVEL * n:g} golpes/s de cadencia"
def _txt_def_magica(n): return f"+{_defensa(n):g} de escudo mágico máx. · +10% regeneración"
def _txt_def_fisica(n): return f"+{_defensa(n):g} de escudo físico máx. · +10% regeneración"
def _txt_regeneracion(n): return f"+{REGEN_VIDA_POR_NIVEL * n:g} de vida por segundo"


def _txt_sombra(tipo, nombre):
    def texto(n):
        s = stats_sombra(tipo, n)
        return (f"Sombra de {nombre}: vida {s['vida']:g} · daño {s['dano']:g} · reaparece en {s['reaparicion']:g} s. "
                f"Te defiende de quien te ataque")
    return texto


# id -> definición
ANILLOS = {
    "viento":     dict(nombre="Anillo de viento", rareza=COMUN, colores=(BLANCO,), nivel_max=10,
                       efecto=_efecto_viento, texto=_txt_viento),
    "fuerza":     dict(nombre="Anillo de fuerza", rareza=COMUN, colores=(NARANJA,), nivel_max=10,
                       efecto=_efecto_fuerza, texto=_txt_fuerza),
    "energia":    dict(nombre="Anillo de energía", rareza=COMUN, colores=(AZUL_MARINO,), nivel_max=10,
                       efecto=_efecto_energia, texto=_txt_energia),
    "sombra_conejo": dict(nombre="Anillo sombra conejo", rareza=COMUN, colores=(OSCURO,), nivel_max=SOMBRA_NIVEL_MAX,
                          efecto=_efecto_sombra_conejo, texto=_txt_sombra("conejo", "conejo")),
    "def_magica": dict(nombre="Anillo de defensa mágica", rareza=ESPECIAL, colores=(AZUL,), nivel_max=DEFENSA_NIVEL_MAX,
                       efecto=_efecto_def_magica, texto=_txt_def_magica),
    "def_fisica": dict(nombre="Anillo de defensa física", rareza=ESPECIAL, colores=(CAFE,), nivel_max=DEFENSA_NIVEL_MAX,
                       efecto=_efecto_def_fisica, texto=_txt_def_fisica),
    "vida":       dict(nombre="Anillo de vida", rareza=EPICO, colores=(ROSA, ROJO), nivel_max=5,
                       efecto=_efecto_vida, texto=_txt_vida),
    "cadencia":   dict(nombre="Anillo de cadencia", rareza=EPICO, colores=(AMARILLO, AZUL), nivel_max=5,
                       efecto=_efecto_cadencia, texto=_txt_cadencia),
    "sombra_lobo": dict(nombre="Anillo sombra lobo", rareza=EPICO, colores=(OSCURO, MORADO), nivel_max=SOMBRA_NIVEL_MAX,
                        efecto=_efecto_sombra_lobo, texto=_txt_sombra("lobo", "lobo")),
    "regeneracion": dict(nombre="Anillo de regeneración inversa", rareza=LEGENDARIO,
                         colores=(ROSA, AZUL_MARINO, DORADO), nivel_max=3,
                         efecto=_efecto_regeneracion, texto=_txt_regeneracion),
}


class GestorSombras:
    """Sombras de los anillos (conejo y lobo): una de cada, te siguen y solo atacan a quien
    te haya atacado a ti o a ellas en los últimos segundos. Si mueren reaparecen tras su
    tiempo. No se controlan. Expone 'criaturas' como las habilidades de invocación."""

    def __init__(self):
        self.niveles = {}        # "conejo"/"lobo" -> nivel del anillo equipado
        self.entidades = {}      # tipo -> entidad viva (o ausente)
        self.esperas = {}        # tipo -> segundos que faltan para reaparecer

    @property
    def criaturas(self):
        return [e for e in self.entidades.values() if e.vivo]

    def configurar(self, niveles, jugador):
        """Anillos de sombra equipados ahora: {"conejo": n, "lobo": n}. Quita las que ya no van
        y hace aparecer al instante las nuevas (o mejora las que cambian de nivel)."""
        for tipo in list(self.entidades):
            if tipo not in niveles:
                self.entidades.pop(tipo).vivo = False
        for tipo in list(self.esperas):
            if tipo not in niveles:
                del self.esperas[tipo]
        for tipo, n in niveles.items():
            if self.niveles.get(tipo) != n:
                vieja = self.entidades.pop(tipo, None)
                if vieja is not None:
                    vieja.vivo = False
                self.esperas[tipo] = 0.0          # aparece ya con el nivel nuevo
        self.niveles = dict(niveles)

    def matar_todas(self):
        """Al morir o al salvarte un tótem: desaparecen y vuelven tras su tiempo de reaparición."""
        for tipo, e in list(self.entidades.items()):
            e.vivo = False
            self.esperas[tipo] = stats_sombra(tipo, self.niveles[tipo])["reaparicion"]
        self.entidades.clear()

    def _crear(self, tipo, jugador):
        import habilidades as H
        import random as _r
        s = stats_sombra(tipo, self.niveles[tipo])
        off = pygame.Vector2(_r.uniform(-30, 30), _r.uniform(-30, 30))
        cls = H.Conejo if tipo == "conejo" else H.Lobo
        e = cls(jugador.posicion.x + off.x, jugador.posicion.y + off.y, s["vida"], s["velocidad"], s["dano"])
        e.es_sombra_anillo = True
        return e

    @staticmethod
    def _agresor(obj):
        a = getattr(obj, "ultimo_agresor", None)
        if a is None or getattr(obj, "t_agresor", 0.0) <= 0 or not getattr(a, "vivo", True):
            return None
        if getattr(a, "invisible", False) or getattr(a, "en_cueva", False) or getattr(a, "sumergido", False):
            return None
        return a

    def actualizar(self, dt, jugador):
        if hasattr(jugador, "t_agresor"):
            jugador.t_agresor = max(0.0, jugador.t_agresor - dt)
        for tipo in self.niveles:
            e = self.entidades.get(tipo)
            if e is not None and not e.vivo:
                self.entidades.pop(tipo)
                self.esperas[tipo] = stats_sombra(tipo, self.niveles[tipo])["reaparicion"]
                e = None
            if e is None:
                self.esperas[tipo] = self.esperas.get(tipo, 0.0) - dt
                if self.esperas[tipo] <= 0:
                    self.entidades[tipo] = e = self._crear(tipo, jugador)
                    del self.esperas[tipo]
                else:
                    continue
            if hasattr(e, "t_agresor"):
                e.t_agresor = max(0.0, e.t_agresor - dt)
            objetivo = self._agresor(e) or self._agresor(jugador)
            if objetivo is not None and (objetivo.posicion - jugador.posicion).length() > 600:
                objetivo = None
            e.actualizar(dt, jugador, objetivo, False)

    def dibujar_invocaciones(self, pantalla, desplazamiento=(0, 0)):
        for e in self.criaturas:
            e.dibujar(pantalla, desplazamiento)


def marcar_agresor(objetivo, atacante):
    """Lo llaman los ataques de la fauna y del maniquí: las sombras de los anillos defienden
    al jugador (o a sí mismas) de este atacante durante AGRESION_MEMORIA segundos."""
    try:
        objetivo.ultimo_agresor = atacante
        objetivo.t_agresor = AGRESION_MEMORIA
    except AttributeError:
        pass


def anillos_de_rareza(rareza):
    return [i for i, d in ANILLOS.items() if d["rareza"] == rareza]


class ColeccionTalismanes:
    """Anillos conseguidos (id -> nivel), tótems acumulados y los 3 huecos equipados."""

    def __init__(self):
        self.anillos = {}
        self.totems = 0
        self.huecos = [None] * HUECOS          # id de anillo, TOTEM o None

    # ---- Conseguir
    def agregar_anillo(self, id_anillo):
        """'nuevo' (nivel 1), 'mejorado' (+1 nivel) o 'maximo' (ya al máximo: devuelve monedas)."""
        maximo = ANILLOS[id_anillo]["nivel_max"]
        nivel = self.anillos.get(id_anillo, 0)
        if nivel >= maximo:
            return "maximo"
        self.anillos[id_anillo] = nivel + 1
        return "nuevo" if nivel == 0 else "mejorado"

    def agregar_totem(self):
        """'nuevo' / 'mas' o 'maximo' (ya tienes 5: devuelve monedas)."""
        if self.totems >= TOTEM_MAX:
            return "maximo"
        self.totems += 1
        return "nuevo" if self.totems == 1 else "mas"

    # ---- Equipar
    def equipados(self):
        return [h for h in self.huecos if h is not None]

    def esta_equipado(self, id_obj):
        return id_obj in self.huecos

    def motivo_no_equipar(self, id_obj):
        """None si se puede equipar; si no, el motivo (texto para la interfaz)."""
        if self.esta_equipado(id_obj):
            return "Ya está equipado"
        if None not in self.huecos:
            return "Los 3 huecos están ocupados: quita uno primero"
        if id_obj == TOTEM:
            return None if self.totems > 0 else "No tienes tótems"
        if id_obj not in self.anillos:
            return "No tienes ese anillo"
        rareza = ANILLOS[id_obj]["rareza"]
        tope = MAX_EQUIPADOS_RAREZA.get(rareza)
        if tope is not None:
            n = sum(1 for h in self.equipados() if h != TOTEM and ANILLOS[h]["rareza"] == rareza)
            if n >= tope:
                return f"Solo puedes equipar {tope} {NOMBRE_RAREZA[rareza].lower()}{'s' if tope > 1 else ''} a la vez"
        return None

    def equipar(self, id_obj):
        motivo = self.motivo_no_equipar(id_obj)
        if motivo is not None:
            return False, motivo
        self.huecos[self.huecos.index(None)] = id_obj
        return True, None

    def quitar(self, hueco):
        if 0 <= hueco < HUECOS:
            self.huecos[hueco] = None

    # ---- Tótem
    def usar_totem(self):
        """Al morir: si el tótem está equipado y queda alguno, gasta uno y devuelve True."""
        if TOTEM not in self.huecos or self.totems <= 0:
            return False
        self.totems -= 1
        if self.totems == 0:
            self.huecos[self.huecos.index(TOTEM)] = None
        return True

    # ---- Efectos
    def bonos(self):
        """Suma de los efectos de los anillos equipados."""
        total = {}
        for h in self.equipados():
            if h == TOTEM:
                continue
            d = ANILLOS[h]
            for clave, valor in d["efecto"](self.anillos[h]).items():
                if clave == "regen_vida":
                    total[clave] = valor
                else:
                    total[clave] = round(total.get(clave, 0) + valor, 4)
        return total


def texto_efecto(id_obj, nivel):
    if id_obj == TOTEM:
        return "Si mueres con él equipado, gastas 1, vuelves al centro y no pierdes nada"
    return ANILLOS[id_obj]["texto"](nivel)


# ---------------------------------------------------------------- Dibujo
def dibujar_anillo(pantalla, centro, radio, id_anillo, tiempo=0.0):
    """Anillo visto de frente: aro grueso con su color (o sus colores por tramos)."""
    colores = ANILLOS[id_anillo]["colores"]
    cx, cy = centro
    grosor = max(3, radio // 3)
    # sombra
    pygame.draw.circle(pantalla, (10, 12, 16), (cx + 2, cy + 3), radio, grosor)
    if len(colores) == 1:
        pygame.draw.circle(pantalla, colores[0], (cx, cy), radio, grosor)
    else:
        n = len(colores)
        rect = pygame.Rect(cx - radio, cy - radio, radio * 2, radio * 2)
        for i, col in enumerate(colores):
            a0 = math.tau * i / n
            a1 = math.tau * (i + 1) / n
            pygame.draw.arc(pantalla, col, rect, a0, a1 + 0.05, grosor)
    # contorno claro para que el azul marino se vea en fondo oscuro
    pygame.draw.circle(pantalla, (200, 205, 220), (cx, cy), radio, 1)
    pygame.draw.circle(pantalla, (60, 64, 76), (cx, cy), radio - grosor, 1)
    # brillo
    pygame.draw.arc(pantalla, (255, 255, 255), pygame.Rect(cx - radio + 2, cy - radio + 2, radio * 2 - 4, radio * 2 - 4),
                    math.radians(100), math.radians(150), 2)
    rareza = ANILLOS[id_anillo]["rareza"]
    if rareza in (EPICO, LEGENDARIO):
        # gema arriba
        gema = DORADO if rareza == LEGENDARIO else CELESTE
        pulso = 1 + int(abs(math.sin(tiempo * 3)) * 2)
        pygame.draw.circle(pantalla, gema, (cx, cy - radio), max(3, radio // 4) + pulso // 2)
        pygame.draw.circle(pantalla, (255, 255, 255), (cx - 1, cy - radio - 1), 1)


def dibujar_totem(pantalla, centro, radio):
    """Tótem de vida: pequeño tótem tallado verde con ojos dorados."""
    cx, cy = centro
    ancho = radio
    alto = int(radio * 1.8)
    cuerpo = pygame.Rect(cx - ancho // 2, cy - alto // 2, ancho, alto)
    pygame.draw.rect(pantalla, (10, 12, 16), cuerpo.move(2, 3), border_radius=4)
    pygame.draw.rect(pantalla, COLOR_TOTEM, cuerpo, border_radius=4)
    pygame.draw.rect(pantalla, (40, 110, 60), cuerpo, width=2, border_radius=4)
    # alas
    pygame.draw.polygon(pantalla, (60, 160, 90), [(cuerpo.left, cy - alto // 6), (cuerpo.left - ancho // 2, cy - alto // 3),
                                                   (cuerpo.left, cy)])
    pygame.draw.polygon(pantalla, (60, 160, 90), [(cuerpo.right, cy - alto // 6), (cuerpo.right + ancho // 2, cy - alto // 3),
                                                   (cuerpo.right, cy)])
    # ojos y boca
    pygame.draw.circle(pantalla, DORADO, (cx - ancho // 5, cy - alto // 5), max(2, radio // 7))
    pygame.draw.circle(pantalla, DORADO, (cx + ancho // 5, cy - alto // 5), max(2, radio // 7))
    pygame.draw.line(pantalla, (30, 70, 40), (cx - ancho // 4, cy + alto // 8), (cx + ancho // 4, cy + alto // 8), 2)


def dibujar_objeto(pantalla, centro, radio, id_obj, tiempo=0.0):
    if id_obj == TOTEM:
        dibujar_totem(pantalla, centro, radio)
    else:
        dibujar_anillo(pantalla, centro, radio, id_obj, tiempo)


def nombre_objeto(id_obj):
    return "Tótem de vida" if id_obj == TOTEM else ANILLOS[id_obj]["nombre"]


def color_objeto(id_obj):
    return COLOR_TOTEM if id_obj == TOTEM else COLOR_RAREZA[ANILLOS[id_obj]["rareza"]]
