const prepareForm = document.querySelector("#prepareForm");
const logForm = document.querySelector("#logForm");
const propertyInput = document.querySelector("#propertyName");
const facebookInput = document.querySelector("#facebookUrl");
const captionOutput = document.querySelector("#captionOutput");
const copyButton = document.querySelector("#copyCaption");
const zipDownload = document.querySelector("#zipDownload");
const imageGallery = document.querySelector("#imageGallery");
const imageTemplate = document.querySelector("#imageTemplate");
const statusPill = document.querySelector("#connectionStatus");

let activeProperty = "";
let activeCaption = "";

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js");
}

prepareForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Preparing");
  const propertyName = propertyInput.value.trim();
  const response = await fetch("/api/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: propertyName }),
  });
  const payload = await response.json();
  if (!response.ok) {
    setStatus(payload.detail || "Preparation failed");
    return;
  }

  activeProperty = payload.property_name;
  activeCaption = payload.caption;
  captionOutput.textContent = payload.caption;
  copyButton.disabled = false;
  logForm.hidden = false;
  renderImages(payload.images);
  zipDownload.href = payload.download_zip_url;
  zipDownload.classList.remove("disabled");
  zipDownload.removeAttribute("aria-disabled");
  setStatus("Ready for manual post");
});

copyButton.addEventListener("click", async () => {
  await navigator.clipboard.writeText(activeCaption);
  setStatus("Caption copied");
});

logForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setStatus("Logging");
  const response = await fetch("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      property_name: activeProperty,
      facebook_url: facebookInput.value.trim(),
    }),
  });
  const payload = await response.json();
  setStatus(response.ok ? "Logged" : payload.detail || "Log failed");
});

function renderImages(images) {
  imageGallery.replaceChildren();
  for (const image of images) {
    const fragment = imageTemplate.content.cloneNode(true);
    const img = fragment.querySelector("img");
    const label = fragment.querySelector("span");
    const link = fragment.querySelector("a");
    img.src = image.url;
    img.alt = image.name;
    label.textContent = image.name;
    link.href = image.url;
    link.download = image.name;
    imageGallery.appendChild(fragment);
  }
}

function setStatus(message) {
  statusPill.textContent = message;
}
