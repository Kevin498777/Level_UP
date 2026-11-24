"""
Inventario del personaje ([I]): ventana superpuesta al mundo con el nivel y la XP, las
monedas, los puntos de mejora, las estadísticas, la herramienta y las 3 habilidades elegidas.

El inventario NO pausa el juego: el mundo sigue en marcha detrás (se puede morir con él
abierto). Se cierra con [I] o con la X. Sus botones [+] gastan puntos igual que los paneles.
"""
import math
import pygame
from habilidades import resumen_habilidad, dibujar_marco_potenciado, COLOR_POTENCIADA_TEXTO
import talismanes as TL
from personaje import PUNTOS_MEJORA_POR_NIVEL, REGEN_ENERGIA_POR_PUNTO, REGEN_ENERGIA_TOPE, NIVEL_MAXIMO

# Medidas y colores del inventario
ANCHO_INVENTARIO = 820
ALTO_INVENTARIO = 580
MARGEN_INVENTARIO = 20          # separación mínima con el borde del área del mundo
ALFA_VELO_INVENTARIO = 110      # oscurecido del mundo detrás (sigue viéndose)
VIDA_BAJA_AVISO = 0.30          # por debajo de este % de vida el borde parpadea en rojo
DURACION_MENSAJE = 2.5          # s que se ve un aviso (p. ej. "no puedes equipar...")
PESTANAS = (("personaje", "Personaje"), ("equipo", "Equipo"), ("talismanes", "Talismanes"), ("gacha", "Gacha"))
HISTORIAL_GACHA = 8             # tiradas que recuerda el historial

COLOR_FONDO = (18, 21, 29)
COLOR_TARJETA = (27, 31, 42)
COLOR_TARJETA_HOVER = (34, 40, 55)
COLOR_BORDE = (55, 66, 88)
COLOR_BORDE_HOVER = (120, 160, 230)
COLOR_TITULO = (255, 215, 0)
COLOR_TEXTO = (220, 226, 238)
COLOR_TEXTO_SUAVE = (150, 160, 182)
COLOR_XP = (120, 200, 255)
COLOR_MAX = (255, 215, 120)
COLOR_MONEDA = (245, 200, 70)
COLOR_MONEDA_BORDE = (180, 130, 30)
COLOR_PUNTOS = (120, 255, 150)
COLOR_MAS_FONDO = (34, 78, 44)
COLOR_MAS_BORDE = (100, 230, 130)

# Explicación de cada estadística (se muestra al pasar el ratón)
EXPLICACION_STATS = {
    "vida": "Vida: puntos de vida. Se recupera con los orbes de los frutales, el orbe de la cueva del oso y Regeneración Inversa. +2 por punto.",
    "fuerza": "Daño (Fuerza): base del golpe del arma. Burst de Fuerza la sube un rato. +0.2 por punto.",
    "velocidad": "Velocidad: cuánto te desplazas. La bajan el arma desenfundada, el agua y el autoapuntado; Destello la sube. +0.1 por punto.",
    "cadencia": "Cadencia: golpes por segundo extra sobre la cadencia de tu arma. +0.1 por punto.",
    "energia": "Energía: lo que gastan las habilidades. Se regenera +1 cada 3 s quieto y +1 cada 6 s en movimiento. +5 por punto.",
    "escudo": "Escudo físico: absorbe daño de armas, mordidas y garras. Se regenera +1/s tras 10 s sin daño físico. +5 hasta 15, luego +2.",
    "escudo_magico": "Escudo mágico: absorbe daño de habilidades. Se regenera +1/s tras 10 s sin daño mágico. +5 hasta 15, luego +2.",
    "regen_energia": (f"Regen de energía: acelera la regeneración de energía. +{REGEN_ENERGIA_POR_PUNTO * 100:.0f}% por punto "
                      f"(hasta +{REGEN_ENERGIA_TOPE * 100:.0f}%). Se duplica en el agua y se cuadruplica en la zona profunda del lago."),
}


def _texto(pantalla, fuente, texto, color, pos, centro=False, derecha=False):
    sup = fuente.render(str(texto), True, color)
    if centro:
        rect = sup.get_rect(center=pos)
    elif derecha:
        rect = sup.get_rect(topright=pos)
    else:
        rect = sup.get_rect(topleft=pos)
    pantalla.blit(sup, rect)
    return rect


def _tarjeta(pantalla, rect, hover, borde=None, radio=8):
    pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER if hover else COLOR_TARJETA, rect, border_radius=radio)
    pygame.draw.rect(pantalla, COLOR_BORDE_HOVER if hover else (borde or COLOR_BORDE), rect, width=1 if not hover else 2,
                     border_radius=radio)


