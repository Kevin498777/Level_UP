# LEVEL_UP — Gacha y talismanes

> Documento de información (no técnico) del sistema de Gacha y sus objetos.
> Se construye por fases. Actualizado: 23 de noviembre de 2026.

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Talismanes: anillos, Tótem de vida, 3 huecos de equipo y pestaña en el inventario | **Hecha** |
| 2 | Colección de herramientas y habilidades: tener varias y elegir en el inventario cuáles llevar | **Hecha** |
| 3 | Gacha: tirada de 30 monedas desde un botón del inventario, con ruleta animada | **Hecha** |
| 4 | Documentación, pruebas y simulación de la economía | Pendiente |

---

## 1. Gacha

Una tirada cuesta **30 monedas**. Se hace en la pestaña **Gacha** del inventario [I] con el botón **TIRAR** y el mundo sigue en marcha mientras tanto.

- **El premio se aplica al momento de tirar.** La ruleta (≈2.6 s, frena poco a poco y se para en el premio) solo lo muestra: cerrar el inventario o que te ataquen mientras gira no hace perder nada. Mientras gira no se puede volver a tirar.
- La pestaña muestra tus monedas, el número de tiradas, el premio (con un brillo especial si es épico o legendario), las probabilidades con lo que te falta (herramientas, habilidades, tótems) y las **últimas 8 tiradas**.
- Los anillos y tótems van a la pestaña **Talismanes**; las herramientas y habilidades, a **Equipo** (una habilidad nueva se equipa sola si hay un hueco libre).

| Premio | Probabilidad | Si ya no queda nada que darte |
|---|---|---|
| Herramienta (una que no tengas, a nivel 1) | 25 % | Devuelve 25 monedas (ya tienes las 6) |
| Habilidad (una que no tengas, a nivel 1) | 15 % | Devuelve 25 monedas (ya tienes todas) |
| Anillo (según su rareza, ver 2) | 45 % | Si el anillo que sale ya está al máximo, devuelve 25 monedas |
| Tótem de vida | 10 % | Si ya tienes 5, devuelve 25 monedas |
| Nada | 5 % | — |

---

## 2. Talismanes

Solo dan efecto si están **equipados** en uno de los **3 huecos**: como máximo **1 legendario** y **2 épicos** a la vez. Un anillo repetido **sube un nivel** ese anillo, hasta su máximo. Se equipan y se quitan en la pestaña **Talismanes** del inventario [I].

Cuando el Gacha da un anillo, primero se sortea la rareza y luego un anillo de esa rareza al azar.

| Rareza | Probabilidad | Anillo | Color | Por nivel | Nivel máx. | Al máximo |
|---|---|---|---|---|---|---|
| Común | 60 % | Viento | Blanco | +0.5 % de velocidad base | 10 | +5 % |
| Común | | Fuerza | Naranja | +0.5 % de daño del arma | 10 | +5 % |
| Común | | Energía | Azul marino | +2.5 de energía máxima | 10 | +25 |
| Especial | 30 % | Vida | Rosa | +2.5 de vida máxima | 7 | +17.5 |
| Especial | | Cadencia | Amarillo | +0.2 golpes/s | 7 | +1.4 |
| Épico | 9 % | Defensa mágica | Gris y celeste | +4 de escudo mágico máximo, y +10 % de regeneración del escudo mágico (fijo) | 5 | +20 |
| Épico | | Defensa física | Café y celeste | +4 de escudo físico máximo, y +10 % de regeneración del escudo físico (fijo) | 5 | +20 |
| Legendario | 1 % | Regeneración inversa | Rosa, azul marino y dorado | Nv1: +0.3 de vida cada 3 s · Nv2: +0.6 cada 2 s · Nv3: +0.9 cada 1 s (siempre, también en combate) | 3 | +0.9/s |

Detalles:

- **Fuerza:** sube el daño de los golpes del **arma** (también las flechas). No afecta a habilidades ni a invocaciones, y no cambia la Fuerza del panel.
- **Viento:** se suma a los demás modificadores de velocidad sobre la velocidad base.
- **Defensas:** el escudo del anillo se suma **aunque tu escudo base sea 0**, y así ya bloquea y absorbe daño.
- **Vida y energía:** suben el máximo, pero **equiparlos no cura**. Al quitarlos, la vida y la energía se recortan al nuevo máximo.

### Tótem de vida

- Se acumula hasta **5**. Si ya tienes 5, otro te devuelve 25 monedas. Se puede conseguir de forma infinita (tras gastarlos).
- Ocupa **un hueco con toda su pila**.
- Si mueres con él equipado: gastas 1, **vuelves al centro** con la vida, la energía y los escudos llenos y sin efectos, y **no pierdes nada** (nivel, XP, monedas, objetos). Tus sombras desaparecen. En pantalla sale **"El Tótem de vida te salvó (quedan N)"**. Al gastar el último se libera su hueco.

### Colección de herramientas y habilidades (fase 2)

- Puedes tener **las 6 herramientas** y **las 15 habilidades**. Las nuevas llegan a **nivel 1**.
- Se eligen en la pestaña **Equipo** del inventario [I], que muestra todas: las que tienes y las que faltan (bloqueadas, "se consigue en el Gacha").
- **Herramienta:** botón **Equipar**. La que dejas conserva su nivel y su durabilidad; la nueva empieza **guardada** (se saca con [1]). Si dejas el Escudo, pierdes su pasiva de escudos.
- **Habilidades:** cada tarjeta tiene los botones **[2] [3] [4]** para ponerla en ese hueco. Si ya estaba en otro hueco, **se intercambian**; si el hueco tenía otra, esa se **guarda**. La tecla siempre es la del hueco.
- **Al guardar una habilidad** terminan sus efectos: desaparecen sus lobos, conejos o arañas y sus telarañas, se cancela la carga o la curación mantenida, y si estaba activa (Paso 0, Destello, Aura…) se acaba. **Conserva su nivel y su recarga**, y la recarga sigue corriendo mientras está guardada: no se puede "resetear" cambiándola.
- Una habilidad nueva se equipa sola si hay un hueco libre; si no, queda guardada.
- Se puede cambiar **en cualquier momento**, pero el mundo sigue en marcha mientras tanto.

### Muerte sin tótem

Se pierde **todo**: nivel, XP, monedas, talismanes, tótems y lo que hayas sacado del Gacha. Vuelves con la herramienta y las 3 habilidades de la creación, a nivel 1.

### Prueba

Teclas de prueba: **[K]** da 100 monedas para probar el Gacha, **[T]** da un talismán al azar (un anillo con las probabilidades de rareza de arriba o, 1 de cada 5 veces, un tótem) y **[Y]** da una herramienta o habilidad que no tengas.
