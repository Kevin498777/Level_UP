# LEVEL_UP — Especificaciones de juego

> Documento de información (no técnico) sobre el estado actual del juego.
> Pensado como contexto de referencia para la IA y para el equipo.
> Actualizado: 23 de noviembre de 2026.

---

## 1. Resumen general

Level_UP es un juego 2D de vista cenital en el que controlas a un personaje dentro de un mundo circular. El personaje se mueve haciendo clic, explora el mapa, se enfrenta a terrenos con efectos (agua, lagos peligrosos), se esconde en la vegetación y mejora sus estadísticas, su arma y sus habilidades subiendo de nivel.

Actualmente el juego cuenta con la generación completa del mundo, el sistema de movimiento y cámara, un sistema de progresión por niveles con puntos de mejora, seis armas (cinco cuerpo a cuerpo y un **Arco** a distancia) y quince habilidades, además de una interfaz con paneles de información a ambos lados de la pantalla. El **combate con armas** ya funciona: con **[Espacio]** el personaje golpea según la **cadencia** de su arma (con el Arco, mantener carga y soltar dispara una flecha). En el centro del mapa hay un **maniquí de pruebas** (versión beta de enemigo): lleva una espada, **ataca** al personaje y a sus invocaciones, y **recibe el daño de todas las habilidades con daño**, del arma y de los efectos (desangrado, quemadura, inmovilización). Además, el mundo tiene **fauna** (ver 10.2): animales ambientales, pasivos que huyen, neutrales que reaccionan si los provocas y **hostiles que te cazan** (lobos en manada, osos y cocodrilos), que son los primeros enemigos reales con IA propia. Cazar animales da **experiencia** para subir de nivel (hasta el **20**) y, si mueres, **reapareces desde el nivel 1** en el mismo mundo (ver 7 y 7.1). El sistema de **puntos de empuje** (retroceso al dar o recibir daño) está activo.

---

## 2. El mundo

- **Forma y tamaño:** mapa circular de radio **10000**, rodeado por una franja oscura exterior que marca el límite.
- **Escalado con el tamaño:** las cantidades de **rocas y lagos** se calculan a partir del área del mundo. Su densidad se define para un mundo de referencia de radio 5000 y se multiplica por (radio / 5000)²; con radio 10000 el factor es **×4**. Si el mundo vuelve a cambiar de tamaño, se ajustan solas.
- **Biomas:** **bosques** (árboles densos, arbustos y pasto de sotobosque), **praderas** (pasto y flores) y **pastizales de pasto alto** (donde están las madrigueras de los conejos), repartidos por todo el mapa (ver 5).
- **Aparición:** el personaje aparece en el centro del mapa, dentro de una zona segura de 140 px sin obstáculos.
- **Cámara:** sigue al personaje con un movimiento suave, manteniéndolo centrado en el área de juego.
- **Fondo:** cuadrícula sutil recortada al círculo, con el borde y el centro del mundo marcados.

---

## 3. Terreno acuático: charcos y lagos

Cada mundo genera entre **24 y 40** masas de agua con forma de nube (6 – 10 por área de referencia ×4), con radios de **150 a 750**. No se solapan entre sí ni invaden la zona de aparición.

- **Flora acuática:** cada lago trae **nenúfares** (algunos con flor blanca o rosa) sobre el agua y **juncos/espadañas** en la orilla. Es solo decorativa. Es la **única** flora que crece en los lagos: el pasto y las flores de pradera nunca aparecen sobre el agua ni sobre el barro de la orilla.

- **Agua normal:** reduce la velocidad de movimiento un **50 %**.
- **Lago profundo (peligroso):** si un lago supera un radio de **300**, su zona central (el 35 % interior, azul más oscuro) reduce la movilidad un **80 %** y resta **10 puntos de vida por segundo**. El resto del lago conserva el −50 %.

---

## 4. Rocas

Cada mundo genera entre **600 y 1200** rocas (150 – 300 por área de referencia ×4). Son **sólidas** (no se atraviesan ni se empujan) y **bloquean los proyectiles**. No aparecen sobre el agua, los arbustos, los troncos de los árboles ni la zona segura. El pasto y las flores que quedarían debajo de una roca se retiran.

| Tipo de roca | Proporción | Tamaño (px) |
|---|---|---|
| Pequeña | 60 % | 22 – 45 |
| Grande | 35 % | 70 – 130 |
| Gigante | 5 % | 150 – 300 |

La habilidad **Cortar** puede destruir rocas pequeñas y grandes; las gigantes solo a nivel 20 (ver 9.14).

---

## 5. Vegetación

Los arbustos tienen forma de nube y los **tres tipos se ven idénticos** a simple vista. Diámetro **50 a 150 px** (frutales mín. 50). Un personaje solo entra y se esconde si cabe; si no cabe, el arbusto es un **obstáculo sólido**. Dentro, el personaje queda **oculto** y el mapa se oscurece. **Oculto, los enemigos no lo detectan**: no lo miran ni inician ataques contra él (lo que lo toque sí le hace daño), igual que con Paso 0 (ver 9.17).

### 5.1 Tipos de arbusto

| Tipo | Cantidad | Efecto |
|---|---|---|
| Escondite | 110 – 210 | Solo sirve para ocultarse. |
| Venenoso | 60 – 110 | Oculta, pero hace 1 de daño cada 2 s (ignora defensa). |
| Frutal | 20 – 32 | Oculta y contiene 1 – 5 orbes rojos; cada uno cura +2 de vida. |

El **70 %** de los arbustos se genera dentro de los bosques (vegetación agrupada).

### 5.2 Ciclo de los frutales

Al quedarse sin orbes, el frutal desaparece y **un minuto después** reaparece en **otro lugar libre** (a más de 300 px del personaje), pasando por tres fases: **brote** (20 px, sin fruta) → **joven** (tamaño normal, 1 fruta, tras 1 min) → **maduro** (frutas aleatorias 1–5, tras otro minuto). Nunca reaparece encima de una roca, un lago, un tronco u otro arbusto. El espacio de un frutal consumido, o de una roca, arbusto o árbol destruido con Cortar, queda libre para futuras reapariciones.

### 5.3 Matorrales

Un **40 % de probabilidad** por mundo genera entre **1 y 3 matorrales**: conjuntos densos de 5 a 8 arbustos de distintos tipos y tamaños, solapados como una sola masa de vegetación.

### 5.4 Bosques y árboles

Cada mundo tiene **10 – 16 bosques** (zonas circulares de radio 500 – 1600) donde los árboles crecen densos, más unos **20 árboles solitarios** repartidos por el mapa (en total, unos 750 – 1100 árboles).

| Tipo de árbol | Proporción | Aspecto |
|---|---|---|
| Frondoso | 55 % | Copa redonda verde claro. |
| Pino | 35 % | Copa verde oscuro con radios marcados. |
| Seco | 10 % | Sin copa: solo ramas marrones. |

