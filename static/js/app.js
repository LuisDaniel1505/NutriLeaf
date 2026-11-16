// ============================================================
// NutriLeaf — Lógica del frontend (3 pestañas)
// Inicio · Analizar imagen · Cámara en vivo
// ============================================================

// Metadatos visuales por clase (símbolo químico + color + descripción).
// Se usan símbolos y colores en lugar de emojis para un aspecto más cuidado.
const CLASS_META = {
  healthy:    { symbol: "OK", badge: "bg-leaf-500",    name: "Saludable",  symptom: "Hojas sin señales visibles" },
  nitrogen:   { symbol: "N",  badge: "bg-yellow-500",  name: "Nitrógeno",  symptom: "Amarillamiento en forma de V" },
  phosphorus: { symbol: "P",  badge: "bg-purple-500",  name: "Fósforo",    symptom: "Tonos morados o rojizos" },
  potassium:  { symbol: "K",  badge: "bg-orange-500",  name: "Potasio",    symptom: "Bordes secos y amarillos" },
};

// ---------- Referencias al DOM ----------
const tabHome = document.getElementById("tab-home");
const tabImage = document.getElementById("tab-image");
const tabCamera = document.getElementById("tab-camera");
const panelHome = document.getElementById("panel-home");
const panelImage = document.getElementById("panel-image");
const panelCamera = document.getElementById("panel-camera");

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const previewWrap = document.getElementById("preview-wrap");
const previewImg = document.getElementById("preview");
const btnAnalyze = document.getElementById("btn-analyze");
const loadingImage = document.getElementById("loading-image");

const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const cameraOverlay = document.getElementById("camera-overlay");
const btnCamera = document.getElementById("btn-camera");
const cameraHint = document.getElementById("camera-hint");

const result = document.getElementById("result");
const resultCard = document.getElementById("result-card");

// Archivo actualmente seleccionado (funciona tanto con selección como con drag & drop).
let selectedFile = null;

// ---------- Pestañas ----------
const TAB_BASE = "px-5 py-2 rounded-full text-sm font-semibold transition-colors";
const TAB_ACTIVE = "bg-leaf-700 text-white shadow";
const TAB_INACTIVE = "text-leaf-700 hover:text-leaf-900";

function setActiveTab(active) {
  const tabs = { home: tabHome, image: tabImage, camera: tabCamera };
  const panels = { home: panelHome, image: panelImage, camera: panelCamera };

  for (const key of Object.keys(tabs)) {
    const isActive = key === active;
    tabs[key].className = `${TAB_BASE} ${isActive ? TAB_ACTIVE : TAB_INACTIVE}`;
    tabs[key].setAttribute("aria-selected", String(isActive));
    panels[key].classList.toggle("hidden", !isActive);
  }

  // Al salir de la cámara, se detiene la captura.
  if (active !== "camera") stopCamera();
}

tabHome.addEventListener("click", () => setActiveTab("home"));
tabImage.addEventListener("click", () => setActiveTab("image"));
tabCamera.addEventListener("click", () => setActiveTab("camera"));

document.getElementById("btn-cta-start").addEventListener("click", () => setActiveTab("image"));
document.getElementById("brand").addEventListener("click", (e) => {
  e.preventDefault();
  setActiveTab("home");
});

// ---------- Tarjetas de la página de inicio ----------
function renderHomeClasses() {
  const wrap = document.getElementById("home-classes");
  wrap.innerHTML = "";
  for (const meta of Object.values(CLASS_META)) {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl p-4 border border-leaf-100 shadow-sm text-center";
    card.innerHTML = `
      <span class="inline-flex items-center justify-center w-11 h-11 rounded-xl ${meta.badge} text-white font-bold text-sm">${meta.symbol}</span>
      <div class="font-semibold text-leaf-900 mt-3">${meta.name}</div>
      <div class="text-xs text-leaf-700/60 mt-1">${meta.symptom}</div>
    `;
    wrap.appendChild(card);
  }
}

// ---------- Selección de imagen ----------
dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) showPreview(e.target.files[0]);
});

["dragover", "dragenter"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("border-leaf-500", "bg-leaf-50");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("border-leaf-500", "bg-leaf-50");
  })
);
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) showPreview(file);
});

function showPreview(file) {
  if (!file.type.startsWith("image/")) {
    renderError("El archivo seleccionado no es una imagen. Usa JPG o PNG.");
    return;
  }
  selectedFile = file; // Guarda el archivo para poder analizarlo después.
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewWrap.classList.remove("hidden");
    result.classList.add("hidden");
  };
  reader.readAsDataURL(file);
}

// ---------- Análisis de imagen ----------
btnAnalyze.addEventListener("click", async () => {
  const file = selectedFile; // Usa el archivo guardado (soporta drag & drop).
  if (!file) return;

  btnAnalyze.disabled = true;
  loadingImage.classList.remove("hidden");

  try {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/predict", { method: "POST", body: form });
    const data = await res.json();
    if (res.status === 503) {
      throw new Error("El modelo aún no está entrenado. Ejecuta el entrenamiento antes de usar la aplicación.");
    }
    if (!res.ok) throw new Error(data.detail || "Error al analizar la imagen");
    renderResult(data);
  } catch (err) {
    renderError(err.message);
  } finally {
    btnAnalyze.disabled = false;
    loadingImage.classList.add("hidden");
  }
});

