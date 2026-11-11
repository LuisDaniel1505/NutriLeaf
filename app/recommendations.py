"""Recomendaciones agronómicas mostradas al usuario según la deficiencia detectada.

El contenido está pensado para un público no especializado (agricultores,
estudiantes y personas interesadas en el cuidado de plantas), tal como
define el documento de NutriLeaf.
"""

RECOMMENDATIONS = {
    "healthy": {
        "short": "Sin deficiencias detectadas",
        "detail": (
            "La hoja no presenta señales visibles de las deficiencias que analiza "
            "NutriLeaf. Continúa con el monitoreo regular del cultivo para detectar "
            "cambios a tiempo."
        ),
        "actions": [
            "Mantener el plan de fertilización actual.",
            "Revisar el cultivo de forma periódica (semanal).",
            "Regar de forma adecuada según la etapa de la planta.",
        ],
    },
    "nitrogen": {
        "short": "Deficiencia de Nitrógeno (N)",
        "detail": (
            "El amarillamiento en forma de 'V' que inicia en la punta de la hoja y "
            "avanza hacia la base es el síntoma típico de falta de nitrógeno. El "
            "nitrógeno es clave para el crecimiento y el color verde de la planta."
        ),
        "actions": [
            "Aplicar fertilizante nitrogenado (urea o sulfato de amonio).",
            "Incorporar materia orgánica o compost al suelo.",
            "Evitar el exceso de agua, que puede lavar el nitrógeno del suelo.",
        ],
    },
    "phosphorus": {
        "short": "Deficiencia de Fósforo (P)",
        "detail": (
            "Las tonalidades moradas o rojizas en algunas partes de la hoja sugieren "
            "falta de fósforo, nutriente esencial para el desarrollo de raíces y la "
            "transferencia de energía."
        ),
        "actions": [
            "Aplicar fertilizante fosfatado (superfosfato o DAP) cerca de la raíz.",
            "Considerar que en suelos fríos el fósforo se absorbe con dificultad.",
            "Verificar el pH del suelo; un pH extremo limita la disponibilidad de fósforo.",
        ],
    },
    "potassium": {
        "short": "Deficiencia de Potasio (K)",
        "detail": (
            "El amarillamiento y las zonas secas, especialmente en los bordes de las "
            "hojas, indican falta de potasio. Este nutriente regula el agua y la "
            "resistencia de la planta."
        ),
        "actions": [
            "Aplicar cloruro o sulfato de potasio.",
            "Evitar el exceso de nitrógeno, que puede agravar la deficiencia.",
            "Mantener un riego regular, ya que el potasio se absorbe con agua.",
        ],
    },
    "magnesium": {
        "short": "Deficiencia de Magnesio (Mg)",
        "detail": (
            "Las zonas amarillas entre las nervaduras de las hojas son un signo de falta "
            "de magnesio, nutriente central en la clorofila y la fotosíntesis."
        ),
        "actions": [
            "Aplicar sulfato de magnesio (sales de Epsom) vía foliar o al suelo.",
            "Incorporar dolomita si el suelo además es ácido.",
            "Evitar excesos de potasio y calcio, que compiten con el magnesio.",
        ],
    },
}
