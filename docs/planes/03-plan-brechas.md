# Plan 03 · Representación y trazado de brechas

Rama: `feature/plan-brechas` · Paso 2 del brief

## Qué se construye

`dominio/plan.py` con `TrazadorBrechas`:

- `limites()`: rango de cada uno de los 4K genes.
- `trazar(poblacion)`: máscara de celdas desmontadas, costo e impacto de cada plan.
- `reparar(poblacion)`: acorta en proporción los planes que exceden el presupuesto.
- `ajustar_al_presupuesto(poblacion)`: escala para gastar todo el presupuesto (lo usan los
  métodos de referencia).

## Definiciones

- Cromosoma: K × (`x`, `y`, `angulo`, `longitud`). Ángulo 0° = este, 90° = sur.
- Costo por metro en cada celda = costo de desmonte del tipo de vegetación × factor de
  densidad × (1 + pendiente / 30°).
- Impacto por metro = valor ecológico × factor de densidad × ancho de brecha, en hectáreas
  equivalentes.
- Se omiten (y no se cobran) los tramos fuera del mapa, sobre agua o sobre poblados.

## Pruebas

- Una brecha horizontal marca exactamente las celdas esperadas.
- El costo es longitud × costo por metro para cualquier ángulo.
- Una brecha diagonal detiene el fuego en el simulador.
- Tras reparar, ningún plan excede el presupuesto y los que ya cumplían no cambian.
