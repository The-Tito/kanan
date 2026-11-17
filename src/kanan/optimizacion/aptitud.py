"""Función de aptitud: los cuatro objetivos de un plan de brechas."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from kanan.dominio.mapa import Mapa
from kanan.dominio.plan import TrazadorBrechas
from kanan.simulacion.automata import SimuladorFuego
from kanan.simulacion.escenarios import Escenarios

OBJETIVOS = ("area_quemada", "valor_afectado", "costo_brechas", "impacto_ecologico")
ETIQUETAS = {
    "area_quemada": "Área quemada (ha)",
    "valor_afectado": "Valor afectado (ha ponderadas)",
    "costo_brechas": "Costo de brechas (pesos)",
    "impacto_ecologico": "Impacto ecológico (ha equivalentes)",
}
AREA, VALOR, COSTO, IMPACTO = range(4)


@dataclass(frozen=True)
class Medicion:
    """Resultado de simular varios planes sobre un conjunto de escenarios."""

    area_ha: np.ndarray
    """Hectáreas quemadas: (planes, escenarios)."""
    valor: np.ndarray
    """Hectáreas quemadas de zonas de valor, ponderadas por importancia: (planes, escenarios)."""
    costos: np.ndarray
    impactos: np.ndarray

    def objetivos(self) -> np.ndarray:
        """Matriz (planes, 4) en el orden de ``OBJETIVOS``; todos se minimizan."""
        return np.column_stack(
            [self.area_ha.mean(axis=1), self.valor.mean(axis=1), self.costos, self.impactos]
        )


class Evaluador:
    def __init__(
        self,
        mapa: Mapa,
        simulador: SimuladorFuego,
        trazador: TrazadorBrechas,
        pesos_zonas: np.ndarray,
    ) -> None:
        self.mapa = mapa
        self.simulador = simulador
        self.trazador = trazador
        self.valor_celda = pesos_zonas[mapa.zona_valor] * mapa.area_celda_ha
        """Hectáreas ponderadas que se pierden si arde cada celda."""

    def medir_mascaras(
        self,
        mascaras: np.ndarray,
        costos: np.ndarray,
        impactos: np.ndarray,
        escenarios: Escenarios,
    ) -> Medicion:
        celdas, valor = self.simulador.simular_lote(mascaras, escenarios, self.valor_celda)
        return Medicion(celdas * self.mapa.area_celda_ha, valor, costos, impactos)

    def medir(self, poblacion: np.ndarray, escenarios: Escenarios) -> Medicion:
        planes = self.trazador.trazar(poblacion)
        return self.medir_mascaras(planes.mascaras, planes.costos, planes.impactos, escenarios)

    def medir_sin_brechas(self, escenarios: Escenarios) -> Medicion:
        vacio = np.zeros((1, *self.mapa.forma), dtype=bool)
        return self.medir_mascaras(vacio, np.zeros(1), np.zeros(1), escenarios)

    def violacion(self, costos: np.ndarray) -> np.ndarray:
        """Exceso relativo sobre el presupuesto; 0 si el plan cumple."""
        presupuesto = self.trazador.config.presupuesto
        return np.maximum(0.0, costos - presupuesto * (1 + 1e-9)) / presupuesto

    def aptitud(self, escenarios: Escenarios):
        """Función ``población → (objetivos, violación)`` sobre escenarios fijos."""

        def evaluar(poblacion: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            medicion = self.medir(poblacion, escenarios)
            return medicion.objetivos(), self.violacion(medicion.costos)

        return evaluar
