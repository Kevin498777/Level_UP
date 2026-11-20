# LEVEL_UP — Tablas de escalado por nivel

> Valores generados a partir del código actual (`herramientas.py` y `habilidades.py`).
> Los daños de ejemplo usan la fuerza inicial del personaje (2); el daño real escala con la fuerza actual.

---

## 1. Herramientas (armas)

Se sacan o guardan con **[1]**. Nivel máximo **5**. Cada mejora cuesta **2 puntos** y repara toda la durabilidad. La velocidad indica el modificador mientras el arma está desenfundada (negativo = debuff, positivo = buff).

**Cadencia** (golpes por segundo con [Espacio]): la del arma por nivel **más** el bonus de cadencia del personaje (+0.1 por punto de mejora). El tiempo entre golpes es 1 / cadencia; la tabla muestra el del arma sola (bonus 0). **Empuje**: puntos de empuje fijos que aplica cada golpe al enemigo.

### 1.1 Espada Ligera

Arma equilibrada: daño moderado y poca penalización de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. | Cadencia (golpes/s) | Tiempo entre golpes | Empuje |
|---|---|---|---|---|---|---|---|
| 1 | ×2.2 | 4.4 | -17 % | 220 | 1.475 | 0.68 s | 8 |
| 2 | ×2.4 | 4.8 | -14 % | 240 | 1.55 | 0.65 s | 8 |
| 3 | ×2.6 | 5.2 | -11 % | 260 | 1.625 | 0.62 s | 8 |
| 4 | ×2.8 | 5.6 | -8 % | 280 | 1.7 | 0.59 s | 8 |
| 5 | ×3 | 6 | -5 % | 300 | 1.775 | 0.56 s | 8 |

### 1.2 Espada Larga

Más larga y potente que la ligera, a cambio de más lentitud.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. | Cadencia (golpes/s) | Tiempo entre golpes | Empuje |
|---|---|---|---|---|---|---|---|
| 1 | ×3.4 | 6.8 | -34 % | 190 | 1.06 | 0.94 s | 12 |
| 2 | ×3.8 | 7.6 | -28 % | 200 | 1.12 | 0.89 s | 12 |
| 3 | ×4.2 | 8.4 | -22 % | 210 | 1.18 | 0.85 s | 12 |
| 4 | ×4.6 | 9.2 | -16 % | 220 | 1.24 | 0.81 s | 12 |
| 5 | ×5 | 10 | -10 % | 230 | 1.3 | 0.77 s | 12 |

### 1.3 Mandoble

Arma pesada: el mayor daño del juego con una fuerte penalización de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. | Cadencia (golpes/s) | Tiempo entre golpes | Empuje |
|---|---|---|---|---|---|---|---|
| 1 | ×6.6 | 13.2 | -70 % | 148 | 0.64 | 1.56 s | 20 |
| 2 | ×7.2 | 14.4 | -60 % | 156 | 0.68 | 1.47 s | 20 |
| 3 | ×7.8 | 15.6 | -50 % | 164 | 0.72 | 1.39 s | 20 |
| 4 | ×8.4 | 16.8 | -40 % | 172 | 0.76 | 1.32 s | 20 |
| 5 | ×9 | 18 | -30 % | 180 | 0.8 | 1.25 s | 20 |

### 1.4 Dagas Simples

Dos dagas pequeñas, una por flanco, que comparten durabilidad. A nivel máximo dan un buff de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. | Cadencia (golpes/s) | Tiempo entre golpes | Empuje |
|---|---|---|---|---|---|---|---|
| 1 | ×1.5 | 3 | -20 % | 150 | 2.125 | 0.47 s | 4 |
| 2 | ×1.75 | 3.5 | -12.5 % | 212 | 2.25 | 0.44 s | 4 |
| 3 | ×2 | 4 | -5 % | 275 | 2.375 | 0.42 s | 4 |
| 4 | ×2.25 | 4.5 | +2.5 % | 338 | 2.5 | 0.4 s | 4 |
| 5 | ×2.5 | 5 | +10 % | 400 | 2.625 | 0.38 s | 4 |

### 1.5 Escudo

No inflige daño, protege. **Desenfundado** ([1]) bloquea **por completo** los ataques que llegan por su **arco frontal de 120°** (60° a cada lado de hacia donde mira el portador): golpes de arma, proyectiles y mordidas, físicos o mágicos. Se dibuja como una banda curva que ocupa exactamente ese arco. El portador no recibe daño ni efectos; el escudo pierde de durabilidad el **daño bloqueado menos su reducción** y empuja al portador 2 puntos. No bloquea la Onda Sonora, el Aura Eléctrica, el terreno, el autodaño ni los efectos ya aplicados. Cada bloqueo **repele al atacante con 40 puntos de empuje** (más que cualquier arma; el mayor es el Arco con 25). Contra una espada funciona como un choque: el golpe no hace daño y el arma atacante pierde 1 de durabilidad.

