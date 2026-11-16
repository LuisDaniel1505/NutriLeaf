# 🌽 NutriLeaf — Contexto del proyecto

> Documento de referencia para el equipo. Explica, en lenguaje sencillo, qué es
> NutriLeaf, qué problema resuelve, cómo funciona y cómo colaborar. Pensado para
> presentar el proyecto en el **Encuentro de Sistemas**.

---

## 1. ¿Qué es NutriLeaf?

NutriLeaf es una **aplicación web de Inteligencia Artificial** que identifica
deficiencias nutricionales en las hojas de maíz a partir de una fotografía o de
la cámara en vivo.

En pocas palabras: **le tomas una foto a una hoja de maíz y NutriLeaf te dice si
está sana o si le falta algún nutriente**, junto con el porcentaje de confianza y
una recomendación práctica.

---

## 2. El problema que resuelve

Las plantas necesitan nutrientes (nitrógeno, fósforo, potasio, etc.) para crecer
bien. Cuando les falta alguno, las hojas muestran **síntomas visibles**:

- Se ponen amarillas.
- Aparecen manchas o zonas secas.
- Cambian de color en los bordes.

El problema es que **a simple vista es difícil saber qué nutriente falta**,
porque varios síntomas se parecen. NutriLeaf automatiza ese diagnóstico con un
modelo de aprendizaje profundo.

**¿Por qué maíz?** Porque es un cultivo común, sus hojas muestran cambios visibles
ante la falta de nutrientes, y existen bases de datos de imágenes para entrenar
el modelo.

---

## 3. ¿Qué puede detectar?

NutriLeaf clasifica cada hoja en **4 estados**:

| Clase | Símbolo | Síntoma característico |
| --- | --- | --- |
| Planta saludable | ✅ | Sin señales visibles de deficiencia |
| Nitrógeno (N) | 🟡 | Amarillamiento en forma de "V" desde la punta |
| Fósforo (P) | 🟣 | Tonalidades moradas o rojizas |
| Potasio (K) | 🟠 | Amarillamiento y zonas secas en los bordes |

---

## 4. ¿Cómo funciona? (de forma sencilla)

1. **Tomas una foto** (o apuntas la cámara) a una hoja de maíz.
2. **El modelo analiza** los colores, manchas y patrones de la hoja.
3. **Compara** esas características con lo que aprendió durante el entrenamiento.
4. **Muestra el resultado**: la deficiencia detectada, el % de confianza y una
   recomendación.

> **La clave:** la IA corre **directamente en el navegador** (gracias a ONNX),
> por lo que la aplicación funciona sin necesidad de un servidor. Esto permite
> publicarla gratis en GitHub Pages.

---

## 5. La inteligencia artificial explicada simple

- **Modelo:** una red neuronal llamada **ResNet18** (una arquitectura probada para
  reconocer imágenes).
- **Transfer learning:** en lugar de entrenar la red desde cero (que requeriría
  millones de imágenes), partimos de una red ya entrenada con millones de fotos y
  solo le "enseñamos" las 4 clases de maíz.
- **Datos de entrenamiento:** ~4.700 imágenes de hojas de maíz de campo real,
  combinando dos bases de datos públicas:
  1. *Maize Nutrient Deficiency Dataset* (463 imágenes).
  2. *Doctor Maíz* de Hugging Face (~4.200 imágenes, de El Salvador).
- **Resultado:** **92.3 % de exactitud** en el conjunto de prueba.

| Clase | F1 |
| --- | --- |
| Sana | 0.92 |
| Nitrógeno | 1.00 |
| Fósforo | 0.97 |
| Potasio | 0.80 |

> El potasio es la clase más difícil porque su síntoma (amarillo tenue en los
> bordes) es el más sutil.

---

## 6. Tecnologías usadas

| Componente | Tecnología |
| --- | --- |
| Lenguaje | Python 3.11 |
| Inteligencia artificial | PyTorch (entrenamiento) + ONNX (despliegue en navegador) |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML + CSS + JavaScript + Tailwind CSS |
| Pruebas | pytest |
| Control de versiones | Git + GitHub |
| Despliegue | GitHub Pages |

---

## 7. ¿Dónde está y cómo lo usamos?

La aplicación está **en línea** y la puede usar cualquier persona:

🔗 **https://luisdaniel1505.github.io/NutriLeaf/**

### Funcionalidades
- 📷 **Analizar imagen**: subir o arrastrar una foto.
- 🎥 **Cámara en vivo**: diagnóstico en tiempo real.
- 📊 **Confianza** y probabilidades por clase.
- 💡 **Recomendaciones** agronómicas.
- 📜 **Historial** de diagnósticos (se guarda en el navegador).
- 📥 **Exportar a PDF** (uno o varios diagnósticos).

### Para probar
Puedes usar las imágenes de prueba en la carpeta `test_images/` (2 por clase).

---

## 8. Organización del proyecto

```
NutriLeaf/
├── app/          # Backend (FastAPI) y lógica del modelo
├── training/     # Preparación de datos y entrenamiento
├── static/       # Interfaz web (HTML, CSS, JS)
├── scripts/      # Herramientas: exportar ONNX, evaluar, desplegar
├── tests/        # Pruebas automatizadas
├── models/       # Modelo entrenado (no se sube a Git)
├── data/         # Datasets (no se suben a Git)
├── docs/         # Documentación
└── test_images/  # Imágenes de prueba
```

---

## 9. Para desarrolladores

### Ejecutar en local

```powershell
# 1. Entorno virtual
python -m venv venv
venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación
uvicorn app.main:app --reload --port 8000
```

Abrir **http://localhost:8000**.

### Re-entrenar el modelo

```powershell
python -m training.preprocess       # prepara el dataset base
python -m training.build_dataset    # combina base + Hugging Face
python -m training.train            # entrena (ResNet18, 20 épocas)
```

### Ejecutar las pruebas

```powershell
python -m pytest tests/ -v
```

### Actualizar el sitio desplegado

```powershell
python scripts/export_onnx.py      # exporta el modelo a ONNX
# (copiar models/leaf_classifier.onnx a static/model.onnx)
python scripts/deploy_ghpages.py   # sube el sitio a GitHub Pages
```

---

## 10. Estado actual

- ✅ **Versión 1.0.0** (release en GitHub).
- ✅ Desplegado en GitHub Pages (con IA en el navegador).
- ✅ 4 clases: sana, nitrógeno, fósforo y potasio.
- ✅ 92.3 % de exactitud en prueba.

### Posibles siguientes pasos
- Mejorar la clase **potasio** con más datos de campo.
- Añadir más clases (por ejemplo, magnesio) si se consigue un dataset.
- Afinar el modelo con fotos propias de parcelas locales.

---

## 11. Equipo

| Nombre |
| --- |
| Trinidad Cárdenas Axdiael |
| Ontiveros Lares Luis Daniel |
| Ríos Villanueva Eduardo |
| Zazueta Carrillo Joel |

---

*Documento generado para el Encuentro de Sistemas — Noviembre 2026.*
