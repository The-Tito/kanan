"""Pruebas de cordura del simulador (sección "Validación" del brief)."""

import numpy as np
import pytest

from kanan.config import ConfigEscenarios, ConfigFuego
from kanan.dominio import catalogos as cat
from kanan.dominio.mapa import Mapa
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import Escenarios, generar_escenarios

LADO = 61
CENTRO = LADO // 2


def mapa_uniforme(elevacion: np.ndarray | None = None) -> Mapa:
    forma = (LADO, LADO)
    return Mapa(
        vegetacion=np.full(forma, cat.SELVA_BAJA, dtype=np.int8),
        densidad=np.full(forma, cat.NORMAL, dtype=np.int8),
        elevacion=np.zeros(forma, dtype=np.float32) if elevacion is None else elevacion,
        zona_valor=np.zeros(forma, dtype=np.int8),
        caminos=np.zeros(forma, dtype=bool),
        prob_ignicion=np.full(forma, 1.0 / LADO**2),
        tam_celda_m=100.0,
    )


def escenarios_centro(n: int, velocidad: float = 0.0, azimut: float = 0.0) -> Escenarios:
    return Escenarios(
        filas=np.full(n, CENTRO, dtype=np.int64),
        columnas=np.full(n, CENTRO, dtype=np.int64),
        viento_vel=np.full(n, velocidad),
        viento_dir=np.full(n, azimut),
        semillas=np.arange(1, n + 1, dtype=np.uint64),
    )


def alcance(quemado: np.ndarray) -> dict[str, float]:
    """Promedio de celdas quemadas hacia cada punto cardinal desde el centro."""
    return {
        "norte": quemado[:, :CENTRO, CENTRO].sum(axis=1).mean(),
        "sur": quemado[:, CENTRO + 1 :, CENTRO].sum(axis=1).mean(),
        "oeste": quemado[:, CENTRO, :CENTRO].sum(axis=1).mean(),
        "este": quemado[:, CENTRO, CENTRO + 1 :].sum(axis=1).mean(),
    }


def test_con_viento_el_fuego_se_alarga_en_esa_direccion():
    sim = SimuladorFuego(mapa_uniforme(), ConfigFuego(p_h=0.3, duracion_max=20))
    quemado = sim.tiempos_ignicion(None, escenarios_centro(40, velocidad=8.0, azimut=90.0)) >= 0
    a = alcance(quemado)
    assert a["este"] > 2 * a["oeste"]
    assert a["este"] > a["norte"] and a["este"] > a["sur"]


def test_sin_viento_no_hay_direccion_preferente():
    sim = SimuladorFuego(mapa_uniforme(), ConfigFuego(p_h=0.3, duracion_max=20))
    a = alcance(sim.tiempos_ignicion(None, escenarios_centro(200)) >= 0)
    assert max(a.values()) < 1.25 * min(a.values())


def test_en_pendiente_el_fuego_sube_mas_rapido():
    # Ladera que sube hacia el norte con 15 grados de inclinación.
    filas = np.arange(LADO, dtype=np.float32)[:, None]
    elevacion = np.broadcast_to((LADO - filas) * 100.0 * np.tan(np.radians(15)), (LADO, LADO))
    sim = SimuladorFuego(mapa_uniforme(elevacion.copy()), ConfigFuego(p_h=0.3, duracion_max=20))
    a = alcance(sim.tiempos_ignicion(None, escenarios_centro(40)) >= 0)
    assert a["norte"] > 1.5 * a["sur"]


def test_una_brecha_continua_detiene_el_fuego():
    sim = SimuladorFuego(mapa_uniforme(), ConfigFuego(duracion_max=500))
    escenarios = escenarios_centro(20, velocidad=10.0, azimut=90.0)
    libre = sim.tiempos_ignicion(None, escenarios) >= 0
    assert libre[:, :, CENTRO + 10 :].any()

    brecha = np.zeros((LADO, LADO), dtype=bool)
    brecha[:, CENTRO + 8] = True
    contenido = sim.tiempos_ignicion(brecha, escenarios) >= 0
    assert not contenido[:, :, CENTRO + 8 :].any()
    assert contenido[:, :, CENTRO + 7].any(axis=1).all()  # el fuego sí llegó hasta la brecha


def test_el_lote_coincide_con_la_simulacion_individual(mapa):
    sim = SimuladorFuego(mapa, ConfigFuego())
    escenarios = generar_escenarios(mapa, ConfigEscenarios(), 6, np.random.default_rng(0))
    brechas = np.zeros((2, *mapa.forma), dtype=bool)
    brechas[1, 40, :] = True
    valor = np.ones(mapa.forma)
    area, afectado = sim.simular_lote(brechas, escenarios, valor)
    for i in range(2):
        for s in range(len(escenarios)):
            incendio = sim.simular(brechas[i], escenarios, s)
            assert incendio.celdas_quemadas == area[i, s] == afectado[i, s]


def test_es_determinista_y_no_quema_agua(mapa):
    sim = SimuladorFuego(mapa, ConfigFuego())
    escenarios = generar_escenarios(mapa, ConfigEscenarios(), 10, np.random.default_rng(1))
    a = sim.tiempos_ignicion(None, escenarios)
    b = sim.tiempos_ignicion(None, escenarios)
    assert np.array_equal(a, b)
    assert not (a >= 0)[:, mapa.vegetacion == cat.AGUA].any()


def test_una_brecha_nunca_aumenta_lo_quemado(mapa):
    """Mismo azar por arista: quitar combustible solo puede reducir el incendio."""
    sim = SimuladorFuego(mapa, ConfigFuego())
    escenarios = generar_escenarios(mapa, ConfigEscenarios(), 20, np.random.default_rng(2))
    brecha = np.zeros(mapa.forma, dtype=bool)
    brecha[30, 10:70] = True
    libre = sim.tiempos_ignicion(None, escenarios) >= 0
    con_brecha = sim.tiempos_ignicion(brecha, escenarios) >= 0
    # La celda de ignición arde aunque caiga sobre la brecha.
    con_brecha[np.arange(20), escenarios.filas, escenarios.columnas] = False
    assert not (con_brecha & ~libre).any()


@pytest.mark.parametrize("minimo,maximo", [(120.0, 240.0), (300.0, 60.0)])
def test_direccion_del_viento_respeta_el_rango(mapa, minimo, maximo):
    config = ConfigEscenarios(viento_dir_min=minimo, viento_dir_max=maximo)
    e = generar_escenarios(mapa, config, 500, np.random.default_rng(3))
    desplazada = (e.viento_dir - minimo) % 360.0
    assert desplazada.max() <= (maximo - minimo) % 360.0
    assert mapa.combustible[e.filas, e.columnas].all()
