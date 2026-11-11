"""Preparación del dataset para entrenamiento.

Pasos:
  1. Localiza y extrae el dataset crudo (Maize Nutrient Deficiency Dataset.zip).
  2. Normaliza los nombres de las clases (carpetas) al orden canónico.
  3. Divide las imágenes en train / val / test de forma estratificada.

Uso (desde la raíz del proyecto):
    python -m training.preprocess
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path

from sklearn.model_selection import train_test_split

from app.config import DATASETS_DIR, PROCESSED_DIR, RAW_DIR
from app.labels import CLASS_NAMES, DATASET_FOLDER_MAP

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def find_dataset_zip() -> Path | None:
    """Busca el zip del dataset de 5 clases en las ubicaciones conocidas."""
    candidates = list(DATASETS_DIR.glob("*.zip")) + list(DATA_DIR.glob("*.zip"))
    for path in candidates:
        if "maize" in path.name.lower() or "nutrient" in path.name.lower():
            return path
    # Si no hay coincidencia por nombre, devuelve el primero que encuentre.
    return candidates[0] if candidates else None


def extract_zip(zip_path: Path) -> None:
    """Extrae el zip en data/raw (sin sobreescribir si ya existe)."""
    if RAW_DIR.exists() and any(RAW_DIR.rglob("*")):
        print(f"[info] {RAW_DIR} ya contiene datos; se omite la extracción.")
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[info] Extrayendo {zip_path.name} ...")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(RAW_DIR)
    print("[info] Extracción completada.")


def collect_images() -> dict[str, list[Path]]:
    """Recorre data/raw y agrupa las imágenes por clase canónica."""
    images: dict[str, list[Path]] = {c: [] for c in CLASS_NAMES}
    for path in sorted(RAW_DIR.rglob("*")):
        if path.suffix.lower() not in IMG_EXTS:
            continue
        folder = path.parent.name.lower()
        cls = DATASET_FOLDER_MAP.get(folder)
        if cls is None:
            print(f"[warn] Clase desconocida para carpeta '{path.parent.name}'; se omite.")
            continue
        images[cls].append(path)
    return images


def build_split(
    images: dict[str, list[Path]],
    val_size: float = 0.15,
    test_size: float = 0.15,
    seed: int = 42,
) -> None:
    """Crea la estructura data/processed/{train,val,test}/<clase>/."""
    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    for cls in CLASS_NAMES:
        if not images[cls]:
            print(f"[warn] No hay imágenes para la clase '{cls}'.")
            continue
        rest, test = train_test_split(
            images[cls], test_size=test_size, random_state=seed, stratify=None
        )
        # val_size relativo al total original
        train, val = train_test_split(
            rest, test_size=val_size / (1 - test_size), random_state=seed
        )
        for split, paths in (("train", train), ("val", val), ("test", test)):
            dest_dir = PROCESSED_DIR / split / cls
            dest_dir.mkdir(parents=True, exist_ok=True)
            for p in paths:
                shutil.copy2(p, dest_dir / p.name)
        print(f"[info] {cls}: {len(train)} train, {len(val)} val, {len(test)} test")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepara el dataset de NutriLeaf.")
    parser.add_argument("--zip", type=Path, default=None, help="Ruta al zip del dataset.")
    parser.add_argument("--val-size", type=float, default=0.15)
    parser.add_argument("--test-size", type=float, default=0.15)
    args = parser.parse_args()

    zip_path = args.zip or find_dataset_zip()
    if zip_path is None or not zip_path.exists():
        raise SystemExit(
            "[error] No se encontró el zip del dataset. "
            "Colócalo en 'Datasets/' o pásalo con --zip."
        )

    extract_zip(zip_path)
    images = collect_images()

    total = sum(len(v) for v in images.values())
    if total == 0:
        raise SystemExit("[error] No se encontraron imágenes tras la extracción.")
    print(f"[info] Total de imágenes encontradas: {total}")
    for cls in CLASS_NAMES:
        print(f"  - {cls}: {len(images[cls])}")

    build_split(images, val_size=args.val_size, test_size=args.test_size, seed=42)
    print(f"[ok] Dataset listo en {PROCESSED_DIR}")


if __name__ == "__main__":
    main()
