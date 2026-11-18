# LEVEL_UP — Tablas de escalado por nivel

> Valores generados a partir del código actual (`herramientas.py` y `habilidades.py`).
> Los daños de ejemplo usan la fuerza inicial del personaje (2); el daño real escala con la fuerza actual.

---

## 1. Herramientas (armas)

Se sacan o guardan con **[1]**. Nivel máximo **5**. Cada mejora cuesta **2 puntos** y repara toda la durabilidad. La velocidad indica el modificador mientras el arma está desenfundada (negativo = debuff, positivo = buff).

### 1.1 Espada Ligera

Arma equilibrada: daño moderado y poca penalización de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. |
|---|---|---|---|---|
| 1 | ×2.2 | 4.4 | -17 % | 220 |
| 2 | ×2.4 | 4.8 | -14 % | 240 |
| 3 | ×2.6 | 5.2 | -11 % | 260 |
| 4 | ×2.8 | 5.6 | -8 % | 280 |
| 5 | ×3 | 6 | -5 % | 300 |

### 1.2 Espada Larga

Más larga y potente que la ligera, a cambio de más lentitud.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. |
|---|---|---|---|---|
| 1 | ×3.4 | 6.8 | -34 % | 190 |
| 2 | ×3.8 | 7.6 | -28 % | 200 |
| 3 | ×4.2 | 8.4 | -22 % | 210 |
| 4 | ×4.6 | 9.2 | -16 % | 220 |
| 5 | ×5 | 10 | -10 % | 230 |

### 1.3 Mandoble

Arma pesada: el mayor daño del juego con una fuerte penalización de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. |
|---|---|---|---|---|
| 1 | ×6.6 | 13.2 | -70 % | 148 |
| 2 | ×7.2 | 14.4 | -60 % | 156 |
| 3 | ×7.8 | 15.6 | -50 % | 164 |
| 4 | ×8.4 | 16.8 | -40 % | 172 |
| 5 | ×9 | 18 | -30 % | 180 |

### 1.4 Dagas Simples

Dos dagas pequeñas, una por flanco, que comparten durabilidad. A nivel máximo dan un buff de velocidad.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. |
|---|---|---|---|---|
| 1 | ×1.5 | 3 | -20 % | 150 |
| 2 | ×1.75 | 3.5 | -12.5 % | 212 |
| 3 | ×2 | 4 | -5 % | 275 |
| 4 | ×2.25 | 4.5 | +2.5 % | 338 |
| 5 | ×2.5 | 5 | +10 % | 400 |

### 1.5 Escudo

No inflige daño, protege. Cada golpe recibido lo desgasta y empuja al portador 2 puntos de empuje.

| Nivel | Daño (× Fuerza) | Daño con Fuerza 2 | Velocidad | Durabilidad máx. |
|---|---|---|---|---|
| 1 | — | — | -34 % | 100 |
| 2 | — | — | -28 % | 150 |
| 3 | — | — | -22 % | 200 |
| 4 | — | — | -16 % | 250 |
| 5 | — | — | -10 % | 300 |

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

Esfera de energía recta (daño mágico). Su daño es un porcentaje del daño total del personaje. Se destruye al chocar con rocas.

| Nivel | Velocidad proyectil | Daño (% del total) | Recarga | Coste En. |
|---|---|---|---|---|
| 1 | 11 | 20.5 % | 2 s | 15 |
| 2 | 12 | 21 % | 1.92 s | 15 |
| 3 | 13 | 21.5 % | 1.84 s | 15 |
| 4 | 14 | 22 % | 1.76 s | 15 |
| 5 | 15 | 22.5 % | 1.68 s | 20 |
| 6 | 16 | 23 % | 1.61 s | 20 |
| 7 | 17 | 23.5 % | 1.53 s | 20 |
| 8 | 18 | 24 % | 1.45 s | 20 |
| 9 | 19 | 24.5 % | 1.37 s | 20 |
| 10 | 20 | 25 % | 1.29 s | 25 |
| 11 | 21 | 25.5 % | 1.21 s | 25 |
| 12 | 22 | 26 % | 1.13 s | 25 |
| 13 | 23 | 26.5 % | 1.05 s | 25 |
| 14 | 24 | 27 % | 0.97 s | 25 |
| 15 | 25 | 27.5 % | 0.89 s | 30 |
| 16 | 26 | 28 % | 0.82 s | 30 |
| 17 | 27 | 28.5 % | 0.74 s | 30 |
| 18 | 28 | 29 % | 0.66 s | 30 |
| 19 | 29 | 29.5 % | 0.58 s | 30 |
| 20 | 30 | 30 % | 0.5 s | 35 |

