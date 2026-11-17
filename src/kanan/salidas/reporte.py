"""Reporte HTML estático que reúne todas las salidas de una corrida."""

from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path

from kanan.optimizacion.aptitud import ETIQUETAS, OBJETIVOS
from kanan.salidas.tablas import Fila

CSS = """
:root { --tinta:#0b0b0b; --secundaria:#52514e; --tenue:#898781; --linea:#e1e0d9;
        --fondo:#f9f9f7; --superficie:#fcfcfb; }
* { box-sizing: border-box; }
body { margin:0; background:var(--fondo); color:var(--tinta);
       font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width:1080px; margin:0 auto; padding:32px 16px 64px; }
h1 { font-size:30px; margin:0 0 4px; }
h2 { font-size:20px; margin:44px 0 12px; padding-top:20px; border-top:1px solid var(--linea); }
h3 { font-size:16px; margin:28px 0 8px; display:flex; align-items:center; gap:8px; }
p { margin:8px 0; max-width:75ch; }
.sub { color:var(--secundaria); }
.aviso { background:var(--superficie); border:1px solid var(--linea); border-left:4px solid #eda100;
         padding:10px 14px; border-radius:6px; margin:16px 0; }
.cifras { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px;
          margin:20px 0; }
.cifra { background:var(--superficie); border:1px solid var(--linea); border-radius:8px;
         padding:12px 14px; }
.cifra b { display:block; font-size:24px; }
.cifra span { color:var(--secundaria); font-size:13px; }
figure { margin:16px 0; }
img { max-width:100%; height:auto; border:1px solid var(--linea); border-radius:8px;
      background:var(--superficie); }
.tabla { overflow-x:auto; }
table { border-collapse:collapse; width:100%; font-size:13.5px; background:var(--superficie); }
th, td { padding:7px 10px; border-bottom:1px solid var(--linea); text-align:right;
         white-space:nowrap; }
th:first-child, td:first-child { text-align:left; }
th { color:var(--secundaria); font-weight:600; }
tr.kanan td:first-child { font-weight:600; }
.punto { width:12px; height:12px; border-radius:50%; display:inline-block; }
.dos { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; }
footer { margin-top:48px; color:var(--tenue); font-size:13px; }
"""


@dataclass(frozen=True)
class PlanReporte:
    nombre: str
    color: str
    descripcion: str
    entrenamiento: tuple[float, ...]
    prueba: tuple[float, ...]
    brechas: list[Fila]
    figura_mapa: str
    figura_probabilidad: str
    animacion: str


@dataclass(frozen=True)
class DatosReporte:
    cifras: list[tuple[str, str]]
    """Pares (valor, descripción) que encabezan el reporte."""
    conclusion: str
    parametros: list[tuple[str, str]]
    figuras: dict[str, str]
    """Rutas relativas: mapa, riesgo, evolucion, hipervolumen, pareto, comparacion, cajas."""
    planes: list[PlanReporte]
    comparacion: list[Fila]
    metodos_kanan: set[str] = field(default_factory=set)
    notas: list[str] = field(default_factory=list)


def _numero(valor: object) -> str:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return escape(str(valor))
    if isinstance(valor, int) or abs(valor) >= 1000:
        return f"{valor:,.0f}"
    return f"{valor:,.2f}" if abs(valor) < 10 else f"{valor:,.1f}"


def _tabla(encabezados: list[str], filas: list[list[object]], resaltar: set[int] = frozenset()):
    cabeza = "".join(f"<th>{escape(e)}</th>" for e in encabezados)
    cuerpo = ""
    for i, fila in enumerate(filas):
        clase = ' class="kanan"' if i in resaltar else ""
        cuerpo += f"<tr{clase}>" + "".join(f"<td>{_numero(v)}</td>" for v in fila) + "</tr>"
    return f'<div class="tabla"><table><tr>{cabeza}</tr>{cuerpo}</table></div>'


def _figura(ruta: str, descripcion: str) -> str:
    return f'<figure><img src="{escape(ruta)}" alt="{escape(descripcion)}" loading="lazy"></figure>'


