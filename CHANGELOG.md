# Changelog

Todos los cambios relevantes del proyecto quedan documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/),
y el proyecto sigue el [Versionado Semántico](https://semver.org/lang/es/).

## [1.0.0] - 2026-11-16

### Añadido
- Modelo de clasificación de 4 clases (sana, nitrógeno, fósforo y potasio) con
  transfer learning (ResNet18) + pesos por clase.
- Backend con FastAPI: endpoints `/health`, `/predict` y `/predict-frame`.
- Interfaz web con Tailwind CSS: pestañas de Inicio, Analizar imagen, Cámara en
  vivo e Historial.
- Análisis de imágenes por subida o arrastrar y soltar.
- Análisis en tiempo real con la cámara del dispositivo.
- Diagnóstico con porcentaje de confianza, probabilidades por clase y
  recomendaciones agronómicas.
- Historial de predicciones (persistente en el navegador).
- Exportación de diagnósticos a PDF (individual o varios a la vez).
- Manual de usuario, documento de proceso de creación y registro de experimentos.
- Pruebas automatizadas con pytest (14 pruebas).
- Scripts auxiliares: verificación y evaluación del modelo, descarga de datasets.
- Integración del dataset *Doctor Maíz* (Hugging Face) para mejorar la precisión.
- Licencia MIT.

### Cambiado
- Se eliminó la clase "magnesio" del modelo (pasó de 5 a 4 clases).
- Preprocesamiento de imágenes: se respeta la proporción y se subió la resolución
  a 320×320.
- Diseño de la interfaz rediseñado por completo (paleta esmeralda + ámbar,
  tipografías Fraunces + Inter, logo de hoja SVG).

### Corregido
- El análisis no funcionaba al arrastrar y soltar imágenes.
- La tarjeta de resultado permanecía visible al cambiar de pestaña.
- El servidor mantenía en memoria un modelo desactualizado.
- Cacheado de archivos estáticos del frontend.

### Técnico
- Entorno: Python 3.11, PyTorch 2.14 (CUDA), FastAPI, Tailwind CSS v4.
- Datos de entrenamiento: *Maize Nutrient Deficiency Dataset* (463 imágenes) +
  *Corn Leaf Diseases, Pests and Deficiencies* (~4.200 imágenes de campo).
- Exactitud en test: **92.3 %** (nitrógeno 1.00, fósforo 0.97, potasio 0.80).

---

## [0.1.0] - 2026-11-10

### Añadido
- Estructura inicial del proyecto, repositorio Git y publicación en GitHub.
- Modelo inicial de 5 clases (sana, N, P, K, Mg) con ResNet18.
- Backend FastAPI y frontend básico (imagen + cámara en vivo).
