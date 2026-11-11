"""Etiquetas de las clases que detecta NutriLeaf.

Orden canónico usado en todo el proyecto (entrenamiento e inferencia).
"""

# Orden canónico de las clases (el índice corresponde a la salida del modelo)
CLASS_NAMES = [
    "healthy",       # 0
    "nitrogen",      # 1
    "phosphorus",    # 2
    "potassium",     # 3
    "magnesium",     # 4
]

# Nombre legible en español para la interfaz
CLASS_LABELS_ES = {
    "healthy": "Planta saludable",
    "nitrogen": "Deficiencia de Nitrógeno (N)",
    "phosphorus": "Deficiencia de Fósforo (P)",
    "potassium": "Deficiencia de Potasio (K)",
    "magnesium": "Deficiencia de Magnesio (Mg)",
}

# Símbolo químico corto para mostrar junto al nombre
CLASS_SYMBOLS = {
    "healthy": "OK",
    "nitrogen": "N",
    "phosphorus": "P",
    "potassium": "K",
    "magnesium": "Mg",
}

CLASS_TO_IDX = {name: i for i, name in enumerate(CLASS_NAMES)}
IDX_TO_CLASS = {i: name for i, name in enumerate(CLASS_NAMES)}

# Mapeo de los nombres de carpetas del dataset original -> nombre canónico.
# El dataset usa nombres con errores de escritura ("Helathy", "Pottasium", etc.)
DATASET_FOLDER_MAP = {
    "helathy": "healthy",
    "healthy": "healthy",
    "nitrogen": "nitrogen",
    "phosphorous": "phosphorus",
    "phosphorus": "phosphorus",
    "pottasium": "potassium",
    "potassium": "potassium",
    "magnessium": "magnesium",
    "magnesium": "magnesium",
}
