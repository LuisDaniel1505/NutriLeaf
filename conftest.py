"""Configuración global de pytest.

Añade la raíz del proyecto a ``sys.path`` para que los tests puedan importar
los paquetes ``app`` y ``training`` sin necesidad de instalar el proyecto.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
