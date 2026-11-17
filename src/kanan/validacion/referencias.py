"""Métodos de referencia contra los que se compara el AG, todos con el mismo presupuesto."""

from __future__ import annotations

import numpy as np

from kanan.config import ConfigEscenarios
from kanan.dominio.plan import TrazadorBrechas
from kanan.optimizacion.nsga2 import Evaluar, ordenamiento_no_dominado

LOTE_BUSQUEDA = 1000


def planes_al_azar(trazador: TrazadorBrechas, n: int, rng: np.random.Generator) -> np.ndarray:
    """Brechas en posiciones y ángulos al azar, escaladas para gastar todo el presupuesto."""
    inferior, superior = trazador.limites()
    return trazador.ajustar_al_presupuesto(rng.uniform(inferior, superior, size=(n, len(inferior))))


def direccion_media_viento(config: ConfigEscenarios) -> float:
    """Azimut central del rango de viento."""
    amplitud = (config.viento_dir_max - config.viento_dir_min) % 360.0
    return (config.viento_dir_min + amplitud / 2.0) % 360.0


def _segmento(inicio: np.ndarray, direccion: np.ndarray, longitud: float) -> list[float]:
    angulo = np.degrees(np.arctan2(direccion[1], direccion[0])) % 360.0
    return [float(inicio[0]), float(inicio[1]), float(angulo), float(longitud)]


def _cerco(centro: np.ndarray, radio: float, viento: np.ndarray, n: int) -> list[list[float]]:
    """``n`` brechas alrededor de un poblado, empezando por el lado de donde viene el fuego.

    Con 1 es una barrera perpendicular al viento; con 2, una cuña; con 3, una U abierta a
    sotavento; con 4, el cuadro completo. Las adicionales repiten la barrera más lejos.
    """
    lateral = np.array([-viento[1], viento[0]])
    lado = 2.0 * radio
    esquina_a = centro - radio * viento - radio * lateral
    esquina_b = centro - radio * viento + radio * lateral
    if n == 2:
        punta = centro - 1.4 * radio * viento
        return [
            _segmento(punta, (viento + lateral) / np.sqrt(2.0), lado),
            _segmento(punta, (viento - lateral) / np.sqrt(2.0), lado),
        ]
    brechas = [
        _segmento(esquina_a, lateral, lado),
        _segmento(esquina_a, viento, lado),
        _segmento(esquina_b, viento, lado),
        _segmento(esquina_a + lado * viento, lateral, lado),
    ]
    for extra in range(max(0, n - 4)):
        lejos = esquina_a - (extra + 1) * radio * viento
        brechas.append(_segmento(lejos, lateral, lado))
    return brechas[:n]


def plan_alrededor_de_poblados(
    trazador: TrazadorBrechas, escenarios: ConfigEscenarios
) -> np.ndarray:
    """Reparte las K brechas entre los poblados y las aleja tanto como permita el presupuesto."""
    mapa, config = trazador.mapa, trazador.config
    if not mapa.poblados:
        raise ValueError("el mapa no tiene poblados")
    azimut = np.radians(direccion_media_viento(escenarios))
    viento = np.array([np.sin(azimut), -np.cos(azimut)])  # x al este, y al sur
    reparto = [
        config.k // len(mapa.poblados) + (i < config.k % len(mapa.poblados))
        for i in range(len(mapa.poblados))
    ]

    def construir(radio: float) -> np.ndarray:
        genes: list[list[float]] = []
        for (fila, col, _), n in zip(mapa.poblados, reparto, strict=True):
            centro = (np.array([col, fila]) + 0.5) * mapa.tam_celda_m
            genes += _cerco(centro, radio, viento, n)
        return np.array(genes).reshape(1, -1)

    radios = np.arange(config.longitud_max_m / 2.0, config.longitud_min_m / 2.0, -25.0)
    for radio in radios:
        plan = construir(radio)
        if trazador.trazar(plan).costos[0] <= config.presupuesto:
            return plan
    return trazador.reparar(construir(config.longitud_min_m / 2.0))


def busqueda_aleatoria(
    trazador: TrazadorBrechas, evaluar: Evaluar, n_evaluaciones: int, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """Evalúa planes al azar y conserva los no dominados.

    Gasta el mismo número de evaluaciones que el AG, para separar el mérito del algoritmo
    del simple esfuerzo de cómputo. Devuelve los planes y sus objetivos.
    """
    planes = np.empty((0, trazador.n_genes))
    objetivos = np.empty((0, 4))
    restantes = n_evaluaciones
    while restantes > 0:
        lote = trazador.poblacion_aleatoria(min(LOTE_BUSQUEDA, restantes), rng)
        obj_lote, violacion = evaluar(lote)
        factible = violacion <= 0
        planes = np.vstack([planes, lote[factible]])
        objetivos = np.vstack([objetivos, obj_lote[factible]])
        no_dominado = ordenamiento_no_dominado(objetivos) == 0
        planes, objetivos = planes[no_dominado], objetivos[no_dominado]
        restantes -= len(lote)
    return planes, objetivos
