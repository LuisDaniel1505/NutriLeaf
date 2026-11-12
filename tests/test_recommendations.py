"""Pruebas unitarias del módulo ``app.recommendations``.

Verifican que cada una de las 5 clases tenga una recomendación completa
(título corto, descripción y lista de acciones).
"""
from app.labels import CLASS_NAMES
from app.recommendations import RECOMMENDATIONS


def test_toda_clase_tiene_recomendacion() -> None:
    """No debe faltar ninguna recomendación para las 5 clases."""
    for clase in CLASS_NAMES:
        assert clase in RECOMMENDATIONS, f"Falta recomendación para '{clase}'"


def test_recomendacion_tiene_campos_obligatorios() -> None:
    """Cada recomendación debe tener 'short', 'detail' y 'actions' no vacíos."""
    for clase, rec in RECOMMENDATIONS.items():
        assert rec["short"], f"Falta 'short' en '{clase}'"
        assert rec["detail"], f"Falta 'detail' en '{clase}'"
        assert isinstance(rec["actions"], list), f"'actions' debe ser lista en '{clase}'"
        assert len(rec["actions"]) > 0, f"Sin acciones en '{clase}'"
