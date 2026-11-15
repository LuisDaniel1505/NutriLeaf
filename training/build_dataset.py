"""Construye el dataset combinado de NutriLeaf a partir de varias fuentes.

Fuentes de imágenes
-------------------
1. ``data/raw/`` — *Maize Nutrient Deficiency Dataset* (5 clases: healthy,
   magnesium, nitrogen, phosphorus, potassium).
2. ``data/external/hf/`` — *Corn Leaf Diseases, Pests and Deficiencies*
   (proyecto Doctor Maíz, Hugging Face), que aporta fotos **de campo real** de
   fósforo, nitrógeno, potasio y sanas.

Mapeo del dataset HF a las clases canónicas
-------------------------------------------
- ``phosphorus_deficiency`` -> ``phosphorus``
- ``nitrogen_deficiency``   -> ``nitrogen``
- ``potassium_deficiency``  -> ``potassium``
- ``healthy``               -> ``healthy`` (se limita a una muestra)

Las clases de enfermedades y plagas no se incluyen (se descartaron al extraer).

Metodología de división
-----------------------
Las imágenes del dataset HF se añaden **solo al conjunto de entrenamiento**. Los
conjuntos de validación y test se mantienen con las imágenes originales de campo
del dataset base, de modo que la evaluación mida la generalización real.

Uso (desde la raíz del proyecto)::

    python -m training.build_dataset
"""
from __future__ import annotations

import random
import shutil
from collections import defaultdict
from pathlib import Path

from sklearn.model_selection import train_test_split

from app.config import DATA_DIR, PROCESSED_DIR, RAW_DIR
from app.labels import CLASS_NAMES, DATASET_FOLDER_MAP

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

# Ruta del dataset HF ya extraído.
HF_DIR = DATA_DIR / "external" / "hf" / "extracted"

# Mapeo de las carpetas del dataset HF a clases canónicas.
HF_MAP = {
    "phosphorus_deficiency": "phosphorus",
    "nitrogen_deficiency": "nitrogen",
    "potassium_deficiency": "potassium",
    "healthy": "healthy",
}

# Límite de imágenes "healthy" del dataset HF (la clase sana es muy numerosa).
HEALTHY_LIMIT = 2000
SEED = 42


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


def collect_hf() -> dict[str, list[Path]]:
    """Recorre ``data/external/hf`` y mapea sus clases de deficiencias.

    La estructura es ``<clase>/<entorno>/<archivo>``, donde ``entorno`` es
    ``real`` (campo) o ``lab``; se conservan ambos. La clase ``healthy`` se
    limita a una muestra para no desbalancear el dataset.
    """
    images: dict[str, list[Path]] = defaultdict(list)
    if not HF_DIR.exists():
        return dict(images)

    for path in sorted(HF_DIR.rglob("*")):
        if not _is_image(path):
            continue
        # El padre del archivo es el entorno y su padre es la clase.
        cls = HF_MAP.get(path.parent.parent.name.lower())
        if cls is not None:
            images[cls].append(path)

    # Limitar la clase "healthy" a una muestra reproducible.
    if len(images.get("healthy", [])) > HEALTHY_LIMIT:
        rng = random.Random(SEED)
        images["healthy"] = rng.sample(images["healthy"], HEALTHY_LIMIT)

    return dict(images)


def _copy_split(paths: list[Path], dest: Path) -> None:
    """Copia una lista de imágenes a un directorio, con nombres únicos."""
    dest.mkdir(parents=True, exist_ok=True)
    for p in paths:
        shutil.copy2(p, dest / f"{p.parent.parent.name}_{p.name}")


def main() -> None:
    base = collect_base()
    hf = collect_hf()

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    for cls in CLASS_NAMES:
        base_paths = base.get(cls, [])
        hf_paths = hf.get(cls, [])

        # División del dataset base (campo) en train/val/test.
        base_rest, base_test = train_test_split(base_paths, test_size=0.15, random_state=SEED)
        base_train, base_val = train_test_split(
            base_rest, test_size=0.15 / 0.85, random_state=SEED
        )

        # El dataset HF se añade íntegramente al entrenamiento (val/test limpios).
        train = base_train + hf_paths
        val = base_val
        test = base_test

        for split, paths in (("train", train), ("val", val), ("test", test)):
            _copy_split(paths, PROCESSED_DIR / split / cls)

        print(f"[info] {cls}: {len(train)} train, {len(val)} val, {len(test)} test")

    print(f"[ok] Dataset combinado listo en {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
