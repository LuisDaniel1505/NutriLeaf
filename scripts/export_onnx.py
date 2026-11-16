"""Exporta el modelo entrenado de NutriLeaf a formato ONNX.

ONNX permite ejecutar el modelo en el navegador (con onnxruntime-web), lo que
habilita el despliegue estático en GitHub Pages sin necesidad de backend Python.

Uso (desde la raíz del proyecto)::

    python scripts/export_onnx.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import torch

from app.config import MODEL_PATH, MODELS_DIR
from app.model import build_model


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(f"[error] No se encontró el modelo en {MODEL_PATH}.")

    checkpoint = torch.load(str(MODEL_PATH), map_location="cpu", weights_only=False)
    arch = checkpoint.get("arch", "resnet18")
    class_names = checkpoint.get("class_names", [])
    input_size = checkpoint.get("input_size", 320)

    print(f"[info] Arquitectura: {arch} · clases: {class_names} · entrada: {input_size}")

    model = build_model(num_classes=len(class_names), arch=arch, pretrained=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    dummy = torch.randn(1, 3, input_size, input_size)
    onnx_path = MODELS_DIR / "leaf_classifier.onnx"

    torch.onnx.export(
        model,
        dummy,
        str(onnx_path),
        input_names=["input"],
        output_names=["output"],
        opset_version=18,
    )

    # El exportador de torch 2.14 guarda los pesos en un archivo `.onnx.data`
    # externo. Se combinan en un único archivo para facilitar el despliegue.
    import onnx

    onnx_model = onnx.load(str(onnx_path), load_external_data=True)
    onnx.save(onnx_model, str(onnx_path), save_as_external_data=False)

    data_path = Path(str(onnx_path) + ".data")
    if data_path.exists():
        data_path.unlink()

    size_mb = onnx_path.stat().st_size / 1e6
    print(f"[ok] Modelo ONNX guardado en {onnx_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