**Pasiva:** mientras sea la herramienta del personaje y **no esté roto** (enfundado o no), sube los **máximos** de escudo físico y mágico un porcentaje de su base (con 0 de escudo sigue en 0).

| Nivel | Velocidad (desenfundado) | Durabilidad máx. | Reducción del desgaste | Durabilidad gastada por 100 de daño | Bonus a los escudos |
|---|---|---|---|---|---|
| 1 | -34 % | 100 | 20 % | 80 | +15 % |
| 2 | -28 % | 150 | 32.5 % | 67.5 | +18.75 % |
| 3 | -22 % | 200 | 45 % | 55 | +22.5 % |
| 4 | -16 % | 250 | 57.5 % | 42.5 | +26.25 % |
| 5 | -10 % | 300 | 70 % | 30 | +30 % |

### 1.6 Arco

Arma de **daño físico** a distancia: no golpea cuerpo a cuerpo. Mantener **[Espacio]** carga la flecha y soltar la dispara; cuentan los segundos completos de carga (menos de 1 s no dispara; desde 5 s se queda al 100 %). Mientras carga, **−10 %** de velocidad extra. La flecha se detiene en el primer enemigo (empuje **25**, gasta 1 de durabilidad si hace daño), las rocas la bloquean y atraviesa los arbustos; si no choca, queda clavada 3 s al final del alcance. Flechas en **lotes de 10** comprados con energía ([R]); lo que no cabe en el carcaj se pierde.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 (carga 5 s) | Velocidad | Durabilidad máx. | Carcaj | Lote de 10 flechas | Empuje |
|---|---|---|---|---|---|---|---|
| 1 | ×5 | 10 | -15 % | 100 | 10 | 10 En. | 25 |
| 2 | ×6.25 | 12.5 | -12 % | 110 | 15 | 15 En. | 25 |
| 3 | ×7.5 | 15 | -9 % | 120 | 20 | 20 En. | 25 |
| 4 | ×8.75 | 17.5 | -6 % | 130 | 25 | 25 En. | 25 |
| 5 | ×10 | 20 | -3 % | 150 | 30 | 30 En. | 25 |

**Escalado por segundo de carga** (igual en todos los niveles):

| Carga | Alcance | Daño (% del daño del arma) | Daño con Fuerza 2, nivel 1 |
|---|---|---|---|
| < 1 s | — | no dispara | — |
| 1 s | 100 | 20 % | 2 |
| 2 s | 150 | 40 % | 4 |
| 3 s | 200 | 60 % | 6 |
| 4 s | 250 | 80 % | 8 |
| 5 s o más | 300 | 100 % | 10 |

---

## 2. Habilidades

Se equipan en **[2] [3] [4]**. Nivel máximo **20**. Cada mejora cuesta **1 punto**. Lanzar una habilidad con otra activa cuesta además un **+5 % de la energía actual** (combo).

### 2.1 Destello

Buff de velocidad temporal. Al terminar deja una fatiga (debuff de velocidad) durante la recarga.

| Nivel | Buff velocidad | Duración | Recarga | Fatiga (debuff) | Coste En. |
|---|---|---|---|---|---|
| 1 | +52 % | 10 s | 5 s | -20 % | 10 |
| 2 | +54 % | 10 s | 5 s | -20 % | 10 |
| 3 | +56 % | 10 s | 5 s | -20 % | 15 |
| 4 | +58 % | 10 s | 5 s | -20 % | 15 |
| 5 | +60 % | 12 s | 4 s | -15 % | 15 |
| 6 | +62 % | 12 s | 4 s | -15 % | 20 |
| 7 | +64 % | 12 s | 4 s | -15 % | 20 |
| 8 | +66 % | 12 s | 4 s | -15 % | 20 |
| 9 | +68 % | 12 s | 4 s | -15 % | 25 |
| 10 | +70 % | 14 s | 3 s | -10 % | 25 |
| 11 | +72 % | 14 s | 3 s | -10 % | 25 |
| 12 | +74 % | 14 s | 3 s | -10 % | 30 |
| 13 | +76 % | 14 s | 3 s | -10 % | 30 |
| 14 | +78 % | 14 s | 3 s | -10 % | 30 |
| 15 | +80 % | 16 s | 2 s | -5 % | 35 |
| 16 | +82 % | 16 s | 2 s | -5 % | 35 |
| 17 | +84 % | 16 s | 2 s | -5 % | 35 |
| 18 | +86 % | 16 s | 2 s | -5 % | 40 |
| 19 | +88 % | 16 s | 2 s | -5 % | 40 |
| 20 | +90 % | 18 s | 1 s | 0 % | 40 |