### 2.4 Invocar Conejos

Invoca **5 conejos** (daño físico) detrás del personaje. No se puede reinvocar hasta que mueran todos. Con 2 o más vivos nacen floor(vivos/2) cada 10 s, hasta **50**. Al morir todos hay **30 s de recarga**. Las estadísticas son por conejo.

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

Esfera de fuego (daño mágico). Pulsar = disparo rápido; mantener hasta 5 s = más daño y tamaño. Recarga 2 s. Al golpear aplica **quemadura**: 1 de daño por segundo durante 5 s.

**Energía en tiempo real:** al pulsar se cobra el coste base y cada segundo completo de carga cobra su parte. Si no hay energía para el siguiente segundo, la carga se detiene en el nivel ya pagado.

**Escalado por nivel de la habilidad:**

| Nivel | Daño base (sin carga) | Daño a carga máx. (5 s) | Recarga |
|---|---|---|---|
| 1 | 20 | 25 | 2 s |
| 2 | 21 | 26.2 | 2 s |
| 3 | 22 | 27.5 | 2 s |
| 4 | 23 | 28.8 | 2 s |
| 5 | 24 | 30 | 2 s |
| 6 | 25 | 31.2 | 2 s |
| 7 | 26 | 32.5 | 2 s |
| 8 | 27 | 33.8 | 2 s |
| 9 | 28 | 35 | 2 s |
| 10 | 29 | 36.2 | 2 s |
| 11 | 30 | 37.5 | 2 s |
| 12 | 31 | 38.8 | 2 s |
| 13 | 32 | 40 | 2 s |
| 14 | 33 | 41.2 | 2 s |
| 15 | 34 | 42.5 | 2 s |
| 16 | 35 | 43.8 | 2 s |
| 17 | 36 | 45 | 2 s |
| 18 | 37 | 46.2 | 2 s |
| 19 | 38 | 47.5 | 2 s |
| 20 | 39 | 48.8 | 2 s |

**Escalado por segundo de carga** (igual en todos los niveles):

| Carga | Bono de daño | Energía cobrada en ese segundo | Coste total acumulado | Radio de la esfera |
|---|---|---|---|---|
| Sin carga | 0 % | 15 | 15 | 6 px |
| 1 s | +5 % | 5 | 20 | 8 px |
| 2 s | +7 % | 5 | 25 | 11 px |
| 3 s | +10 % | 5 | 30 | 14 px |
| 4 s | +15 % | 5 | 35 | 17 px |
| 5 s | +25 % | 10 | 45 | 22 px |

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

Al lanzarla otorga un resultado aleatorio: una habilidad (Burst de Fuerza, Destello, Reforzamiento Mágico, Regeneración Inversa o Aura Eléctrica) como efecto temporal sin coste extra, energía al máximo, escudos al máximo o nada. La habilidad otorgada sale al nivel del tramo de Golpe de Suerte, con las estadísticas de ese nivel (el Destello otorgado no deja fatiga). En nivel 20 la probabilidad de "nada" baja al 5 % y el resto se reparte a partes iguales. **Bloqueo:** no se puede volver a lanzar hasta que termine lo otorgado; después empieza la recarga. La habilidad otorgada dura según el tramo (la Regeneración usa sus propios tiempos) y un resultado instantáneo (energía, escudos o nada) bloquea durante una espera básica antes de la recarga.

| Nivel | Coste En. | Nivel de la habilidad otorgada | Duración de la habilidad otorgada | Espera (instantáneos) | Recarga | Prob. nada | Prob. de cada resultado |
|---|---|---|---|---|---|---|---|
| 1 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 10 % |
| 2 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 10 % |
| 3 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 10 % |
| 4 | 15 | 1 | 5 s | 5 s | 5 s | 30 % | 10 % |
| 5 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 10 % |
| 6 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 10 % |
| 7 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 10 % |
| 8 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 10 % |
| 9 | 20 | 5 | 10 s | 5 s | 8 s | 30 % | 10 % |
| 10 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 10 % |
| 11 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 10 % |
| 12 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 10 % |
| 13 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 10 % |
| 14 | 25 | 10 | 15 s | 5 s | 12 s | 30 % | 10 % |
| 15 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 10 % |
| 16 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 10 % |
| 17 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 10 % |
| 18 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 10 % |
| 19 | 30 | 15 | 20 s | 5 s | 15 s | 30 % | 10 % |
| 20 | 50 | 20 | 30 s | 2 s | 20 s | 5 % | 13.6 % |

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
