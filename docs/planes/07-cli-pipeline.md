# Plan 07 · Caso de uso y línea de comandos

Rama: `feature/cli` · Integra los pasos 1 a 6 del brief

## Qué se construye

- `aplicacion/corrida.py`:
  - `construir_sistema(config)`: mapa, trazador, simulador, evaluador y los dos conjuntos de
    escenarios (sorteos independientes para entrenamiento y prueba).
  - `ejecutar(config)`: optimiza, elige los tres planes y valida. No escribe archivos.
  - `guardar_salidas(resultado, carpeta)`: figuras, animaciones, tablas, resumen y reporte.
- `cli.py`: comandos `kanan ejecutar` y `kanan mapa`.
- `README.md` con instalación, uso y resultados.

## Flujo de `kanan ejecutar`

1. Cargar y validar la configuración.
2. Construir el sistema y compilar el simulador con una evaluación mínima.
3. NSGA-II sobre los escenarios de entrenamiento.
4. Frente de Pareto → tres planes (menor área, menor costo e impacto, más equilibrado).
5. Métodos de referencia y medición de todo en los escenarios de prueba.
6. Escribir la carpeta de salida y mostrar el resumen en consola.

## Pruebas

- Corrida diminuta de punta a punta: se escriben exactamente los archivos esperados.
- Misma configuración, mismo resultado.
- La CLI devuelve 0 al terminar y 2 con un mensaje claro ante un error de configuración.
