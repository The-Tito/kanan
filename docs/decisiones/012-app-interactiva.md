# 012 · Aplicación interactiva; el reporte HTML pasa a ser opcional

Fecha: 2026-11-17 · Estado: aceptada · Reemplaza a [010](010-salida-reporte-estatico.md)

## Contexto

Cada corrida generaba un `reporte.html` con una decena de figuras y tres animaciones. El
usuario no quiere que se produzca un HTML en cada ejecución. Entre las opciones presentadas
(reporte bajo pedido, banderas, solo figuras, otro formato, aplicación interactiva) eligió la
aplicación interactiva.

## Decisión

- Una aplicación en Streamlit (`kanan app`) es la forma principal de usar Kanan: se ajustan
  los parámetros, se corre el algoritmo y se explora el resultado en memoria, sin escribir
  archivos.
- `kanan ejecutar` guarda solo tablas de datos. Figuras, animaciones y HTML se generan con
  `--reporte`; el código del reporte se conserva.
- La app vive en una capa nueva, `interfaz`, que no calcula nada: llama a
  `aplicacion.corrida` y dibuja con las funciones de `salidas`, que ahora pueden devolver la
  figura en lugar de guardarla.
- Streamlit es una dependencia opcional (`pip install -e ".[app]"`).
- La app escucha solo en `localhost`.

## Alternativas

- **Dash o un frontend propio.** Más control sobre la interfaz, a cambio de mucho más código
  para un proyecto cuyo valor está en el algoritmo.
- **Eliminar el reporte HTML.** Se perdería el entregable de un solo archivo para la
  presentación; mantenerlo opcional no cuesta nada.
- **Gráficas interactivas en todas las secciones.** Solo el frente de Pareto es interactivo
  (ahí el clic aporta); el resto reutiliza las figuras ya probadas.

## Consecuencias

- Se puede inspeccionar cualquier plan del frente, no solo los tres elegidos, y simular
  incendios paso a paso: antes eso exigía leer `frente_pareto.csv`.
- Explorar no deja archivos; lo que se quiera conservar se descarga desde la sección Datos.
- Las secciones se eligen con un selector con estado en vez de pestañas: así un clic en la
  gráfica (que recarga la página) no regresa a la primera sección, y solo se dibuja la
  sección visible.
- El resultado vive en la sesión del navegador: al cerrarla se pierde y hay que volver a
  correr (segundos).
- Hay una dependencia más y un servidor local mientras la app está abierta.
