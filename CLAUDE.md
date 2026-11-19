# Level_UP: contexto del proyecto

Juego 2D de vista cenital en Python (Tkinter para la creacion + pygame-ce 2.5.8, Python 3.14).
Hablar siempre en **espanol** con el usuario. Ejecutar con `python main.py`.

## Entorno (importante)
- Carpeta del proyecto: `C:\Odoo\Level_UP` (se movio desde OneDrive).
- **Hay git funcionando**: rama `master` con `origin/master` e historial de commits. (La nota antigua de que "no hay git" por el Acceso controlado a carpetas de Defender ya NO aplica.)
- Atencion a los finales de linea: el arbol de trabajo quedo en **CRLF** y HEAD en **LF**, y no hay `.gitattributes`. Si `git status` marca archivos "modificados" sin cambios reales, suele ser solo CRLF vs LF (comprobar con `git diff --ignore-all-space`).
- Para probar sin ventana: `SDL_VIDEODRIVER=dummy python -B -c "..."` (`-B` evita escribir `__pycache__`). El juego real lo prueba el usuario.

## Documentacion
- Reglas de desarrollo: `reglas.md` (raiz). Leerlas antes de cualquier cambio.
- Carpeta `Documentacion/` (indice en `Documentacion/README.md`):
  - `Level_UP_Especificaciones.md`: especificacion de juego completa y al dia (mundo, terreno, vegetacion, personaje, progresion, armas, habilidades, interfaz, controles). **Fuente de verdad del diseno.**
  - `Tablas_Escalado.md` / `.xlsx`: escalado por nivel de cada arma y habilidad.
  - `Tablas_Tipos.xlsx`: tablas de tipos.
- Todo documento nuevo de informacion va en `Documentacion/`. Este `CLAUDE.md` se queda en la raiz para que Claude Code lo cargue. Cada 3 cambios grandes se actualiza la especificacion (regla 3).

## Estado actual (resumen)
Mundo, movimiento/camara, progresion por niveles con puntos, **5 armas** y **12 habilidades** e interfaz con paneles a ambos lados. El **maniqui de pruebas** (`mundo.Maniqui`) ahora lleva **Espada Larga** y ataca con IA simple (mira al jugador y lanza golpes cada ~2 s dentro de `RANGO_ATAQUE`); su filo hace dano fisico y empuja al jugador. **Choque de armas**: al golpear tu [Espacio] y tocar su espada (`hitboxes_de_armas_chocan`), ambos salen repelidos con la misma fuerza (`max(puntos_empuje)`) y ambas armas pierden durabilidad; el choque tiene prioridad sobre el golpe al cuerpo. Las invocaciones tambien lo atacan en **modo combate** (mantener tecla + clic derecho). El **combate con armas** ya funciona: [Espacio] da un golpe (hitbox del arma); al tocar al maniqui aplica dano fisico, desgasta la herramienta y lo empuja. El golpe tiene **animacion de arco** (`angulo_swing` barre SWING_INICIO->SWING_FIN) y la **hitbox esta activa durante toda la animacion** (`DURACION_VENTANA_GOLPE`=0.18s). **Cadencia** es estadistica del arma (por nivel) + estadistica del personaje mejorable con puntos (`jugador.cadencia`, +0.1/punto); real = `arma.cadencia_efectiva(jugador)`. Empuje fijo por arma (`puntos_empuje`: dagas 4, ligera 8, larga 12, mandoble 20). Empuje y desangrado (5 golpes) activos; jugador, maniqui e invocaciones son cuerpos solidos que no se solapan (`mundo.resolver_solapamientos`, por masa). La quemadura sigue sin dispararse.

