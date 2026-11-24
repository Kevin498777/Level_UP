"""
Gacha de Level_UP. Una tirada cuesta COSTO_TIRADA (15) monedas; desde NIVEL_POTENCIADAS (20) se
habilita el Gacha mejorado, que cuesta COSTO_TIRADA_MEJORADO (20). El premio se aplica al momento
(la ruleta del inventario solo lo muestra: cerrar el inventario o que te ataquen no hace perder nada).

Probabilidades (regla proporcional, ver probabilidades()):
- "Nada" vale siempre PROB_NADA (15 %).
- Una categoria agotada (ya tienes todo lo que puede dar) vale PROB_AGOTADA (5 %) y devuelve
  DEVOLUCION (10) monedas.
- El resto se reparte entre las categorias con premios segun PESOS_BASE.
- Desde NIVEL_POTENCIADAS (20) aparece la Habilidad potenciada; con todas las habilidades
  normales conseguidas, ocupa el sitio de "Habilidad".
- Dentro de "Anillo" solo se sortean los anillos que aun pueden subir de nivel; la probabilidad
  de una rareza sin anillos disponibles pasa a las demas.
- Garantia: la tirada GARANTIA_LEGENDARIO (90) sin legendario da el anillo legendario. Si sale
  antes (por suerte, en el Gacha o en el orbe del oso), la cuenta vuelve a 0.
"""
import math
import random
import pygame
import talismanes as TL

COSTO_TIRADA = 15                        # Gacha normal
COSTO_TIRADA_MEJORADO = 20               # Gacha mejorado (desde NIVEL_POTENCIADAS, con potenciadas)
DEVOLUCION = TL.DEVOLUCION_REPETIDO      # 10 monedas (siempre menos que la tirada)

HERRAMIENTA, HABILIDAD, ANILLO, TOTEM, POTENCIADA, NADA = ("herramienta", "habilidad", "anillo", "totem",
                                                           "potenciada", "nada")
# Peso de cada categoria cuando todavia tiene premios (se reparten lo que no es "Nada" ni agotado)
PESOS_BASE = {HERRAMIENTA: 22, HABILIDAD: 13, ANILLO: 41, TOTEM: 9, POTENCIADA: 20}
PROB_NADA = 0.15                 # fija
PROB_AGOTADA = 0.05              # fija para cada categoria que ya no puede darte nada nuevo
NIVEL_POTENCIADAS = 20           # nivel del personaje que desbloquea las habilidades potenciadas
GARANTIA_LEGENDARIO = 90         # tirada en la que el legendario sale seguro (si aun puede subir)
NOMBRE_CATEGORIA = {HERRAMIENTA: "Herramienta", HABILIDAD: "Habilidad", ANILLO: "Anillo",
                    TOTEM: "Tótem de vida", POTENCIADA: "Potenciada", NADA: "Nada"}

COLOR_HERRAMIENTA = (255, 200, 120)
COLOR_HABILIDAD = (130, 190, 255)
COLOR_POTENCIADA = (255, 120, 220)
COLOR_NADA = (120, 126, 140)


def _sortear(rng, tabla):
    r, acum = rng.random(), 0.0
    for clave, prob in tabla.items():
        acum += prob
        if r < acum:
            return clave
    return list(tabla)[-1]


# ---------------------------------------------------------------- Que queda por conseguir
def anillos_disponibles(jugador):
    """Anillos que todavia pueden subir de nivel (los que estan al maximo salen del sorteo)."""
    col = jugador.talismanes
    return [a for a, d in TL.ANILLOS.items() if col.anillos.get(a, 0) < d["nivel_max"]]


def potenciadas_disponibles(jugador):
    """Habilidades de tu coleccion con version potenciada disenada y aun no desbloqueada."""
    return [h.nombre for h in jugador.coleccion_habilidades
            if h.tiene_potenciada and h.nombre not in jugador.habilidades_potenciadas]


def categorias_activas(jugador):
    """Categorias que existen para este jugador. Desde NIVEL_POTENCIADAS aparece la potenciada;
    si ademas ya tiene todas las habilidades normales, la potenciada ocupa su sitio."""
    cats = [HERRAMIENTA, HABILIDAD, ANILLO, TOTEM]
    if gacha_mejorado(jugador):
        if not jugador.habilidades_faltantes():
            cats[cats.index(HABILIDAD)] = POTENCIADA
        else:
            cats.append(POTENCIADA)
    return cats


