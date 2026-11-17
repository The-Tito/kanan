import numpy as np

from kanan.config import ConfigMapa
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa_sintetico import generar_mapa_sintetico


def test_es_reproducible_con_la_misma_semilla(mapa):
    otro = generar_mapa_sintetico(ConfigMapa())
    assert np.array_equal(mapa.vegetacion, otro.vegetacion)
    assert np.array_equal(mapa.elevacion, otro.elevacion)


def test_contiene_los_rasgos_del_area(mapa):
    assert mapa.forma == (80, 80)
    assert len(mapa.poblados) == 3
    for zona in (cat.Z_POBLADO, cat.Z_INFRAESTRUCTURA, cat.Z_NUCLEO, cat.Z_CULTIVO):
        assert np.any(mapa.zona_valor == zona)
    assert np.any(mapa.vegetacion == cat.AGUA)
    assert mapa.caminos.any()


def test_restricciones_de_brechas_e_ignicion(mapa):
    assert not mapa.construible[mapa.vegetacion == cat.AGUA].any()
    assert not mapa.construible[mapa.vegetacion == cat.POBLADO].any()
    assert np.isclose(mapa.prob_ignicion.sum(), 1.0)
    assert mapa.prob_ignicion[mapa.vegetacion == cat.AGUA].sum() == 0


def test_la_ignicion_es_mas_probable_cerca_de_caminos(mapa):
    assert mapa.prob_ignicion[mapa.caminos].mean() > 2 * mapa.prob_ignicion.mean()


def test_pendientes_moderadas(mapa):
    assert np.percentile(mapa.pendiente_grados, 95) < 35
