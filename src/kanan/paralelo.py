"""Exclusión mutua para el código compilado en paralelo.

La capa de hilos por omisión de Numba (workqueue) no admite que dos hilos de Python lancen a
la vez una función ``parallel=True``: aborta el proceso entero. En la línea de comandos solo
hay un hilo, pero la aplicación interactiva usa uno por cada recarga de página, y dos pueden
coincidir. Todas las llamadas a núcleos paralelos pasan por este candado.
"""

from __future__ import annotations

import threading

CANDADO = threading.Lock()
