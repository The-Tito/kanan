"""Genera el video explicativo de Kanan.

Uso, desde la raíz del repositorio:

    .venv/bin/python -m video.generar            # video completo
    .venv/bin/python -m video.generar --guion    # solo escribe los textos a narrar
    .venv/bin/python -m video.generar --escenas 03-fuego 08-evolucion

Si existe ``video/audio/<clave>.mp3`` (o .wav, .m4a), la escena dura lo que dure ese audio y
lo lleva de pista; si no, se estima la duración y la escena queda en silencio.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from video.datos import cargar
from video.escenas import construir_escenas
from video.motor import Escena, renderizar_escena, unir

RAIZ = Path(__file__).parent
AUDIO = RAIZ / "audio"
GUION = RAIZ / "guion"
TRABAJO = RAIZ / ".trabajo"
SALIDA = RAIZ / "salida"


def escribir_guion(escenas: list[Escena]) -> None:
    """Un archivo de texto por escena (para pegar en ElevenLabs) y el guion completo."""
    GUION.mkdir(exist_ok=True)
    completo = [
        "# Guion del video explicativo de Kanan",
        "",
        "Generado por `python -m video.generar --guion` a partir de `video/escenas.py`; no se "
        "edita a mano.",
        "",
        "Cada escena se narra por separado y se guarda como `video/audio/<clave>.mp3`.",
        "",
    ]
    for escena in escenas:
        (GUION / f"{escena.clave}.txt").write_text(escena.narracion() + "\n", encoding="utf-8")
        completo += [f"## {escena.clave} · {escena.titulo}", ""]
        completo += [f"{tiempo.texto}\n" for tiempo in escena.tiempos]
    (RAIZ / "guion.md").write_text("\n".join(completo), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--guion", action="store_true", help="solo escribe el guion")
    parser.add_argument("--escenas", nargs="*", help="claves de las escenas a generar")
    parser.add_argument("--sin-subtitulos", action="store_true")
    args = parser.parse_args()

    sistema, corrida = cargar(TRABAJO / "corrida.pkl")
    escenas = construir_escenas(sistema, corrida)
    escribir_guion(escenas)
    palabras = sum(e.palabras() for e in escenas)
    print(f"Guion: {len(escenas)} escenas, {palabras} palabras → {GUION}")
    if args.guion:
        return

    elegidas = [e for e in escenas if not args.escenas or e.clave in args.escenas]
    partes, total, con_audio = [], 0.0, 0
    for escena in elegidas:
        numero = escenas.index(escena) + 1
        parte, duracion, tiene_audio = renderizar_escena(
            escena, numero, len(escenas), AUDIO, TRABAJO, not args.sin_subtitulos
        )
        estado = "con audio" if tiene_audio else "sin audio (duración estimada)"
        print(f"  {escena.clave}: {duracion:5.1f} s · {estado}")
        partes.append(parte)
        total += duracion
        con_audio += tiene_audio

    SALIDA.mkdir(exist_ok=True)
    nombre = "kanan_explicado.mp4" if not args.escenas else "kanan_parcial.mp4"
    unir(partes, SALIDA / nombre)
    print(f"\nVideo: {(SALIDA / nombre).resolve()}")
    print(f"Duración: {int(total // 60)} min {total % 60:.0f} s · "
          f"{con_audio} de {len(elegidas)} escenas con narración")  # fmt: skip


if __name__ == "__main__":
    main()
