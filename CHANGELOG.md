# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Sin publicar]

### Agregado

- Botón "Reproducir" en el simulador de incendios de la app, con tres velocidades.
- Documento de justificación del stack tecnológico, con tres alternativas comparadas.

## [0.2.0] - 2026-11-17

### Cambiado

- `kanan ejecutar` ya no genera figuras ni `reporte.html` por omisión: guarda solo las tablas.
  El reporte se pide con `--reporte`.

### Agregado

- Aplicación interactiva (`kanan app`): corre el algoritmo y permite explorar cada plan del
  frente, simular incendios paso a paso y descargar las tablas.
- Sección "La zona real" en el reporte, con la vista satelital de Google Maps de La Sepultura.
- Video explicativo generado por código (`python -m video.generar`) y su guion por escena.

## [0.1.0] - 2026-11-17

Primer MVP funcional.

### Agregado

- Estructura del proyecto, configuración por YAML y documentación de planes y decisiones.
- Base de conocimiento: catálogos de vegetación, densidad y zonas de valor; mapa sintético.
- Simulador de incendios con el autómata celular de Alexandridis et al. (2008).
- Plan de brechas: cromosoma, trazado 4-conexo, costo, impacto y reparación por presupuesto.
- NSGA-II con cuatro objetivos, hipervolumen y selección de tres planes representativos.
- Métodos de referencia y comparación en escenarios de prueba.
- Salidas: mapas, gráficas, animación, tablas CSV y reporte HTML.
- Línea de comandos `kanan ejecutar` y `kanan mapa`.
