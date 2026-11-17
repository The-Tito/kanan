# 006 · Reparación por presupuesto y dominancia con restricciones

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief indica: "si el costo del plan excede el presupuesto, se reducen las longitudes de
forma proporcional". El costo no es lineal en la longitud (hay tramos omitidos y celdas con
distinto costo) y cada brecha tiene una longitud mínima.

## Decisión

- Reparación: se busca por bisección el mayor factor `f ≤ 1` tal que el plan con longitudes
  `max(longitud_min, f · longitud)` cueste a lo más el presupuesto. Un plan que ya cumple no
  se toca.
- Si un plan sigue excedido con todas las brechas en la longitud mínima, queda infactible y
  el NSGA-II lo ordena con dominancia restringida (Deb): un factible domina a un infactible,
  y entre infactibles gana el de menor exceso.

## Alternativas

- **Penalizar el exceso en los objetivos.** Requiere calibrar un peso y contamina el frente.
- **Descartar y volver a sortear.** Pierde el material genético del plan.
- **Permitir longitud cero.** Rompe el rango de longitudes que el usuario pidió.

## Consecuencias

- Con la configuración por omisión todo plan es reparable; la dominancia restringida solo
  actúa si el usuario fija un presupuesto menor que K brechas mínimas.
- La reparación modifica el genotipo (reparación lamarckiana): los hijos heredan las
  longitudes ya acortadas.
