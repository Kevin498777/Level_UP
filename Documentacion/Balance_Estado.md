# LEVEL_UP — Estado del balance

> Documento de trabajo para retomar el balance más adelante.
> Actualizado: 23 de noviembre de 2026.
> Los valores de detalle están en `Tablas_Escalado.md` y en `Level_UP_Especificaciones.md`.

---

## 1. Cómo se mide el balance

- **La energía es el recurso clave.** Hay 100 de energía máxima y se recupera **+1 cada 3 s** quieto y **+1 cada 6 s** en movimiento (unos 0.33/s como mucho). Llenar la barra tarda unos 5 minutos, así que la métrica principal es el **daño por punto de energía** (dmg/En).
- Para las armas se compara el **daño por segundo** (daño × cadencia) con Fuerza 2, la velocidad y la durabilidad.
- **Enemigo de referencia:** el maniquí, con 100 de vida, escudos físico y mágico de 50 y una Espada Larga de nivel 1 (6.8 de daño por golpe cada 2 s, alcance 150). Las mediciones de este documento se hicieron contra él.
- **Fauna (desde el 23/11/2026):** ya hay enemigos reales que rodean y persiguen (lobos en manada, osos, cocodrilos, jabalíes y zorros; ver `Fauna.md`). Todavía no se ha medido el balance contra ellos.
- **Experiencia (desde el 23/11/2026):** cazar animales da XP y se sube de nivel sin teclas de prueba (`sistema_xp.md`); morir devuelve al nivel 1. La tabla de XP está pensada para llegar al nivel 20 en unas 2 horas: hay que medirlo en partida.
- El escudo mágico absorbe el 90 % del daño mágico, así que el daño mágico rinde mucho menos contra objetivos con escudo mágico, salvo si se anula con Cortar.

---

## 2. Cambios de balance ya aplicados (20/11/2026)

| Objeto | Antes | Ahora |
|---|---|---|
| **Escudo** (herramienta) | No funcionaba: `recibir_golpe()` nunca se llamaba | **Desenfundado**, bloquea entero todo lo que llega por un **arco frontal de 120°**: golpes, proyectiles y mordidas, físicos o mágicos. Bloquea sin daño ni efectos. El dibujo del escudo es una banda curva que ocupa exactamente ese arco. **Desgaste** = daño bloqueado × (1 − reducción), con reducción del 20 % (nv1) al 70 % (nv5). En cada bloqueo **repele al atacante con 40 de empuje**, más que cualquier arma (el Arco tiene 25), y el arma atacante pierde 1 de durabilidad. El portador retrocede 2. **Pasiva:** +15 % (nv1) → +30 % (nv5) a los máximos de escudo físico y mágico, sobre la base de puntos (con 0 se queda en 0); se pierde si el escudo se rompe. **No bloquea:** Onda Sonora, Aura Eléctrica, terreno, autodaño ni efectos ya aplicados. |
| **Invocar Conejos** | Camada cada 10 s fijos (de 5 a 50 en ~70 s) | Camada cada **10 s × (1 + vivos/10)**: de 5 a 20 en ~77 s y a 50 en ~3.5 min. Tope de 50. |
| **Disparo Veloz** | 20.5–30 % del daño del arma (0.5–5 de daño); velocidad 11 → 30 | **Daño mágico fijo 8 → 30** y **velocidad 14 → 40**. Coste (15 → 35) y recarga (2 → 0.5 s) sin cambios. Se comprueba el recorrido de cada frame para que no salte rocas pequeñas. |
| **Disparo Venenoso** | Coste 20 → 80 | **Coste 20 → 45.** Lo demás igual. |
| **Carga de Fuego** | Hasta +25 % de daño con la carga; quemadura fija de 5 s; recarga de 2 s | Daño base × **0.6 / 0.8 / 1.0 / 1.3 / 1.6 / 2.0** sin carga y con 1 a 5 s de carga (nv1: 12 → 40; nv20: 23.4 → 78). **Quemadura** de 2 a 7 s según la carga. **Recarga** de 8 a 15 s (+1.4 s por segundo de carga). Energía sin cambios (15 → 45). |

Además se eliminó `Personaje.calcular_dano_total()`, que ya no usaba nada.

Gancho para enemigos: `Personaje.bloquear_con_escudo(daño, origen)`. Los ataques bloqueables (proyectiles, mordidas) deben consultarlo **antes** de aplicar daño y efectos. Ya lo usan la espada del maniquí y los ataques de la fauna (`fauna.bloqueado_por_escudo`: jabalí, zorro, lobo, oso y cocodrilo).

---

## 3. Tier list actual (después de los cambios)

### 3.1 Herramientas

| Tier | Arma | Antes | Motivo |
|---|---|---|---|
| **S** | Dagas Simples | S | A nivel 5 es la mejor: 13.1 de daño/s, +10 % de velocidad, 400 de durabilidad y la cadencia más alta. Es débil a nivel 1. |
| **A** | Escudo | F ⬆️ | Bloqueo frontal total más un empuje de 40. Contra el maniquí aguanta ~18 golpes a nv1 y ~147 a nv5. No hace daño, deja la espalda expuesta y tiene −34 % de velocidad; la pasiva solo vale si se invierte en escudos. |
| **A** | Mandoble | A | Mayor daño/s (8.5 → 14.4) y el que más gana con Burst de Fuerza. Su −70 % de velocidad a nv1 es durísimo. |
| **A** | Espada Larga | A | La más equilibrada: 7.2 → 13.0 de daño/s con −34 % → −10 % de velocidad. |
| **B** | Arco | B | Seguro (300 de alcance, 25 de empuje) pero hace poco daño (2 → 4 de daño/s) y gasta energía en flechas. |
| **B−** | Espada Ligera | B | La de menos daño al máximo nivel (10.6 de daño/s). Las Dagas la superan en todo: no tiene un papel propio. |

