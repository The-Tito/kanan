# 002 · Arquitectura por capas con el dominio al centro

Fecha: 2026-11-16 · Estado: aceptada

## Contexto

El brief separa el trabajo en dos mitades (simulador y mapas; AG y evaluación) unidas por
una función: `simular(plan, escenario) → celdas_quemadas`. El código debe permitir cambiar
el mapa sintético por el real sin tocar el AG.

## Decisión

Un paquete `kanan` con dependencias en un solo sentido:

```
cli  →  aplicacion  →  salidas
                    →  validacion  →  optimizacion  →  simulacion  →  dominio
```

| Capa | Contenido | Depende de |
| --- | --- | --- |
| `dominio` | Catálogos, mapa, plan de brechas (base de conocimiento) | nada |
| `simulacion` | Autómata celular y escenarios | dominio |
| `optimizacion` | Aptitud, NSGA-II, hipervolumen, selección de planes | dominio, simulacion |
| `validacion` | Métodos de referencia y comparación | las tres anteriores |
| `salidas` | Gráficas, mapas, animación, tablas, reporte | datos ya calculados |
| `aplicacion` | Caso de uso que orquesta una corrida | todas |
| `interfaz` | Aplicación interactiva (agregada en ADR 012) | aplicacion, salidas |
| `cli` | Argumentos y mensajes | aplicacion |

Reglas:

- `nsga2.py` no sabe nada de incendios: recibe una función de evaluación y límites.
- `salidas` no calcula nada: solo dibuja lo que recibe.
- `config.py` contiene las entradas del usuario; los parámetros fijos viven en `dominio`.

## Alternativas

- **Un solo script o notebook.** Rápido de empezar, imposible de probar por partes y de
  repartir entre dos personas.
- **Arquitectura hexagonal completa con puertos y adaptadores.** Demasiada ceremonia para un
  programa sin base de datos ni servicios externos.

## Consecuencias

- El mapa real de INEGI se agrega como otro constructor de `Mapa`, sin cambiar otras capas.
- El NSGA-II se prueba con funciones matemáticas simples, sin simular fuego.
