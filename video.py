#!/usr/bin/env python3
"""Screencasts para el App Review de Meta: hojas de contacto y armado con subtítulos.

Stdlib + ffmpeg/ffprobe (con libass para los subtítulos). Nunca sube nada:
deja los .mp4 en una carpeta y la persona (o la sesión, con su OK) los sube.

  python3 -I video.py hoja VIDEO [--cada 2] [--salida hoja.png]
      Una imagen con un cuadro cada N segundos, para ubicar los cortes.
  python3 -I video.py cuadro VIDEO --en 13.5 [--recorte 700:300:300:820] [--salida c.png]
      Un cuadro suelto (con recorte opcional, w:h:x:y), para leer un texto.
  python3 -I video.py armar SPEC.json
      Corta los tramos, tapa lo privado, los une por video y quema los subtítulos.

Forma de SPEC.json (las rutas pueden ser relativas al JSON):

  {
    "salida": "out",
    "segmentos": {"login": ["take1.mp4", 1.5, 27.5], "dash": ["take1.mp4", 29.5, 55]},
    "tapar": {"login": [[0, 1040, 900, 40]]},
    "videos": {
      "app_ads_read": {
        "partes": ["login", "dash"],
        "subtitulos": [[0, 5, "The client opens the private connect link."], ...]
      }
    }
  }

Los tiempos de los subtítulos son del video armado (no del tramo). `\\N` parte
la línea. Todo se normaliza a 1920x1080, 30 fps, H.264, sin audio.

`tapar` (opcional) pone recuadros negros sobre un segmento, en píxeles de la
toma original: [x, y, ancho, alto]. Sirve para una URL, un correo o un chat
que se coló en la grabación. Revisa el resultado con `hoja` sobre la salida.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path

ANCHO, ALTO, FPS = 1920, 1080, 30

ASS_CABECERA = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {ANCHO}
PlayResY: {ALTO}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,40,&H00FFFFFF,&H00FFFFFF,&H00000000,&HC0000000,1,0,0,0,100,100,0,0,3,18,0,2,80,80,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


NOMBRE = re.compile(r"^[A-Za-z0-9_-]+$")


class ErrorSpec(ValueError):
    """La especificación no sirve. El mensaje dice qué arreglar."""


def marca_tiempo(t: float) -> str:
    """Segundos → H:MM:SS.cc, el formato de ASS."""
    if t < 0:
        raise ErrorSpec(f"tiempo negativo: {t}")
    centesimas = round(t * 100)
    h, resto = divmod(centesimas, 360000)
    m, resto = divmod(resto, 6000)
    s, c = divmod(resto, 100)
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"


def ass(subtitulos: list[list]) -> str:
    """El archivo .ass completo para una lista de [inicio, fin, texto]."""
    lineas = []
    for item in subtitulos:
        if len(item) != 3:
            raise ErrorSpec(f"cada subtítulo es [inicio, fin, texto]: {item!r}")
        a, b, texto = float(item[0]), float(item[1]), str(item[2])
        if b <= a:
            raise ErrorSpec(f"el subtítulo termina antes de empezar: {item!r}")
        limpio = texto.replace("\n", "\\N").replace("{", "(").replace("}", ")")
        lineas.append(f"Dialogue: 0,{marca_tiempo(a)},{marca_tiempo(b)},Cap,,0,0,0,,{limpio}\n")
    return ASS_CABECERA + "".join(lineas)


def validar(spec: dict, base: Path) -> dict:
    """Revisa la forma y resuelve rutas. Devuelve la duración de cada video."""
    for clave in ("segmentos", "videos"):
        if not isinstance(spec.get(clave), dict) or not spec[clave]:
            raise ErrorSpec(f"falta '{clave}' (un objeto no vacío)")
    duraciones: dict[str, float] = {}
    for clave in ("segmentos", "videos"):
        for nombre in spec[clave]:
            if not NOMBRE.match(nombre):
                raise ErrorSpec(f"el nombre '{nombre}' de '{clave}' solo puede tener letras, números, _ y -")
    tapas = spec.get("tapar") or {}
    if not isinstance(tapas, dict):
        raise ErrorSpec("'tapar' es un objeto {segmento: [[x, y, ancho, alto], ...]}")
    for nombre, cajas in tapas.items():
        if nombre not in spec["segmentos"]:
            raise ErrorSpec(f"'tapar' usa un segmento que no existe: {nombre}")
        if not isinstance(cajas, list) or not cajas:
            raise ErrorSpec(f"'tapar.{nombre}' es una lista de [x, y, ancho, alto]")
        for caja in cajas:
            if not (isinstance(caja, list) and len(caja) == 4
                    and all(isinstance(n, (int, float)) and not isinstance(n, bool)
                            and math.isfinite(n) and n >= 0 for n in caja)
                    and caja[2] > 0 and caja[3] > 0):
                raise ErrorSpec(f"cada caja de 'tapar.{nombre}' es [x, y, ancho, alto] en píxeles: {caja!r}")
    for nombre, seg in spec["segmentos"].items():
        if not (isinstance(seg, list) and len(seg) == 3):
            raise ErrorSpec(f"el segmento '{nombre}' es [archivo, inicio, fin]")
        archivo, a, b = seg
        if float(b) <= float(a):
            raise ErrorSpec(f"el segmento '{nombre}' termina antes de empezar")
        ruta = Path(archivo).expanduser()
        seg[0] = str(ruta if ruta.is_absolute() else (base / ruta))
    largo_video: dict[str, float] = {}
    for vnombre, v in spec["videos"].items():
        partes = v.get("partes") or []
        if not partes:
            raise ErrorSpec(f"el video '{vnombre}' no tiene partes")
        faltan = [p for p in partes if p not in spec["segmentos"]]
        if faltan:
            raise ErrorSpec(f"el video '{vnombre}' usa segmentos que no existen: {faltan}")
        total = sum(float(spec["segmentos"][p][2]) - float(spec["segmentos"][p][1]) for p in partes)
        ass(v.get("subtitulos") or [])  # valida la forma antes de leer los tiempos
        for sub in v.get("subtitulos") or []:
            if float(sub[1]) > total + 0.5:
                raise ErrorSpec(f"un subtítulo de '{vnombre}' termina en {sub[1]} s y el video dura {total:.1f} s")
        largo_video[vnombre] = total
    duraciones.update(largo_video)
    return duraciones


def filtro_tramo(cajas: list[list] | None = None) -> str:
    """El -vf de un tramo: las tapas (en píxeles de la toma) y después la
    normalización a 1920x1080 y 30 fps."""
    tapas = [f"drawbox=x={int(x)}:y={int(y)}:w={int(w)}:h={int(h)}:color=black@1:t=fill"
             for x, y, w, h in (cajas or [])]
    return ",".join([*tapas, f"scale={ANCHO}:{ALTO},fps={FPS},format=yuv420p"])


def lista_concat(trabajo: Path, partes: list[str]) -> str:
    """La lista del demuxer concat, con rutas ABSOLUTAS: ffmpeg resuelve las
    relativas desde la carpeta de la lista, no desde donde se corre."""
    base = trabajo.resolve()
    return "".join("file '" + str(base / f"{p}.mp4").replace("'", "'\\''") + "'\n" for p in partes)


def _ffmpeg(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True, cwd=cwd)


def _requiere(binario: str) -> None:
    if not shutil.which(binario):
        sys.exit(f"falta {binario} en el PATH")


def armar(ruta_spec: Path) -> None:
    _requiere("ffmpeg")
    spec = json.loads(ruta_spec.read_text())
    base = ruta_spec.resolve().parent
    largos = validar(spec, base)
    salida = Path(spec.get("salida") or "out")
    salida = salida if salida.is_absolute() else base / salida
    trabajo = (salida / ".tramos").resolve()
    trabajo.mkdir(parents=True, exist_ok=True)
    tapas = spec.get("tapar") or {}
    for nombre, (archivo, a, b) in spec["segmentos"].items():
        if not Path(archivo).is_file():
            sys.exit(f"no existe el archivo del segmento '{nombre}': {archivo}")
        _ffmpeg("-ss", str(a), "-to", str(b), "-i", archivo,
                "-vf", filtro_tramo(tapas.get(nombre)), "-an",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", str(trabajo / f"{nombre}.mp4"))
    for vnombre, v in spec["videos"].items():
        lista = trabajo / f"{vnombre}.txt"
        lista.write_text(lista_concat(trabajo, v["partes"]))
        crudo = trabajo / f"{vnombre}_crudo.mp4"
        _ffmpeg("-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(crudo))
        destino = salida / f"{vnombre}.mp4"
        subs = v.get("subtitulos") or []
        if subs:
            archivo_ass = trabajo / f"{vnombre}.ass"
            archivo_ass.write_text(ass(subs))
            # Nombre relativo con cwd=trabajo: en el filtro de ffmpeg, ':' y '\'
            # de una ruta absoluta (C:\... en Windows) rompen la opción.
            _ffmpeg("-i", str(crudo.resolve()), "-vf", f"subtitles={archivo_ass.name}",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-movflags", "+faststart",
                    str(destino.resolve()), cwd=trabajo)
        else:
            shutil.copyfile(crudo, destino)
        print(f"{destino}: {largos[vnombre]:.1f} s")


def hoja(video: Path, cada: float, salida: Path) -> None:
    _requiere("ffmpeg")
    _requiere("ffprobe")
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        check=True, capture_output=True, text=True).stdout.strip() or 0)
    n = max(1, int(dur // cada) + 1)
    cols = min(7, n)
    filas = (n + cols - 1) // cols
    _ffmpeg("-i", str(video), "-vf",
            f"fps=1/{cada},scale=384:-1,tile={cols}x{filas}",
            "-frames:v", "1", str(salida))
    print(f"{salida}: {n} cuadros, uno cada {cada} s (fila por fila, de izquierda a derecha; el primero es 0 s)")


def cuadro(video: Path, en: float, recorte: str | None, salida: Path) -> None:
    _requiere("ffmpeg")
    filtros = ["-vf", f"crop={recorte}"] if recorte else []
    _ffmpeg("-ss", str(en), "-i", str(video), "-frames:v", "1", *filtros, str(salida))
    print(salida)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    h = sub.add_parser("hoja")
    h.add_argument("video", type=Path)
    h.add_argument("--cada", type=float, default=2.0)
    h.add_argument("--salida", type=Path, default=Path("hoja.png"))
    c = sub.add_parser("cuadro")
    c.add_argument("video", type=Path)
    c.add_argument("--en", type=float, required=True)
    c.add_argument("--recorte")
    c.add_argument("--salida", type=Path, default=Path("cuadro.png"))
    a = sub.add_parser("armar")
    a.add_argument("spec", type=Path)
    args = p.parse_args(argv)
    try:
        if args.cmd == "hoja":
            hoja(args.video, args.cada, args.salida)
        elif args.cmd == "cuadro":
            cuadro(args.video, args.en, args.recorte, args.salida)
        else:
            armar(args.spec)
    except ErrorSpec as e:
        print(f"spec: {e}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg falló ({e.returncode})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