def categoria_agotada(jugador, cat):
    if cat == HERRAMIENTA:
        return not jugador.herramientas_faltantes()
    if cat == HABILIDAD:
        return not jugador.habilidades_faltantes()
    if cat == ANILLO:
        return not anillos_disponibles(jugador)
    if cat == TOTEM:
        return jugador.talismanes.totems >= TL.TOTEM_MAX
    if cat == POTENCIADA:
        return not potenciadas_disponibles(jugador)
    return False


def probabilidades(jugador):
    """{categoria: probabilidad} para la proxima tirada (suma 1). "Nada" fija, agotadas fijas
    y el resto repartido en proporcion a PESOS_BASE."""
    cats = categorias_activas(jugador)
    agotadas = [c for c in cats if categoria_agotada(jugador, c)]
    libres = [c for c in cats if c not in agotadas]
    resto = 1.0 - PROB_NADA - PROB_AGOTADA * len(agotadas)
    prob = {}
    if libres:
        total = sum(PESOS_BASE[c] for c in libres)
        for c in cats:
            prob[c] = PROB_AGOTADA if c in agotadas else resto * PESOS_BASE[c] / total
    else:                                  # todo conseguido: lo que no es "Nada" se reparte igual
        for c in cats:
            prob[c] = (1.0 - PROB_NADA) / len(cats)
    prob[NADA] = PROB_NADA
    return prob


def probabilidades_rareza(jugador):
    """Probabilidad de cada rareza dentro de "Anillo", solo entre rarezas con anillos disponibles."""
    disp = anillos_disponibles(jugador)
    rarezas = {r: p for r, p in TL.PROB_RAREZA.items() if any(TL.ANILLOS[a]["rareza"] == r for a in disp)}
    total = sum(rarezas.values())
    return {r: p / total for r, p in rarezas.items()} if total else {}


def gacha_mejorado(jugador):
    """True desde NIVEL_POTENCIADAS: Gacha mejorado (con habilidades potenciadas, otro coste)."""
    return jugador.nivel >= NIVEL_POTENCIADAS


def costo_tirada(jugador):
    return COSTO_TIRADA_MEJORADO if gacha_mejorado(jugador) else COSTO_TIRADA


def legendario_disponible(jugador):
    return any(TL.ANILLOS[a]["rareza"] == TL.LEGENDARIO for a in anillos_disponibles(jugador))


def tiradas_para_garantia(jugador):
    """Tiradas que faltan para el legendario garantizado (contando la que lo da)."""
    return max(1, GARANTIA_LEGENDARIO - jugador.tiradas_sin_legendario)


# ---------------------------------------------------------------- Premios
def _nuevo_resultado(categoria):
    return {"categoria": categoria, "id": None, "texto": "", "color": COLOR_NADA, "rareza": None,
            "devolucion": 0, "agotada": False, "garantia": False}


def _dar_anillo(jugador, rng, res, rareza=None):
    """Sortea la rareza (o usa la dada) y un anillo disponible de esa rareza y se lo da."""
    disp = anillos_disponibles(jugador)
    if rareza is None:
        rareza = _sortear(rng, probabilidades_rareza(jugador))
    id_anillo = rng.choice([a for a in disp if TL.ANILLOS[a]["rareza"] == rareza])
    resultado = jugador.talismanes.agregar_anillo(id_anillo)
    nombre = TL.ANILLOS[id_anillo]["nombre"]
    res.update(categoria=ANILLO, id=id_anillo, rareza=rareza, color=TL.COLOR_RAREZA[rareza])
    res["texto"] = (f"{nombre} ({TL.NOMBRE_RAREZA[rareza]}) nuevo" if resultado == "nuevo"
                    else f"{nombre} sube a Nv {jugador.talismanes.anillos[id_anillo]}")
    if rareza == TL.LEGENDARIO:
        jugador.tiradas_sin_legendario = 0        # la garantia vuelve a empezar
    jugador.recalcular_talismanes()               # por si ese anillo estaba equipado


def _agotada(res, texto, color):
    res.update(texto=texto, color=color, devolucion=DEVOLUCION, agotada=True)


