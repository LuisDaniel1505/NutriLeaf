"""Entrenamiento del modelo de clasificación de NutriLeaf.

Entrena una red convolucional con transfer learning (base preentrenada de
ImageNet + clasificador ajustado a 5 clases) sobre el dataset de hojas de maíz.

Flujo del script
----------------
1. Carga el dataset desde ``data/processed/{train,val,test}`` (generado con
   ``training/preprocess.py``) mediante :class:`~torchvision.datasets.ImageFolder`.
2. Aplica aumentación de datos solo en entrenamiento (flips y rotaciones).
3. Balancea las clases con :class:`~torch.utils.data.WeightedRandomSampler`,
   ya que el dataset original está desbalanceado.
4. Entrena con CrossEntropyLoss + Adam, evaluando en validación cada época.
5. Evalúa en test, genera métricas y gráficas, y guarda el mejor modelo.

Uso (desde la raíz del proyecto)::

    python -m training.train
    python -m training.train --arch resnet18 --epochs 25 --batch-size 32
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Backend sin pantalla (funciona en servidores/CI)

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms
from tqdm import tqdm

from app.config import MODELS_DIR, PROCESSED_DIR
from app.labels import CLASS_NAMES
from app.model import IMAGENET_MEAN, IMAGENET_STD, build_model

# Directorios de salida para gráficas y métricas.
PLOTS_DIR = MODELS_DIR / "plots"
REPORTS_DIR = MODELS_DIR / "reports"


# --------------------------------------------------------------------------- #
#  Transformaciones de datos
# --------------------------------------------------------------------------- #
def build_transforms(input_size: int = 224) -> tuple[transforms.Compose, transforms.Compose]:
    """Devuelve los transform de entrenamiento (con aumentación) y evaluación.

    La aumentación reduce el sobreajuste dado el tamaño pequeño del dataset.
    La normalización usa los valores de ImageNet porque partimos de pesos
    preentrenados en ese conjunto.
    """
    train_transform = transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(degrees=15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

    eval_transform = transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )

    return train_transform, eval_transform


def build_dataloaders(
    batch_size: int, input_size: int, num_workers: int
) -> tuple[DataLoader, DataLoader, DataLoader, list[str]]:
    """Construye los DataLoaders de train/val/test y devuelve los nombres de clase.

    Devuelve
    --------
    (train_loader, val_loader, test_loader, class_names)
        ``class_names`` son las etiquetas en el orden que espera el modelo.
    """
    train_transform, eval_transform = build_transforms(input_size)

    train_set = datasets.ImageFolder(str(PROCESSED_DIR / "train"), transform=train_transform)
    val_set = datasets.ImageFolder(str(PROCESSED_DIR / "val"), transform=eval_transform)
    test_set = datasets.ImageFolder(str(PROCESSED_DIR / "test"), transform=eval_transform)

    class_names = train_set.classes

    # Balanceo de clases: el dataset original tiene clases desbalanceadas.
    train_loader = DataLoader(
        train_set,
        batch_size=batch_size,
        sampler=_make_balanced_sampler(train_set),
        num_workers=num_workers,
    )
    val_loader = DataLoader(val_set, batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader = DataLoader(test_set, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    return train_loader, val_loader, test_loader, class_names


def _make_balanced_sampler(dataset: datasets.ImageFolder) -> WeightedRandomSampler:
    """Crea un sampler que muestra cada clase con igual probabilidad.

    A cada muestra se le asigna un peso inversamente proporcional a la
    frecuencia de su clase, de modo que las clases minoritarias aparezcan
    con más frecuencia durante el entrenamiento.
    """
    targets = np.array(dataset.targets)
    class_counts = np.bincount(targets)
    weights = 1.0 / class_counts[targets]
    return WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)


# --------------------------------------------------------------------------- #
#  Entrenamiento y evaluación
# --------------------------------------------------------------------------- #
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
) -> float:
    """Ejecuta una época de entrenamiento y devuelve la pérdida promedio."""
    model.train()
    running_loss = 0.0

    for images, labels in tqdm(loader, desc="Entrenando", leave=False):
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

    return running_loss / len(loader.dataset)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> tuple[float, np.ndarray, np.ndarray]:
    """Evalúa el modelo y devuelve (loss, predicciones, etiquetas reales)."""
    model.eval()
    criterion = nn.CrossEntropyLoss()
    running_loss = 0.0
    all_preds: list[int] = []
    all_labels: list[int] = []

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)

        all_preds.extend(preds.cpu().numpy().tolist())
        all_labels.extend(labels.cpu().numpy().tolist())

    return running_loss / len(loader.dataset), np.array(all_preds), np.array(all_labels)


# --------------------------------------------------------------------------- #
#  Gráficas y guardado
# --------------------------------------------------------------------------- #
def plot_history(history: dict, output_path: Path) -> None:
    """Guarda la gráfica de pérdida y exactitud por época."""
    epochs = range(1, len(history["train_loss"]) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    ax1.plot(epochs, history["train_loss"], label="Train")
    ax1.plot(epochs, history["val_loss"], label="Val")
    ax1.set_title("Pérdida (Loss)")
    ax1.set_xlabel("Época")
    ax1.set_ylabel("Loss")
    ax1.legend()

    ax2.plot(epochs, history["train_acc"], label="Train")
    ax2.plot(epochs, history["val_acc"], label="Val")
    ax2.set_title("Exactitud (Accuracy)")
    ax2.set_xlabel("Época")
    ax2.set_ylabel("Accuracy")
    ax2.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=120)
    plt.close(fig)


def plot_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, class_names: list[str], output_path: Path) -> None:
    """Guarda la matriz de confusión del conjunto de test."""
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.title("Matriz de confusión — Test")
    plt.xlabel("Predicción")
    plt.ylabel("Real")
    plt.tight_layout()
    plt.savefig(output_path, dpi=120)
    plt.close()


def save_checkpoint(
    model: nn.Module,
    arch: str,
    class_names: list[str],
    input_size: int,
    history: dict,
    metrics: dict,
    output_path: Path,
) -> None:
    """Guarda el modelo junto con la metadata necesaria para la inferencia."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = {
        "arch": arch,
        "class_names": class_names,
        "input_size": input_size,
        "state_dict": model.state_dict(),
        "train_history": history,
        "metrics": metrics,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    torch.save(checkpoint, output_path)
    print(f"[ok] Modelo guardado en {output_path}")


