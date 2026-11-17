# 013 · Candado global para el código paralelo

Fecha: 2026-11-17 · Estado: aceptada

## Contexto

La aplicación interactiva se cerró sola. El registro mostró que Numba abortó el proceso por
acceso concurrente: su capa de hilos por omisión (workqueue) no admite que dos hilos de Python
lancen a la vez una función `parallel=True`, y Streamlit usa un hilo por cada recarga de
página.

## Decisión

Un candado global, `kanan.paralelo.CANDADO`, envuelve cada llamada a un núcleo compilado en
paralelo (dos en el simulador y dos en el trazador de brechas).

## Alternativas

- **Capa de hilos TBB**, que sí es segura entre hilos y es lo que sugiere Numba. Agrega una
  dependencia binaria que hay que instalar aparte en cada equipo.
- **Quitar `parallel=True`.** Elimina el problema y también la velocidad que motivó usar
  Numba.
- **Un candado en la app**, alrededor de cada corrida. Protege solo a quien lo recuerde; el
  defecto está en el simulador y ahí debe resolverse.

## Consecuencias

- Dos simulaciones pedidas a la vez se atienden una tras otra. Cada una ya usa todos los
  núcleos, así que no se pierde rendimiento real.
- En la línea de comandos, con un solo hilo, el costo del candado es despreciable.
- Toda función paralela nueva debe llamarse dentro del candado; hay una prueba de
  concurrencia que lo detecta si se olvida en el simulador o el trazador.