### 2.2 Burst de Fuerza

Buff de fuerza temporal; potencia el golpe del arma (el daño sigue siendo físico).

| Nivel | Buff fuerza | Duración | Recarga | Coste En. |
|---|---|---|---|---|
| 1 | +21 % | 6 s | 12 s | 15 |
| 2 | +22 % | 6 s | 12 s | 15 |
| 3 | +23 % | 6 s | 12 s | 15 |
| 4 | +24 % | 6 s | 12 s | 15 |
| 5 | +25 % | 7 s | 11 s | 20 |
| 6 | +26 % | 7 s | 11 s | 20 |
| 7 | +27 % | 7 s | 11 s | 20 |
| 8 | +28 % | 7 s | 11 s | 20 |
| 9 | +29 % | 7 s | 11 s | 20 |
| 10 | +30 % | 8 s | 10 s | 25 |
| 11 | +31 % | 8 s | 10 s | 25 |
| 12 | +32 % | 8 s | 10 s | 25 |
| 13 | +33 % | 8 s | 10 s | 25 |
| 14 | +34 % | 8 s | 10 s | 25 |
| 15 | +35 % | 9 s | 9 s | 30 |
| 16 | +36 % | 9 s | 9 s | 30 |
| 17 | +37 % | 9 s | 9 s | 30 |
| 18 | +38 % | 9 s | 9 s | 30 |
| 19 | +39 % | 9 s | 9 s | 30 |
| 20 | +40 % | 10 s | 8 s | 35 |

### 2.3 Disparo Veloz

Esfera de energía recta (daño mágico) **muy rápida**: la velocidad del proyectil es su punto fuerte. Daño **fijo** (ya no depende del arma). Se destruye al chocar con rocas (también comprueba el trayecto de cada frame para no saltarse rocas pequeñas).

| Nivel | Velocidad proyectil | Daño | Recarga | Coste En. |
|---|---|---|---|---|
| 1 | 14 | 8 | 2 s | 15 |
| 2 | 15.4 | 9.2 | 1.92 s | 15 |
| 3 | 16.7 | 10.3 | 1.84 s | 15 |
| 4 | 18.1 | 11.5 | 1.76 s | 15 |
| 5 | 19.5 | 12.6 | 1.68 s | 20 |
| 6 | 20.8 | 13.8 | 1.61 s | 20 |
| 7 | 22.2 | 14.9 | 1.53 s | 20 |
| 8 | 23.6 | 16.1 | 1.45 s | 20 |
| 9 | 24.9 | 17.3 | 1.37 s | 20 |
| 10 | 26.3 | 18.4 | 1.29 s | 25 |
| 11 | 27.7 | 19.6 | 1.21 s | 25 |
| 12 | 29.1 | 20.7 | 1.13 s | 25 |
| 13 | 30.4 | 21.9 | 1.05 s | 25 |
| 14 | 31.8 | 23.1 | 0.97 s | 25 |
| 15 | 33.2 | 24.2 | 0.89 s | 30 |
| 16 | 34.5 | 25.4 | 0.82 s | 30 |
| 17 | 35.9 | 26.5 | 0.74 s | 30 |
| 18 | 37.3 | 27.7 | 0.66 s | 30 |
| 19 | 38.6 | 28.8 | 0.58 s | 30 |
| 20 | 40 | 30 | 0.5 s | 35 |

### 2.4 Invocar Conejos

Invoca **5 conejos** (daño físico) detrás del personaje. No se puede reinvocar hasta que mueran todos. Con 2 o más vivos nacen floor(vivos/2) cada **10 s × (1 + vivos / 10)** (5 vivos: 15 s; 20 vivos: 30 s; 40 vivos: 50 s), hasta **50**: de 5 a 20 conejos en ~77 s y a 50 en ~3.5 min. Al morir todos hay **30 s de recarga**. Las estadísticas son por conejo.