# --------------------------------------------------------------------------- #
#  Función principal
# --------------------------------------------------------------------------- #
def main() -> None:
    parser = argparse.ArgumentParser(description="Entrena el modelo de NutriLeaf.")
    parser.add_argument("--arch", type=str, default="resnet18",
                        choices=["resnet18", "resnet50", "mobilenet_v3_small", "efficientnet_b0"])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--input-size", type=int, default=224)
    parser.add_argument("--num-workers", type=int, default=0,
                        help="Hilos de carga de datos (0 evita problemas de spawn en Windows)")
    parser.add_argument("--device", type=str, default=None, help="'cuda' o 'cpu'")
    args = parser.parse_args()

    # ---- Dispositivo de cómputo ----
    device = torch.device(args.device or ("cuda" if torch.cuda.is_available() else "cpu"))
    print(f"[info] Dispositivo: {device}")
    if device.type == "cuda":
        print(f"[info] GPU: {torch.cuda.get_device_name(0)}")

    # ---- Datos ----
    train_loader, val_loader, test_loader, class_names = build_dataloaders(
        batch_size=args.batch_size,
        input_size=args.input_size,
        num_workers=args.num_workers,
    )
    print(f"[info] Clases: {class_names}")

    # ---- Modelo, loss y optimizador ----
    model = build_model(num_classes=len(class_names), arch=args.arch, pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    # ---- Bucle de entrenamiento ----
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val_acc = 0.0
    best_state = None

    for epoch in range(1, args.epochs + 1):
        print(f"\n=== Época {epoch}/{args.epochs} ===")
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device)

        # Métricas en entrenamiento y validación (una única pasada por conjunto).
        _, train_preds, train_labels = evaluate(model, train_loader, device)
        val_loss, val_preds, val_labels = evaluate(model, val_loader, device)

        train_acc = accuracy_score(train_labels, train_preds)
        val_acc = accuracy_score(val_labels, val_preds)

        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)

        print(
            f"  Train loss: {train_loss:.4f} | Val loss: {val_loss:.4f} | "
            f"Train acc: {train_acc:.4f} | Val acc: {val_acc:.4f}"
        )

        # Guarda el mejor modelo según exactitud de validación.
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            print(f"  * Nueva mejor exactitud de validación: {val_acc:.4f}")

    # ---- Evaluación final en test ----
    model.load_state_dict(best_state)
    _, test_preds, test_labels = evaluate(model, test_loader, device)
    test_acc = accuracy_score(test_labels, test_preds)
    report = classification_report(test_labels, test_preds, target_names=class_names, output_dict=True)

    print("\n=== Resultados en Test ===")
    print(classification_report(test_labels, test_preds, target_names=class_names))
    print(f"Exactitud en test: {test_acc:.4f}")

    # ---- Guardado de artefactos ----
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    plot_history(history, PLOTS_DIR / "training_history.png")
    plot_confusion_matrix(test_labels, test_preds, class_names, PLOTS_DIR / "confusion_matrix.png")

    metrics = {"test_accuracy": test_acc, "classification_report": report}
    with open(REPORTS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    save_checkpoint(
        model=model,
        arch=args.arch,
        class_names=class_names,
        input_size=args.input_size,
        history=history,
        metrics=metrics,
        output_path=MODELS_DIR / "leaf_classifier.pt",
    )

    print("\n[ok] Entrenamiento finalizado.")


if __name__ == "__main__":
    main()
