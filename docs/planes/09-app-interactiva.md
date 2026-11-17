# Plan 09 · Aplicación interactiva

Rama: `feature/app-interactiva` · Fecha: 2026-11-17

## Objetivo

Dejar de generar un HTML en cada ejecución y ofrecer en su lugar una aplicación donde se
corre el algoritmo y se explora el resultado.

## Qué se construye

1. `salidas`: las funciones de figuras devuelven la figura cuando no reciben ruta.
2. `aplicacion/corrida.py`: `guardar_datos` (tablas) separado de `guardar_reporte` (figuras,
   animaciones, HTML); `ejecutar` acepta una función de progreso por generación.
3. `cli.py`: `kanan ejecutar` guarda solo datos; `--reporte` para el HTML; `kanan app`.
4. `interfaz/app.py`: la aplicación.

## Secciones de la app

| Sección | Contenido |
| --- | --- |
| Barra lateral | Tamaño de corrida, presupuesto, K, longitudes, viento, duración, parámetros del AG |
| Resultado | Cifras principales, comparación con los métodos de referencia, tabla y cajas |
| Explorar planes | Frente de Pareto con clic, mapa del plan, objetivos en prueba, genes, incendio paso a paso, probabilidad de quema |
| Evolución | Objetivos por generación, hipervolumen, frente en pares de ejes |
| Zona de estudio | Mapa sintético, riesgo de ignición, Google Maps de la zona real |
| Datos | Descarga de CSV y configuración usada |

## Pruebas

- Automática, sin navegador: la app arranca, corre una configuración diminuta, dibuja las
  cinco secciones, cambia de plan y explica una configuración inválida.
- En el navegador: corrida, cambio de sección, clic sobre un punto del frente y simulación.