| Nivel | Vida | Velocidad | Daño | Coste En. |
|---|---|---|---|---|
| 1 | 5 | 3 | 0.1 | 80 |
| 2 | 5 | 3.5 | 0.5 | 80 |
| 3 | 5 | 4 | 0.9 | 80 |
| 4 | 8 | 4.5 | 1.3 | 80 |
| 5 | 8 | 5 | 1.7 | 80 |
| 6 | 8 | 5.5 | 2.1 | 80 |
| 7 | 8 | 6 | 2.5 | 80 |
| 8 | 11 | 6.5 | 2.9 | 80 |
| 9 | 11 | 7 | 3.3 | 80 |
| 10 | 11 | 7.5 | 3.7 | 80 |
| 11 | 11 | 8 | 4.1 | 80 |
| 12 | 14 | 8.5 | 4.5 | 80 |
| 13 | 14 | 9 | 4.9 | 80 |
| 14 | 14 | 9.5 | 5.3 | 80 |
| 15 | 14 | 10 | 5.7 | 80 |
| 16 | 17 | 10.5 | 6.1 | 80 |
| 17 | 17 | 11 | 6.5 | 80 |
| 18 | 17 | 11.5 | 6.9 | 80 |
| 19 | 17 | 12 | 7.3 | 80 |
| 20 | 20 | 12.5 | 7.7 | 80 |

### 2.5 Carga de Fuego

Esfera de fuego (daño mágico). Pulsar = disparo rápido; mantener hasta 5 s = más daño, tamaño y quemadura. Al golpear aplica **quemadura** (1 de daño por segundo, ignora escudos) con una duración que depende de la carga. La **recarga** también depende de la carga: **8 s** sin carga hasta **15 s** a carga máxima.

**Energía en tiempo real:** al pulsar se cobra el coste base y cada segundo completo de carga cobra su parte. Si no hay energía para el siguiente segundo, la carga se detiene en el nivel ya pagado.

**Escalado por nivel de la habilidad:**

| Nivel | Daño base | Daño sin carga (x0.6) | Daño a carga máx. (x2.0) |
|---|---|---|---|
| 1 | 20 | 12 | 40 |
| 2 | 21 | 12.6 | 42 |
| 3 | 22 | 13.2 | 44 |
| 4 | 23 | 13.8 | 46 |
| 5 | 24 | 14.4 | 48 |
| 6 | 25 | 15 | 50 |
| 7 | 26 | 15.6 | 52 |
| 8 | 27 | 16.2 | 54 |
| 9 | 28 | 16.8 | 56 |
| 10 | 29 | 17.4 | 58 |
| 11 | 30 | 18 | 60 |
| 12 | 31 | 18.6 | 62 |
| 13 | 32 | 19.2 | 64 |
| 14 | 33 | 19.8 | 66 |
| 15 | 34 | 20.4 | 68 |
| 16 | 35 | 21 | 70 |
| 17 | 36 | 21.6 | 72 |
| 18 | 37 | 22.2 | 74 |
| 19 | 38 | 22.8 | 76 |
| 20 | 39 | 23.4 | 78 |

**Escalado por segundo de carga** (igual en todos los niveles):

| Carga | Multiplicador del daño base | Quemadura | Recarga | Energía cobrada en ese segundo | Coste total acumulado | Radio de la esfera |
|---|---|---|---|---|---|---|
| Sin carga | x0.6 | 2 s | 8 s | 15 | 15 | 6 px |
| 1 s | x0.8 | 3 s | 9.4 s | 5 | 20 | 8 px |
| 2 s | x1.0 | 4 s | 10.8 s | 5 | 25 | 11 px |
| 3 s | x1.3 | 5 s | 12.2 s | 5 | 30 | 14 px |
| 4 s | x1.6 | 6 s | 13.6 s | 5 | 35 | 17 px |
| 5 s | x2.0 | 7 s | 15 s | 10 | 45 | 22 px |

### 2.6 Aura Eléctrica

Aura de radio 100 px que sigue al personaje: buff de velocidad y daño por segundo a los enemigos cercanos. Mientras está activa, el portador recibe un autodaño mágico (lo amortigua su escudo mágico).

| Nivel | Buff velocidad | Daño/s a enemigos | Autodaño/s | Duración | Recarga | Coste En. |
|---|---|---|---|---|---|---|
| 1 | +5 % | 1 | 0.5 | 10 s | 40 s | 20 |
| 2 | +5 % | 1 | 0.5 | 10 s | 40 s | 22 |
| 3 | +5 % | 1 | 0.5 | 10 s | 40 s | 24 |
| 4 | +5 % | 1 | 0.5 | 10 s | 40 s | 26 |
| 5 | +7.5 % | 2 | 0.5 | 12.5 s | 45 s | 28 |
| 6 | +7.5 % | 2 | 0.5 | 12.5 s | 45 s | 30 |
| 7 | +7.5 % | 2 | 0.5 | 12.5 s | 45 s | 32 |
| 8 | +7.5 % | 2 | 0.5 | 12.5 s | 45 s | 34 |
| 9 | +7.5 % | 2 | 0.5 | 12.5 s | 45 s | 36 |
| 10 | +10 % | 3 | 0.5 | 15 s | 50 s | 38 |
| 11 | +10 % | 3 | 0.5 | 15 s | 50 s | 40 |
| 12 | +10 % | 3 | 0.5 | 15 s | 50 s | 42 |
| 13 | +10 % | 3 | 0.5 | 15 s | 50 s | 44 |
| 14 | +10 % | 3 | 0.5 | 15 s | 50 s | 46 |
| 15 | +12.5 % | 4 | 0.5 | 17.5 s | 55 s | 48 |
| 16 | +12.5 % | 4 | 0.5 | 17.5 s | 55 s | 50 |
| 17 | +12.5 % | 4 | 0.5 | 17.5 s | 55 s | 52 |
| 18 | +12.5 % | 4 | 0.5 | 17.5 s | 55 s | 54 |
| 19 | +12.5 % | 4 | 0.5 | 17.5 s | 55 s | 56 |
| 20 | +15 % | 5 | 0.5 | 20 s | 60 s | 58 |

