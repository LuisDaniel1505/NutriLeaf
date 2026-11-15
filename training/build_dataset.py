"""Construye el dataset combinado de NutriLeaf a partir de varias fuentes.

Fuentes de imágenes
-------------------
1. ``data/raw/`` — *Maize Nutrient Deficiency Dataset* (5 clases: healthy,
   magnesium, nitrogen, phosphorus, potassium).
2. ``data/external/mpls/`` — *Maize Phosphorus Leaf Deficiency (MPLD)*
   (Zenodo, CC BY 4.0), que aporta imágenes de fósforo y de plantas sanas.

Mapeo del dataset MPLD a las clases canónicas
---------------------------------------------
- ``-P``  -> ``phosphorus`` (ausencia total de fósforo).
- ``_C`` / ``-C`` -> ``healthy`` (control, suministro completo).
- ``-P50`` -> se **omite** (deficiencia parcial, ambigua entre sano y deficiente).
- Se descartan las imágenes con el sufijo ``EMPTY`` (sin contenido de hoja).

Metodología de división
-----------------------
Las imágenes de MPLD se añaden **solo al conjunto de entrenamiento**. Los
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

# Ruta de los datos externos (MPLD — fósforo).
MPLS_DIR = DATA_DIR / "external" / "mpls"

# Mapeo de las carpetas del dataset MPLD a clases canónicas.
MPLS_MAP = {
    "-p": "phosphorus",
    "_p": "phosphorus",
    "-c": "healthy",
    "_c": "healthy",
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


def collect_mpls() -> dict[str, list[Path]]:
    """Recorre ``data/external/mpls`` y extrae fósforo y plantas sanas.

    Se omiten las imágenes ``EMPTY`` y la clase ``-P50`` (deficiencia parcial).
    """
    images: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(MPLS_DIR.rglob("*")):
        if not _is_image(path):
            continue
        if "empty" in path.stem.lower():
            continue
        folder = path.parent.name.lower()
        if "p50" in folder:
            continue
        cls = MPLS_MAP.get(folder)
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
    mpls = collect_mpls()

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    for cls in CLASS_NAMES:
        base_paths = base.get(cls, [])
        mpls_paths = mpls.get(cls, [])

        # División del dataset base (campo) en train/val/test.
        base_rest, base_test = train_test_split(base_paths, test_size=0.15, random_state=42)
        base_train, base_val = train_test_split(
            base_rest, test_size=0.15 / 0.85, random_state=42
        )

        # MPLD se añade íntegramente al entrenamiento (val/test permanecen limpios).
        train = base_train + mpls_paths
        val = base_val
        test = base_test

        for split, paths in (("train", train), ("val", val), ("test", test)):
            _copy_split(paths, PROCESSED_DIR / split / cls)

        print(f"[info] {cls}: {len(train)} train, {len(val)} val, {len(test)} test")

    print(f"[ok] Dataset combinado listo en {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
