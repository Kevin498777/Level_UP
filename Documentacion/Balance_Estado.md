# LEVEL_UP — Estado del balance

> Documento de trabajo para retomar el balance más adelante.
> Actualizado: 24 de noviembre de 2026 (ver también `Cambios_2026-11-24.md`).
> Los valores de detalle están en `Tablas_Escalado.md` y en `Level_UP_Especificaciones.md`.

---

## 1. Cómo se mide el balance

- **La energía es el recurso clave.** Hay 100 de energía máxima y se recupera **+1 cada 3 s** quieto y **+1 cada 6 s** en movimiento (unos 0.33/s; hasta el doble con la stat Regen. de energía, x2 en agua y x4 en la zona profunda). Llenar la barra tarda unos 5 minutos, así que la métrica principal es el **daño por punto de energía** (dmg/En).
- Para las armas se compara el **daño por segundo** (daño × cadencia) con Fuerza 2, la velocidad y la durabilidad.
- **Enemigo de referencia:** el maniquí, con 100 de vida, escudos físico y mágico de 50 y una Espada Larga de nivel 1 (6.8 de daño por golpe cada 2 s, alcance 150). Las mediciones de este documento se hicieron contra él.
- **Fauna (desde el 23/11/2026):** ya hay enemigos reales que rodean y persiguen (lobos en manada, osos, cocodrilos, jabalíes y zorros; ver `Fauna.md`). El 24/11/2026 se midió con duelos (clases reales de `fauna.py`) y con la simulación de progresión (sección 2b).
- **Experiencia (desde el 23/11/2026):** cazar animales da XP y se sube de nivel sin teclas de prueba (`sistema_xp.md`); morir devuelve al nivel 1. La tabla de XP está pensada para llegar al nivel 20 en unas 2 horas (la simulación da 134 min de mediana) y el máximo es ahora el nivel 40: hay que medirlo en partida.
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

## 2b. Cambios de balance aplicados el 24/11/2026

| Tema | Antes | Ahora |
|---|---|---|
| **Gacha** | Tirada 10, devolución 25 (daba monedas infinitas) | Tirada **15** (Gacha mejorado **20** desde el nivel 20), devolución **10**; regla proporcional (Nada 15 %, agotada 5 %), anillos al máximo fuera del sorteo y **legendario garantizado en la tirada 90** |
| **Puntos de mejora** | 3 al empezar y +3 por nivel | **4** al empezar y **+4** por nivel (160 al nivel 40) |
| **Regen. de energía** | +0.2 % por punto (inútil) | **+5 % por punto**, máx. +100 % (20 puntos) |
| **Combate cuerpo a cuerpo** | Empuje doble de la fauna, sin protección | Solo el empuje propio del animal; **0.5 s de invulnerabilidad** tras un golpe; cada golpe de arma **aturde 0.3 s** al animal (1 s sin repetir); **vida inicial 30** |
| **Nivel máximo** | 20 | **40** (20 → 40: +8410 XP) |
| **Disparo Veloz (nerf)** | Vel 14 → 40, daño 8 → 30, recarga 2 → 0.5 s | Vel **14 → 35**, daño **8 → 25**, recarga **4 → 2 s** |
| **Cuevas de oso** | Cortar a nivel 20 las destruía | Nada las destruye |
| **Habilidades potenciadas** | — | Relámpago, Fuerza Colosal, Ráfaga Veloz, Estrella Ígnea y Vestigios Míticos (niveles 21 – 30, 2 puntos por nivel) |

**Medición (simulación de 10 000 partidas con el bot):** con todo lo anterior el **83 %** llega al nivel 20 (mediana **134 min**), 5.9 muertes por partida y el 80 % llega al 20 con todos los objetos del Gacha. Duelos solo con arma contra la fauna real: la manada ya se gana desde el nivel 5 (antes 15) y el oso desde el 15.

## 3. Tier list actual (24/11/2026)

Según el porcentaje que llega al nivel 20 empezando con esa arma o habilidad (simulación de 10 000 partidas), los duelos contra la fauna y el daño por energía. Medida **antes** del nerf de Disparo Veloz y sin las potenciadas.

### 3.1 Herramientas

