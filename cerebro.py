"""Inteligencia de los bots (Fase 4 del plan de NPC).

CerebroBot es una maquina de estados que decide las intenciones de un personaje (las mismas que
el teclado y el raton piden para el jugador):

| Estado      | Que hace                                              | Cuando cambia                         |
|-------------|-------------------------------------------------------|---------------------------------------|
| Explorar    | camina por el mapa buscando presas de su nivel        | ve una presa que puede ganar: Cazar   |
| Cazar       | se acerca, usa el arma y sus habilidades              | gana: Explorar; vida < 30 %: Huir     |
| Huir        | se aleja; Destello, Paso 0, "Huye", "Sal volado"...   | a salvo: Curarse                      |
| Curarse     | se queda quieto y se regenera (Regeneracion Inversa)  | vida >= 80 %: Explorar                |
| Defenderse  | contraataca a quien le golpea (o huye si va mal)      | agresor muerto o lejos: Explorar      |

- "piensa" (__call__) cada 0.2-0.5 s, repartido entre fotogramas (mundo.actualizar_otros_combatientes);
  fotograma() se llama en cada fotograma para seguir la ruta y soltar las cargas a tiempo.
- Sin odio (Humanos): nunca empieza una pelea con otro personaje; solo se defiende.
- Sus invocaciones funcionan como los anillos de sombra: solo atacan a quien ataca a su dueno o
  a ellas.
- Al subir de nivel reparte los puntos con su estilo (tanque, dano, equilibrado o habilidades) y
  en el nivel NIVEL_POTENCIADA desbloquea la potenciada de una de sus habilidades (solo una).
- No toca nada del jugador: ni frutales, ni cofres, ni orbes.
"""
import math
import random

import pygame

EXPLORAR, CAZAR, HUIR, CURARSE, DEFENDERSE = "Explorar", "Cazar", "Huir", "Curarse", "Defenderse"
UMBRAL_HUIR = 0.30              # fraccion de vida para huir
UMBRAL_CURADO = 0.80            # fraccion de vida para volver a explorar
VISION = 700                    # px a los que ve presas
DISTANCIA_EXPLORAR = (900, 2500)    # px del siguiente punto al que camina explorando
DISTANCIA_A_SALVO = 650         # px sin amenazas cerca para dejar de huir
TIEMPO_MAX_CAZA = 20.0          # s persiguiendo una presa sin herirla: la deja (se escapa)
IGNORAR_PRESA = 40.0            # s que no vuelve a por una presa que se le escapo
OLVIDAR_AGRESOR = 900           # px a los que deja de perseguir a quien le ataco
NIVEL_POTENCIADA = 20
# Nivel minimo para que una presa le parezca ganable (duelos de Balance_Estado.md: la manada se
# gana desde el nivel 5 y el oso desde el 15). Si una especie le mato, la evita EVITAR_SI_MATO
# niveles mas.
NIVEL_PRESA = {"ConejoSalvaje": 1, "Venado": 1, "Zorro": 2, "Jabali": 2, "Lobo": 5,
               "LoboSolitario": 10, "Cocodrilo": 12, "Oso": 15}
EVITAR_SI_MATO = 5
# Alcance de cada arma (px desde su centro) para empezar a golpear
ALCANCE_ARMA = {"Espada Ligera": 55, "Espada Larga": 70, "Mandoble": 85, "Dagas Simples": 40, "Escudo": 45}
DISTANCIA_ARCO = 220            # px a los que el Arco se pone a disparar
CARGA_ARCO = (2.0, 3.5)         # s que tensa el arco (mas carga = mas alcance y dano)
CARGA_ARCO_LEJOS = (3.5, 4.5)   # contra presas huidizas: mas carga para llegar desde lejos
# Presas que huyen mas rapido que un personaje (y se asustan a ~160 px): se cazan desde lejos
PRESAS_HUIDIZAS = ("ConejoSalvaje", "Venado", "Zorro")
DISTANCIA_CAZA_A_DISTANCIA = 300    # px a los que se queda para disparar habilidades
DISTANCIA_ESCUDO = 110          # px a los que se planta con el Escudo (Aura, Burst, Onda al alcance)
DISTANCIA_SACAR_ARMA = 150      # px antes del alcance en los que desenfunda
HABILIDADES_A_DISTANCIA = ("Disparo Veloz", "Disparo Venenoso", "Cortar", "Carga de Fuego")
CARGA_FUEGO = (1.2, 3.0)        # s que carga la Carga de Fuego / Estrella Ignea
RANGO_DISPARO = 450             # px para Disparo Veloz, Disparo Venenoso y Cortar
RANGO_ONDA = 260                # px para Onda Sonora
RANGO_AURA = 150                # px para Aura Electrica
RANGO_BURST = 100               # px para Burst de Fuerza
# Estilos para repartir los puntos de mejora: peso de cada destino
ESTILOS = {
    "tanque": {"vida": 4, "escudo": 2, "escudo_magico": 2, "fuerza": 1, "habilidad": 1},
    "dano": {"fuerza": 4, "cadencia": 2, "arma": 2, "vida": 1, "habilidad": 1},
    "equilibrado": {"vida": 2, "fuerza": 2, "energia": 1, "escudo": 1, "arma": 1, "habilidad": 2},
    "habilidades": {"habilidad": 6, "energia": 2, "regen_energia": 1, "vida": 1},
}
# Regeneracion de los NPC fuera de pelea (tu indicacion del 27/11): mas rapida que la normal
FUERA_DE_PELEA_TRAS = 5.0       # s sin recibir dano ni pelear
REGEN_VIDA_FUERA = 0.03         # fraccion de la vida maxima por segundo
REGEN_EXTRA_FUERA = 2.0         # energia y escudos se regeneran este numero de veces mas rapido


