# Plan por fases — Personajes NPC (razas) en el mundo

Documento de planificación (26/11/2026; añadida la Fase 2 del mundo fijo, cuadrado de 17 700 px y el personaje de inspección ShadowGOD). **Aún no hay nada implementado.** Describe cómo añadir al mundo personajes controlados por la máquina (humanos, semihumanos, elfos, enanos y el guardián) que suben de nivel, usan armas y habilidades y pelean entre ellos, con la fauna y con el jugador, **sin romper lo que ya funciona y sin hundir el rendimiento**.

Cada fase se entrega por separado, con sus pruebas automáticas (las hace Claude), su lista de comprobación manual (la haces tú jugando), su medición de rendimiento y su commit. No se empieza una fase hasta que la anterior esté probada por los dos.

---

## Índice

0. Preparación: pruebas en el proyecto, medición base y **semilla fija**
1. Combate general (todo personaje es un "combatiente")
2. **Mundo fijo:** mapa guardado en archivo, diseñado contigo por iteraciones
3. Rendimiento: rejilla espacial, fondo pre-dibujado y nivel de detalle cerca/lejos de la cámara
4. Inteligencia del bot y navegación — primera raza: **Humanos**
5. Facciones, odio y relación con la fauna
6. Razas restantes: **Semihumanos**, **Elfos**, **Enanos** y **Guardián**
7. Cierre: balance con el simulador y documentación

Anexos: A) resumen de razas · B) presupuesto de rendimiento · C) preguntas abiertas · D) riesgos · E) características obligatorias del mundo

---

## Reglas comunes a todas las fases

1. **Nada cambia para el jugador** salvo lo que la fase añade a propósito. Toda la batería de pruebas existente debe seguir pasando al final de cada fase.
2. **Interruptor general:** una constante `NPC_ACTIVOS` (y un número máximo por raza) permite apagar los NPC sin tocar más código. Si algo va mal en una partida, se apaga y el juego queda como hoy.
3. **Medir antes y después:** cada fase compara su tiempo por fotograma con la línea base (ver Fase 0 y Anexo B). Si se pasa del presupuesto, la fase no se da por terminada.
4. **Semillas fijas en las pruebas:** los escenarios de prueba usan `random.seed(...)` para que los resultados sean repetibles.
5. **Commits pequeños:** al menos un commit por fase (y por paso grande dentro de la fase), con el formato de `reglas.md`.
6. **Documentación:** al cerrar cada fase se actualizan `CLAUDE.md`, la especificación (regla 3) y, si cambian valores, las tablas.

---

## Fase 0 — Preparación (sin cambios en el juego)

**Objetivo:** tener una red de seguridad antes de tocar el combate.

### Qué se hace
1. **Llevar las pruebas al proyecto.** Hoy las pruebas viven en la carpeta temporal de la sesión de Claude y se pueden perder. Se crea `pruebas/` en el proyecto con:
   - `pruebas/unitarias/`: las pruebas sin ventana ya escritas (Espectro, Disparo Venenoso, Corrosión, Palabras Malditas, Afortunado, vendedores y casa) más las de fases anteriores que se puedan recuperar.
   - `pruebas/humo/`: las pruebas del bucle real sin ventana (`humo_*`), que arrancan `mundo.iniciar_mundo` con eventos simulados.
   - `pruebas/ejecutar_todo.py`: lanza todo y muestra un resumen `N/N OK`. Se ejecuta con `SDL_VIDEODRIVER=dummy python -B pruebas/ejecutar_todo.py`.
2. **Medidor de rendimiento** `pruebas/rendimiento.py`: arranca el mundo sin ventana con semilla fija y recorre escenarios durante 30 s cada uno, midiendo el tiempo de cada fotograma:
   - **Centro:** casa del spawn, sin combate.
   - **Bosque:** junto a una manada de lobos, con combate (habilidades lanzándose).
   - **Lago:** orilla de un lago con cocodrilo.
   - **Caos:** muchas habilidades a la vez (Palabras Malditas, Estrella Ígnea, invocaciones).
   Para cada escenario guarda **media, percentil 95 y máximo** en `pruebas/rendimiento_base.json`.
3. **Línea base:** se ejecuta el medidor sobre el código actual y se apunta en este documento (tabla del Anexo B).
4. **Interruptor `NPC_ACTIVOS = False`** (todavía sin efecto).
5. **Semilla fija del mundo:** `SEMILLA_MUNDO` en `mundo.py`; el generador actual usa siempre la misma semilla, así el mapa sale idéntico en cada partida y las pruebas y mediciones son comparables. Es el paso intermedio hasta el mundo guardado de la Fase 2.

### Pruebas de Claude
- `ejecutar_todo.py` pasa entero sobre el código actual.
- El medidor da resultados estables: dos ejecuciones seguidas difieren menos de un 10 %.
- Con la semilla fija, dos arranques dan exactamente el mismo mapa (mismas rocas, lagos, árboles, arbustos y cuevas).

