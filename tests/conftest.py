import pytest

from kanan.config import ConfigMapa
from kanan.dominio.mapa_sintetico import generar_mapa_sintetico


@pytest.fixture(scope="session")
def mapa():
    return generar_mapa_sintetico(ConfigMapa())
