import numpy as np
import pytest

from kanan.config import ConfigBrechas, ConfigFuego
from kanan.dominio import catalogos as cat
from kanan.dominio.plan import TrazadorBrechas
from kanan.simulacion.automata import SimuladorFuego
from tests.test_automata import CENTRO, LADO, escenarios_centro, mapa_uniforme

COSTO_SELVA = cat.VEGETACION[cat.SELVA_BAJA].costo_desmonte_m


def trazador_uniforme(**kwargs) -> TrazadorBrechas:
    config = ConfigBrechas(k=1, longitud_min_m=100.0, longitud_max_m=10_000.0, **kwargs)
    return TrazadorBrechas(mapa_uniforme(), config)


def test_brecha_horizontal_marca_las_celdas_esperadas():
    planes = trazador_uniforme().trazar(np.array([[1000.0, 550.0, 0.0, 2000.0]]))
    esperado = np.zeros((LADO, LADO), dtype=bool)
    esperado[5, 10:30] = True
    assert np.array_equal(planes.mascaras[0], esperado)


def test_el_costo_es_longitud_por_costo_por_metro():
    trazador = trazador_uniforme()
    for angulo in (0.0, 37.0, 90.0, 225.0):
        planes = trazador.trazar(np.array([[3000.0, 3000.0, angulo, 2000.0]]))
        assert planes.costos[0] == pytest.approx(2000.0 * COSTO_SELVA)
        assert planes.impactos[0] == pytest.approx(2000.0 * 0.6 * 10.0 / 10_000.0)


def test_los_tramos_fuera_del_mapa_no_se_cobran():
    planes = trazador_uniforme().trazar(np.array([[500.0, 500.0, 180.0, 2000.0]]))
    assert planes.costos[0] == pytest.approx(500.0 * COSTO_SELVA)
    assert planes.mascaras[0].sum() == 5


def test_no_se_traza_sobre_agua_ni_poblados(mapa):
    trazador = TrazadorBrechas(mapa, ConfigBrechas())
    rng = np.random.default_rng(0)
    inferior, superior = trazador.limites()
    planes = trazador.trazar(rng.uniform(inferior, superior, size=(200, trazador.n_genes)))
    assert not planes.mascaras[:, ~mapa.construible].any()


def test_una_brecha_diagonal_no_deja_pasar_el_fuego():
    trazador = trazador_uniforme()
    # Diagonal de esquina a esquina que separa el noreste del suroeste.
    planes = trazador.trazar(np.array([[0.0, 0.0, 45.0, 9000.0]]))
    sim = SimuladorFuego(mapa_uniforme(), ConfigFuego(duracion_max=500))
    escenarios = escenarios_centro(10)
    escenarios.filas[:] = CENTRO + 10
    escenarios.columnas[:] = CENTRO - 10
    quemado = sim.tiempos_ignicion(planes.mascaras[0], escenarios) >= 0
    f, c = np.indices((LADO, LADO))
    assert quemado[:, f > c].any()
    assert not quemado[:, c > f].any()


def test_reparar_respeta_el_presupuesto_y_no_toca_lo_factible(mapa):
    trazador = TrazadorBrechas(mapa, ConfigBrechas())
    rng = np.random.default_rng(1)
    inferior, superior = trazador.limites()
    poblacion = rng.uniform(inferior, superior, size=(300, trazador.n_genes))
    costos_antes = trazador.trazar(poblacion).costos
    reparada = trazador.reparar(poblacion)
    costos = trazador.trazar(reparada).costos
    presupuesto = trazador.config.presupuesto

    assert (costos_antes > presupuesto).any()
    assert (costos <= presupuesto + 1e-6).all()
    ya_cumplian = costos_antes <= presupuesto
    assert np.array_equal(reparada[ya_cumplian], poblacion[ya_cumplian])
    # Solo cambian las longitudes, y en la misma proporción dentro de cada plan.
    antes, despues = trazador.brechas(poblacion), trazador.brechas(reparada)
    assert np.array_equal(antes[:, :, :3], despues[:, :, :3])
    assert (despues[:, :, 3] >= trazador.config.longitud_min_m).all()


def test_ajustar_al_presupuesto_lo_aprovecha(mapa):
    trazador = TrazadorBrechas(mapa, ConfigBrechas())
    rng = np.random.default_rng(2)
    inferior, superior = trazador.limites()
    poblacion = rng.uniform(inferior, superior, size=(100, trazador.n_genes))
    costos = trazador.trazar(trazador.ajustar_al_presupuesto(poblacion)).costos
    assert (costos <= trazador.config.presupuesto + 1e-6).all()
    assert np.median(costos) > 0.95 * trazador.config.presupuesto