### Tu comprobación
- [ ] Ejecutar `python pruebas/ejecutar_todo.py` en tu equipo y ver `TODO OK`.
- [ ] Ejecutar `python pruebas/rendimiento.py` y anotar tus números (tu equipo puede ser más rápido o más lento que el de las pruebas).
- [ ] Empezar dos partidas: el mapa es el mismo en las dos.

**Terminada cuando:** las pruebas están en el proyecto, pasan en tu equipo y hay línea base.

---

## Fase 1 — Combate general ("combatiente")

**Objetivo:** que cualquier personaje (no solo el jugador) pueda moverse por el terreno, golpear, disparar, usar habilidades, recibir efectos y ser detectado, **sin cambiar en nada cómo juega el jugador**. Es la fase con más riesgo, por eso no añade NPC todavía.

### Qué hay que cambiar (y por qué)
Hoy `mundo.py` hace muchas cosas "solo para el jugador":

| Hoy (solo jugador) | Después (cualquier combatiente) |
|---|---|
| Golpe del arma: un bucle contra `enemigos` | `resolver_golpes_arma(combatiente, enemigos_de(combatiente))` |
| Proyectiles (`jugador.proyectiles`) contra `enemigos` | Proyectiles de cada combatiente contra *sus* enemigos |
| Ondas, cuchillas, explosiones, telarañas, auras: se recorre `jugador.habilidades` | Se recorren las habilidades de cada combatiente |
| `en_agua`, `en_agua_profunda`, daño del lago: solo el jugador | Para todo combatiente (necesario para el cocodrilo semihumano) |
| `vegetacion.actualizar(dt, jugador)`: oculto en arbusto, hierba venenosa, frutales | Para todo combatiente (necesario para los elfos) |
| La fauna solo mira si `jugador.detectable` | La fauna mira a todos los combatientes detectables cercanos |
| `Personaje.combustible`, sombras de anillo, efectos de Golpe de Suerte | Ya van por personaje; se revisa que no supongan "el jugador" |

### Cómo se hace
1. **Contexto del mundo:** un objeto `Contexto` con lo que hoy son variables locales de `iniciar_mundo` (rocas, vegetación, charcos, fauna, casa, maniquí, tumba, vendedores, lista de combatientes). Así las funciones nuevas no dependen de variables sueltas.
2. **Bucle por combatiente:** se extrae de `iniciar_mundo` una función `actualizar_combatiente(c, ctx, dt)` con exactamente lo que hoy se hace con el jugador (terreno, efectos, habilidades, arma, proyectiles, movimiento, empuje). El jugador pasa por esa misma función. **Primer paso: extraer sin cambiar nada** y comprobar que las pruebas siguen igual; **segundo paso:** permitir varios combatientes.
3. **Enemigos de cada uno:** `enemigos_de(c)` devuelve la lista de objetivos de ese combatiente. Para el jugador es exactamente la lista de hoy (maniquí, fauna cercana, vendedores, tumba).
4. **Controles separados de la acción ("intenciones"):** el teclado y el ratón ya no llaman directamente a las habilidades; producen intenciones (`mover_a`, `atacar`, `usar_habilidad(i)`, `mantener/soltar(i)`, `apuntar(objetivo)`, `ordenar_sombras(objetivo)`, `elegir_palabra(clave)`). El jugador las genera con teclado y ratón; un bot las generará con su inteligencia (Fase 4). Esto resuelve las habilidades manejadas con el ratón:
   - Invocaciones: `ordenar(punto/enemigo)` ya existe; el bot lo llamará directamente.
   - Palabras Malditas: el bot fija `palabra_pendiente` sin la ruleta.
   - Autoapuntado y cargas (Arco, Carga de Fuego, Regeneración): `iniciar_carga` / `soltar_carga` ya existen.
5. **Dibujo:** cada combatiente usa `Personaje.dibujar`; solo el jugador dibuja paneles, inventario, brújula y textos de XP.

### Pruebas de Claude
- **Regresión:** toda la batería de la Fase 0 pasa igual.
- **Equivalencia:** escenario con semilla fija (jugador contra maniquí y contra una manada, con cada arma y cada habilidad): mismos daños, mismas muertes y mismas posiciones antes y después de la extracción (se graba una "huella" del escenario y se compara).
- **Dos combatientes:** un segundo `Personaje` movido por script golpea al jugador con cada arma; lanza cada habilidad de daño contra el jugador; el jugador recibe daño, empuje y efectos (veneno, quemadura, corrosión, inmovilización…) igual que de un enemigo.
- **Terreno para todos:** un combatiente no jugador en el agua va más lento; en la zona profunda pierde vida; dentro de un arbusto queda oculto y la fauna no lo detecta.
- **Fauna:** un lobo persigue al combatiente no jugador más cercano y detectable.

### Tu comprobación
- [ ] Jugar 15 minutos normal (con varias armas y habilidades): todo se siente igual que antes.
- [ ] Probar en especial: Arco (cargar y disparar), Carga de Fuego, invocaciones con clic derecho, Palabras Malditas con la ruleta, Autoapuntado, inventario, Gacha, tienda del vendedor, morir y la tumba.
- [ ] Mirar que el juego no va más lento (no hay NPC todavía).

