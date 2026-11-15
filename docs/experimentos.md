# Experimentos y comparativa del modelo

> Documento que registra los experimentos de entrenamiento realizados para
> elegir el mejor modelo de NutriLeaf.

---

## Configuración común

- **Dataset:** 463 imágenes de hojas de maíz, 5 clases (dividido 70/15/15).
- **Épocas:** 20 · **Batch:** 32 · **Optimizador:** Adam (lr 1e-4).
- **Aumentación:** flip horizontal, rotación y ajuste de brillo/contraste.
- **Balanceo de muestreo:** `WeightedRandomSampler`.
- **Evaluación:** conjunto de test (71 imágenes no vistas durante el entrenamiento).

## Comparativa

| # | Arquitectura | Pesos por clase | Val acc | Test acc | F1 macro | F1 Potasio |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ResNet18 | ❌ | 0.958 | 0.8732 | 0.86 | 0.71 |
| 2 | **ResNet18** | ✅ | **0.972** | **0.9014** | **0.89** | 0.75 |
| 3 | EfficientNet-B0 | ✅ | 0.916 | 0.8873 | 0.88 | **0.86** |

## Detalle por clase del modelo final (experimento 2)

| Clase | Precisión | Recall | F1 |
| --- | --- | --- | --- |
| healthy | 0.91 | 0.91 | 0.91 |
| magnesium | 0.82 | 0.95 | 0.88 |
| nitrogen | 0.93 | 0.93 | 0.93 |
| phosphorus | 1.00 | 0.94 | 0.97 |
| potassium | 0.86 | 0.67 | 0.75 |

## Conclusiones

1. **Los pesos por clase mejoran el resultado.** Añadir pesos inversamente
   proporcionales a la frecuencia de cada clase subió la exactitud de test de
   **87.32 % → 90.14 %** y el F1 de Potasio de **0.71 → 0.75**.

2. **ResNet18 gana en exactitud global.** EfficientNet-B0 mejoró el recall de
   Potasio (0.86), pero a costa de empeorar otras clases (healthy 0.82 recall,
   nitrogen 0.80), por lo que su exactitud global fue menor (88.73 %).

3. **Modelo elegido: ResNet18 + pesos por clase** (exactitud de test 90.14 %).
   Se guarda como el modelo definitivo en `models/leaf_classifier.pt`.

## Cómo reproducir los experimentos

```bash
# Experimento 2 (modelo elegido)
python -m training.train --arch resnet18 --epochs 20 --output models/leaf_classifier.pt

# Experimento 3 (comparación)
python -m training.train --arch efficientnet_b0 --epochs 20 --output models/efficientnet_b0.pt
```

> **Limitación conocida:** Potasio sigue siendo la clase con menor F1 (0.75) por
> tener solo 56 imágenes en el dataset y confundirse con Magnesio (ambas causan
> amarillamiento). Se podría mejorar añadiendo más imágenes de esa clase.
