# LEVEL_UP — Medidas para pixel art

> Medidas sacadas del código actual (personaje de **tamaño 1**, radio 20 px).
> "Tamaño en juego" = lo que ocupa hoy en pantalla (1 unidad del mundo = 1 px; la cámara no hace zoom).
> **Lienzo ×1**: dibujas 1 píxel de arte = 1 píxel de pantalla. **Lienzo ×2**: dibujas a la mitad y el juego lo escala ×2 (píxel más grueso, menos trabajo).
> Elige **una sola escala** para todo el juego, para que todos los sprites tengan el mismo grosor de píxel.

---

## 0. Reglas generales para los dibujos

- **Formato:** PNG con fondo transparente, sin antialiasing ni bordes difuminados.
- **Orientación:** todo lo que gira con el personaje (armas, flecha, cuchilla) se dibuja **apuntando hacia arriba** (norte); el juego lo rota.
- **Centro:** el centro del lienzo = centro del objeto (el punto de su hitbox). Usa lienzos de medida **par**.
- **Hitbox:** la colisión no cambia con el dibujo. El sprite debe **ocupar aproximadamente su hitbox** (círculo o cuadrado indicado), si no se verá que choca "en el aire" o que lo atraviesa.
- **Margen:** lo que sobresale (orejas, patas, brillo) puede salirse un poco del círculo; las medidas de lienzo ya lo incluyen.

---

## 1. Personajes y criaturas

| Objeto | Hitbox (código) | Tamaño en juego | Lienzo ×1 | Lienzo ×2 | Notas |
|---|---|---|---|---|---|
| Personaje (jugador) | círculo radio 20 | Ø 40 | **40 × 40** | 20 × 20 | Gira hacia donde se mueve. Hoy el cuerpo se tiñe con el color elegido en la creación: si quieres conservarlo, dibuja el cuerpo en **gris/blanco** y el juego lo colorea. Los ojos pueden seguir dibujándose por código. |
| Personaje invisible (Paso 0) | — | Ø 40 | 40 × 40 | 20 × 20 | Opcional: silueta. Si no, el juego aplica transparencia al sprite normal. |
| Maniquí de pruebas | círculo radio 18 | Ø 36 | **36 × 36** | 18 × 18 | Lleva Espada Larga (sprite aparte). |
| Conejo (invocación) | círculo radio 8 | Ø 16 (+orejas) | **16 × 20** | 8 × 10 | Orejas hacia arriba fuera del círculo. Variante "modo combate" con ojos brillantes. |
| Lobo (invocación) | círculo radio 11 | Ø 22 (+orejas) | **24 × 28** | 12 × 14 | Orejas sobresalen ~4 px arriba. Variante modo combate. |
| Araña (Sombra Araña) | círculo radio 5 | Ø 10 cuerpo, patas hasta Ø 22 | **22 × 22** | 11 × 11 | Variante modo combate (ojos rojos más vivos). |

---

## 2. Armas (dibujar en vertical, punta hacia arriba)

El largo depende del tamaño del personaje: `largo = max(24, radio × 1.35) × factor`. Con tamaño 1 (radio 20) la base es 27 px.

| Arma | Largo en juego | Ancho aprox. | Lienzo ×1 | Lienzo ×2 | Notas |
|---|---|---|---|---|---|
| Espada Ligera | 32 | 4–6 | **8 × 32** | 4 × 16 | Empuñadura en el extremo de abajo (¼ del largo). |
| Espada Larga | 48 | 5–7 | **8 × 48** | 4 × 24 | También la usa el maniquí. |
| Mandoble | 72 | 6–8 | **10 × 72** | 5 × 36 | |
| Dagas Simples (×2) | 22 | 4–5 | **6 × 22** | 3 × 11 | Un sprite; el juego lo pone en ambos flancos (espejo). |
| Escudo | 72 de alto | 30 | **30 × 72** | 15 × 36 | Forma de escudo alargado; umbo al centro. |
| Arco | 36 de ancho | 10 de curva | **36 × 12** | 18 × 6 | Dibujar el arco **sin cuerda** (la cuerda se tensa por código según la carga). Va delante del personaje, perpendicular a la mirada. |
| Versión nivel máximo (todas) | — | — | igual | igual | Opcional: variante dorada. Si no, el juego tiñe de dorado. |

---

## 3. Proyectiles y efectos de ataque

