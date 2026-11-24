# LEVEL_UP — Gacha y talismanes

> Documento de información (no técnico) del sistema de Gacha y sus objetos.
> Se construye por fases. Actualizado: 24 de noviembre de 2026.

| Fase | Contenido | Estado |
|---|---|---|
| 1 | Talismanes: anillos, Tótem de vida, 3 huecos de equipo y pestaña en el inventario | **Hecha** |
| 2 | Colección de herramientas y habilidades: tener varias y elegir en el inventario cuáles llevar | **Hecha** |
| 3 | Gacha: tirada de 15 monedas (20 el mejorado desde el nivel 20) desde un botón del inventario, con ruleta animada; rediseño con regla proporcional, legendario garantizado a las 90 y habilidades potenciadas (24/11) | **Hecha** |
| 4 | Documentación, pruebas y simulación de la economía | Pendiente |

---

## 1. Gacha (rediseño del 24/11/2026)

Una tirada cuesta **15 monedas**. Al llegar al **nivel 20** se habilita el **Gacha mejorado** (con habilidades potenciadas), que cuesta **20 monedas**. Si te sale algo que ya no te sirve, ambos devuelven **10**. Se hace en la pestaña **Gacha** del inventario [I] con el botón **TIRAR** y el mundo sigue en marcha mientras tanto.

- **El premio se aplica al momento de tirar.** La ruleta (≈2.6 s) solo lo muestra: cerrar el inventario o que te ataquen mientras gira no hace perder nada. Mientras gira no se puede volver a tirar.
- La pestaña muestra tus monedas, las tiradas, el premio, las **probabilidades reales de tu próxima tirada** (cambian según lo que ya tienes), cuántas tiradas faltan para el legendario garantizado y las **últimas 8 tiradas**.
- Los anillos y tótems van a la pestaña **Talismanes**; las herramientas y habilidades, a **Equipo** (una habilidad nueva se equipa sola si hay un hueco libre).

### 1.1 Probabilidades: regla proporcional

1. **Nada** vale siempre **15 %**.
2. Una categoría **agotada** (ya no puede darte nada nuevo) baja a **5 %** fijo y, si sale, **devuelve 10 monedas**.
3. El resto se reparte entre las categorías que aún tienen premios, en proporción a su **peso base**: Herramienta 22 · Habilidad 13 · Anillo 41 · Tótem 9 · Habilidad potenciada 20.

| Caso | Herramienta | Habilidad | Anillo | Tótem | Nada |
|---|---|---|---|---|---|
| Normal | 22 % | 13 % | 41 % | 9 % | 15 % |
| Todas las herramientas | 5 % | 16.5 % | 52.1 % | 11.4 % | 15 % |
| Todas las habilidades | 24.4 % | 5 % | 45.6 % | 10 % | 15 % |
| Herramientas + habilidades | 5 % | 5 % | 61.5 % | 13.5 % | 15 % |
| 5 tótems | 23.2 % | 13.7 % | 43.2 % | 5 % | 15 % |
| Herramientas + habilidades + 5 tótems | 5 % | 5 % | 70 % | 5 % | 15 % |

Cuándo está agotada cada categoría: **Herramienta** si tienes las 6; **Habilidad** si tienes las 15; **Anillo** si los 10 están al máximo; **Tótem** si tienes 5 (al gastarlos vuelve a su probabilidad normal); **Potenciada** si todas tus habilidades están potenciadas.

### 1.2 Anillos

- **Solo se sortean anillos que aún pueden subir de nivel**: nunca sale uno que ya está al máximo.
- Primero se sortea la rareza (60 / 30 / 9 / 1) y luego un anillo de esa rareza. Si una rareza ya no tiene anillos por subir, su probabilidad **pasa a las demás** en proporción (ej. con los 4 comunes al máximo: Especial 75 %, Épico 22.5 %, Legendario 2.5 %).
- **Legendario garantizado:** la **tirada 90** sin legendario lo da seguro. Puede salir antes por suerte; cuando sale (por suerte, por la garantía o en el orbe del oso) **la cuenta vuelve a 0** para el siguiente. Si el legendario ya está al máximo no hay garantía. Las tiradas gratis del orbe no suman a la cuenta.
- **Orbe Gacha:** al matar un oso, con un 50 % aparece un orbe dorado en la boca de su cueva. Gira una **ruleta gratis solo de anillos** (mismas reglas: solo anillos que pueden subir); si todos están al máximo devuelve 10 monedas.

