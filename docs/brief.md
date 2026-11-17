# Kanan — Brief del proyecto

Fundamentos de IA · Proyecto final de algoritmos genéticos · Nov 16, 2026 · @Antonio

## Resumen

Kanan es un sistema que usa un algoritmo genético multiobjetivo (NSGA-II) para decidir dónde construir brechas cortafuego en una zona forestal, con un presupuesto limitado. Su caso de estudio es la Reserva de la Biosfera La Sepultura, Chiapas.

- **Problema:** las brechas frenan el fuego, pero cuestan, desmontan vegetación y solo se pueden construir unos pocos kilómetros por temporada. Mal ubicadas, dejan zonas críticas expuestas.
- **Solución:** cada individuo del AG es un plan de 8 brechas (punto de inicio, ángulo y longitud). Cada plan se califica simulando \~30 incendios con un autómata celular.
- **Objetivos:** minimizar área quemada, daño a zonas de alto valor, costo e impacto ecológico.
- **Resultado:** los 3 mejores planes en mapa y animación, frente de Pareto, gráficas de evolución y comparación contra métodos simples.
- **Por qué vale la pena:** problema real y local, exigente pero viable, y distinto de las 18 propuestas registradas en el grupo.

## Contexto y problemática

La Sepultura fue el área natural protegida federal más afectada por incendios en Chiapas en 2025, y ubicar brechas sin simular el fuego deja huecos o desperdicia presupuesto.

