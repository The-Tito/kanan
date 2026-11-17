"""Prueba de humo de la aplicación interactiva, sin navegador."""

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

import kanan.interfaz  # noqa: E402

APP = str(Path(kanan.interfaz.__file__).parent / "app.py")


def test_la_app_corre_y_deja_explorar_un_plan():
    app = AppTest.from_file(APP, default_timeout=120).run()
    assert not app.exception
    assert "Ejecutar" in app.info[0].value

    # Corrida diminuta para que la prueba sea rápida.
    app.number_input(key="poblacion-0").set_value(12)
    app.number_input(key="generaciones-0").set_value(4)
    app.number_input(key="entrenamiento-0").set_value(12)
    app.number_input(key="prueba-0").set_value(15)
    app.button(key="ejecutar").click().run()
    assert not app.exception
    assert "ha" in app.metric[0].value

    # Cada sección se dibuja sin errores.
    for seccion in app.radio(key="seccion").options:
        app.radio(key="seccion").set_value(seccion).run()
        assert not app.exception, seccion

    # Elegir otro plan vuelve a dibujar sin errores y no cambia de sección.
    app.radio(key="seccion").set_value("Explorar planes").run()
    app.number_input(key="plan").set_value(0).run()
    assert not app.exception
    assert app.session_state["plan"] == 0
    assert app.radio(key="seccion").value == "Explorar planes"

    # Reproducir el incendio recorre todos los pasos y deja la barra al final.
    boton = next(b for b in app.button if b.key.startswith("reproducir-"))
    app.selectbox(key="velocidad").set_value("Rápida").run()
    barra = next(s for s in app.slider if s.key.startswith("paso-"))
    barra.set_value(0).run()
    boton.click().run()
    assert not app.exception
    barra = next(s for s in app.slider if s.key.startswith("paso-"))
    assert barra.value == barra.max


def test_una_configuracion_invalida_se_explica():
    app = AppTest.from_file(APP, default_timeout=120).run()
    app.number_input(key="poblacion-0").set_value(13)
    app.button(key="ejecutar").click().run()
    assert not app.exception
    assert "par" in app.error[0].value