### 1.3 Habilidades potenciadas (desde el nivel 20)

- Al llegar al **nivel 20** aparece la categoría **Habilidad potenciada** (peso 20): desbloquea la versión potenciada de una habilidad de tu colección. **Solo salen las que ya están diseñadas** (por ahora: Destello → **Relámpago** y Burst de Fuerza → **Fuerza Colosal** , Disparo Veloz → **Ráfaga Veloz** y Carga de Fuego → **Estrella Ígnea**); si no te queda ninguna, la categoría cuenta como agotada.
- Si ya tienes las 15 habilidades normales, la potenciada **ocupa el sitio de "Habilidad"**; si no, conviven las dos.
- Si sale con la habilidad por debajo de su nivel máximo normal queda **desbloqueada pero inactiva** (en Equipo aparece "Pot. al Nv 20"); al llegar al máximo se convierte en la potenciada, sube hasta el **nivel 30** y cada nivel extra cuesta **2 puntos**. Detalle de cada una en `Level_UP_Especificaciones.md` (9.x). Se pierden al morir sin tótem.

| Nivel 20 (herramientas completas, 5 tótems) | Herramienta | Potenciada | Anillo | Tótem | Nada |
|---|---|---|---|---|---|
| Sin potenciadas | 5 % | 24.6 % | 50.4 % | 5 % | 15 % |
| Con todas las potenciadas | 5 % | 5 % | 70 % | 5 % | 15 % |

### 1.4 Economía

La devolución (10) es siempre **menor** que la tirada: con todo conseguido, cada tirada del Gacha mejorado pierde 11.5 monedas de media (20 − 0.85 × 10), así que no puede dar monedas infinitas.

Simulación del 24/11/2026 (10 000 partidas con el bot, combate cuerpo a cuerpo nuevo y 4 puntos por nivel):

| | Tirada a 10 | Tirada a 25 | **15 / 20 mejorado (actual)** |
|---|---|---|---|
| Llegan al nivel 20 | 92.1 % | 71.4 % | **83.3 %** |
| Tiempo mediano al nivel 20 | 125 min | 135 min | **134 min** |
| Llegan al nivel 15 / 10 | 95 % / 96 % | 76 % / 81 % | **88 % / 90 %** |
| Muertes por partida | 3.8 | 8.8 | **5.9** |
| Tiradas hasta el nivel 20 | 231 | 62 | **114** |
| Al llegar al 20: todos los objetos | 52 % | 1.4 % | **80 %** |
| Al llegar al 20: legendario | 61 % | 27 % | **100 %** (por la garantía) |

Jugando **2 horas más** en el nivel 20 con el Gacha mejorado (≈43 tiradas más), de los que siguen vivos en el 20: 99 % tiene todos los objetos, 9.6 de 10 anillos al máximo y 13.4 de 15 potenciadas (**76 % las 15**). El primer legendario sale de media en la tirada 77.

---|---|---|
| Llegan al nivel 20 | 92.1 % (mediana 125 min) | 71.4 % (mediana 135 min) |
| Muertes por partida | 3.8 | 8.8 (menos tótems: el Gacha da menos) |
| Tiradas hasta el nivel 20 | 231 | 62 |
| Al llegar al 20: todos los objetos | 52 % | 1.4 % |
| Al llegar al 20: legendario | 61 % | 27 % |

Jugando **2 horas más** en el nivel 20 (≈55 tiradas más), de los que siguen vivos en el 20: 88 % tiene las 15 habilidades, 74 % los 10 anillos, 94 % el legendario, **69 % todos los objetos**, 5.6 de 10 anillos al máximo y 11.7 de 15 potenciadas (46 % las 15). El legendario sale de media en la tirada 74; el 61 % de las veces llega por la garantía de la tirada 90.

---

## 2. Talismanes

Solo dan efecto si están **equipados** en uno de los **3 huecos**: como máximo **1 legendario** y **2 épicos** a la vez. Un anillo repetido **sube un nivel** ese anillo, hasta su máximo. Se equipan y se quitan en la pestaña **Talismanes** del inventario [I].

Cuando el Gacha da un anillo, primero se sortea la rareza y luego un anillo de esa rareza al azar, solo entre los que aún pueden subir (ver 1.2).

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

- Se acumula hasta **5**. Si ya tienes 5, el Tótem baja al 5 % y, si sale, devuelve 10 monedas. Se puede conseguir de forma infinita (tras gastarlos).
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

### Economía anterior (simulación del 23/11/2026 con la tirada a 30, ya no vigente)

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
