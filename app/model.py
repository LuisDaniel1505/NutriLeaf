"""Definición de la arquitectura del modelo y de la clase de inferencia.

Usa PyTorch + torchvision con una red convolucional preentrenada (por defecto
ResNet18) a la que se le reemplaza la última capa para las 5 clases de NutriLeaf.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
from PIL import Image
from torchvision import transforms

from .labels import CLASS_LABELS_ES, CLASS_NAMES
from .recommendations import RECOMMENDATIONS

# Media y desviación estándar de ImageNet (necesarias porque usamos pesos preentrenados)
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# --------------------------------------------------------------------------- #
#  Arquitectura del modelo
# --------------------------------------------------------------------------- #
def build_model(num_classes: int = 5, arch: str = "resnet18", pretrained: bool = True) -> nn.Module:
    """Construye una CNN con base preentrenada y clasificador ajustado a `num_classes`.

    Args:
        num_classes: Número de clases de salida (5 para NutriLeaf).
        arch: Arquitectura base: "resnet18", "resnet50", "mobilenet_v3_small" o "efficientnet_b0".
        pretrained: Si se cargan pesos preentrenados de ImageNet.
    """
    arch = arch.lower()

    if arch == "resnet18":
        weights = models.ResNet18_Weights.DEFAULT if pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)

    elif arch == "resnet50":
        weights = models.ResNet50_Weights.DEFAULT if pretrained else None
        model = models.resnet50(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)

    elif arch == "mobilenet_v3_small":
        weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
        model = models.mobilenet_v3_small(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    elif arch == "efficientnet_b0":
        weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    else:
        raise ValueError(f"Arquitectura no soportada: {arch}")

    return model


def build_inference_transform(input_size: int = 224) -> transforms.Compose:
    """Transform de preprocesado para inferencia (redimensionar + normalizar)."""
    return transforms.Compose(
        [
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


# --------------------------------------------------------------------------- #
#  Clase de inferencia
# --------------------------------------------------------------------------- #
class LeafClassifier:
    """Carga un modelo entrenado y devuelve predicciones con confianza y recomendación."""

    def __init__(self, model_path: Path, device: str | None = None):
        if not Path(model_path).exists():
            raise FileNotFoundError(
                f"No se encontró el modelo entrenado en: {model_path}. "
                "Ejecuta primero el entrenamiento (training/train.py)."
            )

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # weights_only=False permite cargar el checkpoint completo (arch, clases, etc.)
        checkpoint = torch.load(str(model_path), map_location=self.device, weights_only=False)

        self.arch = checkpoint.get("arch", "resnet18")
        self.class_names: List[str] = checkpoint.get("class_names", CLASS_NAMES)
        self.input_size: int = checkpoint.get("input_size", 224)

        self.model = build_model(num_classes=len(self.class_names), arch=self.arch, pretrained=False)
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.to(self.device)
        self.model.eval()

        self.transform = build_inference_transform(self.input_size)
        self.softmax = nn.Softmax(dim=1)

    @torch.no_grad()
    def predict(self, image: Image.Image) -> Dict[str, Any]:
        """Predice la clase de una imagen PIL y devuelve un dict con el resultado."""
        image = image.convert("RGB")
        x = self.transform(image).unsqueeze(0).to(self.device)

        logits = self.model(x)
        probs = self.softmax(logits).cpu().numpy()[0]

        idx = int(probs.argmax())
        class_name = self.class_names[idx]
        confidence = float(probs[idx])

        probabilities = {
            self.class_names[i]: float(probs[i]) for i in range(len(self.class_names))
        }

        return {
            "class": class_name,
            "class_index": idx,
            "label_es": CLASS_LABELS_ES.get(class_name, class_name),
            "confidence": confidence,
            "probabilities": probabilities,
            "recommendation": RECOMMENDATIONS.get(class_name, {}),
        }