### Rendimiento
Sin NPC: **±0.5 ms** respecto a la línea base en todos los escenarios.

**Terminada cuando:** el juego es idéntico para el jugador y un combatiente de prueba puede pelear contra él.

---

## Fase 2 — Mundo fijo: mapa guardado y diseñado contigo

**Objetivo:** que el mundo sea **siempre el mismo**, guardado en un archivo, y que lo diseñemos juntos: tú das las indicaciones, yo las aplico, lo pruebas y repetimos hasta que te guste. Además deja preparadas dos mejoras de rendimiento que necesitan un mapa fijo: la rejilla de rutas guardada (Fase 4) y el fondo pre-dibujado (Fase 3).

### Qué se hace
0. **Mapa cuadrado de 17 700 × 17 700 px** (decisión del 26/11): la misma superficie que el círculo actual de radio 10 000, así la cantidad de fauna, los tiempos de viaje y las tablas del simulador no cambian. Un cuadrado no mejora los fps por sí mismo, pero encaja exacto en las rejillas, en la rejilla de rutas y en el fondo pre-dibujado por trozos (el círculo desperdicia ~21 % en las esquinas) y facilita describir el diseño (cuadrantes, bordes, esquinas). Hay que sustituir el límite circular (unas 55 referencias en `mundo.py`, `personaje.py`, `fauna.py`, `vegetacion.py`, `vendedores.py` y `habilidades.py`: movimiento, empuje, proyectiles, fauna, generación, vendedores, `sacar_a_hueco_libre`, dibujo del borde y la escala por área) por un límite cuadrado en un único sitio (`limite_mundo`), con la casa del spawn en el centro del cuadrado.
1. **Formato del mapa:** `mapas/mundo.json` con todo lo que hoy se genera al azar:
   - Lagos (forma de nube, radio, zona profunda), rocas (posición, tamaño, si es cueva de oso), árboles (tipo y tamaño), arbustos (tipo: escondite, venenoso o frutal), praderas, bosques, madrigueras, cofres.
   - **Zonas con nombre** (polígonos o círculos): bosques élficos, norte del guardián, cuevas de enanos, zona de vendedores, zonas de caza por dificultad…
   - **Puntos de aparición** por raza y para la fauna (manadas, osos, cocodrilos, venados…).
   - Versión del formato, para poder cambiarlo sin romper mapas viejos.
2. **Cargador:** `mundo.py` crea el mundo leyendo el archivo en vez de generarlo. Si el archivo falta o está mal, avisa y usa el generador con la semilla fija (el juego nunca se queda sin mundo).
3. **Generador asistido** (`herramientas_mapa/generar_mapa.py`): parte del generador actual y aplica tus indicaciones como **reglas** ("bosque grande al noreste", "lago en el centro-oeste con isla", "cordillera de rocas al sur con dos pasos"…). Así no hay que colocar a mano 800 rocas y 1000 árboles: describes, se genera, y se retoca lo que haga falta. Lo que fijes a mano se respeta en las siguientes generaciones.
4. **Validador** (`herramientas_mapa/validar_mapa.py`): comprueba que el mapa cumple las **características obligatorias del Anexo E** (conectividad, pasillos, zonas de cada raza, densidades para el rendimiento…). Un mapa que no pasa el validador no se usa.
5. **Vista previa:** `herramientas_mapa/vista_previa.py` dibuja el mapa entero en una imagen (PNG) con las zonas, cuevas, lagos, puntos de aparición y la rejilla de rutas encima. Te paso la imagen en cada iteración para que no tengas que recorrer el mapa jugando para ver el diseño.
6. **Rejilla de rutas guardada:** `mapas/mundo_rutas.bin` con las celdas transitables (la usará la navegación de la Fase 4). Se recalcula solo cuando cambia el mapa.
7. **Personaje de inspección `ShadowGOD`** (personaje de pruebas, como `shadow498`): para revisar el mundo sin recorrerlo andando. Como mínimo, **ver el mapa desde más distancia** (alejar la cámara con zoom) y desplazarse rápido por él. Las características exactas las describirás tú más adelante (ver Anexo C); se implementa al principio de esta fase porque es la herramienta con la que revisarás cada versión del diseño. Solo existe con el nombre clave de pruebas y no afecta a las partidas normales.

### Cómo trabajamos el diseño (bucle de iteración)
1. Me das indicaciones (pueden ser generales o muy concretas, incluso un dibujo a mano alzada).
2. Aplico los cambios, paso el validador y te envío la **vista previa** con lo que cambió.
3. Lo pruebas jugando si hace falta (zona concreta, recorrido, sensación de tamaño).
4. Repetimos hasta que te guste. Cada versión aprobada se guarda con su commit (`mapas/mundo.json` versionado), así siempre se puede volver a una anterior.

