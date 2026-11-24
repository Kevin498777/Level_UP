"""
Gacha de Level_UP (fase 3): una tirada cuesta 30 monedas y da una herramienta, una habilidad,
un anillo, un Tótem de vida o nada. Lo que ya no se puede dar (todas las herramientas o
habilidades, un anillo al máximo, 5 tótems) devuelve 25 monedas.

El premio se aplica al momento de tirar (la ruleta del inventario solo lo muestra), así que
cerrar el inventario o que te ataquen durante la animación no hace perder nada.
"""
import math
import random
import pygame
import talismanes as TL

COSTO_TIRADA = 30
DEVOLUCION = TL.DEVOLUCION_REPETIDO      # 25 monedas

HERRAMIENTA, HABILIDAD, ANILLO, TOTEM, NADA = "herramienta", "habilidad", "anillo", "totem", "nada"
PROBABILIDADES = {HERRAMIENTA: 0.25, HABILIDAD: 0.15, ANILLO: 0.45, TOTEM: 0.10, NADA: 0.05}
NOMBRE_CATEGORIA = {HERRAMIENTA: "Herramienta", HABILIDAD: "Habilidad", ANILLO: "Anillo",
                    TOTEM: "Tótem de vida", NADA: "Nada"}

COLOR_HERRAMIENTA = (255, 200, 120)
COLOR_HABILIDAD = (130, 190, 255)
COLOR_NADA = (120, 126, 140)


def _sortear(rng, tabla):
    r, acum = rng.random(), 0.0
    for clave, prob in tabla.items():
        acum += prob
        if r < acum:
            return clave
    return list(tabla)[-1]


def _dar_anillo(jugador, rng, res):
    """Sortea la rareza y un anillo de esa rareza y se lo da al jugador (rellena 'res')."""
    rareza = _sortear(rng, TL.PROB_RAREZA)
    id_anillo = rng.choice(TL.anillos_de_rareza(rareza))
    resultado = jugador.talismanes.agregar_anillo(id_anillo)
    nombre = TL.ANILLOS[id_anillo]["nombre"]
    res.update(categoria=ANILLO, id=id_anillo, rareza=rareza, color=TL.COLOR_RAREZA[rareza])
    if resultado == "maximo":
        res.update(texto=f"{nombre} (ya al máximo)", devolucion=DEVOLUCION)
    elif resultado == "nuevo":
        res["texto"] = f"{nombre} ({TL.NOMBRE_RAREZA[rareza]}) nuevo"
    else:
        res["texto"] = f"{nombre} sube a Nv {jugador.talismanes.anillos[id_anillo]}"
    jugador.recalcular_talismanes()       # por si ese anillo estaba equipado


def tirar_anillo(jugador, rng=random):
    """Ruleta gratis solo de anillos (orbe Gacha de la cueva del oso). Misma rareza que el
    Gacha; si el anillo ya está al máximo devuelve 25 monedas."""
    res = {"categoria": ANILLO, "id": None, "texto": "", "color": COLOR_NADA, "rareza": None, "devolucion": 0,
           "solo_anillos": True}
    _dar_anillo(jugador, rng, res)
    if res["devolucion"]:
        jugador.monedas += res["devolucion"]
        res["texto"] += f" · +{res['devolucion']} monedas"
    return res


def tirar(jugador, rng=random):
    """Hace una tirada. Devuelve None si no hay monedas suficientes; si no, el premio:
    {categoria, id, texto, color, rareza, devolucion} (ya aplicado al jugador)."""
    if jugador.monedas < COSTO_TIRADA:
        return None
    jugador.monedas -= COSTO_TIRADA
    categoria = _sortear(rng, PROBABILIDADES)
    res = {"categoria": categoria, "id": None, "texto": "", "color": COLOR_NADA, "rareza": None, "devolucion": 0}

    if categoria == HERRAMIENTA:
        faltan = jugador.herramientas_faltantes()
        if faltan:
            nombre = rng.choice(faltan)
            jugador.agregar_herramienta(nombre)
            res.update(id=nombre, texto=f"Herramienta nueva: {nombre}", color=COLOR_HERRAMIENTA)
        else:
            res.update(texto="Ya tienes las 6 herramientas", devolucion=DEVOLUCION, color=COLOR_HERRAMIENTA)
    elif categoria == HABILIDAD:
        faltan = jugador.habilidades_faltantes()
        if faltan:
            nombre = rng.choice(faltan)
            jugador.agregar_habilidad(nombre)
            res.update(id=nombre, texto=f"Habilidad nueva: {nombre}", color=COLOR_HABILIDAD)
        else:
            res.update(texto="Ya tienes todas las habilidades", devolucion=DEVOLUCION, color=COLOR_HABILIDAD)
    elif categoria == ANILLO:
        _dar_anillo(jugador, rng, res)
    elif categoria == TOTEM:
        resultado = jugador.talismanes.agregar_totem()
        res.update(id=TL.TOTEM, color=TL.COLOR_TOTEM)
        if resultado == "maximo":
            res.update(texto=f"Tótem de vida (ya tienes {TL.TOTEM_MAX})", devolucion=DEVOLUCION)
        else:
            res["texto"] = f"Tótem de vida (x{jugador.talismanes.totems})"
    else:
        res["texto"] = "Nada... suerte para la próxima"

    if res["devolucion"]:
        jugador.monedas += res["devolucion"]
        res["texto"] += f" · +{res['devolucion']} monedas"
    return res


# ---------------------------------------------------------------- Ruleta (animación)
DURACION_RULETA = 2.6          # s que gira la ruleta hasta pararse en el premio
ANCHO_CASILLA = 96
CASILLAS_ANTES = 38            # casillas de relleno antes del premio (lo que "gira")


def casilla_aleatoria(rng=random, solo_anillos=False):
    """Casilla de relleno para la ruleta (solo visual), con la misma proporción que el Gacha
    (o solo anillos, para la ruleta del orbe Gacha)."""
    cat = ANILLO if solo_anillos else _sortear(rng, PROBABILIDADES)
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
    elif cat == HABILIDAD:
        # rombo mágico con brillo
        pts = [(cx, cy - radio), (cx + radio * 0.8, cy), (cx, cy + radio), (cx - radio * 0.8, cy)]
        pygame.draw.polygon(pantalla, (40, 70, 130), pts)
        pygame.draw.polygon(pantalla, COLOR_HABILIDAD, pts, 3)
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
