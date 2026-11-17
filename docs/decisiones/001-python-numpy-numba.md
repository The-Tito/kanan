# 001 · Python con numpy y numba

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief identifica la velocidad como el riesgo principal: 100 individuos × 200 generaciones ×
30 escenarios son 600 000 simulaciones de incendio. El curso trabaja en Python.

## Decisión

Python 3.11+ con numpy para los datos y numba para compilar el núcleo del autómata y el
trazado de brechas. El lote de simulaciones de una generación se reparte entre núcleos con
`prange`.

## Alternativas

- **Solo numpy, vectorizando toda la cuadrícula.** Cada paso recorre las 6 400 celdas aunque
  solo arda el borde del incendio. Con numba se recorre únicamente el frente activo, que es
  una fracción pequeña.
- **C++ o Rust con bindings.** Más rápido, pero agrega un paso de compilación y un segundo
  lenguaje a un proyecto escolar de dos personas.

## Consecuencias

- La primera ejecución tarda unos segundos más por la compilación (queda en caché).
- numba es una dependencia obligatoria; limita las versiones de Python y numpy admitidas.
- El código compilado debe ser Python simple (arreglos y ciclos), sin objetos.
