# LEVEL_UP — Especificaciones de juego

> Documento de información (no técnico) sobre el estado actual del juego.
> Pensado como contexto de referencia para la IA y para el equipo.
> Actualizado: 18 de noviembre de 2026.

---

## 1. Resumen general

Level_UP es un juego 2D de vista cenital en el que controlas a un personaje dentro de un mundo circular. El personaje se mueve haciendo clic, explora el mapa, se enfrenta a terrenos con efectos (agua, lagos peligrosos), se esconde en la vegetación y mejora sus estadísticas, su arma y sus habilidades subiendo de nivel.

Actualmente el juego cuenta con la generación completa del mundo, el sistema de movimiento y cámara, un sistema de progresión por niveles con puntos de mejora, cinco armas y doce habilidades, además de una interfaz con paneles de información a ambos lados de la pantalla. **Todavía no hay enemigos**, pero sí un **maniquí de pruebas** en el centro del mapa al que las invocaciones ya pueden atacar; el sistema de **puntos de empuje** (retroceso al dar o recibir daño) ya está activo, y efectos como la quemadura quedan preparados para cuando se añadan enemigos.

---

## 2. El mundo

- **Forma y tamaño:** mapa circular de radio 5000, rodeado por una franja oscura exterior que marca el límite.
- **Aparición:** el personaje aparece en el centro del mapa, dentro de una zona segura de 140 px sin obstáculos.
- **Cámara:** sigue al personaje con un movimiento suave, manteniéndolo centrado en el área de juego.
- **Fondo:** cuadrícula sutil recortada al círculo, con el borde y el centro del mundo marcados.

---

## 3. Terreno acuático: charcos y lagos

Cada mundo genera entre **4 y 6** masas de agua con forma de nube, con radios de **100 a 500**. No se solapan entre sí ni invaden la zona de aparición.

- **Agua normal:** reduce la velocidad de movimiento un **50 %**.
- **Lago profundo (peligroso):** si un lago supera un radio de **300**, su zona central (el 35 % interior, azul más oscuro) reduce la movilidad un **80 %** y resta **10 puntos de vida por segundo**. El resto del lago conserva el −50 %.

---

## 4. Rocas

Cada mundo genera entre **100 y 250** rocas. Son **sólidas** (no se atraviesan ni se empujan) y **bloquean los proyectiles**. No aparecen sobre el agua, la vegetación ni la zona segura.

| Tipo de roca | Proporción | Tamaño (px) |
|---|---|---|
| Pequeña | 60 % | 22 – 45 |
| Grande | 35 % | 70 – 130 |
| Gigante | 5 % | 150 – 300 |

La habilidad **Cortar** puede destruir rocas pequeñas y grandes; las gigantes solo a nivel 20 (ver 9.14).

---

## 5. Vegetación

Los arbustos tienen forma de nube y los **tres tipos se ven idénticos** a simple vista. Diámetro **50 a 150 px** (frutales mín. 50). Un personaje solo entra y se esconde si cabe; si no cabe, el arbusto es un **obstáculo sólido**. Dentro, el personaje queda **oculto** y el mapa se oscurece.

### 5.1 Tipos de arbusto

| Tipo | Cantidad | Efecto |
|---|---|---|
| Escondite | 35 – 80 | Solo sirve para ocultarse. |
| Venenoso | 25 – 45 | Oculta, pero hace 1 de daño cada 2 s (ignora defensa). |
| Frutal | 10 – 16 | Oculta y contiene 1 – 5 orbes rojos; cada uno cura +2 de vida. |

### 5.2 Ciclo de los frutales

Al quedarse sin orbes, el frutal desaparece y **un minuto después** reaparece pasando por tres fases: **brote** (20 px, sin fruta) → **joven** (tamaño normal, 1 fruta, tras 1 min) → **maduro** (frutas aleatorias 1–5, tras otro minuto).

### 5.3 Matorrales

Un **40 % de probabilidad** por mundo genera entre **1 y 3 matorrales**: conjuntos densos de 5 a 8 arbustos de distintos tipos y tamaños, solapados como una sola masa de vegetación.

---

## 6. El personaje

Se mueve haciendo clic; gira hacia donde se desplaza. Colisiona con rocas y arbustos sólidos y no sale del límite del mapa.

