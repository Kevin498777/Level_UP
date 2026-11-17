import tkinter as tk
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
    "Escudo": "No golpea, protege. Debuff -34% a -10%, durabilidad 100-300. Al bloquear empuja al portador."
}

COLOR_HERRAMIENTAS = {
    "Espada Ligera": "#B0B5C0",
    "Espada Larga": "#9DA5B4",
    "Mandoble": "#7F8694",
    "Dagas Simples": "#C0C8D6",
    "Escudo": "#8FB0D6"
}

DESC_HABILIDADES = {
    "Destello": "Buff de velocidad +52% a +90% por 10-18s. Recarga 5-1s con fatiga al acabar. Costo 10-40 En. Máx nivel 20.",
    "Burst de Fuerza": "Buff de fuerza +21% a +40% por 6-10s. Recarga 12-8s. Costo 15-35 En.",
    "Disparo Veloz": "Esfera recta. Velocidad 11-30 y daño 20.5%-30% del total. Costo 15-35. Recarga 2-0.5s.",
    "Invocar Conejos": "Invoca 5 conejos que se reproducen (máx 50). Vida 5-20, velocidad 3-12.5, daño 0.1-7.7. Costo 80 En.",
    "Carga de Fuego": "Pulsa para disparo rápido o mantén hasta 5s para más daño (+25%) y tamaño. Al golpear quema 1/s por 5s. Costo 15 al pulsar y se cobra cada segundo cargado (hasta 45 En.).",
    "Aura Electrica": "Aura que te sigue: +5% a +15% velocidad y 1 a 5 daño/s a enemigos cercanos. Autodaño 0.5/s (mágico, lo frena tu escudo mágico). Costo 20-58 En., CD 40-60s.",
    "Reforzamiento Mágico": "Campo de fuerza que bloquea daño físico y mágico. Dureza 200-500, duración 1-6s. Si se agota la dureza se rompe. Costo 25-50 En., CD 10-35s.",
    "Regeneración Inversa": "Mágica. Mantén pulsado para curar: +1 vida/-10 En. cada 2s hasta +6 vida/-40 En. cada 3s. Sin recarga. Máx nivel 10 (mejora: 2 puntos)."
}

COLOR_HABILIDADES = {
    "Destello": "#56B6C2",
    "Burst de Fuerza": "#E5C07B",
    "Disparo Veloz": "#98C379",
    "Invocar Conejos": "#8FD694",
    "Carga de Fuego": "#E06C4A",
    "Aura Electrica": "#5BC8FF",
    "Reforzamiento Mágico": "#87CEFA",
    "Regeneración Inversa": "#FF69B4"
}

