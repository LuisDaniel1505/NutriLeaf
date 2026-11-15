"""Construye el dataset combinado de NutriLeaf a partir de varias fuentes.

Fuentes de imágenes
-------------------
1. ``data/raw/`` — *Maize Nutrient Deficiency Dataset* (5 clases: healthy,
   magnesium, nitrogen, phosphorus, potassium).
2. ``data/external/kaggle/`` — *Maize Plant Leaf Nutrient Deficiency Dataset*
   (Kaggle, ~17.6K imágenes), que aporta más ejemplos de fósforo, potasio,
   nitrógeno y sanas.

Mapeo del dataset de Kaggle a las clases canónicas
--------------------------------------------------
- ``PAB``          -> ``phosphorus`` (fósforo ausente).
- ``KAB``          -> ``potassium``  (potasio ausente).
- ``NAB``          -> ``nitrogen``   (nitrógeno ausente).
- ``ALL Present``  -> ``healthy``    (todos los nutrientes presentes).
- ``ALLAB`` y ``ZNAB`` -> se **omiten** (deficiencia total y de zinc, que no
  están en el modelo de 5 clases).

Metodología de división
-----------------------
Las imágenes de Kaggle se añaden **solo al conjunto de entrenamiento**. Los
conjuntos de validación y test se mantienen con las imágenes originales de
campo, de modo que la evaluación mida la generalización real del modelo.

Uso (desde la raíz del proyecto)::

    python -m training.build_dataset
"""
from __future__ import annotations

import shutil
from collections import defaultdict
from pathlib import Path

from sklearn.model_selection import train_test_split

from app.config import DATA_DIR, PROCESSED_DIR, RAW_DIR
from app.labels import CLASS_NAMES, DATASET_FOLDER_MAP

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

# Ruta del dataset de Kaggle ya extraído.
KAGGLE_DIR = DATA_DIR / "external" / "kaggle" / "Nutrition_dataset"

# Mapeo de las carpetas del dataset de Kaggle a clases canónicas.
KAGGLE_MAP = {
    "all present": "healthy",
    "nab": "nitrogen",
    "pab": "phosphorus",
    "kab": "potassium",
}


def _is_image(path: Path) -> bool:
    return path.suffix.lower() in IMG_EXTS


def collect_base() -> dict[str, list[Path]]:
    """Recorre ``data/raw`` y agrupa las imágenes por clase canónica."""
    images: dict[str, list[Path]] = {c: [] for c in CLASS_NAMES}
    for path in sorted(RAW_DIR.rglob("*")):
        if not _is_image(path):
            continue
        cls = DATASET_FOLDER_MAP.get(path.parent.name.lower())
        if cls is None:
            continue
        images[cls].append(path)
    return images


def collect_kaggle() -> dict[str, list[Path]]:
    """Recorre el subconjunto ``train`` de Kaggle y mapea sus clases.

    Se omiten las clases ``ALLAB`` (deficiencia total) y ``ZNAB`` (zinc).
    """
    images: dict[str, list[Path]] = defaultdict(list)
    kaggle_train = KAGGLE_DIR / "train"
    if not kaggle_train.exists():
        return dict(images)
    for path in sorted(kaggle_train.rglob("*")):
        if not _is_image(path):
            continue
        cls = KAGGLE_MAP.get(path.parent.name.lower())
        if cls is not None:
            images[cls].append(path)
    return dict(images)


def _copy_split(paths: list[Path], dest: Path) -> None:
    """Copia una lista de imágenes a un directorio, con nombres únicos."""
    dest.mkdir(parents=True, exist_ok=True)
    for p in paths:
        shutil.copy2(p, dest / f"{p.parent.name}_{p.name}")


def main() -> None:
    base = collect_base()
    kaggle = collect_kaggle()

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    for cls in CLASS_NAMES:
        base_paths = base.get(cls, [])
        kaggle_paths = kaggle.get(cls, [])

        # División del dataset base (campo) en train/val/test.
        base_rest, base_test = train_test_split(base_paths, test_size=0.15, random_state=42)
        base_train, base_val = train_test_split(
            base_rest, test_size=0.15 / 0.85, random_state=42
        )

        # Kaggle se añade íntegramente al entrenamiento (val/test permanecen limpios).
        train = base_train + kaggle_paths
        val = base_val
        test = base_test

        for split, paths in (("train", train), ("val", val), ("test", test)):
            _copy_split(paths, PROCESSED_DIR / split / cls)

        print(f"[info] {cls}: {len(train)} train, {len(val)} val, {len(test)} test")

    print(f"[ok] Dataset combinado listo en {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