### 2.7 Reforzamiento Mágico

Campo de fuerza azul celeste (solo contorno), un 10 % más grande que el personaje, que bloquea daño físico y mágico. Absorbe todo el daño hasta agotar su dureza; si se agota antes de terminar la duración se rompe, entra en recarga y el sobrante pasa a los escudos y a la vida.

| Nivel | Dureza | Duración | Recarga | Coste En. |
|---|---|---|---|---|
| 1 | 200 | 1 s | 10 s | 25 |
| 2 | 215 | 1 s | 10 s | 25 |
| 3 | 230 | 1 s | 10 s | 25 |
| 4 | 245 | 1 s | 10 s | 25 |
| 5 | 260 | 2 s | 15 s | 30 |
| 6 | 275 | 2 s | 15 s | 30 |
| 7 | 290 | 2 s | 15 s | 30 |
| 8 | 305 | 2 s | 15 s | 30 |
| 9 | 320 | 2 s | 15 s | 30 |
| 10 | 335 | 3 s | 20 s | 35 |
| 11 | 350 | 3 s | 20 s | 35 |
| 12 | 365 | 3 s | 20 s | 35 |
| 13 | 380 | 3 s | 20 s | 35 |
| 14 | 395 | 3 s | 20 s | 35 |
| 15 | 410 | 4 s | 25 s | 40 |
| 16 | 425 | 4 s | 25 s | 40 |
| 17 | 440 | 4 s | 25 s | 40 |
| 18 | 455 | 4 s | 25 s | 40 |
| 19 | 470 | 4 s | 25 s | 40 |
| 20 | 500 | 6 s | 35 s | 50 |

### 2.8 Regeneración Inversa

Habilidad mágica que se **mantiene pulsada**, sin recarga. Cada intervalo completo cobra energía y cura vida (sin pasar de la vida máxima); si no hay energía suficiente deja de curar. Nivel máximo **10**; cada mejora cuesta **2 puntos**. Mientras está activa muestra un contorno rosa.

| Nivel | Vida curada | Energía gastada | Intervalo | Vida por segundo | Energía por vida |
|---|---|---|---|---|---|
| 1 | +1 | -10 | 2 s | 0.5 | 10 |
| 2 | +1 | -10 | 2 s | 0.5 | 10 |
| 3 | +2 | -15 | 2 s | 1 | 7.5 |
| 4 | +2 | -15 | 2 s | 1 | 7.5 |
| 5 | +2 | -15 | 2 s | 1 | 7.5 |
| 6 | +3 | -20 | 2 s | 1.5 | 6.67 |
| 7 | +3 | -20 | 2 s | 1.5 | 6.67 |
| 8 | +3 | -20 | 2 s | 1.5 | 6.67 |
| 9 | +4 | -25 | 2 s | 2 | 6.25 |
| 10 | +6 | -40 | 3 s | 2 | 6.67 |

### 2.9 Golpe de Suerte

Al lanzarla otorga un resultado aleatorio: una habilidad (Burst de Fuerza, Destello, Reforzamiento Mágico, Regeneración Inversa, Aura Eléctrica o Paso 0) como efecto temporal sin coste extra, energía al máximo, escudos al máximo, Disparo Venenoso (negativo: envenena al portador con la mitad del daño del veneno de ese nivel y la misma duración) o nada. La habilidad otorgada sale al nivel del tramo de Golpe de Suerte, con las estadísticas de ese nivel (el Destello otorgado no deja fatiga). "Nada" tiene un 30 % y los otros 9 resultados se reparten el resto a partes iguales; en nivel 20 "nada" baja al 5 %. Paso 0 otorgado no pasa de su nivel máximo (10). **Bloqueo:** no se puede volver a lanzar hasta que termine lo otorgado; después empieza la recarga. La habilidad otorgada dura según el tramo (la Regeneración usa sus propios tiempos) y un resultado instantáneo (energía, escudos o nada) bloquea durante una espera básica antes de la recarga.

