import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
import pygame
from habilidades import HABILIDADES_DISPONIBLES, crear_habilidad
from herramientas import HERRAMIENTAS_DISPONIBLES, crear_herramienta
from mundo import iniciar_mundo

# -----------------------------
# PALETA DE COLORES
# -----------------------------
COLORES = {
    "Azul": (0, 150, 255),
    "Rojo": (255, 60, 60),
    "Verde": (0, 210, 110),
    "Amarillo": (255, 220, 0),
    "Morado": (160, 80, 255),
    "Naranja": (255, 140, 30),
    "Cian": (0, 230, 240)
}

# -----------------------------
# DESCRIPCIONES Y COLORES DE LAS TARJETAS DE SELECCIÓN
# -----------------------------
DESC_HERRAMIENTAS = {
    "Espada Ligera": "Equilibrada. Daño Fza x2.2 a x3.0, debuff -17% a -5%, durabilidad 220-300. Máx nivel 5.",
    "Espada Larga": "Más larga y potente. Daño Fza x3.4 a x5.0, debuff -34% a -10%, durabilidad 190-230.",
    "Mandoble": "Pesada y lenta. Daño Fza x6.6 a x9.0, debuff -70% a -30%, durabilidad 148-180.",
    "Dagas Simples": "Dos dagas rápidas y pequeñas. Daño Fza x1.5 a x2.5; a nivel máximo dan +10% de velocidad. Durabilidad 150-400 compartida.",
    "Escudo": "No golpea, protege. Desenfundado bloquea entero lo que llega por delante (arco de 120°): golpes, proyectiles y mordidas, físicos o mágicos (no la Onda Sonora ni el Aura Eléctrica). Pierde de durabilidad el daño bloqueado menos un 20%-70% y repele al atacante con 40 de empuje (más que cualquier arma). Pasiva: tus escudos físico y mágico +15% a +30% (si no está roto). Debuff -34% a -10% desenfundado, durabilidad 100-300.",
    "Arco": "Daño físico a distancia. Mantén [Espacio] para cargar y suelta para disparar: 1s=100px/20% ... 5s=300px/100% del daño (menos de 1s no dispara; cargando -10% velocidad). Daño Fza x5 a x10, debuff -15% a -3%, durabilidad 100-150, empuje 25. Carcaj 10-30 flechas; [R] compra 10 por 10-30 En. (las que no caben se pierden)."
}

COLOR_HERRAMIENTAS = {
    "Espada Ligera": "#B0B5C0",
    "Espada Larga": "#9DA5B4",
    "Mandoble": "#7F8694",
    "Dagas Simples": "#C0C8D6",
    "Escudo": "#8FB0D6",
    "Arco": "#C49A6C"
}