### Pruebas de Claude
- **Equivalencia:** el mundo cargado del archivo es idéntico al que se guardó (posiciones, tamaños y tipos de todo).
- **Arranque:** cargar el mapa tarda menos que generarlo hoy (0.32 s medido el 26/11).
- **Validador:** pasa con el mapa aprobado; falla, con un mensaje claro, en mapas de prueba rotos (una zona aislada, un pasillo demasiado estrecho, falta de cuevas…).
- **Toda la batería** (Fases 0 y 1) pasa con el mapa fijo.
- **Límite cuadrado:** nada (jugador, NPC, fauna, vendedores, proyectiles, empuje, `sacar_a_hueco_libre`) sale del cuadrado ni queda pegado al borde; la generación no coloca nada fuera; las esquinas son accesibles.
- **ShadowGOD:** el zoom y el desplazamiento rápido no cambian nada del mundo (es solo vista) y el rendimiento con la vista alejada se mide aparte (dibujar más superficie cuesta más; si hace falta, el fondo pre-dibujado o un mapa simplificado se usan a esa distancia).

### Tu comprobación
- [ ] Con **ShadowGOD**, alejar la vista y recorrer el mapa rápido para revisar cada versión.
- [ ] Revisar cada vista previa y decir qué cambiar.
- [ ] Recorrer el mapa aprobado: se puede llegar a todas partes y la distribución te gusta.
- [ ] Empezar dos partidas: el mundo es el mismo.

**Terminada cuando:** apruebas un diseño, pasa el validador y el juego lo carga siempre.

---

## Fase 3 — Rendimiento: rejilla espacial y nivel de detalle

**Objetivo:** que 19 personajes más los vendedores y la fauna quepan en el presupuesto de 16.7 ms por fotograma (60 fps).

Medición previa (26/11): mover 19 personajes con sus choques cuesta **~10 ms por fotograma** (2.3 ms en calcular obstáculos y 7.4 ms en moverlos), y hoy el juego ya usa 9–14 ms. Sin esta fase el juego bajaría a ~35–40 fps.

### Qué se hace
1. **Obstáculos estáticos en rejilla:** rocas, troncos, arbustos sólidos y paredes de la casa en una `RejillaEspacial` (ya existe para la vegetación). `obstaculos_para` y `mover` preguntan solo por las celdas cercanas en vez de recorrer las ~800 rocas y ~1000 árboles cada vez.
2. **Rejilla dinámica de personajes y fauna:** se rehace una vez por fotograma; sirve para "¿quién está cerca de mí?" (objetivos, solapamientos, auras, ondas) sin comparar todos con todos.
3. **Nivel de detalle (cerca / lejos):**
   - **Zona activa:** la vista de la cámara más un margen (≈ 1.5 pantallas). Dentro, simulación completa: se mueven, pelean y se ven.
   - **Fuera:** simulación **resumida** cada pocos segundos:
     - Se mueven por el mapa siguiendo su objetivo a grandes rasgos (sin choques finos).
     - Ganan XP por minuto según su nivel y su raza (tablas sacadas del simulador, que ya mide cuánta XP por minuto se gana en cada nivel).
     - Pueden morir con una probabilidad por minuto según su nivel y el peligro de la zona.
     - Gastan los puntos al subir de nivel como lo harían en la zona activa.
   - **Al entrar en la zona activa** el NPC "se materializa" en su posición resumida; si cae dentro de algo, sale al hueco libre más cercano (`sacar_a_hueco_libre`, ya existe para Espectro).
   - **Peleas lejos:** dos NPC hostiles en la zona resumida resuelven su pelea con una tirada según su poder (nivel, vida, daño estimado); el ganador se lleva la XP.
4. **Fondo pre-dibujado por trozos:** con el mapa fijo, el suelo, el agua, la flora acuática, las rocas, los troncos, la casa y el pasto se dibujan una vez en "trozos" (p. ej. 1024 × 1024 px) y en cada fotograma solo se pegan los trozos visibles. Lo que se mueve o cambia (personajes, fauna, copas que se desvanecen, rocas destruidas) se sigue dibujando encima; cuando algo del fondo cambia (una roca destruida, un lago evaporado) solo se redibuja su trozo. **Esta es la mejora real de fps del mapa fijo.**
5. **Límite de seguridad:** como mucho `MAX_NPC_ACTIVOS` (p. ej. 8) con simulación completa a la vez; si hay más en pantalla, los más lejanos pasan a una versión intermedia (se mueven y se ven, pero piensan menos a menudo).
6. **IA escalonada:** cada bot "piensa" (elige objetivo, ruta, habilidad) cada 0.2–0.5 s, repartidos entre fotogramas, no todos en el mismo.

### Pruebas de Claude
- **Rejilla:** `obstaculos_para` y `mover` dan exactamente los mismos resultados con la rejilla que sin ella (miles de posiciones al azar).
- **Fondo pre-dibujado:** la imagen del mundo con trozos es idéntica (píxel a píxel) a la dibujada como hoy en varias posiciones de cámara; destruir una roca o evaporar un lago actualiza su trozo. Sin NPC, el escenario **Centro** y el **Bosque** deben bajar de tiempo respecto a la línea base.
- **Rendimiento con NPC de prueba quietos o paseando** (todavía sin inteligencia):
  - 19 NPC lejos de la cámara: **≤ +1 ms**.
  - 8 NPC en pantalla paseando: **≤ +3 ms**.
