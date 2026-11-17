# 004 · Números aleatorios por arista en el autómata

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief pide que todos los individuos de una generación usen los mismos escenarios "para
compararlos con justicia". Fijar ignición y viento no basta: si el azar sale de una secuencia,
basta una brecha para desfasarla y el resto del incendio cambia por pura suerte. Ese ruido se
mezcla con el efecto real del plan y confunde al AG.

## Decisión

Cada intento de propagación obtiene su número aleatorio de una función determinista de
(semilla del escenario, celda de origen, dirección), usando el mezclador splitmix64. Un
escenario fija así la "suerte" de cada arista del mapa.

## Alternativas

- **Generador secuencial con la misma semilla por escenario.** Mismo costo, pero los
  incendios de dos planes divergen tras la primera diferencia.
- **Más escenarios por evaluación para promediar el ruido.** Multiplica el costo de cómputo.

## Consecuencias

- Dos planes en el mismo escenario difieren solo por sus brechas. Agregar una brecha nunca
  aumenta lo quemado (hay una prueba que lo verifica).
- La simulación es reproducible sin importar el número de hilos.
- Como cada celda arde una sola vez, cada arista se usa a lo sumo una vez y la distribución
  es la misma que con un generador secuencial.
- La celda de ignición arde aunque tenga brecha encima, para que el AG no gane por "tapar"
  los puntos de inicio de los escenarios de entrenamiento.