### 6.1 Estadísticas iniciales (nivel 1, fijas)

| Estadística | Valor inicial | Mejora por punto |
|---|---|---|
| Vida | 20 | +2 |
| Fuerza (Daño) | 2 | +0.2 |
| Velocidad | 1 | +0.1 |
| Escudo (físico) | 0 | +5 hasta 15, luego +2 |
| Escudo mágico | 0 | +5 hasta 15, luego +2 |
| Energía | 100 | +5 |
| Tamaño | 1 | — (estético) |

### 6.2 Significado de cada estadística

- **Vida:** puntos de vida; se recupera con los orbes de los frutales.
- **Fuerza (Daño):** base del golpe del arma; en el panel de mejora se muestra como **Daño**. Sube con la habilidad Burst de Fuerza.
- **Velocidad:** desplazamiento; cambia con el agua, el arma desenfundada y la habilidad Destello.
- **Escudo (físico):** reserva que absorbe el **daño físico** (armas y conejos). Se gasta al recibir golpes y se regenera.
- **Escudo mágico:** reserva que absorbe el **daño mágico** (habilidades que consumen energía). Se gasta y regenera igual que el físico.
- **Energía:** coste de las habilidades. Regenera **+1 cada 3 s** quieto y **+1 cada 6 s** en movimiento.

### 6.3 Tipos de daño y escudos

El daño se divide en dos tipos:

- **Físico:** el de las herramientas (espadas, dagas, mandoble) y los conejos.
- **Mágico:** el de las habilidades que consumen energía (Disparo Veloz, Carga de Fuego, Aura Eléctrica, Cortar, Onda Sonora). Burst de Fuerza no cuenta como daño mágico: solo sube la fuerza, el golpe lo sigue dando el arma (físico).

Cada tipo lo amortigua su propio escudo del personaje:

| Escudo | Bloqueo del daño total | Reparto (escudo / vida) |
|---|---|---|
| Físico | 20 % | 70 % / 30 % |
| Mágico | 10 % | 90 % / 10 % |

El escudo absorbe su parte hasta agotarse; si esa parte supera el escudo disponible, el sobrante pasa también a la vida. Ambos escudos empiezan en **0**, se mejoran **+5 por punto hasta un máximo de 15** y luego **+2 por punto**, y **se regeneran +1 por segundo tras 10 s sin recibir ese tipo de daño** (cada uno con su propio contador). El daño de terreno (lago profundo, hierba venenosa) ignora los escudos y se aplica directo a la vida.

**Anulación del escudo mágico (pasiva de Cortar):** el escudo absorbe el golpe con las reglas normales y, si el golpe llegó a hacer daño, el escudo restante queda **anulado 10 s**: se muestra en 0, no absorbe nada (el daño mágico va directo a la vida) y no se regenera. Al terminar **vuelve al valor que le quedó tras el golpe** (ej. 100 → el corte lo deja en 25 → 0 durante 10 s → vuelve a 25). Otro corte durante la anulación reinicia los 10 s. En el panel se ve como **ANULADO**.

Si el **Reforzamiento Mágico** está activo, su campo de fuerza recibe primero cualquier daño físico o mágico; solo lo que sobra cuando se rompe llega a los escudos y a la vida (ver 9.7).

---

## 7. Progresión y puntos de mejora

El personaje empieza con **3 puntos de mejora** y gana **3 por cada nivel**. Son un **recurso compartido** para mejorar estadísticas, arma o habilidades con los botones **[+]** verdes.

- **Coste:** una estadística cuesta **1 punto**, una habilidad **1 punto** y el arma **2 puntos** por nivel.
- **Subir de nivel:** por ahora con una tecla de prueba (ver controles); en el futuro vendrá del combate.

---

## 8. Herramientas (armas)

Se saca o guarda con la tecla **[1]**. Desenfundada reduce la velocidad y permite hacer daño. Hay **cinco** a elegir en la creación. Nivel máximo **5**; al alcanzarlo, la hoja toma un tono dorado.

### 8.1 Comparativa