DESC_HABILIDADES = {
    "Destello": "Buff de velocidad +52% a +90% por 10-18s. Recarga 5-1s con fatiga al acabar. Costo 10-40 En. Máx nivel 20.",
    "Burst de Fuerza": "Buff de fuerza +21% a +40% por 6-10s. Recarga 12-8s. Costo 15-35 En.",
    "Disparo Veloz": "Mágica. Esfera recta muy rápida (velocidad 14-35) con daño fijo 8-25 (no depende del arma). Costo 15-35 En. Recarga 4-2s.",
    "Onda Sonora": "Mágica. Anillos blancos en 360° desde donde la lanzas (1 onda de 10; 2 desde nv10: 10+20; 3 a nv20: 10+20+30), uno cada 0.8s. Radio 200-400. Atraviesan obstáculos sin destruir nada y solo afectan a enemigos. Ralentizan -5%/-10%/-20% (3s) según cuántas ondas golpeen. Agua->agua: daño y ralentización x2; si la onda cambia de medio: x0.5. Desde el agua viajan al doble de velocidad. Costo 10-30 En., recarga 10-30s.",
    "Cortar": "Mágica. Cuchilla recta que se detiene en el primer enemigo. Daño 5-40, velocidad 5-24, costo 15-53 En., recarga 2-10s (sube con el nivel). Si hace daño, anula el escudo mágico del enemigo 8s. Destruye una roca o arbusto al chocar, salvo el arbusto en el que estás (gigantes y arbustos grandes solo a nivel 20).",
    "Invocar Conejos": "Invoca 5 conejos que se reproducen (máx 50), más despacio cuantos más hay. Vida 5-20, velocidad 3-12.5, daño 0.1-7.7. Costo 80 En. Mantén la tecla para modo combate (clic derecho: persiguen al enemigo marcado; mantén y suelta de nuevo para volver a pasivo). 30s de recarga al morir todos.",
    "Carga de Fuego": "Pulsa para disparo rápido o mantén hasta 5s: daño base 20-39 x0.6 (sin carga) a x2.0 (5s) y más tamaño. Al golpear quema 1/s durante 2s (sin carga) a 7s (5s). Recarga 8s a 15s según la carga. Costo 15 al pulsar y se cobra cada segundo cargado (hasta 45 En.).",
    "Aura Electrica": "Aura que te sigue: +5% a +15% velocidad y 1 a 5 daño/s a enemigos cercanos. Autodaño 0.5/s (mágico, lo frena tu escudo mágico). Costo 20-58 En., CD 40-60s.",
    "Reforzamiento Mágico": "Campo de fuerza que bloquea daño físico y mágico. Dureza 200-500, duración 1-6s. Si se agota la dureza se rompe. Costo 25-50 En., CD 10-35s.",
    "Regeneración Inversa": "Mágica. Mantén pulsado para curar: +1 vida/-10 En. cada 2s hasta +6 vida/-40 En. cada 3s. Sin recarga. Máx nivel 10 (mejora: 2 puntos).",
    "Disparo Venenoso": "Mágica. Esfera verde que envenena al primer enemigo: 20 de daño en 20s (nv1) a 40 en 10s (nv20), daño mágico por segundo que frena el escudo mágico. El impacto no daña ni empuja; el veneno no se acumula (reinicia). Costo 20-45 En., CD 30-15s.",
    "Paso 0": "Potenciador mágico. Te vuelve invisible 3-8s: los enemigos no te detectan (no te miran ni te atacan), pero puedes recibir daño. Tus invocaciones y ataques sí se ven; tu arma se oculta salvo al golpear. Costo 30-60 En., CD 6-16s. Máx nivel 10 (mejora: 2 puntos).",
    "Sombra Araña": "Arte de las sombras. Invoca una araña (1 HP). Mantén la tecla (ojos rojos) y marca un punto con clic derecho; al llegar teje una telaraña de un solo uso que inmoviliza al primer enemigo que la pise (5s nv1 -> 20s nv20). Máx 3 telarañas; 5s de recarga. Costo 50->100 En. A nivel 20 la telaraña hace 1 daño mágico/s mientras inmoviliza (lo amortigua el escudo mágico).",
    "Invocar Lobos": "Mágica (invocación sombría). Invoca 3 lobos; máx nivel 20, cuesta 90 En. Vida 10-67, velocidad 10-18, daño 8-30. Golpes con 33% de desangrado (5 golpes de 1 vida cada 2s y -50% curación mientras dure). Mantén la tecla para modo combate (clic derecho: persiguen al enemigo marcado, la orden de ataque cuesta 5-10 En.; mantén y suelta de nuevo para volver a pasivo). 30s de recarga al morir todos.",
    "Golpe de Suerte": "Efecto aleatorio: Burst, Destello, Reforzamiento, Regeneración, Aura, Paso 0, energía o escudos al máximo, o Disparo Venenoso (¡te envenena a ti con la mitad del daño!) (7.78% c/u) o nada (30%; 5% a nv20). La habilidad otorgada dura 5-30s; no se relanza hasta que termine. Costo 15-50 En., CD 5-20s."
}

COLOR_HABILIDADES = {
    "Destello": "#56B6C2",
    "Burst de Fuerza": "#E5C07B",
    "Disparo Veloz": "#98C379",
    "Cortar": "#D7263D",
    "Onda Sonora": "#E8E8F0",
    "Invocar Conejos": "#8FD694",
    "Carga de Fuego": "#E06C4A",
    "Aura Electrica": "#5BC8FF",
    "Reforzamiento Mágico": "#87CEFA",
    "Regeneración Inversa": "#FF69B4",
    "Golpe de Suerte": "#F2C94C",
    "Paso 0": "#6E7BA8",
    "Disparo Venenoso": "#5ADC5A",
    "Invocar Lobos": "#8A8F98",
    "Sombra Araña": "#7A6CCF"
}