- **Tamaño:** escala 1.0 – 1.9; copa de radio 34 – 65 y tronco de radio 7 – 13.
- **Tronco sólido:** el personaje y las criaturas chocan con él. La **copa** es solo visual y puede solaparse con la de otros árboles (bosque tupido).
- **Profundidad:** la sombra y el tronco se dibujan **debajo** de las entidades; las copas, **encima de todo**, incluidos los arbustos (los arbustos quedan bajo los árboles).
- **Copa transparente:** si **cualquier entidad** (personaje, maniquí, invocaciones o animales con cuerpo sólido) está bajo una copa, aunque sea en parte, esa copa se vuelve **semitransparente** para que se vea. Bajo un árbol **no te escondes**: para ocultarse están los arbustos.
- **Cortar** destruye un árbol al tocar **cualquier parte** (la copa), a cualquier nivel (ver 9.14).

### 5.5 Praderas: pasto y flores

Cada mundo tiene **8 – 14 praderas** (zonas de radio 600 – 1800) cubiertas de **pasto** (hierba de altura media) y **flores** de varios colores (20 – 60 por pradera). En los bosques también crece pasto, más ralo (sotobosque).

- **Pasto alto:** además hay **8 – 12 pastizales** (zonas de radio 300 – 700) de hierba más alta (×1.8 – ×2.8 del tamaño normal). Es el bioma de las **madrigueras de conejos** (ver 10.2).
- Son **decorativos**: sin colisión y dibujados **bajo las entidades**, así que nunca tapan al personaje.
- **No crecen en los lagos** ni en su orilla (ahí solo hay flora acuática, ver 3), ni debajo de las rocas. Esto vale también para el pasto alto.

---

## 6. El personaje

Se mueve haciendo clic; gira hacia donde se desplaza. Colisiona con rocas y arbustos sólidos y no sale del límite del mapa.

### 6.1 Estadísticas iniciales (nivel 1, fijas)

| Estadística | Valor inicial | Mejora por punto |
|---|---|---|
| Vida | 20 | +2 |
| Fuerza (Daño) | 2 | +0.2 |
| Velocidad | 1 | +0.1 |
| Cadencia (bonus) | +0 golpes/s | +0.1 golpes/s |
| Escudo (físico) | 0 | +5 hasta 15, luego +2 |
| Escudo mágico | 0 | +5 hasta 15, luego +2 |
| Energía | 100 | +5 |
| Tamaño | 1 | — (estético) |

### 6.2 Significado de cada estadística

- **Vida:** puntos de vida; se recupera con los orbes de los frutales.
- **Fuerza (Daño):** base del golpe del arma; en el panel de mejora se muestra como **Daño**. Sube con la habilidad Burst de Fuerza.
- **Velocidad:** desplazamiento; cambia con el agua, el arma desenfundada y la habilidad Destello.
- **Cadencia:** golpes por segundo del arma. La cadencia real es la del arma (según su nivel) **más** este bonus del personaje (ver 8.5).
- **Escudo (físico):** reserva que absorbe el **daño físico** (armas e invocaciones). Se gasta al recibir golpes y se regenera.
- **Escudo mágico:** reserva que absorbe el **daño mágico** (habilidades que consumen energía). Se gasta y regenera igual que el físico.
- **Energía:** coste de las habilidades. Regenera **+1 cada 3 s** quieto y **+1 cada 6 s** en movimiento.

### 6.3 Tipos de daño y escudos

El daño se divide en dos tipos:

- **Físico:** el de las herramientas (espadas, dagas, mandoble, las flechas del Arco y también la espada del maniquí) y las invocaciones (conejos y lobos).
- **Mágico:** el de las habilidades que consumen energía (Disparo Veloz, Carga de Fuego, Aura Eléctrica, Cortar, Onda Sonora, el veneno de Disparo Venenoso). Burst de Fuerza no cuenta como daño mágico: solo sube la fuerza, el golpe lo sigue dando el arma (físico).

Cada tipo lo amortigua su propio escudo del personaje:

| Escudo | Bloqueo del daño total | Reparto (escudo / vida) |
|---|---|---|
| Físico | 20 % | 70 % / 30 % |
| Mágico | 10 % | 90 % / 10 % |

El escudo absorbe su parte hasta agotarse; si esa parte supera el escudo disponible, el sobrante pasa también a la vida. El **bloqueo y el reparto solo existen si ese escudo tiene al menos 1 punto**: sin escudo (o con el mágico anulado por Cortar) el daño llega **entero** a la vida. Ambos escudos empiezan en **0**, se mejoran **+5 por punto hasta un máximo de 15** y luego **+2 por punto**, y **se regeneran +1 por segundo tras 10 s sin recibir ese tipo de daño** (cada uno con su propio contador). El daño de terreno (lago profundo, hierba venenosa) ignora los escudos y se aplica directo a la vida.

**Anulación del escudo mágico (pasiva de Cortar):** el escudo absorbe el golpe con las reglas normales y, si el golpe llegó a hacer daño, el escudo restante queda **anulado 8 s**: se muestra en 0, no absorbe nada (el daño mágico va directo a la vida) y no se regenera. Al terminar **vuelve al valor que le quedó tras el golpe** (ej. 100 → el corte lo deja en 25 → 0 durante 8 s → vuelve a 25). Otro corte durante la anulación reinicia los 8 s. En el panel se ve como **ANULADO**.

Si el **Reforzamiento Mágico** está activo, su campo de fuerza recibe primero cualquier daño físico o mágico; solo lo que sobra cuando se rompe llega a los escudos y a la vida (ver 9.7).


### 6.4 Autoapuntado

Con el **clic derecho sobre un enemigo** (sin mantener la tecla de una invocación) el personaje lo **fija como objetivo** y se queda **mirándolo siempre**, aunque se mueva con el clic izquierdo (camina de lado). Como golpes, flechas y disparos salen hacia donde mira, todos van hacia el objetivo, aunque **no lo persiguen**: van al punto donde estaba al disparar.

- **Activación:** solo sobre un enemigo a **500 o menos** de distancia. **No se puede activar mientras se mantiene una carga**: Carga de Fuego cargando o el Arco tensando (aviso "No puedes autoapuntar mientras cargas"). Con una invocación en modo combate (su tecla mantenida) el clic derecho da órdenes a las sombras, no autoapunta. La curación mantenida (Regeneración Inversa) no lo impide. **Una vez activo sí se puede cargar.**
- **Debuff:** **−40 % de velocidad** mientras está activo; se suma a los demás modificadores (arma, agua…), con el mínimo de velocidad de siempre.
- **Se desactiva:** con otro clic derecho en **terreno libre** o sobre **el mismo objetivo**, si el objetivo **muere**, si te alejas **más de 500** o si el objetivo **deja de estar al alcance** (animales: zorro invisible por su Paso 0, oso dentro de su cueva, cocodrilo sumergido o conejo escondido en la madriguera). Un clic derecho sobre **otro enemigo** cambia de objetivo.
- **Cómo se ve:** **mira roja** sobre el objetivo y el aviso **"AUTOAPUNTADO: -40% Vel"** en la barra inferior. No se muestra la distancia: la calcula el jugador.
- **Con el Escudo:** el arco de bloqueo mira siempre al objetivo, así que bloquea sus golpes de frente (la espalda sigue expuesta).
---