| Dato | Valor | Fuente |
| --- | --- | --- |
| Incendios forestales en Chiapas (1 ene – 2 oct 2025, preliminar) | 279 incendios, 38,927 ha | [Protección Civil Chiapas](https://proteccioncivil.chiapas.gob.mx/storage/tarjetas/9b0a6646-1f35-4265-9ee9-079fc81544a3.pdf) |
| La Sepultura en el mismo periodo | 28 incendios, 4,097 ha | [Protección Civil Chiapas](https://proteccioncivil.chiapas.gob.mx/storage/tarjetas/9b0a6646-1f35-4265-9ee9-079fc81544a3.pdf) |
| Superficie de la reserva | 167,309 ha en Arriaga, Cintalapa, Jiquipilas, Tonalá, Villacorzo y Villaflores | [DOF, Programa de Manejo](https://dof.gob.mx/nota_detalle_popup.php?codigo=2059981) |
| Causas conocidas | 108 de 113 de origen humano (intencionales, agrícolas, pecuarias) | [Protección Civil Chiapas](https://proteccioncivil.chiapas.gob.mx/storage/tarjetas/9b0a6646-1f35-4265-9ee9-079fc81544a3.pdf) |

**Por qué es difícil ubicar las brechas:**

- No se sabe dónde iniciará el próximo incendio ni hacia dónde soplará el viento.
- Cada brecha tiene miles de posiciones, orientaciones y longitudes posibles.
- La calidad de un plan solo se conoce simulando muchos incendios.
- Abrir brechas cuesta y desmonta vegetación valiosa, así que más brechas no siempre es mejor.

La ubicación de cortafuegos se estudia en investigación de operaciones forestal y se considera un problema abierto; existe un estudio de 2023 que la resuelve con un algoritmo genético sobre simulaciones ([Palacios-Meneses et al.](https://doi.org/10.48550/arXiv.2311.17393)).

## Cómo funciona Kanan

&#91;embedded content: ciclo de Kanan · 7 pasos, 1 decisión\]

El paso costoso es la simulación: cada plan se prueba en \~30 incendios antes de recibir sus 4 calificaciones, y el ciclo se repite cientos de generaciones.

## Diseño del algoritmo genético

Cada individuo es un plan de K = 8 brechas, y cada brecha son 4 genes reales: un cromosoma de 32 números.

| Variable de decisión | Qué representa | Rango |
| --- | --- | --- |
| x\_inicio\_k | Coordenada horizontal donde inicia la brecha k (m) | 0 a ancho del área |
| y\_inicio\_k | Coordenada vertical donde inicia la brecha k (m) | 0 a alto del área |
| angulo\_k | Orientación de la brecha k (°) | 0 a 360 |
| longitud\_k | Largo de la brecha k (m) | longitud mínima a máxima |

**Por qué segmentos y no celdas:** un cromosoma de celdas sueltas (0/1 por celda) tendría miles de genes y produciría puntos dispersos que no frenan nada. Con segmentos, cada brecha siempre es una línea continua.

**Componentes del AG:**

- **Población inicial:** planes al azar dentro de los rangos.
- **Trazado:** cada segmento se dibuja sobre la cuadrícula y sus celdas se marcan como no combustibles; se omiten tramos fuera del mapa, sobre agua o sobre poblados.
- **Reparación:** si el costo del plan excede el presupuesto, se reducen las longitudes de forma proporcional.
- **Evaluación:** cada plan se simula en \~30 escenarios (punto de ignición + viento) y se promedian los resultados. Todos los individuos de una generación usan los mismos escenarios, para compararlos con justicia.
- **Selección:** torneo binario por rango de Pareto y distancia de apiñamiento (NSGA-II).
- **Cruza:** intercambio de brechas completas entre padres, más cruza SBX sobre los genes.
- **Mutación:** mutación polinomial (desplazar, rotar, alargar o acortar una brecha).
- **Elitismo:** implícito en NSGA-II, que conserva los mejores frentes entre padres e hijos.

## Modelo de propagación del fuego

El fuego se simula con el autómata celular de Alexandridis et al. (2008), validado con incendios reales en Grecia y usado como referencia en estudios posteriores.

- **Cuadrícula:** cada celda tiene tipo y densidad de vegetación y una elevación.
- **Estados de una celda:** sin combustible, combustible sin quemar, en llamas, quemada. Las brechas son celdas sin combustible.
- **Regla:** en cada paso, una celda en llamas enciende a cada una de sus 8 vecinas con probabilidad p\_burn y después queda quemada.

```latex
p_{burn} = p_h \, (1 + p_{veg}) \, (1 + p_{den}) \, p_w \, p_s
```

- p\_h: probabilidad base de propagación.
- p\_veg y p\_den: efecto del tipo y la densidad de vegetación.
- p\_w: efecto del viento; crece cuando el fuego avanza en la dirección del viento.
- p\_s: efecto de la pendiente; el fuego sube más rápido que baja.

Los parámetros se toman de la literatura. El modelo es una simplificación, así que Kanan se presenta como prototipo de apoyo a la decisión, no como recomendación operativa. Fuente de la fórmula: [formulación citada en arXiv 2507.00761](https://arxiv.org/pdf/2507.00761).

## Variables a optimizar y objetivos

Cuatro objetivos en conflicto: más brechas protegen más, pero cuestan más y desmontan más vegetación. Por eso NSGA-II entrega un frente de Pareto y no una sola respuesta.

| Variable a optimizar | Cómo se calcula | Objetivo |
| --- | --- | --- |
| area\_quemada | Hectáreas quemadas, promedio de los escenarios | Minimizar |
| valor\_afectado | Superficie quemada de poblados, infraestructura, zonas núcleo y cultivos, ponderada por importancia | Minimizar (maximizar protección) |
| costo\_brechas | Longitud de cada brecha × factor de pendiente y densidad de vegetación | Minimizar, sin exceder el presupuesto |
| impacto\_ecologico | Valor ecológico de la vegetación desmontada para abrir las brechas | Minimizar |

## Base de conocimiento, entradas y salidas

La base de conocimiento es fija y alimenta el cálculo de aptitud; las entradas las da el usuario en cada ejecución.

**Base de conocimiento (no modificable):**

- **Mapa del área:** vegetación por celda (Carta de Uso del Suelo y Vegetación de INEGI, serie VII, 1:250 000), elevación (Continuo de Elevaciones Mexicano de INEGI), ubicación de poblados, caminos, cultivos y zonas núcleo.
- **Catálogo de vegetación:** p\_veg, p\_den, valor ecológico y costo de desmonte por metro.
- **Catálogo de zonas de valor:** tipo y peso de importancia.
- **Modelo de propagación:** reglas y parámetros del autómata celular.
- **Escenarios:** mapa de probabilidad de ignición (mayor cerca de caminos y parcelas) y rangos de viento de temporada seca.
- **Restricciones:** no hay brechas sobre agua ni poblados; el costo no excede el presupuesto.
- **Alternativa:** mapa sintético con las características del área si los datos de INEGI no se procesan a tiempo.

**Entradas al sistema:**

- Área de estudio (real o sintética) y tamaño de celda en metros.
- Presupuesto para brechas.
- K, longitud mínima y máxima por brecha.
- Rangos de velocidad y dirección del viento.
- Número de escenarios por evaluación (\~30) y duración máxima de simulación.
- Pesos de las zonas de valor.
- Parámetros del AG: población, generaciones, probabilidades de cruza y mutación, semilla.

**Salidas esperadas:**

- **Evolución de la aptitud:** mejor valor y promedio de cada objetivo por generación, hipervolumen por generación y frente de Pareto en pares de ejes.
- **Tres mejores individuos** (menor área quemada, menor costo e impacto, más equilibrado): mapa con sus brechas, mapa de probabilidad de quema con y sin brechas, animación de un incendio, y diagrama de caja del área quemada por escenario.
- **Tabla comparativa** con los genes de cada brecha y los 4 objetivos de los tres mejores.
- **Comparación** contra métodos de referencia (siguiente sección).

## Validación y comparación

Kanan demuestra su valor si, con el mismo presupuesto, sus planes queman menos que los métodos simples en escenarios que nunca vio.

| Método de referencia | Qué representa |
| --- | --- |
| Sin brechas | El peor caso: cuánto se quema sin prevención |
| Brechas al azar | Si el AG no supera esto, no está aprendiendo nada |
| Brechas alrededor de los poblados | Una práctica intuitiva para proteger a las personas |
| Búsqueda aleatoria con el mismo número de evaluaciones | Separa el mérito del AG del simple esfuerzo de cómputo |

**Reglas para que la comparación sea justa:**

- Todos los métodos usan el mismo presupuesto.
- La comparación final se hace en un conjunto nuevo de escenarios que no se usó durante la optimización, para evitar que el AG se "aprenda" los escenarios.
- Se reportan promedio y dispersión del área quemada, no solo el mejor caso.

**Pruebas de cordura del simulador:** con viento, el fuego debe alargarse en esa dirección; en pendiente, debe subir más rápido; una brecha continua debe detenerlo.

## Riesgos y mitigaciones

El riesgo principal es la velocidad: 100 individuos × 200 generaciones × 30 escenarios son 600,000 simulaciones de incendio.

| Riesgo | Mitigación |
| --- | --- |
| Simulación lenta en Python | Vectorizar el autómata con numpy (o numba) desde el inicio; cuadrícula moderada (p. ej. 80×80); mismos escenarios por generación |
| Datos de INEGI difíciles de convertir a cuadrícula | Mapa sintético con las características del área (ya previsto en la propuesta) |
| Escala 1:250 000 muy gruesa para el detalle de una brecha | Presentarlo como área representativa y prototipo, no como plan operativo |
| Solución trivial (llenar el mapa de brechas o encerrar un solo punto de ignición) | Presupuesto como restricción e igniciones y vientos aleatorios |
| El AG se ajusta a los escenarios de entrenamiento | Evaluación final en escenarios nuevos |
| Parecido con EvacuAG (fuego en edificios) | Dejar claro: ellos evacúan personas durante el incendio; Kanan previene la propagación en un bosque antes de que ocurra |
| Modelo simplificado del fuego | Usar un modelo validado en la literatura y declarar sus límites |

## Plan de trabajo sugerido

Construir primero el simulador sobre un mapa sintético, porque todo lo demás depende de él; el mapa real es una mejora, no un requisito.

1. **Simulador del fuego** sobre un mapa sintético pequeño, vectorizado, con las pruebas de cordura (viento, pendiente, brecha).
2. **Representación y trazado:** cromosoma de 32 genes, trazado de segmentos sobre la cuadrícula, cálculo de costo e impacto, reparación por presupuesto.
3. **Función de aptitud:** escenarios de ignición y viento, cálculo de los 4 objetivos, mismos escenarios por generación.
4. **NSGA-II:** ordenamiento no dominado, apiñamiento, torneo, SBX, mutación polinomial.
5. **Métodos de referencia** y evaluación en escenarios nuevos.
6. **Salidas:** gráficas de evolución, frente de Pareto, mapas, animación, tablas.
7. **Mapa de La Sepultura** a partir de INEGI, si queda tiempo.
8. **Presentación y reporte.**

**Reparto sugerido para dos integrantes:** uno lleva el simulador y los mapas (pasos 1, 7 y animación); el otro el AG y la evaluación (pasos 2 a 5). Las salidas y la presentación se hacen juntos. La interfaz entre ambos es una función: `simular(plan, escenario) → celdas_quemadas`.

## El nombre

*Kanan* viene del tseltal, lengua maya de Chiapas, y significa cuidar, proteger, vigilar y guardar (a gente, lugares, animales, cosas), según el [Diccionario multidialectal tseltal-español de Polian](https://dictionaria.clld.org/units/tseltal-TSE28441). Se pronuncia "ka-NÁN".

Frase de apertura sugerida: *"Kanan significa 'cuidar, proteger, vigilar' en tseltal. Eso hace nuestro algoritmo: aprende a proteger el bosque."*

## Fuentes

- [Protección Civil Chiapas, tarjeta semanal de incendios forestales (corte al 2 de octubre de 2025)](https://proteccioncivil.chiapas.gob.mx/storage/tarjetas/9b0a6646-1f35-4265-9ee9-079fc81544a3.pdf)
- [DOF, Programa de Manejo de la Reserva de la Biosfera La Sepultura](https://dof.gob.mx/nota_detalle_popup.php?codigo=2059981)
- [Palacios-Meneses et al. (2023), Comparison of metaheuristics for the firebreak placement problem](https://doi.org/10.48550/arXiv.2311.17393)
- [Alexandridis et al. (2008), modelo de autómata celular para incendios (Spetses)](https://dspace.lib.ntua.gr/xmlui/handle/123456789/18520?show=full)
- [Formulación de p\_burn citada en arXiv 2507.00761](https://arxiv.org/pdf/2507.00761)
- [CONAFOR/IDEFOR, actividades de prevención física](https://idefor.cnf.gob.mx/documents/1775/download)
- [INEGI, Uso del Suelo y Vegetación serie VII](https://inegi.org.mx/contenidos/temas/usosuelo/doc/USV_250K_SVII.pdf)
- [Diccionario multidialectal tseltal-español: kanan / kanantay](https://dictionaria.clld.org/units/tseltal-TSE28441)
