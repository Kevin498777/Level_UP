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
| Común | 60 % | Viento | Blanco | +1 % de velocidad base | 10 | +10 % |
| Común | | Fuerza | Naranja | +1 % de daño del arma | 10 | +10 % |
| Común | | Energía | Azul marino | +2.5 de energía máxima | 10 | +25 |
| Común | | Sombra conejo | Oscuro | Una sombra de conejo que te defiende (ver abajo) | 10 | daño 7.7, reaparece en 5 s |
| Especial | 30 % | Defensa mágica | Azul | +20/7 (≈2.86) de escudo mágico máximo, y +10 % de regeneración del escudo mágico (fijo) | 7 | +20 |
| Especial | | Defensa física | Café | +20/7 (≈2.86) de escudo físico máximo, y +10 % de regeneración del escudo físico (fijo) | 7 | +20 |
| Épico | 9 % | Vida | Rosa y rojo | +4 de vida máxima | 5 | +20 |
| Épico | | Cadencia | Amarillo y azul | +0.3 golpes/s | 5 | +1.5 |
| Épico | | Sombra lobo | Oscuro y morado | Una sombra de lobo que te defiende (ver abajo) | 10 | daño 30, reaparece en 4 s |
| Legendario | 1 % | Regeneración inversa | Rosa, azul marino y dorado | +0.3 de vida por segundo (siempre, también en combate) | 3 | +0.9/s |

Detalles:

- **Fuerza:** sube el daño de los golpes del **arma** (también las flechas). No afecta a habilidades ni a invocaciones, y no cambia la Fuerza del panel.
- **Viento:** se suma a los demás modificadores de velocidad sobre la velocidad base.
- **Defensas:** el escudo del anillo se suma **aunque tu escudo base sea 0**, y así ya bloquea y absorbe daño.
- **Vida y energía:** suben el máximo, pero **equiparlos no cura**. Al quitarlos, la vida y la energía se recortan al nuevo máximo.

### Anillos de sombra (conejo y lobo)

- Cada uno da **una** sombra (no se reproduce) que **te sigue** y **no se controla**.
- **Solo ataca** a quien te haya atacado **a ti o a ella** en los últimos 6 s (animales o el maniquí). Si tú atacas a algo que no te ataca (p. ej. un venado), no te ayuda.
- Su vida y velocidad son las de la habilidad de invocación al nivel equivalente: anillo 1 – 10 = habilidad 1, 3, 5, 7, 9, 12, 14, 16, 18, 20. El **daño** va en línea recta: conejo **1 → 7.7**, lobo **4 → 30** (el lobo conserva el 33 % de desangrado).
- Si muere, reaparece a tu lado: conejo **10 s → 5 s**, lobo **8 s → 4 s** según el nivel.
- Cuenta como una de **tus sombras**: los animales pasivos huyen de ella, lo que mate te da XP y monedas, y desaparece si quitas el anillo, si mueres o si te salva un tótem (después vuelve con su tiempo de reaparición). Es independiente de las habilidades Invocar Conejos e Invocar Lobos.

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

### Economía (simulación del 23/11/2026, 10 000 partidas, anillos v2)

Con las monedas de caza más **+20 por nivel**, un bot que tira en cuanto junta 30 monedas consiguió:

| | Jugador cuidadoso | Con encuentros de lobos y osos |
|---|---|---|
| Monedas ganadas por partida (media) | 290 | 567 (muere y vuelve a subir muchas veces) |
| Tiradas por partida (media / mediana) | 8.9 / 5 | 14.3 / 10 |
| Partidas que acabaron con el anillo legendario | 131 de 5000 | 23 de 5000 |
| Veces que un tótem evitó la muerte | 1908 | 6653 |
| Llegaron al nivel 20 (de 5000) | 48 | 2 |

### Prueba

Teclas de prueba: **[K]** da 100 monedas para probar el Gacha, **[T]** da un talismán al azar (un anillo con las probabilidades de rareza de arriba o, 1 de cada 5 veces, un tótem) y **[Y]** da una herramienta o habilidad que no tengas.
