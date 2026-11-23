# LEVEL_UP — Fauna del mundo

> Documento de información (no técnico) sobre los animales del mundo.
> Pensado como contexto de referencia para la IA y para el equipo.
> Actualizado: 23 de noviembre de 2026.

---

## Resumen

La fauna se divide en cuatro grupos según su comportamiento. Toda la fauna se
genera y se actualiza **solo cerca de la cámara** (lo que queda fuera de pantalla
no consume rendimiento), aunque las poblaciones "globales" (venados, jabalíes,
zorros) existen repartidas por todo el mundo.

**Reglas comunes de la fauna con vida** (pasivas y neutrales: conejo, venado,
jabalí, zorro):

- Tienen **hitbox sólido**: el jugador y las demás criaturas no las atraviesan.
- Tienen **vida** con **barra** visible cuando están heridas.
- **Reciben daño de todo**: armas cuerpo a cuerpo, arco/proyectiles, todas las
  habilidades con daño (Cortar, Onda Sonora, Aura Eléctrica, quemadura, veneno,
  desangrado…) y las **mascotas** (invocaciones de sombra).
- La **telaraña** de la Sombra Araña las **inmoviliza**.
- Al **golpearlas con un arma** son **empujadas** (puntos de empuje × 6 px).
- **Sigilo:** si el jugador está **oculto en un arbusto** o en **Paso 0**
  (indetectable), **ningún animal** lo detecta — los pasivos no huyen de él, los
  neutrales no reaccionan y los hostiles no lo persiguen.

---

## Fase 1 — Fauna ambiental (sin colisión, pura vida visual)

### Mariposas y luciérnagas
- **Dónde:** revolotean sobre praderas, con más densidad cerca de las flores.
- **Aspecto:** dos alitas que aletean en colores variados (blanco, amarillo,
  naranja, azul, rosa). Alrededor del 22% salen como **luciérnagas**: un punto
  ámbar con un halo suave (vuelan de día, sin esperar a la noche).
- **Comportamiento:** te ignoran por completo. Población dinámica alrededor de la
  cámara, con un máximo de **6** visibles a la vez.

### Pájaros
- **Dónde:** posados sobre la copa de aproximadamente **1 de cada 5 árboles** de
  los bosques.
- **Aspecto:** silueta pequeña posada; en vuelo, una "V" que aletea.
- **Comportamiento:** alzan el vuelo si te acercas a **120 px** y **regresan a su
  árbol** cuando te alejas.

### Peces
- **Dónde:** dentro de los lagos medianos y grandes (radio ≥ 120), de **2 a 5**
  por lago.
- **Aspecto:** una **sombra ovalada** oscura justo bajo la superficie del agua
  (no se ve el pez, solo su sombra).
- **Comportamiento:** nadan en curvas sin salir del lago; si entras al agua cerca,
  se **dispersan** un momento.

### Ranas
- **Dónde:** en los lagos medianos y grandes, de **1 a 3** por lago. Aparecen en
  la **orilla** o, con un 50% de probabilidad, **encima de un nenúfar**.
- **Aspecto:** cuerpo verde con dos ojos; da pequeños saltos.
- **Comportamiento:** están quietas dando saltitos; si te acercas a **72 px**
  **saltan al agua y se sumergen** unos segundos, luego reaparecen.

---

## Fase 2 — Fauna pasiva (huye de ti y de tus sombras)

La fauna pasiva huye de la **amenaza más cercana**: el jugador, cualquiera de tus
**sombras** (invocaciones) y los **zorros hambrientos** visibles.

### Conejo salvaje
- **Vida:** 5 a 20.
- **Aspecto:** conejo natural (gris/café) con orejas largas y cola blanca.
- **Madrigueras:** hay **10 madrigueras** por mundo, situadas en el **bioma de
  pasto alto**. Cada madriguera alberga de **2 a 10** conejos.
- **Comportamiento:** deambulan alrededor de su madriguera en un radio amplio
  (180 a 320 px, se separan de forma progresiva). Si ven una amenaza a menos de
  **100 px**, **huyen a su madriguera** y se **esconden 60 s** antes de volver a
  salir. Si dejan de perseguirlos, retoman el deambular sin volver obligados.
- **Reproducción:** si una madriguera tiene **2 o más** conejos vivos, cada **30 s**
  nace **+1**, sin superar el máximo de la madriguera (10).
- **Madriguera vacía:** si se queda sin conejos, **desaparece** y aparece otra en
  otro pastizal (fuera de tu vista) con **2 a 10** conejos nuevos.
- **Velocidad:** paseo 45, huida 160.

### Venado / ciervo
- **Vida:** 20 a 40. Es de los **pocos que se regeneran**: **+1 de vida cada 2 s**
  después de recibir daño.
- **Aspecto:** cuerpo café con patas, cuello y cabeza; algunos con cornamenta.
  Más grande que el conejo.
- **Población:** **50** repartidos por todo el mundo (muy dispersos).
- **Comportamiento:** muy tímido; pasta tranquilo y **huye lejos** si una amenaza
  entra a menos de **160 px**.
