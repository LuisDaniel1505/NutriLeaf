"""Pruebas unitarias del módulo ``app.labels``.

Verifican que las etiquetas de las 5 clases sean coherentes y que el mapeo
de las carpetas del dataset (con errores de escritura) funcione correctamente.
"""
from app.labels import (
    CLASS_LABELS_ES,
    CLASS_NAMES,
    CLASS_SYMBOLS,
    CLASS_TO_IDX,
    DATASET_FOLDER_MAP,
    IDX_TO_CLASS,
)


def test_hay_cinco_clases() -> None:
    """El modelo debe distinguir exactamente 5 clases."""
    assert len(CLASS_NAMES) == 5


def test_clases_esperadas() -> None:
    """Las clases deben ser las definidas en el documento del proyecto."""
    esperadas = {"healthy", "nitrogen", "phosphorus", "potassium", "magnesium"}
    assert set(CLASS_NAMES) == esperadas


def test_toda_clase_tiene_etiqueta_en_espanol() -> None:
    """Cada clase debe tener una etiqueta legible en español no vacía."""
    for clase in CLASS_NAMES:
        assert clase in CLASS_LABELS_ES
        assert CLASS_LABELS_ES[clase].strip()


def test_toda_clase_tiene_simbolo() -> None:
    """Cada clase debe tener un símbolo químico o identificador corto."""
    for clase in CLASS_NAMES:
        assert clase in CLASS_SYMBOLS


def test_indices_son_inversos() -> None:
    """``CLASS_TO_IDX`` e ``IDX_TO_CLASS`` deben ser inversos entre sí."""
    assert len(CLASS_TO_IDX) == 5
    assert len(IDX_TO_CLASS) == 5
    for nombre, indice in CLASS_TO_IDX.items():
        assert IDX_TO_CLASS[indice] == nombre


def test_mapeo_carpetas_dataset() -> None:
    """Los nombres con errores del dataset deben mapearse a clases canónicas."""
    assert DATASET_FOLDER_MAP["helathy"] == "healthy"
    assert DATASET_FOLDER_MAP["magnessium"] == "magnesium"
    assert DATASET_FOLDER_MAP["phosphorous"] == "phosphorus"
    assert DATASET_FOLDER_MAP["pottasium"] == "potassium"