## 7. Progresión y puntos de mejora

El personaje empieza con **3 puntos de mejora** y gana **3 por cada nivel**. Son un **recurso compartido** para mejorar estadísticas, arma o habilidades con los botones **[+]** verdes.

- **Coste:** una estadística cuesta **1 punto**, una habilidad **1 punto** y el arma **2 puntos** por nivel.
- **Subir de nivel:** con **experiencia (XP)** al cazar animales (tú o tus sombras). Nivel máximo **20**; llegar a él cuesta **1048 XP**, pensado para unas **2 horas** de juego. Al subir, la XP vuelve a 0 más lo que sobró. La tecla de prueba **[L]** sigue subiendo un nivel. Tablas de XP por nivel y por animal en `sistema_xp.md`.

| Animal | XP | Monedas (probabilidad) |
|---|---|---|
| Conejo salvaje | 0.5 | 1 (5 %) |
| Venado | 2 | 1 – 2 (25 %) |
| Zorro | 3 | 1 – 3 (40 %) |
| Jabalí | 5 | 2 – 5 (70 %) |
| Lobo / lobo alfa | 5 / 8 | 5 – 10 / 7 – 10 (100 %) |
| Cocodrilo | 10 | 6 – 12 (100 %) |
| Oso | 15 (+2 al recoger el orbe de su cueva) | 8 – 12 (100 %) |
| Manada completa, alfa incluido (bono) | +3 | — |

- **Monedas:** al matar un animal puede soltar monedas según la tabla; se suman al momento ("+X monedas"). **Por ahora no se gastan** y se pierden al morir.
- Lo que cazan los depredadores salvajes no da XP ni monedas, y el maniquí tampoco.

### 7.1 Muerte

Si la vida llega a **0**, el mundo se congela tras un aviso **"HAS MUERTO"** con **Reaparecer [R]** y **Volver al menú principal [M]**. Al reaparecer vuelves al **centro** desde cero: nivel 1, XP 0, **sin monedas**, 3 puntos, estadísticas iniciales, arma y habilidades a nivel 1 (en las mismas teclas), vida y energía llenas; tus **sombras desaparecen**. El **mundo sigue igual** (solo se genera uno nuevo al crear otra partida).

---

## 8. Herramientas (armas)

Se saca o guarda con la tecla **[1]** y se golpea con **[Espacio]** (ver 8.5; el Arco carga y dispara, ver 8.6). Desenfundada reduce la velocidad. Hay **seis** a elegir en la creación. Nivel máximo **5**; al alcanzarlo, la hoja toma un tono dorado.

### 8.1 Comparativa

| Arma | Nivel | Daño (×Fuerza) | Debuff velocidad | Durabilidad | Cadencia (golpes/s) | Empuje |
|---|---|---|---|---|---|---|
| Espada Ligera | 1 → 5 | ×2.2 → ×3.0 | −17 % → −5 % | 220 → 300 | 1.475 → 1.775 | 8 |
| Espada Larga | 1 → 5 | ×3.4 → ×5.0 | −34 % → −10 % | 190 → 230 | 1.06 → 1.30 | 12 |
| Mandoble | 1 → 5 | ×6.6 → ×9.0 | −70 % → −30 % | 148 → 180 | 0.64 → 0.80 | 20 |
| Dagas Simples | 1 → 5 | ×1.5 → ×2.5 | −20 % → **+10 % (buff)** | 150 → 400 (compartida) | 2.125 → 2.625 | 4 |
| Escudo | 1 → 5 | — (bloquea, ver 8.2) | −34 % → −10 % | 100 → 300 | — | 40 (al bloquear) |
| Arco | 1 → 5 | ×5.0 → ×10.0 (según la carga) | −15 % → −3 % | 100 → 150 | — (carga, ver 8.6) | 25 |

> El daño se calcula sobre la **fuerza actual**, así que también se beneficia de Burst de Fuerza.

### 8.2 Particularidades

- **Dagas Simples:** son **dos** hojas (una por flanco), más pequeñas; a **nivel máximo** su debuff se convierte en un **buff de +10 %** de velocidad. Las dos comparten la misma durabilidad.
- **Escudo:** no inflige daño, **protege**.
  - **Bloqueo (desenfundado):** su hitbox es un **arco frontal de 120°** (60° a cada lado de hacia donde mira el portador) y el escudo **se dibuja como una banda curva que ocupa exactamente ese arco**, así se ve dónde bloquea. Lo que llega por ese arco se **bloquea entero**: golpes de arma, proyectiles y mordidas, físicos o mágicos, incluidos los ataques de la **fauna** (embestida del jabalí, mordidas de zorro, lobo y cocodrilo y zarpazo del oso, que entonces tampoco desangra ni resta el 30 % extra al escudo). El portador no recibe daño ni efectos (un ataque bloqueado no aplica efectos). Solo bloquea desenfundado, que es cuando aplica su debuff de velocidad. Con [H] se marca el arco sobre el dibujo.
  - **Desgaste:** pierde de durabilidad el daño bloqueado **menos su reducción**: **20 %** a nivel 1 → **70 %** a nivel 5 (lineal). Ej.: a nivel 5, un golpe de 100 le quita 30 de durabilidad. Cada bloqueo **empuja al portador** 2 puntos.
  - **Empuje al bloquear:** cada vez que recibe un golpe, el escudo **repele al atacante con 40 puntos de empuje**, más que cualquier arma (el mayor es el Arco con 25). Contra una espada funciona como un choque: el golpe no hace daño y el arma atacante pierde 1 de durabilidad.
  - **No bloquea:** la Onda Sonora, el Aura Eléctrica, el daño de terreno, el autodaño (Aura Eléctrica, autoveneno de Golpe de Suerte) ni los efectos ya aplicados (quemadura, veneno, desangrado), que siguen haciendo daño.
  - **Pasiva:** mientras sea la herramienta del personaje y **no esté roto** (enfundado o no), sube los **máximos** de escudo físico y mágico un **15 %** (nivel 1) → **30 %** (nivel 5) de su base. Es un porcentaje: con 0 de escudo sigue en 0. Si el escudo se rompe, el bonus desaparece hasta repararlo.

### 8.3 Durabilidad y rotura

- **Desgaste:** cada golpe que hace daño gasta 1 punto de durabilidad, y cada **choque de armas** gasta 1 punto a cada arma (ver 8.5).
- **Rotura:** al llegar a 0, el arma se rompe, pierde todos los niveles (vuelve a nivel 1) y queda inutilizable.
- **Reparación:** la única forma de repararla es **subirla de nivel**; recupera toda su durabilidad.

