# 011 · Video explicativo generado por código

Fecha: 2026-11-17 · Estado: aceptada

## Contexto

Se quiere un video que explique el funcionamiento interno de Kanan, con narración grabada
aparte en ElevenLabs. En el equipo no hay una clave de esa API.

## Decisión

- El video se genera con un script: matplotlib dibuja los cuadros con el mismo código y los
  mismos datos de Kanan, y ffmpeg los codifica.
- El guion vive junto a los dibujos (`video/escenas.py`): cada frase lleva su imagen.
- La narración es un archivo de audio por escena, que el script toma de `video/audio/`.
- El video, los audios y los cuadros intermedios no se versionan; el guion sí.

## Alternativas

- **Editor de video.** Las figuras se desactualizarían al cambiar el código y la sincronía
  habría que rehacerla a mano.
- **Una sola pista de audio para todo el video.** Menos archivos, pero obliga a adivinar dónde
  empieza cada escena; por escena la sincronía es exacta.
- **Llamar a la API de ElevenLabs desde el script.** Requiere guardar una clave; se puede
  agregar después sin cambiar lo demás.

## Consecuencias

- Lo que muestra el video es lo que hace el programa: el incendio, los planes y la evolución
  son salidas reales.
- Cambiar una frase obliga a regenerar el audio de esa escena.
- Dentro de una escena la sincronía es aproximada (proporcional a las palabras de cada frase).
- `ffmpeg` pasa a ser un requisito, solo para el video.
