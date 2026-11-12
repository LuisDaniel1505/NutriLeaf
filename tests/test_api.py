"""Pruebas de integración de la API (FastAPI + TestClient).

Verifican el contrato de los endpoints ``/health``, ``/predict`` y
``/predict-frame``, incluyendo los casos de error (imagen inválida y frame
inválido).
"""
import base64
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import MODEL_PATH
from app.labels import CLASS_NAMES
from app.main import app

client = TestClient(app)


@pytest.fixture
def imagen_valida_bytes() -> bytes:
    """Genera una imagen JPEG válida en memoria (no depende de archivos)."""
    img = Image.new("RGB", (100, 100), color=(80, 140, 60))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_health() -> None:
    """El endpoint /health debe responder OK e indicar el estado del modelo."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] == MODEL_PATH.exists()


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Modelo no entrenado")
def test_predict_imagen_valida(imagen_valida_bytes: bytes) -> None:
    """/predict debe devolver 200 con la estructura de respuesta esperada."""
    resp = client.post(
        "/predict",
        files={"file": ("hoja.jpg", imagen_valida_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    for campo in ("class", "class_index", "label_es", "confidence", "probabilities", "recommendation"):
        assert campo in body, f"Falta el campo '{campo}'"


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Modelo no entrenado")
def test_predict_devuelve_clase_conocida(imagen_valida_bytes: bytes) -> None:
    """La clase predicha debe estar entre las 5 clases conocidas."""
    resp = client.post(
        "/predict",
        files={"file": ("hoja.jpg", imagen_valida_bytes, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["class"] in CLASS_NAMES


def test_predict_imagen_invalida() -> None:
    """Un archivo que no es una imagen debe devolver 400."""
    resp = client.post(
        "/predict",
        files={"file": ("mal.jpg", b"esto no es una imagen", "image/jpeg")},
    )
    assert resp.status_code == 400


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="Modelo no entrenado")
def test_predict_frame_valido(imagen_valida_bytes: bytes) -> None:
    """/predict-frame debe aceptar una imagen en base64 y devolver 200."""
    b64 = base64.b64encode(imagen_valida_bytes).decode("ascii")
    resp = client.post("/predict-frame", json={"image": b64})
    assert resp.status_code == 200
    assert resp.json()["class"] in CLASS_NAMES


def test_predict_frame_invalido() -> None:
    """Un frame con base64 corrupto debe devolver 400."""
    resp = client.post("/predict-frame", json={"image": "no-es-base64-!!!"})
    assert resp.status_code == 400
