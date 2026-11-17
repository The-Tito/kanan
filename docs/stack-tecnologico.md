# Justificación del stack tecnológico

Kanan · versión 0.2.0 · 2026-11-17

## Resumen

Kanan está escrito en Python, con NumPy para los datos y Numba para compilar el simulador de
incendios; el algoritmo genético (NSGA-II) es propio; las figuras se hacen con Matplotlib y
la interfaz con Streamlit. La elección responde a tres exigencias del proyecto:

1. **Velocidad.** Una corrida simula seis millones de incendios. Con este stack la
   optimización completa tarda 27 segundos.
2. **Que el algoritmo sea nuestro.** Es el proyecto final de algoritmos genéticos: el NSGA-II
   debe poder explicarse y defenderse línea por línea.
3. **Dos personas y un cuatrimestre.** Un solo lenguaje, sin paso de compilación manual y sin
   infraestructura.

Se consideran tres alternativas completas: Python con bibliotecas ya hechas, Julia, y una
aplicación web en TypeScript con WebAssembly. Ninguna cumple mejor las tres exigencias a la
vez (ver la [comparación](#comparación)).

> Las cifras de Kanan en este documento son mediciones de este proyecto. Las alternativas no
> se implementaron: lo que se dice de ellas es una valoración razonada, no un resultado
> medido.

## El stack usado

| Capa | Tecnología | Versión | Para qué |
| --- | --- | --- | --- |
| Lenguaje | Python | 3.13 (mínimo 3.11) | Todo el proyecto |
| Cálculo numérico | NumPy | 2.5 | Mapa, población, objetivos |
| Compilación | Numba | 0.68 | Autómata del fuego y trazado de brechas |
| Algoritmo genético | Implementación propia | — | NSGA-II completo |
| Figuras | Matplotlib, Pillow | 3.11, 13.0 | Mapas, gráficas, animaciones GIF |
| Interfaz | Streamlit, Altair | 1.67, 6.3 | Aplicación interactiva |
| Configuración | PyYAML, dataclasses | 6.0 | Entradas del usuario |
| Línea de comandos | argparse (biblioteca estándar) | — | `kanan ejecutar`, `kanan app` |
| Video | ffmpeg | 8.1 | Codificar el video explicativo |
| Pruebas y estilo | pytest, ruff | 9.2, 0.17 | 54 pruebas, análisis estático |
| Empaquetado | setuptools, `pyproject.toml` | — | Paquete instalable |
| Control de versiones | Git con gitflow, GitHub | — | Historial y versiones |

El código suma unas 4 300 líneas de Python, más 760 de pruebas.

## Por qué cada tecnología

### Python

- Es el lenguaje del curso: el profesor y el equipo lo leen sin fricción.
- Tiene en un solo ecosistema lo que el proyecto necesita: cálculo, gráficas, interfaz y
  pruebas.
- Su debilidad conocida, la velocidad en ciclos, se resuelve con Numba solo donde hace falta.

### NumPy

- El mapa es un conjunto de matrices de 80 × 80 (vegetación, densidad, elevación, zonas de
  valor) y la población una matriz de 100 × 32. Es su caso de uso natural.
- Los operadores del NSGA-II (dominancia, apiñamiento, cruza, mutación) se escriben sobre
  toda la población de una vez, sin ciclos.

### Numba

Es la decisión técnica más importante del proyecto.

- El brief identifica la velocidad como el riesgo principal: 100 individuos × 200
  generaciones × 300 escenarios son seis millones de incendios.
- El fuego avanza por un frente: en cada paso solo importan las celdas que acaban de
  encenderse. Eso se escribe como un ciclo sobre el frente, que en Python puro es lento y en
  NumPy no se puede expresar sin recorrer toda la cuadrícula.
- Numba compila ese ciclo a código máquina y lo reparte entre los núcleos del procesador,
  sin salir de Python.
- **Medido:** 3 000 incendios en centésimas de segundo; la optimización completa en 27 s.
- Esa holgura permitió subir de 30 a 300 escenarios de entrenamiento, que es lo que evitó el
  sobreajuste (la mejora real en incendios nuevos pasó de 8 % a 35 %).

Costos: la primera ejecución tarda unos segundos más por la compilación, y Numba limita qué
versiones de Python y NumPy se pueden usar.

### NSGA-II propio

- El algoritmo es lo que se evalúa en la materia; usar una biblioteca lo ocultaría.
- Kanan necesita piezas que no vienen de fábrica: cruza por brechas completas, ángulos
  circulares que dan la vuelta en 360°, y reparación por presupuesto.
- Son unas 240 líneas, validadas contra ZDT1, un problema cuyo frente óptimo se conoce.

### Matplotlib y Pillow

- Controlan cada detalle de los mapas: capas, curvas de nivel, brechas, celdas en llamas.
- El mismo código de dibujo sirve para el reporte, la aplicación y el video explicativo.
- Pillow escribe las animaciones GIF sin programas externos.

### Streamlit y Altair

- La aplicación completa (parámetros, corrida, exploración de planes, simulación paso a paso)
  son unas 390 líneas de Python, sin HTML, CSS ni JavaScript.
- Altair aporta la única gráfica que necesita interacción real: hacer clic en un plan del
  frente de Pareto.
- Es una dependencia opcional: el algoritmo y la línea de comandos funcionan sin ella.

### PyYAML y dataclasses

- La configuración es un archivo de texto legible, con validación y mensajes claros cuando
  una clave está mal escrita.
- Cada corrida guarda la configuración que usó, así que se puede repetir exactamente.

### pytest y ruff

- Las pruebas incluyen las tres de cordura que pide el brief (viento, pendiente, brecha) y la
  corrida de punta a punta.
- ruff revisa estilo e importaciones en milisegundos.

### Git con gitflow

- Cada fase tiene su rama, su plan y su entrada en la bitácora; `main` solo contiene
  versiones etiquetadas.

## Alternativa 1 · Python con bibliotecas ya hechas

**Stack:** Python, NumPy sin compilar, pymoo o DEAP para el NSGA-II, Plotly Dash para la
interfaz.

| A favor | En contra |
| --- | --- |
| Menos código que escribir y probar | El NSGA-II deja de ser propio: se pierde lo que evalúa la materia |
| pymoo trae NSGA-II, SBX e hipervolumen exacto ya validados | La cruza por brechas, los ángulos circulares y la reparación habría que escribirlos de todos modos, dentro del marco de la biblioteca |
| Sin la restricción de versiones de Numba | Sin compilar, el autómata recorre toda la cuadrícula en cada paso; con 300 escenarios la corrida dejaría de tardar segundos |
| Dash da más control sobre la interfaz | Dash exige más código (diseño y callbacks) que Streamlit para lo mismo |

**Cuándo convendría:** si el objetivo fuera aplicar un algoritmo genético a un problema, no
demostrar que se sabe construir uno.

## Alternativa 2 · Julia

**Stack:** Julia, Metaheuristics.jl o implementación propia, Makie para las figuras, Pluto o
Genie para la interfaz.

| A favor | En contra |
| --- | --- |
| Compila todo el código, no solo las funciones marcadas: los ciclos son rápidos sin herramientas extra | No es el lenguaje del curso: el equipo tendría que aprenderlo durante el proyecto |
| Un solo lenguaje para el simulador y el resto, sin las limitaciones de Numba | El profesor y los compañeros lo leerían con más dificultad |
| Sintaxis cercana a la notación matemática | Ecosistema más chico para interfaces y para futuros datos geográficos de INEGI |
| | El tiempo de compilación al arrancar se nota en un programa que se ejecuta muchas veces |

**Cuándo convendría:** en un equipo que ya domina Julia, o si el simulador creciera hasta el
punto en que Numba se quedara corto.

## Alternativa 3 · Aplicación web con TypeScript y WebAssembly

**Stack:** TypeScript con React, el simulador en Rust compilado a WebAssembly, D3 o Canvas
para los mapas, Web Workers para no congelar la página.

| A favor | En contra |
| --- | --- |
| No se instala nada: se abre un enlace y corre en el navegador | Dos lenguajes y una cadena de compilación (Rust, WebAssembly, empaquetador) |
| Se puede publicar gratis como sitio estático | Hay que construir a mano lo que Python da hecho: matrices, gráficas, pruebas numéricas |
| La interacción es más fluida que en Streamlit | El paralelismo en el navegador es más limitado y complejo que `prange` |
| Buena pieza para mostrar en un portafolio | Lejos del lenguaje del curso y del mundo científico donde están los datos de INEGI |
| | Varias veces más trabajo para llegar al mismo resultado |

**Cuándo convendría:** si la prioridad fuera que cualquier persona use Kanan desde un enlace,
como herramienta de divulgación, y hubiera tiempo y experiencia web en el equipo.

## Comparación

Valoración cualitativa frente a las exigencias del proyecto (● cumple bien, ◐ cumple a
medias, ○ cumple mal).

| Criterio | Stack usado | 1 · Bibliotecas | 2 · Julia | 3 · Web |
| --- | :---: | :---: | :---: | :---: |
| Velocidad del simulador | ● | ○ | ● | ● |
| El algoritmo es propio y explicable | ● | ○ | ● | ● |
| Lenguaje del curso | ● | ● | ○ | ○ |
| Tiempo de desarrollo para dos personas | ● | ● | ◐ | ○ |
| Facilidad para que otro lo ejecute | ◐ | ◐ | ◐ | ● |
| Camino hacia el mapa real de INEGI | ● | ● | ◐ | ○ |
| Calidad de la interfaz | ◐ | ◐ | ◐ | ● |

- La alternativa 1 falla justo en las dos exigencias centrales: velocidad y algoritmo propio.
- Las alternativas 2 y 3 igualan la velocidad, pero a cambio de salir del lenguaje del curso
  y, en el caso web, de multiplicar el trabajo.
- El stack usado es el único que cumple las tres exigencias a la vez.

## Límites del stack elegido

- **Instalación.** Quien quiera usar Kanan necesita Python y un entorno virtual; no hay un
  enlace público.
- **Numba.** Ata el proyecto a las versiones de Python y NumPy que soporta, y el código
  compilado debe ser Python simple (matrices y ciclos, sin objetos).
- **Streamlit.** Recarga la página en cada interacción y el resultado vive en la sesión del
  navegador: al cerrarla hay que volver a correr.
- **Figuras estáticas.** Salvo el frente de Pareto, las gráficas de la aplicación son
  imágenes de Matplotlib, sin acercamiento ni información al pasar el cursor.

## Referencias internas

- [ADR 001 · Python con NumPy y Numba](decisiones/001-python-numpy-numba.md)
- [ADR 002 · Arquitectura por capas](decisiones/002-arquitectura-por-capas.md)
- [ADR 007 · NSGA-II implementado a mano](decisiones/007-nsga2-propio.md)
- [ADR 008 · 300 escenarios de entrenamiento](decisiones/008-escenarios-fijos.md)
- [ADR 012 · Aplicación interactiva](decisiones/012-app-interactiva.md)
- [Bitácora](bitacora.md), con las mediciones citadas