def tirar_anillo(jugador, rng=random):
    """Ruleta gratis solo de anillos (orbe Gacha de la cueva del oso). Solo sortea anillos que
    aun pueden subir; si todos estan al maximo devuelve DEVOLUCION monedas. No cuenta para la
    garantia, pero si da el legendario la reinicia."""
    res = _nuevo_resultado(ANILLO)
    res["solo_anillos"] = True
    if anillos_disponibles(jugador):
        _dar_anillo(jugador, rng, res)
    else:
        _agotada(res, "Todos los anillos al máximo", TL.COLOR_RAREZA[TL.COMUN])
    if res["devolucion"]:
        jugador.monedas += res["devolucion"]
        res["texto"] += f" · +{res['devolucion']} monedas"
    return res


def tirar(jugador, rng=random):
    """Hace una tirada. Devuelve None si no hay monedas suficientes; si no, el premio:
    {categoria, id, texto, color, rareza, devolucion, agotada, garantia} (ya aplicado al jugador)."""
    costo = costo_tirada(jugador)
    if jugador.monedas < costo:
        return None
    jugador.monedas -= costo
    jugador.tiradas_sin_legendario += 1
    if jugador.tiradas_sin_legendario >= GARANTIA_LEGENDARIO and legendario_disponible(jugador):
        res = _nuevo_resultado(ANILLO)
        _dar_anillo(jugador, rng, res, TL.LEGENDARIO)
        res["garantia"] = True
        res["texto"] += " (garantizado)"
        return res

    categoria = _sortear(rng, probabilidades(jugador))
    res = _nuevo_resultado(categoria)
    if categoria == NADA:
        res["texto"] = "Nada... suerte para la próxima"
    elif categoria_agotada(jugador, categoria):
        textos = {HERRAMIENTA: ("Ya tienes todas las herramientas", COLOR_HERRAMIENTA),
                  HABILIDAD: ("Ya tienes todas las habilidades", COLOR_HABILIDAD),
                  ANILLO: ("Todos los anillos al máximo", TL.COLOR_RAREZA[TL.COMUN]),
                  TOTEM: (f"Tótem de vida (ya tienes {TL.TOTEM_MAX})", TL.COLOR_TOTEM),
                  POTENCIADA: ("Ya tienes todas las potenciadas disponibles", COLOR_POTENCIADA)}
        _agotada(res, *textos[categoria])
        if categoria == TOTEM:
            res["id"] = TL.TOTEM
        elif categoria == ANILLO:
            res["categoria"] = NADA       # sin anillo concreto que dibujar
    elif categoria == HERRAMIENTA:
        nombre = rng.choice(jugador.herramientas_faltantes())
        jugador.agregar_herramienta(nombre)
        res.update(id=nombre, texto=f"Herramienta nueva: {nombre}", color=COLOR_HERRAMIENTA)
    elif categoria == HABILIDAD:
        nombre = rng.choice(jugador.habilidades_faltantes())
        jugador.agregar_habilidad(nombre)
        res.update(id=nombre, texto=f"Habilidad nueva: {nombre}", color=COLOR_HABILIDAD)
    elif categoria == ANILLO:
        _dar_anillo(jugador, rng, res)
    elif categoria == TOTEM:
        jugador.talismanes.agregar_totem()
        res.update(id=TL.TOTEM, color=TL.COLOR_TOTEM, texto=f"Tótem de vida (x{jugador.talismanes.totems})")
    elif categoria == POTENCIADA:
        nombre = rng.choice(potenciadas_disponibles(jugador))
        jugador.potenciar_habilidad(nombre)
        hab = next(h for h in jugador.coleccion_habilidades if h.nombre == nombre)
        aviso = "" if hab.potenciada_activa else f" (súbela al Nv {hab._nivel_max_base} para usarla)"
        res.update(id=nombre, texto=f"Potenciada: {hab.POTENCIADA['nombre']} ({nombre}){aviso}", color=COLOR_POTENCIADA)

    if res["devolucion"]:
        jugador.monedas += res["devolucion"]
        res["texto"] += f" · +{res['devolucion']} monedas"
    return res


# ---------------------------------------------------------------- Ruleta (animación)
DURACION_RULETA = 2.6          # s que gira la ruleta hasta pararse en el premio
ANCHO_CASILLA = 96
CASILLAS_ANTES = 38            # casillas de relleno antes del premio (lo que "gira")


