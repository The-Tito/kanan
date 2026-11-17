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