| Nivel | Coste En. | Nivel de la habilidad otorgada | Duración de la habilidad otorgada | Espera (instantáneos) | Recarga | Prob. nada | Prob. de cada resultado |
|---|---|---|---|---|---|---|---|
| 1 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 7.78 % |
| 2 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 7.78 % |
| 3 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 7.78 % |
| 4 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 7.78 % |
| 5 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 7.78 % |
| 6 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 7.78 % |
| 7 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 7.78 % |
| 8 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 7.78 % |
| 9 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 7.78 % |
| 10 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 7.78 % |
| 11 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 7.78 % |
| 12 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 7.78 % |
| 13 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 7.78 % |
| 14 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 7.78 % |
| 15 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 7.78 % |
| 16 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 7.78 % |
| 17 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 7.78 % |
| 18 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 7.78 % |
| 19 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 7.78 % |
| 20 | 50 | 20 | 30 s | 2 s | 20 s | 5 % | 10.56 % |

**Regeneración Inversa otorgada** (cura sola, sin pulsar ni gastar energía):

| Nivel de Golpe de Suerte | Duración | Vida curada | Intervalo | Vida total |
|---|---|---|---|---|
| 1 – 4 | 4 s | +1 | 2 s | +2 |
| 5 – 9 | 6 s | +1 | 2 s | +3 |
| 10 – 14 | 8 s | +1 | 2 s | +4 |
| 15 – 19 | 10 s | +2 | 2 s | +10 |
| 20 | 10 s | +2 | 1 s | +20 |

### 2.10 Invocar Lobos

Invoca **3 lobos** (daño físico) detrás del personaje. No se puede reinvocar hasta que mueran todos; al morir el último hay **30 s de recarga**. Segunda de las 10 Artes de las Sombras. Cada golpe tiene un **33 %** de causar **desangrado** (5 golpes de 1 vida, uno cada 2 s; activo hasta el último golpe, no acumulable, y -50 % a toda curación). Las estadísticas son por lobo.

| Nivel | Vida | Velocidad | Daño | Coste En. |
|---|---|---|---|---|
| 1 | 10 | 10 | 8 | 90 |
| 2 | 13 | 10 | 9.16 | 90 |
| 3 | 16 | 10 | 10.32 | 90 |
| 4 | 19 | 10 | 11.47 | 90 |
| 5 | 22 | 12 | 12.63 | 90 |
| 6 | 25 | 12 | 13.79 | 90 |
| 7 | 28 | 12 | 14.95 | 90 |
| 8 | 31 | 12 | 16.11 | 90 |
| 9 | 34 | 12 | 17.26 | 90 |
| 10 | 37 | 14 | 18.42 | 90 |
| 11 | 40 | 14 | 19.58 | 90 |
| 12 | 43 | 14 | 20.74 | 90 |
| 13 | 46 | 14 | 21.89 | 90 |
| 14 | 49 | 14 | 23.05 | 90 |
| 15 | 52 | 16 | 24.21 | 90 |
| 16 | 55 | 16 | 25.37 | 90 |
| 17 | 58 | 16 | 26.53 | 90 |
| 18 | 61 | 16 | 27.68 | 90 |
| 19 | 64 | 16 | 28.84 | 90 |
| 20 | 67 | 18 | 30 | 90 |

### 2.11 Cortar

Habilidad de **daño mágico**. Lanza una cuchilla recta (negra con contorno rojo, del largo de la Espada Ligera) que se detiene en el **primer enemigo**. Lanzada desde dentro de un arbusto no lo corta. Si llega a hacer daño, **anula el escudo mágico** del enemigo **8 s** (queda en 0 sin regenerar y luego vuelve al valor que tenía tras el golpe; otro corte reinicia los 8 s). Al chocar con una **roca o un arbusto** lo destruye y se rompe (solo un objeto); las **rocas gigantes** y los **arbustos grandes** (más de 100 de diámetro) solo se destruyen a **nivel 20**. Daño **5 → 40** lineal (redondeado a 1 decimal). La recarga **sube** con el nivel a propósito.

