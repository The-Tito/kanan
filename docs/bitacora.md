# Bitácora

Registro cronológico de lo realizado. Una entrada por fase integrada a `develop`.

## 2026-11-16 · Fase 1 · Base del proyecto (`feature/base-proyecto`)

- Repositorio inicializado con `main` y `develop`; el brief quedó en `docs/brief.md`.
- Paquete `kanan` instalable (`pyproject.toml`), con `ruff` y `pytest` configurados.
- `kanan.config`: entradas del sistema como dataclasses, cargadas desde YAML y validadas.
- Plan maestro, forma de trabajo (gitflow, commits) y primeras tres decisiones registradas.

## 2026-11-16 · Fase 2 · Base de conocimiento (`feature/base-conocimiento`)

- Catálogos de vegetación, densidad y zonas de valor. Los valores de Alexandridis se usan
  donde existen; el resto son supuestos declarados en el propio archivo.
- `Mapa` como estructura de capas independiente del origen de los datos.
- Mapa sintético de 80 × 80: 6 400 ha, elevación de 300 a 1 580 m, pendiente mediana de 8°,
  río, tres poblados, 136 celdas de cultivo y 940 de zona núcleo.
- El desnivel se escala con el tamaño del área para que las pendientes no se disparen en
  mapas pequeños.

## 2026-11-16 · Fase 3 · Simulador del fuego (`feature/simulador-fuego`)

- Autómata de Alexandridis compilado con numba; recorre solo el frente activo.
- Medición: 3 000 incendios (100 planes × 30 escenarios) en 80 × 80 tardan centésimas de
  segundo; el riesgo de velocidad del brief queda cubierto.
- Con `p_h = 0.58` y 45 pasos, un incendio sin brechas quema en promedio 1 280 ha de 6 400,
  con mucha variación (de 24 a 2 770 ha entre los percentiles 10 y 90).
- Las tres pruebas de cordura del brief pasan, más equivalencia lote/individual y monotonía.
- Ajuste: la prueba de la brecha exigía que ardiera todo el lado del fuego; con viento de
  10 m/s el avance contra el viento es casi nulo, así que ahora solo exige que llegue a ella.

## 2026-11-16 · Fase 4 · Plan de brechas (`feature/plan-brechas`)

- `TrazadorBrechas`: cromosoma → máscara, costo e impacto, compilado y en paralelo.
- El presupuesto por omisión (350 000 pesos) alcanza para unos 8.6 km de brechas; 81 % de los
  planes al azar lo exceden, así que la restricción sí aprieta.
- Reparar 2 000 planes toma milisegundos.
