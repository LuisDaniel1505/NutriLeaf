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

// Etiquetas y recomendaciones en español (para la inferencia en el navegador).
const LABELS_ES = {
  healthy: "Planta saludable",
  nitrogen: "Deficiencia de Nitrógeno (N)",
  phosphorus: "Deficiencia de Fósforo (P)",
  potassium: "Deficiencia de Potasio (K)",
};

const RECOMMENDATIONS = {
  healthy: {
    short: "Sin deficiencias detectadas",
    detail: "La hoja no presenta señales visibles de las deficiencias que analiza NutriLeaf. Continúa con el monitoreo regular del cultivo para detectar cambios a tiempo.",
    actions: ["Mantener el plan de fertilización actual.", "Revisar el cultivo de forma periódica (semanal).", "Regar de forma adecuada según la etapa de la planta."],
  },
  nitrogen: {
    short: "Deficiencia de Nitrógeno (N)",
    detail: "El amarillamiento en forma de 'V' que inicia en la punta de la hoja y avanza hacia la base es el síntoma típico de falta de nitrógeno. El nitrógeno es clave para el crecimiento y el color verde de la planta.",
    actions: ["Aplicar fertilizante nitrogenado (urea o sulfato de amonio).", "Incorporar materia orgánica o compost al suelo.", "Evitar el exceso de agua, que puede lavar el nitrógeno del suelo."],
  },
  phosphorus: {
    short: "Deficiencia de Fósforo (P)",
    detail: "Las tonalidades moradas o rojizas en algunas partes de la hoja sugieren falta de fósforo, nutriente esencial para el desarrollo de raíces y la transferencia de energía.",
    actions: ["Aplicar fertilizante fosfatado (superfosfato o DAP) cerca de la raíz.", "Considerar que en suelos fríos el fósforo se absorbe con dificultad.", "Verificar el pH del suelo; un pH extremo limita la disponibilidad de fósforo."],
  },
  potassium: {
    short: "Deficiencia de Potasio (K)",
    detail: "El amarillamiento y las zonas secas, especialmente en los bordes de las hojas, indican falta de potasio. Este nutriente regula el agua y la resistencia de la planta.",
    actions: ["Aplicar cloruro o sulfato de potasio.", "Evitar el exceso de nitrógeno, que puede agravar la deficiencia.", "Mantener un riego regular, ya que el potasio se absorbe con agua."],
  },
};

// ---------- Inferencia en el navegador (ONNX Runtime) ----------
const CLASS_ORDER = ["healthy", "nitrogen", "phosphorus", "potassium"];
const INPUT_SIZE = 320;
const RESIZE = Math.round(INPUT_SIZE * 1.14); // 365
const MEAN = [0.485, 0.456, 0.406];
const STD = [0.229, 0.224, 0.225];

let onnxSession = null;
let onnxFailed = false;

async function getOnnxSession() {
  if (onnxSession) return onnxSession;
  if (onnxFailed) return null;
  // Prueba rutas relativas y absolutas (para GitHub Pages y servidor local).
  const paths = ["model.onnx", "/static/model.onnx"];
  for (const p of paths) {
    try {
      onnxSession = await ort.InferenceSession.create(p);
      return onnxSession;
    } catch (e) {
      // Probar la siguiente ruta.
    }
  }
  onnxFailed = true;
  return null;
}

function preprocessToTensor(img) {
  const w = img.naturalWidth || img.videoWidth || img.width;
  const h = img.naturalHeight || img.videoHeight || img.height;
  const scale = RESIZE / Math.min(w, h);
  const nw = Math.round(w * scale);
  const nh = Math.round(h * scale);

  const canvas = document.createElement("canvas");
  canvas.width = nw;
  canvas.height = nh;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(img, 0, 0, nw, nh);

  const cx = Math.floor((nw - INPUT_SIZE) / 2);
  const cy = Math.floor((nh - INPUT_SIZE) / 2);
  const crop = document.createElement("canvas");
  crop.width = INPUT_SIZE;
  crop.height = INPUT_SIZE;
  const cctx = crop.getContext("2d");
  cctx.drawImage(canvas, cx, cy, INPUT_SIZE, INPUT_SIZE, 0, 0, INPUT_SIZE, INPUT_SIZE);

  const data = cctx.getImageData(0, 0, INPUT_SIZE, INPUT_SIZE).data;
  const input = new Float32Array(3 * INPUT_SIZE * INPUT_SIZE);
  for (let i = 0; i < INPUT_SIZE * INPUT_SIZE; i++) {
    for (let c = 0; c < 3; c++) {
      input[c * INPUT_SIZE * INPUT_SIZE + i] = (data[i * 4 + c] / 255.0 - MEAN[c]) / STD[c];
    }
  }
  return input;
}

