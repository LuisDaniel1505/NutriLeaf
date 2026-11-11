// ============================================================
// NutriLeaf — Lógica del frontend
// Dos modos: análisis de imagen subida y cámara en vivo.
// ============================================================

const CLASS_ICONS = {
  healthy: "✅",
  nitrogen: "🟡",
  phosphorus: "🟣",
  potassium: "🟠",
  magnesium: "🟢",
};

// ---------- Referencias al DOM ----------
const tabImage = document.getElementById("tab-image");
const tabCamera = document.getElementById("tab-camera");
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

// ---------- Pestañas ----------
function switchTab(active) {
  const imageActive = active === "image";
  tabImage.classList.toggle("active", imageActive);
  tabCamera.classList.toggle("active", !imageActive);
  panelImage.classList.toggle("active", imageActive);
  panelCamera.classList.toggle("active", !imageActive);
}

tabImage.addEventListener("click", () => {
  switchTab("image");
  stopCamera();
});
tabCamera.addEventListener("click", () => switchTab("camera"));

// ---------- Selección de imagen ----------
dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length) showPreview(e.target.files[0]);
});

["dragover", "dragenter"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) showPreview(file);
});

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    previewWrap.classList.remove("hidden");
    result.classList.add("hidden");
  };
  reader.readAsDataURL(file);
}

// ---------- Análisis de imagen subida ----------
btnAnalyze.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  btnAnalyze.disabled = true;
  loadingImage.classList.remove("hidden");

  try {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch("/predict", { method: "POST", body: form });
    const data = await res.json();
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
    btnCamera.textContent = "⏹ Detener cámara";
    startFrameLoop();
  } catch (err) {
    renderError("No se pudo acceder a la cámara: " + err.message);
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
  btnCamera.textContent = "▶ Iniciar cámara";
  cameraHint.classList.add("hidden");
  cameraOverlay.classList.add("hidden");
}

function startFrameLoop() {
  const ctx = canvas.getContext("2d");
  // Envía un frame cada ~600 ms para analizar en tiempo real.
  frameTimer = setInterval(async () => {
    if (!stream) return;
    // Dibuja el frame actual en el canvas y lo codifica a JPEG base64.
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
  const icon = CLASS_ICONS[data.class] || "🌿";
  cameraOverlay.innerHTML = `
    <span style="font-size:38px">${icon}</span>
    <strong>${data.label_es}</strong>
    <span>${Math.round(data.confidence * 100)}% de confianza</span>
  `;
}

// ---------- Renderizado del resultado ----------
function renderResult(data) {
  const icon = CLASS_ICONS[data.class] || "🌿";
  const pct = Math.round(data.confidence * 100);

  document.getElementById("result-icon").textContent = icon;
  document.getElementById("result-label").textContent = data.label_es;
  document.getElementById("result-short").textContent =
    data.recommendation.short || "";

  document.getElementById("result-confidence").textContent = pct + "%";
  document.getElementById("confidence-fill").style.width = pct + "%";

  // Barras de probabilidad por clase.
  const probsEl = document.getElementById("probs");
  probsEl.innerHTML = "";
  const sorted = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);
  sorted.forEach(([cls, p]) => {
    const chip = document.createElement("span");
    chip.className = "prob-chip" + (cls === data.class ? " top" : "");
    chip.textContent = `${CLASS_ICONS[cls] || ""} ${formatClass(cls)} ${Math.round(p * 100)}%`;
    probsEl.appendChild(chip);
  });

  // Recomendación.
  document.getElementById("rec-detail").textContent =
    data.recommendation.detail || "";
  const actionsEl = document.getElementById("rec-actions");
  actionsEl.innerHTML = "";
  (data.recommendation.actions || []).forEach((a) => {
    const li = document.createElement("li");
    li.textContent = a;
    actionsEl.appendChild(li);
  });

  result.classList.remove("hidden");
}

function renderError(msg) {
  result.classList.remove("hidden");
  resultCard.style.borderLeftColor = "var(--danger)";
  document.getElementById("result-icon").textContent = "⚠️";
  document.getElementById("result-label").textContent = "Error";
  document.getElementById("result-short").textContent = msg;
  document.getElementById("result-confidence").textContent = "—";
  document.getElementById("confidence-fill").style.width = "0%";
  document.getElementById("probs").innerHTML = "";
  document.getElementById("rec-detail").textContent =
    "Revisa la consola o el servidor para más detalles.";
  document.getElementById("rec-actions").innerHTML = "";
}

function formatClass(cls) {
  return cls.charAt(0).toUpperCase() + cls.slice(1);
}
