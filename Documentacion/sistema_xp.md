# LEVEL_UP — Sistema de experiencia, monedas y muerte

> Documento de información (no técnico) sobre cómo se sube de nivel y qué pasa al morir.
> Nace de la propuesta del equipo (ver el anexo) y refleja lo que ya está en el juego.
> Actualizado: 24 de noviembre de 2026.

---

## 1. Niveles

- Nivel máximo del personaje: **40** (hasta el 24/11/2026 era 20). Al llegar al **nivel 20** se habilita el **Gacha mejorado** con las habilidades potenciadas (ver `Gacha_Talismanes.md`).
- Cada nivel da **4 puntos de mejora** (3 hasta el 24/11/2026; se empieza con 4, así que hay 80 al nivel 20 y **160 al nivel 40**) (ver la sección 7 de `Level_UP_Especificaciones.md`) y **+20 monedas** (380 hasta el nivel 20 y 780 hasta el 40; [L] también las da).
- Al subir, la experiencia **vuelve a 0 más lo que sobró**: si te faltaba 1 XP y ganas 4, subes y empiezas el siguiente nivel con 3. Con mucha XP de golpe se pueden subir varios niveles.
- En el nivel 40 la experiencia ya no se acumula y la barra muestra **MÁX**.
- La tecla de prueba **[L]** sigue subiendo un nivel (también se detiene en el 40).

| Salto | XP | Salto | XP | Salto | XP |
|---|---|---|---|---|---|
| 1 → 2 | 1 | 8 → 9 | 25 | 15 → 16 | 95 |
| 2 → 3 | 2 | 9 → 10 | 30 | 16 → 17 | 110 |
| 3 → 4 | 4 | 10 → 11 | 40 | 17 → 18 | 125 |
| 4 → 5 | 8 | 11 → 12 | 50 | 18 → 19 | 140 |
| 5 → 6 | 12 | 12 → 13 | 60 | 19 → 20 | 160 |
| 6 → 7 | 16 | 13 → 14 | 70 | | |
| 7 → 8 | 20 | 14 → 15 | 80 | **Total 1 → 20** | **1048** |

### Niveles 20 → 40 (desde el 24/11/2026)

El salto sigue creciendo de forma suave: **+20 por nivel** hasta el 25, **+25** del 25 al 29 y **+30 – 40** del 30 al 40.

| Salto | XP | XP acumulada | Salto | XP | XP acumulada |
|---|---|---|---|---|---|
| 20 → 21 | 180 | 1228 | 30 → 31 | 420 | 4248 |
| 21 → 22 | 200 | 1428 | 31 → 32 | 450 | 4698 |
| 22 → 23 | 220 | 1648 | 32 → 33 | 480 | 5178 |
| 23 → 24 | 240 | 1888 | 33 → 34 | 510 | 5688 |
| 24 → 25 | 260 | 2148 | 34 → 35 | 540 | 6228 |
| 25 → 26 | 285 | 2433 | 35 → 36 | 575 | 6803 |
| 26 → 27 | 310 | 2743 | 36 → 37 | 610 | 7413 |
| 27 → 28 | 335 | 3078 | 37 → 38 | 645 | 8058 |
| 28 → 29 | 360 | 3438 | 38 → 39 | 680 | 8738 |
| 29 → 30 | 390 | 3828 | 39 → 40 | 720 | **9458** |
| **Total 20 → 30** | **2780** | | **Total 30 → 40** | **5630** | |

**Ritmo esperado (simulación del 24/11/2026, 3000 partidas, solo con la fauna actual):** a partir del nivel 10 el bot gana unas **14.5 XP por minuto** y ese ritmo ya no sube, porque no hay animales que den más XP. Con eso:

| Tramo | XP | Con la fauna actual (≈14.5 XP/min) | Si los enemigos nuevos duplican la XP/min |
|---|---|---|---|
| 1 → 20 | 1048 | ≈2.4 h (mediana) | — |
| 20 → 30 | 2780 | ≈3.2 h | ≈1.6 h |
| 30 → 40 | 5630 | ≈6.5 h | ≈3.2 h |
| **1 → 40** | **9458** | **≈12 h** | **≈7 h** |

La tabla 20 → 40 está pensada para los **enemigos futuros**, que darán más XP pero serán más difíciles. Con solo la fauna actual el tramo 30 → 40 se hace largo (cada nivel de 30 a 50 minutos).

La tabla está pensada para llegar al nivel 20 en **unas 2 horas** de caza. Las simulaciones del 23/11/2026 (10 000 partidas con un bot) dicen que todavía no se consigue: con la XP actual el mejor llegó al 20 en unas 4.3 h y la mayoría se queda entre el nivel 5 y el 12, porque lobos, osos y cocodrilos siguen siendo demasiado peligrosos para el personaje. Falta medirlo jugando.

---

## 2. Recompensas por animal (XP y monedas)

