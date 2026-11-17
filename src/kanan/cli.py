"""Línea de comandos de Kanan."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

from kanan import __version__
from kanan.aplicacion.corrida import (
    AL_AZAR,
    SIN_BRECHAS,
    ejecutar,
    guardar_datos,
    guardar_reporte,
)
from kanan.config import cargar_config
from kanan.dominio.mapa_sintetico import construir_mapa
from kanan.salidas import mapas


def _cmd_ejecutar(args: argparse.Namespace) -> int:
    config = cargar_config(args.config)
    if args.semilla is not None:
        config = replace(config, ag=replace(config.ag, semilla=args.semilla))
    resultado = ejecutar(config)
    carpeta = Path(args.salida)
    if args.reporte:
        destino = f"Reporte: {guardar_reporte(resultado, carpeta).resolve()}"
    else:
        destino = f"Datos: {guardar_datos(resultado, carpeta).resolve()}"

    base = resultado.metodo(SIN_BRECHAS)
    print("\nÁrea quemada media en escenarios de prueba:")
    for metodo in resultado.comparacion:
        marca = "*" if metodo.es_kanan else " "
        print(
            f" {marca} {metodo.nombre:<34} {metodo.area_media:>8,.0f} ha  "
            f"({metodo.reduccion_frente_a(base):>5.1%} menos que sin brechas)"
        )
    print(f"\n{destino}")
    if not args.reporte:
        print("Para explorar los resultados: kanan app  ·  para el reporte HTML: --reporte")
    mejor = min((m for m in resultado.comparacion if m.es_kanan), key=lambda m: m.area_media)
    if mejor.area_media >= resultado.metodo(AL_AZAR).area_media:
        print("Aviso: en esta corrida Kanan no superó a las brechas al azar.", file=sys.stderr)
    return 0


def _cmd_mapa(args: argparse.Namespace) -> int:
    config = cargar_config(args.config)
    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    mapa = construir_mapa(config.mapa)
    mapas.figura_mapa(mapa, carpeta / "mapa.png")
    mapas.figura_riesgo(mapa, carpeta / "riesgo.png")
    print(f"Mapas en {carpeta.resolve()}")
    return 0


def _cmd_app(args: argparse.Namespace) -> int:
    if importlib.util.find_spec("streamlit") is None:
        print('Falta Streamlit. Instálalo con: pip install -e ".[app]"', file=sys.stderr)
        return 2
    guion = Path(__file__).parent / "interfaz" / "app.py"
    # Solo escucha en esta máquina: la app no queda expuesta a la red local.
    orden = [sys.executable, "-m", "streamlit", "run", str(guion), "--server.port",
             str(args.puerto), "--server.address", "localhost",
             "--browser.gatherUsageStats", "false"]  # fmt: skip
    try:
        return subprocess.call(orden)
    except KeyboardInterrupt:
        return 0


def crear_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanan", description="Optimización de brechas cortafuego con NSGA-II."
    )
    parser.add_argument("--version", action="version", version=f"kanan {__version__}")
    comandos = parser.add_subparsers(dest="comando", required=True)

    ejecutar_p = comandos.add_parser(
        "ejecutar", help="optimiza, valida y guarda las tablas de resultados"
    )
    ejecutar_p.add_argument("--config", help="archivo YAML; sin él se usan los valores por omisión")
    ejecutar_p.add_argument("--salida", default="resultados", help="carpeta de salida")
    ejecutar_p.add_argument("--semilla", type=int, help="sustituye la semilla del AG")
    ejecutar_p.add_argument(
        "--reporte", action="store_true",
        help="genera además figuras, animaciones y reporte.html",
    )  # fmt: skip
    ejecutar_p.set_defaults(funcion=_cmd_ejecutar)

    app_p = comandos.add_parser("app", help="abre la aplicación interactiva en el navegador")
    app_p.add_argument("--puerto", type=int, default=8501)
    app_p.set_defaults(funcion=_cmd_app)

    mapa_p = comandos.add_parser("mapa", help="dibuja el área de estudio sin optimizar")
    mapa_p.add_argument("--config")
    mapa_p.add_argument("--salida", default="resultados")
    mapa_p.set_defaults(funcion=_cmd_mapa)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = crear_parser().parse_args(argv)
    try:
        return args.funcion(args)
    except (ValueError, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