### 8.4 Diferencias estéticas de tamaño

Solo visual: Espada Ligera 20 % más grande; Espada Larga 20 % más larga y 10 % más ancha; Mandoble 20 % más largo y 30 % más ancho.

### 8.5 Golpe con el arma (combate cuerpo a cuerpo)

- **Golpear:** con el arma desenfundada (y sin romper), **[Espacio]** lanza un golpe. **Mantener [Espacio]** encadena golpes seguidos al ritmo de la cadencia. El Escudo no golpea.
- **Animación:** la hoja barre un **arco** (de 70° a −40°) durante **0.18 s**, con un destello blanco en el filo. La **hitbox del arma está activa durante toda la animación**, y cada golpe solo puede dañar **una vez** a cada enemigo.
- **Cadencia:** golpes por segundo = cadencia del arma (sube con su nivel) **+** bonus de cadencia del personaje (+0.1 por punto). El tiempo entre golpes es 1 / cadencia. El panel izquierdo muestra la cadencia real.
- **Al acertar en el cuerpo:** hace el daño del arma (físico, Fuerza × multiplicador), gasta 1 de durabilidad y **empuja** al enemigo con los puntos de empuje fijos del arma (dagas 4, ligera 8, larga 12, mandoble 20).
- **Choque de armas:** si durante el golpe tu hoja toca la espada del enemigo, **chocan**: ambos salen repelidos con la misma fuerza (la mayor de los empujes de las dos armas), las **dos armas pierden 1 de durabilidad** y ese golpe ya no daña el cuerpo. El choque tiene **prioridad** sobre el golpe al cuerpo.

### 8.6 Arco (daño físico a distancia)

Arma de **daño físico** que dispara **flechas de energía** (la energía es solo su aspecto y lo que cuesta comprarlas; el daño es físico y lo amortigua el escudo físico). No golpea cuerpo a cuerpo y no tiene hitbox de hoja, así que **no choca** con las espadas.

- **Cargar y disparar:** con el arco desenfundado, **mantén [Espacio]** para tensar la cuerda y **suelta** para disparar hacia donde mira el personaje. Cuentan los **segundos completos** de carga:

| Carga | Alcance | Daño (% del daño del arma) |
|---|---|---|
| menos de 1 s | — (no dispara ni gasta flecha, para evitar el spam) | — |
| 1 s | 100 | 20 % |
| 2 s | 150 | 40 % |
| 3 s | 200 | 60 % |
| 4 s | 250 | 80 % |
| 5 s o más | 300 | **100 %** (se queda al máximo hasta soltar) |

- **Moverse cargando:** se puede, con una ralentización extra de **−10 %** de velocidad mientras se tensa (se suma al debuff del arma). Guardar el arco cancela la carga.
- **La flecha:** el daño se calcula al soltar (Fuerza actual × multiplicador × % de la carga). Se detiene en el **primer enemigo** que toca: le hace el daño físico, lo **empuja 25 puntos** y gasta **1 de durabilidad** del arco. Las **rocas la bloquean** (desaparece) y **atraviesa los arbustos** sin romperlos. Si no choca con nada, se queda **clavada** al final de su alcance **3 s** solo como ambientación (ya no hace daño).
- **Carcaj y compra de flechas:** el arco empieza con el carcaj lleno. Las flechas se compran en **lotes de 10** con energía, con **[R]** o con el botón del panel izquierdo. Las que **no caben se pierden** y la energía se cobra entera (ej. con 9 de 10 y comprando 10, solo se suma 1). No se puede comprar con el carcaj lleno ni sin energía suficiente. Si el arco **se rompe**, vuelve a nivel 1 y el carcaj se reduce a 10.

| Nivel | Daño (×Fuerza) | Daño con Fuerza 2 (5 s) | Debuff velocidad | Durabilidad | Carcaj | Lote de 10 flechas |
|---|---|---|---|---|---|---|
| 1 | ×5.0 | 10 | −15 % | 100 | 10 | 10 En. |
| 2 | ×6.25 | 12.5 | −12 % | 110 | 15 | 15 En. |
| 3 | ×7.5 | 15 | −9 % | 120 | 20 | 20 En. |
| 4 | ×8.75 | 17.5 | −6 % | 130 | 25 | 25 En. |
| 5 | ×10.0 | 20 | −3 % | 150 | 30 | 30 En. |

El coste del lote **sube** con el nivel a propósito. **Aspecto:** arco de madera delante del personaje; la cuerda se tensa según la carga y muestra la flecha cian encajada. En el panel izquierdo se ven las flechas (x / carcaj), la carga actual (alcance y %) con su barra, y el botón de compra (gris si no se puede).

---

## 9. Habilidades

Se equipan en las teclas **[2]**, **[3]** y **[4]** (hasta 3 elegidas en la creación). Consumen energía y tienen recarga. Nivel máximo **20** (Regeneración Inversa y Paso 0: **10**).

### 9.1 Destello

Buff de velocidad **+52 % → +90 %**, duración **10 → 18 s**, recarga **5 → 1 s**, debuff de fatiga al acabar **−20 % → 0 %**, coste **10 → 40 En.**

### 9.2 Burst de Fuerza

Buff de fuerza **+21 % → +40 %**, duración **6 → 10 s**, recarga **12 → 8 s**, coste **15 → 35 En.**

### 9.3 Disparo Veloz

Esfera recta **muy rápida**: su punto fuerte es la velocidad del proyectil, **14 → 40** (lineal, la más alta del juego). Daño mágico **fijo 8 → 30** (lineal; ya no depende del arma), coste fijo **15 → 35 En.** (15 +5 cada 5 niveles), recarga **2 → 0.5 s**. Se detiene en el **primer enemigo** que toca (daño mágico) o en las rocas (se comprueba su trayecto en cada frame para que no salte rocas pequeñas).

### 9.4 Invocar Conejos

Invoca **5 conejos** detrás del personaje (esferas verdes con cara `:3`). No se puede reinvocar hasta que todos mueran; con 2 o más vivos nacen **floor(vivos/2)** cada **10 s × (1 + vivos / 10)** (más lento cuantos más hay: 15 s con 5 vivos, 30 s con 20), hasta un máximo de **50** (de 5 a 20 conejos en ~77 s; a 50 en ~3.5 min). Por conejo: Vida **5 → 20** (+3 cada 4 niveles), Velocidad **3 → 12.5**, Daño **0.1 → 7.7**. Coste fijo **80 En.** Al morir todos, **30 s de recarga** antes de reinvocar. Se les puede poner en **modo combate** (ver 9.11).

### 9.5 Carga de Fuego

Esfera de fuego con **dos modos**: pulsar = disparo rápido; mantener la tecla hasta **5 s** = carga más daño y tamaño, y dispara al soltar. Daño base **20 → 39** (+1 por nivel). Se detiene en el **primer enemigo** que toca y le aplica **quemadura**: 1 de daño por segundo (**ignora escudos**, como el desangrado). Cada segundo completo de carga cambia el daño, el tamaño, la quemadura y la recarga:

