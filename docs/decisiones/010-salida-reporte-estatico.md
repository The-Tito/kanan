# 010 · Salida como reporte HTML estático

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief pide mapas, gráficas, animación y tablas para una presentación. No pide interfaz.

## Decisión

Cada corrida escribe una carpeta con figuras PNG, animaciones GIF, tablas CSV, un resumen
JSON y un `reporte.html` que lo reúne todo. Las figuras se hacen con matplotlib.

## Alternativas

- **Aplicación web interactiva (Streamlit, Dash).** Atractiva para la demo, pero agrega un
  servidor y dependencias, y los resultados dejan de ser un archivo que se pueda entregar.
- **Notebook.** Mezcla el cálculo con la presentación y no se ejecuta con un comando.

## Consecuencias

- El reporte se abre sin servidor y las figuras se pegan directo en las diapositivas.
- No hay exploración interactiva (por ejemplo, elegir otro plan del frente); el frente
  completo queda en `frente_pareto.csv` para quien quiera hacerlo.
- La carpeta guarda la configuración usada: una corrida se puede repetir exactamente.