def _seccion_plan(plan: PlanReporte) -> str:
    objetivos = _tabla(
        ["Escenarios"] + [ETIQUETAS[o] for o in OBJETIVOS],
        [["Entrenamiento", *plan.entrenamiento], ["Prueba (no vistos)", *plan.prueba]],
    )
    genes = _tabla(
        ["Brecha", "x inicio (m)", "y inicio (m)", "Ángulo (°)", "Longitud (m)"],
        [[f["brecha"], f["x_inicio_m"], f["y_inicio_m"], f["angulo_grados"], f["longitud_m"]]
         for f in plan.brechas],  # fmt: skip
    )
    return f"""
<h3><span class="punto" style="background:{plan.color}"></span>{escape(plan.nombre)}</h3>
<p class="sub">{escape(plan.descripcion)}</p>
{objetivos}
<div class="dos">
  {_figura(plan.figura_mapa, f"Mapa con las brechas del plan {plan.nombre}")}
  {_figura(plan.animacion, f"Animación de un incendio con el plan {plan.nombre}")}
</div>
{_figura(plan.figura_probabilidad, "Probabilidad de quema sin brechas y con el plan")}
<details><summary>Genes de las brechas</summary>{genes}</details>
"""


def generar_reporte(datos: DatosReporte, ruta: Path) -> None:
    cifras = "".join(
        f'<div class="cifra"><b>{escape(valor)}</b><span>{escape(texto)}</span></div>'
        for valor, texto in datos.cifras
    )
    comparacion = _tabla(
        ["Método", "Planes", "Área media (ha)", "Desv. (ha)", "Mediana (ha)", "P90 (ha)",
         "Reducción", "Valor afectado", "Costo (pesos)", "Impacto ecol."],  # fmt: skip
        [
            [f["metodo"], f["planes"], f["area_media_ha"], f["area_desviacion_ha"],
             f["area_mediana_ha"], f["area_p90_ha"], f"{f['reduccion_vs_sin_brechas']:.1%}",
             f["valor_afectado"], f["costo"], f["impacto_ecologico"]]
            for f in datos.comparacion
        ],  # fmt: skip
        {i for i, f in enumerate(datos.comparacion) if f["metodo"] in datos.metodos_kanan},
    )
    parametros = _tabla(["Parámetro", "Valor"], [[p, v] for p, v in datos.parametros])
    notas = "".join(f"<li>{escape(n)}</li>" for n in datos.notas)
    f = datos.figuras
    html = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kanan · Reporte de corrida</title><style>{CSS}</style></head>
<body><main>
<h1>Kanan</h1>
<p class="sub">Optimización de brechas cortafuego con NSGA-II · reporte de corrida</p>
<div class="aviso">Prototipo de apoyo a la decisión sobre un <b>mapa sintético</b> con los
rasgos de La Sepultura. El modelo de fuego es una simplificación: estos resultados no son una
recomendación operativa.</div>
<div class="cifras">{cifras}</div>
<p>{escape(datos.conclusion)}</p>

<h2>Comparación con métodos de referencia</h2>
<p>Todos los métodos usan el mismo presupuesto y se miden en escenarios de prueba que el
algoritmo nunca vio durante la optimización.</p>
{_figura(f["comparacion"], "Área quemada media por método")}
{comparacion}
{_figura(f["cajas"], "Diagrama de caja del área quemada por escenario")}

<h2>Los tres mejores planes</h2>
{"".join(_seccion_plan(p) for p in datos.planes)}

<h2>Evolución del algoritmo</h2>
{_figura(f["evolucion"], "Mejor valor y promedio de cada objetivo por generación")}
{_figura(f["hipervolumen"], "Hipervolumen por generación")}
{_figura(f["pareto"], "Frente de Pareto en pares de ejes")}

<h2>Área de estudio</h2>
<div class="dos">
  {_figura(f["mapa"], "Mapa del área de estudio")}
  {_figura(f["riesgo"], "Mapa de riesgo de ignición")}
</div>

<h2>Parámetros de la corrida</h2>
{parametros}

<h2>Límites y notas</h2>
<ul>{notas}</ul>
<footer>Kanan significa "cuidar, proteger, vigilar" en tseltal.</footer>
</main></body></html>"""
    ruta.write_text(html, encoding="utf-8")