### 3.2 Habilidades

| Tier | Habilidad | Antes | dmg/En nv1 → nv20 | Motivo |
|---|---|---|---|---|
| **S** | Invocar Lobos | S | (24 de daño/s desde nv1) | **La más desbalanceada.** A nv1 los tres lobos hacen el triple de daño/s que cualquier arma y 90/s a nv20. Además desangran y reducen la curación un 50 %. |
| **A** | Carga de Fuego | S ⬇️ | 0.93 → 1.9 | Ya no se puede spamear. Ahora premia cargarla: a nv20 la carga completa hace 78 + 7 de quemadura. Bien ubicada. |
| **A** | Invocar Conejos | S ⬇️ | — | Tardan en multiplicarse y los cuerpos sólidos limitan a ~10 los que tocan al objetivo a la vez (≈77 de daño/s a nv20). Inútiles a nv1–3 (0.1 de daño). |
| **A** | Onda Sonora | A | 1.0 → 2.0 (4.0 en agua) | La mejor en daño por energía. Golpea en área y ralentiza. |
| **A** | Destello | A | — | Barata (+52 % de velocidad durante 10 s por 10 de energía) y casi permanente a nv20. |
| **B** | Disparo Veloz | D ⬆️ | 0.53 → 0.86 | Ya es viable: casi instantánea y con 0.5 s de recarga. A nv1 rinde menos que el toque de Carga de Fuego (8 contra 14 de daño por 15 de energía). La limita la energía, no la recarga. |
| **B** | Burst de Fuerza | B | — | +21–40 % honesto; solo mejora el arma. |
| **B** | Sombra Araña | B | — | Inmoviliza 5 → 20 s, pero es cara (50 → 100 de energía) y el inmovilizado puede seguir atacando. Ganará valor con enemigos que se muevan. |
| **B** | Golpe de Suerte | B | — | Mala a nv1 (30 % de no obtener nada y puede envenenarte); muy fuerte a nv20. Pura varianza. |
| **B** | Cortar | B | 0.33 → 0.75 | Su valor está en anular el escudo mágico 8 s (combo con Carga de Fuego u Onda Sonora). |
| **B** | Reforzamiento Mágico | B | — | En la práctica es 1 s de invulnerabilidad. Se pisa con el Escudo. |
| **B−** | Disparo Venenoso | C ⬆️ | 1.0 → 0.89 | Ya no empeora tanto al subir de nivel, pero tiene 30 s de recarga a nv1 y el escudo mágico enemigo le absorbe el 90 %. |
| **C** | Paso 0 | C | — | Los arbustos esconden gratis y cada nivel cuesta 2 puntos. |
| **C** | Aura Eléctrica | C | 0.5 → 1.7 por enemigo | 40 s de recarga a nv1 (sube a 60 s) y daño a sí mismo. Solo vale a nv20 y rodeado de enemigos. |
| **C** | Regeneración Inversa | C | (10 de energía por vida) | Muy cara para lo poco que se recupera la energía; los frutales curan gratis. Cuesta 2 puntos por nivel. |

---

## 4. Pendiente: siguientes fases de balance (propuestas, no aplicadas)

1. **Invocar Lobos (demasiado fuerte, prioridad):** daño **4 → 30** en vez de 8 → 30 y desangrado del 33 % al **20 %**. A nv1 quedarían en 12 de daño/s en total; el nv20 no cambia.
2. **Regeneración Inversa (débil):** bajar el coste a ~6 de energía por vida o que cada nivel cueste 1 punto en vez de 2.
3. **Aura Eléctrica (débil):** que la recarga **baje** con el nivel (40 → 25 s) en vez de subir a 60 s.
4. **Paso 0 (débil):** darle un plus que el arbusto no tenga (p. ej. +50 % de daño en el primer ataque desde la invisibilidad) o bajar el coste de nv1 a 20.
5. **Espada Ligera (sin papel):** darle un rasgo propio, como más cadencia o no desgastarse en los choques de armas.
6. **Disparo Veloz (algo débil al principio):** coste de nv1 de 10 de energía o daño inicial de 10.
7. **Escudo (vigilar, ya se puede medir):** con el maniquí siempre te da de frente. La manada de lobos ya rodea al jugador: revisar que el bloqueo total sin coste para el jugador más el empuje de 40 no lo haga intocable, y que contra el oso (que además resta un 30 % extra al escudo cuando no se bloquea) no sea obligatorio.
8. **Autoapuntado (vigilar, ya se puede medir):** −40 % de velocidad a cambio de apuntar siempre. Con el Escudo, el arco de bloqueo mira siempre al objetivo; junto al −34 % del escudo, la velocidad baja al mínimo (0.4). Revisarlo contra la manada de lobos y el jabalí en rabia.
9. **Invocar Lobos y la fauna:** ordenar el ataque ahora cuesta 5 → 10 de energía (rama de fauna). Tenerlo en cuenta al bajar su daño (punto 1).

Orden sugerido para la próxima sesión: **Lobos → Regeneración Inversa → Aura Eléctrica**, y después el resto.

---

## 5. Pendientes de documentación

- Ninguno: `Tablas_Escalado.xlsx` ya está al día con `Tablas_Escalado.md` (23/11/2026), incluidos los cambios de la sección 2 y el coste de la orden de ataque de Invocar Lobos.
