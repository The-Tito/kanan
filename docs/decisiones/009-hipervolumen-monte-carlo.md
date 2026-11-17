# 009 · Hipervolumen por Monte Carlo, calculado al final

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief pide el hipervolumen por generación. Con 4 objetivos el cálculo exacto es costoso,
y el valor depende de un punto de referencia que debe ser el mismo en todas las generaciones.

## Decisión

- Guardar los objetivos de toda la población en cada generación y calcular el hipervolumen
  al terminar la corrida.
- Normalizar con una caja común: ideal = mínimo observado en toda la corrida; referencia =
  peor valor de la población inicial.
- Estimarlo con 20 000 puntos uniformes, los mismos para todas las generaciones.

## Alternativas

- **Algoritmo exacto (WFG).** Preciso pero más código que probar, para una gráfica.
- **Calcularlo dentro del ciclo.** Exige fijar la referencia antes de conocer el rango real.

## Consecuencias

- El valor es la fracción de la caja dominada (0 a 1), con error cercano a ±0.005.
- La curva puede bajar ligeramente cuando el frente no cabe en la población y el
  apiñamiento lo recorta; es propio de NSGA-II, no un error.