class CerebroBot:
    def __init__(self, navegador, rng=None, estilo=None, odio=False):
        self.nav = navegador
        self.rng = rng or random.Random()
        self.estilo = estilo or self.rng.choice(tuple(ESTILOS))
        self.odio = odio                # Humanos: False (solo se defienden)
        self.estado = EXPLORAR
        self.presa = None
        self.agresor = None
        self.carga = None               # (habilidad o "arco", segundos que faltan)
        self.temidos = {}               # especie -> veces que le mato
        self.vida_previa = None
        self.t_sin_pelea = 0.0
        self.potenciada_elegida = False
        self.vida_criaturas = {}
        self.t_caza = 0.0               # s persiguiendo la presa actual sin herirla
        self.vida_presa = None
        self.ignoradas = {}             # id(animal) -> segundos que la ignora

    # ------------------------------------------------------------ percepcion
    def _animales_cerca(self, c, ctx, radio=VISION):
        zona = pygame.Rect(0, 0, radio * 2, radio * 2)
        zona.center = (round(c.posicion.x), round(c.posicion.y))
        return [a for a in ctx.fauna.animales_con_vida(zona) if (a.posicion - c.posicion).length() <= radio]

    def nivel_presa(self, animal):
        especie = type(animal).__name__
        return NIVEL_PRESA.get(especie, 99) + EVITAR_SI_MATO * self.temidos.get(especie, 0)

    def recordar_muerte(self, asesino):
        """Lo mato 'asesino': esa especie le parecera mas dificil a partir de ahora."""
        if asesino is not None:
            especie = type(asesino).__name__
            self.temidos[especie] = self.temidos.get(especie, 0) + 1

    def _agresor_valido(self, c):
        a = getattr(c, "ultimo_agresor", None)
        if a is None or getattr(c, "t_agresor", 0) <= 0:
            return None
        if not getattr(a, "vivo", True) or getattr(a, "vida", 1) <= 0:
            return None
        if (a.posicion - c.posicion).length() > OLVIDAR_AGRESOR:
            return None
        return a

    # ------------------------------------------------------------ pensar
    def __call__(self, c, ctx, jugador):
        frac = c.vida / max(1, c.vida_max)
        herido = self.vida_previa is not None and c.vida < self.vida_previa - 0.01
        self.vida_previa = c.vida
        agresor = self._agresor_valido(c)
        self._gastar_puntos(c)

        # Transiciones
        if frac < UMBRAL_HUIR and self.estado not in (HUIR, CURARSE):
            self._cambiar(c, HUIR)
        elif agresor is not None and self.estado in (EXPLORAR, CURARSE, CAZAR) and frac >= UMBRAL_HUIR:
            self.agresor = agresor
            self._cambiar(c, DEFENDERSE)
        if self.estado == DEFENDERSE and agresor is None:
            self.agresor = None
            self._cambiar(c, EXPLORAR)
        if self.estado == CAZAR and self.presa is not None:
            if self.vida_presa is None or self.presa.vida < self.vida_presa - 0.01:
                self.t_caza = 0.0               # le esta haciendo dano: sigue
            self.vida_presa = self.presa.vida
            if self.t_caza > TIEMPO_MAX_CAZA:
                self.ignoradas[id(self.presa)] = IGNORAR_PRESA
                self.presa = None
        if self.estado == CAZAR and (self.presa is None or not self.presa.vivo or
                                     (self.presa.posicion - c.posicion).length() > VISION * 1.5):
            self.presa = None
            self._cambiar(c, EXPLORAR)
        if self.estado == HUIR and not self._amenazas(c, ctx, DISTANCIA_A_SALVO):
            self._cambiar(c, CURARSE)
        if self.estado == CURARSE:
            if self._amenazas(c, ctx, DISTANCIA_A_SALVO * 0.6) and frac < UMBRAL_HUIR:
                self._cambiar(c, HUIR)
            elif frac >= UMBRAL_CURADO:
                self._cambiar(c, EXPLORAR)
        if self.estado == EXPLORAR:
            presa = self._elegir_presa(c, ctx)
            if presa is not None:
                self.presa = presa
                self.t_caza = 0.0
                self.vida_presa = None
                self._cambiar(c, CAZAR)

        # Acciones del estado
        if self.estado == EXPLORAR:
            if self.nav.objetivo is None or self.nav.llegado or self.nav.sin_ruta:
                self._nuevo_destino(c, ctx)
        elif self.estado in (CAZAR, DEFENDERSE):
            objetivo = self.presa if self.estado == CAZAR else self.agresor
            if objetivo is not None:
                self._pelear(c, ctx, objetivo, herido)
        elif self.estado == HUIR:
            self._huir(c, ctx)
        elif self.estado == CURARSE:
            self._curarse(c)
        self._ordenar_sombras(c, ctx)
        en_pelea = self.estado in (CAZAR, DEFENDERSE, HUIR) or herido
        self.t_sin_pelea = 0.0 if en_pelea else self.t_sin_pelea

    def _cambiar(self, c, estado):
        if estado == self.estado:
            return
        self.estado = estado
        c.mantiene_ataque = False
        if c.objetivo_apuntado is not None:
            c.apuntar(None)
        if estado in (EXPLORAR, HUIR, CURARSE) and c.herramienta and c.herramienta.activa:
            c.alternar_arma()                   # enfundada camina mas rapido
        if estado == CURARSE:
            self.nav.parar(c)

    # ------------------------------------------------------------ explorar y cazar
    def _elegir_presa(self, c, ctx):
        """La presa ganable que mas XP da por distancia (como el simulador: XP esperada / tiempo)."""
        mejor, valor = None, 0.0
        a_distancia = puede_atacar_a_distancia(c)
        for a in self._animales_cerca(c, ctx):
            if self.nivel_presa(a) > c.nivel or not getattr(a, "apuntable", True) or id(a) in self.ignoradas:
                continue
            if type(a).__name__ in PRESAS_HUIDIZAS and not a_distancia:
                continue                        # huye mas rapido que el: sin ataques a distancia, no
            d = (a.posicion - c.posicion).length()
            v = getattr(a, "xp", 1.0) / (60.0 + d)
            if v > valor:
                mejor, valor = a, v
        return mejor

    def _nuevo_destino(self, c, ctx):
        limite = ctx.limite
        for _ in range(12):
            ang = self.rng.uniform(0, math.tau)
            d = self.rng.uniform(*DISTANCIA_EXPLORAR)
            p = c.posicion + pygame.Vector2(math.cos(ang), math.sin(ang)) * d
            if limite.dentro(p, 400):
                self.nav.ir_a(c, p, forzar=True)
                return
        self.nav.ir_a(c, limite.centro, forzar=True)

    def _pelear(self, c, ctx, objetivo, herido):
        d = (objetivo.posicion - c.posicion).length()
        arma = c.herramienta
        es_arco = arma is not None and hasattr(arma, "iniciar_carga")
        huidiza = type(objetivo).__name__ in PRESAS_HUIDIZAS
        es_escudo = getattr(arma, "es_escudo", False)       # no hace dano: bloquea y usa habilidades
        if es_escudo:
            alcance = DISTANCIA_CAZA_A_DISTANCIA if huidiza else DISTANCIA_ESCUDO
        elif huidiza:
            # Se asusta si se acerca: se caza desde lejos (arco o habilidades a distancia)
            alcance = DISTANCIA_ARCO if es_arco else DISTANCIA_CAZA_A_DISTANCIA
        else:
            alcance = DISTANCIA_ARCO if es_arco else ALCANCE_ARMA.get(arma.nombre if arma else "", 50) + getattr(objetivo, "radio", 15)
        # el arma desenfundada frena: se saca solo al llegar cerca
        if arma and arma.activa != (d <= alcance + DISTANCIA_SACAR_ARMA):
            c.alternar_arma()
        if d > alcance:
            self.nav.ir_a(c, objetivo.posicion)
            c.mantiene_ataque = False
            if d > 500 and c.objetivo_apuntado is not None:
                c.apuntar(None)
        else:
            self.nav.parar(c)
            if c.objetivo_apuntado is not objetivo:
                c.apuntar(objetivo)
            if es_arco:
                if self.carga is None and not getattr(arma, "cargando", False):
                    c.pulsar_ataque()
                    self.carga = ("arco", self.rng.uniform(*(CARGA_ARCO_LEJOS if huidiza else CARGA_ARCO)))
            else:
                c.mantiene_ataque = not huidiza and not es_escudo
        self._usar_habilidades(c, ctx, objetivo, d, herido)

    # ------------------------------------------------------------ huir y curarse
    def _amenazas(self, c, ctx, radio):
        hostiles = [a for a in self._animales_cerca(c, ctx, radio) if getattr(a, "estado", "") in ("ataca", "rabia", "caza")
                    or self.nivel_presa(a) > c.nivel]
        if self.agresor is not None and (self.agresor.posicion - c.posicion).length() <= radio:
            hostiles.append(self.agresor)
        return hostiles

    def _huir(self, c, ctx):
        c.mantiene_ataque = False
        amenazas = self._amenazas(c, ctx, VISION)
        if amenazas:
            centro = sum((a.posicion for a in amenazas), pygame.Vector2()) / len(amenazas)
            lejos = c.posicion - centro
            if lejos.length_squared() == 0:
                lejos = pygame.Vector2(1, 0)
            destino = ctx.limite.acotar(c.posicion + lejos.normalize() * 900, 400)
            self.nav.ir_a(c, destino)
        for h in c.habilidades:
            if h.estado != "LISTA":
                continue
            if h.nombre in ("Destello", "Paso 0", "Reforzamiento Mágico"):
                c.pulsar_habilidad(h)
                c.soltar_habilidad(h)
            elif h.nombre == "Onda Sonora" and getattr(h, "cargable", False) and amenazas:
                for clave in ("huye", "sal_volado"):
                    if c.elegir_palabra(clave):
                        break

    def _curarse(self, c):
        for h in c.habilidades:
            if h.nombre == "Regeneración Inversa" and h.estado == "LISTA" and not getattr(h, "canalizando", False):
                c.pulsar_habilidad(h)               # se mantiene hasta curarse (fotograma suelta)

    # ------------------------------------------------------------ habilidades
    def _usar_habilidades(self, c, ctx, objetivo, d, herido):
        for h in c.habilidades:
            n = h.nombre
            if n in ("Invocar Conejos", "Invocar Lobos", "Sombra Araña"):
                if h.estado == "LISTA" and self.estado == DEFENDERSE:
                    c.pulsar_habilidad(h)
                    c.soltar_habilidad(h)
                continue
            if h.estado != "LISTA" or self.carga is not None:
                continue
            if n == "Carga de Fuego":
                if 150 <= d <= 500 and c.objetivo_apuntado is objetivo:
                    c.pulsar_habilidad(h)
                    self.carga = (h, self.rng.uniform(*CARGA_FUEGO))
            elif n in ("Disparo Veloz", "Disparo Venenoso", "Cortar"):
                if d <= RANGO_DISPARO and c.objetivo_apuntado is objetivo:
                    c.pulsar_habilidad(h)
            elif n == "Onda Sonora":
                if getattr(h, "cargable", False):          # Palabras Malditas
                    for clave in ("muere", "explota", "duerme", "no_te_muevas"):
                        if d <= 400 and c.elegir_palabra(clave):
                            break
                elif d <= RANGO_ONDA:
                    c.pulsar_habilidad(h)
            elif n == "Aura Electrica":
                if d <= RANGO_AURA:
                    c.pulsar_habilidad(h)
            elif n == "Burst de Fuerza":
                if d <= RANGO_BURST:
                    c.pulsar_habilidad(h)
            elif n == "Destello":
                if d > 300:
                    c.pulsar_habilidad(h)
            elif n == "Reforzamiento Mágico":
                if herido:
                    c.pulsar_habilidad(h)
                    c.soltar_habilidad(h)
            elif n == "Golpe de Suerte":
                c.pulsar_habilidad(h)
            elif n == "Regeneración Inversa":
                if c.vida < c.vida_max * 0.5 and d > 300:
                    c.pulsar_habilidad(h)

    def _ordenar_sombras(self, c, ctx):
        """Sombras como los anillos: atacan a quien ataca a su dueno o a ellas."""
        objetivo = self._agresor_valido(c)
        for h in c.fuentes_criaturas():
            for cr in getattr(h, "criaturas", ()):
                previa = self.vida_criaturas.get(id(cr), cr.vida)
                self.vida_criaturas[id(cr)] = cr.vida
                if objetivo is None and cr.vida < previa:
                    cerca = [a for a in self._animales_cerca(c, ctx, 220) if (a.posicion - cr.posicion).length() < 120]
                    if cerca:
                        objetivo = min(cerca, key=lambda a: (a.posicion - cr.posicion).length())
        if objetivo is None:
            return
        for h in c.habilidades:
            if hasattr(h, "ordenar") and h.estado == "INVOCADO":
                h.modo_combate = True
                h.ordenar(pygame.Vector2(objetivo.posicion), c, [objetivo])
                h.modo_combate = False

    # ------------------------------------------------------------ cada fotograma
    def fotograma(self, c, ctx, dt):
        """Seguir la ruta, soltar las cargas a tiempo, terminar de curarse y regenerarse fuera de
        pelea. Se llama en cada fotograma (pensar es mas espaciado)."""
        self.nav.actualizar(c, dt, ctx.salir_a_hueco)
        if self.carga is not None:
            que, falta = self.carga
            falta -= dt
            if falta <= 0:
                if que == "arco":
                    c.soltar_ataque()
                else:
                    c.soltar_habilidad(que)
                self.carga = None
            else:
                self.carga = (que, falta)
        for h in c.habilidades:
            if h.nombre == "Regeneración Inversa" and getattr(h, "canalizando", False) and \
                    (c.vida >= c.vida_max * UMBRAL_CURADO or self.estado in (CAZAR, DEFENDERSE, HUIR)):
                c.soltar_habilidad(h)
        if self.estado == CAZAR:
            self.t_caza += dt
        for k in list(self.ignoradas):
            self.ignoradas[k] -= dt
            if self.ignoradas[k] <= 0:
                del self.ignoradas[k]
        self.t_sin_pelea += dt
        if self.t_sin_pelea >= FUERA_DE_PELEA_TRAS and c.vida > 0:
            regenerar_fuera_de_pelea(c, dt)

    # ------------------------------------------------------------ puntos de mejora
    def _gastar_puntos(self, c):
        """Reparte los puntos con su estilo; en el nivel 20 elige su unica potenciada."""
        pesos = ESTILOS[self.estilo]
        intentos, maximo = 0, c.puntos_mejora * 4 + 20
        while c.puntos_mejora > 0 and intentos < maximo:
            intentos += 1
            destino = self.rng.choices(tuple(pesos), weights=tuple(pesos.values()))[0]
            if destino == "habilidad":
                opciones = [h for h in c.habilidades if h.nivel < h.nivel_max and c.puntos_mejora >= h.costo_mejora]
                if opciones:
                    h = self.rng.choice(opciones)
                    costo = h.costo_mejora
                    if h.subir_nivel():
                        c.puntos_mejora -= costo
            elif destino == "arma":
                if c.herramienta and c.puntos_mejora >= 2 and c.herramienta.subir_nivel():
                    c.puntos_mejora -= 2
            else:
                c.subir_stat(destino)
        if c.nivel >= NIVEL_POTENCIADA and not self.potenciada_elegida:
            self.potenciada_elegida = True
            con_potenciada = [h for h in c.habilidades if getattr(h, "tiene_potenciada", False)]
            if con_potenciada:
                c.potenciar_habilidad(self.rng.choice(con_potenciada).nombre)


def puede_atacar_a_distancia(c):
    """Lleva el Arco o alguna habilidad que dana desde lejos."""
    if c.herramienta is not None and hasattr(c.herramienta, "iniciar_carga"):
        return True
    return any(h.nombre in HABILIDADES_A_DISTANCIA for h in c.habilidades)


def regenerar_fuera_de_pelea(c, dt):
    """NPC fuera de pelea: recupera REGEN_VIDA_FUERA de su vida maxima por segundo y la energia y
    los escudos REGEN_EXTRA_FUERA veces mas rapido (lo normal ya lo hace su turno)."""
    # se acumula y se cura de 0.1 en 0.1 (curar redondea a centesimas: por fotograma se inflaria)
    c._regen_fuera = getattr(c, "_regen_fuera", 0.0) + c.vida_max * REGEN_VIDA_FUERA * dt
    if c._regen_fuera >= 0.1:
        c.curar(c._regen_fuera)
        c._regen_fuera = 0.0
    extra = dt * (REGEN_EXTRA_FUERA - 1)
    if extra > 0:
        c.actualizar_regeneracion(extra)
        c.actualizar_regeneracion_escudo(extra)
        c.actualizar_regeneracion_escudo_magico(extra)