- **Transición cerca/lejos:** un NPC que entra y sale de la zona activa 100 veces nunca queda dentro de una roca ni pierde su nivel, vida o equipo.
- **Simulación resumida:** en 1 h de juego simulada, la XP que gana un NPC lejos se parece (±20 %) a la que gana cerca.

### Tu comprobación
- [ ] Mirar el contador de rendimiento (se añade un indicador de ms por fotograma con una tecla de prueba) en el centro, en un bosque y en una pelea grande.
- [ ] Recorrer el mapa con [C]: los NPC (de prueba) aparecen en su sitio al acercarte, nunca dentro de rocas.

**Terminada cuando:** el presupuesto del Anexo B se cumple con NPC de prueba.

---

## Fase 4 — Inteligencia del bot y navegación (primera raza: Humanos)

**Objetivo:** bots que se mueven por el mapa sin atascarse, cazan, huyen, se curan, suben de nivel y usan sus armas y habilidades. Se estrena con los **Humanos** porque no odian a nadie (solo se defienden): es la raza más sencilla para probar.

### Navegación
- **Rejilla de paso** gruesa (celdas de ~40 px), **cargada del archivo del mapa** (Fase 2) y actualizada si se destruye un obstáculo, marcando rocas, troncos, paredes de la casa, arbustos sólidos y la zona profunda de los lagos (el agua normal se puede cruzar, pero cuesta más).
- **Ruta con A\*** sobre esa rejilla, calculada solo cuando hace falta (nuevo destino, o el bot no avanza) y guardada; el bot sigue los puntos de la ruta.
- **Antiatascos:** si en 1 s no avanza, recalcula la ruta; si sigue igual, se sale al hueco libre más cercano.
- **Coste controlado:** como mucho unas pocas rutas nuevas por fotograma (cola de peticiones).

### "Cerebro" (máquina de estados)
| Estado | Qué hace | Cuándo cambia |
|---|---|---|
| Explorar | Camina hacia zonas con presas de su nivel | Ve una presa que puede ganar → Cazar |
| Cazar | Se acerca, usa habilidades y el arma | Gana → Explorar · vida < 30 % → Huir |
| Huir | Se aleja; usa Destello, Paso 0, Palabras (Huye/Sal volado)… | A salvo → Curarse |
| Curarse | Busca frutales / espera a regenerar / Regeneración Inversa | Vida alta → Explorar |
| Defenderse | Si alguien le golpea, contraataca o huye según su poder | Agresor muerto o lejos → anterior |

- **Elegir presa:** la misma idea que el simulador (XP esperada / tiempo, evitando lo que le ha matado antes), con lo que ve a su alrededor.
- **Habilidades:** reglas por habilidad (cuándo lanzar Disparo Veloz, cuándo cargar el Arco o la Carga de Fuego, cuándo invocar y a quién ordenar, qué palabra pronunciar, cuándo encender Reforzamiento…). Se reutiliza la lógica del simulador.
- **Subir de nivel:** reparte los puntos con una de las políticas del simulador (tanque, daño, equilibrado, habilidades).

### Humanos
- **6** en el mapa, estadísticas iniciales normales (vida 30 · fuerza 2 · velocidad 1 · cadencia +0 · energía 100 · escudos 0), cualquier arma y cualquier habilidad (3 al azar).
- **Sin odio:** no empiezan peleas con otros personajes; si les golpean se defienden.
- Suben de nivel con la XP real de lo que cazan.
- **Si muere:** reaparece en un punto al azar desde el nivel 1.

### Pruebas de Claude
- **Navegación:** desde 200 puntos al azar a 200 destinos al azar, el bot llega en el 98 % de los casos sin quedarse atascado más de 3 s; nunca atraviesa rocas ni paredes.
- **Cada arma y cada habilidad usada por un bot** en un escenario fijo: sin errores, hace daño y respeta costes y recargas (incluidas las potenciadas).
- **Ciclo de vida:** un humano caza, sube de nivel, muere y reaparece al nivel 1 en otro punto.
- **Defensa:** un humano al que golpeas se defiende; si no le haces nada, te ignora.
- **Rendimiento:** 6 humanos activos en pantalla peleando: **dentro del presupuesto** (Anexo B).
- **Prueba de resistencia:** 30 min de juego acelerado sin ventana con los 6 humanos: sin errores ni fugas de memoria.

### Tu comprobación
- [ ] Seguir a un humano un rato con [C]: caza, huye cuando va mal y no se queda atascado en rocas ni en lagos.
- [ ] Golpear a un humano: se defiende. No golpearle: te ignora.
- [ ] Ver a un humano usar habilidades vistosas (invocaciones, Estrella Ígnea, Palabras Malditas) sin cosas raras.
- [ ] Partida larga (30–60 min): el juego no se vuelve más lento con el tiempo.

