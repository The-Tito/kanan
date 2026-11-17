# 008 · 300 escenarios de entrenamiento fijos y prueba separada

Fecha: 2026-11-16 · Estado: aceptada · Se aparta del brief (~30 escenarios)

## Contexto

El brief propone ~30 escenarios por evaluación, limitado por el costo de cómputo, y advierte
del riesgo de que el AG "se aprenda" los escenarios. Con el simulador compilado, 600 000
incendios toman 3 segundos, así que el cómputo dejó de ser el límite. Se midió el efecto del
número de escenarios (100 individuos, 200 generaciones, plan de menor área, hectáreas):

| Escenarios | En entrenamiento | En prueba | Sin brechas (prueba) | Mejora real |
| --- | --- | --- | --- | --- |
| 30 | 545 | 1 165 | 1 261 | 8 % |
| 100 | 620 | 860 | 1 279 | 33 % |
| 300 | 808 | 944 | 1 446 | 35 % |

Con 30 escenarios el plan rodea esos 30 puntos de ignición y casi no protege contra
incendios nuevos: queda al nivel de las brechas al azar.

## Decisión

- 300 escenarios de entrenamiento por omisión, los mismos durante toda la corrida.
- 500 escenarios de prueba, sorteados aparte, que el AG nunca ve.
- La corrida tarda unos 30 segundos.

## Alternativas

- **30 escenarios, como el brief.** Rápido pero sobreajustado (ver tabla).
- **Sortear escenarios nuevos en cada generación.** Evita memorizarlos, pero obliga a
  reevaluar a los padres para compararlos con los hijos y vuelve ruidosas las curvas de
  evolución.

## Consecuencias

- La diferencia entre entrenamiento y prueba baja de 53 % a 14 %; el reporte muestra ambas.
- Las curvas de evolución son comparables entre generaciones porque el conjunto no cambia.
- El número sigue siendo configurable; `configs/rapido.yaml` usa 100.