# -----------------------------
# CATEGORIAS DE HABILIDADES (para separar la seleccion por grupos)
# Cada entrada: (nombre de la categoria, color de la cabecera, [habilidades]).
# Para agregar habilidades nuevas, basta con sumarlas a su categoria (o crear otra).
# Cualquier habilidad de HABILIDADES_DISPONIBLES que no este aqui aparece en "Otras".
# -----------------------------
CATEGORIAS_HABILIDADES = [
    ("Artes de las Sombras", "#9B8CFF", ["Invocar Conejos", "Invocar Lobos", "Sombra Araña"]),
    ("Potenciadores",        "#E5C07B", ["Destello", "Burst de Fuerza", "Aura Electrica", "Paso 0"]),
    ("Ataque Mágico",        "#E06C4A", ["Disparo Veloz", "Carga de Fuego", "Cortar", "Onda Sonora", "Disparo Venenoso"]),
    ("Defensa y Soporte",    "#87CEFA", ["Reforzamiento Mágico", "Regeneración Inversa"]),
    ("Especiales",           "#F2C94C", ["Golpe de Suerte"]),
]

# -----------------------------
# ESTADÍSTICAS INICIALES (FIJAS)
# -----------------------------
def generar_estadisticas():
    # Estadísticas FIJAS de nivel 1 (sin aleatoriedad). Se mejoran con los puntos de nivel.
    return {
        "vida": 30,
        "fuerza": 2,
        "velocidad": 1,
        "energia": 100,
        "escudo": 0,
        "escudo_magico": 0,
        "tamano": 1
    }


# -----------------------------
# PERSONAJE DE PRUEBAS (NOMBRE CLAVE)
# -----------------------------
NOMBRE_CLAVE_PRUEBAS = "shadow498"

# shadow498 empieza con las estadisticas NORMALES de cualquier jugador (generar_estadisticas);
# sus ventajas de prueba son opcionales y se eligen con las casillas de "Opciones de pruebas":
# puntos de mejora extra para subir stats a gusto, y/o todo el inventario (ver mundo.py).


def es_personaje_pruebas(nombre):
    """True si el nombre es el nombre clave del personaje de pruebas."""
    return nombre.strip().lower() == NOMBRE_CLAVE_PRUEBAS


# -----------------------------
# DISEÑO ADAPTABLE DE LA PANTALLA DE CREACIÓN
# Las medidas base están pensadas para 1600x900 y se escalan según la pantalla. El contenido
# se reorganiza al ancho disponible (2 columnas o 1) y, si aun así no cabe en alto, aparece
# una barra de desplazamiento. El botón de comenzar queda fijo abajo, siempre visible.
# -----------------------------
RESOLUCION_BASE = (1600, 900)
ESCALA_MIN = 0.6
ESCALA_MAX = 1.6

COLOR_FONDO = "#1E2229"
COLOR_PANEL = "#282C34"
COLOR_CAJA = "#21252B"
COLOR_BORDE = "#3A3F4B"

TARJETA_ANCHO = 240          # px base de cada tarjeta (herramienta / habilidad)
TARJETA_ANCHO_MIN = 170      # px reales mínimos, para que los nombres quepan en pantallas pequeñas
TARJETA_ALTO = 46
SEPARACION = 6               # px base entre tarjetas
MARGEN = 24                  # px base del margen exterior
RELLENO_PANEL = 14           # px base de relleno dentro de cada panel
ANCHO_MIN_DOS_COLUMNAS = 1150   # px base: por debajo, todo va en una sola columna
TARJETAS_HERR_POR_FILA = 2      # en 2 columnas, el panel izquierdo lleva 2 tarjetas por fila


def calcular_escala(ancho, alto):
    """Factor de escala de la interfaz según el tamaño de pantalla (limitado)."""
    return max(ESCALA_MIN, min(ESCALA_MAX, min(ancho / RESOLUCION_BASE[0], alto / RESOLUCION_BASE[1])))