**Terminada cuando:** los humanos viven en el mapa de forma creíble y el rendimiento aguanta.

---

## Fase 5 — Facciones, odio y relación con la fauna

**Objetivo:** que las razas se odien con las probabilidades que diste y que cada una tenga su relación especial con la fauna.

### Odio
- **Matriz de odio** por raza (porcentaje hacia cada otra raza), en un único sitio del código para poder ajustarla.
- **Cómo funciona:** cuando dos personajes que se pueden odiar están a la vista (≈ 400 px) y ninguno está ya peleando, cada cierto tiempo (p. ej. cada 5 s) se tira el porcentaje de odio; si sale, empiezan a pelear "sin razón".
- **Defensa:** cualquier personaje golpeado considera enemigo a su agresor durante un tiempo (se reutiliza la idea de `marcar_agresor` de los anillos de sombra).
- **El jugador** cuenta como humano para el odio de las demás razas.

### Relación con la fauna
| Raza | Regla |
|---|---|
| Elfos | Solo atacan a animales hostiles (no a pasivos ni neutrales). |
| Enanos | No atacan osos y los osos no los atacan. |
| Guardián | Ningún animal lo ataca. |
| Resto | Como el jugador. |

Se implementa con dos filtros: "¿a quién puede atacar este personaje?" y "¿a quién puede atacar este animal?".

### Pruebas de Claude
- **Probabilidades:** con 10 000 encuentros simulados, la frecuencia de peleas espontáneas se ajusta al porcentaje de la matriz (±2 %).
- **Casos fijos:** un oso pasa junto a un enano sin atacarlo; un elfo no ataca a un venado pero sí a un lobo; ningún animal ataca al guardián.
- **Defensa y memoria:** golpeado, se defiende; pasado el tiempo de memoria, deja de perseguir.

### Tu comprobación
- [ ] Observar encuentros entre razas: se pelean más las que más se odian.
- [ ] Ver un enano junto a un oso sin pelear.

**Terminada cuando:** las relaciones se comportan según la matriz.

---

## Fase 6 — Razas restantes

Se añaden **una a una**, cada una con su commit, sus pruebas y su comprobación manual. Todas usan el combate, el rendimiento, la inteligencia y el odio de las fases anteriores; solo cambian estadísticas, equipo, aparición y reglas propias.

### 5.1 Semihumanos (4, uno de cada tipo)
Comunes: habilidades **al azar y fijas** (no las cambian), **nivel máximo 20**, y al llegar al 20 **una de sus habilidades al azar pasa a potenciada**.

| Tipo | Armas | Vida | Fuerza | Velocidad | Cadencia | Energía | Escudos | Odio (humano / elfo / enano) | Regla propia |
|---|---|---|---|---|---|---|---|---|---|
| Lobo | Cualquiera salvo Arco y Escudo | 50 | 4 | 2 | +0 | 50 | 10 | 40 % / 0 % / 5 % | — |
| Conejo | Espada Ligera o Dagas | 10 | 2 | 4 | +0 | 50 | 0 | 5 % / 0 % / 5 % | — |
| Oso | Espada Ligera, Espada Larga o Escudo | 80 | 4 | −1 (ver Anexo C) | +4 | 30 | 20 | 20 % / 0 % / 5 % | — |
| Cocodrilo | Espada Larga o Dagas | 50 | 2 | 1 | +0 | 50 | 40 | 20 % / 0 % / 5 % | Velocidad ×3 en el agua |

### 5.2 Elfos (4)
- Solo **Arco**; habilidades al azar y fijas; vida 80 · fuerza 5 · velocidad 1 · cadencia +0 · energía 200 · escudos 0.
- **Nivel máximo 30**; una potenciada al azar en el 20 y ninguna más.
- Odio: humano 30 % · enano 20 % · semihumano 0 %.
- Solo atacan animales hostiles.
- **El 80 % aparece en bosques** y se esconde entre arbustos (usa el sistema de "oculto" de la Fase 1).

### 5.3 Enanos (4)
- **Espada Larga o Mandoble**; habilidades al azar y fijas; vida 120 · fuerza 4 · velocidad 1 · cadencia +0 · energía 50 · escudos 30.
- **Nivel máximo 30**.
- Odio: humano 10 % · elfo 30 % · semihumano 10 %.
- No atacan osos y los osos no los atacan.
- **Aparecen en cuevas de oso** (no se quedan en ellas).

### 5.4 Guardián (semidiós, 1)
- **Mandoble al máximo**, sin habilidades; vida 999 · fuerza 9 · velocidad 1 · cadencia +4 · energía 0 · escudos 999.
- **No sube de nivel.** Sin odio: solo se defiende si le golpean.
- Ningún animal lo ataca. Suele estar en el **norte del mapa**.

### Regla común de muerte
Si muere cualquier NPC, **reaparece en un punto al azar** (según su raza: bosque, cueva, norte…) con sus estadísticas iniciales.