async function predictOnnx(img) {
  const session = await getOnnxSession();
  if (!session) return null;
  const input = preprocessToTensor(img);
  const tensor = new ort.Tensor("float32", input, [1, 3, INPUT_SIZE, INPUT_SIZE]);
  const results = await session.run({ input: tensor });
  const logits = Array.from(results.output.data);
  const maxLogit = Math.max(...logits);
  const exp = logits.map((x) => Math.exp(x - maxLogit));
  const sum = exp.reduce((a, b) => a + b, 0);
  const probs = exp.map((x) => x / sum);
  const idx = probs.indexOf(Math.max(...probs));
  const className = CLASS_ORDER[idx];
  const probabilities = {};
  CLASS_ORDER.forEach((c, i) => { probabilities[c] = probs[i]; });
  return {
    class: className,
    class_index: idx,
    label_es: LABELS_ES[className],
    confidence: probs[idx],
    probabilities,
    recommendation: RECOMMENDATIONS[className],
  };
}

// ---------- Referencias al DOM ----------
const tabHome = document.getElementById("tab-home");
const tabImage = document.getElementById("tab-image");
const tabCamera = document.getElementById("tab-camera");
const tabHistory = document.getElementById("tab-history");
const panelHome = document.getElementById("panel-home");
const panelImage = document.getElementById("panel-image");
const panelCamera = document.getElementById("panel-camera");
const panelHistory = document.getElementById("panel-history");

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

// Último diagnóstico (para poder exportarlo).
let lastResult = null;

// Historial de predicciones (persistente en localStorage).
let history = [];
try {
  history = JSON.parse(localStorage.getItem("nutrileaf_history") || "[]");
} catch {
  history = [];
}

// ---------- Pestañas ----------
const TAB_BASE = "px-5 py-2 rounded-full text-sm font-semibold transition-colors";
const TAB_ACTIVE = "bg-leaf-700 text-white shadow";
const TAB_INACTIVE = "text-leaf-700 hover:text-leaf-900";

function setActiveTab(active) {
  const tabs = { home: tabHome, image: tabImage, camera: tabCamera, history: tabHistory };
  const panels = { home: panelHome, image: panelImage, camera: panelCamera, history: panelHistory };

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
tabHistory.addEventListener("click", () => setActiveTab("history"));

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
    card.className = "bg-white rounded-2xl p-4 border border-leaf-100 shadow-sm text-center w-40 sm:w-44";
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
    // Intenta primero la inferencia en el navegador (ONNX); si no está
    // disponible, recurre al backend (/predict).
    let data = await predictOnnx(previewImg);
    if (!data) {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch("/predict", { method: "POST", body: form });
      data = await res.json();
      if (res.status === 503) {
        throw new Error("El modelo aún no está entrenado. Ejecuta el entrenamiento antes de usar la aplicación.");
      }
      if (!res.ok) throw new Error(data.detail || "Error al analizar la imagen");
    }
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
let lastCameraResult = null; // Último diagnóstico para mostrar al detener la cámara.

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
    document.getElementById("camera-result").classList.add("hidden");
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
  // Muestra el diagnóstico completo (con recomendación) del último frame.
  if (lastCameraResult) renderCameraResult(lastCameraResult);
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
      let data = await predictOnnx(video);
      if (!data) {
        const res = await fetch("/predict-frame", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: dataUrl }),
        });
        data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Error");
      }
      renderCameraOverlay(data);
      lastCameraResult = data;
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

