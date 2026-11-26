# Reglas de desarrollo — Level_UP

Guía de trabajo para cualquier cambio en el proyecto. Deben leerse y respetarse
antes y durante cada modificación.

---

## 1. Contexto antes de cambiar

Antes de hacer **cualquier** cambio, leer el proyecto completo (todos los módulos
relevantes: `main.py`, `mundo.py`, `personaje.py`, `herramientas.py`,
`habilidades.py`, `vegetacion.py`, `fauna.py`, `inventario.py`, `talismanes.py`, `gacha.py`, `tumba.py`, `spawn.py`, `vendedores.py`) para entender el estado actual.

- Los documentos de información del proyecto (especificaciones, tablas de
  escalado, hojas de cálculo) están en la carpeta `Documentacion/`; ver su
  `README.md`. Todo documento nuevo de información se guarda ahí.

- No inventar funcionalidad, valores ni comportamientos.
- Si algo no está definido, está incompleto o es ambiguo, **preguntar antes de
  implementar** en lugar de asumir.
- Verificar primero si ya existe algo parecido para no duplicar.

## 2. Sugerencia de commit en cada cambio

Al terminar cada cambio, entregar una **sugerencia de mensaje de commit de una
sola línea** con el formato:

```
[TAG] (modulo): descripcion breve
```

Ejemplo: `[FEAT] (habilidades): Carga de Fuego con disparo rapido y carga mantenida`

TAGs habituales: `FEAT` (nueva funcionalidad), `FIX` (corrección),
`TWEAK` (ajuste de valores/balance), `REFACTOR` (mejora interna sin cambio de
comportamiento), `DOCS` (documentación).

## 3. Actualizar el documento de contexto cada 3 cambios grandes

Llevar la cuenta de los cambios grandes. **Cada 3 cambios grandes**, actualizar
`Documentacion/Level_UP_Especificaciones.md` con la información nueva, para que el documento
refleje siempre el estado real del proyecto y se pueda ver cómo avanza.

- Un "cambio grande" es una nueva mecánica, herramienta, habilidad, sistema o un
  rediseño; no un ajuste menor de un número.
- Mantener el mismo estilo y estructura del documento existente.

## 4. Pruebas para cada cambio

Generar **pruebas** (ejecutables sin ventana / headless) que comprueben la
coherencia de cada cambio nuevo:

- Fórmulas de escalado por nivel (valores en nivel 1, intermedios y nivel máximo).
- Costes de energía, límites (topes), estados y transiciones.
- Que no se rompa lo que ya funcionaba.

Además, validar siempre la **sintaxis** (`python -m py_compile`) antes de dar un
cambio por terminado.

---

## 5. Reglas adicionales de calidad

- **Dividir los cambios grandes en pasos.** Explicar brevemente qué se hará y
  advertir riesgos o dependencias antes de ejecutar.
- **No romper lo existente.** Respetar las convenciones ya usadas: nombres de
  variables, estructura de clases y el patrón de escalado (valor base +
  incremento por nivel, conservando el valor declarado en nivel 1).
- **Constantes con nombre** en lugar de números mágicos dispersos por el código.
- **Coherencia de balance:** mantener las fórmulas y proporciones ya establecidas
  entre armas, habilidades y estadísticas.
- **Textos y comentarios en español**, claros y concisos.
- **Sin emojis en el código.** Si se considera necesario añadir alguno, preguntar
  primero.
- **Sin código muerto** ni imports sin usar.
- **Editar, no reescribir de más:** modificar solo lo necesario, conservando el
  resto del archivo intacto.
- **Seguridad básica:** no exponer datos sensibles ni dejar valores de prueba
  (teclas de debug, personajes de prueba) activos sin avisarlo.