| Carga | Daño (× base) | Nv 1 | Nv 20 | Quemadura | Recarga |
|---|---|---|---|---|---|
| Toque | ×0.6 | 12 | 23.4 | 2 s | 8 s |
| 1 s | ×0.8 | 16 | 31.2 | 3 s | 9.4 s |
| 2 s | ×1.0 | 20 | 39 | 4 s | 10.8 s |
| 3 s | ×1.3 | 26 | 50.7 | 5 s | 12.2 s |
| 4 s | ×1.6 | 32 | 62.4 | 6 s | 13.6 s |
| 5 s | ×2.0 | 40 | 78 | 7 s | 15 s |

**No es acumulable**: reaplicarla reinicia la duración y se queda con el mayor daño por segundo. El enemigo quemado muestra un **anillo naranja**.

La energía se gasta **en tiempo real**: al pulsar se cobran 15 y cada segundo completo de carga cobra su parte (+5, +5, +5, +5 y +10; 45 en total a 5 s). Si no queda energía para el siguiente segundo, la carga se detiene en el nivel ya pagado y dispara con él al soltar.

### 9.6 Aura Eléctrica

Aura de 100 px de radio que sigue al personaje. Buff de velocidad **+5 % → +15 %** y **1 → 5** de daño mágico por segundo a cada enemigo dentro del aura (lo amortigua su escudo mágico). Mientras está activa, el portador recibe **0.5 de daño mágico por segundo** (lo amortigua su escudo mágico). Duración **10 → 20 s**, recarga **40 → 60 s**, coste **20 → 58 En.** (+2 por nivel).

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

Al lanzarla otorga un **resultado aleatorio**: Burst de Fuerza, Destello, Reforzamiento Mágico, Regeneración Inversa, Aura Eléctrica o **Paso 0** (como efecto temporal, sin coste extra), **energía al máximo**, **escudos al máximo** (físico y mágico), **Disparo Venenoso** o **nada**. "Nada" tiene un **30 %** y los otros **9** resultados se reparten el resto a partes iguales (**≈7.78 %** cada uno); en **nivel 20** "nada" baja al **5 %** y el resto se reparte igual (**≈10.56 %** cada uno).

**Disparo Venenoso es un resultado negativo:** no dispara nada; **envenena al portador** con el veneno del nivel que marca el tramo, pero a la **mitad del daño** y con la **misma duración** (ej. tramo nv1: 10 de daño en 20 s; nv20: 20 de daño en 10 s). Es daño mágico, así que lo amortigua su escudo mágico. Cuenta como resultado instantáneo (espera básica). Paso 0 otorgado no pasa de su nivel máximo (10).

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

Invocación **mágica** (segunda de las 10 Artes de las Sombras): la habilidad gasta energía, pero las **mordidas de los lobos hacen daño físico** (las amortigua el escudo físico del objetivo). Invoca **3 lobos** detrás del personaje (cuerpo gris con orejas y ojos rojos). No se puede reinvocar hasta que mueran todos; al morir el último hay **30 s de recarga**. Cada golpe tiene un **33 %** de aplicar **desangrado** al objetivo: recibe **5 golpes de 1 de vida, uno cada 2 s** (ignora escudos). Se cuenta **por golpes, no por tiempo**, así el daño total es siempre 5 sin importar los FPS. El efecto sigue **activo hasta que cae el último golpe** y mientras dura reduce **toda curación un 50 %**. **No es acumulable**: reaplicarlo solo reinicia los 5 golpes.

| Nivel | Vida | Velocidad | Daño | Coste En. |
|---|---|---|---|---|
| 1 | 10 | 10 | 8 | 90 |
| 5 | 22 | 12 | 12.6 | 90 |
| 10 | 37 | 14 | 18.4 | 90 |
| 15 | 52 | 16 | 24.2 | 90 |
| 20 | 67 | 18 | 30 | 90 |

La vida sube **+3 por nivel**, la velocidad **+2 cada 5 niveles** y el daño escala de forma lineal de **8 a 30** (nivel 1 a 20). Coste fijo **90 En.** Nivel máximo **20**. **Ordenar el ataque** a un enemigo en modo combate (clic derecho sobre él) cuesta **5 En.** (nivel 1) → **10 En.** (nivel 20); sin energía suficiente la orden no se da (ir a un punto o llamarlos es gratis). Tabla completa en `Tablas_Escalado.md` (2.10).

No confundir con los **lobos salvajes** de la fauna (ver 10.2), que son enemigos.

### 9.12 Modo combate (invocaciones sombrías)

Conejos, lobos y la araña (ver 9.16) comparten el **modo combate**. Con la invocación ya activa, **mantener su tecla** ([2], [3] o [4]) las pone en guardia (se les **encienden los ojos** al instante). Mientras mantienes la tecla, el **clic derecho** da la orden:

- **Clic derecho sobre un enemigo** (p. ej. el maniquí): lo fijan como objetivo y lo **persiguen aunque se mueva**, atacándolo hasta que muera. Al morir el objetivo vuelven a seguirte.
- **Clic derecho en terreno libre**: van a ese punto.
- **Clic derecho junto a ti**: las llama de vuelta (vuelven a seguirte).

La orden **persiste aunque sueltes la tecla**, así conservas tu movilidad (el **clic izquierdo** sigue moviendo solo a tu personaje) mientras las sombras siguen atacando. Con una orden en curso, **volver a mantener la tecla y soltarla sin dar otra orden** las devuelve al **estado pasivo** (te siguen); si mientras la mantienes das otra orden con el clic derecho, se queda la nueva. Atacan **por intervalos** (1 golpe/s por criatura) y, por el retroceso al golpear (ver sección 10), no apilan todo su daño de golpe.

Los conejos tienen la cara `:3` con los **ojos rojos**, que en modo combate brillan con un halo. La araña es la excepción: el clic derecho **siempre la manda a un punto** (no persigue enemigos).

### 9.13 Cuerpos sólidos (sin solapamientos)

El personaje, el maniquí, las invocaciones y los **animales con cuerpo** de la fauna (conejos fuera de la madriguera, venados, jabalíes, zorros visibles, lobos, osos fuera de la cueva y cocodrilos emergidos) tienen **hitbox circular** (su radio): pueden **recibir daño** y **no se solapan** entre sí. Al chocar se separan según su **masa**: araña 0.6, conejo 1, lobo 3, personaje 100 (sus invocaciones apenas lo desplazan) y maniquí fijo (nada lo mueve, salvo su propio retroceso). Con [H] se ven las hitboxes del maniquí y de las invocaciones (círculos magenta).

### 9.14 Cortar