### Pruebas de Claude (por raza)
- Aparece con estadísticas, armas permitidas y habilidades correctas (1000 apariciones al azar).
- Respeta su nivel máximo; en el 20 desbloquea exactamente una potenciada (cuando corresponde).
- Su regla propia funciona (cocodrilo ×3 en agua, elfos ocultos en arbustos, enanos y osos, guardián intocable por la fauna).
- Reaparece bien al morir.
- Rendimiento con todas las razas a la vez dentro del presupuesto.

### Tu comprobación (por raza)
- [ ] Encontrar uno con [C] y ver que se comporta según su raza.
- [ ] Pelear con él: la dificultad es razonable para su nivel.

---

## Fase 7 — Cierre: balance y documentación

- **Simulador:** se amplía para incluir a los NPC (como peligro y como competencia por la XP) y se mide de nuevo cuánto se tarda en llegar al 20 y al 30.
- **Ajustes** de cantidades, odio y estadísticas según lo medido y lo que veas jugando.
- **Documentación:** especificación, `CLAUDE.md`, `Fauna.md` (relaciones con las razas), un `Razas.md` nuevo con las fichas de cada raza y una lista de comprobación final.

---

## Anexo A — Resumen de razas

| Raza | Cantidad | Nivel máx. | Armas | Habilidades | Potenciada | Aparición |
|---|---|---|---|---|---|---|
| Humanos | 6 | Normal | Cualquiera | Cualquiera (al azar) | Como el jugador (ver Anexo C) | Al azar |
| Semihumano lobo | 1 | 20 | No Arco ni Escudo | Al azar, fijas | 1 al azar en el 20 | Al azar |
| Semihumano conejo | 1 | 20 | Ligera o Dagas | Al azar, fijas | 1 al azar en el 20 | Al azar |
| Semihumano oso | 1 | 20 | Ligera, Larga o Escudo | Al azar, fijas | 1 al azar en el 20 | Al azar |
| Semihumano cocodrilo | 1 | 20 | Larga o Dagas | Al azar, fijas | 1 al azar en el 20 | Al azar (¿cerca de lagos?) |
| Elfos | 4 | 30 | Arco | Al azar, fijas | 1 al azar en el 20 | 80 % en bosques |
| Enanos | 4 | 30 | Larga o Mandoble | Al azar, fijas | (ver Anexo C) | Cuevas de oso |
| Guardián | 1 | No sube | Mandoble al máximo | Ninguna | — | Norte |

Total: **19 NPC** (+ 3 vendedores + la fauna).

## Anexo B — Presupuesto de rendimiento

Objetivo: **60 fps** (16.7 ms por fotograma) con margen. Línea base a rellenar en la Fase 0 (referencia actual: 9–14 ms por fotograma).

| Escenario | Línea base (Fase 0) | Máximo permitido al final |
|---|---|---|
| Centro, sin NPC cerca | (medir) | base + 1 ms |
| Bosque con manada, sin NPC cerca | (medir) | base + 1 ms |
| 4 NPC en pantalla peleando | — | p95 ≤ 16 ms |
| 8 NPC en pantalla peleando (caso extremo) | — | p95 ≤ 16.7 ms |
| 19 NPC lejos (simulación resumida) | — | base + 1 ms |

Si una fase se pasa del presupuesto: primero se optimiza (rejillas, pensar menos a menudo, menos detalle lejos), después se baja `MAX_NPC_ACTIVOS`.

## Anexo C — Preguntas abiertas (se resuelven al llegar a cada fase)

1. **Semihumano oso, velocidad −1:** con velocidad base 1 quedaría en 0 (no se movería). ¿Es "−1 respecto al normal" (es decir, 0.5?), o un modificador del −10 %?
2. **Cadencia +4** (oso semihumano, guardián): es mucho (el máximo del jugador al nivel 30 todo en cadencia es +12). ¿Se queda así?
3. **Humanos y enanos, potenciadas:** ¿los humanos pueden conseguir potenciadas (como el jugador, con el Gacha) o ninguna? ¿Y los enanos, que suben al 30?
4. **Nivel máximo de los humanos:** ¿40 como el jugador?
5. **Economía de los NPC:** ¿usan monedas, el Gacha o los vendedores? ¿Recogen cofres, frutales y orbes?
6. **Recompensa por matar a un NPC:** ¿cuánta XP y monedas te dan (según su nivel)?
7. **Tiempo de reaparición** de los NPC (los vendedores tardan 5 min).
8. **¿Los NPC atacan a tus invocaciones y anillos de sombra?** ¿Y al maniquí, a los vendedores y a tu tumba?
9. **Guardián "se defiende":** ¿cuánto tiempo te persigue después de un golpe? Con 999 de vida y escudos, ¿se puede matar (y qué da)?
10. **Elfos ocultos:** dentro de un arbusto, ¿atacan desde ahí (emboscada) o solo se esconden para huir?
11. **Semihumano cocodrilo:** ¿aparece cerca de lagos?
12. **Odio "hacia semihumanos"** de elfos y enanos: ¿vale igual para los 4 tipos?
13. **ShadowGOD:** características exactas (zoom máximo, desplazamiento rápido o teletransporte, ver zonas y puntos de aparición, ser invisible o invulnerable, mover la cámara sin el personaje…). Pendiente de que las describas (Fase 2).

