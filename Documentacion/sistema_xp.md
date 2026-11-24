# LEVEL_UP — Sistema de experiencia, monedas y muerte

> Documento de información (no técnico) sobre cómo se sube de nivel y qué pasa al morir.
> Nace de la propuesta del equipo (ver el anexo) y refleja lo que ya está en el juego.
> Actualizado: 23 de noviembre de 2026.

---

## 1. Niveles

- Nivel máximo del personaje: **20**.
- Cada nivel da **4 puntos de mejora** (3 hasta el 24/11/2026; se empieza con 4, así que al nivel 20 hay 80 en total) (ver la sección 7 de `Level_UP_Especificaciones.md`) y **+20 monedas** (380 en total hasta el nivel 20; [L] también las da).
- Al subir, la experiencia **vuelve a 0 más lo que sobró**: si te faltaba 1 XP y ganas 4, subes y empiezas el siguiente nivel con 3. Con mucha XP de golpe se pueden subir varios niveles.
- En el nivel 20 la experiencia ya no se acumula y la barra muestra **MÁX**.
- La tecla de prueba **[L]** sigue subiendo un nivel (también se detiene en el 20).

| Salto | XP | Salto | XP | Salto | XP |
|---|---|---|---|---|---|
| 1 → 2 | 1 | 8 → 9 | 25 | 15 → 16 | 95 |
| 2 → 3 | 2 | 9 → 10 | 30 | 16 → 17 | 110 |
| 3 → 4 | 4 | 10 → 11 | 40 | 17 → 18 | 125 |
| 4 → 5 | 8 | 11 → 12 | 50 | 18 → 19 | 140 |
| 5 → 6 | 12 | 12 → 13 | 60 | 19 → 20 | 160 |
| 6 → 7 | 16 | 13 → 14 | 70 | | |
| 7 → 8 | 20 | 14 → 15 | 80 | **Total** | **1048** |

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
| Oso | **3 min** después de morir aparece un oso nuevo **en su misma cueva**, salvo que estés dentro de ella o que la roca se haya destruido con Cortar. |
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