| Arma | Nivel | Daño (×Fuerza) | Debuff velocidad | Durabilidad |
|---|---|---|---|---|
| Espada Ligera | 1 → 5 | ×2.2 → ×3.0 | −17 % → −5 % | 220 → 300 |
| Espada Larga | 1 → 5 | ×3.4 → ×5.0 | −34 % → −10 % | 190 → 230 |
| Mandoble | 1 → 5 | ×6.6 → ×9.0 | −70 % → −30 % | 148 → 180 |
| Dagas Simples | 1 → 5 | ×1.5 → ×2.5 | −20 % → **+10 % (buff)** | 150 → 400 (compartida) |
| Escudo | 1 → 5 | — (no golpea) | −34 % → −10 % | 100 → 300 |

> El daño se calcula sobre la **fuerza actual**, así que también se beneficia de Burst de Fuerza.

### 8.2 Particularidades

- **Dagas Simples:** son **dos** hojas (una por flanco), más pequeñas; a **nivel máximo** su debuff se convierte en un **buff de +10 %** de velocidad. Las dos comparten la misma durabilidad.
- **Escudo:** no inflige daño, **protege**. Cada vez que es golpeado se desgasta y **empuja al portador** 2 puntos de empuje hacia atrás.

### 8.3 Durabilidad y rotura

- **Desgaste:** cada golpe que hace daño gasta 1 punto de durabilidad.
- **Rotura:** al llegar a 0, el arma se rompe, pierde todos los niveles (vuelve a nivel 1) y queda inutilizable.
- **Reparación:** la única forma de repararla es **subirla de nivel**; recupera toda su durabilidad.

### 8.4 Diferencias estéticas de tamaño

Solo visual: Espada Ligera 20 % más grande; Espada Larga 20 % más larga y 10 % más ancha; Mandoble 20 % más largo y 30 % más ancho.

---

## 9. Habilidades

Se equipan en las teclas **[2]**, **[3]** y **[4]** (hasta 3 elegidas en la creación). Consumen energía y tienen recarga. Nivel máximo **20** (Regeneración Inversa: **10**).

### 9.1 Destello

Buff de velocidad **+52 % → +90 %**, duración **10 → 18 s**, recarga **5 → 1 s**, debuff de fatiga al acabar **−20 % → 0 %**, coste **10 → 40 En.**

### 9.2 Burst de Fuerza

Buff de fuerza **+21 % → +40 %**, duración **6 → 10 s**, recarga **12 → 8 s**, coste **15 → 35 En.**

### 9.3 Disparo Veloz

Esfera recta. Velocidad del proyectil **11 → 30**, daño **20.5 % → 30 %** del daño total, coste fijo **15 → 35 En.** (15 +5 cada 5 niveles), recarga **2 → 0.5 s**.

### 9.4 Invocar Conejos

Invoca **5 conejos** detrás del personaje (esferas verdes con cara `:3`). No se puede reinvocar hasta que todos mueran; con 2 o más vivos nacen **floor(vivos/2) cada 10 s**, hasta un máximo de **50**. Por conejo: Vida **5 → 20** (+3 cada 4 niveles), Velocidad **3 → 12.5**, Daño **0.1 → 7.7**. Coste fijo **80 En.** Al morir todos, **30 s de recarga** antes de reinvocar. Se les puede poner en **modo combate** (ver 9.11).

### 9.5 Carga de Fuego

Esfera de fuego con **dos modos**: pulsar = disparo rápido; mantener la tecla hasta **5 s** = carga más daño y tamaño, y dispara al soltar. Daño base **20 → 39** (+1 por nivel). La carga añade daño (hasta **+25 %**) y tamaño. Al golpear aplica **quemadura**: 1 de daño por segundo durante 5 segundos.

La energía se gasta **en tiempo real**: al pulsar se cobran 15 y cada segundo completo de carga cobra su parte (+5, +5, +5, +5 y +10; 45 en total a 5 s). Si no queda energía para el siguiente segundo, la carga se detiene en el nivel ya pagado y dispara con él al soltar.

### 9.6 Aura Eléctrica

Aura de 100 px de radio que sigue al personaje. Buff de velocidad **+5 % → +15 %** y **1 → 5** de daño por segundo a los enemigos cercanos (preparado para cuando existan). Mientras está activa, el portador recibe **0.5 de daño mágico por segundo** (lo amortigua su escudo mágico). Duración **10 → 20 s**, recarga **40 → 60 s**, coste **20 → 58 En.** (+2 por nivel).

### 9.7 Reforzamiento Mágico

