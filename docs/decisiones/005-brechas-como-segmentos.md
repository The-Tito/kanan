# 005 · Trazado 4-conexo y costo por metro recorrido

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief fija la representación (segmentos, no celdas). Falta decidir cómo se pasa del
segmento a la cuadrícula. El fuego se propaga a las 8 vecinas, así que una línea diagonal
dibujada con el algoritmo usual (Bresenham) deja pasar el fuego entre dos celdas que solo se
tocan por la esquina.

## Decisión

- El segmento se recorre en pasos de un cuarto de celda. Cuando el trazo cambia de fila y de
  columna a la vez, se marca también la celda de la esquina: la brecha queda 4-conexa.
- El costo y el impacto se acumulan por metro recorrido sobre terreno construible, no por
  celda marcada. Las celdas de esquina no se cobran.

## Alternativas

- **Bresenham y cobrar por celda.** Las diagonales no detienen el fuego.
- **4-conexo y cobrar por celda.** Una diagonal costaría 41 % más que una brecha recta del
  mismo largo; el AG preferiría brechas alineadas con la cuadrícula por un artefacto.
- **Fuego con vecindad de 4.** Cambia el modelo publicado y da incendios en forma de rombo.

## Consecuencias

- El costo es exactamente `longitud × costo por metro`, sin importar el ángulo.
- Una brecha diagonal ocupa más celdas que una recta: desmonta algo más de área en la
  cuadrícula de la que se cobra. A 100 m por celda la brecha real (10 m) es mucho más angosta
  que la celda, así que la máscara ya es una aproximación.
- Dos brechas que se cruzan pagan dos veces el tramo compartido.