| Nivel | Daño | Velocidad | Coste En. | Recarga | Corta gigantes/grandes |
|---|---|---|---|---|---|
| 1 | 5 | 5 | 15 | 2 s | No |
| 2 | 6.8 | 6 | 17 | 2 s | No |
| 3 | 8.7 | 7 | 19 | 2 s | No |
| 4 | 10.5 | 8 | 21 | 2 s | No |
| 5 | 12.4 | 9 | 23 | 4 s | No |
| 6 | 14.2 | 10 | 25 | 4 s | No |
| 7 | 16.1 | 11 | 27 | 4 s | No |
| 8 | 17.9 | 12 | 29 | 4 s | No |
| 9 | 19.7 | 13 | 31 | 4 s | No |
| 10 | 21.6 | 14 | 33 | 6 s | No |
| 11 | 23.4 | 15 | 35 | 6 s | No |
| 12 | 25.3 | 16 | 37 | 6 s | No |
| 13 | 27.1 | 17 | 39 | 6 s | No |
| 14 | 28.9 | 18 | 41 | 6 s | No |
| 15 | 30.8 | 19 | 43 | 8 s | No |
| 16 | 32.6 | 20 | 45 | 8 s | No |
| 17 | 34.5 | 21 | 47 | 8 s | No |
| 18 | 36.3 | 22 | 49 | 8 s | No |
| 19 | 38.2 | 23 | 51 | 8 s | No |
| 20 | 40 | 24 | 53 | 10 s | Sí |

### 2.12 Onda Sonora

Habilidad de **daño mágico** en área: anillos blancos en 360°, uno cada **0.8 s**, todos desde el punto de lanzamiento (no siguen al personaje). Daño fijo por onda: **10** (1.ª), **20** (2.ª, desde nivel 10) y **30** (3.ª, a nivel 20). Atraviesan obstáculos sin destruir nada y solo afectan a enemigos. Ralentiza **-5 / -10 / -20 %** durante 3 s según cuántas ondas golpeen. Agua → agua: daño y ralentización x2; cambio de medio: x0.5. Velocidad de la onda **300 px/s** (600 si se lanza desde el agua).

| Nivel | Ondas (daño) | Radio | Coste En. | Recarga |
|---|---|---|---|---|
| 1 | 1 (10) | 200 | 10 | 10 s |
| 2 | 1 (10) | 210.5 | 10 | 11.05 s |
| 3 | 1 (10) | 221.1 | 10 | 12.11 s |
| 4 | 1 (10) | 231.6 | 10 | 13.16 s |
| 5 | 1 (10) | 242.1 | 15 | 14.21 s |
| 6 | 1 (10) | 252.6 | 15 | 15.26 s |
| 7 | 1 (10) | 263.2 | 15 | 16.32 s |
| 8 | 1 (10) | 273.7 | 15 | 17.37 s |
| 9 | 1 (10) | 284.2 | 15 | 18.42 s |
| 10 | 2 (10 + 20) | 294.7 | 20 | 19.47 s |
| 11 | 2 (10 + 20) | 305.3 | 20 | 20.53 s |
| 12 | 2 (10 + 20) | 315.8 | 20 | 21.58 s |
| 13 | 2 (10 + 20) | 326.3 | 20 | 22.63 s |
| 14 | 2 (10 + 20) | 336.8 | 20 | 23.68 s |
| 15 | 2 (10 + 20) | 347.4 | 25 | 24.74 s |
| 16 | 2 (10 + 20) | 357.9 | 25 | 25.79 s |
| 17 | 2 (10 + 20) | 368.4 | 25 | 26.84 s |
| 18 | 2 (10 + 20) | 378.9 | 25 | 27.89 s |
| 19 | 2 (10 + 20) | 389.5 | 25 | 28.95 s |
| 20 | 3 (10 + 20 + 30) | 400 | 30 | 30 s |

### 2.13 Sombra Araña

Tercera de las Artes de las Sombras. Invoca **una araña** (1 HP, sin ataque, velocidad 6) detrás del personaje. Manteniendo la tecla (ojos rojos) el **clic derecho** la envía a un **punto** (no persigue enemigos); al llegar teje una **telaraña** de un solo uso, de radio 1.6 veces el del personaje, que **inmoviliza** (no puede moverse, pero sí atacar) al primer enemigo que la pise. Máximo **3 telarañas** (la nueva quita la más vieja). Tras tejer, o si la araña muere antes, hay **5 s de recarga**. A **nivel 20** la telaraña además hace **1 de daño mágico por segundo** mientras dura la inmovilización (lo amortigua el escudo mágico del enemigo). Coste e inmovilización escalan de forma lineal (redondeados).

