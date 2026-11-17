# 003 · Mapa sintético en el MVP

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief prevé un mapa sintético como alternativa si los datos de INEGI no se procesan a
tiempo, y recomienda construir primero el simulador sobre él.

## Decisión

El MVP usa solo un mapa sintético de 80 × 80 celdas de 100 m (6 400 ha), generado con una
semilla. Imita los rasgos del área: sierra con gradiente de elevación, pastizal y selva baja
abajo, pino-encino y mesófilo arriba, un río, tres poblados con cultivos, caminos entre
ellos, y la parte alta como zona núcleo.

## Alternativas

- **Procesar INEGI desde el inicio.** Requiere geopandas/rasterio, reproyección y
  reclasificación de la serie VII; arriesga todo el proyecto por un insumo.

## Consecuencias

- Los resultados son de un área representativa, no de un sitio real. El reporte lo declara.
- Los valores de `p_veg`, costo y valor ecológico por tipo de vegetación son supuestos
  razonados, no mediciones (ver `dominio/catalogos.py`).
- `Mapa` es una estructura de arreglos independiente de su origen, lista para recibir el
  mapa real.
