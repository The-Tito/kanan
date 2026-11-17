# 007 · NSGA-II implementado a mano

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

Es el proyecto final de algoritmos genéticos: el algoritmo es lo que se evalúa.

## Decisión

Implementar NSGA-II en `optimizacion/nsga2.py` con numpy, sin bibliotecas de optimización.
El módulo es genérico: recibe la función de evaluación, los límites, el tamaño de bloque para
la cruza por brechas, qué genes son circulares y la función de reparación.

## Alternativas

- **pymoo o DEAP.** Menos código y ya probados, pero ocultan justo lo que hay que demostrar
  y no traen la cruza por brechas completas.

## Consecuencias

- Se puede explicar y defender cada línea del algoritmo.
- Hay que probarlo aparte: se valida contra ZDT1, cuyo frente óptimo se conoce.
- La matriz de dominancia es O(n²) en memoria; sobra para poblaciones de cientos.
