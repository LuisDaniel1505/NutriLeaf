"""Evalúa un modelo guardado sobre el conjunto de test y regenera sus métricas.

Calcula exactitud, precision, recall y F1 por clase, y guarda ``metrics.json``,
la matriz de confusión y la gráfica correspondiente en ``models/``. Útil para
verificar un modelo ya entrenado sin necesidad de volver a entrenar.

Uso (desde la raíz del proyecto)::

    python scripts/evaluate_model.py
    python scripts/evaluate_model.py --model models/otro_modelo.pt
"""
import argparse
import json
import sys
from pathlib import Path

# Permite importar el paquete `app` aunque el script se ejecute directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib

matplotlib.use("Agg")  # Backend sin pantalla.

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision import datasets

from app.config import MODEL_PATH, MODELS_DIR, PROCESSED_DIR
from app.model import LeafClassifier, build_inference_transform

PLOTS_DIR = MODELS_DIR / "plots"
REPORTS_DIR = MODELS_DIR / "reports"


@torch.no_grad()
def predict_all(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[np.ndarray, np.ndarray]:
    """Ejecuta inferencia en todo el loader y devuelve (predicciones, etiquetas)."""
    preds: list[int] = []
    labels: list[int] = []
    for images, targets in loader:
        images = images.to(device)
        outputs = model(images)
        preds.extend(outputs.argmax(dim=1).cpu().numpy().tolist())
        labels.extend(targets.numpy().tolist())
    return np.array(preds), np.array(labels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa un modelo guardado de NutriLeaf.")
    parser.add_argument("--model", type=Path, default=MODEL_PATH, help="Ruta del checkpoint")
    args = parser.parse_args()

    clf = LeafClassifier(args.model)
    class_names = clf.class_names
    device = clf.device

    transform = build_inference_transform(clf.input_size)
    test_set = datasets.ImageFolder(str(PROCESSED_DIR / "test"), transform=transform)
    loader = DataLoader(test_set, batch_size=32, shuffle=False)

    preds, labels = predict_all(clf.model, loader, device)
    acc = accuracy_score(labels, preds)
    report = classification_report(labels, preds, target_names=class_names, output_dict=True)

    print(classification_report(labels, preds, target_names=class_names))
    print(f"Exactitud en test: {acc:.4f}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({"test_accuracy": acc, "classification_report": report}, f, indent=2, ensure_ascii=False)

    cm = confusion_matrix(labels, preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Greens", xticklabels=class_names, yticklabels=class_names)
    plt.title("Matriz de confusión — Test")
    plt.xlabel("Predicción")
    plt.ylabel("Real")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "confusion_matrix.png", dpi=120)
    plt.close()

    print(f"[ok] Métricas y gráficas guardadas en {REPORTS_DIR} y {PLOTS_DIR}")


if __name__ == "__main__":
    main()
