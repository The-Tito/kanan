import numpy as np
import pytest

from kanan.config import Config, ConfigEscenarios
from kanan.dominio import catalogos as cat
from kanan.dominio.plan import TrazadorBrechas
from kanan.optimizacion.aptitud import Evaluador
from kanan.optimizacion.nsga2 import ordenamiento_no_dominado
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import generar_escenarios
from kanan.validacion.comparacion import comparar
from kanan.validacion.referencias import (
    busqueda_aleatoria,
    direccion_media_viento,
    plan_alrededor_de_poblados,
    planes_al_azar,
)


@pytest.fixture(scope="module")
def sistema(mapa):
    config = Config()
    trazador = TrazadorBrechas(mapa, config.brechas)
    evaluador = Evaluador(mapa, SimuladorFuego(mapa, config.fuego), trazador, cat.pesos_zonas())
    escenarios = generar_escenarios(mapa, config.escenarios, 60, np.random.default_rng(0))
    return config, trazador, evaluador, escenarios


def test_direccion_media_del_viento():
    assert direccion_media_viento(ConfigEscenarios()) == 180.0
    cruza_norte = ConfigEscenarios(viento_dir_min=300.0, viento_dir_max=60.0)
    assert direccion_media_viento(cruza_norte) == 0.0


def test_los_planes_al_azar_gastan_el_presupuesto(sistema):
    config, trazador, _, _ = sistema
    costos = trazador.trazar(planes_al_azar(trazador, 50, np.random.default_rng(1))).costos
    assert (costos <= config.brechas.presupuesto * 1.000001).all()
    assert np.median(costos) > 0.95 * config.brechas.presupuesto


def test_el_plan_de_poblados_los_rodea_dentro_del_presupuesto(sistema, mapa):
    config, trazador, _, _ = sistema
    plan = plan_alrededor_de_poblados(trazador, config.escenarios)
    trazado = trazador.trazar(plan)
    assert plan.shape == (1, trazador.n_genes)
    assert trazado.costos[0] <= config.brechas.presupuesto
    assert trazado.costos[0] > 0.6 * config.brechas.presupuesto
    filas, cols = np.nonzero(trazado.mascaras[0])
    for fila, col, _ in mapa.poblados:
        distancia = np.hypot(filas - fila, cols - col).min() * mapa.tam_celda_m
        assert distancia <= config.brechas.longitud_max_m


def test_la_busqueda_aleatoria_devuelve_un_frente(sistema):
    _, trazador, evaluador, escenarios = sistema
    planes, objetivos = busqueda_aleatoria(
        trazador, evaluador.aptitud(escenarios), 2500, np.random.default_rng(2)
    )
    assert len(planes) == len(objetivos) > 1
    assert (ordenamiento_no_dominado(objetivos) == 0).all()


def test_comparar_mide_todos_los_metodos_en_los_mismos_escenarios(sistema):
    config, trazador, evaluador, escenarios = sistema
    metodos = {
        "Sin brechas": None,
        "Al azar": planes_al_azar(trazador, 10, np.random.default_rng(3)),
        "Poblados": plan_alrededor_de_poblados(trazador, config.escenarios),
    }
    sin, azar, poblados = comparar(evaluador, escenarios, metodos, kanan=("Poblados",))
    assert sin.n_planes == 1 and azar.n_planes == 10
    assert sin.area_por_escenario.shape == azar.area_por_escenario.shape == (60,)
    assert sin.costo_medio == 0 and azar.costo_medio > 0
    assert azar.area_media <= sin.area_media
    assert 0 <= poblados.reduccion_frente_a(sin) < 1
    assert poblados.valor_medio <= sin.valor_medio
    assert poblados.es_kanan and not sin.es_kanan