| Tier | Arma | Llega a nv20 | Motivo |
|---|---|---|---|
| **S** | Mandoble | 96.6 % | Más daño por golpe, alcance (91) y empuje (20); el mejor contra el oso. Muy lento al principio. |
| **A** | Espada Larga | 95.3 % | La más equilibrada; gana al lobo solitario desde el nivel 1. |
| **A−** | Dagas Simples | 93.7 % | Débil a nv1, la de más daño/s a nv5; poco alcance contra manadas. |
| **B** | Espada Ligera | 91.9 % | Sin papel propio: Dagas en daño y Larga en alcance la superan. |
| **C** | Arco | 89.4 % | Seguro pero poco daño y gasta energía; más muertes (5.7). |
| **C** | Escudo | 86.6 % | Bloquea todo de frente pero no hace daño. |

### 3.2 Habilidades

| Tier | Habilidad | Llega a nv20 | Motivo |
|---|---|---|---|
| **S** | Carga de Fuego | 99.7 % | Mucho daño a distancia; 1 muerte de media. |
| **S** | Invocar Lobos | 96.9 % | Demasiado fuerte a nivel 1 (≈24 de daño/s) y se llevan los golpes. **Ajuste pendiente.** |
| **S → ?** | Disparo Veloz | 99.0 % | Barata y casi instantánea. **Nerfeada el 24/11**: hay que volver a medirla. |
| **A** | Onda Sonora | 97.1 % | Mejor daño por energía, en área y ralentiza. |
| **A** | Cortar | 96.3 % | Daño a distancia y anula el escudo mágico. |
| **B** | Paso 0 | 91.0 % | No hace daño pero es la mejor para escapar (2 muertes de media). |
| **B** | Burst de Fuerza / Golpe de Suerte / Reforzamiento Mágico | ≈90 % | Útiles pero dependientes (solo el arma, azar, o solapadas con la invulnerabilidad nueva). |
| **B−** | Destello | 89.3 % | Barata para huir o perseguir; no mata. |
| **C** | Invocar Conejos, Sombra Araña, Regeneración Inversa, Aura Eléctrica | 88.6 – 90.6 % | Lentas, caras o con autodaño. |
| **D** | Disparo Venenoso | 85.1 % | 7.1 muertes de media, 30 s de recarga y el escudo mágico le quita el 90 %. |

### 3.3 Anillos y tótem

| Tier | Objeto | Motivo |
|---|---|---|
| **S+** | Tótem de vida | Evita perderlo todo al morir. |
| **S** | Regeneración inversa (legendario), Vida (épico) | +0.9 vida/s siempre; +20 de vida (dos tercios de la vida inicial). |
| **A** | Cadencia (épico), Sombra lobo (épico) | Casi duplica el daño de un arma; defensa muy fuerte. |
| **B** | Defensa física | Absorbe mordidas y zarpazos. |
| **C** | Fuerza, Viento, Energía, Sombra conejo | Efectos pequeños. |
| **D** | Defensa mágica | Casi no hay daño mágico enemigo (solo ondas de 5 – 10). |

## 4. Pendiente: siguientes fases de balance (propuestas, no aplicadas)

1. **Invocar Lobos (demasiado fuerte, prioridad):** daño **4 → 30** en vez de 8 → 30 y desangrado del 33 % al **20 %**.
2. **Volver a medir** con la simulación: el nerf de Disparo Veloz, las 5 potenciadas y la economía del Gacha (15 / 20).
3. **Regeneración Inversa (débil):** bajar el coste a ~6 de energía por vida o que cada nivel cueste 1 punto en vez de 2.
4. **Paso 0 (débil):** darle un plus (p. ej. +50 % de daño en el primer ataque desde la invisibilidad) o bajar el coste de nv1 a 20.
5. **Espada Ligera (sin papel):** darle un rasgo propio (más cadencia o no desgastarse en los choques).
6. **Disparo Venenoso y anillo de Defensa mágica (los más flojos).**
7. **Lobo solitario (vigilar):** con 10 XP y 10 monedas fijas es la mejor fuente de XP del bot; si se nota en partida, bajar a 6 – 8 XP.
8. **Estrella Ígnea (vigilar):** una carga de 5 s o más borra una manada de lobos normales con la explosión (29 – 38 de daño en 100 px).
9. **Nivel 20 → 40:** con solo la fauna actual se tarda ≈10 h (14.5 XP/min); depende de los enemigos nuevos.
10. **Habilidades potenciadas pendientes de diseñar:** Invocar Conejos, Invocar Lobos, Cortar, Onda Sonora, Reforzamiento Mágico, Regeneración Inversa, Golpe de Suerte, Sombra Araña, Paso 0 y Disparo Venenoso.

## 5. Pendientes de documentación

- Ninguno al 24/11/2026: especificación, tablas (`.md` y `.xlsx`), fauna, XP y Gacha están al día con el código.