# -----------------------------
# ESTADÍSTICAS INICIALES (FIJAS)
# -----------------------------
def generar_estadisticas():
    # Estadísticas FIJAS de nivel 1 (sin aleatoriedad). Se mejoran con los puntos de nivel.
    return {
        "vida": 20,
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

STATS_PRUEBAS = {
    "velocidad": 99,
    "fuerza": 999,      # Daño base = fuerza -> 999 (con Espada Ligera x2)
    "energia": 999,
    "vida": 999,
    "escudo": 999,
    "escudo_magico": 999
}


def aplicar_stats_pruebas(nombre, stats):
    """Si el nombre es el nombre clave, sobrescribe las estadísticas con las de pruebas."""
    if nombre.strip().lower() == NOMBRE_CLAVE_PRUEBAS:
        stats = dict(stats)
        stats.update(STATS_PRUEBAS)
    return stats


# -----------------------------
# INTERFAZ PRINCIPAL DE CREACIÓN
# -----------------------------
def iniciar_aplicacion():
    stats_actuales = generar_estadisticas()

    ventana = tk.Tk()
    ventana.title("Creador de Personaje - Level")
    ventana.configure(bg="#1E2229")

    # Pantalla completa, como el juego. [ESC] sale de pantalla completa por si se necesita.
    ventana.attributes("-fullscreen", True)
    ventana.bind("<Escape>", lambda e: ventana.attributes("-fullscreen", False))

    # Contenedor central: mantiene el bloque de creación centrado en la pantalla.
    contenedor = tk.Frame(ventana, bg="#1E2229")
    contenedor.place(relx=0.5, rely=0.5, anchor="center")

    # Título Principal
    tk.Label(
        contenedor, text="CREACIÓN DE PERSONAJE",
        font=("Segoe UI", 18, "bold"), fg="#FFFFFF", bg="#1E2229"
    ).pack(pady=(12, 2))
    tk.Label(
        contenedor, text="Elige nombre, color, herramienta y habilidades.",
        font=("Segoe UI", 9), fg="#9DA5B4", bg="#1E2229"
    ).pack(pady=(0, 8))

    # -----------------------------
    # NOMBRE Y COLOR
    # -----------------------------
    frame_top = tk.Frame(contenedor, bg="#1E2229")
    frame_top.pack(padx=30, fill="x")

    frame_nombre = tk.Frame(frame_top, bg="#1E2229")
    frame_nombre.pack(side="left", fill="both", expand=True)
    tk.Label(frame_nombre, text="Nombre del Personaje:", font=("Segoe UI", 10, "bold"),
             fg="#E5C07B", bg="#1E2229").pack(anchor="w", pady=(0, 2))
    nombre_var = tk.StringVar(value="Héroe")
    tk.Entry(frame_nombre, textvariable=nombre_var, font=("Segoe UI", 11),
             bg="#282C34", fg="white", insertbackground="white", relief="flat",
             highlightthickness=1, highlightbackground="#4B5263",
             highlightcolor="#61AFEF").pack(fill="x", ipady=4)

    tk.Label(frame_nombre, text="Color:", font=("Segoe UI", 10, "bold"),
             fg="#61AFEF", bg="#1E2229").pack(anchor="w", pady=(8, 2))
    color_var = tk.StringVar(value="Azul")
    ttk.Combobox(frame_nombre, textvariable=color_var, values=list(COLORES.keys()),
                 state="readonly", font=("Segoe UI", 10)).pack(anchor="w", fill="x")

    vista_canvas = tk.Canvas(frame_top, width=70, height=70, bg="#282C34",
                             highlightthickness=1, highlightbackground="#4B5263")
    vista_canvas.pack(side="right", padx=(14, 0))

    def actualizar_vista_previa(*args):
        vista_canvas.delete("all")
        rgb = COLORES.get(color_var.get(), (0, 150, 255))
        color_hex = "#{:02x}{:02x}{:02x}".format(*rgb)
        cx, cy, radio = 35, 35, 20
        vista_canvas.create_oval(cx - radio, cy - radio, cx + radio, cy + radio,
                                 fill=color_hex, outline="white", width=2)
        vista_canvas.create_line(cx + radio + 4, cy - 12, cx + radio + 4, cy + 12, fill="#B0B5C0", width=2)

    color_var.trace_add("write", actualizar_vista_previa)

    # -----------------------------
    # ESTADO DE SELECCIÓN (tarjetas)
    # -----------------------------
    herramienta_var = tk.StringVar(value="Espada Ligera")
    hab_seleccionadas = ["Destello", "Burst de Fuerza", "Disparo Veloz"]  # orden = teclas [2],[3],[4]
    tarjetas_herr = {}
    tarjetas_hab = {}
    info_var = tk.StringVar(value="Pulsa el ? de una tarjeta para ver qué hace.")

    def _estilo_tarjeta(card, lbl, chk, color, seleccionado, numero=None):
        bg = "#30363F" if seleccionado else "#282C34"
        card.config(bg=bg, highlightthickness=2,
                    highlightbackground=(color if seleccionado else "#3A3F4B"))
        lbl.config(bg=bg)
        if seleccionado:
            chk.config(text=(str(numero) if numero else "●"), bg=bg, fg=color)
        else:
            chk.config(text="○", bg=bg, fg="#555C6A")

    def _construir_tarjeta(parent, nombre, color_hex, on_select, on_info):
        card = tk.Frame(parent, bg="#282C34", highlightthickness=2,
                        highlightbackground="#3A3F4B", width=205, height=50, cursor="hand2")
        card.pack_propagate(False)
        chk = tk.Label(card, text="○", font=("Segoe UI", 11, "bold"), fg="#555C6A", bg="#282C34")
        chk.place(x=8, y=14)
        lbl = tk.Label(card, text=nombre, font=("Segoe UI", 10, "bold"), fg=color_hex, bg="#282C34")
        lbl.place(x=32, y=15)
        info = tk.Label(card, text=" ? ", font=("Segoe UI", 9, "bold"),
                        fg="#1E2229", bg="#8A93A6", cursor="hand2")
        info.place(x=178, y=6)
        for w in (card, chk, lbl):
            w.bind("<Button-1>", lambda e, n=nombre: on_select(n))
        info.bind("<Button-1>", lambda e, n=nombre: on_info(n))
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
    # BLOQUE: EQUIPO Y HABILIDADES
    # -----------------------------
    frame_equipo = tk.LabelFrame(
        contenedor, text="  Equipo y Habilidades  ",
        font=("Segoe UI", 11, "bold"), fg="#61AFEF", bg="#282C34",
        padx=14, pady=10, relief="groove", bd=1
    )
    frame_equipo.pack(padx=30, pady=8, fill="x")

    tk.Label(frame_equipo, text="Herramienta principal  —  tecla [1]",
             font=("Segoe UI", 10, "bold"), fg="#CDD2DE", bg="#282C34").pack(anchor="w")
    grid_herr = tk.Frame(frame_equipo, bg="#282C34")
    grid_herr.pack(fill="x", pady=(6, 2))
    for i, nombre in enumerate(HERRAMIENTAS_DISPONIBLES.keys()):
        card, lbl, chk = _construir_tarjeta(grid_herr, nombre,
                                            COLOR_HERRAMIENTAS.get(nombre, "#B0B5C0"),
                                            seleccionar_herramienta, info_herramienta)
        card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="w")
        tarjetas_herr[nombre] = (card, lbl, chk)

    tk.Label(frame_equipo, text="Habilidades  —  elige hasta 3  (teclas [2] [3] [4])",
             font=("Segoe UI", 10, "bold"), fg="#CDD2DE", bg="#282C34").pack(anchor="w", pady=(12, 0))
    grid_hab = tk.Frame(frame_equipo, bg="#282C34")
    grid_hab.pack(fill="x", pady=(6, 2))
    for i, nombre in enumerate(HABILIDADES_DISPONIBLES.keys()):
        card, lbl, chk = _construir_tarjeta(grid_hab, nombre,
                                            COLOR_HABILIDADES.get(nombre, "#98C379"),
                                            alternar_habilidad, info_habilidad)
        card.grid(row=i // 3, column=i % 3, padx=5, pady=5, sticky="w")
        tarjetas_hab[nombre] = (card, lbl, chk)

    # Caja de información (la que alimenta el botón ?)
    tk.Label(frame_equipo, textvariable=info_var, font=("Segoe UI", 9),
             fg="#CDD2DE", bg="#21252B", justify="left", anchor="w",
             wraplength=640, padx=12, pady=10).pack(fill="x", pady=(12, 2))

    # -----------------------------
    # ESTADÍSTICAS INICIALES
    # -----------------------------
    frame_stats = tk.LabelFrame(
        contenedor, text="  Estadísticas Iniciales (Fijas · Nivel 1)  ",
        font=("Segoe UI", 10, "bold"), fg="#ABB2BF", bg="#282C34",
        padx=14, pady=8, relief="groove", bd=1
    )
    frame_stats.pack(padx=30, pady=4, fill="x")

    def renderizar_stats():
        for widget in frame_stats.winfo_children():
            widget.destroy()
        stats_vista = aplicar_stats_pruebas(nombre_var.get(), stats_actuales)
        filas = [
            ("Vida:", stats_vista["vida"], "#E06C75"),
            ("Fuerza:", stats_vista["fuerza"], "#D19A66"),
            ("Velocidad:", stats_vista["velocidad"], "#56B6C2"),
            ("Energía:", stats_vista["energia"], "#C678DD"),
            ("Escudo:", stats_vista["escudo"], "#98C379"),
            ("Escudo M.:", stats_vista["escudo_magico"], "#56B6C2"),
            ("Tamaño:", stats_vista["tamano"], "#E5C07B")
        ]
        for idx, (etiqueta, valor, color_destaque) in enumerate(filas):
            mitad = (len(filas) + 1) // 2
            col = 0 if idx < mitad else 2
            fila = idx if idx < mitad else idx - mitad
            tk.Label(frame_stats, text=etiqueta, font=("Segoe UI", 9, "bold"),
                     fg="#ABB2BF", bg="#282C34").grid(row=fila, column=col, sticky="w", pady=3, padx=(0, 4))
            tk.Label(frame_stats, text=str(valor), font=("Segoe UI", 9, "bold"),
                     fg=color_destaque, bg="#1E2229", width=6, relief="solid",
                     bd=1).grid(row=fila, column=col + 1, sticky="w", pady=3, padx=(0, 20))

    # -----------------------------
    # BOTÓN: COMENZAR MUNDO
    # -----------------------------
    def al_comenzar_mundo():
        nombre = nombre_var.get().strip() or "Héroe"
        color_rgb = COLORES.get(color_var.get(), (0, 150, 255))

        # Habilidades en el orden elegido (ya están limitadas a 3)
        habilidades = [crear_habilidad(n) for n in hab_seleccionadas[:3]]
        slots_teclas = [(pygame.K_2, "2"), (pygame.K_3, "3"), (pygame.K_4, "4")]
        for idx, hab in enumerate(habilidades):
            tecla, tecla_str = slots_teclas[idx]
            hab.asignar_tecla(tecla, tecla_str)

        stats_finales = aplicar_stats_pruebas(nombre, stats_actuales)
        config_mundo = {
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
            "herramienta": crear_herramienta(herramienta_var.get())
        }
        ventana.destroy()
        iniciar_mundo(config_mundo)

    tk.Button(contenedor, text="▶ Comenzar mundo (Pantalla Completa)",
              font=("Segoe UI", 13, "bold"), bg="#98C379", fg="#1E2229",
              activebackground="#7FA961", activeforeground="#1E2229", relief="flat",
              cursor="hand2", command=al_comenzar_mundo).pack(fill="x", padx=30, pady=(8, 14), ipady=6)

    nombre_var.trace_add("write", lambda *args: renderizar_stats())

    actualizar_vista_previa()
    renderizar_stats()
    refrescar()
    ventana.mainloop()


if __name__ == "__main__":
    iniciar_aplicacion()