Campo de fuerza **azul celeste** (solo el contorno, delgado) un **10 % más grande** que el personaje. Bloquea **daño físico y mágico**: absorbe todo el daño hasta agotar su **dureza**. Si la dureza se agota antes de terminar la duración, el campo **se rompe**, entra en recarga y el daño sobrante pasa a los escudos y a la vida.

| Nivel | Dureza | Duración | Recarga | Coste En. |
|---|---|---|---|---|
| 1 | 200 | 1 s | 10 s | 25 |
| 5 | 260 | 2 s | 15 s | 30 |
| 10 | 335 | 3 s | 20 s | 35 |
| 15 | 410 | 4 s | 25 s | 40 |
| 20 | **500** | 6 s | 35 s | 50 |

La dureza sube **+15 por nivel** y en el nivel 20 recibe un bono final hasta **500**. Duración, recarga y coste se mantienen por tramos hasta el siguiente nivel de la tabla.

### 9.8 Regeneración Inversa

Habilidad **mágica** que se **mantiene pulsada** y **no tiene recarga**. Mientras la tecla sigue pulsada, cada intervalo completo cobra energía y cura vida (sin pasar de la vida máxima; con la vida llena no cobra). Si no hay energía para el siguiente intervalo, deja de curar hasta volver a pulsar. Mientras está activa muestra el mismo contorno que el Reforzamiento Mágico, en **rosa**. Nivel máximo **10**; cada mejora cuesta **2 puntos** (como las armas).

| Nivel | Cura | Energía | Cada |
|---|---|---|---|
| 1 – 2 | +1 | −10 | 2 s |
| 3 – 5 | +2 | −15 | 2 s |
| 6 – 8 | +3 | −20 | 2 s |
| 9 | +4 | −25 | 2 s |
| 10 | +6 | −40 | 3 s |

### 9.9 Golpe de Suerte

Al lanzarla otorga un **resultado aleatorio**: Burst de Fuerza, Destello, Reforzamiento Mágico, Regeneración Inversa o Aura Eléctrica (como efecto temporal, sin coste extra), **energía al máximo**, **escudos al máximo** (físico y mágico) o **nada**. Cada resultado tiene un **10 %** y "nada" un **30 %**; en **nivel 20** "nada" baja al **5 %** y el resto se reparte a partes iguales (≈13.6 % cada uno).

| Nivel | Coste En. | Nivel de la habilidad otorgada | Duración otorgada | Espera (instantáneos) | Recarga |
|---|---|---|---|---|---|
| 1 – 4 | 15 | 1 | 5 s | 5 s | 5 s |
| 5 – 9 | 20 | 5 | 10 s | 5 s | 8 s |
| 10 – 14 | 25 | 10 | 15 s | 5 s | 12 s |
| 15 – 19 | 30 | 15 | 20 s | 5 s | 15 s |
| 20 | 50 | 20 | 30 s | **2 s** | 20 s |

- **Bloqueo:** no se puede volver a lanzar hasta que termine lo otorgado; **después** empieza la recarga. Así nunca hay dos resultados a la vez.
- **Habilidad otorgada:** tiene las estadísticas de su nivel pero dura lo que marca la tabla. Si termina antes (por ejemplo, el Reforzamiento se rompe), la recarga empieza en ese momento. El Destello otorgado no deja fatiga.
- **Regeneración otorgada:** cura sola, sin pulsar ni gastar energía, con sus propios tiempos: 4 s (+1 cada 2 s) en nv 1–4, 6 s en nv 5–9, 8 s en nv 10–14, 10 s (+2 cada 2 s) en nv 15–19 y 10 s (+2 cada 1 s) en nv 20.
- **Resultado instantáneo** (energía, escudos o nada): bloquea durante la espera básica y luego empieza la recarga.
- **Misma habilidad activa dos veces** (equipada y otorgada): sus efectos buenos **se suman**. La otorgada por Golpe de Suerte aporta siempre el **100 %** y la equipada solo el **50 %**, sin importar su nivel ni el orden en que se activen (ej. Burst otorgado +21 % y equipado +35 % = +21 % + 17.5 % = **+38.5 %**). Reforzamiento: absorbe primero el campo otorgado y luego el equipado al 50 % de eficacia. Regeneración: la equipada cura al 50 %. Cuando una termina, la otra vuelve al 100 %. Costes, recargas, combo y efectos negativos (fatiga del Destello, autodaño del Aura) no cambian.

