"""Escenarios de incendio: punto de ignición, viento y semilla del azar."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from kanan.config import ConfigEscenarios
from kanan.dominio.mapa import Mapa


@dataclass(frozen=True)
class Escenarios:
    """Conjunto de escenarios guardado por columnas para simularlos en lote."""

    filas: np.ndarray
    columnas: np.ndarray
    viento_vel: np.ndarray
    """Velocidad en m/s."""
    viento_dir: np.ndarray
    """Azimut hacia donde sopla el viento (grados, horario desde el norte)."""
    semillas: np.ndarray

    def __len__(self) -> int:
        return len(self.filas)

    def uno(self, i: int) -> Escenarios:
        """Subconjunto con un solo escenario."""
        s = slice(i, i + 1)
        return Escenarios(
            self.filas[s],
            self.columnas[s],
            self.viento_vel[s],
            self.viento_dir[s],
            self.semillas[s],
        )


def generar_escenarios(
    mapa: Mapa, config: ConfigEscenarios, n: int, rng: np.random.Generator
) -> Escenarios:
    """Sortea ``n`` escenarios: ignición según el mapa de riesgo y viento de temporada."""
    celdas = rng.choice(mapa.prob_ignicion.size, size=n, p=mapa.prob_ignicion.ravel())
    filas, columnas = np.unravel_index(celdas, mapa.forma)
    velocidad = rng.uniform(config.viento_vel_min, config.viento_vel_max, size=n)
    # El rango de direcciones puede cruzar el norte (p. ej. de 300 a 60 grados).
    amplitud = (config.viento_dir_max - config.viento_dir_min) % 360.0
    if amplitud == 0.0 and config.viento_dir_max != config.viento_dir_min:
        amplitud = 360.0
    direccion = (config.viento_dir_min + rng.uniform(0.0, 1.0, size=n) * amplitud) % 360.0
    semillas = rng.integers(1, 2**62, size=n, dtype=np.uint64)
    return Escenarios(
        filas.astype(np.int64), columnas.astype(np.int64), velocidad, direccion, semillas
    )
