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

## 2026-11-16 · Fase 5 · Aptitud y NSGA-II (`feature/nsga2`)

- `Evaluador` con los 4 objetivos y NSGA-II propio, validado contra ZDT1.
- La corrida del brief (100 × 200 × 30) tarda 3 segundos.
- Hallazgo: con 30 escenarios el AG sobreajusta (545 ha en entrenamiento, 1 165 en prueba,
  contra 1 261 sin brechas). Con 300 la mejora en prueba es de 35 %. Se cambió el valor por
  omisión (ADR 008).
- Hallazgo: el extremo barato del frente es un plan con las brechas fuera del mapa (costo 0).
  Es correcto como punto del frente, pero inútil como "plan de menor costo"; la selección
  ahora exige al menos la mitad de la mejor reducción de área.
- Ajustes de pruebas: el hipervolumen puede bajar un poco al recortar el frente.

## 2026-11-16 · Fase 6 · Validación (`feature/validacion`)

- Cuatro métodos de referencia y `comparar`, que los mide junto a los planes de Kanan.
- Decisión menor: las brechas al azar se escalan hasta agotar el presupuesto. Sin eso
  gastarían menos que Kanan y la comparación las perjudicaría por una razón ajena al método.
- Decisión menor: el plan de poblados protege el lado de barlovento (de donde viene el viento
  medio de la temporada), que es lo que haría una brigada con pocas brechas por poblado.

## 2026-11-16 · Fase 7 · Salidas (`feature/salidas`)

- Figuras de mapa, riesgo, evolución, hipervolumen, Pareto, comparación y cajas; animación
  del incendio; tablas CSV; reporte HTML.
- Las brechas que salen del mapa se dibujan recortadas, igual que las trata el trazado.

## 2026-11-17 · Fase 8 · Caso de uso y CLI (`feature/cli`)

- `kanan ejecutar` hace la corrida completa en cerca de un minuto: 27 s de optimización y
  28 s de validación (la búsqueda aleatoria repite las 20 100 evaluaciones del AG).
- Resultado con la configuración por omisión, en 500 escenarios de prueba: sin brechas
  1 318 ha; al azar 1 216; alrededor de poblados 1 088; búsqueda aleatoria 1 058; Kanan
  (menor área) 855, es decir 35 % menos que sin brechas. Se cumple el criterio de terminado.
- Ajuste a la selección de planes: el "más equilibrado" salía más barato que el de "menor
  costo e impacto". Ahora el de menor costo exige una cuarta parte de la mejor reducción (antes
  la mitad) y el equilibrado nunca puede ser más barato que él. Los tres quedan ordenados:
  350 000, 125 671 y 53 823 pesos.
- Revisión visual del reporte y de las figuras; se movió la leyenda de la gráfica de evolución
  porque tapaba una curva.