function renderCameraResult(data) {
  const meta = CLASS_META[data.class] || { symbol: "?", badge: "bg-leaf-500" };
  const pct = Math.round(data.confidence * 100);

  const iconEl = document.getElementById("camera-result-icon");
  iconEl.className = `w-14 h-14 rounded-2xl flex items-center justify-center text-white text-lg font-bold shrink-0 ${meta.badge}`;
  iconEl.textContent = meta.symbol;

  document.getElementById("camera-result-label").textContent = data.label_es;
  document.getElementById("camera-result-short").textContent = data.recommendation.short || "";
  document.getElementById("camera-result-confidence").textContent = pct + "%";
  document.getElementById("camera-confidence-fill").style.width = pct + "%";

  document.getElementById("camera-rec-detail").textContent = data.recommendation.detail || "";
  const actionsEl = document.getElementById("camera-rec-actions");
  actionsEl.innerHTML = "";
  (data.recommendation.actions || []).forEach((a) => {
    const li = document.createElement("li");
    li.className = "flex gap-2 text-leaf-800";
    li.innerHTML = `<span class="text-leaf-500">•</span><span>${a}</span>`;
    actionsEl.appendChild(li);
  });

  document.getElementById("camera-result").classList.remove("hidden");
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

  lastResult = data;
  addToHistory(data);
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

// ---------- Historial ----------
function addToHistory(data) {
  const entry = {
    class: data.class,
    label_es: data.label_es,
    confidence: data.confidence,
    probabilities: data.probabilities,
    recommendation: data.recommendation,
    time: new Date().toLocaleString("es-MX"),
  };
  history.unshift(entry);
  if (history.length > 20) history = history.slice(0, 20);
  localStorage.setItem("nutrileaf_history", JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  const list = document.getElementById("history-list");
  const empty = document.getElementById("history-empty");
  const hasHistory = history.length > 0;
  list.innerHTML = "";
  empty.classList.toggle("hidden", hasHistory);
  document.getElementById("btn-export-selected").disabled = !hasHistory;
  document.getElementById("btn-export-all").disabled = !hasHistory;
  document.getElementById("btn-clear-history").disabled = !hasHistory;

  history.forEach((entry, index) => {
    const meta = CLASS_META[entry.class] || { badge: "bg-leaf-500", symbol: "?", name: entry.class };
    const li = document.createElement("li");
    li.className = "flex items-center gap-3 bg-white rounded-xl px-4 py-3 border border-leaf-100 shadow-sm";
    li.innerHTML = `
      <input type="checkbox" data-index="${index}" class="w-4 h-4 accent-leaf-600 shrink-0" />
      <span class="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-xs shrink-0 ${meta.badge}">${meta.symbol}</span>
      <div class="flex-1 min-w-0">
        <div class="font-medium text-leaf-900 truncate">${entry.label_es}</div>
        <div class="text-xs text-leaf-700/60">${entry.time}</div>
      </div>
      <span class="font-semibold text-leaf-900 text-sm shrink-0">${Math.round(entry.confidence * 100)}%</span>
    `;
    list.appendChild(li);
  });
}

// ---------- Exportación a PDF ----------
// jsPDF usa fuentes estándar sin soporte de acentos, por eso se normaliza el texto.
function normalizeText(s) {
  return (s || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ñ/g, "n")
    .replace(/Ñ/g, "N");
}

function exportDiagnosesPDF(entries) {
  if (!entries || entries.length === 0) return;
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();
  const pageWidth = doc.internal.pageSize.getWidth();
  const margin = 15;
  const lineHeight = 5.5;
  let y = margin;

  doc.setFontSize(18);
  doc.setFont("helvetica", "bold");
  doc.text("NutriLeaf - Diagnostico", margin, y);
  y += 10;

  entries.forEach((d, idx) => {
    if (y > 250) {
      doc.addPage();
      y = margin;
    }

    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.text(normalizeText(`${idx + 1}. ${d.label_es}`), margin, y);
    y += lineHeight;

    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Fecha: ${d.time || "-"}`, margin, y);
    y += lineHeight;
    doc.text(`Confianza: ${Math.round(d.confidence * 100)}%`, margin, y);
    y += lineHeight;

    const probs = Object.entries(d.probabilities || {}).sort((a, b) => b[1] - a[1]);
    probs.forEach(([k, v]) => {
      doc.text(`  - ${normalizeText(CLASS_META[k]?.name || k)}: ${Math.round(v * 100)}%`, margin, y);
      y += lineHeight;
    });

    y += 2;
    doc.setFont("helvetica", "bold");
    doc.text("Recomendacion:", margin, y);
    y += lineHeight;
    doc.setFont("helvetica", "normal");
    const detail = doc.splitTextToSize(normalizeText(d.recommendation?.detail || ""), pageWidth - margin * 2);
    doc.text(detail, margin, y);
    y += detail.length * lineHeight;
    (d.recommendation?.actions || []).forEach((a) => {
      const act = doc.splitTextToSize(normalizeText(`- ${a}`), pageWidth - margin * 2);
      doc.text(act, margin, y);
      y += act.length * lineHeight;
    });

    y += 8;
  });

  doc.save(`diagnosticos_nutrileaf_${Date.now()}.pdf`);
}

document.getElementById("btn-export").addEventListener("click", () => {
  if (!lastResult) return;
  exportDiagnosesPDF([{ ...lastResult, time: new Date().toLocaleString("es-MX") }]);
});

document.getElementById("btn-export-selected").addEventListener("click", () => {
  const checked = [...document.querySelectorAll("#history-list input[type=checkbox]:checked")];
  const selected = checked.map((cb) => history[Number(cb.dataset.index)]).filter(Boolean);
  exportDiagnosesPDF(selected);
});

document.getElementById("btn-export-all").addEventListener("click", () => {
  exportDiagnosesPDF(history);
});

document.getElementById("btn-clear-history").addEventListener("click", () => {
  history = [];
  localStorage.removeItem("nutrileaf_history");
  renderHistory();
});

// ---------- Inicialización ----------
renderHomeClasses();
renderHistory();
setActiveTab("home");