Habilidad de **daño mágico** (categoría Ataque Mágico). Lanza hacia donde mira el personaje una **cuchilla delgada** en línea recta, del largo aproximado de la Espada Ligera, **negra con contorno rojo**. Sale desde el centro del personaje (se hace visible al salir de su cuerpo) y se detiene en lo primero que toque:

- **Enemigo:** se detiene en el **primero**. Hace su daño mágico (lo amortigua el escudo mágico) y, si llega a hacer daño, **anula su escudo mágico 8 s** (ver 6.3).
- **Roca o arbusto:** lo **destruye** y la cuchilla se rompe con él (**solo un objeto** por cuchilla). Las **rocas gigantes** y los **arbustos grandes** (más de 100 de diámetro) solo se destruyen a **nivel 20**; antes, la cuchilla se rompe y el objeto queda intacto. Si hay arbustos solapados (matorral), corta el más cercano.
- **Árbol:** lo **destruye al tocar cualquier parte** (incluida la copa), **a cualquier nivel**, y la cuchilla se rompe con él.
- Los objetos destruidos **no reaparecen** (tampoco los frutales) y, si estabas escondido en un arbusto que se destruye, quedas a la vista. **Lanzada desde dentro de un arbusto**, la cuchilla sale de dentro hacia afuera **sin cortarlo** (sí corta el siguiente objeto de su camino).

| Nivel | Daño | Velocidad | Coste En. | Recarga |
|---|---|---|---|---|
| 1 | 5 | 5 | 15 | 2 s |
| 5 | 12.4 | 9 | 23 | 4 s |
| 10 | 21.6 | 14 | 33 | 6 s |
| 15 | 30.8 | 19 | 43 | 8 s |
| 19 | 38.2 | 23 | 51 | 8 s |
| 20 | 40 | 24 | 53 | 10 s |

Daño **5 → 40** lineal (redondeado a 1 decimal), velocidad **5 +1 por nivel**, coste **15 +2 por nivel** y recarga **2 s +2 s cada 5 niveles** (sube a propósito). Nivel máximo **20**. Tabla completa en `Tablas_Escalado.md` (2.11).

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

### 9.16 Sombra Araña

Invocación **mágica** (tercera de las 10 Artes de las Sombras). Invoca **una araña** detrás del personaje: esfera oscura pequeña con 8 patas y ojos rojos, **1 de vida**, sin ataque. Si no recibe orden, te sigue como las demás invocaciones.

- **Orden:** mantén la tecla (los ojos se encienden) y marca un **punto** con el clic derecho. La araña va hasta allí (no persigue enemigos).
- **Telaraña:** al llegar teje una **telaraña en el suelo** (círculo con radios, algo más grande que el personaje: 1.6 veces su radio) y desaparece. Es una **trampa de un solo uso**: el **primer enemigo** que la pisa queda **inmovilizado** (no puede moverse, pero sí atacar) y la telaraña se consume. Los enemigos no la ven ni la evitan. El enemigo inmovilizado muestra un **anillo gris azulado**.
- **Límite:** máximo **3 telarañas** a la vez; tejer una cuarta quita la más vieja.
- **Recarga:** **5 s** fijos, que empiezan al tejer o si la araña muere antes de llegar (en ese caso no hay telaraña).
- **Nivel 20:** la telaraña además hace **1 de daño mágico por segundo** mientras dura la inmovilización: lo amortigua el **escudo mágico** del enemigo (bloqueo 10 %, reparto 90 / 10, ver 6.3) y no lo empuja.

| Nivel | Coste En. | Inmovilización |
|---|---|---|
| 1 | 50 | 5 s |
| 5 | 61 | 8.2 s |
| 10 | 74 | 12.1 s |
| 15 | 87 | 16.1 s |
| 20 | 100 | 20 s (+1 daño mágico/s) |

Coste **50 → 100 En.** e inmovilización **5 → 20 s**, ambos lineales. Nivel máximo **20**. En el panel derecho muestra la inmovilización actual y las telarañas colocadas (x/3). Tabla completa en `Tablas_Escalado.md` (2.13).

### 9.17 Paso 0

Habilidad **mágica** de la categoría **Potenciadores**. Vuelve **invisible** al personaje durante un tiempo (sus **invocaciones no**).

- **Enemigos:** mientras eres invisible **no te detectan**: no te miran ni inician ataques contra ti. Pero **sí puedes recibir daño** de lo que te toque igualmente: un golpe que ya estaba en marcha, el agua profunda, los arbustos venenosos, etc.
- **Duración:** sigues invisible **hasta que se acaba el tiempo**, aunque ataques o recibas daño. La **recarga** empieza al terminar.
- **Cómo se ve:** al activarse **te desvaneces en 0.4 s** (y al terminar vuelves a verte con el mismo fundido); es solo visual, para los enemigos la invisibilidad empieza y acaba al instante. Invisible te ves como una **silueta casi transparente** (contorno tenue y ojos) para saber dónde estás. Se ocultan el **nombre**, el **arma** (cualquiera, también el arco o el escudo), las **auras** de habilidades (Destello, Burst, Aura Eléctrica, Reforzamiento, Regeneración) y el **círculo de destino**. Siguen viéndose las **invocaciones**, los **ataques** (Carga de Fuego, Disparo Veloz, Cortar, flechas, Onda Sonora, telarañas) y la **animación del golpe** del arma.
- **Pantalla:** el mapa se **oscurece** igual que dentro de un arbusto; si estás invisible y en un arbusto a la vez **no se oscurece el doble**.
- **Combo:** lanzarla con otra habilidad activa cuesta el **+5 %** de la energía actual (ver 9.10). También puede salir en **Golpe de Suerte** (ver 9.9).

| Nivel | Invisibilidad | Coste En. | Recarga |
|---|---|---|---|
| 1 – 2 | 3 s | 30 | 6 s |
| 3 – 4 | 4 s | 35 | 8 s |
| 5 – 7 | 5 s | 40 | 10 s |
| 8 – 9 | 6 s | 50 | 12 s |
| 10 | 8 s | 60 | 16 s |

Valores **por tramos** (cada nivel conserva el del tramo anterior). Nivel máximo **10**; cada mejora cuesta **2 puntos** (como Regeneración Inversa). Tabla completa en `Tablas_Escalado.md` (2.14).

### 9.18 Disparo Venenoso

Habilidad de **daño mágico** (categoría Ataque Mágico). Dispara hacia donde mira el personaje una **esfera verde con una pequeña esfera morada** en el centro (velocidad **12**, sin alcance máximo, como Disparo Veloz). Se detiene en el **primer enemigo** y las **rocas la bloquean**.

- **Impacto:** no hace daño ni empuja; **envenena** al enemigo.
- **Veneno:** daño **mágico** repartido en el tiempo, un golpe por segundo (y la fracción que falte al terminar, para que siempre llegue el total). Lo **amortigua el escudo mágico** del enemigo y no empuja. El enemigo envenenado muestra un **anillo verde**.
- **No acumulable:** volver a envenenar al mismo enemigo **reinicia** el veneno con los valores del nuevo disparo. Puede estar activo a la vez que la quemadura, el desangrado o la inmovilización.
- **Golpe de Suerte:** puede salir como resultado **negativo** que envenena al portador (ver 9.9).

