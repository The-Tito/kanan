"""La aplicación interactiva llama al simulador desde varios hilos a la vez."""

from concurrent.futures import ThreadPoolExecutor

import numpy as np

from kanan.config import Config
from kanan.dominio import catalogos as cat
from kanan.dominio.plan import TrazadorBrechas
from kanan.optimizacion.aptitud import Evaluador
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import generar_escenarios


def test_varios_hilos_pueden_simular_a_la_vez(mapa):
    """Sin el candado, Numba aborta el proceso completo en esta prueba."""
    config = Config()
    trazador = TrazadorBrechas(mapa, config.brechas)
    simulador = SimuladorFuego(mapa, config.fuego)
    evaluador = Evaluador(mapa, simulador, trazador, cat.pesos_zonas())
    escenarios = generar_escenarios(mapa, config.escenarios, 40, np.random.default_rng(0))
    poblacion = trazador.poblacion_aleatoria(40, np.random.default_rng(1))
    esperado = evaluador.medir(poblacion, escenarios).objetivos()

    def trabajo(_):
        simulador.probabilidad_quema(None, escenarios)
        return evaluador.medir(trazador.reparar(poblacion), escenarios).objetivos()

    with ThreadPoolExecutor(max_workers=8) as hilos:
        resultados = list(hilos.map(trabajo, range(40)))
    assert all(np.array_equal(r, esperado) for r in resultados)
