# Plan 05 · Métodos de referencia y comparación

Rama: `feature/validacion` · Paso 5 del brief

## Qué se construye

- `validacion/referencias.py`: los cuatro métodos simples del brief.
- `validacion/comparacion.py`: medición de todos los métodos en los escenarios de prueba.

## Métodos

| Método | Cómo se construye |
| --- | --- |
| Sin brechas | Mapa intacto |
| Brechas al azar | Genes al azar; longitudes escaladas para gastar todo el presupuesto; se promedian varios planes |
| Alrededor de poblados | Las K brechas se reparten entre los poblados (3, 3, 2) como U o cuña del lado de donde viene el viento medio, tan lejos como alcance el presupuesto |
| Búsqueda aleatoria | Tantos planes al azar como evaluaciones hizo el AG, sobre los mismos escenarios de entrenamiento; se conserva el frente no dominado y se presenta su plan de menor área |

## Reglas de justicia

- Mismo presupuesto para todos.
- La comparación usa escenarios de prueba que ningún método vio al optimizar.
- Se reportan media, desviación, mediana y percentil 90 del área quemada.

## Pruebas

- Los planes al azar gastan el presupuesto sin excederlo.
- El plan de poblados queda dentro del presupuesto y cerca de cada poblado.
- La búsqueda aleatoria devuelve solo planes no dominados.
- Todos los métodos se miden sobre los mismos escenarios.
