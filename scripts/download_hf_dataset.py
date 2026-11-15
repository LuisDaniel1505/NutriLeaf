"""Descarga y extrae el dataset de maíz de Hugging Face (proyecto Doctor Maíz).

Descarga los shards del dataset ``daiv05/corn-leaf-diseases-pests-and-deficiencies``
y extrae únicamente las clases de deficiencias nutricionales que interesan a
NutriLeaf:

- ``phosphorus_deficiency`` -> fósforo
- ``nitrogen_deficiency``   -> nitrógeno
- ``potassium_deficiency``  -> potasio
- ``healthy``               -> sano

Las clases de enfermedades y plagas se descartan para ahorrar espacio en disco.

Uso (desde la raíz del proyecto)::

    python scripts/download_hf_dataset.py
"""
from __future__ import annotations

import tarfile
from pathlib import Path

from huggingface_hub import snapshot_download

REPO_ID = "daiv05/corn-leaf-diseases-pests-and-deficiencies"
DEST = Path("data/external/hf")

# Clases que se conservan (el resto — enfermedades y plagas — se descarta).
TARGET_CLASSES = {
    "phosphorus_deficiency",
    "nitrogen_deficiency",
    "potassium_deficiency",
    "healthy",
}


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)

    print(f"[info] Descargando {REPO_ID} ... (puede tardar, ~19 GB)")
    snapshot_download(repo_id=REPO_ID, repo_type="dataset", local_dir=str(DEST))

    extracted = DEST / "extracted"
    extracted.mkdir(parents=True, exist_ok=True)

    print("[info] Extrayendo clases de interés ...")
    for tar_path in sorted(DEST.glob("clean-*.tar")):
        print(f"  - {tar_path.name}")
        with tarfile.open(tar_path) as tf:
            for member in tf.getmembers():
                parts = member.name.split("/")
                if len(parts) >= 3 and parts[0] in TARGET_CLASSES:
                    tf.extract(member, extracted)
        # Se elimina el shard tras extraer para liberar espacio.
        tar_path.unlink()

    print("[info] Conteo final:")
    total = 0
    for cls in sorted(TARGET_CLASSES):
        cls_dir = extracted / cls
        n = sum(1 for _ in cls_dir.rglob("*")) if cls_dir.exists() else 0
        total += n
        print(f"  {cls}: {n}")
    print(f"[ok] Extraídas {total} imágenes en {extracted}")


if __name__ == "__main__":
    main()
