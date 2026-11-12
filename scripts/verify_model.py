"""Verifica el modelo entrenado evaluándolo sobre el conjunto de test.

Carga el modelo desde ``models/leaf_classifier.pt``, evalúa cada imagen del
conjunto de test y muestra la exactitud total y por clase.

Uso (desde la raíz del proyecto)::

    python scripts/verify_model.py
"""
import sys
from pathlib import Path

# Permite importar el paquete `app` aunque el script se ejecute directamente.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from app.config import MODEL_PATH, PROCESSED_DIR
from app.model import LeafClassifier

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def main() -> None:
    if not MODEL_PATH.exists():
        raise SystemExit(
            f"[error] No se encontró el modelo en {MODEL_PATH}. "
            "Ejecuta `python -m training.train` primero."
        )

    test_dir = PROCESSED_DIR / "test"
    if not test_dir.exists():
        raise SystemExit(
            f"[error] No existe el conjunto de test en {test_dir}. "
            "Ejecuta `python -m training.preprocess` primero."
        )

    print(f"[info] Cargando modelo desde {MODEL_PATH} ...")
    clf = LeafClassifier(MODEL_PATH)
    print(f"[info] Dispositivo de inferencia: {clf.device}")

    correct = 0
    total = 0
    per_class: dict[str, tuple[int, int]] = {}

    for class_dir in sorted(test_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        clase = class_dir.name
        aciertos = 0
        n = 0
        for img_path in class_dir.glob("*"):
            if img_path.suffix.lower() not in IMG_EXTS:
                continue
            imagen = Image.open(img_path).convert("RGB")
            resultado = clf.predict(imagen)
            n += 1
            if resultado["class"] == clase:
                aciertos += 1
        per_class[clase] = (aciertos, n)
        total += n
        correct += aciertos

    print("\n=== Resultado de la verificación ===")
    for clase in sorted(per_class):
        ok, n = per_class[clase]
        print(f"  {clase:<12} {ok}/{n}")
    if total:
        print(f"\nExactitud total: {correct}/{total} = {correct / total:.2%}")


if __name__ == "__main__":
    main()
