import pytest

from kanan.config import Config, cargar_config


def test_valores_por_omision_son_validos():
    config = cargar_config()
    assert config == Config()
    assert config.brechas.k == 8


def test_yaml_parcial_conserva_el_resto(tmp_path):
    ruta = tmp_path / "c.yaml"
    ruta.write_text("ag:\n  poblacion: 20\n", encoding="utf-8")
    config = cargar_config(ruta)
    assert config.ag.poblacion == 20
    assert config.ag.generaciones == Config().ag.generaciones


def test_clave_desconocida_falla(tmp_path):
    ruta = tmp_path / "c.yaml"
    ruta.write_text("ag:\n  poblasion: 20\n", encoding="utf-8")
    with pytest.raises(ValueError, match="poblasion"):
        cargar_config(ruta)


def test_poblacion_impar_falla(tmp_path):
    ruta = tmp_path / "c.yaml"
    ruta.write_text("ag:\n  poblacion: 21\n", encoding="utf-8")
    with pytest.raises(ValueError):
        cargar_config(ruta)