| Nivel | Coste En. | Veneno total | Duración | Daño por segundo | Recarga |
|---|---|---|---|---|---|
| 1 | 20 | 20 | 20 s | 1 | 30 s |
| 5 | 25 | 24.2 | 17.9 s | 1.35 | 26.8 s |
| 10 | 32 | 29.5 | 15.3 s | 1.93 | 22.9 s |
| 15 | 38 | 34.7 | 12.6 s | 2.75 | 18.9 s |
| 20 | 45 | 40 | 10 s | 4 | 15 s |

Todo **lineal**: coste **20 → 45 En.**, veneno **20 → 40** de daño, duración **20 → 10 s** y recarga **30 → 15 s** (a 1 decimal). Nivel máximo **20**. Tabla completa en `Tablas_Escalado.md` (2.15).

## 10. Puntos de empuje (retroceso)

Cada punto de **daño** aplica **1 punto de empuje** (retroceso) a quien lo recibe, alejándolo del atacante. Además, **quien genera el daño también retrocede** un poco al golpear: así un grupo de invocaciones no inflige todo su daño a la vez (daño explosivo en conjunto), sino **por intervalos**, al tener que reacercarse tras cada golpe (junto con su recarga de ataque de 1 s). El **Escudo** aplica 2 puntos de empuje a su propio portador al bloquear. Los **golpes con arma** no usan esta regla: empujan con los puntos fijos de cada arma (ver 8.5), y en el **choque de armas** ambos retroceden con la misma fuerza.

### 10.1 Maniquí de pruebas (beta de enemigos)

En el centro del mapa hay un **maniquí**: **100 de vida** y **escudos físico y mágico de 50** (mismas reglas que los del personaje: reparto, regeneración y anulación por Cortar).

- **Ataque:** lleva una **Espada Larga** (nivel 1, Fuerza 2). Con una IA simple **gira hacia el personaje** y, si está a menos de 150 de distancia, lanza un golpe cada **2 s**. **No detecta** al personaje **oculto en un arbusto** ni **invisible** (Paso 0): deja de girarse hacia él y no inicia golpes, aunque un golpe que ya estaba en marcha termina y puede dañarlo. Su filo hace **daño físico** y empuja tanto al personaje como a sus **invocaciones**. Si el personaje lleva el **Escudo** desenfundado y el golpe le llega por el frente, lo **bloquea** (ver 8.2). Su espada también se desgasta y puede chocar con la del personaje (ver 8.5).
- **Daño recibido:** le afectan el arma del personaje y **todas las habilidades con daño**: Disparo Veloz, Carga de Fuego (con quemadura), Disparo Venenoso (veneno, anillo verde), Cortar, Onda Sonora, Aura Eléctrica, las invocaciones (con el desangrado de los lobos) y la telaraña de la Sombra Araña (inmovilización). Muestra una **barra de vida** (roja mientras sangra) y encima sus dos escudos (verde físico, azul mágico; recuadro rojo si el mágico está anulado). Como no se mueve, muestra la ralentización recibida como texto (**"Vel -X%"**) junto a sus barras. Al recibir un golpe retrocede y luego **vuelve a su posición** (sigue siendo un blanco centrado); mientras está **inmovilizado** no retrocede ni vuelve. Si lo destruyen, **reaparece a los 5 s** con la vida y los escudos llenos y una espada nueva.

### 10.2 Fauna

El mundo tiene animales en cuatro grupos (detalle y valores en `Fauna.md`). Solo se actualizan y dibujan **cerca de la cámara**, por rendimiento.

- **Ambiental (sin colisión):** mariposas y luciérnagas sobre las praderas, pájaros posados en las copas que alzan el vuelo si te acercas, peces (sombras bajo el agua) y ranas en orillas y nenúfares que saltan al agua.
- **Pasiva (huye):** **conejos salvajes** (10 madrigueras en el pasto alto, se esconden 60 s y se reproducen; una madriguera vacía se muda a otro pastizal) y **venados** (50 en el mundo, se regeneran y se reproducen). Huyen del jugador, de sus sombras y de los zorros hambrientos.
- **Neutral (reacciona si la provocas):** **jabalí** (rabia de 6 s al recibir un golpe: embiste con 10 – 18 de daño y 40 de empuje) y **zorro** (muerde si lo acorralas o golpeas, roba un 30 % de velocidad a su objetivo, caza conejos cuando tiene hambre y tiene su propio **Paso 0**, con el mismo fundido de 0.4 s).
- **Hostil (te caza):** **lobos en manada** (7 manadas de 4 con un alfa; desangran, se retiran si queda uno y cazan presas con hambre compartida), **osos** (150 de vida, viven en una roca gigante que hace de cueva; zarpazo de 15 – 25 que resta un 30 % extra al escudo y rugido que ralentiza; al morir se puede entrar a la cueva, que oscurece el mapa, y recoger un orbe que cura +20) y **cocodrilos** (uno en la zona profunda de cada lago grande, intocables sumergidos, con escudo físico de 30).

Reglas comunes:

- Los animales con vida **reciben daño de todo** (armas, proyectiles, habilidades, efectos e invocaciones), los inmoviliza la telaraña y los empuja el arma. Cuentan como **enemigos** para el modo combate de las sombras y para el **Autoapuntado** (ver 6.4).
- **Sigilo:** oculto en un arbusto o invisible (Paso 0), **ningún animal** te detecta.
- **Escudo:** sus golpes y mordidas consultan al Escudo igual que la espada del maniquí: de frente con el Escudo desenfundado se bloquean enteros y el animal sale repelido con 40 de empuje (ver 8.2).
- **Experiencia y monedas:** al morir a tus manos dan XP y pueden soltar monedas (ver 7).
- **Reaparición:** sin pasar el máximo de cada especie, los **zorros** vuelven (uno nuevo cada 3 min y +1 cada 2 min si quedan 2), las **manadas** crecen +1 lobo por minuto hasta 4 (al llegar a 4 sin alfa, uno evoluciona) y una manada exterminada se **reinicia con 2 lobos en otro bosque**, y cada **oso** muerto es sustituido por otro en su cueva a los **3 min**. Conejos, venados y jabalíes se reproducen; el cocodrilo no vuelve. Detalle en `sistema_xp.md`.

---

## 11. Interfaz

