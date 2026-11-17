# Plan maestro del MVP

Fecha: 2026-11-16 · Estado: en ejecución · Fuente: [brief](../brief.md)

## Objetivo

Entregar un MVP funcional de Kanan: una corrida de un solo comando que optimiza un plan de
brechas con NSGA-II sobre un mapa sintético, lo valida contra métodos simples en escenarios
nuevos y genera todas las salidas que pide el brief.

## Alcance

Incluido:

- Mapa sintético con las características de La Sepultura (relieve, vegetación, río, poblados,
  caminos, cultivos, zona núcleo).
- Autómata celular de Alexandridis et al. (2008) con viento y pendiente.
- Cromosoma de K brechas × 4 genes, trazado, costo, impacto y reparación por presupuesto.
- NSGA-II propio con 4 objetivos y manejo de restricciones.
- Cuatro métodos de referencia y evaluación en escenarios no vistos.
- Gráficas, mapas, animación, tablas y un reporte HTML.
- CLI y archivos de configuración YAML.

Fuera del MVP (queda como trabajo futuro):

- Mapa real de La Sepultura a partir de INEGI (paso 7 del brief, "si queda tiempo").
- Interfaz gráfica interactiva.
- Presentación y reporte escrito del curso.

## Fases

Cada fase es una rama `feature/*` que se integra a `develop`. Su plan detallado está en este
mismo directorio.

| # | Rama | Entrega | Plan |
| --- | --- | --- | --- |
| 1 | `feature/base-proyecto` | Estructura, configuración, documentación | este archivo |
| 2 | `feature/base-conocimiento` | Catálogos y mapa sintético | [01](01-base-conocimiento.md) |
| 3 | `feature/simulador-fuego` | Autómata, escenarios, pruebas de cordura | [02](02-simulador-fuego.md) |
| 4 | `feature/plan-brechas` | Cromosoma, trazado, costo, reparación | [03](03-plan-brechas.md) |
| 5 | `feature/nsga2` | Función de aptitud y NSGA-II | [04](04-aptitud-nsga2.md) |
| 6 | `feature/validacion` | Métodos de referencia y comparación | [05](05-validacion.md) |
| 7 | `feature/salidas` | Gráficas, mapas, animación, reporte | [06](06-salidas.md) |
| 8 | `feature/cli` | Caso de uso completo y CLI | [07](07-cli-pipeline.md) |
| 9 | `release/0.1.0` | Corrida de verificación, versión y etiqueta | — |

## Criterio de terminado

- `pytest` pasa, incluidas las tres pruebas de cordura del simulador.
- `kanan ejecutar` termina sin errores y produce el reporte con todas las salidas.
- Los planes de Kanan queman menos que las brechas al azar con el mismo presupuesto, en
  escenarios de prueba.
- `main` contiene la versión etiquetada `v0.1.0`.

## Registro

- Decisiones: [`docs/decisiones`](../decisiones/README.md).
- Lo realizado: [`docs/bitacora.md`](../bitacora.md) y [`CHANGELOG.md`](../../CHANGELOG.md).
- Forma de trabajo: [`CONTRIBUTING.md`](../../CONTRIBUTING.md).
