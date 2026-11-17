# Plan 08 · Video explicativo

Rama: `feature/video-explicativo` · Fecha: 2026-11-17

## Objetivo

Un video que permita entender cómo funciona Kanan por dentro. La narración se graba aparte
(ElevenLabs) y el video se sincroniza con ella.

## Qué se construye

- `video/escenas.py`: diez escenas; cada una es una lista de frases con su dibujo.
- `video/motor.py`: reparte el tiempo, pone subtítulos y codifica con ffmpeg.
- `video/datos.py`: corre Kanan y guarda el mejor plan de cada generación para animarla.
- `video/generar.py`: comando único; también escribe el guion por escena.

## Escenas

| # | Escena | Qué muestra |
| --- | --- | --- |
| 1 | El problema | Cifras de La Sepultura, qué es una brecha, planes al azar |
| 2 | El mapa | Vegetación, elevación, zonas de valor, riesgo de ignición |
| 3 | El fuego | Estados, regla de las 8 vecinas, viento y pendiente, un incendio animado |
| 4 | El plan | Tabla de 32 genes, trazado sobre la cuadrícula, reparación |
| 5 | La aptitud | Un plan contra muchos incendios, los 4 objetivos, su conflicto |
| 6 | Pareto | Dominancia, frentes, apiñamiento |
| 7 | El ciclo | Torneo, cruza, mutación, reparación y evaluación, elitismo |
| 8 | La evolución | Población y mejor plan de la generación 0 a la 200 |
| 9 | La validación | Sobreajuste con 30 escenarios, comparación con métodos simples |
| 10 | El resultado | Los tres planes, límites, resumen |

## Sincronía

- Duración de la escena = duración de su audio (más una pausa corta); sin audio, se estima
  con 2.5 palabras por segundo.
- Dentro de la escena, cada frase dura en proporción a sus palabras.
- Subtítulos cortados por oración.

## Pruebas

- Unitarias del reparto de tiempos y del corte de subtítulos.
- Revisión visual de cuadros de las diez escenas.
- Una escena con audio de prueba: su duración coincide con la del audio.
