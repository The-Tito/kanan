import numpy as np
import pytest

from kanan.config import Config
from kanan.dominio import catalogos as cat
from kanan.dominio.plan import GENES_POR_BRECHA, TrazadorBrechas
from kanan.optimizacion.aptitud import AREA, COSTO, VALOR, Evaluador
from kanan.optimizacion.nsga2 import NSGA2
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import generar_escenarios


@pytest.fixture(scope="module")
def sistema(mapa):
    config = Config()
    trazador = TrazadorBrechas(mapa, config.brechas)
    evaluador = Evaluador(mapa, SimuladorFuego(mapa, config.fuego), trazador, cat.pesos_zonas())
    escenarios = generar_escenarios(mapa, config.escenarios, 20, np.random.default_rng(0))
    return config, trazador, evaluador, escenarios


def test_objetivos_y_restriccion(sistema):
    config, trazador, evaluador, escenarios = sistema
    poblacion = trazador.poblacion_aleatoria(30, np.random.default_rng(1))
    objetivos, violacion = evaluador.aptitud(escenarios)(poblacion)
    assert objetivos.shape == (30, 4)
    assert (objetivos >= 0).all()
    assert (objetivos[:, COSTO] <= config.brechas.presupuesto * 1.000001).all()
    assert (violacion == 0).all()
    exceso = evaluador.violacion(np.array([2 * config.brechas.presupuesto]))
    assert exceso[0] == pytest.approx(1.0)


def test_las_brechas_no_empeoran_al_caso_sin_brechas(sistema):
    _, trazador, evaluador, escenarios = sistema
    base = evaluador.medir_sin_brechas(escenarios)
    planes = evaluador.medir(trazador.poblacion_aleatoria(30, np.random.default_rng(2)), escenarios)
    assert (planes.area_ha <= base.area_ha + 1e-9).all()
    assert (planes.valor <= base.valor + 1e-9).all()
    assert base.objetivos()[0, AREA] > 0 and base.objetivos()[0, VALOR] > 0


def test_la_evaluacion_es_determinista(sistema):
    _, trazador, evaluador, escenarios = sistema
    poblacion = trazador.poblacion_aleatoria(10, np.random.default_rng(3))
    a, _ = evaluador.aptitud(escenarios)(poblacion)
    b, _ = evaluador.aptitud(escenarios)(poblacion)
    assert np.array_equal(a, b)


def test_el_ag_mejora_el_area_quemada(sistema):
    config, trazador, evaluador, escenarios = sistema
    inferior, superior = trazador.limites()
    periodicos = np.tile([False, False, True, False], config.brechas.k)
    ag = type(config.ag)(poblacion=30, generaciones=25, semilla=5)
    nsga = NSGA2(ag, inferior, superior, tam_bloque=GENES_POR_BRECHA, periodicos=periodicos,
                 reparar=trazador.reparar)  # fmt: skip
    resultado = nsga.ejecutar(evaluador.aptitud(escenarios))
    mejor = resultado.historial.mejor()[:, AREA]
    assert mejor[-1] < 0.9 * mejor[0]
    assert (resultado.violacion == 0).all()
