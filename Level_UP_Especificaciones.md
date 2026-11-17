# LEVEL_UP — Especificaciones de juego

> Documento de información (no técnico) sobre el estado actual del juego.
> Pensado como contexto de referencia para la IA y para el equipo.
> Actualizado: 16 de noviembre de 2026.

---

## 1. Resumen general

Level_UP es un juego 2D de vista cenital en el que controlas a un personaje dentro de un mundo circular. El personaje se mueve haciendo clic, explora el mapa, se enfrenta a terrenos con efectos (agua, lagos peligrosos), se esconde en la vegetación y mejora sus estadísticas, su arma y sus habilidades subiendo de nivel.

Actualmente el juego cuenta con la generación completa del mundo, el sistema de movimiento y cámara, un sistema de progresión por niveles con puntos de mejora, cinco armas y cinco habilidades, además de una interfaz con paneles de información a ambos lados de la pantalla. **El combate contra enemigos todavía no existe**: las zonas de daño (hitboxes), el sistema de puntos de empuje y los efectos como la quemadura ya están preparados para cuando se añada.

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

---

## 5. Vegetación

Los arbustos tienen forma de nube y los **tres tipos se ven idénticos** a simple vista. Diámetro **50 a 150 px** (frutales mín. 50). Un personaje solo entra y se esconde si cabe; si no cabe, el arbusto es un **obstáculo sólido**. Dentro, el personaje queda **oculto** y el mapa se oscurece.

### 5.1 Tipos de arbusto

| Tipo | Cantidad | Efecto |
|---|---|---|
| Escondite | 20 – 60 | Solo sirve para ocultarse. |
| Venenoso | 15 – 30 | Oculta, pero hace 1 de daño cada 2 s (ignora defensa). |
| Frutal | 5 – 10 | Oculta y contiene 1 – 5 orbes rojos; cada uno cura +2 de vida. |

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
- **Mágico:** el de las habilidades que consumen energía (Disparo Veloz, Carga de Fuego). Burst de Fuerza no cuenta como daño mágico: solo sube la fuerza, el golpe lo sigue dando el arma (físico).

Cada tipo lo amortigua su propio escudo del personaje:

| Escudo | Bloqueo del daño total | Reparto (escudo / vida) |
|---|---|---|
| Físico | 20 % | 70 % / 30 % |
| Mágico | 10 % | 90 % / 10 % |

El escudo absorbe su parte hasta agotarse; si esa parte supera el escudo disponible, el sobrante pasa también a la vida. Ambos escudos empiezan en **0**, se mejoran **+5 por punto hasta un máximo de 15** y luego **+2 por punto**, y **se regeneran +1 por segundo tras 10 s sin recibir ese tipo de daño** (cada uno con su propio contador). El daño de terreno (lago profundo, hierba venenosa) ignora los escudos y se aplica directo a la vida.

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

Se equipan en las teclas **[2]**, **[3]** y **[4]** (hasta 3 elegidas en la creación). Consumen energía y tienen recarga. Nivel máximo **20**.

### 9.1 Destello

Buff de velocidad **+52 % → +90 %**, duración **10 → 18 s**, recarga **5 → 1 s**, debuff de fatiga al acabar **−20 % → 0 %**, coste **10 → 40 En.**

### 9.2 Burst de Fuerza

Buff de fuerza **+21 % → +40 %**, duración **6 → 10 s**, recarga **12 → 8 s**, coste **15 → 35 En.**

### 9.3 Disparo Veloz

Esfera recta. Velocidad del proyectil **11 → 30**, daño **20.5 % → 30 %** del daño total, coste fijo **15 → 35 En.** (15 +5 cada 5 niveles), recarga **2 → 0.5 s**.

### 9.4 Invocar Conejos

Invoca **5 conejos** detrás del personaje (esferas verdes con cara `:3`). No se puede reinvocar hasta que todos mueran; con 2 o más vivos nacen **floor(vivos/2) cada 10 s**, hasta un máximo de **50**. Por conejo: Vida **5 → 20** (+3 cada 4 niveles), Velocidad **3 → 12.5**, Daño **0.1 → 7.7**. Coste fijo **80 En.**

### 9.5 Carga de Fuego

Esfera de fuego con **dos modos**: pulsar = disparo rápido; mantener la tecla hasta **5 s** = carga más daño y tamaño, y dispara al soltar. Daño base **20 → 39** (+1 por nivel). La carga añade daño (hasta **+25 %**) y sube el coste (15 sin carga → **45** a 5 s). Al golpear aplica **quemadura**: 1 de daño por segundo durante 5 segundos.

### 9.6 Regla de combo

Lanzar una habilidad mientras otra sigue activa cuesta un **+5 % de la energía actual**.

---

## 10. Puntos de empuje (mecánica de combate)

Sistema preparado para el combate futuro:

- Cada punto de **daño** que recibe un personaje u objeto le aplica **1 punto de empuje**, que lo hace retroceder una cantidad de píxeles.
- El **Escudo** aplica 2 puntos de empuje a su propio portador cada vez que lo golpean.
- La **quemadura** de la Carga de Fuego (1/s por 5 s) también está lista para aplicarse al impactar.

Como aún no hay enemigos, estas reglas están implementadas pero todavía no se disparan en la práctica.

---

## 11. Interfaz

- **Pantalla de creación (a pantalla completa):** nombre, color con vista previa, y **tarjetas de selección** para la herramienta (una) y las habilidades (hasta 3). Cada tarjeta tiene un botón **[?]** que muestra su descripción en un recuadro.
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
| [H] | Mostrar / ocultar las hitboxes |
| [L] | (Prueba) Subir de nivel al personaje (+3 puntos) |
| [J] | (Prueba) Simular un golpe del arma (desgasta durabilidad) |
| [ESC] | Salir del juego |

---

## 13. Pendiente (a futuro)

- Sistema de **enemigos y combate**, que activará el daño real del arma y las habilidades, el desgaste de la durabilidad, los puntos de empuje, la quemadura y una fuente de experiencia para subir de nivel sin teclas de prueba.
- La **segunda daga** de las Dagas Simples y los conejos ya pueden hacer daño cuando exista un objetivo.
- Mecánica adicional prevista a partir del **nivel 20** del personaje.