// ---------- Cámara en vivo ----------
let stream = null;
let frameTimer = null;

btnCamera.addEventListener("click", async () => {
  if (stream) {
    stopCamera();
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
    });
    video.srcObject = stream;
    cameraHint.classList.remove("hidden");
    cameraOverlay.classList.remove("hidden");
    btnCamera.textContent = "Detener cámara";
    startFrameLoop();
  } catch (err) {
    renderError(cameraErrorMessage(err));
  }
});

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop());
    stream = null;
  }
  if (frameTimer) {
    clearInterval(frameTimer);
    frameTimer = null;
  }
  btnCamera.textContent = "Iniciar cámara";
  cameraHint.classList.add("hidden");
  cameraOverlay.classList.add("hidden");
}

function cameraErrorMessage(err) {
  if (err.name === "NotAllowedError" || err.name === "SecurityError") {
    return "Permiso de cámara denegado. Activa el acceso a la cámara en la configuración del navegador.";
  }
  if (err.name === "NotFoundError" || err.name === "OverconstrainedError") {
    return "No se encontró una cámara disponible en este dispositivo.";
  }
  if (err.name === "NotReadableError") {
    return "La cámara está siendo utilizada por otra aplicación.";
  }
  return "No se pudo acceder a la cámara: " + err.message;
}

function startFrameLoop() {
  const ctx = canvas.getContext("2d");
  // Envía un frame cada ~600 ms para analizar en tiempo real.
  frameTimer = setInterval(async () => {
    if (!stream) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.7);

    try {
      const res = await fetch("/predict-frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error");
      renderResult(data);
      renderCameraOverlay(data);
    } catch (err) {
      cameraOverlay.innerHTML = `<span>⚠️ ${err.message}</span>`;
    }
  }, 600);
}

function renderCameraOverlay(data) {
  const meta = CLASS_META[data.class] || { symbol: "?", badge: "bg-leaf-500" };
  cameraOverlay.innerHTML = `
    <span class="inline-flex items-center justify-center w-10 h-10 rounded-xl ${meta.badge} text-white font-bold mb-2">${meta.symbol}</span>
    <strong class="text-lg">${data.label_es}</strong>
    <span class="text-white/80 text-sm">${Math.round(data.confidence * 100)}% de confianza</span>
  `;
}

// ---------- Renderizado del resultado ----------
const RESULT_BASE = "bg-white rounded-3xl border border-l-4 shadow-lg shadow-leaf-900/5 p-6 sm:p-8";

function renderResult(data) {
  const meta = CLASS_META[data.class] || { symbol: "?", badge: "bg-leaf-500" };
  const pct = Math.round(data.confidence * 100);

  resultCard.className = `${RESULT_BASE} border-leaf-100 border-l-leaf-500`;

  const iconEl = document.getElementById("result-icon");
  iconEl.className = `w-14 h-14 rounded-2xl flex items-center justify-center text-white text-lg font-bold shrink-0 ${meta.badge}`;
  iconEl.textContent = meta.symbol;

  document.getElementById("result-label").textContent = data.label_es;
  document.getElementById("result-short").textContent = data.recommendation.short || "";
  document.getElementById("result-confidence").textContent = pct + "%";
  document.getElementById("confidence-fill").style.width = pct + "%";

  // Chips con la probabilidad de cada clase.
  const probsEl = document.getElementById("probs");
  probsEl.innerHTML = "";
  const sorted = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);
  sorted.forEach(([cls, p]) => {
    const m = CLASS_META[cls] || { badge: "bg-leaf-500", name: cls };
    const chip = document.createElement("span");
    chip.className =
      "inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full " +
      (cls === data.class
        ? "bg-leaf-100 text-leaf-800"
        : "bg-cream text-leaf-700/70 border border-leaf-100");
    chip.innerHTML = `<span class="w-2 h-2 rounded-full ${m.badge}"></span> ${m.name} ${Math.round(p * 100)}%`;
    probsEl.appendChild(chip);
  });

  // Recomendación.
  document.getElementById("rec-detail").textContent = data.recommendation.detail || "";
  const actionsEl = document.getElementById("rec-actions");
  actionsEl.innerHTML = "";
  (data.recommendation.actions || []).forEach((a) => {
    const li = document.createElement("li");
    li.className = "flex gap-2 text-leaf-800";
    li.innerHTML = `<span class="text-leaf-500">•</span><span>${a}</span>`;
    actionsEl.appendChild(li);
  });

  result.classList.remove("hidden");
}

function renderError(msg) {
  result.classList.remove("hidden");
  resultCard.className = `${RESULT_BASE} border-red-200 border-l-red-500`;

  const iconEl = document.getElementById("result-icon");
  iconEl.className =
    "w-14 h-14 rounded-2xl flex items-center justify-center text-white text-lg font-bold shrink-0 bg-red-500";
  iconEl.textContent = "!";

  document.getElementById("result-label").textContent = "Algo salió mal";
  document.getElementById("result-short").textContent = msg;
  document.getElementById("result-confidence").textContent = "—";
  document.getElementById("confidence-fill").style.width = "0%";
  document.getElementById("probs").innerHTML = "";
  document.getElementById("rec-detail").textContent = "Revisa la imagen e inténtalo de nuevo.";
  document.getElementById("rec-actions").innerHTML = "";
}

// ---------- Inicialización ----------
renderHomeClasses();
setActiveTab("home");