# Proporcion de las casillas de relleno (solo visual): la de un personaje que empieza
_PESO_VISUAL = {c: PESOS_BASE[c] for c in (HERRAMIENTA, HABILIDAD, ANILLO, TOTEM)}
PROB_VISUAL = {c: (1.0 - PROB_NADA) * p / sum(_PESO_VISUAL.values()) for c, p in _PESO_VISUAL.items()}
PROB_VISUAL[NADA] = PROB_NADA


def casilla_aleatoria(rng=random, solo_anillos=False):
    """Casilla de relleno para la ruleta (solo visual), con la misma proporción que el Gacha
    (o solo anillos, para la ruleta del orbe Gacha)."""
    cat = ANILLO if solo_anillos else _sortear(rng, PROB_VISUAL)
    if cat == ANILLO:
        rareza = _sortear(rng, TL.PROB_RAREZA)
        return {"categoria": cat, "id": rng.choice(TL.anillos_de_rareza(rareza)), "rareza": rareza,
                "color": TL.COLOR_RAREZA[rareza]}
    if cat == TOTEM:
        return {"categoria": cat, "id": TL.TOTEM, "rareza": None, "color": TL.COLOR_TOTEM}
    color = {HERRAMIENTA: COLOR_HERRAMIENTA, HABILIDAD: COLOR_HABILIDAD}.get(cat, COLOR_NADA)
    return {"categoria": cat, "id": None, "rareza": None, "color": color}


def nueva_ruleta(resultado, tiempo, rng=random, solo_anillos=False):
    """Tira de casillas que termina en el premio, y el momento en que empieza a girar."""
    casillas = [casilla_aleatoria(rng, solo_anillos) for _ in range(CASILLAS_ANTES)]
    casillas.append(resultado)
    casillas += [casilla_aleatoria(rng, solo_anillos) for _ in range(4)]
    return {"casillas": casillas, "t0": tiempo, "indice": CASILLAS_ANTES, "resultado": resultado,
            "desfase": rng.uniform(-0.3, 0.3)}


def progreso_ruleta(ruleta, tiempo):
    """0 -> 1 con frenado suave (ease-out cúbico)."""
    t = max(0.0, min(1.0, (tiempo - ruleta["t0"]) / DURACION_RULETA))
    return 1 - (1 - t) ** 3


def ruleta_girando(ruleta, tiempo):
    return ruleta is not None and tiempo - ruleta["t0"] < DURACION_RULETA


