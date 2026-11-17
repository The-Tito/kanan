# Plan 02 · Simulador del fuego

Rama: `feature/simulador-fuego` · Paso 1 del brief

## Qué se construye

- `simulacion/escenarios.py`: `Escenarios` (ignición, viento, semilla) y su sorteo a partir
  del mapa de riesgo y los rangos de viento.
- `simulacion/automata.py`: `SimuladorFuego`, con la interfaz `simular(plan, escenario)` y
  una versión por lotes para evaluar toda una generación.

## Modelo

`p_burn = p_h (1 + p_veg)(1 + p_den) p_w p_s`, con los parámetros publicados:

| Parámetro | Valor | Significado |
| --- | --- | --- |
| `p_h` | 0.58 | Probabilidad base |
| `c1`, `c2` | 0.045, 0.131 | `p_w = exp(V (c1 + c2 (cos θ − 1)))`, V en m/s |
| `a` | 0.078 | `p_s = exp(a · θ_s)`, θ_s en grados |

`p_veg` y `p_den` son los de la celda que recibe el fuego. La distancia entre celdas
diagonales es `√2 · lado` al calcular la pendiente.

## Cómo

1. Precalcular por mapa: probabilidad por celda y factor de pendiente por dirección.
2. Precalcular por escenario: factor de viento para las 8 direcciones.
3. Núcleo compilado que recorre solo el frente activo y registra el paso de ignición.
4. Lote en paralelo sobre planes × escenarios.

## Pruebas de cordura

- Con viento, el fuego se alarga en esa dirección; sin viento, no hay dirección preferente.
- En pendiente, sube más rápido que baja.
- Una brecha continua lo detiene.
- El lote da lo mismo que la simulación individual; agregar brecha nunca quema más.
