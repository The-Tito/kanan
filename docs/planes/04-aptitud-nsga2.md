# Plan 04 · Función de aptitud y NSGA-II

Rama: `feature/nsga2` · Pasos 3 y 4 del brief

## Qué se construye

- `optimizacion/aptitud.py`: `Evaluador`, que traza los planes, los simula en un conjunto de
  escenarios y devuelve los 4 objetivos y la violación del presupuesto.
- `optimizacion/nsga2.py`: ordenamiento no dominado, apiñamiento, torneo binario, cruza
  (intercambio de brechas completas + SBX), mutación polinomial y el ciclo con elitismo.
- `optimizacion/hipervolumen.py`: hipervolumen por generación.
- `optimizacion/seleccion.py`: elección de los tres planes que se presentan.

## Objetivos (todos se minimizan)

| Objetivo | Cálculo |
| --- | --- |
| `area_quemada` | Hectáreas quemadas, promedio de los escenarios |
| `valor_afectado` | Hectáreas quemadas de zonas de valor × peso de la zona, promedio |
| `costo_brechas` | Suma de metros de brecha × costo por metro de cada celda |
| `impacto_ecologico` | Suma de metros × ancho × valor ecológico de la vegetación |

## Operadores

- Selección: torneo binario por rango y, en empate, mayor apiñamiento.
- Cruza (probabilidad 0.9): cada brecha completa se intercambia entre padres con
  probabilidad 0.5; después SBX (η = 15) gen por gen.
- Mutación polinomial (η = 20) con probabilidad 1/32 por gen. El ángulo es circular: al
  salirse de 0–360 da la vuelta en lugar de pegarse al borde.
- Reparación por presupuesto a todos los hijos antes de evaluarlos.

## Pruebas

- Ordenamiento y apiñamiento en ejemplos resueltos a mano.
- Convergencia al frente conocido de ZDT1 (sin simular fuego).
- Límites, genes circulares y reparación respetados; misma semilla, mismo resultado.
- Sobre el mapa: el AG reduce el área quemada y nunca produce planes fuera de presupuesto.