- **Reproducción:** si hay **2 o más** venados en el mundo, cada **60 s** nace
  **+1** junto a otro venado, sin pasar de 50.
- **Velocidad:** paseo 40, huida 235.

---

## Fase 3 — Fauna neutral (te ignora, pero reacciona si la provocas)

### Jabalí
- **Vida:** 40 a 70. Resistente.
- **Aspecto:** cuerpo robusto marrón con colmillo; los **ojos se ponen rojos**
  mientras está en rabia.
- **Población:** **20** repartidos por los bosques del mundo.
- **Comportamiento:** neutral; te ignora mientras no lo golpees. Al recibir un
  golpe entra en **estado de RABIA** durante **6 s**: se mueve de forma
  **errática** y **embiste a quien lo golpeó** (jugador o sombra), haciendo **10 a
  18 de daño** y un **empuje muy alto (40 puntos)**. Si recibe otro golpe, su
  atención se **redirige** al nuevo atacante. Pasados los 6 s, **sale corriendo
  del jugador**; si le vuelven a pegar, entra en rabia otra vez.
- **Reproducción:** igual que el venado (cada 60 s si hay 2 o más, hasta 20).
- **Velocidad:** paseo 30, rabia 195, huida 175.

### Zorro
- **Vida:** 15 a 30.
- **Aspecto:** cuerpo naranja con orejas puntiagudas, hocico y cola de punta
  blanca.
- **Población:** **15** repartidos por el mapa.
- **Comportamiento base:** neutral; ronda manteniendo distancia. Si lo
  **acorralas** (a menos de 45 px) o lo **golpeas**, **muerde** a esa amenaza
  (**5 a 10 de daño**) y huye.

El zorro tiene **tres pasivas**:

1. **Cacería / robo de velocidad (siempre acierta).** Cuando fija un objetivo
   (un conejo que caza, o el jugador/sombra que lo golpeó o acorraló), le **roba
   un 30% de velocidad**: el objetivo queda **30% más lento** y el zorro **30%
   más rápido**. El robo afecta a **un solo objetivo a la vez** y es
   **permanente**: dura hasta que el **zorro muere** o hasta que **dejas de ser su
   objetivo**, es decir cuando **sales de su vista** (unos 500 px, prácticamente
   cuando deja de verse en tu pantalla). El zorro sigue robando **incluso mientras
   huye** de ti.

2. **Hambre y caza de conejos.** Al zorro le da **hambre cada 5 minutos**. Cuando
   tiene hambre, busca al **conejo más cercano** (dentro de 450 px), lo **persigue**
   (aplicando el robo de velocidad, así lo alcanza) y lo **mata al instante** al
   tocarlo, llenándose (reinicia el hambre). No muere de hambre, pero mientras la
   tiene, caza. Si el conejo **escapa** (se esconde en su madriguera), el zorro
   **suelta el robo** y se **aleja de la madriguera**.

3. **Paso 0 (invisibilidad total).** Tiene una recarga de **10 s**. Cuando la
   recarga está lista y el zorro **detecta** algo (un conejo, el jugador o una
   sombra), hace **un tiro del 30%**: si sale, se vuelve **completamente invisible
   durante 5 s** — no se dibuja y **nada puede detectarlo ni tocarlo** (ni el
   conejo huye de él, ni el jugador puede golpearlo). Si el tiro falla, reinicia la
   recarga de 10 s. Puede activarlo también mientras corre. Al activarlo **se
   desvanece en 0.4 s** (y reaparece con el mismo fundido), pero deja de poder
   tocarse desde el primer instante.
- **Reaparición:** cada **3 min** aparece un zorro nuevo en el mundo (fuera de tu
  vista) y cada **2 min** nace **+1** junto a otro si quedan 2 o más, sin pasar
  de 15.
- **Velocidad:** paseo 42, correr 150 (×1.3 mientras roba velocidad).

---

## Fase 4 — Fauna hostil (te caza)

### Lobo (en manada)
- **Manada de 4 lobos:** 1 **alfa** (vida 40, daño 15, 30% de desangrado) y 3
  normales (vida 25, daño 8, 10% de desangrado). Hay **7 manadas** por mundo,
  en los bosques.
- **Aspecto:** cuerpo gris con orejas puntiagudas y cola; el **alfa** es más
  grande y oscuro, con ojos amarillos y una marca sobre la cabeza.
- **Hostil:** si la manada **ve al jugador** (a 250 px, estando detectable), se
  **alerta** y lo **persigue hasta matarlo**, mordiendo (daño + posible
  **desangrado**). Ataca también a las **sombras** que se acerquen, siempre a la
  **amenaza más cercana**. Pierde el rastro si te alejas más de 600 px o te
  vuelves indetectable.
- **Retirada:** si la manada queda reducida a **1 lobo**, ese lobo **huye** del
  jugador con la **velocidad aumentada**.
- **Hambre compartida (cada 6 min):** si tiene hambre y no está en combate,
  **caza conejos y venados**; con que **un** lobo mate a una presa, **toda la
  manada** sacia el hambre. Aunque no tengan hambre, atacan al jugador o a las
  sombras que se acerquen o los ataquen.
