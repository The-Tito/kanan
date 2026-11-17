"""Comparación de métodos en escenarios de prueba que el AG nunca vio."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from kanan.optimizacion.aptitud import Evaluador, Medicion
from kanan.simulacion.escenarios import Escenarios


@dataclass(frozen=True)
class ResultadoMetodo:
    """Desempeño de un método (uno o varios planes) sobre los escenarios de prueba."""

    nombre: str
    medicion: Medicion
    es_kanan: bool = False

    @property
    def area_por_escenario(self) -> np.ndarray:
        """Hectáreas quemadas en cada escenario, promediando los planes del método."""
        return self.medicion.area_ha.mean(axis=0)

    @property
    def area_media(self) -> float:
        return float(self.area_por_escenario.mean())

    @property
    def area_desviacion(self) -> float:
        """Dispersión entre escenarios."""
        return float(self.area_por_escenario.std())

    @property
    def area_mediana(self) -> float:
        return float(np.median(self.area_por_escenario))

    @property
    def area_p90(self) -> float:
        return float(np.percentile(self.area_por_escenario, 90))

    @property
    def valor_medio(self) -> float:
        return float(self.medicion.valor.mean())

    @property
    def costo_medio(self) -> float:
        return float(self.medicion.costos.mean())

    @property
    def impacto_medio(self) -> float:
        return float(self.medicion.impactos.mean())

    @property
    def n_planes(self) -> int:
        return len(self.medicion.costos)

    def reduccion_frente_a(self, base: ResultadoMetodo) -> float:
        """Fracción de área quemada que evita respecto a ``base``."""
        return 1.0 - self.area_media / base.area_media


def comparar(
    evaluador: Evaluador,
    escenarios: Escenarios,
    metodos: dict[str, np.ndarray | None],
    kanan: tuple[str, ...] = (),
) -> list[ResultadoMetodo]:
    """Mide cada método en los mismos escenarios. ``None`` significa "sin brechas"."""
    resultados = []
    for nombre, planes in metodos.items():
        if planes is None:
            medicion = evaluador.medir_sin_brechas(escenarios)
        else:
            medicion = evaluador.medir(np.atleast_2d(planes), escenarios)
        resultados.append(ResultadoMetodo(nombre, medicion, nombre in kanan))
    return resultados