def dibujar_icono(pantalla, casilla, centro, radio, tiempo=0.0):
    """Icono de una casilla: anillo, tótem, herramienta, habilidad o nada."""
    cat = casilla["categoria"]
    cx, cy = centro
    if cat == ANILLO:
        TL.dibujar_anillo(pantalla, centro, radio, casilla["id"], tiempo)
    elif cat == TOTEM:
        TL.dibujar_totem(pantalla, centro, radio)
    elif cat == HERRAMIENTA:
        # espada en diagonal
        hoja_a = (cx - radio * 0.7, cy + radio * 0.7)
        hoja_b = (cx + radio * 0.8, cy - radio * 0.8)
        pygame.draw.line(pantalla, (225, 230, 240), hoja_a, hoja_b, max(3, radio // 5))
        pygame.draw.line(pantalla, COLOR_HERRAMIENTA, (cx - radio * 0.55, cy + radio * 0.15),
                         (cx - radio * 0.15, cy + radio * 0.55), max(3, radio // 5))
        pygame.draw.circle(pantalla, COLOR_HERRAMIENTA, (int(cx - radio * 0.75), int(cy + radio * 0.75)), max(3, radio // 5))
    elif cat in (HABILIDAD, POTENCIADA):
        # rombo mágico con brillo (rosa si es potenciada)
        color = COLOR_POTENCIADA if cat == POTENCIADA else COLOR_HABILIDAD
        pts = [(cx, cy - radio), (cx + radio * 0.8, cy), (cx, cy + radio), (cx - radio * 0.8, cy)]
        pygame.draw.polygon(pantalla, (40, 70, 130) if cat == HABILIDAD else (110, 40, 100), pts)
        pygame.draw.polygon(pantalla, color, pts, 3)
        pulso = 0.5 + 0.5 * math.sin(tiempo * 5)
        pygame.draw.circle(pantalla, (200, 230, 255), (cx, cy), int(radio * (0.25 + 0.1 * pulso)))
    else:
        pygame.draw.circle(pantalla, (60, 64, 76), centro, radio, 3)
        d = int(radio * 0.5)
        pygame.draw.line(pantalla, COLOR_NADA, (cx - d, cy - d), (cx + d, cy + d), 3)
        pygame.draw.line(pantalla, COLOR_NADA, (cx - d, cy + d), (cx + d, cy - d), 3)


# ---------------------------------------------------------------- Ruleta del orbe Gacha (sobre el mundo)
DURACION_RESULTADO_MUNDO = 2.5   # s que se ve el premio tras pararse la ruleta
ANCHO_RULETA_MUNDO = 560


def ruleta_mundo_terminada(ruleta, tiempo):
    return tiempo - ruleta["t0"] >= DURACION_RULETA + DURACION_RESULTADO_MUNDO


def dibujar_ruleta_mundo(pantalla, area, ruleta, tiempo, fuentes):
    """Ventana pequeña arriba del mundo con la ruleta de anillos del orbe Gacha. No bloquea:
    el juego sigue y el premio ya está aplicado."""
    ancho = min(ANCHO_RULETA_MUNDO, area.width - 40)
    caja = pygame.Rect(0, 0, ancho, 168)
    caja.midtop = (area.centerx, area.y + 112)
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    pygame.draw.rect(fondo, (16, 14, 26, 225), fondo.get_rect(), border_radius=12)
    pantalla.blit(fondo, caja.topleft)
    pulso = 0.5 + 0.5 * math.sin(tiempo * 5)
    pygame.draw.rect(pantalla, (int(200 + 55 * pulso), 170, 60), caja, width=2, border_radius=12)
    titulo = fuentes["hab_nom"].render("Orbe Gacha · ruleta de anillos", True, (255, 215, 90))
    pantalla.blit(titulo, titulo.get_rect(midtop=(caja.centerx, caja.y + 8)))
    # tira
    r_rul = pygame.Rect(caja.x + 12, caja.y + 32, caja.width - 24, 92)
    pygame.draw.rect(pantalla, (10, 10, 16), r_rul, border_radius=8)
    prog = progreso_ruleta(ruleta, tiempo)
    distancia = (ruleta["indice"] + 0.5 + ruleta["desfase"] * 0.5) * ANCHO_CASILLA - r_rul.width / 2
    desplazado = distancia * prog
    clip = pantalla.get_clip()
    pantalla.set_clip(r_rul.clip(clip) if clip else r_rul)
    girando = ruleta_girando(ruleta, tiempo)
    for i, cas in enumerate(ruleta["casillas"]):
        cx = r_rul.x + i * ANCHO_CASILLA - desplazado
        if cx + ANCHO_CASILLA < r_rul.x or cx > r_rul.right:
            continue
        rc = pygame.Rect(int(cx) + 4, r_rul.y + 6, ANCHO_CASILLA - 8, r_rul.height - 12)
        premio = not girando and i == ruleta["indice"]
        pygame.draw.rect(pantalla, (52, 46, 24) if premio else (30, 34, 46), rc, border_radius=8)
        pygame.draw.rect(pantalla, cas["color"], rc, width=3 if premio else 2, border_radius=8)
        dibujar_icono(pantalla, cas, (rc.centerx, rc.centery - 8), 18, tiempo)
        et = fuentes["hab_mini"].render(TL.NOMBRE_RAREZA.get(cas.get("rareza"), ""), True, cas["color"])
        pantalla.blit(et, et.get_rect(center=(rc.centerx, rc.bottom - 10)))
    pantalla.set_clip(clip)
    cxm = r_rul.centerx
    pygame.draw.polygon(pantalla, (255, 215, 0), [(cxm - 8, r_rul.y), (cxm + 8, r_rul.y), (cxm, r_rul.y + 10)])
    pygame.draw.polygon(pantalla, (255, 215, 0), [(cxm - 8, r_rul.bottom), (cxm + 8, r_rul.bottom), (cxm, r_rul.bottom - 10)])
    # premio
    if girando:
        txt, col = "Girando" + "." * (1 + int(tiempo * 3) % 3), (180, 186, 200)
    else:
        res = ruleta["resultado"]
        txt, col = res["texto"], res["color"]
    sup = fuentes["hab_det"].render(txt, True, col)
    pantalla.blit(sup, sup.get_rect(midtop=(caja.centerx, r_rul.bottom + 10)))
