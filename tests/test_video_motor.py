import pytest
from video.motor import PAUSA_FINAL, Escena, Tiempo, planear, trocear


def nada(figura, avance):
    pass


def test_los_subtitulos_se_cortan_por_oracion():
    assert trocear("Hay una trampa. ¿Funciona? Sí, funciona.") == [
        "Hay una trampa.", "¿Funciona?", "Sí, funciona.",
    ]  # fmt: skip
    largos = trocear("palabra " * 60)
    assert len(largos) > 1 and all(len(t) <= 150 for t in largos)
    assert " ".join(largos).split() == ["palabra"] * 60


def test_cada_tiempo_dura_en_proporcion_a_sus_palabras():
    escena = Escena("x", "X", [Tiempo("uno dos tres.", nada), Tiempo("cuatro.", nada)])
    cuadros = planear(escena, 8.0)
    assert [c.subtitulo for c in cuadros] == ["uno dos tres.", "cuatro."]
    assert cuadros[0].duracion == pytest.approx(6.0)
    assert cuadros[1].duracion == pytest.approx(2.0 + PAUSA_FINAL)
    assert escena.narracion() == "uno dos tres. cuatro."


def test_un_tiempo_animado_recorre_el_avance_de_0_a_1():
    escena = Escena("x", "X", [Tiempo("Primera oración. Segunda oración.", nada, cuadros=5)])
    cuadros = planear(escena, 10.0)
    avances = [c.avance for c in cuadros]
    assert avances[0] == 0.0 and avances[-1] == 1.0
    assert avances == sorted(avances)
    assert sum(c.duracion for c in cuadros) == pytest.approx(10.0 + PAUSA_FINAL)
    assert {c.subtitulo for c in cuadros} == {"Primera oración.", "Segunda oración."}
