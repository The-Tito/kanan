"""Catálogos fijos de la base de conocimiento.

Los valores de ``p_veg`` y ``p_den`` parten de Alexandridis et al. (2008): agricultura -0.3,
matorral 0.0, pino 0.4; densidad rala -0.4, normal 0.0, densa 0.3. Los demás tipos, los
costos y los valores ecológicos son supuestos razonados para el mapa sintético, no
mediciones de campo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TipoVegetacion:
    id: int
    nombre: str
    combustible: bool
    p_veg: float
    valor_ecologico: float
    """Valor relativo (0 a 1) de una hectárea de esta vegetación."""
    costo_desmonte_m: float
    """Pesos por metro lineal de brecha en terreno plano y densidad normal."""
    color: str


AGUA, PASTIZAL, AGRICULTURA, SELVA_BAJA, PINO_ENCINO, MESOFILO, POBLADO = range(7)

VEGETACION: tuple[TipoVegetacion, ...] = (
    TipoVegetacion(AGUA, "Agua", False, 0.0, 0.0, 0.0, "#4a90c2"),
    TipoVegetacion(PASTIZAL, "Pastizal", True, -0.1, 0.15, 14.0, "#d9d38c"),
    TipoVegetacion(AGRICULTURA, "Agricultura", True, -0.3, 0.05, 10.0, "#e8c36a"),
    TipoVegetacion(SELVA_BAJA, "Selva baja caducifolia", True, 0.0, 0.6, 30.0, "#9bbf6b"),
    TipoVegetacion(PINO_ENCINO, "Bosque de pino-encino", True, 0.4, 0.8, 42.0, "#4f8a4b"),
    TipoVegetacion(MESOFILO, "Bosque mesófilo", True, 0.1, 1.0, 55.0, "#1f5c46"),
    TipoVegetacion(POBLADO, "Poblado", True, -0.4, 0.0, 0.0, "#8c8c8c"),
)


@dataclass(frozen=True)
class NivelDensidad:
    id: int
    nombre: str
    p_den: float
    factor_costo: float
    factor_ecologico: float


RALA, NORMAL, DENSA = range(3)

DENSIDAD: tuple[NivelDensidad, ...] = (
    NivelDensidad(RALA, "Rala", -0.4, 0.8, 0.7),
    NivelDensidad(NORMAL, "Normal", 0.0, 1.0, 1.0),
    NivelDensidad(DENSA, "Densa", 0.3, 1.3, 1.2),
)


@dataclass(frozen=True)
class ZonaValor:
    id: int
    nombre: str
    peso: float
    """Importancia relativa de una hectárea quemada de esta zona."""
    color: str


SIN_ZONA, Z_POBLADO, Z_INFRAESTRUCTURA, Z_NUCLEO, Z_CULTIVO = range(5)

ZONAS_VALOR: tuple[ZonaValor, ...] = (
    ZonaValor(SIN_ZONA, "sin_zona", 0.0, "#00000000"),
    ZonaValor(Z_POBLADO, "poblado", 10.0, "#d62728"),
    ZonaValor(Z_INFRAESTRUCTURA, "infraestructura", 6.0, "#9467bd"),
    ZonaValor(Z_NUCLEO, "zona_nucleo", 4.0, "#17becf"),
    ZonaValor(Z_CULTIVO, "cultivo", 2.0, "#ff7f0e"),
)

PENDIENTE_REFERENCIA_GRADOS = 30.0
"""Pendiente a la que abrir una brecha cuesta el doble que en terreno plano."""


def tabla_vegetacion(campo: str) -> np.ndarray:
    """Columna del catálogo de vegetación como arreglo indexable por id."""
    return np.array([getattr(v, campo) for v in VEGETACION])


def tabla_densidad(campo: str) -> np.ndarray:
    return np.array([getattr(d, campo) for d in DENSIDAD])


def pesos_zonas(sustitutos: dict[str, float] | None = None) -> np.ndarray:
    """Pesos por id de zona; ``sustitutos`` reemplaza por nombre los del catálogo."""
    sustitutos = sustitutos or {}
    nombres = {z.nombre for z in ZONAS_VALOR}
    desconocidos = set(sustitutos) - nombres
    if desconocidos:
        raise ValueError(f"zonas de valor desconocidas: {sorted(desconocidos)}")
    return np.array([float(sustitutos.get(z.nombre, z.peso)) for z in ZONAS_VALOR])