### 9.10 Regla de combo

Lanzar una habilidad mientras otra sigue activa cuesta un **+5 % de la energía actual**.

---

### 9.11 Invocar Lobos

Invocación **mágica** (segunda de las 10 Artes de las Sombras). Invoca **3 lobos** detrás del personaje (cuerpo gris con orejas y ojos rojos). No se puede reinvocar hasta que mueran todos; al morir el último hay **30 s de recarga**. Cada golpe tiene un **33 %** de aplicar **desangrado** al objetivo: recibe **5 golpes de 1 de vida, uno cada 2 s** (ignora escudos). Se cuenta **por golpes, no por tiempo**, así el daño total es siempre 5 sin importar los FPS. El efecto sigue **activo hasta que cae el último golpe** y mientras dura reduce **toda curación un 50 %**. **No es acumulable**: reaplicarlo solo reinicia los 5 golpes.

| Nivel | Vida | Velocidad | Daño | Coste En. |
|---|---|---|---|---|
| 1 | 10 | 10 | 8 | 90 |
| 5 | 22 | 12 | 12.6 | 90 |
| 10 | 37 | 14 | 18.4 | 90 |
| 15 | 52 | 16 | 24.2 | 90 |
| 20 | 67 | 18 | 30 | 90 |

La vida sube **+3 por nivel**, la velocidad **+2 cada 5 niveles** y el daño escala de forma lineal de **8 a 30** (nivel 1 a 20). Coste fijo **90 En.** Nivel máximo **20**. Tabla completa en `Tablas_Escalado.md` (2.10).

### 9.12 Modo combate (invocaciones sombrías)

Conejos y lobos comparten el **modo combate**. Con la invocación ya activa, **mantener su tecla** ([2], [3] o [4]) las pone en guardia (se les **encienden los ojos** al instante). Mientras mantienes la tecla, el **clic derecho** da la orden:

- **Clic derecho sobre un enemigo** (p. ej. el maniquí): lo fijan como objetivo y lo **persiguen aunque se mueva**, atacándolo hasta que muera. Al morir el objetivo vuelven a seguirte.
- **Clic derecho en terreno libre**: van a ese punto.
- **Clic derecho junto a ti**: las llama de vuelta (vuelven a seguirte).

La orden **persiste aunque sueltes la tecla**, así conservas tu movilidad (el **clic izquierdo** sigue moviendo solo a tu personaje) mientras las sombras siguen atacando. Con una orden en curso, **volver a mantener la tecla y soltarla sin dar otra orden** las devuelve al **estado pasivo** (te siguen); si mientras la mantienes das otra orden con el clic derecho, se queda la nueva. Atacan **por intervalos** (1 golpe/s por criatura) y, por el retroceso al golpear (ver sección 10), no apilan todo su daño de golpe.

Los conejos tienen la cara `:3` con los **ojos rojos**, que en modo combate brillan con un halo.

### 9.13 Cuerpos sólidos (sin solapamientos)

El personaje, el maniquí y las invocaciones tienen **hitbox circular** (su radio): pueden **recibir daño** y **no se solapan** entre sí. Al chocar se separan según su **masa**: conejo 1, lobo 3, personaje 100 (sus invocaciones apenas lo desplazan) y maniquí fijo (nada lo mueve, salvo su propio retroceso). Con [H] se ven las hitboxes del maniquí y de las invocaciones (círculos magenta).

### 9.14 Cortar

Habilidad de **daño mágico** (categoría Ataque Mágico). Lanza hacia donde mira el personaje una **cuchilla delgada** en línea recta, del largo aproximado de la Espada Ligera, **negra con contorno rojo**. Sale desde el centro del personaje (se hace visible al salir de su cuerpo) y se detiene en lo primero que toque:

