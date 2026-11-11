# 🌽 Manual de usuario — NutriLeaf

> **Versión:** 1.0 · **Última actualización:** noviembre de 2026
>
> NutriLeaf es una aplicación web que identifica deficiencias nutricionales en
> hojas de maíz a partir de una fotografía o de la cámara en tiempo real.

---

## 📋 Tabla de contenido

1. [¿Qué es NutriLeaf?](#1-qué-es-nutrileaf)
2. [¿A quién está dirigido?](#2-a-quién-está-dirigido)
3. [Requisitos del sistema](#3-requisitos-del-sistema)
4. [Instalación y puesta en marcha](#4-instalación-y-puesta-en-marcha)
5. [Guía de uso](#5-guía-de-uso)
6. [Deficiencias que identifica](#6-deficiencias-que-identifica)
7. [Interpretación de resultados](#7-interpretación-de-resultados)
8. [Preguntas frecuentes](#8-preguntas-frecuentes)
9. [Solución de problemas](#9-solución-de-problemas)
10. [Soporte](#10-soporte)

---

## 1. ¿Qué es NutriLeaf?

NutriLeaf es una herramienta de **inteligencia artificial** que analiza la
apariencia de las hojas de maíz para detectar posibles **deficiencias
nutricionales**. El usuario solo necesita una fotografía (o apuntar la cámara a
una hoja) y el sistema devuelve:

- La **deficiencia detectada** (o "planta saludable").
- El **porcentaje de confianza** del modelo.
- Una **recomendación** práctica para corregir la deficiencia.

No se requieren conocimientos de inteligencia artificial ni de agronomía para
utilizarlo.

## 2. ¿A quién está dirigido?

- **Agricultores** que desean revisar el estado de sus cultivos.
- **Estudiantes** de agricultura y tecnología.
- **Personas** interesadas en el cuidado de las plantas.
- **Investigadores** que trabajan con análisis de imágenes agrícolas.

## 3. Requisitos del sistema

### Para usar la aplicación (ya instalada)

- Un navegador web moderno (Chrome, Edge, Firefox o Safari actualizados).
- Conexión local al servidor donde se ejecuta NutriLeaf.

### Para ejecutar el proyecto desde el código

- **Sistema operativo:** Windows 10/11 (también funciona en Linux/macOS).
- **Python:** 3.11 o superior.
- **GPU (recomendado):** tarjeta NVIDIA compatible con CUDA (opcional, acelera
  el entrenamiento; la inferencia funciona en CPU).

## 4. Instalación y puesta en marcha

### 4.1 Clonar el repositorio

```bash
git clone https://github.com/LuisDaniel1505/NutriLeaf
cd NutriLeaf
```

### 4.2 Crear y activar el entorno virtual (Windows)

```powershell
python -m venv venv
venv\Scripts\activate
```

### 4.3 Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4.4 Obtener el modelo entrenado

El modelo se genera durante el entrenamiento. Si ya se cuenta con el archivo
`models/leaf_classifier.pt`, se puede omitir el paso 4.5.

### 4.5 (Opcional) Preparar datos y entrenar

> Solo es necesario si se quiere re-entrenar el modelo desde cero.

```bash
python -m training.preprocess
python -m training.train --arch resnet18 --epochs 20
```

### 4.6 Ejecutar la aplicación

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A continuación, abrir el navegador en **http://localhost:8000**.

## 5. Guía de uso

Al abrir la aplicación se muestran dos pestañas: **"Analizar imagen"** y
**"Cámara en vivo"**.

### 5.1 Analizar una imagen

1. Abre la pestaña **"📷 Analizar imagen"**.
2. Arrastra una fotografía de la hoja al recuadro, o haz clic en él para
   seleccionar el archivo desde tu equipo.
3. Pulsa el botón **"🔍 Analizar hoja"**.
4. Observa el resultado: la deficiencia detectada, la confianza y la
   recomendación.

### 5.2 Analizar con la cámara en vivo

1. Abre la pestaña **"🎥 Cámara en vivo"**.
2. Pulsa **"▶ Iniciar cámara"** y permite el acceso a la cámara cuando el
   navegador lo solicite.
3. Enfoca una hoja de maíz.
4. El diagnóstico se actualiza automáticamente en pantalla (aproximadamente
   dos veces por segundo).

### 5.3 Consejos para obtener buenos resultados

- Usa **buena iluminación** y evita sombras fuertes.
- Procura que la hoja **ocupe la mayor parte del encuadre**.
- Evita fondos muy recargados que puedan confundir al modelo.
- Para mejores resultados en video, mantén la hoja **estable** frente a la cámara.

## 6. Deficiencias que identifica

| Clase | Símbolo | Síntoma característico |
| --- | --- | --- |
| Planta saludable | ✅ | Sin señales visibles de deficiencia |
| Nitrógeno (N) | 🟡 | Amarillamiento en forma de "V" desde la punta |
| Fósforo (P) | 🟣 | Tonalidades moradas o rojizas |
| Potasio (K) | 🟠 | Amarillamiento y zonas secas en los bordes |
| Magnesio (Mg) | 🟢 | Zonas amarillas entre las nervaduras |

## 7. Interpretación de resultados

Cada resultado muestra:

- **Etiqueta de la deficiencia** y su icono.
- **Porcentaje de confianza**: qué tan seguro está el modelo de su respuesta.
- **Probabilidades por clase**: la distribución de confianza entre las 5 clases.
- **Recomendación**: acciones sugeridas para corregir la deficiencia.

> **Importante:** NutriLeaf es una herramienta de **apoyo**. Ante dudas o
> decisiones importantes, se recomienda consultar con un especialista agrónomo.

## 8. Preguntas frecuentes

**¿Necesito conexión a internet para usarlo?**
No. Una vez instalado, todo funciona de forma local.

**¿Puedo usar cualquier foto de una hoja de maíz?**
Sí, siempre que sea una hoja de maíz. El modelo está entrenado específicamente
para esa especie.

**¿Qué tan preciso es el modelo?**
El modelo alcanza aproximadamente un **87 %** de exactitud en pruebas. La clase
con menor rendimiento es el Potasio, por tener menos imágenes de entrenamiento.

**¿Puedo entrenar mi propio modelo?**
Sí. Consulta la sección [4.5](#45-opcional-preparar-datos-y-entrenar).

## 9. Solución de problemas

| Problema | Posible solución |
| --- | --- |
| La página no carga | Verifica que el servidor esté corriendo y que uses `http://localhost:8000`. |
| La cámara no enciende | Permite el acceso a la cámara en el navegador y revisa que no esté en uso por otra aplicación. |
| Aparece "modelo no entrenado" | Ejecuta el entrenamiento (`python -m training.train`) o coloca el archivo del modelo en `models/`. |
| La imagen no se analiza | Verifica que el archivo sea JPG o PNG y no esté dañado. |
| El servidor no inicia | Revisa que el entorno virtual esté activado y que las dependencias estén instaladas. |

## 10. Soporte

- **Repositorio:** https://github.com/LuisDaniel1505/NutriLeaf
- **Equipo:** Trinidad Cárdenas Axdiael · Ontiveros Lares Luis Daniel ·
  Ríos Villanueva Eduardo · Zazueta Carrillo Joel

---

> 📸 *Las capturas de pantalla se incorporan en la fase final del proyecto.*