| Objeto | Tamaño en juego | Lienzo ×1 | Lienzo ×2 | Notas |
|---|---|---|---|---|
| Disparo Veloz (esfera de energía) | Ø 16 (radio 6 + brillo 2) | **16 × 16** | 8 × 8 | |
| Carga de Fuego, sin carga | Ø 16 | **16 × 16** | 8 × 8 | El radio crece con la carga: |
| Carga de Fuego, 1 s | Ø 20 | **20 × 20** | 10 × 10 | radio 8 |
| Carga de Fuego, 2 s | Ø 26 | **26 × 26** | 13 × 13 | radio 11 |
| Carga de Fuego, 3 s | Ø 32 | **32 × 32** | 16 × 16 | radio 14 |
| Carga de Fuego, 4 s | Ø 38 | **38 × 38** | 19 × 19 | radio 17 |
| Carga de Fuego, 5 s | Ø 48 | **48 × 48** | 24 × 24 | radio 22. Alternativa: un solo sprite de 48 × 48 que el juego reduce (pierde nitidez). |
| Flecha del Arco (en vuelo) | 20 de largo, 6 de ancho | **6 × 20** | 3 × 10 | Punta hacia arriba. Aspecto de energía (cian). |
| Flecha clavada | 20 × 6 | **6 × 20** | 3 × 10 | Opcional: versión apagada (si no, se oscurece por código). |
| Cuchilla de Cortar | 32 de largo, muy fina | **4 × 32** | 2 × 16 | Negra con contorno rojo, vertical. |
| Telaraña (Sombra Araña) | Ø 64 (1.6 × radio del personaje) | **64 × 64** | 32 × 32 | En el suelo, debajo de todo. |

---

## 4. Auras y estados (encima o alrededor del personaje)

| Objeto | Tamaño en juego | Lienzo ×1 | Lienzo ×2 | Notas |
|---|---|---|---|---|
| Aura Eléctrica | Ø 200 (radio 100) | **200 × 200** | 100 × 100 | Semitransparente; ideal 2–4 fotogramas de animación. |
| Reforzamiento Mágico (campo) | Ø 44 (1.1 × radio) | **44 × 44** | 22 × 22 | Solo contorno azul celeste. |
| Regeneración Inversa (contorno) | Ø 44 | **44 × 44** | 22 × 22 | Igual que el Reforzamiento, en rosa. |
| Anillos interiores Destello / Burst / fatiga | dentro del Ø 40 | 40 × 40 | 20 × 20 | Hoy son anillos por código; pueden quedarse así. |
| Quemadura en enemigo (anillo naranja) | Ø 44 sobre el maniquí | 44 × 44 | 22 × 22 | Opcional. |
| Inmovilizado (anillo gris azulado) | Ø 48 sobre el maniquí | 48 × 48 | 24 × 24 | Opcional. |
| Onda Sonora | anillos de radio 0 → 200–400 | — | — | **Mejor por código** (crece de forma continua). |

---

## 5. Terreno y vegetación

Estos objetos tienen **tamaño variable**, así que no se puede dibujar un único sprite exacto. Opciones recomendadas:

| Objeto | Tamaño en juego | Recomendación | Lienzo ×1 |
|---|---|---|---|
| Suelo | todo el mapa (radio 5000) | **Textura repetible** (tile sin costuras) | **64 × 64** (o 32 × 32) |
| Agua normal | nubes de radio 100–500 | Textura repetible recortada a la forma de la nube; el borde por código | **32 × 32** |
| Agua profunda (centro de lagos > 300) | 35 % interior | Otra textura repetible más oscura | **32 × 32** |
| Roca pequeña | cuadrado de 22–45 | 2–3 variantes; el juego las escala al lado real | **32 × 32** |
| Roca grande | cuadrado de 70–130 | 2–3 variantes | **96 × 96** |
| Roca gigante | cuadrado de 150–300 | 1–2 variantes | **224 × 224** |
| Arbusto (3 tipos se ven iguales) | nube de Ø 50–150 | 3–4 tamaños base; el juego usa el más cercano | **64, 96, 128 y 160** (cuadrados) |
| Brote de frutal | Ø 20 | Sprite propio | **24 × 24** |
| Orbe de fruta | Ø 8 | Sprite propio | **8 × 8** |

> **Rocas y arbustos:** escalar pixel art a un tamaño no entero (ej. 96 → 113) deforma los píxeles. Si quieres píxel perfecto, la alternativa es cambiar la generación del mundo para que solo use los tamaños dibujados (ej. rocas de 32, 64, 96, 128, 192 y 256). Es un cambio pequeño de código, pero cambia el mapa: decídelo antes.

---

## 6. Interfaz (opcional)

| Objeto | Lienzo ×1 | Notas |
|---|---|---|
| Icono de habilidad (panel derecho y creación) | **32 × 32** | Uno por habilidad (14). Hoy las tarjetas no tienen icono. |
| Icono de arma (panel izquierdo y creación) | **32 × 32** | Uno por arma (6). |
| Icono pequeño de estado (agua, oculto, invisible…) | **16 × 16** | Para la barra inferior. |

---

## 7. Animación (opcional, por prioridad)

| Objeto | Fotogramas sugeridos | Para qué |
|---|---|---|
| Carga de Fuego | 2–3 | Llama parpadeando |
| Aura Eléctrica | 3–4 | Chispas |
| Lobo / conejo / araña | 2 (caminar) | Movimiento |
| Personaje | 1–2 | Reposo / andar |
| Disparo Veloz, flecha | 1–2 | Brillo |

Cada fotograma va en un PNG aparte o en una tira horizontal (todos del mismo tamaño).
