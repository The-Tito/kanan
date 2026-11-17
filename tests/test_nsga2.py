import numpy as np
import pytest

from kanan.config import ConfigAG
from kanan.optimizacion.hipervolumen import hipervolumen, hipervolumen_por_generacion
from kanan.optimizacion.nsga2 import (
    NSGA2,
    distancia_apinamiento,
    intercambio_de_bloques,
    ordenamiento_no_dominado,
)
from kanan.optimizacion.seleccion import EQUILIBRADO, MENOR_AREA, MENOR_COSTO, elegir_planes


def test_ordenamiento_en_un_ejemplo_conocido():
    objetivos = np.array([[1, 5], [2, 3], [4, 1], [3, 4], [5, 5], [2, 3]], dtype=float)
    assert ordenamiento_no_dominado(objetivos).tolist() == [0, 0, 0, 1, 2, 0]


def test_un_factible_domina_a_cualquier_infactible():
    objetivos = np.array([[9.0, 9.0], [1.0, 1.0], [0.5, 0.5]])
    violacion = np.array([0.0, 0.2, 0.1])
    assert ordenamiento_no_dominado(objetivos, violacion).tolist() == [0, 2, 1]


def test_apinamiento_premia_extremos_y_zonas_despobladas():
    objetivos = np.array([[0, 10], [1, 9], [2, 8], [9, 1], [10, 0]], dtype=float)
    d = distancia_apinamiento(objetivos, np.zeros(5, dtype=int))
    assert np.isinf(d[[0, 4]]).all()
    assert d[2] > d[1]


def test_el_intercambio_mueve_brechas_completas():
    rng = np.random.default_rng(0)
    a, b = np.zeros((50, 32)), np.ones((50, 32))
    hijo_a, hijo_b = intercambio_de_bloques(rng, a, b, 4, 0.5)
    bloques = hijo_a.reshape(50, 8, 4)
    assert (bloques.min(axis=2) == bloques.max(axis=2)).all()
    assert np.array_equal(hijo_a + hijo_b, np.ones((50, 32)))
    assert 0.3 < hijo_a.mean() < 0.7


def zdt1(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    f1 = x[:, 0]
    g = 1 + 9 * x[:, 1:].mean(axis=1)
    return np.column_stack([f1, g * (1 - np.sqrt(f1 / g))]), np.zeros(len(x))


def test_converge_al_frente_de_zdt1():
    config = ConfigAG(poblacion=60, generaciones=120, semilla=1)
    resultado = NSGA2(config, np.zeros(10), np.ones(10)).ejecutar(zdt1)
    _, frente = resultado.frente()
    # En el frente óptimo f2 = 1 - sqrt(f1).
    assert np.abs(frente[:, 1] - (1 - np.sqrt(frente[:, 0]))).mean() < 0.05
    assert frente[:, 0].max() - frente[:, 0].min() > 0.8
    assert resultado.evaluaciones == 60 * 121

    hv = hipervolumen_por_generacion(resultado.historial)
    assert hv[-1] > hv[0]
    # Puede bajar un poco cuando el frente no cabe en la población y se recorta.
    assert np.diff(hv).min() > -0.01


def test_respeta_limites_genes_periodicos_y_reparacion():
    config = ConfigAG(poblacion=20, generaciones=15, semilla=2)
    periodicos = np.array([False, True])
    vistos = []

    def evaluar(x):
        vistos.append(x.copy())
        return np.column_stack([x[:, 0], 10 - x[:, 0] + np.sin(np.radians(x[:, 1]))]), np.zeros(
            len(x)
        )

    def reparar(x):
        x = x.copy()
        x[:, 0] = np.minimum(x[:, 0], 4.0)
        return x

    nsga = NSGA2(config, np.array([0.0, 0.0]), np.array([5.0, 360.0]), periodicos=periodicos,
                 reparar=reparar)  # fmt: skip
    nsga.ejecutar(evaluar)
    todos = np.vstack(vistos)
    assert todos[:, 0].min() >= 0 and todos[:, 0].max() <= 4.0
    assert todos[:, 1].min() >= 0 and todos[:, 1].max() <= 360.0


def test_misma_semilla_mismo_resultado():
    config = ConfigAG(poblacion=20, generaciones=10, semilla=3)
    a = NSGA2(config, np.zeros(5), np.ones(5)).ejecutar(zdt1)
    b = NSGA2(config, np.zeros(5), np.ones(5)).ejecutar(zdt1)
    assert np.array_equal(a.poblacion, b.poblacion)


def test_hipervolumen_de_un_punto():
    muestras = np.random.default_rng(0).random((50_000, 2))
    hv = hipervolumen(np.array([[0.5, 0.5]]), np.zeros(2), np.ones(2), muestras)
    assert hv == pytest.approx(0.25, abs=0.01)
    assert hipervolumen(np.array([[2.0, 0.1]]), np.zeros(2), np.ones(2), muestras) == 0.0


def test_eleccion_de_los_tres_planes():
    #                   área  valor  costo  impacto
    frente = np.array(
        [
            [100.0, 50.0, 300.0, 3.0],
            [400.0, 90.0, 0.0, 0.0],  # no construir nada: barato pero no protege
            [240.0, 70.0, 120.0, 1.2],
            [170.0, 58.0, 200.0, 2.0],
            [390.0, 95.0, 290.0, 2.9],
        ]
    )
    elegidos = elegir_planes(frente)
    assert elegidos == {MENOR_AREA: 0, MENOR_COSTO: 2, EQUILIBRADO: 3}