| Nivel | Coste En. | Inmovilización | Daño mágico telaraña (por s) | Recarga |
|---|---|---|---|---|
| 1 | 50 | 5 s | 0 | 5 s |
| 2 | 53 | 5.8 s | 0 | 5 s |
| 3 | 55 | 6.6 s | 0 | 5 s |
| 4 | 58 | 7.4 s | 0 | 5 s |
| 5 | 61 | 8.2 s | 0 | 5 s |
| 6 | 63 | 8.9 s | 0 | 5 s |
| 7 | 66 | 9.7 s | 0 | 5 s |
| 8 | 68 | 10.5 s | 0 | 5 s |
| 9 | 71 | 11.3 s | 0 | 5 s |
| 10 | 74 | 12.1 s | 0 | 5 s |
| 11 | 76 | 12.9 s | 0 | 5 s |
| 12 | 79 | 13.7 s | 0 | 5 s |
| 13 | 82 | 14.5 s | 0 | 5 s |
| 14 | 84 | 15.3 s | 0 | 5 s |
| 15 | 87 | 16.1 s | 0 | 5 s |
| 16 | 89 | 16.8 s | 0 | 5 s |
| 17 | 92 | 17.6 s | 0 | 5 s |
| 18 | 95 | 18.4 s | 0 | 5 s |
| 19 | 97 | 19.2 s | 0 | 5 s |
| 20 | 100 | 20 s | 1 | 5 s |

### 2.14 Paso 0

Potenciador **mágico**: vuelve invisible al personaje (no a sus invocaciones). Los enemigos no lo detectan (no lo miran ni inician ataques contra él), pero sí puede recibir daño. Dura todo su tiempo aunque ataque o reciba daño; la recarga empieza al terminar. El mapa se oscurece como dentro de un arbusto (sin oscurecerse el doble). Nivel máximo **10**; cada mejora cuesta **2 puntos**. Valores por tramos.

| Nivel | Invisibilidad | Coste En. | Recarga |
|---|---|---|---|
| 1 | 3 s | 30 | 6 s |
| 2 | 3 s | 30 | 6 s |
| 3 | 4 s | 35 | 8 s |
| 4 | 4 s | 35 | 8 s |
| 5 | 5 s | 40 | 10 s |
| 6 | 5 s | 40 | 10 s |
| 7 | 5 s | 40 | 10 s |
| 8 | 6 s | 50 | 12 s |
| 9 | 6 s | 50 | 12 s |
| 10 | 8 s | 60 | 16 s |

### 2.15 Disparo Venenoso

Habilidad de **daño mágico**: esfera verde (núcleo morado, velocidad 12) que se detiene en el primer enemigo y lo **envenena**; el impacto no daña ni empuja. El veneno hace su daño total repartido en su duración (un golpe por segundo), lo amortigua el escudo mágico y no se acumula (reinicia). Escalado **lineal** (coste 20 → 45 En.).

| Nivel | Coste En. | Veneno total | Duración | Daño por segundo | Recarga |
|---|---|---|---|---|---|
| 1 | 20 | 20 | 20 s | 1 | 30 s |
| 2 | 21 | 21.1 | 19.5 s | 1.08 | 29.2 s |
| 3 | 23 | 22.1 | 18.9 s | 1.17 | 28.4 s |
| 4 | 24 | 23.2 | 18.4 s | 1.26 | 27.6 s |
| 5 | 25 | 24.2 | 17.9 s | 1.35 | 26.8 s |
| 6 | 27 | 25.3 | 17.4 s | 1.45 | 26.1 s |
| 7 | 28 | 26.3 | 16.8 s | 1.57 | 25.3 s |
| 8 | 29 | 27.4 | 16.3 s | 1.68 | 24.5 s |
| 9 | 31 | 28.4 | 15.8 s | 1.8 | 23.7 s |
| 10 | 32 | 29.5 | 15.3 s | 1.93 | 22.9 s |
| 11 | 33 | 30.5 | 14.7 s | 2.07 | 22.1 s |
| 12 | 34 | 31.6 | 14.2 s | 2.23 | 21.3 s |
| 13 | 36 | 32.6 | 13.7 s | 2.38 | 20.5 s |
| 14 | 37 | 33.7 | 13.2 s | 2.55 | 19.7 s |
| 15 | 38 | 34.7 | 12.6 s | 2.75 | 18.9 s |
| 16 | 40 | 35.8 | 12.1 s | 2.96 | 18.2 s |
| 17 | 41 | 36.8 | 11.6 s | 3.17 | 17.4 s |
| 18 | 42 | 37.9 | 11.1 s | 3.41 | 16.6 s |
| 19 | 44 | 38.9 | 10.5 s | 3.7 | 15.8 s |
| 20 | 45 | 40 | 10 s | 4 | 15 s |

**Autoveneno de Golpe de Suerte** (resultado negativo): mitad del daño total, misma duración, al nivel del tramo (nv1 → 10 en 20 s · nv5 → 12.1 en 17.9 s · nv10 → 14.75 en 15.3 s · nv15 → 17.35 en 12.6 s · nv20 → 20 en 10 s).