- **Crecimiento:** cada **1 min**, si no está en combate, la manada gana **+1
  lobo** (hasta 4). Al llegar a 4 sin alfa, **uno evoluciona a alfa** (gana su
  vida, daño, desangrado y aspecto).
- **Manada nueva:** si la exterminas, al minuto **se inicia otra con 2 lobos en
  otro bosque** (a más de 1500 px y fuera de tu vista), que crece igual. Siempre
  hay como máximo **7 manadas**.
- **Velocidad:** paseo 40, persecución 165, retirada 210.

### Oso (en su cueva, roca gigante)
- **Tanque territorial:** vida **150**, muy resistente, lento pero demoledor.
  Hay **8–12 osos** por mundo; cada uno vive en una **roca gigante** que hace de
  su **cueva**.
- **Aspecto:** cuerpo grande marrón con orejas redondas y hocico; ojos rojos al
  atacar.
- **Zarpazo:** daño **15–25** (físico) **+ empuje fuerte**, y además **resta un
  30% extra directo al escudo** del jugador.
- **Territorial:** se enfurece si te acercas mucho a él o a su cueva (~180 px) o
  lo golpeas, y te **caza a zarpazos** mientras estés en su territorio (~1000 px);
  si te alejas, **regresa a su cueva**.
- **Rugido:** al alertarse (y cada 10 s en combate) lanza una **onda de choque**
  que te **ralentiza** (~30% por 2 s).
- **Guarida:** vive metido en su cueva — ahí es **intocable** y se **regenera**.
  Sale si te detecta (**emboscada**) y, además, **cada 1 minuto sale 10 s** a
  acercarse al **lago más cercano** a "pescar" y vuelve.
- **Entrada de la cueva:** la roca del oso tiene una **entrada oscura** dibujada
  que la distingue de una roca normal.
- **Orbe de la cueva:** solo se puede **entrar a la cueva cuando el oso muere**.
  Al llegar a la entrada, el **mapa se oscurece** (simula estar dentro de la cueva)
  y recoges un **orbe que cura +20** de vida y da **+2 XP** (un solo uso; más
  recompensas más adelante). El orbe aparece también si el oso muere por un
  efecto (desangrado, quemadura, veneno).
- **Reaparición:** **3 min** después de morir aparece un **oso nuevo en su
  cueva** (si no estás dentro y la roca sigue en pie; si Cortar la destruyó, ya no
  vuelve). El orbe que no recogiste se pierde.
- **Velocidad:** lento (paseo 90, persecución 120).

### Cocodrilo (zona profunda del lago)
- **Depredador de emboscada acuática:** vive en la **zona profunda peligrosa** de
  los lagos grandes (**1 por lago**). Vida **70** y un **escudo físico de 30** con
  las mismas reglas que el del jugador (absorbe parte del daño físico y se
  regenera).
- **Acecho sumergido:** mientras espera es **intocable** — solo se ven una sombra
  y sus ojos sobre el agua. Patrulla el lago (temáticamente "caza" peces/ranas,
  que reaparecen).
- **Emboscada:** solo te detecta si **entras a la zona profunda peligrosa** del
  lago (el centro); entonces **emerge** y muerde fuerte (**18–30** + empuje).
  Solo es vulnerable mientras está emergido. Si una **mascota** (sombra) lo
  daña, **cambia de objetivo** y ataca al atacante.
- **Veloz en el agua, lento en tierra:** te persigue muy rápido dentro del lago y
  sale un poco a la orilla, pero en tierra es lento; si te alejas del lago, **vuelve
  a sumergirse**.
- **Velocidad:** agua 210, tierra 65.

---

## Notas de diseño

- **Reaparición:** venados y jabalíes se recuperan por **reproducción**; zorros,
  lobos y osos además **reaparecen** con el tiempo, y las madrigueras vacías se
  mudan (ver cada animal y `sistema_xp.md`). Nada pasa nunca del máximo de su
  especie. El cocodrilo no vuelve.
- **Experiencia:** cada animal muerto a manos del jugador o de sus sombras da XP
  (tabla en `sistema_xp.md`); lo que cazan zorros y lobos salvajes no cuenta.
- Mientras un zorro está **invisible** (Paso 0) queda fuera de la lista de objetivos
  y de las colisiones: es intencional, para mostrar la característica estrella de
  Paso 0.
- Los efectos de estado (quemadura, veneno, inmovilización) de un animal solo
  "corren" mientras está cerca de la cámara; si se aleja de la pantalla, el efecto
  se congela hasta que vuelvas (decisión por rendimiento).
- **Escudo (herramienta):** los golpes y mordidas de jabalí, zorro, lobo, oso y
  cocodrilo consultan al Escudo igual que la espada del maniquí: si está desenfundado
  y su arco frontal cubre al animal, el ataque se bloquea entero (sin daño, sin
  desangrado, sin el desgaste extra de escudo del oso), el escudo se desgasta y el
  animal sale repelido con el empuje del escudo (40).
- **Autoapuntado:** se suelta solo si el animal fijado deja de estar al alcance
  (zorro invisible, oso en su cueva, cocodrilo sumergido o conejo en la madriguera).
