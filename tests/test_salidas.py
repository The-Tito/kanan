import numpy as np

from kanan.config import ConfigBrechas
from kanan.dominio.plan import TrazadorBrechas
from kanan.optimizacion.aptitud import Medicion
from kanan.optimizacion.nsga2 import Historial
from kanan.salidas import graficas, mapas, tablas
from kanan.salidas.reporte import DatosReporte, PlanReporte, generar_reporte
from kanan.validacion.comparacion import ResultadoMetodo


def metodo(nombre: str, area: float, kanan: bool = False) -> ResultadoMetodo:
    rng = np.random.default_rng(int(area))
    areas = rng.normal(area, 50, size=(2, 30)).clip(0)
    return ResultadoMetodo(
        nombre, Medicion(areas, areas / 2, np.full(2, 1000.0), np.full(2, 1.5)), kanan
    )


def test_figuras_de_mapa_y_animacion(mapa, tmp_path):
    trazador = TrazadorBrechas(mapa, ConfigBrechas())
    plan = trazador.poblacion_aleatoria(1, np.random.default_rng(0))
    brechas = trazador.brechas(plan)[0]
    t_ign = np.full(mapa.forma, -1, dtype=np.int32)
    t_ign[10:14, 10:14] = [[0, 1, 2, 3]] * 4
    mapas.figura_mapa(mapa, tmp_path / "mapa.png", brechas)
    mapas.figura_riesgo(mapa, tmp_path / "riesgo.png")
    prob = (t_ign >= 0).astype(float)
    mapas.figura_probabilidad(mapa, prob, prob / 2, brechas, "t", tmp_path / "prob.png")
    mapas.animar_incendio(mapa, t_ign, t_ign, brechas, "t", tmp_path / "fuego.gif")
    for nombre in ("mapa.png", "riesgo.png", "prob.png", "fuego.gif"):
        assert (tmp_path / nombre).stat().st_size > 1000


def test_graficas(tmp_path):
    rng = np.random.default_rng(0)
    historial = Historial(
        rng.random((6, 12, 4)), np.zeros((6, 12)), rng.integers(0, 2, size=(6, 12))
    )
    resultados = [metodo("Sin brechas", 900), metodo("Kanan", 500, kanan=True)]
    graficas.figura_evolucion(historial, tmp_path / "evolucion.png")
    graficas.figura_hipervolumen(np.linspace(0.1, 0.5, 6), tmp_path / "hv.png")
    graficas.figura_pareto(rng.random((15, 4)), {"A": (0, "#2a78d6")}, tmp_path / "pareto.png")
    graficas.figura_comparacion(resultados, tmp_path / "comparacion.png")
    graficas.figura_cajas(resultados, tmp_path / "cajas.png")
    assert len(list(tmp_path.glob("*.png"))) == 5


def test_tablas_y_reporte(tmp_path):
    base, kanan = metodo("Sin brechas", 900), metodo("Kanan <b>", 500, kanan=True)
    filas = tablas.filas_comparacion([base, kanan], base)
    assert filas[0]["reduccion_vs_sin_brechas"] == 0
    assert 0.3 < filas[1]["reduccion_vs_sin_brechas"] < 0.6
    tablas.escribir_csv(filas, tmp_path / "c.csv")
    assert (tmp_path / "c.csv").read_text(encoding="utf-8").count("\n") == 3

    genes = tablas.filas_brechas("P", np.array([[10.0, 20.0, 45.0, 500.0]]))
    assert genes[0]["brecha"] == 1 and genes[0]["longitud_m"] == 500.0
    frente = tablas.filas_frente(np.zeros((2, 8)), np.ones((2, 4)))
    assert len(frente) == 2 and "gen_7" in frente[0] and frente[0]["area_quemada"] == 1.0

    plan = PlanReporte("P", "#2a78d6", "d", (1, 2, 3, 4), (5, 6, 7, 8), genes, "a.png", "b.png",
                       "c.gif")  # fmt: skip
    figuras = {k: f"{k}.png" for k in ("mapa", "riesgo", "evolucion", "hipervolumen", "pareto",
                                       "comparacion", "cajas")}  # fmt: skip
    datos = DatosReporte([("35%", "menos")], "Conclusión.", [("K", "8")], figuras, [plan], filas,
                         {"Kanan <b>"}, ["nota"])  # fmt: skip
    generar_reporte(datos, tmp_path / "reporte.html")
    html = (tmp_path / "reporte.html").read_text(encoding="utf-8")
    assert "Kanan &lt;b&gt;" in html and "Kanan <b>" not in html
    assert 'class="kanan"' in html and "pareto.png" in html and "c.gif" in html
    assert "<iframe" in html and "output=embed" in html and "La Sepultura" in html