- **Enemigo:** se detiene en el **primero**. Hace su daño mágico (lo amortigua el escudo mágico) y, si llega a hacer daño, **anula su escudo mágico 10 s** (ver 6.3).
- **Roca o arbusto:** lo **destruye** y la cuchilla se rompe con él (**solo un objeto** por cuchilla). Las **rocas gigantes** y los **arbustos grandes** (más de 100 de diámetro) solo se destruyen a **nivel 20**; antes, la cuchilla se rompe y el objeto queda intacto. Si hay arbustos solapados (matorral), corta el más cercano. Los objetos destruidos **no reaparecen** (tampoco los frutales) y, si estabas escondido en un arbusto que se destruye, quedas a la vista. **Lanzada desde dentro de un arbusto**, la cuchilla sale de dentro hacia afuera **sin cortarlo** (sí corta el siguiente objeto de su camino).

| Nivel | Daño | Velocidad | Coste En. | Recarga |
|---|---|---|---|---|
| 1 | 35 | 5 | 15 | 2 s |
| 5 | 43 | 9 | 23 | 4 s |
| 10 | 53 | 14 | 33 | 6 s |
| 15 | 63 | 19 | 43 | 8 s |
| 19 | 71 | 23 | 51 | 8 s |
| 20 | 75 | 24 | 53 | 10 s |

Daño **35 +2 por nivel** (a nivel 20 sube a **75**), velocidad **5 +1 por nivel**, coste **15 +2 por nivel** y recarga **2 s +2 s cada 5 niveles** (sube a propósito). Nivel máximo **20**. Tabla completa en `Tablas_Escalado.md` (2.11).

### 9.15 Onda Sonora

Habilidad de **daño mágico** (categoría Ataque Mágico). Emite **anillos blancos finos** que se expanden en **360°** hasta el radio máximo, donde se desvanecen. Las ondas salen **una cada 0.8 s**, todas desde el **punto donde se lanzó** (no siguen al personaje aunque se mueva):

- **Nivel 1–9:** 1 onda de **10** de daño.
- **Nivel 10–19:** 2 ondas (**10** y **20**).
- **Nivel 20:** 3 ondas (**10**, **20** y **30**).

Atraviesan rocas y arbustos **sin destruir nada** y **solo afectan a enemigos** (no al lanzador ni a sus invocaciones). Cada onda golpea **una sola vez** a cada objetivo; tras golpear sigue visible y las ondas siguientes sí pueden golpearlo. El escudo mágico amortigua su daño.

**Pasiva (ralentización):** según cuántas ondas del mismo lanzamiento golpeen al objetivo: **-5 % / -10 % / -20 %** de velocidad de movimiento durante **3 s**. No se suma: se queda la más fuerte y cada impacto reinicia los 3 s.

**Medio (agua):** cuenta el punto de lanzamiento (agua o tierra, igual para todas sus ondas) y dónde está el objetivo al recibir cada onda.

| Lanzador → objetivo | Daño | Ralentización |
|---|---|---|
| Tierra → tierra | normal | -5 / -10 / -20 % |
| Agua → agua | **x2** (20 / 40 / 60) | **x2** (-10 / -20 / -40 %) |
| Cambio de medio (tierra ↔ agua) | **x0.5** (5 / 10 / 15) | **x0.5** (-2.5 / -5 / -10 %) |

La onda viaja a **300 px/s** y al **doble (600 px/s)** si se lanza desde el agua; el alcance no cambia.

| Nivel | Ondas | Radio | Coste En. | Recarga |
|---|---|---|---|---|
| 1 | 1 | 200 | 10 | 10 s |
| 5 | 1 | 242 | 15 | 14.2 s |
| 10 | 2 | 295 | 20 | 19.5 s |
| 15 | 2 | 347 | 25 | 24.7 s |
| 20 | 3 | 400 | 30 | 30 s |

Radio **200 → 400** y recarga **10 → 30 s** lineales (la recarga sube a propósito); coste **10 +5 cada 5 niveles** (máx. 30). Nivel máximo **20**. Tabla completa en `Tablas_Escalado.md` (2.12).

## 10. Puntos de empuje (retroceso)

Cada punto de **daño** aplica **1 punto de empuje** (retroceso) a quien lo recibe, alejándolo del atacante. Además, **quien genera el daño también retrocede** un poco al golpear: así un grupo de invocaciones no inflige todo su daño a la vez (daño explosivo en conjunto), sino **por intervalos**, al tener que reacercarse tras cada golpe (junto con su recarga de ataque de 1 s). El **Escudo** aplica 2 puntos de empuje a su propio portador al bloquear. La **quemadura** de la Carga de Fuego (1/s por 5 s) sigue preparada para el combate contra enemigos.

