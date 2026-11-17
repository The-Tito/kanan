from dataclasses import replace

import numpy as np

from kanan.aplicacion.corrida import AL_AZAR, SIN_BRECHAS, ejecutar, guardar_salidas
from kanan.cli import main
from kanan.config import Config, ConfigAG, ConfigEscenarios, ConfigValidacion

CHICA = replace(
    Config(),
    ag=ConfigAG(poblacion=12, generaciones=4),
    escenarios=ConfigEscenarios(n_entrenamiento=12, n_prueba=15),
    validacion=ConfigValidacion(n_planes_azar=3),
)


def test_corrida_completa_escribe_todas_las_salidas(tmp_path):
    mensajes = []
    resultado = ejecutar(CHICA, mensajes.append)
    assert len(resultado.comparacion) == 7
    assert resultado.metodo(SIN_BRECHAS).area_media >= resultado.metodo(AL_AZAR).area_media
    assert len(resultado.hipervolumen) == 5
    assert set(resultado.elegidos.values()) <= set(range(len(resultado.frente_planes)))
    # Entrenamiento y prueba son sorteos distintos.
    sistema = resultado.sistema
    assert not np.array_equal(sistema.entrenamiento.semillas[:12], sistema.prueba.semillas[:12])

    reporte = guardar_salidas(resultado, tmp_path, mensajes.append)
    esperados = [
        "reporte.html", "resumen.json", "config_usada.yaml", "historial.npz", "comparacion.csv",
        "planes_brechas.csv", "frente_pareto.csv", "mapa.png", "riesgo.png", "evolucion.png",
        "hipervolumen.png", "pareto.png", "comparacion.png", "cajas.png",
    ]  # fmt: skip
    for clave in resultado.elegidos:
        esperados += [f"plan_{clave}_mapa.png", f"plan_{clave}_probabilidad.png",
                      f"plan_{clave}_incendio.gif"]  # fmt: skip
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(esperados)
    assert "Los tres mejores planes" in reporte.read_text(encoding="utf-8")
    assert mensajes


def test_la_corrida_es_reproducible():
    a, b = ejecutar(CHICA, lambda _: None), ejecutar(CHICA, lambda _: None)
    assert np.array_equal(a.frente_objetivos, b.frente_objetivos)
    assert a.metodo(AL_AZAR).area_media == b.metodo(AL_AZAR).area_media


def test_cli_mapa_y_errores(tmp_path, capsys):
    assert main(["mapa", "--salida", str(tmp_path)]) == 0
    assert (tmp_path / "mapa.png").exists()
    assert main(["ejecutar", "--config", str(tmp_path / "no_existe.yaml")]) == 2
    assert "Error" in capsys.readouterr().err
