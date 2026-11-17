# Guía de estudio de Kanan

Qué hay que saber para entender Kanan a fondo y poder rehacerlo a mano, sin copiar el código.

## Cómo usar esta guía

- Está ordenada como se construye el proyecto: cada módulo depende de los anteriores.
- Cada módulo dice **qué estudiar**, **dónde está en el código**, **cómo comprobar que lo
  entendiste** y un **ejercicio** para hacerlo tú.
- La sección [Ruta para rehacerlo](#ruta-para-rehacerlo-a-mano) convierte los módulos en hitos
  con criterio de terminado.
- Las [preguntas de defensa](#preguntas-de-defensa) son las que conviene poder contestar sin
  mirar nada.
- Complementos: el [video explicativo](../video/README.md) da la vista general en 7 minutos;
  las [decisiones](decisiones/README.md) explican cada "por qué"; el [brief](brief.md) es el
  planteamiento original.

Si solo tienes una tarde, estudia los módulos 3, 5, 6 y 7: son el corazón del proyecto.

## Mapa del proyecto

| Pieza | Archivo | Módulo de esta guía |
| --- | --- | --- |
| Catálogos de vegetación y zonas | `src/kanan/dominio/catalogos.py` | 2 |
| Mapa y mapa sintético | `src/kanan/dominio/mapa.py`, `mapa_sintetico.py` | 2 |
| Autómata del fuego | `src/kanan/simulacion/automata.py` | 3 y 4 |
| Escenarios | `src/kanan/simulacion/escenarios.py` | 3 |
| Cromosoma, trazado, reparación | `src/kanan/dominio/plan.py` | 5 |
| Función de aptitud | `src/kanan/optimizacion/aptitud.py` | 6 |
| NSGA-II | `src/kanan/optimizacion/nsga2.py` | 6 y 7 |
| Hipervolumen | `src/kanan/optimizacion/hipervolumen.py` | 6 |
| Elección de los tres planes | `src/kanan/optimizacion/seleccion.py` | 6 |
| Métodos de referencia | `src/kanan/validacion/referencias.py` | 8 |
| Comparación | `src/kanan/validacion/comparacion.py` | 8 |
| Caso de uso completo | `src/kanan/aplicacion/corrida.py` | 9 |
| Figuras y reporte | `src/kanan/salidas/` | 10 |
| Aplicación interactiva | `src/kanan/interfaz/app.py` | 10 |
| Pruebas | `tests/` | todos |

## Conocimientos previos

Antes de empezar conviene tener:

- **Python intermedio:** funciones, clases, `dataclasses`, anotaciones de tipos, módulos y
  paquetes, entornos virtuales.
- **NumPy:** arreglos, indexación con máscaras booleanas, *broadcasting*, operaciones por eje
  (`axis`), generadores de números aleatorios (`np.random.default_rng`).
- **Probabilidad básica:** probabilidad de un evento, eventos independientes, valor esperado,
  varianza, muestreo.
- **Trigonometría:** seno, coseno, arcotangente, grados y radianes, vectores en el plano.
- **Git básico:** commit, rama, merge.

---

## Módulo 1 · El problema y cómo se modela

**Qué estudiar**

- Qué es una brecha cortafuego y por qué ubicarla es difícil (no se sabe dónde iniciará el
  fuego ni cómo soplará el viento).
- La diferencia entre un problema de **optimización** (buscar el mejor plan) y uno de
  **simulación** (saber qué pasa con un plan dado). Kanan usa la simulación *dentro* de la
  optimización.
- Qué significa que un problema sea **multiobjetivo** y por qué aquí los objetivos chocan.
- Variables de decisión, función objetivo y restricciones.

**En el proyecto**

| Concepto | En Kanan |
| --- | --- |
| Variables de decisión | 8 brechas × (x, y, ángulo, longitud) = 32 números |
| Objetivos (todos a minimizar) | Área quemada, valor afectado, costo, impacto ecológico |
| Restricciones | Presupuesto; no trazar sobre agua ni poblados; rangos de los genes |
| Incertidumbre | Punto de ignición y viento, que se sortean |

**Compruébalo:** explica en dos minutos, sin jerga, qué entra y qué sale de Kanan.

**Fuente:** [brief](brief.md), secciones "Contexto" y "Variables a optimizar".

---

## Módulo 2 · El mapa: datos en cuadrícula

**Qué estudiar**

- Representación *raster*: el terreno como matrices donde cada celda guarda un valor.
- Capas: varias matrices del mismo tamaño (vegetación, densidad, elevación, zona de valor).
- Tablas de consulta: guardar un identificador por celda y traducirlo con un catálogo
  (`tabla[matriz_de_ids]`).
- Pendiente a partir de la elevación: gradiente (`np.gradient`) y arcotangente.
- Generación de terreno sintético: ruido suave por interpolación bilineal, y por qué sumar
  varias escalas da un relieve creíble.
- Distancia sobre una cuadrícula (distancia de Chebyshev por dilataciones sucesivas).
- Convertir una matriz de pesos en una distribución de probabilidad (dividir entre la suma).

**En el proyecto**

- `Mapa` es solo un contenedor de matrices; no sabe si vienen de un generador o de INEGI.
- El mapa sintético arma: relieve → vegetación por altitud y humedad → río → poblados y
  cultivos → caminos → riesgo de ignición.
- El riesgo de ignición decae con la distancia a caminos y cultivos, porque casi todos los
  incendios son de origen humano.

**Compruébalo**

- ¿Por qué la fila 0 es el norte? ¿Qué pasaría con el viento si lo olvidas?
- ¿Por qué el río se traza 4-conexo? (Pista: mira el módulo 5.)

**Ejercicio:** genera una matriz de 40 × 40 de elevación con ruido suave y clasifícala en tres
tipos de vegetación por altura. Dibújala con `plt.imshow`.

---

## Módulo 3 · El fuego: autómata celular probabilístico

Es la pieza de la que depende todo lo demás.

**Qué estudiar**

- **Autómata celular:** cuadrícula, estados, vecindad y regla de transición. Vecindad de Moore
  (8 vecinas) frente a von Neumann (4).
- El **modelo de Alexandridis et al. (2008)**: estados, regla y la fórmula de probabilidad.
- **Simulación de Monte Carlo:** un solo incendio no dice nada; se promedian muchos.
- **Números pseudoaleatorios y semillas:** por qué una simulación debe poder repetirse.
- **Números aleatorios comunes:** comparar dos alternativas con la *misma* suerte para que la
  diferencia se deba a ellas y no al azar.
- Idea de **percolación:** con probabilidad alta el fuego ocupa casi todo; con baja se apaga.

**La regla**

Cada celda está en uno de cuatro estados: sin combustible, con combustible, en llamas,
quemada. En cada paso, una celda en llamas intenta encender a cada una de sus 8 vecinas y
después queda quemada.

```
p_quema = p_h · (1 + p_veg) · (1 + p_den) · p_viento · p_pendiente

p_viento    = exp( V · (c1 + c2 · (cos θ − 1)) )
p_pendiente = exp( a · θ_s )
```

| Símbolo | Significado | Valor |
| --- | --- | --- |
| `p_h` | Probabilidad base | 0.58 |
| `p_veg`, `p_den` | Efecto del tipo y la densidad de la celda que recibe el fuego | catálogo |
| `V` | Velocidad del viento (m/s) | del escenario |
| `θ` | Ángulo entre el viento y la dirección en que avanza el fuego | — |
| `c1`, `c2` | Constantes del viento | 0.045, 0.131 |
| `θ_s` | Pendiente hacia la vecina, en grados (positiva cuesta arriba) | — |
| `a` | Constante de la pendiente | 0.078 |

- A favor del viento `cos θ = 1` y la probabilidad sube; en contra `cos θ = −1` y baja mucho.
- La distancia a una vecina diagonal es `√2 · lado`; se usa al calcular la pendiente.

**Lo que Kanan hace distinto y hay que entender**

- **Azar por arista.** El número aleatorio de cada intento no sale de una secuencia: es una
  función de (semilla del escenario, celda de origen, dirección). Así dos planes simulados en
  el mismo escenario comparten la misma suerte y solo difieren por sus brechas. Consecuencia
  comprobable: agregar una brecha nunca aumenta lo quemado. Ver
  [ADR 004](decisiones/004-azar-por-arista.md).
- **La ignición arde aunque tenga una brecha encima**, para que el algoritmo no "gane"
  tapando los puntos de inicio.
- **Duración máxima:** el incendio se corta a los 45 pasos, que representa el tiempo hasta
  que llega el combate. Sin ese límite, una brecha solo retrasaría al fuego.

**Compruébalo: las pruebas de cordura** (`tests/test_automata.py`)

1. Con viento, el fuego se alarga en esa dirección.
2. En pendiente, sube más rápido de lo que baja.
3. Una brecha continua lo detiene.

Si tu simulador pasa estas tres, la regla está bien implementada.

**Ejercicio:** escribe el autómata en Python puro sobre una cuadrícula de 30 × 30 uniforme,
sin viento ni pendiente. Después agrega el viento y verifica la prueba 1.

**Fuentes:** Alexandridis et al. (2008); [ADR 004](decisiones/004-azar-por-arista.md).

---

## Módulo 4 · Rendimiento: por qué corre en segundos

**Qué estudiar**

- Por qué los ciclos en Python puro son lentos.
- **Vectorización** con NumPy y sus límites: sirve cuando la operación toca todo el arreglo.
- **Compilación JIT con Numba:** `@njit`, qué código acepta (arreglos y ciclos, no objetos),
  `parallel=True` y `prange`.
- Elegir el algoritmo antes que el lenguaje: recorrer solo el **frente activo** (las celdas
  recién encendidas) en lugar de toda la cuadrícula en cada paso.
- **Precálculo:** lo que depende solo del mapa se calcula una vez; lo que depende del
  escenario, una vez por escenario.
- **Concurrencia:** condiciones de carrera y exclusión mutua (`threading.Lock`).

**En el proyecto**

- `SimuladorFuego.__init__` precalcula la probabilidad por celda y el factor de pendiente por
  dirección; el factor de viento se calcula por escenario.
- `_propagar` es el núcleo: mantiene una lista con el frente y la va reemplazando.
- `_simular_lote` reparte *planes × escenarios* entre los núcleos con `prange`.
- **Medido:** 3 000 incendios en centésimas de segundo; seis millones en 27 s.
- La capa de hilos de Numba no admite llamadas simultáneas desde varios hilos de Python: por
  eso todas pasan por un candado. Ver
  [ADR 013](decisiones/013-candado-para-codigo-paralelo.md).

**Compruébalo**

- ¿Por qué NumPy solo no basta para este autómata?
- ¿Qué pasa si dos hilos llaman a la vez a una función `parallel=True`?

**Ejercicio:** mide tu autómata del módulo 3 en Python puro, luego decóralo con `@njit` y
vuelve a medir. Anota el factor de mejora.

**Fuentes:** documentación de Numba; [ADR 001](decisiones/001-python-numpy-numba.md).

---

## Módulo 5 · El cromosoma: de 32 números a brechas en el mapa

**Qué estudiar**

- **Codificación** en algoritmos genéticos: genotipo (los números) y fenotipo (lo que
  significan). Codificación binaria frente a real.
- Por qué la codificación decide si el algoritmo funciona: una mala produce soluciones sin
  sentido.
- **Rasterización de segmentos:** pasar de una línea continua a celdas. Algoritmo de
  Bresenham y muestreo a lo largo del segmento.
- **Conectividad 4 y 8:** una línea diagonal 8-conexa deja pasar un fuego que se propaga a 8
  vecinas.
- **Manejo de restricciones:** penalización, reparación y dominancia restringida.
- **Búsqueda por bisección** para encontrar el mayor factor que cumple una condición.

**En el proyecto**

- Cada brecha: `x`, `y` de inicio (metros), `ángulo` (0° = este, 90° = sur) y `longitud`.
- **Por qué segmentos y no celdas:** un cromosoma de una casilla por celda tendría 6 400
  genes y daría puntos sueltos que no frenan nada. Un segmento siempre es una línea continua.
- **Trazado:** se avanza por el segmento en pasos de un cuarto de celda; cuando cambia de fila
  y columna a la vez se marca también la esquina, para que la brecha sea 4-conexa.
- **Costo** = metros recorridos × costo por metro de cada celda, donde

  ```
  costo por metro = costo de desmonte del tipo × factor de densidad × (1 + pendiente / 30°)
  ```

- **Impacto ecológico** = metros × ancho de la brecha × valor ecológico de la vegetación.
- **Reparación:** si el plan excede el presupuesto, se busca por bisección el mayor factor
  `f ≤ 1` tal que con longitudes `max(mínima, f · longitud)` el costo quepa.
- Los tramos fuera del mapa, sobre agua o sobre poblados se omiten y no se cobran.

**Compruébalo**

- Dibuja en papel una diagonal 8-conexa y muestra por dónde cruza el fuego.
- ¿Por qué el costo se cobra por metro y no por celda marcada?
  ([ADR 005](decisiones/005-brechas-como-segmentos.md))
- ¿Qué pasa con un plan que sigue excedido con todas las brechas en la longitud mínima?

**Ejercicio:** escribe una función que reciba `(x, y, ángulo, longitud)` y devuelva la máscara
de celdas. Pruébala en tu autómata: una diagonal debe detener el fuego.

---

## Módulo 6 · Optimización multiobjetivo

**Qué estudiar**

- **Dominancia de Pareto:** `A` domina a `B` si es igual o mejor en todos los objetivos y
  estrictamente mejor en al menos uno.
- **Frente de Pareto:** el conjunto de soluciones que nadie domina.
- Por qué **no** conviene sumar los objetivos con pesos: hay que elegir los pesos antes de
  conocer las opciones, y se pierden partes del frente.
- **Ordenamiento no dominado:** frente 1, frente 2, … El número de frente es el rango.
- **Distancia de apiñamiento:** qué tan aislada está una solución dentro de su frente.
- **Hipervolumen:** el volumen del espacio de objetivos dominado por el frente, respecto a un
  punto de referencia. Es el indicador más usado para medir un frente con un solo número.
- **Dominancia restringida (Deb):** un factible domina a un infactible; entre infactibles gana
  el de menor violación.

**Los cuatro objetivos**

| Objetivo | Cómo se calcula |
| --- | --- |
| `area_quemada` | Hectáreas quemadas, promedio sobre los escenarios |
| `valor_afectado` | Hectáreas quemadas de cada zona × su peso, promedio |
| `costo_brechas` | Suma de metros × costo por metro |
| `impacto_ecologico` | Suma de metros × ancho × valor ecológico |

**En el proyecto**

- `matriz_dominancia` compara todos contra todos de una sola vez con *broadcasting*.
- El hipervolumen se estima por Monte Carlo: se sortean 20 000 puntos en la caja y se cuenta
  qué fracción queda dominada. Ver
  [ADR 009](decisiones/009-hipervolumen-monte-carlo.md).
- De todo el frente se presentan tres planes: menor área, menor costo con un piso de
  protección, y el más cercano al punto ideal.

**Compruébalo:** con estos puntos (objetivo 1, objetivo 2), ambos a minimizar, calcula el
rango de cada uno a mano:

```
(1, 5)  (2, 3)  (4, 1)  (3, 4)  (5, 5)
```

Respuesta: los tres primeros son rango 1; `(3, 4)` es rango 2; `(5, 5)` es rango 3. Es la
prueba `test_ordenamiento_en_un_ejemplo_conocido`.

**Ejercicio:** implementa la función de dominancia y el ordenamiento, y verifica con el
ejemplo.

---

## Módulo 7 · Algoritmos genéticos y NSGA-II

**Qué estudiar**

- El ciclo de un algoritmo genético: población, evaluación, selección, cruza, mutación,
  reemplazo.
- **Exploración frente a explotación** y el papel de cada operador.
- **Selección por torneo binario.**
- **Cruza SBX** (*Simulated Binary Crossover*) para genes reales y su parámetro `η`.
- **Mutación polinomial** y su parámetro `η`.
- **Elitismo:** no perder a los mejores.
- **NSGA-II** (Deb et al., 2002): cómo combina rango, apiñamiento y elitismo.
- **Problemas de prueba** con frente conocido (familia ZDT) para validar una implementación.

**El ciclo de NSGA-II, paso a paso**

1. Población inicial al azar (reparada).
2. Evaluar: objetivos y violación de cada individuo.
3. Calcular rango y apiñamiento.
4. **Torneo binario:** dos al azar; gana el de menor rango y, si empatan, el más aislado.
5. **Cruza:** intercambio de brechas completas, luego SBX gen por gen.
6. **Mutación polinomial.**
7. Regresar los genes a su rango y **reparar** por presupuesto.
8. Evaluar a los hijos.
9. **Elitismo:** juntar padres e hijos (2N), ordenar por rango y apiñamiento, quedarse con N.
10. Repetir desde el paso 3.

**Fórmulas de los operadores**

SBX, con `u` uniforme en [0, 1):

```
β = (2u)^(1/(η+1))                 si u ≤ 0.5
β = (1 / (2(1 − u)))^(1/(η+1))     si u > 0.5

hijo₁ = 0.5 · ((1 + β)·p₁ + (1 − β)·p₂)
hijo₂ = 0.5 · ((1 − β)·p₁ + (1 + β)·p₂)
```

Mutación polinomial:

```
δ = (2u)^(1/(η+1)) − 1             si u < 0.5
δ = 1 − (2(1 − u))^(1/(η+1))       si u ≥ 0.5

gen ← gen + δ · (máximo − mínimo)
```

Apiñamiento, para cada objetivo `m` con el frente ordenado por ese objetivo:

```
d(i) += ( f_m(i+1) − f_m(i−1) ) / ( f_m máximo − f_m mínimo )
```

Los extremos de cada objetivo reciben distancia infinita.

- Un `η` grande deja a los hijos cerca de los padres (explotación); uno chico los aleja
  (exploración). Kanan usa 15 en la cruza y 20 en la mutación.
- La probabilidad de mutación por gen es `1/32`: en promedio muta un gen por individuo.

**Lo que Kanan hace distinto y hay que entender**

- **Cruza por brechas completas** antes de SBX: una brecha es una unidad con sentido, y
  conviene heredarla entera.
- **El ángulo es circular:** al salirse de 0–360 da la vuelta en lugar de pegarse al borde.
- **Reparación lamarckiana:** el hijo reparado conserva sus genes ya acortados.
- El módulo `nsga2.py` **no sabe nada de incendios**: recibe una función de evaluación. Por
  eso se puede probar con ZDT1.

**Parámetros por omisión**

| Parámetro | Valor |
| --- | --- |
| Población | 100 |
| Generaciones | 200 |
| Probabilidad de cruza | 0.9 |
| Probabilidad de intercambiar cada brecha | 0.5 |
| `η` de cruza, `η` de mutación | 15, 20 |
| Probabilidad de mutación por gen | 1/32 |
| Evaluaciones totales | 20 100 planes |

**Compruébalo**

- ¿Por qué el elitismo de NSGA-II junta padres e hijos en vez de reemplazar a los padres?
- ¿Para qué sirve el apiñamiento si ya existe el rango?
- ¿Por qué el hipervolumen puede bajar un poco entre generaciones aunque haya elitismo?

**Ejercicio:** implementa NSGA-II y pruébalo con ZDT1 (10 genes en [0, 1]):

```
f₁ = x₁
g  = 1 + 9 · promedio(x₂ … xₙ)
f₂ = g · (1 − √(f₁ / g))
```

En el frente óptimo `f₂ = 1 − √f₁`. Si tu frente final cae sobre esa curva y cubre casi todo
el rango de `f₁`, tu NSGA-II funciona.

**Fuentes:** Deb et al. (2002); Deb y Agrawal (1995); Zitzler, Deb y Thiele (2000);
[ADR 007](decisiones/007-nsga2-propio.md).

---

## Módulo 8 · Evaluación con azar y validación

**Qué estudiar**

- **Optimización bajo incertidumbre:** la aptitud es un promedio sobre escenarios sorteados.
- **Sobreajuste:** el algoritmo aprende los escenarios en lugar del problema.
- **Entrenamiento y prueba:** medir el resultado con datos que el optimizador nunca vio.
- **Líneas base:** un resultado solo significa algo comparado con alternativas simples.
- **Estadística descriptiva:** media, desviación, mediana, percentiles, diagrama de caja.
- **Comparación justa:** mismo presupuesto, mismos escenarios, mismo esfuerzo de cómputo.

**En el proyecto**

- 300 escenarios de entrenamiento, fijos durante toda la corrida, y 500 de prueba sorteados
  aparte.
- Cuatro métodos de referencia:

| Método | Qué demuestra |
| --- | --- |
| Sin brechas | El peor caso |
| Brechas al azar | Si el algoritmo no lo supera, no aprende nada |
| Alrededor de poblados | Lo que haría la intuición |
| Búsqueda aleatoria con las mismas evaluaciones | Separa el mérito del algoritmo del simple cómputo |

- **El hallazgo más importante del proyecto.** Con 30 escenarios, como proponía el brief, el
  plan quemaba 545 ha en entrenamiento y 1 165 ha en prueba, casi lo mismo que sin brechas.
  Con 300, la mejora en prueba fue real (35 %). Ver
  [ADR 008](decisiones/008-escenarios-fijos.md).

**Resultado de la corrida por omisión** (500 incendios de prueba)

| Método | Área quemada media | Reducción |
| --- | ---: | ---: |
| Sin brechas | 1 318 ha | — |
| Brechas al azar | 1 216 ha | 7.7 % |
| Alrededor de poblados | 1 088 ha | 17.4 % |
| Búsqueda aleatoria | 1 058 ha | 19.7 % |
| Kanan · menor área | 855 ha | 35.1 % |

**Compruébalo**

- ¿Por qué no basta reportar el área quemada en los escenarios de entrenamiento?
- ¿Por qué las brechas al azar se escalan hasta gastar todo el presupuesto?
- ¿Qué prueba la búsqueda aleatoria que no pruebe "brechas al azar"?

**Ejercicio:** corre Kanan con 30 y con 300 escenarios de entrenamiento y compara el área en
entrenamiento contra el área en prueba.

---

## Módulo 9 · Ingeniería de software

**Qué estudiar**

- **Arquitectura por capas** y dependencias en un solo sentido.
- **Separar el cálculo de la presentación:** quien dibuja no calcula.
- **Inyección de dependencias sencilla:** pasar funciones como argumento (el NSGA-II recibe la
  función de evaluación).
- **Configuración externa:** archivos YAML, validación y valores por omisión.
- **Pruebas automáticas:** unitarias, de propiedad ("una brecha nunca aumenta lo quemado"), de
  punta a punta, y de regresión (la de concurrencia).
- **Reproducibilidad:** semillas y guardar la configuración de cada corrida.
- **Gitflow:** `main`, `develop`, `feature/*`, `release/*`, `hotfix/*`.
- **Registro de decisiones (ADR):** contexto, decisión, alternativas, consecuencias.

**En el proyecto**

```
cli / interfaz  →  aplicacion  →  salidas
                               →  validacion  →  optimizacion  →  simulacion  →  dominio
```

- `dominio` no depende de nadie; `nsga2.py` no sabe de incendios; `salidas` solo dibuja.
- 55 pruebas; el historial muestra un hotfix real (`v0.2.1`) hecho con gitflow.

**Compruébalo:** ¿qué archivos tendrías que tocar para usar el mapa real de INEGI? (Respuesta:
solo agregar otro constructor de `Mapa`; ver
[ADR 003](decisiones/003-mapa-sintetico-primero.md).)

**Fuentes:** [ADR 002](decisiones/002-arquitectura-por-capas.md);
[CONTRIBUTING](../CONTRIBUTING.md); [bitácora](bitacora.md).

---

## Módulo 10 · Visualización e interfaz

**Qué estudiar**

- **Matplotlib:** figuras y ejes, `imshow` con `extent`, mapas de color discretos y
  secuenciales, curvas de nivel, animaciones.
- **Elegir la gráfica según el dato:** barras para comparar, cajas para dispersión, dispersión
  para el frente, líneas para la evolución; un panel por objetivo en vez de doble eje.
- **Streamlit:** el guion se vuelve a ejecutar completo en cada interacción; `session_state`
  guarda lo que debe sobrevivir; cada recarga corre en su propio hilo.
- **Altair:** gráficas declarativas con selección por clic.

**En el proyecto**

- Las funciones de `salidas` devuelven la figura o la guardan, según reciban ruta.
- La app guarda el resultado en `session_state`; usa un selector con estado en lugar de
  pestañas para no perder la sección al recargar. Ver
  [ADR 012](decisiones/012-app-interactiva.md).

**Compruébalo:** ¿por qué el resultado se pierde al cerrar la pestaña del navegador?

---

## Ruta para rehacerlo a mano

Cada hito tiene un criterio de terminado comprobable. No pases al siguiente sin cumplirlo.

| # | Hito | Terminado cuando… |
| --- | --- | --- |
| 1 | Mapa sintético | Misma semilla, mismo mapa; tiene agua, poblados, caminos y zonas de valor |
| 2 | Autómata en Python puro | Pasa las tres pruebas de cordura |
| 3 | Escenarios | Se sortean según el riesgo; el viento respeta su rango |
| 4 | Autómata compilado y por lotes | El lote da lo mismo que la simulación individual |
| 5 | Trazado de brechas | Una diagonal detiene el fuego; el costo es longitud × costo por metro |
| 6 | Reparación | Ningún plan excede el presupuesto; los que cumplían no cambian |
| 7 | Función de aptitud | Devuelve 4 objetivos; con brechas nunca quema más que sin ellas |
| 8 | NSGA-II genérico | Converge al frente de ZDT1 |
| 9 | NSGA-II sobre el mapa | El mejor área baja con las generaciones |
| 10 | Métodos de referencia | Todos gastan el mismo presupuesto |
| 11 | Validación | Kanan supera a las brechas al azar en escenarios de prueba |
| 12 | Salidas | Mapas, evolución, frente y comparación se generan sin error |

Consejos para el camino:

- **Empieza por el simulador.** Todo lo demás depende de él.
- **Escribe la prueba antes de optimizar.** La equivalencia entre el lote y la simulación
  individual te salva al compilar con Numba.
- **Prueba el NSGA-II sin fuego.** Con ZDT1 sabes si el error está en el algoritmo o en el
  problema.
- **Mide antes de decidir.** El número de escenarios se eligió midiendo, no suponiendo.

## Errores que ya cometimos

Cada uno costó tiempo; conviene conocerlos antes de repetirlos. Están en la
[bitácora](bitacora.md).

| Error | Cómo se notó | Corrección |
| --- | --- | --- |
| Sobreajuste con 30 escenarios | Buen resultado en entrenamiento, malo en prueba | 300 escenarios y prueba separada |
| Brechas diagonales que el fuego cruzaría | Se previó al diseñar el trazado | Trazado 4-conexo |
| El plan "más barato" era no construir nada | Costo 0 en el reporte | Piso de protección al elegirlo |
| El plan "equilibrado" salía más barato que el de "menor costo" | Tabla de resultados incoherente | Ordenar los tres por gasto |
| Prueba de la brecha demasiado estricta | Fallaba con viento fuerte | Exigir solo que el fuego llegue a la brecha |
| La app se cerraba sola | Código de salida 134 en el servidor | Candado para el código paralelo |
| Un clic regresaba a la primera pestaña | Prueba en el navegador | Selector con estado |
| Texto suelto aparecía en la app | Prueba en el navegador | Comentario en vez de cadena suelta |

## Preguntas de defensa

Las que conviene poder contestar de memoria.

**¿Por qué un algoritmo genético y no otro método?**
El espacio de búsqueda es enorme y continuo, la función objetivo no tiene derivada (es una
simulación con azar) y hay varios objetivos en conflicto. Un algoritmo genético multiobjetivo
no necesita derivadas y entrega todo un frente de compromisos.

**¿Por qué NSGA-II?**
Es el algoritmo de referencia para problemas multiobjetivo: ordena por dominancia sin pesos,
mantiene la diversidad con el apiñamiento y es elitista.

**¿Por qué la brecha se codifica como segmento?**
Porque una codificación por celdas tendría miles de genes y produciría puntos sueltos. El
segmento garantiza una línea continua con solo cuatro números.

**¿Cómo saben que el simulador está bien?**
Usa un modelo publicado y validado con un incendio real, y pasa tres pruebas de cordura:
viento, pendiente y brecha.

**¿Cómo saben que el algoritmo aprende y no solo tiene suerte?**
Se compara con brechas al azar y con una búsqueda aleatoria que gasta las mismas
evaluaciones, todo en incendios que nunca vio. Kanan reduce 35 %; la búsqueda aleatoria, 20 %.

**¿Qué es el sobreajuste aquí y cómo lo evitaron?**
Que el plan rodee los puntos de ignición del entrenamiento en lugar de proteger el bosque. Se
evita entrenando con muchos escenarios y midiendo en un conjunto aparte.

**¿Por qué no hay una sola respuesta?**
Porque los objetivos chocan: más protección cuesta más y desmonta más. La decisión entre
compromisos es de las personas, no del algoritmo.

**¿Cuáles son los límites del proyecto?**
El mapa es sintético; los costos y valores ecológicos son supuestos; el modelo de fuego es una
simplificación y sus pasos no están calibrados contra tiempo real. Es un prototipo de apoyo a
la decisión, no una recomendación operativa.

**¿Qué harían después?**
Construir el mapa real desde INEGI, repetir la corrida con varias semillas para medir la
variación, y calibrar el paso del autómata contra un incendio documentado.

## Fórmulas en una hoja

```
Fuego        p = p_h (1 + p_veg)(1 + p_den) · exp(V (c1 + c2 (cos θ − 1))) · exp(a θ_s)
Costo        Σ metros × costo_desmonte × factor_densidad × (1 + pendiente/30°)
Impacto      Σ metros × ancho × valor_ecológico × factor_densidad
Reparación   mayor f ≤ 1 con costo( max(mínima, f · longitud) ) ≤ presupuesto
Dominancia   A ≺ B  ⇔  A ≤ B en todo  y  A < B en algo
Apiñamiento  d(i) = Σ_m ( f_m(i+1) − f_m(i−1) ) / rango_m
SBX          β = (2u)^(1/(η+1))  o  (1/(2(1−u)))^(1/(η+1))
Mutación     δ = (2u)^(1/(η+1)) − 1  o  1 − (2(1−u))^(1/(η+1))
```

## Bibliografía

Del proyecto:

- [Brief del proyecto](brief.md), con sus fuentes sobre La Sepultura y los incendios.
- [Registro de decisiones](decisiones/README.md) y [bitácora](bitacora.md).

Algoritmos genéticos y optimización multiobjetivo:

- Deb, K., Pratap, A., Agarwal, S. y Meyarivan, T. (2002). *A fast and elitist multiobjective
  genetic algorithm: NSGA-II*. IEEE Transactions on Evolutionary Computation, 6(2), 182–197.
  DOI [10.1109/4235.996017](https://doi.org/10.1109/4235.996017).
- Deb, K. y Agrawal, R. B. (1995). *Simulated binary crossover for continuous search space*.
  Complex Systems, 9, 115–148. [Texto en la revista](https://www.complex-systems.com/?p=2148).
- Zitzler, E., Deb, K. y Thiele, L. (2000). *Comparison of multiobjective evolutionary
  algorithms: empirical results*. Evolutionary Computation, 8(2), 173–195.
  DOI [10.1162/106365600568202](https://doi.org/10.1162/106365600568202).
- Deb, K. (2001). *Multi-Objective Optimization Using Evolutionary Algorithms*. Wiley.
  ISBN 978-0-471-87339-6.

Fuego y brechas:

- Alexandridis, A., Vakalis, D., Siettos, C. I. y Bafas, G. V. (2008). *A cellular automata
  model for forest fire spread prediction: the case of the wildfire that swept through
  Spetses Island in 1990*. Applied Mathematics and Computation.
  DOI [10.1016/j.amc.2008.06.046](https://doi.org/10.1016/j.amc.2008.06.046).
- Palacios-Meneses, D., Carrasco, J., Dávila, S., Martínez, M., Mahaluf, R. y Weintraub, A.
  (2023). *Comparison of metaheuristics for the firebreak placement problem: a
  simulation-based optimization approach*.
  [arXiv:2311.17393](https://doi.org/10.48550/arXiv.2311.17393).

Herramientas:

- Documentación de NumPy, Numba, Matplotlib y Streamlit.

> Referencias verificadas en línea el 2026-11-17: autores, título, revista, año, volumen y
> páginas coinciden con los registros públicos. La excepción es Alexandridis et al. (2008):
> se confirmaron autores, título, revista, año y DOI, pero no el volumen ni las páginas, así
> que se cita solo con su DOI; tómalos de la página del artículo antes de un trabajo formal.
