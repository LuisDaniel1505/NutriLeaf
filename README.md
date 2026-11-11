# 🌽 NutriLeaf

**Identificación de deficiencias nutricionales en la planta de maíz.**

NutriLeaf es un proyecto de **Inteligencia Artificial** que analiza fotografías de
hojas de maíz para detectar deficiencias nutricionales por su apariencia visual
(colores, manchas y patrones). El sistema permite analizar tanto **imágenes subidas**
como **video en tiempo real desde la cámara**, y devuelve el diagnóstico con su
porcentaje de confianza y recomendaciones prácticas.

> Proyecto desarrollado como parte de la materia de Inteligencia Artificial.

---

## 👥 Integrantes

| Nombre |
| --- |
| Trinidad Cárdenas Axdiael |
| Ontiveros Lares Luis Daniel |
| Ríos Villanueva Eduardo |
| Zazueta Carrillo Joel |

---

## 🎯 ¿Qué problema resuelve?

No siempre es fácil reconocer a simple vista qué nutriente le falta a una planta.
Cuando un cultivo no recibe los nutrientes necesarios, sus hojas muestran cambios
visibles (amarillamiento, manchas, bordes secos, tonos morados, etc.). NutriLeaf
automatiza ese diagnóstico mediante un modelo de aprendizaje profundo.

## 🔍 Deficiencias que identifica

| Clase | Símbolo | Síntoma característico |
| --- | --- | --- |
| Planta saludable | ✅ | Sin señales visibles de deficiencia |
| Nitrógeno (N) | 🟡 | Amarillamiento en forma de "V" desde la punta |
| Fósforo (P) | 🟣 | Tonalidades moradas o rojizas |
| Potasio (K) | 🟠 | Amarillamiento y zonas secas en los bordes |
| Magnesio (Mg) | 🟢 | Zonas amarillas entre las nervaduras |

---

## ✨ Funcionalidades

- 📷 **Análisis de imágenes**: sube una foto de la hoja y recibe el diagnóstico.
- 🎥 **Cámara en vivo**: analiza la hoja en tiempo real con la cámara del dispositivo.
- 📊 **Confianza del modelo**: muestra el porcentaje de confianza por clase.
- 💡 **Recomendaciones**: sugerencias agronómicas sencillas para cada deficiencia.

## 🧠 Tecnologías

| Componente | Tecnología |
| --- | --- |
| Lenguaje | Python 3.11 |
| Deep learning | PyTorch + torchvision (transfer learning, ResNet18) |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML + CSS + JavaScript (vanilla) |
| Datos | `Maize Nutrient Deficiency Dataset` (5 clases) |
| Control de versiones | Git + GitHub |

> **Nota sobre TensorFlow:** TensorFlow no ofrece soporte de GPU en Windows nativo
> (solo hasta la versión 2.10, incompatible con Python 3.11). Por eso se eligió
> **PyTorch**, que ofrece soporte nativo de GPU en Windows sin configuraciones extra.

---

## 📁 Estructura del proyecto

```
NutriLeaf/
├── app/                    # Backend (FastAPI) y lógica de inferencia
│   ├── config.py           # Rutas y configuración global
│   ├── labels.py           # Etiquetas de las 5 clases
│   ├── recommendations.py  # Recomendaciones agronómicas
│   ├── model.py            # Arquitectura del modelo + inferencia
│   └── main.py             # Endpoints de la API
├── training/               # Preparación de datos y entrenamiento
│   ├── preprocess.py       # Extrae y divide el dataset
│   └── train.py            # Entrena el modelo con transfer learning
├── static/                 # Interfaz web
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── models/                 # Modelo entrenado (no versionado)
├── data/                   # Dataset (no versionado)
├── docs/                   # Documentación y manual de usuario
├── requirements.txt        # Dependencias del proyecto
└── README.md
```

---

## 🚀 Puesta en marcha

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd NutriLeaf
```

### 2. Crear y activar el entorno virtual (Windows)

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> En Windows, `pip install torch torchvision` instala automáticamente la versión
> con soporte CUDA. Verifica la GPU con:
> ```python
> import torch; print(torch.cuda.is_available())
> ```

### 4. Preparar el dataset

Coloca `Maize Nutrient Deficiency Dataset.zip` en la carpeta `Datasets/` (junto al
proyecto) y ejecuta:

```bash
python -m training.preprocess
```

### 5. Entrenar el modelo

```bash
python -m training.train --arch resnet18 --epochs 20
```

El modelo entrenado se guarda en `models/leaf_classifier.pt`.

### 6. Ejecutar la aplicación

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Abre <http://localhost:8000> en tu navegador.

---

## 🔌 Endpoints de la API

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/` | Interfaz web |
| `GET` | `/health` | Estado del servicio y del modelo |
| `POST` | `/predict` | Predice a partir de una imagen (multipart/form-data) |
| `POST` | `/predict-frame` | Predice a partir de un frame base64 (video en vivo) |

---

## 🗺️ Hoja de ruta

- [x] Estructura del proyecto y control de versiones
- [ ] Preparación del dataset
- [ ] Entrenamiento y evaluación del modelo
- [ ] Backend de predicción
- [ ] Interfaz web (imagen + cámara en vivo)
- [ ] Manual de usuario (`docs/`)
- [ ] Pulido final y documentación

---

## 📄 Licencia

Este proyecto se distribuye con fines académicos. Consúltese el equipo antes de
reutilizar el código fuera del ámbito educativo.