- **Pantalla de creación (a pantalla completa y adaptable):** se escala al tamaño de la pantalla (diseño base 1600x900, factor 0.6–1.6) y se reorganiza al ancho disponible: en pantallas anchas va en **dos columnas** (personaje, herramienta y estadísticas a la izquierda; habilidades a la derecha) y en estrechas en **una**. Las tarjetas se reparten en filas según quepan, los nombres largos reducen su fuente para no cortarse y, si el contenido no cabe en alto, aparece una **barra de desplazamiento** (rueda del ratón). El botón **Comenzar mundo** queda **fijo abajo**, siempre visible. [ESC] sale de pantalla completa y la interfaz se reacomoda sola. Contiene nombre, color con vista previa, y **tarjetas de selección** para la herramienta (una) y las habilidades (hasta 3). Las habilidades se agrupan **por categorías en columnas** (Artes de las Sombras, Potenciadores, Ataque Mágico, Defensa y Soporte, Especiales), pensado para escalar al añadir más. Cada tarjeta tiene un botón **[?]** que muestra su descripción en un recuadro; el texto de cada habilidad vive **solo** en ese **[?]**.
- **Panel izquierdo (en juego):** nivel y puntos, **barra de experiencia** (XP actual / necesaria, o MÁX en el nivel 20) con las **monedas** a la derecha, tarjeta del arma (nombre, nivel, daño y cadencia real "Daño X · Cad Y/s", debuff/buff y barra de durabilidad; con el **Arco**: flechas en el carcaj, carga actual con su barra y botón de compra de flechas) y la lista de estadísticas con su botón **[+]**: Vida, **Daño**, **Velocidad** (ya muestran el valor efectivo, sin filas separadas de base/actual), **Cadencia** (la real con el arma desenfundada; si no, el bonus del personaje), Energía, **Escudo** y **Escudo M.** (actual / máximo). Abajo, el botón **Volver a selección [M]**.
- **Panel derecho (en juego):** más ancho y con letra más grande y de alto contraste. Una tarjeta por habilidad con tecla, nivel, coste, estado, recarga, resumen del efecto según el nivel y botón **[+]**.
- **Volver a selección:** el botón del panel izquierdo o **[M]** cierran el mundo y reabren la pantalla de creación para probar otro personaje sin salir del juego.
- **Iconos de ayuda [?]:** en ambos paneles abren un tooltip con las explicaciones, manteniendo la interfaz despejada.
- **Indicadores de terreno:** avisan cuando estás en agua, en un lago profundo, oculto en un arbusto, **invisible** (Paso 0) o en **autoapuntado**. Dentro de la cueva de un oso muerto el mapa se oscurece como en un arbusto.
- **Textos flotantes:** **"+X XP"** y **"+X monedas"** sobre el personaje al cazar y **"NIVEL N"** al subir.
- **Pantalla de muerte:** velo oscuro sobre el mundo con **Reaparecer [R]** y **Volver al menú principal [M]** (ver 7.1). Si tienes un **Tótem de vida** equipado no sale: vuelves al centro sin perder nada y aparece "El Tótem de vida te salvó (quedan N)".
- **Inventario [I]:** ventana sobre el mundo con el **nivel y la XP** (cuánto falta para el siguiente), las **monedas**, los **puntos de mejora**, las **estadísticas** (con barras de vida, energía y escudos), la **herramienta** elegida (nivel, daño, cadencia, velocidad, estado y durabilidad) y **solo las 3 habilidades equipadas** (tecla, nivel, coste, estado o recarga y resumen). Tiene cuatro pestañas: **Personaje** (lo anterior), **Equipo** (las 6 herramientas y las 15 habilidades: equipar la herramienta y elegir qué habilidad va en [2] [3] [4]; las que faltan salen bloqueadas) **Gacha** (tirada de 30 monedas con ruleta, probabilidades e historial; ver `Gacha_Talismanes.md`) y **Talismanes** (los 3 huecos equipados y la colección de anillos y tótems, con botones Equipar y Quitar; ver `Gacha_Talismanes.md`). Es **interactivo**: las tarjetas se iluminan al pasar el ratón y abajo se muestra su descripción, y sus botones **[+]** gastan puntos igual que los paneles. **No pausa el juego**: el mundo sigue detrás (se puede morir con él abierto; con poca vida el borde parpadea en rojo). Se cierra con **[I]** o con la **X**; al morir se cierra solo. Un clic dentro no mueve al personaje.
- **Brújula [C]:** flechas alrededor del personaje hacia el **conejo (C)**, **lobo (L)** y **oso (O)** más cercanos y hacia el **maniquí (M)**, con la distancia a cada uno y una leyenda arriba a la izquierda.

---

## 12. Controles

| Entrada | Acción |
|---|---|
| Clic izquierdo | Mover el personaje (o pulsar botones [+] y [?] de la interfaz) |
| [1] | Sacar / guardar la herramienta |
| [Espacio] | Golpear con el arma (mantener = golpes seguidos según la cadencia). Con el **Arco**: mantener = cargar, soltar = disparar |
| [R] | Arco: comprar un lote de 10 flechas con energía (también con el botón del panel izquierdo) |
| [2] [3] [4] | Usar las habilidades equipadas (mantener pulsado para cargar la Carga de Fuego) |
| Mantener [2] [3] [4] | Poner esa invocación sombría en **modo combate** (ojos encendidos) |
| Clic derecho (en modo combate) | Enviar a las sombras a un punto o a perseguir y atacar al enemigo bajo el clic (la orden persiste al soltar la tecla) |
| Mantener y soltar [2] [3] [4] con una orden en curso | Devolver esa invocación al estado pasivo (te siguen) |
| Clic derecho junto a ti | Llamar de vuelta a las sombras (vuelven a seguirte) |
| Clic derecho sobre un enemigo (sin modo combate) | **Autoapuntado**: el personaje mira siempre a ese enemigo (−40 % Vel, rango 500). En terreno libre o sobre el mismo objetivo lo quita (ver 6.4) |
| [H] | Mostrar / ocultar las hitboxes |
| [C] | Mostrar / ocultar la **brújula** a los animales más cercanos (conejo, lobo, oso) y al maniquí |
| [I] | Abrir / cerrar el **inventario** (no pausa el juego; también se cierra con la X) |
| [T] | (Prueba) Conseguir un talismán al azar (anillo o Tótem de vida) hasta que exista el Gacha |
| [Y] | (Prueba) Conseguir una herramienta o habilidad que no tengas, a nivel 1 |
| [K] | (Prueba) +100 monedas para probar el Gacha |
| [L] | (Prueba) Subir de nivel al personaje (+3 puntos, hasta el 20) |
| [R] / [M] (al morir) | Reaparecer desde el nivel 1 / volver al menú principal |
| [J] | (Prueba) Simular un golpe del arma (desgasta durabilidad) |
| [M] | Volver a la pantalla de selección (también con el botón del panel izquierdo) |
| [ESC] | Salir del juego |

---

## 13. Pendiente (a futuro)

- **Enemigos reales:** la fauna hostil (lobos, osos, cocodrilos) ya da enemigos con IA propia y experiencia; faltan más recompensas en las cuevas de los osos y **medir en partida** que el nivel 20 se alcance en unas 2 horas.
- Mecánica adicional prevista a partir del **nivel 20** del personaje.