def construir_interfaz(ventana, ancho, alto, al_comenzar=None):
    """
    Construye la pantalla de creación dentro de `ventana`, escalada para una pantalla de
    `ancho` x `alto`. `al_comenzar(config)` recibe la configuración del mundo (por defecto
    cierra la ventana e inicia el mundo). Devuelve un dict con los elementos principales
    (lo usan también las pruebas de integración).
    """
    stats_actuales = generar_estadisticas()
    escala = calcular_escala(ancho, alto)

    def px(valor):
        return max(1, round(valor * escala))

    def fuente(tam, negrita=False):
        # Tamaño negativo = píxeles: así la fuente escala igual que el resto de medidas
        return ("Segoe UI", -max(9, px(tam)), "bold" if negrita else "normal")

    ancho_tarjeta = max(TARJETA_ANCHO_MIN, px(TARJETA_ANCHO))

    ventana.configure(bg=COLOR_FONDO)
    ventana.option_add("*TCombobox*Listbox.font", fuente(15))
    ventana.grid_rowconfigure(0, weight=1)
    ventana.grid_columnconfigure(0, weight=1)

    # -----------------------------
    # ÁREA DESPLAZABLE (todo menos el botón de comenzar)
    # -----------------------------
    canvas = tk.Canvas(ventana, bg=COLOR_FONDO, highlightthickness=0, bd=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    barra = tk.Scrollbar(ventana, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=barra.set)
    cuerpo = tk.Frame(canvas, bg=COLOR_FONDO)
    item_cuerpo = canvas.create_window(0, 0, window=cuerpo, anchor="nw")

    # Título
    cabecera = tk.Frame(cuerpo, bg=COLOR_FONDO)
    tk.Label(cabecera, text="CREACIÓN DE PERSONAJE", font=fuente(30, True),
             fg="#FFFFFF", bg=COLOR_FONDO).pack()
    tk.Label(cabecera, text="Elige nombre, color, herramienta y habilidades.  [ESC] sale de pantalla completa.",
             font=fuente(14), fg="#9DA5B4", bg=COLOR_FONDO).pack()

    def panel(padre, titulo, color_titulo):
        return tk.LabelFrame(padre, text=f"  {titulo}  ", font=fuente(17, True), fg=color_titulo,
                             bg=COLOR_PANEL, padx=px(RELLENO_PANEL), pady=px(10), relief="groove", bd=1)

    columna_izq = tk.Frame(cuerpo, bg=COLOR_FONDO)
    columna_der = tk.Frame(cuerpo, bg=COLOR_FONDO)

    # -----------------------------
    # NOMBRE Y COLOR
    # -----------------------------
    panel_pj = panel(columna_izq, "Personaje", "#E5C07B")
    panel_pj.pack(fill="x", pady=(0, px(10)))
    panel_pj.grid_columnconfigure(0, weight=1)

    tk.Label(panel_pj, text="Nombre del personaje:", font=fuente(15, True),
             fg="#E5C07B", bg=COLOR_PANEL).grid(row=0, column=0, sticky="w")
    nombre_var = tk.StringVar(value="Héroe")
    tk.Entry(panel_pj, textvariable=nombre_var, font=fuente(16),
             bg=COLOR_FONDO, fg="white", insertbackground="white", relief="flat",
             highlightthickness=1, highlightbackground="#4B5263",
             highlightcolor="#61AFEF").grid(row=1, column=0, sticky="ew", ipady=px(3))

    tk.Label(panel_pj, text="Color:", font=fuente(15, True),
             fg="#61AFEF", bg=COLOR_PANEL).grid(row=2, column=0, sticky="w", pady=(px(8), 0))
    color_var = tk.StringVar(value="Azul")
    ttk.Combobox(panel_pj, textvariable=color_var, values=list(COLORES.keys()),
                 state="readonly", font=fuente(15)).grid(row=3, column=0, sticky="ew")

    lado_vista = px(70)
    vista_canvas = tk.Canvas(panel_pj, width=lado_vista, height=lado_vista, bg=COLOR_FONDO,
                             highlightthickness=1, highlightbackground="#4B5263")
    vista_canvas.grid(row=0, column=1, rowspan=4, padx=(px(14), 0))

    def actualizar_vista_previa(*args):
        vista_canvas.delete("all")
        rgb = COLORES.get(color_var.get(), (0, 150, 255))
        color_hex = "#{:02x}{:02x}{:02x}".format(*rgb)
        c, r = lado_vista / 2, lado_vista * 0.29
        vista_canvas.create_oval(c - r, c - r, c + r, c + r, fill=color_hex, outline="white", width=2)
        vista_canvas.create_line(c + r + 4, c - r * 0.6, c + r + 4, c + r * 0.6, fill="#B0B5C0", width=2)

    color_var.trace_add("write", actualizar_vista_previa)

    # -----------------------------
    # ESTADO DE SELECCIÓN (tarjetas)
    # -----------------------------
    herramienta_var = tk.StringVar(value="Espada Ligera")
    hab_seleccionadas = ["Destello", "Burst de Fuerza", "Disparo Veloz"]  # orden = teclas [2],[3],[4]
    tarjetas_herr = {}
    tarjetas_hab = {}
    info_var = tk.StringVar(value="Pulsa el ? de una tarjeta para ver qué hace.")
    # Opciones del personaje de pruebas (solo se usan si el nombre es el nombre clave)
    opt_puntos_var = tk.BooleanVar(value=False)      # puntos de mejora extra (editar stats con el panel)
    opt_inventario_var = tk.BooleanVar(value=False)  # todas las armas y objetos en el inventario

    def _estilo_tarjeta(card, lbl, chk, color, seleccionado, numero=None):
        bg = "#30363F" if seleccionado else COLOR_PANEL
        card.config(bg=bg, highlightbackground=(color if seleccionado else COLOR_BORDE))
        lbl.config(bg=bg)
        if seleccionado:
            chk.config(text=(str(numero) if numero else "●"), bg=bg, fg=color)
        else:
            chk.config(text="○", bg=bg, fg="#555C6A")

    def _construir_tarjeta(parent, nombre, color_hex, on_select, on_info):
        card = tk.Frame(parent, bg=COLOR_PANEL, highlightthickness=2, highlightbackground=COLOR_BORDE,
                        width=ancho_tarjeta, height=px(TARJETA_ALTO), cursor="hand2")
        card.pack_propagate(False)
        chk = tk.Label(card, text="○", font=fuente(17, True), fg="#555C6A", bg=COLOR_PANEL, width=2)
        chk.pack(side="left", padx=(px(4), 0))
        info = tk.Label(card, text=" ? ", font=fuente(13, True), fg=COLOR_FONDO, bg="#8A93A6", cursor="hand2")
        info.pack(side="right", padx=px(6))
        # El nombre usa la fuente base y se reduce solo si no cabe (nombres largos)
        disponible = (ancho_tarjeta - 4 - chk.winfo_reqwidth() - px(4)
                      - info.winfo_reqwidth() - 2 * px(6) - 4 - 8)   # 8 = bordes y relleno del Label
        tam = px(15)
        while tam > 9 and tkfont.Font(family="Segoe UI", size=-tam, weight="bold").measure(nombre) > disponible:
            tam -= 1
        lbl = tk.Label(card, text=nombre, font=("Segoe UI", -tam, "bold"), fg=color_hex, bg=COLOR_PANEL, anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        for w in (card, chk, lbl):
            w.bind("<Button-1>", lambda e, n=nombre: on_select(n))
        info.bind("<Button-1>", lambda e, n=nombre: on_info(n))
        card.info = info
        return card, lbl, chk

    def refrescar():
        for nombre, (card, lbl, chk) in tarjetas_herr.items():
            _estilo_tarjeta(card, lbl, chk, COLOR_HERRAMIENTAS.get(nombre, "#B0B5C0"),
                            herramienta_var.get() == nombre)
        for nombre, (card, lbl, chk) in tarjetas_hab.items():
            sel = nombre in hab_seleccionadas
            num = (hab_seleccionadas.index(nombre) + 2) if sel else None  # slots [2],[3],[4]
            _estilo_tarjeta(card, lbl, chk, COLOR_HABILIDADES.get(nombre, "#98C379"), sel, num)

    def seleccionar_herramienta(nombre):
        herramienta_var.set(nombre)
        info_var.set(f"{nombre}: {DESC_HERRAMIENTAS.get(nombre, '')}")
        refrescar()

    def alternar_habilidad(nombre):
        if nombre in hab_seleccionadas:
            hab_seleccionadas.remove(nombre)
        else:
            if len(hab_seleccionadas) >= 3:
                info_var.set("Máximo 3 habilidades (teclas [2], [3] y [4]). Deselecciona una primero.")
                return
            hab_seleccionadas.append(nombre)
        info_var.set(f"{nombre}: {DESC_HABILIDADES.get(nombre, '')}")
        refrescar()

    def info_herramienta(nombre):
        info_var.set(f"{nombre}: {DESC_HERRAMIENTAS.get(nombre, '')}")

    def info_habilidad(nombre):
        info_var.set(f"{nombre}: {DESC_HABILIDADES.get(nombre, '')}")

    # -----------------------------
    # HERRAMIENTA
    # -----------------------------
    panel_herr = panel(columna_izq, "Herramienta principal  ·  tecla [1]", "#61AFEF")
    panel_herr.pack(fill="x", pady=(0, px(10)))
    for nombre in HERRAMIENTAS_DISPONIBLES:
        tarjetas_herr[nombre] = _construir_tarjeta(panel_herr, nombre,
                                                   COLOR_HERRAMIENTAS.get(nombre, "#B0B5C0"),
                                                   seleccionar_herramienta, info_herramienta)

    # -----------------------------
    # ESTADÍSTICAS INICIALES
    # -----------------------------
    panel_stats = panel(columna_izq, "Estadísticas iniciales (fijas · nivel 1)", "#ABB2BF")
    panel_stats.pack(fill="x")

    def renderizar_stats():
        for widget in panel_stats.winfo_children():
            widget.destroy()
        stats_vista = stats_actuales
        filas = [
            ("Vida:", stats_vista["vida"], "#E06C75"),
            ("Fuerza:", stats_vista["fuerza"], "#D19A66"),
            ("Velocidad:", stats_vista["velocidad"], "#56B6C2"),
            ("Energía:", stats_vista["energia"], "#C678DD"),
            ("Escudo:", stats_vista["escudo"], "#98C379"),
            ("Escudo M.:", stats_vista["escudo_magico"], "#56B6C2"),
            ("Tamaño:", stats_vista["tamano"], "#E5C07B")
        ]
        mitad = (len(filas) + 1) // 2
        for idx, (etiqueta, valor, color_destaque) in enumerate(filas):
            col = 0 if idx < mitad else 2
            fila = idx if idx < mitad else idx - mitad
            tk.Label(panel_stats, text=etiqueta, font=fuente(14, True),
                     fg="#ABB2BF", bg=COLOR_PANEL).grid(row=fila, column=col, sticky="w", pady=px(2), padx=(0, px(4)))
            tk.Label(panel_stats, text=str(valor), font=fuente(14, True),
                     fg=color_destaque, bg=COLOR_FONDO, width=6, relief="solid",
                     bd=1).grid(row=fila, column=col + 1, sticky="w", pady=px(2), padx=(0, px(20)))

    # -----------------------------
    # OPCIONES DEL PERSONAJE DE PRUEBAS (solo visibles al escribir el nombre clave)
    # -----------------------------
    panel_pruebas = panel(columna_izq, f"Opciones de pruebas  ·  {NOMBRE_CLAVE_PRUEBAS}", "#E06C75")

    chk_puntos = tk.Checkbutton(
        panel_pruebas, text="Puntos de mejora extra (editar stats con el panel: botones + o [L])",
        variable=opt_puntos_var, font=fuente(13, True), fg="#CDD2DE", bg=COLOR_PANEL,
        activebackground=COLOR_PANEL, activeforeground="#FFFFFF", selectcolor=COLOR_FONDO,
        anchor="w", justify="left", wraplength=px(TARJETA_ANCHO) * 2)
    chk_puntos.pack(fill="x", anchor="w", pady=px(2))

    chk_inv = tk.Checkbutton(
        panel_pruebas, text="Todas las armas y objetos en el inventario (6 armas, 15 habilidades, anillos y tótems)",
        variable=opt_inventario_var, font=fuente(13, True), fg="#CDD2DE", bg=COLOR_PANEL,
        activebackground=COLOR_PANEL, activeforeground="#FFFFFF", selectcolor=COLOR_FONDO,
        anchor="w", justify="left", wraplength=px(TARJETA_ANCHO) * 2)
    chk_inv.pack(fill="x", anchor="w", pady=px(2))

    def actualizar_opciones_pruebas(*_):
        """Muestra el panel de opciones solo cuando el nombre es el personaje de pruebas."""
        if nombre_var.get().strip().lower() == NOMBRE_CLAVE_PRUEBAS:
            panel_pruebas.pack(fill="x", pady=(px(10), 0))
        else:
            panel_pruebas.pack_forget()

    # -----------------------------
    # HABILIDADES POR CATEGORÍAS
    # -----------------------------
    panel_hab = panel(columna_der, "Habilidades  ·  elige hasta 3  (teclas [2] [3] [4])", "#C678DD")
    panel_hab.pack(fill="both", expand=True)
    cont_categorias = tk.Frame(panel_hab, bg=COLOR_PANEL)
    cont_categorias.pack(fill="x")

    columnas_cat = []

    def _columna_categoria(titulo, color, nombres):
        columna = tk.Frame(cont_categorias, bg=COLOR_PANEL)
        tk.Label(columna, text=titulo.upper(), font=fuente(13, True),
                 fg=color, bg=COLOR_PANEL).pack(anchor="w")
        tk.Frame(columna, bg=color, height=2).pack(fill="x", pady=(px(2), px(6)))
        for nombre in nombres:
            card, lbl, chk = _construir_tarjeta(columna, nombre, COLOR_HABILIDADES.get(nombre, "#98C379"),
                                                alternar_habilidad, info_habilidad)
            card.pack(pady=px(3))
            tarjetas_hab[nombre] = (card, lbl, chk)
        columnas_cat.append(columna)

    categorizadas = set()
    for titulo, color, nombres in CATEGORIAS_HABILIDADES:
        visibles = [n for n in nombres if n in HABILIDADES_DISPONIBLES]
        if visibles:
            _columna_categoria(titulo, color, visibles)
            categorizadas.update(visibles)
    # Respaldo: cualquier habilidad sin categoría asignada va a "Otras"
    sin_categoria = [n for n in HABILIDADES_DISPONIBLES if n not in categorizadas]
    if sin_categoria:
        _columna_categoria("Otras", "#8A93A6", sin_categoria)

    # Caja de información (la que alimenta el botón ?)
    caja_info = tk.Label(panel_hab, textvariable=info_var, font=fuente(14),
                         fg="#CDD2DE", bg=COLOR_CAJA, justify="left", anchor="nw",
                         padx=px(12), pady=px(10))
    caja_info.pack(fill="x", pady=(px(10), 0))

    # -----------------------------
    # REORGANIZACIÓN SEGÚN EL ANCHO DISPONIBLE
    # -----------------------------
    disposicion = {"clave": None}
    paso_tarjeta = ancho_tarjeta + 2 * px(SEPARACION)
    relleno_panel = 2 * px(RELLENO_PANEL) + 6     # relleno interno + bordes del LabelFrame

    def _repartir(widgets, columnas, padx, pady):
        for i, w in enumerate(widgets):
            w.grid(row=i // columnas, column=i % columnas, padx=padx, pady=pady, sticky="nw")

    def reorganizar(ancho_disp):
        margen = px(MARGEN)
        util = max(paso_tarjeta + relleno_panel, ancho_disp - 2 * margen)
        dos_columnas = ancho_disp >= px(ANCHO_MIN_DOS_COLUMNAS)
        if dos_columnas:
            ancho_izq = TARJETAS_HERR_POR_FILA * paso_tarjeta + relleno_panel
            ancho_der = util - ancho_izq - margen
        else:
            ancho_izq = ancho_der = util
        por_fila_herr = max(1, (ancho_izq - relleno_panel) // paso_tarjeta)
        por_fila_cat = max(1, (ancho_der - relleno_panel) // paso_tarjeta)
        clave = (dos_columnas, por_fila_herr, por_fila_cat, ancho_der)
        if clave == disposicion["clave"]:
            return
        disposicion["clave"] = clave

        for w in (cabecera, columna_izq, columna_der):
            w.grid_forget()
        cuerpo.grid_columnconfigure(0, weight=0)
        cuerpo.grid_columnconfigure(1, weight=0)
        cabecera.grid(row=0, column=0, columnspan=2, pady=(px(14), px(10)))
        if dos_columnas:
            columna_izq.grid(row=1, column=0, sticky="nw", padx=(margen, margen // 2), pady=(0, margen))
            columna_der.grid(row=1, column=1, sticky="nsew", padx=(margen // 2, margen), pady=(0, margen))
            cuerpo.grid_columnconfigure(1, weight=1)
        else:
            columna_izq.grid(row=1, column=0, sticky="ew", padx=margen, pady=(0, px(10)))
            columna_der.grid(row=2, column=0, sticky="ew", padx=margen, pady=(0, margen))
            cuerpo.grid_columnconfigure(0, weight=1)

        _repartir([tarjetas_herr[n][0] for n in tarjetas_herr], por_fila_herr, px(SEPARACION), px(SEPARACION))
        _repartir(columnas_cat, por_fila_cat, px(SEPARACION), (0, px(10)))
        caja_info.configure(wraplength=max(px(150), ancho_der - relleno_panel - 2 * px(12)))

    # -----------------------------
    # DESPLAZAMIENTO (solo si el contenido no cabe en alto)
    # -----------------------------
    def actualizar_desplazamiento(event=None):
        canvas.configure(scrollregion=(0, 0, cuerpo.winfo_reqwidth(), cuerpo.winfo_reqheight()))
        if cuerpo.winfo_reqheight() > canvas.winfo_height() + 1:
            barra.grid(row=0, column=1, sticky="ns")
        else:
            barra.grid_remove()
            canvas.yview_moveto(0)

    def al_cambiar_tamano(event):
        canvas.itemconfigure(item_cuerpo, width=event.width)
        # La disposición se calcula con el ancho de la ventana menos el hueco de la barra, así
        # mostrar u ocultar la barra no vuelve a reorganizar (evita un bucle de redimensionado)
        reorganizar(max(1, ventana.winfo_width() - barra.winfo_reqwidth()))
        ventana.after_idle(actualizar_desplazamiento)

    canvas.bind("<Configure>", al_cambiar_tamano)
    cuerpo.bind("<Configure>", actualizar_desplazamiento)

    def rueda(event):
        if barra.winfo_ismapped():
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    ventana.bind_all("<MouseWheel>", rueda)

    # -----------------------------
    # BOTÓN: COMENZAR MUNDO (fijo abajo, siempre visible)
    # -----------------------------
    def construir_config():
        nombre = nombre_var.get().strip() or "Héroe"
        color_rgb = COLORES.get(color_var.get(), (0, 150, 255))

        # Habilidades en el orden elegido (ya están limitadas a 3)
        habilidades = [crear_habilidad(n) for n in hab_seleccionadas[:3]]
        slots_teclas = [(pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4")]
        for idx, hab in enumerate(habilidades):
            tecla, tecla_str = slots_teclas[idx]
            hab.asignar_tecla(tecla, tecla_str)

        stats_finales = stats_actuales
        return {
            "nombre": nombre,
            "color": color_rgb,
            "tamano": stats_finales["tamano"],
            "velocidad": stats_finales["velocidad"],
            "vida": stats_finales["vida"],
            "fuerza": stats_finales["fuerza"],
            "energia": stats_finales["energia"],
            "escudo": stats_finales["escudo"],
            "escudo_magico": stats_finales["escudo_magico"],
            "habilidades": habilidades,
            "herramienta": crear_herramienta(herramienta_var.get()),
            # Opciones del personaje de pruebas: solo valen si el nombre es el nombre clave
            "puntos_extra": bool(opt_puntos_var.get()) and (nombre.lower() == NOMBRE_CLAVE_PRUEBAS),
            "dar_todo": bool(opt_inventario_var.get()) and (nombre.lower() == NOMBRE_CLAVE_PRUEBAS)
        }

    def al_comenzar_mundo():
        config_mundo = construir_config()
        if al_comenzar is not None:
            al_comenzar(config_mundo)
            return
        ventana.destroy()
        iniciar_mundo(config_mundo)

    pie = tk.Frame(ventana, bg=COLOR_FONDO)
    pie.grid(row=1, column=0, columnspan=2, sticky="ew")
    boton = tk.Button(pie, text="▶ Comenzar mundo (pantalla completa)",
                      font=fuente(20, True), bg="#98C379", fg=COLOR_FONDO,
                      activebackground="#7FA961", activeforeground=COLOR_FONDO, relief="flat",
                      cursor="hand2", command=al_comenzar_mundo)
    boton.pack(fill="x", padx=px(MARGEN), pady=(px(6), px(12)), ipady=px(5))

    nombre_var.trace_add("write", lambda *args: renderizar_stats())
    nombre_var.trace_add("write", actualizar_opciones_pruebas)

    actualizar_vista_previa()
    renderizar_stats()
    actualizar_opciones_pruebas()
    refrescar()
    reorganizar(ancho - barra.winfo_reqwidth())

    return {
        "escala": escala,
        "canvas": canvas,
        "barra": barra,
        "cuerpo": cuerpo,
        "boton": boton,
        "nombre_var": nombre_var,
        "color_var": color_var,
        "herramienta_var": herramienta_var,
        "hab_seleccionadas": hab_seleccionadas,
        "tarjetas_herr": tarjetas_herr,
        "tarjetas_hab": tarjetas_hab,
        "info_var": info_var,
        "caja_info": caja_info,
        "comenzar": al_comenzar_mundo,
    }


# -----------------------------
# INTERFAZ PRINCIPAL DE CREACIÓN
# -----------------------------
def iniciar_aplicacion():
    # Bucle de sesión: creación -> mundo -> (botón/[M] Volver) -> creación de nuevo.
    while True:
        ventana = tk.Tk()
        ventana.title("Creador de Personaje - Level")

        # Pantalla completa, como el juego. [ESC] sale de pantalla completa por si se necesita
        # (la interfaz se reorganiza sola al nuevo tamaño).
        ventana.attributes("-fullscreen", True)
        ventana.bind("<Escape>", lambda e: ventana.attributes("-fullscreen", False))

        sesion = {"config": None}

        def al_comenzar(config):
            sesion["config"] = config
            ventana.destroy()

        construir_interfaz(ventana, ventana.winfo_screenwidth(), ventana.winfo_screenheight(),
                           al_comenzar=al_comenzar)
        ventana.mainloop()

        if sesion["config"] is None:
            break  # Se cerró la creación sin comenzar: salir del programa.
        if iniciar_mundo(sesion["config"]) != "menu":
            break  # Salida total ([ESC]); si fue "menu", el while reabre la creación.


if __name__ == "__main__":
    iniciar_aplicacion()