## Anexo D — Riesgos y cómo se controlan

| Riesgo | Control |
|---|---|
| La Fase 1 cambia sin querer cómo juega el jugador | Prueba de equivalencia con "huella" del escenario + tu partida de 15 min |
| Bajada de fps al añadir NPC | Fase 3 antes de la inteligencia; medidor en cada fase; `MAX_NPC_ACTIVOS` |
| Bots atascados en rocas o lagos | A\* + antiatascos + prueba de 200 rutas |
| Habilidades que asumen ratón o teclado | Intenciones (Fase 1); prueba de cada habilidad usada por un bot (Fase 4) |
| Peleas entre NPC lejos de la cámara poco creíbles | Resolución resumida calibrada con el simulador (Fase 3) y revisada en la Fase 7 |
| Errores que solo salen tras mucho tiempo | Pruebas de resistencia de 30 min acelerados sin ventana |
| Se pierden las pruebas | Fase 0: las pruebas viven en `pruebas/` dentro del proyecto |
| Algo falla en una partida tuya | Interruptor `NPC_ACTIVOS = False` |
| El diseño del mapa deja zonas inaccesibles o demasiado densas | Validador (Anexo E) antes de aceptar cada versión; vista previa en cada iteración |
| Se rompe o se pierde el archivo del mapa | `mapas/mundo.json` versionado en git; si falta, el juego genera el mundo con la semilla fija |

## Anexo E — Características obligatorias del mundo

El diseño lo decides tú; estas condiciones son las que el **validador** exige para que el resto del plan funcione (personajes, fauna, rendimiento). Si alguna choca con lo que quieres, se habla y se ajusta.

### Forma y tamaño
- Mapa **cuadrado de 17 700 × 17 700 px** (misma superficie que el círculo actual de radio 10 000). Cambiar el tamaño afecta a la cantidad de fauna, al tiempo de viaje de los vendedores y a las tablas del simulador: se puede, pero se recalibra.
- **Casa del spawn en el centro del cuadrado** con su jardín de 350 px libre de obstáculos y de fauna.

### Recorrido (para que nada ni nadie se quede atascado)
- **Conectividad:** desde la puerta de la casa se puede llegar andando a **todo** punto de tierra del mapa (sin zonas encerradas por rocas o lagos).
- **Pasillos de al menos 80 px** de ancho entre obstáculos sólidos (rocas, troncos, paredes, arbustos en los que no se cabe), para que pase un personaje (40 px) y otro en sentido contrario.
- **Lagos:** la zona profunda nunca corta el único camino entre dos partes del mapa; siempre hay orilla transitable alrededor.
- Sin obstáculos a menos de 300 px del borde del mapa (los vendedores y bots se mantienen dentro).

### Zonas por raza y por sistema
| Para | Requisito mínimo |
|---|---|
| Guardián | Una zona "norte" marcada (por encima del centro) con espacio abierto de al menos 600 px de radio. |
| Elfos | Al menos **4 bosques** densos con arbustos de escondite (el 80 % de los elfos aparece en bosques). |
| Enanos y osos | Al menos **12 cuevas de oso** (rocas gigantes), separadas entre sí más de 1500 px; los enanos aparecen en ellas. |
| Semihumano cocodrilo y cocodrilos | Al menos **6 lagos con zona profunda** (radio > 300). |
| Fauna pasiva | Praderas para las madrigueras (al menos 8) y espacio para 70 venados y 40 jabalíes. |
| Manadas de lobos | Al menos 8 bosques donde situar manadas, a más de 1500 px del centro. |
| Vendedores | Tierra firme a más de 1500 px del centro (pasean por ahí). |
| Humanos y semihumanos | Puntos de aparición repartidos por todo el mapa, a más de 1000 px del centro. |
| Cofres | Entre 20 y 40, repartidos. |

### Densidad (para el rendimiento)
- Como mucho, en cualquier zona del tamaño de una pantalla: **~60 rocas, ~150 árboles y ~80 arbustos** (los bosques más densos de hoy están por debajo). Por encima, el dibujo y los choques se encarecen.
- Totales orientativos parecidos a los de hoy: 600 – 1200 rocas, ~1000 árboles, 24 – 40 lagos. Si el diseño necesita más, se mide antes con el medidor de la Fase 0.

### Dificultad (recomendación, no obligatoria)
- Anillos de peligro: cerca del centro animales fáciles (conejos, venados), en la mitad del radio lobos y jabalíes, y hacia el borde osos y cocodrilos, para que el jugador y los bots suban de nivel alejándose poco a poco.

### Qué puedes pedir libremente
Situación y forma de bosques, lagos, praderas y cordilleras de rocas; ríos (como cadenas de lagos); islas; zonas con nombre; caminos; dónde está cada raza; la cantidad de cada cosa (dentro de la densidad de arriba); y cualquier elemento decorativo.
