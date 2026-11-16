"""Tests de video.py sin ffmpeg: tiempos, subtítulos y validación del spec."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import video

SPEC = {
    "salida": "out",
    "segmentos": {"login": ["take1.mp4", 1.5, 27.5], "dash": ["take1.mp4", 29.5, 55.0]},
    "videos": {
        "app_ads_read": {
            "partes": ["login", "dash"],
            "subtitulos": [[0, 5, "Connect link."], [26, 51.5, "ads_read: spend, reach.\\NRead only."]],
        }
    },
}


def test_marca_tiempo():
    assert video.marca_tiempo(0) == "0:00:00.00"
    assert video.marca_tiempo(85.3) == "0:01:25.30"
    assert video.marca_tiempo(3725.456) == "1:02:05.46"
    with pytest.raises(video.ErrorSpec):
        video.marca_tiempo(-1)


def test_ass_lineas_y_escape():
    out = video.ass([[0, 5, "uno {dos}\ntres"]])
    assert out.startswith("[Script Info]")
    assert "Dialogue: 0,0:00:00.00,0:00:05.00,Cap,,0,0,0,,uno (dos)\\Ntres" in out


@pytest.mark.parametrize("malo", [[[5, 5, "x"]], [[6, 5, "x"]], [[1, 2]]])
def test_ass_rechaza_subtitulos_malos(malo):
    with pytest.raises(video.ErrorSpec):
        video.ass(malo)


def test_validar_resuelve_rutas_y_duracion(tmp_path: Path):
    spec = copy.deepcopy(SPEC)
    largos = video.validar(spec, tmp_path)
    assert largos == {"app_ads_read": pytest.approx(51.5)}
    assert spec["segmentos"]["login"][0] == str(tmp_path / "take1.mp4")


@pytest.mark.parametrize("cambio,mensaje", [
    (lambda s: s["videos"]["app_ads_read"].update(partes=["nada"]), "no existen"),
    (lambda s: s["segmentos"].update(login=["a.mp4", 10, 5]), "termina antes"),
    (lambda s: s["videos"]["app_ads_read"]["subtitulos"].append([50, 80, "x"]), "dura"),
    (lambda s: s.pop("videos"), "falta 'videos'"),
])
def test_validar_rechaza(tmp_path: Path, cambio, mensaje):
    spec = copy.deepcopy(SPEC)
    cambio(spec)
    with pytest.raises(video.ErrorSpec, match=mensaje):
        video.validar(spec, tmp_path)


def test_lista_concat_usa_rutas_absolutas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    texto = video.lista_concat(Path("out/.tramos"), ["login", "dash"])
    rutas = [linea.split("'")[1] for linea in texto.splitlines()]
    assert rutas == [str(tmp_path / "out/.tramos/login.mp4"), str(tmp_path / "out/.tramos/dash.mp4")]
    assert all(Path(r).is_absolute() for r in rutas)


def test_filtro_tramo_sin_y_con_tapas():
    assert video.filtro_tramo() == "scale=1920:1080,fps=30,format=yuv420p"
    f = video.filtro_tramo([[0, 1040, 900, 40]])
    assert f.startswith("drawbox=x=0:y=1040:w=900:h=40:color=black@1:t=fill,scale=1920:1080")


def test_validar_acepta_tapar(tmp_path: Path):
    spec = copy.deepcopy(SPEC)
    spec["tapar"] = {"login": [[0, 1040, 900, 40]]}
    assert video.validar(spec, tmp_path) == {"app_ads_read": pytest.approx(51.5)}


@pytest.mark.parametrize("tapar,mensaje", [
    ({"nada": [[0, 0, 10, 10]]}, "no existe"),
    ({"login": []}, "lista"),
    ({"login": [[0, 0, 0, 10]]}, "píxeles"),
    ({"login": [[0, 0, 10]]}, "píxeles"),
    ([1, 2], "objeto"),
])
def test_validar_rechaza_tapar(tmp_path: Path, tapar, mensaje):
    spec = copy.deepcopy(SPEC)
    spec["tapar"] = tapar
    with pytest.raises(video.ErrorSpec, match=mensaje):
        video.validar(spec, tmp_path)


@pytest.mark.parametrize("cambio,mensaje", [
    (lambda s: s["segmentos"].update({"../fuera": ["a.mp4", 0, 1]}), "solo puede tener"),
    (lambda s: s["videos"].update({"mal nombre": {"partes": ["login"]}}), "solo puede tener"),
    (lambda s: s.update(tapar={"login": [[True, True, True, True]]}), "píxeles"),
    (lambda s: s.update(tapar={"login": [[0, 0, float("inf"), 10]]}), "píxeles"),
    (lambda s: s["videos"]["app_ads_read"]["subtitulos"].append([1]), r"\[inicio, fin, texto\]"),
])
def test_validar_rechaza_nombres_cajas_y_subtitulos_malos(tmp_path: Path, cambio, mensaje):
    spec = copy.deepcopy(SPEC)
    cambio(spec)
    with pytest.raises(video.ErrorSpec, match=mensaje):
        video.validar(spec, tmp_path)


def test_lista_concat_escapa_comillas(tmp_path):
    carpeta = tmp_path / "John's"
    texto = video.lista_concat(carpeta, ["login"])
    assert texto == "file '" + str(carpeta.resolve() / "login.mp4").replace("'", "'\\''") + "'\n"


def test_armar_lee_y_escribe_utf8(tmp_path, monkeypatch):
    """El spec y los archivos de trabajo van en UTF-8 aunque el sistema use otra
    codificación (Windows usa cp1252 por defecto)."""
    llamadas = []
    monkeypatch.setattr(video, "_requiere", lambda b: None)
    monkeypatch.setattr(video, "_ffmpeg", lambda *a, **k: llamadas.append(a))
    base = tmp_path / "José"
    base.mkdir()
    toma = base / "Grabación.mp4"
    toma.write_bytes(b"")
    spec = {"salida": "out", "segmentos": {"a": [toma.name, 0, 2]},
            "videos": {"v": {"partes": ["a"], "subtitulos": [[0, 2, "Configuración (Settings)"]]}}}
    ruta = base / "spec.json"
    ruta.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    real = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, encoding=None, **k: real(self, encoding=encoding or "cp1252", **k))
    video.armar(ruta)
    trabajo = base / "out" / ".tramos"
    assert "Configuración" in (trabajo / "v.ass").read_bytes().decode("utf-8")
    assert "José" in (trabajo / "v.txt").read_bytes().decode("utf-8")


def test_hoja_toma_el_cuadro_del_inicio_de_cada_intervalo(tmp_path, monkeypatch):
    filtros = []
    monkeypatch.setattr(video, "_requiere", lambda b: None)
    monkeypatch.setattr(video.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "10.0"})())
    monkeypatch.setattr(video, "_ffmpeg", lambda *a, **k: filtros.append(a[a.index("-vf") + 1]))
    video.hoja(tmp_path / "t.mp4", 2.0, tmp_path / "h.png")
    assert filtros[0].startswith("fps=1/2.0:round=up,")