| Animal | XP | Probabilidad de monedas | Monedas | Promedio |
|---|---|---|---|---|
| Conejo salvaje | 0.5 | 5 % | 1 | 0.05 |
| Venado | 2 | 25 % | 1 – 2 | 0.4 |
| Zorro | 3 | 40 % | 1 – 3 | 0.8 |
| Jabalí | 5 | 70 % | 2 – 5 | 2.5 |
| Lobo | 5 | 100 % | 5 – 10 | 7.5 |
| Lobo alfa | 8 | 100 % | 7 – 10 | 8.5 |
| Cocodrilo | 10 | 100 % | 6 – 12 | 9 |
| Oso | 15 | 100 % | 8 – 12 | 10 |
| Orbe de curación de la cueva del oso | +2 | — | — | — |
| Orbe de XP de la cueva del oso | +5 | — | — | — |
| Orbe Gacha de la cueva del oso (50 % de que aparezca) | — | ruleta gratis de anillos | — | — |
| Manada completa (bono) | +3 | — | — | — |

Una manada completa da **26 XP** (3 lobos × 5 + alfa 8 + bono 3) y unas **31 monedas** de promedio.

- **Quién da XP y monedas:** solo los animales que matas **tú o tus sombras** (invocaciones), incluidos los que mueren por un efecto que causaste (desangrado, quemadura, veneno, telaraña). Lo que cazan los **depredadores salvajes** (zorros y lobos que se comen conejos o venados) **no da XP**.
- **Bono de manada:** se da al acabar con **todos** los lobos de la manada y **solo si entre ellos estaba el alfa** (por eso es "completa"). Así no se puede farmear matando a los 2 lobos de una manada que se está formando.
- **El maniquí no da XP ni monedas.**
- **Monedas:** si el animal suelta, la cantidad es un entero al azar entre el mínimo y el máximo. Además cada subida de nivel da **+20**. Se gastan en el **Gacha** (15 por tirada; 20 el mejorado desde el nivel 20, ver `Gacha_Talismanes.md`). En las simulaciones del 23/11/2026 un jugador cuidadoso ganó unas **270 monedas** por partida (≈ 8 tiradas).
- En pantalla aparece **"+X XP"**, **"+X monedas"** y **"NIVEL N"** sobre el personaje. El panel izquierdo muestra la XP actual y la necesaria con una barra, y las monedas a la derecha.

---

## 3. Reaparición de la fauna

Para que el mundo no se agote, los animales vuelven sin pasar nunca el máximo de su especie:

| Animal | Cómo vuelve |
|---|---|
| Conejo | Cada 30 s nace +1 en su madriguera si quedan 2 o más (máx. 10). Si una madriguera **se queda sin conejos, desaparece** y aparece otra en otro pastizal con 2 – 10 conejos. |
| Venado | Cada 60 s nace +1 si quedan 2 o más (máx. 50). |
| Jabalí | Cada 60 s nace +1 si quedan 2 o más (máx. 20). |
| Zorro | Cada **3 min** aparece uno nuevo en el mundo (fuera de tu vista) y cada **2 min** nace +1 si quedan 2 o más (máx. 15). |
| Lobos | Cada **1 min** la manada crece **+1** (hasta 4) si no está en combate. Al llegar a 4 sin alfa, **uno evoluciona a alfa**. Si exterminas una manada, al minuto **se inicia otra con 2 lobos en otro bosque** (a más de 1500 px y fuera de tu vista). Siempre hay **7 manadas** como máximo. |
| Oso | **3 min** después de morir aparece un oso nuevo **en su misma cueva**, salvo que estés dentro de ella (la cueva no se puede destruir). |
| Cocodrilo | No reaparece. |

---

## 4. Muerte del jugador

- Si tu vida llega a **0**, el mundo se congela detrás de un aviso **"HAS MUERTO"** con dos opciones:
  - **Reaparecer [R]** (o Enter): vuelves al **centro del mapa** desde cero.
  - **Volver al menú principal [M]**: regresa a la pantalla de creación.
- **Al reaparecer se reinicia:** nivel 1, XP 0, **pierdes todas las monedas**, 4 puntos de mejora, estadísticas iniciales, arma y habilidades a nivel 1 (en las mismas teclas), vida y energía llenas. Tus **sombras desaparecen** y los animales que te perseguían te olvidan.
- **El mundo sigue igual:** los animales muertos siguen muertos y lo que se regeneró sigue ahí. Solo se genera un mundo nuevo al **crear otra partida** con un personaje nuevo.

---

## Anexo: propuesta original

La primera propuesta del equipo usaba esta tabla (**1977 XP** en total), que se cambió por la de la sección 1 para acercarse a las 2 horas de juego:

| Salto | XP | Salto | XP | Salto | XP |
|---|---|---|---|---|---|
| 1 → 2 | 1 | 8 → 9 | 44 | 15 → 16 | 184 |
| 2 → 3 | 2 | 9 → 10 | 58 | 16 → 17 | 212 |
| 3 → 4 | 4 | 10 → 11 | 74 | 17 → 18 | 242 |
| 4 → 5 | 8 | 11 → 12 | 92 | 18 → 19 | 274 |
| 5 → 6 | 14 | 12 → 13 | 112 | 19 → 20 | 310 |
| 6 → 7 | 22 | 13 → 14 | 134 | | |
| 7 → 8 | 32 | 14 → 15 | 158 | | |

La XP por animal se subió después (conejo 0.1 → 0.5, venado 1 → 2, zorro 1.5 → 3, jabalí 3 → 5, lobo 2 → 5, alfa 4 → 8, cocodrilo 4 → 10, oso 6 → 15); las reglas de muerte se mantuvieron. Las monedas se añadieron después.
