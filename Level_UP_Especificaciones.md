# LEVEL_UP — Especificaciones de juego

> Documento de información (no técnico) sobre el estado actual del juego.
> Pensado como contexto de referencia para la IA y para el equipo.
> Actualizado: 16 de noviembre de 2026.

---

## 1. Resumen general

Level_UP es un juego 2D de vista cenital en el que controlas a un personaje dentro de un mundo circular. El personaje se mueve haciendo clic, explora el mapa, se enfrenta a terrenos con efectos (agua, lagos peligrosos), se esconde en la vegetación y mejora sus estadísticas, su arma y sus habilidades subiendo de nivel.

Actualmente el juego cuenta con la generación completa del mundo, el sistema de movimiento y cámara, un sistema de progresión por niveles con puntos de mejora, tres armas y tres habilidades, además de una interfaz con paneles de información a ambos lados de la pantalla. **El combate contra enemigos todavía no existe**: las zonas de daño (hitboxes) ya están preparadas para cuando se añada.

---

## 2. El mundo

- **Forma y tamaño:** mapa circular de radio 5000, rodeado por una franja oscura exterior que marca el límite.
- **Aparición:** el personaje aparece en el centro del mapa, dentro de una zona segura de 140 px sin obstáculos.
- **Cámara:** sigue al personaje con un movimiento suave, manteniéndolo centrado en el área de juego.
- **Fondo:** cuadrícula sutil recortada al círculo, con el borde y el centro del mundo marcados.

---

## 3. Terreno acuático: charcos y lagos

Cada mundo genera entre **4 y 6** masas de agua con forma de nube (un cuerpo central con varios lóbulos), con radios que van de **100 a 500**. No se solapan entre sí ni invaden la zona de aparición.

- **Agua normal:** reduce la velocidad de movimiento un **50 %** mientras estás sobre ella.
- **Lago profundo (peligroso):** si un lago supera un radio de **300**, su zona central (el 35 % interior, de tono azul más oscuro) se vuelve peligrosa: reduce la movilidad un **80 %** y resta **10 puntos de vida por segundo**. El resto del lago conserva el efecto normal de −50 %.

---

## 4. Rocas

Cada mundo genera entre **100 y 250** rocas. Son **sólidas**: no se pueden atravesar ni empujar, y además **bloquean los proyectiles** (las balas se destruyen al chocar con ellas). No aparecen sobre el agua, la vegetación ni la zona segura central.

| Tipo de roca | Proporción | Tamaño (px) |
|---|---|---|
| Pequeña | 60 % | 22 – 45 |
| Grande | 35 % | 70 – 130 |
| Gigante | 5 % | 150 – 300 |

---

## 5. Vegetación

Los arbustos tienen forma de nube y los **tres tipos se ven idénticos** a simple vista (misma mezcla de verdes), para que no se distinga su efecto hasta entrar. Su diámetro general va de **50 a 150 px** (los frutales, mínimo 50). Un personaje solo puede entrar y esconderse si su tamaño cabe en el arbusto; si no cabe, el arbusto actúa como **obstáculo sólido**. Al estar dentro, el personaje queda **oculto** (no se ve desde fuera y se oculta su nombre) y el mapa se oscurece.

### 5.1 Tipos de arbusto

| Tipo | Cantidad | Efecto |
|---|---|---|
| Escondite | 20 – 60 | Solo sirve para ocultarse. |
| Venenoso | 15 – 30 | Oculta, pero hace 1 de daño cada 2 s (ignora defensa). |
| Frutal | 5 – 10 | Oculta y contiene 1 – 5 orbes rojos; cada uno cura +2 de vida. |

### 5.2 Ciclo de los frutales

Cuando un frutal se queda sin orbes, desaparece y, **un minuto después**, reaparece en otro lugar pasando por tres fases de crecimiento:

1. **Brote:** aparece pequeño (20 px), sin fruta.
2. **Joven (tras 1 minuto):** crece a su tamaño normal con 1 sola fruta.
3. **Maduro (tras otro minuto):** pasa a tener su cantidad de frutas aleatoria (1 – 5) habitual.

### 5.3 Matorrales

Existe un **40 % de probabilidad** de que un mundo genere entre **1 y 3 matorrales**. Un matorral es un conjunto denso de **5 a 8 arbustos** de distintos tipos y tamaños, solapados entre sí de forma que forman una sola masa de vegetación sin huecos (como un gran arbusto).

---

## 6. El personaje

El personaje se mueve haciendo clic en el punto de destino; gira para mirar hacia donde se desplaza y sus ojos apuntan en esa dirección. Colisiona con rocas y arbustos sólidos, y no puede salir del límite circular del mapa.

### 6.1 Estadísticas iniciales (nivel 1, fijas)

Todos los personajes empiezan con las mismas estadísticas (**no hay aleatoriedad**):

| Estadística | Valor inicial | Mejora por punto |
|---|---|---|
| Vida | 20 | +2 |
| Fuerza | 2 | +0.2 |
| Velocidad | 1 | +0.1 |
| Defensa | 10 | +1 |
| Energía | 100 | +2 |
| Tamaño | 1 | — (estético) |

### 6.2 Significado de cada estadística

- **Vida:** puntos de vida; se recupera con los orbes de los frutales.
- **Fuerza:** base del daño del arma.
- **Velocidad:** rapidez de desplazamiento; cambia con el agua, el arma desenfundada y la habilidad Destello.
- **Defensa:** reduce el daño recibido.
- **Energía:** coste de las habilidades. Se regenera **+1 cada 3 s** estando quieto y **+1 cada 6 s** en movimiento.

---

