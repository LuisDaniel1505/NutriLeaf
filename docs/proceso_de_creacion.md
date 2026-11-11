# Proceso de creación de NutriLeaf

> Documento que describe, paso a paso, cómo se creó el proyecto y cómo
> funciona cada una de sus partes importantes. Sirve como guía de referencia
> para el equipo y como base para explicar el proyecto.

---

## 1. Contexto y objetivo

**NutriLeaf** identifica deficiencias nutricionales en hojas de maíz a partir
de fotografías. El sistema analiza una imagen (o un video en tiempo real) y
responde con:

1. La **deficiencia detectada** (o "planta saludable").
2. El **porcentaje de confianza** del modelo.
3. Una **recomendación** práctica para corregir la deficiencia.

El problema de fondo: a simple vista es difícil saber qué nutriente le falta a
una planta, porque varias deficiencias producen síntomas parecidos (amarillamiento,
manchas, bordes secos). Un modelo de aprendizaje automático aprende a distinguir
esos patrones a partir de ejemplos etiquetados.

---

## 2. Decisiones de arquitectura

### 2.1. ¿Por qué PyTorch y no TensorFlow?

La elección inicial fue TensorFlow/Keras, pero se descartó por una limitación
técnica importante:

> TensorFlow **no ofrece soporte de GPU en Windows nativo** desde la versión 2.11.
> La única versión con GPU (2.10) es incompatible con Python 3.11.

**PyTorch**, en cambio, instala soporte CUDA directamente en Windows con un solo
comando (`pip install torch`), aprovechando la GPU sin configuraciones extra.
Además es 100 % Python y está ampliamente usado en visión por computadora.

### 2.2. ¿Por qué transfer learning?

Entrenar una red neuronal **desde cero** requiere millones de imágenes. El dataset
de NutriLeaf tiene ~463 imágenes, lo cual es poco.

**Transfer learning** resuelve esto: se toma una red ya entrenada con millones de
imágenes (ImageNet) y se **reutiliza su conocimiento** sobre formas, bordes,
texturas y colores. Solo se re-entrena la última capa para las 5 clases nuevas.

### 2.3. ¿Por qué ResNet18?

- Es ligera y rápida (ideal para una GPU como la RTX 4050).
- Ofrece un buen equilibrio entre precisión y costo de cómputo.
- Viene preentrenada en `torchvision` (fácil de usar).

> El proyecto permite cambiar de arquitectura (`resnet50`, `mobilenet_v3_small`,
> `efficientnet_b0`) con el argumento `--arch`.

---

## 3. Estructura del proyecto (paso a paso de creación)

1. Se inicializó el repositorio Git (`git init -b main`) y se conectó a GitHub.
2. Se definió la separación por responsabilidades:

| Carpeta | Responsabilidad |
| --- | --- |
| `app/` | Backend (API) y lógica de inferencia |
| `training/` | Preparación de datos y entrenamiento |
| `static/` | Interfaz web (HTML/CSS/JS) |
| `models/` | Modelo entrenado (no versionado) |
| `data/` | Dataset (no versionado) |
| `docs/` | Documentación |

3. Se crearon los módulos con documentación completa (docstrings, type hints).
4. Se configuró `.gitignore` para **no** versionar datos ni modelos (son grandes
   y no son código).

---

## 4. Preparación de datos (`training/preprocess.py`)

El dataset crudo (`Maize Nutrient Deficiency Dataset.zip`) contiene 5 carpetas
con nombres que incluyen errores de escritura. El script:

1. **Localiza y extrae** el zip en `data/raw/`.
2. **Normaliza los nombres** de las clases mediante `DATASET_FOLDER_MAP`:

   | Carpeta original | Clase canónica |
   | --- | --- |
   | `Helathy` | `healthy` |
   | `Nitrogen` | `nitrogen` |
   | `Phosphorous` | `phosphorus` |
   | `Pottasium` | `potassium` |
   | `Magnessium` | `magnesium` |

