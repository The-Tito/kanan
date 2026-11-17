"""El mapa del área de estudio: capas por celda, independientes de su origen.

Convención de la cuadrícula: la fila 0 es el norte y la columna 0 el oeste. En metros,
``x`` crece hacia el este y ``y`` hacia el sur.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from kanan.dominio import catalogos as cat


@dataclass(frozen=True)
class Mapa:
    vegetacion: np.ndarray
    """Id de ``catalogos.VEGETACION`` por celda."""
    densidad: np.ndarray
    """Id de ``catalogos.DENSIDAD`` por celda."""
    elevacion: np.ndarray
    """Metros sobre el nivel del mar."""
    zona_valor: np.ndarray
    """Id de ``catalogos.ZONAS_VALOR`` por celda."""
    caminos: np.ndarray
    """Máscara de celdas por las que pasa un camino."""
    prob_ignicion: np.ndarray
    """Probabilidad de que un incendio inicie en cada celda; suma 1."""
    tam_celda_m: float
    poblados: tuple[tuple[int, int, int], ...] = ()
    """Centro (fila, columna) y radio en celdas de cada poblado."""

    def __post_init__(self) -> None:
        forma = self.vegetacion.shape
        for nombre in ("densidad", "elevacion", "zona_valor", "caminos", "prob_ignicion"):
            if getattr(self, nombre).shape != forma:
                raise ValueError(f"la capa '{nombre}' no coincide con la forma {forma}")
        if not np.isclose(self.prob_ignicion.sum(), 1.0):
            raise ValueError("prob_ignicion debe sumar 1")
        if np.any(self.prob_ignicion[~self.combustible] > 0):
            raise ValueError("no puede iniciar un incendio en una celda sin combustible")

    @property
    def forma(self) -> tuple[int, int]:
        return self.vegetacion.shape

    @property
    def ancho_m(self) -> float:
        return self.forma[1] * self.tam_celda_m

    @property
    def alto_m(self) -> float:
        return self.forma[0] * self.tam_celda_m

    @property
    def area_celda_ha(self) -> float:
        return self.tam_celda_m**2 / 10_000.0

    @property
    def combustible(self) -> np.ndarray:
        return cat.tabla_vegetacion("combustible")[self.vegetacion]

    @property
    def construible(self) -> np.ndarray:
        """Celdas donde se permite abrir brecha: ni agua ni poblados."""
        return (self.vegetacion != cat.AGUA) & (self.vegetacion != cat.POBLADO)

    @property
    def pendiente_grados(self) -> np.ndarray:
        """Inclinación local del terreno."""
        d_fila, d_col = np.gradient(self.elevacion.astype(float), self.tam_celda_m)
        return np.degrees(np.arctan(np.hypot(d_fila, d_col)))