## 7. Progresión y puntos de mejora

El personaje empieza con **3 puntos de mejora** y gana **3 puntos más por cada nivel** que sube. Esos puntos son un **recurso compartido**: se usan para mejorar las estadísticas, el arma o las habilidades mediante los botones **[+]** verdes de la interfaz. Esto obliga a repartir y evita subirlo todo al máximo.

- **Coste de cada mejora:** una estadística cuesta **1 punto**, una habilidad cuesta **1 punto** y el arma cuesta **2 puntos** por nivel.
- **Subir de nivel:** actualmente se hace con una tecla de prueba (ver controles); otorga los 3 puntos. En el futuro vendrá de la experiencia en combate.

---

## 8. Herramientas (armas)

El personaje lleva una herramienta principal que saca o guarda con la tecla **[1]**. Mientras está desenfundada reduce la velocidad (debuff) y permite hacer daño. Hay **tres espadas** a elegir en la creación del personaje. Todas tienen **nivel máximo 5** y, al alcanzarlo, la hoja toma un tono ligeramente dorado.

### 8.1 Comparativa de las tres espadas

| Arma | Nivel | Daño (×Fuerza) | Debuff velocidad | Durabilidad |
|---|---|---|---|---|
| Espada Ligera | 1 → 5 | ×2.2 → ×3.0 | −17 % → −5 % | 220 → 300 |
| Espada Larga | 1 → 5 | ×3.4 → ×5.0 | −34 % → −10 % | 190 → 230 |
| Mandoble | 1 → 5 | ×6.6 → ×9.0 | −70 % → −30 % | 148 → 180 |

> El daño se calcula sobre la **fuerza actual** del personaje, así que también se beneficia de la habilidad Burst de Fuerza.

### 8.2 Durabilidad y rotura

- **Desgaste:** cada golpe que hace daño gasta 1 punto de durabilidad.
- **Rotura:** si la durabilidad llega a 0, el arma se rompe, pierde todos los niveles conseguidos (vuelve a nivel 1) y queda inutilizable.
- **Reparación:** la única forma de repararla es **subirla de nivel**; al hacerlo recupera toda su durabilidad.

### 8.3 Diferencias estéticas de tamaño

El tamaño es **solo visual** (no cambia daño, debuff ni durabilidad):

- **Espada Ligera:** un 20 % más grande (base de referencia).
- **Espada Larga:** un 20 % más larga y un 10 % más ancha.
- **Mandoble:** un 20 % más largo y un 30 % más ancho.

---

## 9. Habilidades

El personaje equipa habilidades en las teclas **[2]**, **[3]** y **[4]**. Cada una consume energía y tiene un tiempo de recarga (cooldown). **Destello** y **Burst de Fuerza** suben de nivel (máximo 20) mejorando sus valores; **Disparo Veloz** no escala por ahora.

### 9.1 Destello (nivel 1 → 20)

| Parámetro | Nivel 1 → 20 |
|---|---|
| Buff de velocidad | +52 % → +90 % |
| Duración | 10 s → 18 s |
| Recarga (cooldown) | 5 s → 1 s |
| Debuff de fatiga al acabar | −20 % → 0 % |
| Coste de energía | 10 → 40 |

### 9.2 Burst de Fuerza (nivel 1 → 20)

| Parámetro | Nivel 1 → 20 |
|---|---|
| Buff de fuerza | +21 % → +40 % |
| Duración | 6 s → 10 s |
| Recarga (cooldown) | 12 s → 8 s |
| Coste de energía | 15 → 35 |

### 9.3 Disparo Veloz (no escala)

- **Efecto:** dispara una esfera de energía en línea recta (velocidad 10) con el **20 % del daño total** del personaje.
- **Coste:** 15 % de la energía máxima.
- **Recarga:** 2 s. No tiene duración activa (pasa directo a enfriamiento).

### 9.4 Regla de combo

Si lanzas una habilidad mientras otra sigue activa, se aplica un **sobrecosto del 5 % de la energía actual**.

---

## 10. Interfaz

- **Panel izquierdo (Ficha del personaje):** nivel y puntos disponibles, tarjeta del arma (nombre, nivel, daño, debuff y barra de durabilidad) y la lista de estadísticas con su botón **[+]** para mejorar.
- **Panel derecho (Habilidades):** una tarjeta por habilidad con su tecla, nivel, coste, estado, tiempo de recarga y su botón **[+]** para subir de nivel.
- **Iconos de ayuda [?]:** cada panel tiene un pequeño icono de interrogación; al pulsarlo se abre un recuadro con la explicación textual (qué hace cada estadística, reglas de habilidades, etc.), manteniendo la interfaz despejada.
- **Indicadores de terreno:** la interfaz avisa cuando estás en agua, en un lago profundo u oculto en un arbusto.

---

## 11. Controles

| Entrada | Acción |
|---|---|
| Clic izquierdo | Mover el personaje (o pulsar botones [+] y [?] de la interfaz) |
| [1] | Sacar / guardar la herramienta |
| [2] [3] [4] | Usar las habilidades equipadas |
| [H] | Mostrar / ocultar las hitboxes |
| [L] | (Prueba) Subir de nivel al personaje (+3 puntos) |
| [J] | (Prueba) Simular un golpe del arma (desgasta durabilidad) |
| [ESC] | Salir del juego |

---

## 12. Pendiente (a futuro)

- Sistema de **enemigos y combate**, que activará el daño real del arma y las habilidades, el desgaste de la durabilidad y una fuente de experiencia para subir de nivel sin teclas de prueba.
- Mecánica adicional prevista a partir del **nivel 20** del personaje.
