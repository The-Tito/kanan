# Guion del video explicativo de Kanan

Generado por `python -m video.generar --guion` a partir de `video/escenas.py`; no se edita a mano.

Cada escena se narra por separado y se guarda como `video/audio/<clave>.mp3`.

## 01-problema · El problema

Kanan significa cuidar, proteger y vigilar en tseltal. Es un programa que decide dónde construir brechas cortafuego en un bosque.

El caso de estudio es la reserva de La Sepultura, en Chiapas. En dos mil veinticinco tuvo veintiocho incendios y perdió más de cuatro mil hectáreas. Casi todos los incendios del estado fueron provocados por personas.

Una brecha es una franja sin vegetación que detiene al fuego. Pero abrirla cuesta dinero, destruye parte del bosque, y el presupuesto solo alcanza para unos cuantos kilómetros.

Entonces, ¿dónde conviene ponerlas? Hay miles de combinaciones posibles, y la única forma de saber si un plan funciona es simular incendios sobre él. Eso es lo que hace Kanan.

## 02-mapa · El mapa: lo que Kanan sabe del terreno

Todo empieza con un mapa dividido en una cuadrícula de ochenta por ochenta celdas. Cada celda mide cien metros por lado y guarda qué vegetación tiene y qué tan densa es.

También guarda su elevación. Con ella se calcula la pendiente, que importa porque el fuego sube más rápido de lo que baja.

Algunas celdas valen más que otras: los poblados, la infraestructura, la zona núcleo de la reserva y los cultivos. Cada una tiene un peso según su importancia.

Y por último, el riesgo de ignición. Como casi todos los incendios son de origen humano, es más probable que el fuego empiece cerca de caminos y parcelas.

## 03-fuego · El fuego: un autómata celular

Para simular un incendio, Kanan usa un autómata celular. Cada celda está en uno de cuatro estados: sin combustible, con combustible, en llamas, o ya quemada.

La regla es simple. En cada paso, una celda en llamas intenta encender a cada una de sus ocho vecinas, con cierta probabilidad, y después queda quemada.

Esa probabilidad no es fija. Sube si la vecina tiene vegetación densa o muy inflamable. Sube mucho en la dirección del viento, y baja en contra. Y sube cuando el fuego va cuesta arriba.

Repitiendo esa regla paso a paso, el fuego se extiende por el mapa. Un escenario de incendio es un punto de inicio, un viento, y una semilla que fija el azar. Así, el mismo escenario se puede repetir con distintos planes y compararlos con justicia.

## 04-plan · El plan: un cromosoma de 32 números

Ahora, el algoritmo genético. Cada individuo es un plan de ocho brechas. Y cada brecha se describe con cuatro números: dónde empieza, en equis y en ye, hacia dónde apunta, y cuánto mide.

Cuatro números por ocho brechas dan un cromosoma de treinta y dos genes. Eso es todo lo que el algoritmo manipula.

Para probar el plan, cada brecha se dibuja sobre la cuadrícula y sus celdas se quedan sin combustible. Las diagonales se rellenan en las esquinas, para que el fuego no se cuele entre dos celdas.

Si el plan cuesta más que el presupuesto, se repara: todas sus brechas se acortan en la misma proporción hasta que alcance el dinero.

## 05-aptitud · La aptitud: cómo se califica un plan

¿Cómo se sabe si un plan es bueno? Se prueba contra trescientos incendios distintos, cada uno con su punto de inicio y su viento, y se promedian los resultados.

De ahí salen cuatro calificaciones, y las cuatro se quieren lo más bajas posible: las hectáreas quemadas, el daño a las zonas de valor, el costo de las brechas, y el impacto ecológico de abrirlas.

Estas metas se pelean entre sí. Más brechas protegen más, pero cuestan más y desmontan más bosque. Por eso no existe un único plan ganador.

## 06-pareto · Pareto: comparar sin mezclar objetivos

Para comparar planes, Kanan usa la idea de dominancia. Un plan domina a otro si es igual o mejor en todo, y estrictamente mejor en algo.

Los planes que nadie domina forman el primer frente de Pareto. Si se quitan, los siguientes forman el segundo frente, y así sucesivamente. Ese número de frente es el rango de cada plan.

Entre planes del mismo frente, se prefiere al que tiene menos vecinos cerca. Eso se llama distancia de apiñamiento, y sirve para que las soluciones no se amontonen en un solo lugar.

## 07-ciclo · El ciclo de NSGA-II

Con rango y apiñamiento ya se puede evolucionar. Primero, la selección: se toman dos planes al azar y gana el de mejor rango. Si empatan, gana el más aislado.

Después, la cruza. El hijo hereda brechas completas de cada padre, y luego sus números se mezclan un poco con los del otro.

Luego, la mutación: de vez en cuando una brecha se desplaza, gira, se alarga o se acorta.

El hijo se repara si excede el presupuesto, y se califica con los mismos trescientos incendios.

Al final, padres e hijos compiten juntos: de doscientos planes sobreviven los cien mejores. Así nunca se pierde una buena solución.

## 08-evolucion · La evolución

Este ciclo se repite doscientas generaciones. Cada punto es un plan: hacia la izquierda quema menos, hacia abajo cuesta menos. A la derecha se ve el mejor plan de cada generación. Al principio las brechas están regadas al azar. Poco a poco se acomodan y empiezan a cerrarle el paso al fuego. En total se evalúan veinte mil planes, con seis millones de incendios simulados, en menos de medio minuto.

## 09-validacion · La validación: ¿de verdad funciona?

Hay una trampa. Si el algoritmo siempre ve los mismos incendios, puede aprenderse esos incendios en vez de aprender a proteger el bosque. Con solo treinta escenarios, eso fue justo lo que pasó.

Por eso Kanan entrena con trescientos escenarios, y se califica al final con quinientos incendios nuevos que nunca vio.

Y se compara, con el mismo presupuesto, contra métodos simples: no hacer nada, poner brechas al azar, rodear los poblados, y una búsqueda aleatoria con el mismo esfuerzo de cómputo. El mejor plan de Kanan reduce el área quemada en treinta y cinco por ciento. Las brechas al azar, apenas ocho.

## 10-resultado · El resultado

Kanan no entrega una sola respuesta, sino un frente de planes. De ahí se muestran tres: el que menos deja arder, uno equilibrado, y el más barato que todavía protege.

Y hay que decirlo claro: es un prototipo. El mapa es sintético, los costos son supuestos, y el modelo de fuego es una simplificación. Sirve para apoyar una decisión, no para sustituirla.

En resumen: un mapa, planes de ocho brechas, cientos de incendios simulados, cuatro objetivos, y un algoritmo genético que conserva lo mejor de cada generación. Eso es Kanan.