## Archivos
- `main.py`: ventana Tkinter de creacion (nombre, color, seleccion de 1 arma y hasta 3 habilidades con tooltips [?], stats). Adaptable: `construir_interfaz(ventana, ancho, alto, al_comenzar)` escala segun pantalla (`calcular_escala`), reorganiza en 2/1 columnas, desplazamiento vertical si no cabe y boton Comenzar fijo abajo. `al_comenzar` permite probarla sin lanzar el mundo. Personaje de pruebas `shadow498` (`NOMBRE_CLAVE_PRUEBAS` / `STATS_PRUEBAS`). Habilidades vienen de `HABILIDADES_DISPONIBLES`.
- `mundo.py`: bucle pygame a pantalla completa, paneles laterales (izq. stats, der. habilidades).
  - Mapa **circular de radio 5000** (`RADIO_MUNDO`), spawn en el centro con zona segura (`ZONA_SEGURA_SPAWN`), camara suave (`SUAVIZADO_CAMARA`). Solo se dibuja lo visible con offset `desplazamiento`.
  - **Rocas**: 100 a 250 (`MIN_ROCAS`/`MAX_ROCAS`), pequenas/grandes/gigantes, solidas y bloquean proyectiles.
  - **Agua**: 4-6 masas tipo nube (radio 100-500); -50% velocidad. Lagos de radio > 300 tienen centro profundo: -80% velocidad y -10 vida/s (ignora escudos).
- `vegetacion.py`: arbustos nube, 3 tipos identicos a la vista (Escondite, Venenoso, Frutal), diametro 50-150 (frutales min. 50). Si el personaje no cabe, el arbusto es solido. Dentro: `oculto=True`, mapa oscurecido (`OSCURECIMIENTO`). Frutales con ciclo de reaparicion por fases; posibilidad de matorrales (grupos densos).
- `personaje.py`: clase `Personaje`. Movimiento por clic con sub-pasos, colisiones roca (circulo-rect) y arbusto (circulo-circulo), limite circular, ojos que miran al moverse. Dano separado en **fisico** y **magico**, cada uno amortiguado por su escudo (`escudo` fisico / escudo magico), con empuje (`actualizar_empuje`).
- `herramientas.py`: 5 armas (`EspadaLigera`, `EspadaLarga`, `Mandoble`, `DagasSimples`, `Escudo`) con niveles (max 5), durabilidad y rotura. Dano = factor x Fuerza actual. El Escudo no golpea: protege y empuja al portador.
- `habilidades.py`: 12 habilidades (`Destello`, `BurstDeFuerza`, `DisparoVeloz`, `Cortar` (cuchilla `CuchillaCortante`: destruye rocas/arbustos y anula el escudo magico 10 s), `OndaSonora` (anillos 360 `AnilloSonoro`/`EmisionSonora`, ralentizacion por medio agua/tierra), `InvocacionConejos`, `InvocacionLobos`, `CargaDeFuego`, `AuraElectrica`, `ReforzamientoMagico`, `RegeneracionInversa`, `GolpeDeSuerte`), proyectiles (`ProyectilEnergia`, `ProyectilFuego`) y `Conejo`. Max nivel 20 (Regeneracion Inversa 10). Ver detalle y tablas en la especificacion.
- `word.py`: solo compatibilidad, llama a `main.py`.

## Convencion de dibujo
Todo lo del mundo se dibuja con `desplazamiento = (vista.x - mundo_x, vista.y - mundo_y)`:
pantalla = mundo - desplazamiento. Las funciones `dibujar(...)` reciben ese offset.
Orden: suelo -> agua -> rocas -> personaje -> arbustos -> capa oscura + orbes (si oculto) -> hitboxes.

## Controles
[Clic izq] mover / botones de interfaz · [1] sacar/guardar arma · [Espacio] golpear con el arma (mantener = golpes seguidos) · [2][3][4] habilidades (mantener para cargar la Carga de Fuego; con una invocacion activa, mantener = modo combate y [Clic der] da la orden; mantener y soltar de nuevo = pasivo) · [H] hitboxes · [L] subir nivel (+3 puntos, prueba) · [J] simular golpe (prueba) · [M] / boton "Volver a seleccion" regresa a la pantalla de creacion (main.py reabre la creacion; `iniciar_mundo` devuelve "menu") · [ESC] salir.

## Pendiente / ideas
- Sistema de enemigos y combate: activara el dano real, el desgaste de durabilidad, los puntos de empuje, la quemadura y una fuente de experiencia para subir sin teclas de prueba.
- Mecanica adicional prevista a partir del nivel 20 del personaje.
