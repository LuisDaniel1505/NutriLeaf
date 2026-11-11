"""Configuración y rutas globales del proyecto NutriLeaf."""
from pathlib import Path

# Raíz del proyecto (carpeta NutriLeaf/)
ROOT_DIR = Path(__file__).resolve().parent.parent

# Directorios principales
APP_DIR = ROOT_DIR / "app"
STATIC_DIR = ROOT_DIR / "static"
MODELS_DIR = ROOT_DIR / "models"
DATA_DIR = ROOT_DIR / "data"
TRAINING_DIR = ROOT_DIR / "training"

# Datasets crudos (carpeta hermana "Datasets" dentro de EncuentroSistemas)
DATASETS_DIR = ROOT_DIR.parent / "Datasets"

# Datos extraídos y procesados (no versionados en git)
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Modelo entrenado
MODEL_PATH = MODELS_DIR / "leaf_classifier.pt"

# Tamaño de entrada por defecto (ImageNet)
DEFAULT_INPUT_SIZE = 224
