# Plan 06 · Salidas

Rama: `feature/salidas` · Paso 6 del brief

## Qué se construye

| Salida del brief | Archivo | Módulo |
| --- | --- | --- |
| Mejor valor y promedio de cada objetivo por generación | `evolucion.png` | `salidas/graficas.py` |
| Hipervolumen por generación | `hipervolumen.png` | `salidas/graficas.py` |
| Frente de Pareto en pares de ejes | `pareto.png` | `salidas/graficas.py` |
| Mapa con las brechas de cada plan | `plan_<clave>_mapa.png` | `salidas/mapas.py` |
| Probabilidad de quema con y sin brechas | `plan_<clave>_probabilidad.png` | `salidas/mapas.py` |
| Animación de un incendio | `plan_<clave>_incendio.gif` | `salidas/mapas.py` |
| Diagrama de caja del área quemada por escenario | `cajas.png` | `salidas/graficas.py` |
| Tabla de genes y objetivos de los tres mejores | `planes_brechas.csv`, reporte | `salidas/tablas.py` |
| Comparación contra métodos de referencia | `comparacion.png`, `comparacion.csv` | ambos |
| Todo reunido | `reporte.html` | `salidas/reporte.py` |

## Criterios de diseño

- Esta capa solo dibuja: recibe datos ya calculados.
- Un panel por objetivo en la evolución (unidades distintas, nunca doble eje).
- Color por entidad: cada plan de Kanan conserva su color en todas las figuras; los métodos
  de referencia van en gris. Paleta categórica validada para daltonismo.
- Probabilidad de quema con una escala secuencial de un solo tono y la misma escala en ambos
  paneles.
- La animación muestra el mismo incendio sin y con brechas, lado a lado.
- Toda figura tiene su tabla equivalente en CSV.

## Pruebas

Pruebas de humo: cada función escribe su archivo; el reporte escapa el texto y enlaza las
figuras.