3. **Divide** las imágenes en tres conjuntos:

   | Conjunto | Uso | Proporción |
   | --- | --- | --- |
   | `train` | Ajustar los pesos del modelo | 70 % |
   | `val` | Elegir el mejor modelo durante el entrenamiento | 15 % |
   | `test` | Medir el rendimiento final (datos no vistos) | 15 % |

   La división es **estratificada** (mantiene la proporción de cada clase).

---

## 5. Entrenamiento (`training/train.py`)

### 5.1. Conceptos clave

- **Red neuronal**: función con millones de parámetros (pesos) que convierte una
  imagen en un vector de probabilidades.
- **Época (epoch)**: una pasada completa por todo el dataset de entrenamiento.
- **Batch**: subconjunto de imágenes procesadas a la vez.
- **Loss (pérdida)**: número que mide qué tan mal predice el modelo.
- **Optimizador**: algoritmo que ajusta los pesos para reducir la pérdida.

### 5.2. El bucle de entrenamiento

Para cada época se repite:

1. **Forward pass**: la imagen entra a la red y produce probabilidades para las 5 clases.
2. **Cálculo de pérdida**: `CrossEntropyLoss` compara la predicción con la etiqueta real.
3. **Backpropagation**: se calcula cuánto debe cambiar cada peso (gradiente).
4. **Actualización**: el optimizador **Adam** ajusta los pesos.
5. **Evaluación en validación**: se mide la exactitud con datos que el modelo no usó para entrenar.

El modelo con mejor exactitud en validación se conserva como el mejor.

### 5.3. Técnicas aplicadas

- **Aumentación de datos**: flips horizontales, rotaciones y ajustes de brillo.
  Genera variaciones de las imágenes para reducir el sobreajuste (que el modelo
  "memorice" en lugar de generalizar).
- **Balanceo de clases**: el dataset original tiene clases desbalanceadas (ej.
  `potassium` tiene 56 imágenes, `magnesium` 123). Se usa
  `WeightedRandomSampler` para que cada clase tenga igual probabilidad de aparecer.

### 5.4. Métricas de evaluación

| Métrica | Significado |
| --- | --- |
| **Accuracy** | Fracción de predicciones correctas |
| **Precision** | De lo que predijo como clase X, cuánto era realmente X |
| **Recall** | De lo que realmente es X, cuánto detectó |
| **F1-score** | Promedio armónico de precisión y recall |
| **Matriz de confusión** | Tabla que muestra aciertos y errores por clase |

---

## 6. Inferencia (`app/model.py`)

Una vez entrenado, el modelo se guarda en `models/leaf_classifier.pt` con toda la
metadata necesaria (arquitectura, nombres de clase, tamaño de entrada).

Para predecir una imagen nueva:

1. Se **redimensiona** a 224×224 y se **normaliza** (media/desviación de ImageNet).
2. Se pasa por la red (forward) **sin calcular gradientes** (`torch.no_grad()`).
3. Se aplica **softmax** para convertir las salidas en probabilidades (0 a 1).
4. Se devuelve la clase con mayor probabilidad, su confianza y la recomendación.

---

## 7. API y frontend

- **FastAPI** expone dos endpoints:
  - `POST /predict`: recibe una imagen (archivo).
  - `POST /predict-frame`: recibe un frame codificado en base64 (video).
- El **frontend** (HTML/CSS/JS) permite subir una foto o usar la cámara en vivo.
  Para video, captura un frame cada ~600 ms y lo envía al backend.

---

## 8. Cómo reproducir el proyecto desde cero

```powershell
# 1. Clonar
git clone https://github.com/LuisDaniel1505/NutriLeaf
cd NutriLeaf

# 2. Entorno virtual
python -m venv venv
venv\Scripts\activate

# 3. Dependencias
pip install -r requirements.txt

# 4. Preparar datos (requiere el zip en Datasets/)
python -m training.preprocess

# 5. Entrenar
python -m training.train --arch resnet18 --epochs 20

# 6. Ejecutar
uvicorn app.main:app --reload --port 8000
```

---

## 9. Referencias

- Dataset: *Maize nitrogen deficiency: annotated imagery classification dataset* —
  Galić, Novoselnik, Salaić, Žarko.
- [PyTorch Documentation](https://pytorch.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
