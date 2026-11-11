"""API de NutriLeaf construida con FastAPI.

Expone los endpoints de predicción para imágenes y frames de video, y sirve
la interfaz web estática.

Ejecutar (desde la raíz del proyecto):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import base64
import io
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from .config import MODEL_PATH, STATIC_DIR
from .model import LeafClassifier

app = FastAPI(
    title="NutriLeaf API",
    description="Identificación de deficiencias nutricionales en hojas de maíz.",
    version="0.1.0",
)

# El clasificador se carga de forma perezosa (la primera vez que se usa).
_classifier: Optional[LeafClassifier] = None


def get_classifier() -> LeafClassifier:
    global _classifier
    if _classifier is None:
        _classifier = LeafClassifier(MODEL_PATH)
    return _classifier


class FrameRequest(BaseModel):
    """Un frame de video codificado como data URI o base64 puro."""

    image: str


@app.get("/health")
def health() -> dict:
    """Estado del servicio y del modelo."""
    return {
        "status": "ok",
        "model_loaded": MODEL_PATH.exists(),
        "model_path": str(MODEL_PATH),
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)) -> dict:
    """Predice la deficiencia a partir de una imagen subida (multipart/form-data)."""
    _ensure_model()
    image = _read_image(await file.read())
    return get_classifier().predict(image)


@app.post("/predict-frame")
async def predict_frame(req: FrameRequest) -> dict:
    """Predice la deficiencia a partir de un frame de video (base64)."""
    _ensure_model()
    image = _decode_frame(req.image)
    return get_classifier().predict(image)


def _ensure_model() -> None:
    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="El modelo aún no está entrenado. Ejecuta training/train.py primero.",
        )


def _read_image(data: bytes) -> Image.Image:
    try:
        return Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="No se pudo leer la imagen.") from exc


def _decode_frame(data: str) -> Image.Image:
    # Acepta data URI ("data:image/jpeg;base64,...") o base64 puro.
    if "," in data:
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Frame inválido.") from exc


# ---- Archivos estáticos y página principal ----
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(str(STATIC_DIR / "index.html"))