def _barra(pantalla, x, y, ancho, alto, prog, color, fondo=(40, 45, 58)):
    pygame.draw.rect(pantalla, fondo, (x, y, ancho, alto), border_radius=alto // 2)
    prog = max(0.0, min(1.0, prog))
    if prog > 0:
        pygame.draw.rect(pantalla, color, (x, y, max(alto, int(ancho * prog)), alto), border_radius=alto // 2)


def _boton_mas(pantalla, fuente, x, y, botones, clave, tam=18):
    rect = pygame.Rect(x, y, tam, tam)
    hover = rect.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(pantalla, (46, 104, 60) if hover else COLOR_MAS_FONDO, rect, border_radius=4)
    pygame.draw.rect(pantalla, COLOR_MAS_BORDE, rect, width=1, border_radius=4)
    _texto(pantalla, fuente, "+", (150, 255, 180), rect.center, centro=True)
    botones[clave] = rect
    return rect


def _moneda(pantalla, centro, r):
    pygame.draw.circle(pantalla, COLOR_MONEDA_BORDE, centro, r)
    pygame.draw.circle(pantalla, COLOR_MONEDA, centro, r - 2)
    pygame.draw.circle(pantalla, COLOR_MONEDA_BORDE, centro, max(2, r - 6), 1)


def _envolver(fuente, texto, ancho):
    palabras, lineas, linea = texto.split(), [], ""
    for p in palabras:
        prueba = (linea + " " + p).strip()
        if fuente.size(prueba)[0] <= ancho:
            linea = prueba
        else:
            if linea:
                lineas.append(linea)
            linea = p
    if linea:
        lineas.append(linea)
    return lineas


def rect_inventario(area):
    """Rectángulo del inventario centrado en el área del mundo."""
    ancho = min(ANCHO_INVENTARIO, area.width - MARGEN_INVENTARIO * 2)
    alto = min(ALTO_INVENTARIO, area.height - MARGEN_INVENTARIO * 2)
    rect = pygame.Rect(0, 0, ancho, alto)
    rect.center = area.center
    return rect


def nuevo_estado_inventario():
    """Estado de la ventana: pestaña abierta y último aviso (texto, momento, es_error)."""
    return {"pestana": "personaje", "mensaje": None}


def manejar_clic_inventario(clave, jugador, estado, tiempo):
    """Clics propios del inventario (claves que empiezan por '__inv__'). True si lo manejó."""
    if not clave.startswith("__inv__"):
        return False
    partes = clave.split("__")          # ['', 'inv', accion, arg]
    accion = partes[2]
    arg = partes[3] if len(partes) > 3 else ""
    if accion == "tab":
        estado["pestana"] = arg
    elif accion == "tirar":
        import gacha as G
        if G.ruleta_girando(estado.get("ruleta"), tiempo):
            return True
        res = G.tirar(jugador)
        if res is None:
            estado["mensaje"] = (f"Necesitas {G.costo_tirada(jugador)} monedas para tirar", tiempo, True)
        else:
            estado["ruleta"] = G.nueva_ruleta(res, tiempo)
            estado["tiradas"] = estado.get("tiradas", 0) + 1
            estado.setdefault("historial", []).insert(0, res)
            del estado["historial"][HISTORIAL_GACHA:]
    elif accion == "equipar":
        ok, motivo = jugador.talismanes.equipar(arg)
        if ok:
            jugador.recalcular_talismanes()
            estado["mensaje"] = (f"{TL.nombre_objeto(arg)} equipado", tiempo, False)
        else:
            estado["mensaje"] = (motivo, tiempo, True)
    elif accion == "herr":
        herr = jugador.coleccion_herramientas[int(arg)]
        if jugador.equipar_herramienta(herr):
            estado["mensaje"] = (f"Ahora llevas {herr.nombre} (guardada: sácala con [1])", tiempo, False)
    elif accion == "hab":
        hab = jugador.coleccion_habilidades[int(arg)]
        hueco = int(partes[4])
        if jugador.equipar_habilidad(hab, hueco):
            estado["mensaje"] = (f"{hab.nombre_mostrado} va ahora en [{hueco + 2}]", tiempo, False)
    elif accion == "quitar":
        hueco = int(arg)
        id_obj = jugador.talismanes.huecos[hueco]
        jugador.talismanes.quitar(hueco)
        jugador.recalcular_talismanes()
        if id_obj:
            estado["mensaje"] = (f"{TL.nombre_objeto(id_obj)} quitado", tiempo, False)
    return True


def dibujar_inventario(pantalla, area, jugador, fuentes, tiempo, estado=None):
    """Dibuja el inventario sobre el mundo. Devuelve los botones {clave: Rect}: las claves de
    mejora son las mismas que las de los paneles (stats, "__arma__", "__hab__N"), más
    "__cerrar_inv__" (la X) y "__inv_fondo__" (el resto de la ventana, para que un clic dentro
    no mueva al personaje)."""
    raton = pygame.mouse.get_pos()
    botones = {}
    descripcion = None
    f_titulo = fuentes["hab_contador"]
    f_sub = fuentes["hab_nom"]
    f_txt = fuentes["hab_det"]
    f_mini = fuentes["hab_mini"]
    f_grande = fuentes["contador"]

    # Velo: oscurece el mundo pero se sigue viendo (el juego no está en pausa)
    velo = pygame.Surface(area.size, pygame.SRCALPHA)
    velo.fill((0, 0, 0, ALFA_VELO_INVENTARIO))
    pantalla.blit(velo, area.topleft)

    caja = rect_inventario(area)
    pygame.draw.rect(pantalla, COLOR_FONDO, caja, border_radius=12)
    vida_baja = jugador.vida <= jugador.vida_max * VIDA_BAJA_AVISO
    if vida_baja:
        pulso = 0.5 + 0.5 * math.sin(tiempo * 8)
        borde = (int(150 + 100 * pulso), 50, 50)
    else:
        borde = (90, 110, 150)
    pygame.draw.rect(pantalla, borde, caja, width=2, border_radius=12)

    x0, y0 = caja.x + 18, caja.y + 14
    ancho_util = caja.width - 36

    # ---------------- Cabecera
    if estado is None:
        estado = nuevo_estado_inventario()
    _texto(pantalla, f_titulo, "INVENTARIO", COLOR_TITULO, (x0, y0))
    # Pestañas
    tx = x0 + 150
    for clave_p, nombre_p in PESTANAS:
        sup = f_sub.render(nombre_p, True, (255, 255, 255))
        r_tab = pygame.Rect(tx, y0, sup.get_width() + 24, 28)
        activa = estado["pestana"] == clave_p
        hover = r_tab.collidepoint(raton)
        pygame.draw.rect(pantalla, (48, 58, 82) if activa else ((36, 42, 58) if hover else (26, 30, 40)), r_tab,
                         border_radius=6)
        pygame.draw.rect(pantalla, COLOR_TITULO if activa else COLOR_BORDE, r_tab, width=1, border_radius=6)
        pantalla.blit(sup, sup.get_rect(center=r_tab.center))
        botones[f"__inv__tab__{clave_p}"] = r_tab
        tx = r_tab.right + 8
    aviso = "¡VIDA BAJA!" if vida_baja else "El mundo sigue en marcha"
    _texto(pantalla, f_mini, aviso, (255, 110, 110) if vida_baja else (130, 140, 160),
           (caja.right - 64, y0 + 9), derecha=True)
    rect_x = pygame.Rect(caja.right - 46, y0 - 2, 30, 30)
    hover_x = rect_x.collidepoint(raton)
    pygame.draw.rect(pantalla, (170, 55, 55) if hover_x else (60, 34, 40), rect_x, border_radius=6)
    pygame.draw.rect(pantalla, (230, 110, 110), rect_x, width=1, border_radius=6)
    c = rect_x.center
    pygame.draw.line(pantalla, (255, 235, 235), (c[0] - 7, c[1] - 7), (c[0] + 7, c[1] + 7), 3)
    pygame.draw.line(pantalla, (255, 235, 235), (c[0] - 7, c[1] + 7), (c[0] + 7, c[1] - 7), 3)
    botones["__cerrar_inv__"] = rect_x

    alto_desc = 62
    if estado["pestana"] == "gacha":
        import gacha as G
        descripcion = _pestana_gacha(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y0 + 44,
                                     ancho_util, caja.bottom - 14 - alto_desc - 10, estado)
        _caja_descripcion(pantalla, f_txt, pygame.Rect(x0, caja.bottom - 14 - alto_desc, ancho_util, alto_desc),
                          descripcion, estado, tiempo,
                          f"Gacha{' mejorado' if G.gacha_mejorado(jugador) else ''}: pulsa TIRAR para gastar {G.costo_tirada(jugador)} monedas. Lo que consigas va a las pestañas Equipo y "
                          "Talismanes. Cuidado: el mundo sigue en marcha.")
        botones["__inv_fondo__"] = caja
        return botones
    if estado["pestana"] == "equipo":
        descripcion = _pestana_equipo(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y0 + 44,
                                      ancho_util, caja.bottom - 14 - alto_desc - 10)
        _caja_descripcion(pantalla, f_txt, pygame.Rect(x0, caja.bottom - 14 - alto_desc, ancho_util, alto_desc),
                          descripcion, estado, tiempo,
                          "Elige qué herramienta llevar y qué habilidades van en [2] [3] [4]. "
                          "Cuidado: el mundo sigue en marcha mientras cambias.")
        botones["__inv_fondo__"] = caja
        return botones
    if estado["pestana"] == "talismanes":
        descripcion = _pestana_talismanes(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y0 + 44,
                                          ancho_util, caja.bottom - 14 - alto_desc - 10)
        _caja_descripcion(pantalla, f_txt, pygame.Rect(x0, caja.bottom - 14 - alto_desc, ancho_util, alto_desc),
                          descripcion, estado, tiempo,
                          "Pasa el ratón sobre un talismán para ver su efecto. Pulsa Equipar o Quitar. "
                          "Solo funcionan los equipados (3 huecos).")
        botones["__inv_fondo__"] = caja
        return botones

    # ---------------- Resumen: nivel + XP, monedas, puntos
    y = y0 + 44
    alto_res = 74
    ancho_nivel = int(ancho_util * 0.52)
    ancho_peq = (ancho_util - ancho_nivel - 20) // 2
    r_nivel = pygame.Rect(x0, y, ancho_nivel, alto_res)
    r_mon = pygame.Rect(r_nivel.right + 10, y, ancho_peq, alto_res)
    r_pts = pygame.Rect(r_mon.right + 10, y, ancho_peq, alto_res)

    h = r_nivel.collidepoint(raton)
    _tarjeta(pantalla, r_nivel, h)
    _texto(pantalla, f_mini, "NIVEL", COLOR_TEXTO_SUAVE, (r_nivel.x + 14, r_nivel.y + 10))
    _texto(pantalla, f_titulo, jugador.nivel, COLOR_MAX if jugador.xp_siguiente is None else COLOR_TEXTO,
           (r_nivel.x + 14, r_nivel.y + 28))
    bx = r_nivel.x + 70
    bw = r_nivel.width - 84
    if jugador.xp_siguiente is None:
        _texto(pantalla, f_txt, "XP: MÁX (nivel máximo)", COLOR_MAX, (bx, r_nivel.y + 14))
        _barra(pantalla, bx, r_nivel.y + 40, bw, 10, 1.0, COLOR_MAX)
    else:
        _texto(pantalla, f_txt, f"XP {jugador.xp:g} / {jugador.xp_siguiente}", COLOR_XP, (bx, r_nivel.y + 14))
        falta = round(jugador.xp_siguiente - jugador.xp, 2)
        _texto(pantalla, f_mini, f"faltan {falta:g} para el nivel {jugador.nivel + 1}", COLOR_TEXTO_SUAVE,
               (bx + bw, r_nivel.y + 16), derecha=True)
        _barra(pantalla, bx, r_nivel.y + 40, bw, 10, jugador.xp / jugador.xp_siguiente, COLOR_XP)
    if h:
        descripcion = (f"Nivel y experiencia: cazar animales da XP (tú o tus sombras). Cada nivel da {PUNTOS_MEJORA_POR_NIVEL} puntos de "
                       f"mejora; el sobrante de XP pasa al siguiente nivel. Máximo nivel {NIVEL_MAXIMO}.")

    h = r_mon.collidepoint(raton)
    _tarjeta(pantalla, r_mon, h)
    _texto(pantalla, f_mini, "MONEDAS", COLOR_TEXTO_SUAVE, (r_mon.x + 14, r_mon.y + 10))
    _moneda(pantalla, (r_mon.x + 26, r_mon.y + 46), 12)
    _texto(pantalla, f_titulo, jugador.monedas, COLOR_MONEDA, (r_mon.x + 46, r_mon.y + 32))
    if h:
        descripcion = ("Monedas: las sueltan los animales al cazarlos (más y con más probabilidad cuanto más "
                       "difíciles son). Por ahora no se gastan y se pierden al morir.")

    h = r_pts.collidepoint(raton)
    _tarjeta(pantalla, r_pts, h, borde=(70, 140, 90) if jugador.puntos_mejora > 0 else None)
    _texto(pantalla, f_mini, "PUNTOS DE MEJORA", COLOR_TEXTO_SUAVE, (r_pts.x + 14, r_pts.y + 10))
    _texto(pantalla, f_titulo, jugador.puntos_mejora,
           COLOR_PUNTOS if jugador.puntos_mejora > 0 else COLOR_TEXTO_SUAVE, (r_pts.x + 14, r_pts.y + 32))
    if h:
        descripcion = ("Puntos de mejora: recurso compartido. Una estadística o una habilidad cuestan 1 punto "
                       "(Regeneración Inversa y Paso 0: 2) y el arma 2 por nivel. Usa los botones [+].")

    # ---------------- Cuerpo: estadísticas (izquierda) | herramienta + habilidades (derecha)
    y_cuerpo = y + alto_res + 14
    alto_cuerpo = caja.bottom - 14 - alto_desc - 10 - y_cuerpo
    ancho_izq = int(ancho_util * 0.38)
    r_stats = pygame.Rect(x0, y_cuerpo, ancho_izq, alto_cuerpo)
    _tarjeta(pantalla, r_stats, False)
    _texto(pantalla, f_sub, "Estadísticas", COLOR_TEXTO, (r_stats.x + 14, r_stats.y + 10))

    pct_vel = int(round((jugador.velocidad / jugador.velocidad_base - 1.0) * 100)) if jugador.velocidad_base else 0
    filas = [
        ("vida", "Vida", f"{round(jugador.vida, 1):g} / {jugador.vida_max:g}", (255, 95, 95), jugador.vida / max(1, jugador.vida_max)),
        ("fuerza", "Daño", f"{jugador.fuerza:.2f}", (255, 140, 80), None),
        ("velocidad", "Velocidad", f"{jugador.velocidad:.2f}" + (f" ({pct_vel:+d}%)" if pct_vel else ""), (90, 220, 255), None),
        ("cadencia", "Cadencia", f"+{jugador.cadencia:.2f}/s", (255, 200, 120), None),
        ("energia", "Energía", f"{round(jugador.energia, 1):g} / {jugador.energia_max:g}", (180, 130, 255),
         jugador.energia / max(1, jugador.energia_max)),
        ("escudo", "Escudo", f"{jugador.escudo:.1f} / {jugador.escudo_max:.0f}", (120, 255, 150),
         jugador.escudo / jugador.escudo_max if jugador.escudo_max else 0),
        ("escudo_magico", "Escudo M.",
         "ANULADO" if jugador.anulacion_escudo_magico > 0 else f"{jugador.escudo_magico:.1f} / {jugador.escudo_magico_max:.0f}",
         (90, 200, 255), jugador.escudo_magico / jugador.escudo_magico_max if jugador.escudo_magico_max else 0),
        ("regen_energia", "Regen En.", f"+{jugador.bono_regen_energia * 100:.0f}%" + (" (máx)" if jugador.regen_energia_al_tope else ""),
         (150, 210, 255), None),
    ]
    alto_fila = max(30, (r_stats.height - 44) // len(filas))
    fy = r_stats.y + 40
    for clave, etiqueta, valor, color, prog in filas:
        r_fila = pygame.Rect(r_stats.x + 6, fy - 4, r_stats.width - 12, alto_fila - 2)
        if r_fila.collidepoint(raton):
            pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER, r_fila, border_radius=6)
            descripcion = EXPLICACION_STATS[clave]
        _texto(pantalla, f_txt, etiqueta, COLOR_TEXTO_SUAVE, (r_stats.x + 14, fy))
        derecha = r_stats.right - 14
        if jugador.puntos_mejora > 0:
            _boton_mas(pantalla, f_txt, derecha - 18, fy - 1, botones, clave)
            derecha -= 26
        _texto(pantalla, f_txt, valor, color, (derecha, fy), derecha=True)
        if prog is not None:
            _barra(pantalla, r_stats.x + 14, fy + 19, r_stats.width - 28, 4, prog, color)
        fy += alto_fila

    # Herramienta
    x_der = r_stats.right + 14
    ancho_der = caja.right - 18 - x_der
    arma = jugador.herramienta
    alto_arma = 88
    r_arma = pygame.Rect(x_der, y_cuerpo, ancho_der, alto_arma)
    h = r_arma.collidepoint(raton)
    _tarjeta(pantalla, r_arma, h, borde=(210, 80, 70) if arma and arma.roto else
             ((100, 255, 140) if arma and arma.activa else None))
    _texto(pantalla, f_mini, "HERRAMIENTA  [1]", COLOR_TEXTO_SUAVE, (r_arma.x + 14, r_arma.y + 8))
    if arma:
        _texto(pantalla, f_sub, arma.nombre, (255, 255, 255), (r_arma.x + 14, r_arma.y + 24))
        der = r_arma.right - 14
        if jugador.puntos_mejora >= 2 and (arma.roto or arma.nivel < arma.nivel_max):
            _boton_mas(pantalla, f_txt, der - 18, r_arma.y + 8, botones, "__arma__")
            der -= 26
        if arma.roto:
            _texto(pantalla, f_txt, "ROTA", (255, 90, 80), (der, r_arma.y + 8), derecha=True)
        else:
            _texto(pantalla, f_txt, f"Nv {arma.nivel}/{arma.nivel_max}",
                   COLOR_MAX if arma.nivel >= arma.nivel_max else (170, 205, 255), (der, r_arma.y + 8), derecha=True)
        estado_arma = "Rota" if arma.roto else ("Desenfundada" if arma.activa else "Guardada")
        if arma.es_escudo:
            linea = f"Bloqueo frontal 120° · Vel -{arma.debuff_velocidad * 100:.0f}% · {estado_arma}"
        elif hasattr(arma, "comprar_flechas"):
            linea = f"Flechas {arma.flechas}/{arma.capacidad_carcaj} · Daño máx {arma.calcular_dano(jugador):g} · {estado_arma}"
        else:
            debuff = arma.debuff_velocidad
            vel_txt = f"Vel {-debuff * 100:+.0f}%" if debuff else "Vel 0%"
            linea = (f"Daño {arma.calcular_dano(jugador):g} · Cad {arma.cadencia_efectiva(jugador):.2f}/s · "
                     f"{vel_txt} · {estado_arma}")
        _texto(pantalla, f_mini, linea, COLOR_TEXTO, (r_arma.x + 14, r_arma.y + 50))
        prog = arma.durabilidad / max(1, arma.durabilidad_max)
        col = (100, 220, 120) if prog > 0.5 else ((230, 200, 70) if prog > 0.2 else (230, 90, 70))
        _barra(pantalla, r_arma.x + 14, r_arma.y + 70, r_arma.width - 120, 6, 0 if arma.roto else prog, col)
        _texto(pantalla, f_mini, f"{arma.durabilidad:g}/{arma.durabilidad_max}", COLOR_TEXTO_SUAVE,
               (r_arma.right - 14, r_arma.y + 66), derecha=True)
        if h:
            descripcion = (f"{arma.nombre}: herramienta elegida. Sácala o guárdala con [1] y golpea con [Espacio]. "
                           f"Mejorarla cuesta 2 puntos por nivel (o la repara si está rota). Nivel máximo {arma.nivel_max}.")
    else:
        _texto(pantalla, f_sub, "Sin herramienta", COLOR_TEXTO_SUAVE, (r_arma.x + 14, r_arma.y + 28))

    # Habilidades equipadas (solo las elegidas)
    y_hab = r_arma.bottom + 10
    _texto(pantalla, f_mini, "HABILIDADES EQUIPADAS", COLOR_TEXTO_SUAVE, (x_der + 2, y_hab))
    y_hab += 18
    n = max(1, len(jugador.habilidades))
    alto_hab = min(86, (y_cuerpo + alto_cuerpo - y_hab - (n - 1) * 8) // n)
    for idx, hab in enumerate(jugador.habilidades):
        r = pygame.Rect(x_der, y_hab, ancho_der, alto_hab)
        h = r.collidepoint(raton)
        if hab.estado == "ACTIVA" or hab.estado == "INVOCADO":
            borde, col_est, txt_est = (0, 210, 255), (0, 220, 255), "ACTIVA"
        elif hab.estado == "COOLDOWN":
            borde, col_est = (230, 140, 40), (255, 165, 80)
            txt_est = f"RECARGA {max(0.0, hab.tiempo_restante_cooldown):.1f}s"
        else:
            borde, col_est, txt_est = None, (120, 255, 160), "LISTA"
        _tarjeta(pantalla, r, h, borde=borde)
        if hab.potenciada_activa:
            dibujar_marco_potenciado(pantalla, r, tiempo)
        # Tecla
        r_tecla = pygame.Rect(r.x + 12, r.y + 12, 28, 28)
        pygame.draw.rect(pantalla, (60, 52, 22), r_tecla, border_radius=6)
        pygame.draw.rect(pantalla, (255, 220, 80), r_tecla, width=1, border_radius=6)
        _texto(pantalla, f_sub, hab.tecla_str, (255, 220, 80), r_tecla.center, centro=True)
        _texto(pantalla, f_sub, hab.nombre_mostrado, COLOR_POTENCIADA_TEXTO if hab.potenciada_activa else (255, 255, 255),
               (r.x + 50, r.y + 9))
        der = r.right - 14
        if hab.escalable and hab.nivel < hab.nivel_max and jugador.puntos_mejora >= hab.costo_mejora:
            _boton_mas(pantalla, f_txt, der - 18, r.y + 10, botones, f"__hab__{idx}")
            der -= 26
        nivel_txt = f"Nv {hab.nivel}/{hab.nivel_max}" if hab.escalable else "Nv —"
        _texto(pantalla, f_txt, nivel_txt, COLOR_MAX if hab.escalable and hab.nivel >= hab.nivel_max else (170, 205, 255),
               (der, r.y + 10), derecha=True)
        costo = hab.obtener_costo_base(jugador) if hasattr(hab, "obtener_costo_base") else hab.costo_energia
        _texto(pantalla, f_mini, f"Costo {costo} En.", (200, 165, 255), (r.x + 50, r.y + 31))
        _texto(pantalla, f_mini, txt_est, col_est, (r.x + 150, r.y + 31))
        if alto_hab >= 70:
            _texto(pantalla, f_mini, resumen_habilidad(hab), COLOR_TEXTO, (r.x + 12, r.y + 50))
        if hab.estado == "COOLDOWN":
            _barra(pantalla, r.x + 12, r.bottom - 10, r.width - 24, 4,
                   1 - hab.tiempo_restante_cooldown / max(0.1, hab.duracion_cooldown), (255, 140, 50))
        if h:
            descripcion = f"{hab.nombre_mostrado} [{hab.tecla_str}]: {_descripcion_con_potenciada(hab)}"
        y_hab += alto_hab + 8

    # ---------------- Descripción (lo que hay bajo el ratón)
    _caja_descripcion(pantalla, f_txt, pygame.Rect(x0, caja.bottom - 14 - alto_desc, ancho_util, alto_desc),
                      descripcion, estado, tiempo,
                      "Pasa el ratón sobre una tarjeta para ver su descripción. Los [+] gastan puntos de mejora. "
                      "Cierra con [I] o con la X.")

    # El resto de la ventana absorbe los clics (no mueven al personaje). Va al final: los
    # botones de arriba tienen prioridad porque se recorren en orden de inserción.
    botones["__inv_fondo__"] = caja
    return botones


def _caja_descripcion(pantalla, fuente, r_desc, descripcion, estado, tiempo, texto_por_defecto):
    """Recuadro inferior: el último aviso (si es reciente) o lo que hay bajo el ratón."""
    pygame.draw.rect(pantalla, (23, 27, 37), r_desc, border_radius=8)
    pygame.draw.rect(pantalla, (45, 52, 70), r_desc, width=1, border_radius=8)
    color = COLOR_TEXTO
    msg = estado.get("mensaje")
    if msg and tiempo - msg[1] < DURACION_MENSAJE:
        descripcion = msg[0]
        color = (255, 120, 110) if msg[2] else (140, 240, 160)
    elif descripcion is None:
        descripcion = texto_por_defecto
        color = COLOR_TEXTO_SUAVE
    for i, linea in enumerate(_envolver(fuente, descripcion, r_desc.width - 24)[:3]):
        _texto(pantalla, fuente, linea, color, (r_desc.x + 12, r_desc.y + 6 + i * 17))


def _boton_texto(pantalla, fuente, rect, texto, activo, botones, clave, color=(100, 230, 130)):
    hover = activo and rect.collidepoint(pygame.mouse.get_pos())
    rojo = color[0] > color[1]
    if not activo:
        fondo = (36, 40, 50)
    elif rojo:
        fondo = (110, 44, 44) if hover else (72, 34, 36)
    else:
        fondo = (46, 104, 60) if hover else (34, 70, 44)
    pygame.draw.rect(pantalla, fondo, rect, border_radius=5)
    pygame.draw.rect(pantalla, color if activo else (70, 78, 92), rect, width=1, border_radius=5)
    _texto(pantalla, fuente, texto, (220, 255, 225) if activo else (120, 128, 140), rect.center, centro=True)
    if activo:
        botones[clave] = rect


def _descripcion_talisman(jugador, id_obj):
    col = jugador.talismanes
    if id_obj == TL.TOTEM:
        return (f"Tótem de vida (x{col.totems}/{TL.TOTEM_MAX}): ocupa un hueco con toda su pila. Si mueres con él "
                f"equipado, gastas uno, vuelves al centro con la vida llena y no pierdes nada.")
    d = TL.ANILLOS[id_obj]
    n = col.anillos[id_obj]
    sig = (f" Siguiente nivel: {TL.texto_efecto(id_obj, n + 1)}." if n < d["nivel_max"]
           else " Nivel máximo: si te sale otro, te devuelve monedas.")
    return (f"{d['nombre']} ({TL.NOMBRE_RAREZA[d['rareza']]}, Nv {n}/{d['nivel_max']}): "
            f"{TL.texto_efecto(id_obj, n)}.{sig} Se mejora consiguiendo otro igual.")


def _pestana_talismanes(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y, ancho, y_fin):
    """Huecos equipados arriba y la colección abajo. Devuelve la descripción bajo el ratón."""
    f_sub = fuentes["hab_nom"]
    f_txt = fuentes["hab_det"]
    f_mini = fuentes["hab_mini"]
    col = jugador.talismanes
    descripcion = None

    _texto(pantalla, f_sub, "Equipados", COLOR_TEXTO, (x0, y))
    _texto(pantalla, f_mini, "3 huecos · máx. 1 legendario y 2 épicos · solo dan efecto los equipados",
           COLOR_TEXTO_SUAVE, (x0 + 100, y + 4))
    y += 26
    ancho_hueco = (ancho - 2 * 12) // TL.HUECOS
    alto_hueco = 104
    for i, id_obj in enumerate(col.huecos):
        r = pygame.Rect(x0 + i * (ancho_hueco + 12), y, ancho_hueco, alto_hueco)
        hover = r.collidepoint(raton)
        if id_obj is None:
            pygame.draw.rect(pantalla, (22, 25, 33), r, border_radius=10)
            for k in range(0, r.width, 14):     # borde discontinuo
                pygame.draw.line(pantalla, (60, 68, 86), (r.x + k, r.y), (r.x + min(k + 7, r.width), r.y))
                pygame.draw.line(pantalla, (60, 68, 86), (r.x + k, r.bottom - 1), (r.x + min(k + 7, r.width), r.bottom - 1))
            pygame.draw.line(pantalla, (60, 68, 86), (r.x, r.y), (r.x, r.bottom))
            pygame.draw.line(pantalla, (60, 68, 86), (r.right - 1, r.y), (r.right - 1, r.bottom))
            _texto(pantalla, f_txt, f"Hueco {i + 1} libre", (110, 120, 140), r.center, centro=True)
            continue
        color = TL.color_objeto(id_obj)
        pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER if hover else COLOR_TARJETA, r, border_radius=10)
        pygame.draw.rect(pantalla, color, r, width=2, border_radius=10)
        TL.dibujar_objeto(pantalla, (r.x + 34, r.y + 40), 20, id_obj, tiempo)
        _texto(pantalla, f_txt, TL.nombre_objeto(id_obj), (255, 255, 255), (r.x + 64, r.y + 12))
        if id_obj == TL.TOTEM:
            sub = f"x{col.totems} / {TL.TOTEM_MAX}"
        else:
            d = TL.ANILLOS[id_obj]
            sub = f"{TL.NOMBRE_RAREZA[d['rareza']]} · Nv {col.anillos[id_obj]}/{d['nivel_max']}"
        _texto(pantalla, f_mini, sub, color, (r.x + 64, r.y + 32))
        lineas = _envolver(f_mini, TL.texto_efecto(id_obj, col.anillos.get(id_obj, 0)), r.width - 76)
        for k, linea in enumerate(lineas[:2]):
            _texto(pantalla, f_mini, linea, COLOR_TEXTO, (r.x + 64, r.y + 50 + k * 14))
        _boton_texto(pantalla, f_mini, pygame.Rect(r.right - 70, r.bottom - 26, 60, 20), "Quitar", True,
                     botones, f"__inv__quitar__{i}", color=(230, 120, 110))
        if hover:
            descripcion = _descripcion_talisman(jugador, id_obj)

    # Colección
    y += alto_hueco + 16
    objetos = sorted(col.anillos, key=lambda a: (list(TL.PROB_RAREZA).index(TL.ANILLOS[a]["rareza"]), a))
    if col.totems > 0:
        objetos = [TL.TOTEM] + objetos
    _texto(pantalla, f_sub, "Colección", COLOR_TEXTO, (x0, y))
    _texto(pantalla, f_mini, f"{len(col.anillos)} de {len(TL.ANILLOS)} anillos · tótems {col.totems}/{TL.TOTEM_MAX}",
           COLOR_TEXTO_SUAVE, (x0 + 100, y + 4))
    y += 26
    if not objetos:
        r = pygame.Rect(x0, y, ancho, 70)
        pygame.draw.rect(pantalla, (22, 25, 33), r, border_radius=10)
        _texto(pantalla, f_txt, "Aún no tienes talismanes. Se consiguen en el Gacha (próximamente).",
               COLOR_TEXTO_SUAVE, r.center, centro=True)
        return descripcion
    columnas = 4
    ancho_c = (ancho - (columnas - 1) * 10) // columnas
    alto_c = 60
    for idx, id_obj in enumerate(objetos):
        fila, colm = divmod(idx, columnas)
        r = pygame.Rect(x0 + colm * (ancho_c + 10), y + fila * (alto_c + 8), ancho_c, alto_c)
        if r.bottom > y_fin:
            break
        hover = r.collidepoint(raton)
        color = TL.color_objeto(id_obj)
        equipado = col.esta_equipado(id_obj)
        pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER if hover else COLOR_TARJETA, r, border_radius=8)
        pygame.draw.rect(pantalla, color if (hover or equipado) else COLOR_BORDE, r, width=2 if equipado else 1,
                         border_radius=8)
        TL.dibujar_objeto(pantalla, (r.x + 26, r.y + r.height // 2), 14, id_obj, tiempo)
        nombre = TL.nombre_objeto(id_obj).replace("Anillo de ", "")
        _texto(pantalla, f_txt, nombre[:1].upper() + nombre[1:], (255, 255, 255), (r.x + 46, r.y + 6))
        if id_obj == TL.TOTEM:
            sub = f"Tótem · x{col.totems}"
        else:
            d = TL.ANILLOS[id_obj]
            sub = f"{TL.NOMBRE_RAREZA[d['rareza']]} · Nv {col.anillos[id_obj]}/{d['nivel_max']}"
        _texto(pantalla, f_mini, sub, color, (r.x + 46, r.y + 24))
        rb = pygame.Rect(r.right - 72, r.bottom - 21, 64, 17)
        if equipado:
            _boton_texto(pantalla, f_mini, rb, "Equipado", False, botones, "")
        else:
            _boton_texto(pantalla, f_mini, rb, "Equipar", True, botones, f"__inv__equipar__{id_obj}")
        if hover:
            descripcion = _descripcion_talisman(jugador, id_obj)
    return descripcion


_DESCRIPCIONES_HAB = {}


def _descripcion_habilidad_clase(nombre):
    """Descripción de una habilidad que aún no tienes (se crea una vez y se guarda)."""
    if nombre not in _DESCRIPCIONES_HAB:
        from habilidades import crear_habilidad
        h = crear_habilidad(nombre)
        _DESCRIPCIONES_HAB[nombre] = h.descripcion if h else ""
    return _DESCRIPCIONES_HAB[nombre]


def _descripcion_con_potenciada(hab):
    """Descripcion de la habilidad mas el estado de su version potenciada, si la tiene desbloqueada."""
    if not hab.potenciada_desbloqueada:
        return hab.descripcion
    nombre_pot = hab.POTENCIADA["nombre"]
    if hab.potenciada_activa:
        return f"{hab.descripcion} POTENCIADA ({nombre_pot}): niveles hasta el {hab.nivel_max}, cada uno cuesta {hab.POTENCIADA['costo_mejora']} puntos."
    return f"{hab.descripcion} {nombre_pot} desbloqueada: súbela al Nv {hab._nivel_max_base} para usarla."


def _pestana_equipo(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y, ancho, y_fin):
    """Herramientas (izquierda) y habilidades (derecha): las conseguidas se pueden equipar,
    las que faltan se ven bloqueadas. Devuelve la descripción bajo el ratón."""
    from herramientas import HERRAMIENTAS_DISPONIBLES
    from habilidades import HABILIDADES_DISPONIBLES
    f_sub = fuentes["hab_nom"]
    f_txt = fuentes["hab_det"]
    f_mini = fuentes["hab_mini"]
    descripcion = None

    # ---- Herramientas
    ancho_izq = int(ancho * 0.32)
    _texto(pantalla, f_sub, "Herramientas", COLOR_TEXTO, (x0, y))
    _texto(pantalla, f_mini, f"{len(jugador.coleccion_herramientas)}/{len(HERRAMIENTAS_DISPONIBLES)}",
           COLOR_TEXTO_SUAVE, (x0 + ancho_izq, y + 4), derecha=True)
    yh = y + 26
    n = len(HERRAMIENTAS_DISPONIBLES)
    alto_h = min(58, (y_fin - yh - (n - 1) * 6) // n)
    for nombre in HERRAMIENTAS_DISPONIBLES:
        r = pygame.Rect(x0, yh, ancho_izq, alto_h)
        hover = r.collidepoint(raton)
        herr = next((h for h in jugador.coleccion_herramientas if h.nombre == nombre), None)
        equipada = herr is not None and herr is jugador.herramienta
        if herr is None:
            pygame.draw.rect(pantalla, (22, 25, 33), r, border_radius=8)
            pygame.draw.rect(pantalla, (44, 50, 64), r, width=1, border_radius=8)
            _texto(pantalla, f_txt, nombre, (95, 102, 118), (r.x + 12, r.y + 8))
            _texto(pantalla, f_mini, "Bloqueada · se consigue en el Gacha", (85, 92, 108), (r.x + 12, r.y + 28))
            if hover:
                descripcion = f"{nombre}: aún no la tienes. Se consigue en el Gacha (a nivel 1)."
        else:
            _tarjeta(pantalla, r, hover, borde=(255, 215, 0) if equipada else None)
            _texto(pantalla, f_txt, nombre, (255, 255, 255), (r.x + 12, r.y + 7))
            estado = "ROTA" if herr.roto else f"Nv {herr.nivel}/{herr.nivel_max}"
            _texto(pantalla, f_mini, f"{estado} · Dur. {herr.durabilidad:g}/{herr.durabilidad_max}",
                   (255, 90, 80) if herr.roto else (170, 205, 255), (r.x + 12, r.y + 27))
            rb = pygame.Rect(r.right - 78, r.y + (r.height - 20) // 2, 68, 20)
            if equipada:
                _boton_texto(pantalla, f_mini, rb, "Equipada", False, botones, "")
            else:
                idx = jugador.coleccion_herramientas.index(herr)
                _boton_texto(pantalla, f_mini, rb, "Equipar", True, botones, f"__inv__herr__{idx}")
            if hover:
                descripcion = (f"{nombre} (Nv {herr.nivel}/{herr.nivel_max}): "
                               + ("la llevas equipada. Sácala o guárdala con [1]." if equipada else
                                  "pulsa Equipar para llevarla. Conserva su nivel y su durabilidad; empieza guardada."))
        yh += alto_h + 6

    # ---- Habilidades
    xh = x0 + ancho_izq + 16
    ancho_der = x0 + ancho - xh
    _texto(pantalla, f_sub, "Habilidades", COLOR_TEXTO, (xh, y))
    equipadas = " · ".join(f"[{i + 2}] {h.nombre_mostrado if h else '—'}" for i, h in enumerate(jugador.huecos_habilidades))
    _texto(pantalla, f_mini, equipadas, (255, 220, 80), (xh + 104, y + 4))
    yk = y + 26
    nombres = list(HABILIDADES_DISPONIBLES)
    columnas = 3
    filas = (len(nombres) + columnas - 1) // columnas
    ancho_c = (ancho_der - (columnas - 1) * 8) // columnas
    alto_c = min(76, (y_fin - yk - (filas - 1) * 6) // filas)
    for k, nombre in enumerate(nombres):
        fila, col = divmod(k, columnas)
        r = pygame.Rect(xh + col * (ancho_c + 8), yk + fila * (alto_c + 6), ancho_c, alto_c)
        hover = r.collidepoint(raton)
        hab = next((h for h in jugador.coleccion_habilidades if h.nombre == nombre), None)
        if hab is None:
            pygame.draw.rect(pantalla, (22, 25, 33), r, border_radius=8)
            pygame.draw.rect(pantalla, (44, 50, 64), r, width=1, border_radius=8)
            _texto(pantalla, f_mini, nombre, (95, 102, 118), (r.x + 10, r.y + 8))
            _texto(pantalla, f_mini, "Bloqueada · Gacha", (85, 92, 108), (r.x + 10, r.y + 26))
            if hover:
                descripcion = f"{nombre} (aún no la tienes, se consigue en el Gacha): {_descripcion_habilidad_clase(nombre)}"
            continue
        hueco = jugador.huecos_habilidades.index(hab) if hab in jugador.huecos_habilidades else None
        _tarjeta(pantalla, r, hover, borde=(255, 215, 0) if hueco is not None else None)
        if hab.potenciada_activa:
            dibujar_marco_potenciado(pantalla, r, tiempo)
        _texto(pantalla, f_mini, hab.nombre_mostrado, COLOR_POTENCIADA_TEXTO if hab.potenciada_activa else (255, 255, 255),
               (r.x + 10, r.y + 6))
        if hab.potenciada_desbloqueada and not hab.potenciada_activa:
            _texto(pantalla, f_mini, f"Pot. al Nv {hab._nivel_max_base}", COLOR_POTENCIADA_TEXTO, (r.right - 10, r.y + 6), derecha=True)
        if hab.estado == "COOLDOWN":
            est, col_est = f"Recarga {max(0.0, hab.tiempo_restante_cooldown):.0f}s", (255, 165, 80)
        elif hab.estado in ("ACTIVA", "INVOCADO"):
            est, col_est = "Activa", (0, 220, 255)
        else:
            est, col_est = "Lista", (120, 255, 160)
        nivel_txt = f"Nv {hab.nivel}/{hab.nivel_max}" if hab.escalable else "Nv —"
        _texto(pantalla, f_mini, f"{nivel_txt} · ", (170, 205, 255), (r.x + 10, r.y + 22))
        _texto(pantalla, f_mini, est, col_est, (r.x + 10 + f_mini.size(f"{nivel_txt} · ")[0], r.y + 22))
        # Botones de hueco [2] [3] [4]: el actual va en dorado
        idx = jugador.coleccion_habilidades.index(hab)
        bx = r.x + 10
        by = r.bottom - 24
        for i in range(len(jugador.huecos_habilidades)):
            rb = pygame.Rect(bx + i * 30, by, 26, 18)
            if hueco == i:
                pygame.draw.rect(pantalla, (90, 74, 20), rb, border_radius=4)
                pygame.draw.rect(pantalla, (255, 215, 0), rb, width=1, border_radius=4)
                _texto(pantalla, f_mini, str(i + 2), (255, 230, 120), rb.center, centro=True)
            else:
                _boton_texto(pantalla, f_mini, rb, str(i + 2), True, botones, f"__inv__hab__{idx}__{i}",
                             color=(120, 160, 230))
        if hover:
            lugar = f"va en [{hueco + 2}]" if hueco is not None else "guardada (no está en ningún hueco)"
            descripcion = (f"{hab.nombre_mostrado} ({lugar}): {_descripcion_con_potenciada(hab)} Pulsa [2], [3] o [4] para ponerla en ese hueco; "
                           f"si ya estaba en otro, se intercambian.")
    return descripcion


def _pct(p):
    """0.4556 -> '45.6%', 0.05 -> '5%'."""
    txt = f"{p * 100:.1f}".rstrip("0").rstrip(".")
    return txt + "%"


def _filas_probabilidades(jugador):
    """Filas (categoria, titulo, detalle, descripcion) con las probabilidades reales de la
    proxima tirada para este jugador (cambian segun lo que ya tiene)."""
    import gacha as G
    prob = G.probabilidades(jugador)
    dev = f"+{G.DEVOLUCION} monedas"
    filas = []
    for cat, p in prob.items():
        titulo = f"{G.NOMBRE_CATEGORIA[cat]}  {_pct(p)}"
        agotada = cat != G.NADA and G.categoria_agotada(jugador, cat)
        if cat == G.HERRAMIENTA:
            n = len(jugador.herramientas_faltantes())
            detalle = f"te faltan {n}" if n else f"tienes todas: {dev}"
            desc = "Una herramienta que no tengas, a nivel 1."
        elif cat == G.HABILIDAD:
            n = len(jugador.habilidades_faltantes())
            detalle = f"te faltan {n}" if n else f"tienes todas: {dev}"
            desc = "Una habilidad que no tengas, a nivel 1 (se equipa sola si hay hueco libre)."
        elif cat == G.ANILLO:
            if agotada:
                detalle = f"todos al máximo: {dev}"
            elif G.legendario_disponible(jugador):
                detalle = f"legendario seguro en {G.tiradas_para_garantia(jugador)}"
            else:
                detalle = f"quedan {len(G.anillos_disponibles(jugador))} por subir"
            rz = G.probabilidades_rareza(jugador)
            desc = ("Solo salen anillos que aún pueden subir. Rareza: "
                    + " · ".join(f"{TL.NOMBRE_RAREZA[r]} {_pct(q)}" for r, q in rz.items())
                    + f". La tirada {G.GARANTIA_LEGENDARIO} sin legendario lo da seguro.")
        elif cat == G.TOTEM:
            detalle = f"tienes {jugador.talismanes.totems}/{TL.TOTEM_MAX}" + (f": {dev}" if agotada else "")
            desc = f"Se acumula hasta {TL.TOTEM_MAX}. Equipado, te salva de una muerte."
        elif cat == G.POTENCIADA:
            n = len(G.potenciadas_disponibles(jugador))
            detalle = f"te faltan {n}" if n else f"todas: {dev}"
            desc = (f"Desde el nivel {G.NIVEL_POTENCIADAS}: potencia una habilidad de tu colección "
                    "(su efecto llega en la siguiente fase).")
        else:
            detalle = "fija"
            desc = "No te toca nada."
        if agotada:
            desc += f" Ya no queda nada que darte: baja al {_pct(G.PROB_AGOTADA)} y devuelve {G.DEVOLUCION} monedas."
        filas.append((cat, titulo, detalle, desc))
    return filas


def _pestana_gacha(pantalla, jugador, fuentes, botones, raton, tiempo, x0, y, ancho, y_fin, estado):
    """Monedas y botón de tirar, la ruleta, el premio, las probabilidades y el historial."""
    import gacha as G
    f_titulo = fuentes["hab_contador"]
    f_sub = fuentes["hab_nom"]
    f_txt = fuentes["hab_det"]
    f_mini = fuentes["hab_mini"]
    descripcion = None
    ruleta = estado.get("ruleta")
    girando = G.ruleta_girando(ruleta, tiempo)

    # ---- Fila 1: monedas | botón tirar | tiradas
    alto1 = 62
    r_mon = pygame.Rect(x0, y, 200, alto1)
    _tarjeta(pantalla, r_mon, r_mon.collidepoint(raton))
    _texto(pantalla, f_mini, "TUS MONEDAS", COLOR_TEXTO_SUAVE, (r_mon.x + 14, r_mon.y + 8))
    _moneda(pantalla, (r_mon.x + 26, r_mon.y + 40), 11)
    _texto(pantalla, f_titulo, jugador.monedas, COLOR_MONEDA, (r_mon.x + 44, r_mon.y + 26))
    if r_mon.collidepoint(raton):
        descripcion = "Monedas: se consiguen cazando animales y se pierden al morir (salvo con un Tótem de vida)."

    r_tirar = pygame.Rect(r_mon.right + 14, y, ancho - 200 - 14 - 170 - 14, alto1)
    costo = G.costo_tirada(jugador)
    puede = jugador.monedas >= costo and not girando
    hover = r_tirar.collidepoint(raton)
    if puede:
        pulso = 0.5 + 0.5 * math.sin(tiempo * 4)
        fondo = (120, 84, 20) if hover else (int(86 + 20 * pulso), int(62 + 14 * pulso), 18)
        borde = (255, 215, 0)
    else:
        fondo, borde = (40, 42, 50), (80, 86, 100)
    pygame.draw.rect(pantalla, fondo, r_tirar, border_radius=10)
    pygame.draw.rect(pantalla, borde, r_tirar, width=2, border_radius=10)
    if girando:
        texto_boton = "Girando..."
    elif jugador.monedas < costo:
        texto_boton = f"Te faltan {costo - jugador.monedas} monedas"
    else:
        texto_boton = f"TIRAR{' MEJORADO' if G.gacha_mejorado(jugador) else ''}  ·  {costo} monedas"
    _texto(pantalla, f_titulo if puede else f_sub, texto_boton, (255, 240, 200) if puede else (130, 136, 150),
           r_tirar.center, centro=True)
    if puede:
        botones["__inv__tirar"] = r_tirar
    if hover:
        descripcion = (f"Una tirada cuesta {costo} monedas{' (Gacha mejorado: desde el nivel ' + str(G.NIVEL_POTENCIADAS) + ', con habilidades potenciadas)' if G.gacha_mejorado(jugador) else ''}. El premio se aplica al instante; "
                       "la ruleta solo lo muestra. El mundo sigue en marcha mientras giras.")

    r_tot = pygame.Rect(r_tirar.right + 14, y, 170, alto1)
    _tarjeta(pantalla, r_tot, False)
    _texto(pantalla, f_mini, "TIRADAS", COLOR_TEXTO_SUAVE, (r_tot.x + 14, r_tot.y + 8))
    _texto(pantalla, f_titulo, estado.get("tiradas", 0), COLOR_TEXTO, (r_tot.x + 14, r_tot.y + 26))

    # ---- Fila 2: ruleta
    y2 = y + alto1 + 10
    alto2 = 118
    r_rul = pygame.Rect(x0, y2, ancho, alto2)
    pygame.draw.rect(pantalla, (14, 16, 22), r_rul, border_radius=10)
    if ruleta is None:
        if "ruleta_quieta" not in estado:
            estado["ruleta_quieta"] = [G.casilla_aleatoria() for _ in range(ancho // G.ANCHO_CASILLA + 3)]
        casillas, desplazado = estado["ruleta_quieta"], (tiempo * 12) % G.ANCHO_CASILLA
        primera = -1
    else:
        casillas = ruleta["casillas"]
        prog = G.progreso_ruleta(ruleta, tiempo)
        distancia = (ruleta["indice"] + 0.5 + ruleta["desfase"] * 0.5) * G.ANCHO_CASILLA - ancho / 2
        desplazado = distancia * prog
        primera = 0
    clip_previo = pantalla.get_clip()
    pantalla.set_clip(r_rul.clip(clip_previo) if clip_previo else r_rul)
    for i, cas in enumerate(casillas):
        cx = r_rul.x + i * G.ANCHO_CASILLA - desplazado + (0 if primera == 0 else -G.ANCHO_CASILLA)
        if cx + G.ANCHO_CASILLA < r_rul.x or cx > r_rul.right:
            continue
        rc = pygame.Rect(int(cx) + 4, r_rul.y + 10, G.ANCHO_CASILLA - 8, alto2 - 20)
        es_premio = ruleta is not None and not girando and i == ruleta["indice"]
        pygame.draw.rect(pantalla, (30, 34, 46) if not es_premio else (52, 46, 24), rc, border_radius=8)
        pygame.draw.rect(pantalla, cas["color"], rc, width=2 if not es_premio else 3, border_radius=8)
        G.dibujar_icono(pantalla, cas, (rc.centerx, rc.centery - 8), 22, tiempo)
        etiqueta = (TL.NOMBRE_RAREZA[cas["rareza"]] if cas.get("rareza") else G.NOMBRE_CATEGORIA[cas["categoria"]])
        if cas["categoria"] == G.TOTEM:
            etiqueta = "Tótem"
        _texto(pantalla, f_mini, etiqueta, cas["color"], (rc.centerx, rc.bottom - 12), centro=True)
    pantalla.set_clip(clip_previo)
    # marcador central y bordes
    cxm = r_rul.centerx
    pygame.draw.polygon(pantalla, (255, 215, 0), [(cxm - 9, r_rul.y), (cxm + 9, r_rul.y), (cxm, r_rul.y + 12)])
    pygame.draw.polygon(pantalla, (255, 215, 0), [(cxm - 9, r_rul.bottom), (cxm + 9, r_rul.bottom), (cxm, r_rul.bottom - 12)])
    pygame.draw.rect(pantalla, (90, 100, 130), r_rul, width=2, border_radius=10)

    # ---- Fila 3: premio
    y3 = y2 + alto2 + 10
    alto3 = 58
    r_pre = pygame.Rect(x0, y3, ancho, alto3)
    if ruleta is None:
        pygame.draw.rect(pantalla, (22, 25, 33), r_pre, border_radius=10)
        _texto(pantalla, f_txt, "Pulsa TIRAR para girar la ruleta.", COLOR_TEXTO_SUAVE, r_pre.center, centro=True)
    elif girando:
        pygame.draw.rect(pantalla, (22, 25, 33), r_pre, border_radius=10)
        puntos = "." * (1 + int(tiempo * 3) % 3)
        _texto(pantalla, f_sub, "Girando" + puntos, COLOR_TEXTO_SUAVE, r_pre.center, centro=True)
    else:
        res = ruleta["resultado"]
        brillo = res.get("rareza") in (TL.EPICO, TL.LEGENDARIO)
        pulso = 0.5 + 0.5 * math.sin(tiempo * 6)
        fondo = (40, 34, 18) if brillo else (26, 30, 40)
        pygame.draw.rect(pantalla, fondo, r_pre, border_radius=10)
        ancho_borde = 2 + (int(2 * pulso) if brillo else 0)
        pygame.draw.rect(pantalla, res["color"], r_pre, width=ancho_borde, border_radius=10)
        G.dibujar_icono(pantalla, res, (r_pre.x + 34, r_pre.centery), 18, tiempo)
        titulo = "¡Nada!" if res["categoria"] == G.NADA else ("¡LEGENDARIO!" if res.get("rareza") == TL.LEGENDARIO
                                                                else ("¡Épico!" if res.get("rareza") == TL.EPICO
                                                                      else "¡Conseguiste!"))
        _texto(pantalla, f_sub, titulo, res["color"], (r_pre.x + 64, r_pre.y + 8))
        _texto(pantalla, f_txt, res["texto"], COLOR_TEXTO, (r_pre.x + 64, r_pre.y + 31))

    # ---- Fila 4: probabilidades | historial
    y4 = y3 + alto3 + 10
    alto4 = y_fin - y4
    ancho_p = int(ancho * 0.56)
    r_prob = pygame.Rect(x0, y4, ancho_p, alto4)
    _tarjeta(pantalla, r_prob, False)
    _texto(pantalla, f_mini, "PROBABILIDADES", COLOR_TEXTO_SUAVE, (r_prob.x + 12, r_prob.y + 8))
    filas = _filas_probabilidades(jugador)
    paso = max(18, (alto4 - 30) // len(filas))
    color_cat = {G.HERRAMIENTA: G.COLOR_HERRAMIENTA, G.HABILIDAD: G.COLOR_HABILIDAD, G.ANILLO: TL.COLOR_RAREZA[TL.EPICO],
                 G.TOTEM: TL.COLOR_TOTEM, G.POTENCIADA: G.COLOR_POTENCIADA, G.NADA: G.COLOR_NADA}
    for k, (cat, titulo, detalle, desc) in enumerate(filas):
        fy = r_prob.y + 28 + k * paso
        r_fila = pygame.Rect(r_prob.x + 4, fy - 2, r_prob.width - 8, paso)
        if r_fila.collidepoint(raton):
            pygame.draw.rect(pantalla, COLOR_TARJETA_HOVER, r_fila, border_radius=5)
            descripcion = desc
        pygame.draw.circle(pantalla, color_cat[cat], (r_prob.x + 18, fy + 8), 5)
        _texto(pantalla, f_txt, titulo, COLOR_TEXTO, (r_prob.x + 30, fy))
        _texto(pantalla, f_mini, detalle, COLOR_TEXTO_SUAVE, (r_prob.right - 12, fy + 2), derecha=True)

    r_his = pygame.Rect(r_prob.right + 12, y4, ancho - ancho_p - 12, alto4)
    _tarjeta(pantalla, r_his, False)
    _texto(pantalla, f_mini, "ÚLTIMAS TIRADAS", COLOR_TEXTO_SUAVE, (r_his.x + 12, r_his.y + 8))
    historial = estado.get("historial", [])
    if girando:
        historial = historial[1:]          # la que gira aún no se muestra
    if not historial:
        _texto(pantalla, f_mini, "Todavía no has tirado.", COLOR_TEXTO_SUAVE, (r_his.x + 12, r_his.y + 30))
    for k, res in enumerate(historial[:max(1, (alto4 - 30) // 18)]):
        _texto(pantalla, f_mini, "• " + res["texto"], res["color"], (r_his.x + 12, r_his.y + 28 + k * 18))
    return descripcion
