"""Entradas del sistema: parámetros que el usuario fija en cada ejecución.

La base de conocimiento (catálogos, mapa, modelo de fuego) vive en ``kanan.dominio``
y ``kanan.simulacion``; aquí solo están los valores que cambian entre corridas.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ConfigMapa:
    tipo: str = "sintetico"
    filas: int = 80
    columnas: int = 80
    tam_celda_m: float = 100.0
    semilla: int = 7


@dataclass(frozen=True)
class ConfigBrechas:
    k: int = 8
    longitud_min_m: float = 300.0
    longitud_max_m: float = 2500.0
    presupuesto: float = 350_000.0
    """Presupuesto total en pesos (costo de desmonte acumulado de todas las brechas)."""
    ancho_m: float = 10.0
    """Ancho de la franja desmontada; solo afecta el impacto ecológico."""


@dataclass(frozen=True)
class ConfigFuego:
    """Parámetros del autómata de Alexandridis et al. (2008)."""

    p_h: float = 0.58
    c1: float = 0.045
    c2: float = 0.131
    a_pendiente: float = 0.078
    duracion_max: int = 45
    """Pasos máximos de simulación (representa el tiempo hasta que llega el combate)."""


@dataclass(frozen=True)
class ConfigEscenarios:
    n_entrenamiento: int = 30
    n_prueba: int = 100
    viento_vel_min: float = 2.0
    viento_vel_max: float = 10.0
    """Velocidad del viento en m/s."""
    viento_dir_min: float = 120.0
    viento_dir_max: float = 240.0
    """Azimut hacia donde sopla el viento (grados, horario desde el norte)."""
    semilla: int = 2026


@dataclass(frozen=True)
class ConfigAG:
    poblacion: int = 100
    generaciones: int = 200
    p_cruza: float = 0.9
    p_intercambio_brecha: float = 0.5
    p_mutacion: float | None = None
    """Probabilidad de mutar cada gen; ``None`` usa 1 / número de genes."""
    eta_cruza: float = 15.0
    eta_mutacion: float = 20.0
    semilla: int = 42


@dataclass(frozen=True)
class ConfigValidacion:
    n_planes_azar: int = 30
    busqueda_aleatoria: bool = True


@dataclass(frozen=True)
class Config:
    mapa: ConfigMapa = field(default_factory=ConfigMapa)
    brechas: ConfigBrechas = field(default_factory=ConfigBrechas)
    fuego: ConfigFuego = field(default_factory=ConfigFuego)
    escenarios: ConfigEscenarios = field(default_factory=ConfigEscenarios)
    ag: ConfigAG = field(default_factory=ConfigAG)
    validacion: ConfigValidacion = field(default_factory=ConfigValidacion)
    pesos_zonas: dict[str, float] = field(default_factory=dict)
    """Pesos por zona de valor que sustituyen a los del catálogo (por nombre)."""

    def validar(self) -> None:
        b, a, e = self.brechas, self.ag, self.escenarios
        if b.k < 1:
            raise ValueError("brechas.k debe ser al menos 1")
        if not 0 < b.longitud_min_m <= b.longitud_max_m:
            raise ValueError("se requiere 0 < longitud_min_m <= longitud_max_m")
        if b.presupuesto <= 0:
            raise ValueError("brechas.presupuesto debe ser positivo")
        if a.poblacion < 4 or a.poblacion % 2:
            raise ValueError("ag.poblacion debe ser par y al menos 4")
        if a.generaciones < 1:
            raise ValueError("ag.generaciones debe ser al menos 1")
        if e.n_entrenamiento < 1 or e.n_prueba < 1:
            raise ValueError("se requiere al menos un escenario de entrenamiento y de prueba")
        if e.viento_vel_min > e.viento_vel_max:
            raise ValueError("viento_vel_min no puede exceder viento_vel_max")
        if self.mapa.tipo != "sintetico":
            raise ValueError("el MVP solo incluye el mapa 'sintetico'")

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _construir(cls: type, datos: dict[str, Any]) -> Any:
    validos = {f.name: f for f in fields(cls)}
    desconocidos = set(datos) - set(validos)
    if desconocidos:
        raise ValueError(f"claves desconocidas en {cls.__name__}: {sorted(desconocidos)}")
    kwargs = {}
    for nombre, valor in datos.items():
        tipo = validos[nombre].default_factory if nombre != "pesos_zonas" else None
        if isinstance(tipo, type) and is_dataclass(tipo):
            kwargs[nombre] = _construir(tipo, valor or {})
        else:
            kwargs[nombre] = valor
    return cls(**kwargs)


def cargar_config(ruta: str | Path | None = None) -> Config:
    """Lee un YAML; las claves ausentes conservan su valor por omisión."""
    datos: dict[str, Any] = {}
    if ruta is not None:
        datos = yaml.safe_load(Path(ruta).read_text(encoding="utf-8")) or {}
    config = _construir(Config, datos)
    config.validar()
    return config