### 10.1 Maniquí de pruebas

En el centro del mapa hay un **maniquí**: **100 de vida** y **escudos físico y mágico de 50** (mismas reglas que los del personaje: reparto, regeneración y anulación por Cortar). No ataca, pero **recibe daño y desangrado** para probar las invocaciones y las habilidades. Muestra una **barra de vida** (roja mientras sangra) y encima sus dos escudos (verde físico, azul mágico; recuadro rojo si el mágico está anulado). Como no se mueve, muestra la ralentización recibida como texto (**"Vel -X%"**) junto a sus barras. Al recibir un golpe retrocede y luego **vuelve a su posición** (sigue siendo un blanco centrado); si lo destruyen, **reaparece a los 5 s** con la vida llena.

---

## 11. Interfaz

- **Pantalla de creación (a pantalla completa y adaptable):** se escala al tamaño de la pantalla (diseño base 1600x900, factor 0.6–1.6) y se reorganiza al ancho disponible: en pantallas anchas va en **dos columnas** (personaje, herramienta y estadísticas a la izquierda; habilidades a la derecha) y en estrechas en **una**. Las tarjetas se reparten en filas según quepan, los nombres largos reducen su fuente para no cortarse y, si el contenido no cabe en alto, aparece una **barra de desplazamiento** (rueda del ratón). El botón **Comenzar mundo** queda **fijo abajo**, siempre visible. [ESC] sale de pantalla completa y la interfaz se reacomoda sola. Contiene nombre, color con vista previa, y **tarjetas de selección** para la herramienta (una) y las habilidades (hasta 3). Las habilidades se agrupan **por categorías en columnas** (Artes de las Sombras, Potenciadores, Ataque Mágico, Defensa y Soporte, Especiales), pensado para escalar al añadir más. Cada tarjeta tiene un botón **[?]** que muestra su descripción en un recuadro; el texto de cada habilidad vive **solo** en ese **[?]**.
- **Panel izquierdo (en juego):** nivel y puntos, tarjeta del arma (nombre, nivel, daño, debuff/buff y barra de durabilidad) y la lista de estadísticas con su botón **[+]**: Vida, **Daño**, **Velocidad** (ya muestran el valor efectivo, sin filas separadas de base/actual), Energía, **Escudo** y **Escudo M.** (actual / máximo).
- **Panel derecho (en juego):** una tarjeta por habilidad con tecla, nivel, coste, estado, recarga y botón **[+]**.
- **Iconos de ayuda [?]:** en ambos paneles abren un tooltip con las explicaciones, manteniendo la interfaz despejada.
- **Indicadores de terreno:** avisan cuando estás en agua, en un lago profundo u oculto en un arbusto.

---

## 12. Controles

| Entrada | Acción |
|---|---|
| Clic izquierdo | Mover el personaje (o pulsar botones [+] y [?] de la interfaz) |
| [1] | Sacar / guardar la herramienta |
| [2] [3] [4] | Usar las habilidades equipadas (mantener pulsado para cargar la Carga de Fuego) |
| Mantener [2] [3] [4] | Poner esa invocación sombría en **modo combate** (ojos encendidos) |
| Clic derecho (en modo combate) | Enviar a las sombras a un punto o a perseguir y atacar al enemigo bajo el clic (la orden persiste al soltar la tecla) |
| Mantener y soltar [2] [3] [4] con una orden en curso | Devolver esa invocación al estado pasivo (te siguen) |
| Clic derecho junto a ti | Llamar de vuelta a las sombras (vuelven a seguirte) |
| [H] | Mostrar / ocultar las hitboxes |
| [L] | (Prueba) Subir de nivel al personaje (+3 puntos) |
| [J] | (Prueba) Simular un golpe del arma (desgasta durabilidad) |
| [ESC] | Salir del juego |

---

## 13. Pendiente (a futuro)

- Sistema de **enemigos y combate**, que activará el daño real del arma y las habilidades, el desgaste de la durabilidad, los puntos de empuje, la quemadura y una fuente de experiencia para subir de nivel sin teclas de prueba.
- La **segunda daga** de las Dagas Simples y los conejos ya pueden hacer daño cuando exista un objetivo.
- Mecánica adicional prevista a partir del **nivel 20** del personaje.
