// allow: SIZE_OK - Todo 3 scope permits only the existing Vite entry file for the prototype console.
import "./styles.css";
import { initializeApp } from "firebase/app";
import {
  GoogleAuthProvider,
  getAuth,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from "firebase/auth";

const doc = document;
const qs = (selector) => doc.querySelector(selector);

const elements = {
  activityCount: qs("#activityCount"),
  activityLog: qs("#activityLog"),
  assignedBy: qs("#assignedBy"),
  captionGuidance: qs("#captionGuidance"),
  captionOutput: qs("#captionOutput"),
  captionSourceOutput: qs("#captionSourceOutput"),
  captionVariants: qs("#captionVariants"),
  checkCaption: qs("#checkCaption"),
  checkManualPost: qs("#checkManualPost"),
  checkPhotos: qs("#checkPhotos"),
  connectionStatus: qs("#connectionStatus"),
  copyCaption: qs("#copyCaption"),
  countAssigned: qs("#countAssigned"),
  countPosted: qs("#countPosted"),
  countReady: qs("#countReady"),
  countWaiting: qs("#countWaiting"),
  dailyReport: qs("#dailyReport"),
  driveUrl: qs("#driveUrl"),
  dueDate: qs("#dueDate"),
  facebookInput: qs("#facebookUrl"),
  facebookUrlGroup: qs("#facebookUrlGroup"),
  generateCaptionButton: qs("#generateCaption"),
  imageGallery: qs("#imageGallery"),
  imageTemplate: qs("#imageTemplate"),
  jobList: qs("#jobList"),
  jobTemplate: qs("#jobTemplate"),
  logButton: qs("#logPostButton"),
  logForm: qs("#logForm"),
  metricCaption: qs("#metricCaption"),
  metricPhotos: qs("#metricPhotos"),
  metricRole: qs("#metricRole"),
  metricValidation: qs("#metricValidation"),
  newIntake: qs("#newIntake"),
  openFacebook: qs("#openFacebook"),
  operatorName: qs("#operatorName"),
  prepareForm: qs("#prepareForm"),
  processNextButton: qs("#processNext"),
  propertyInput: qs("#propertyName"),
  refreshJobs: qs("#refreshJobs"),
  roleBadge: qs("#roleBadge"),
  runPipeline: qs("#runPipeline"),
  selectedPhotoBadge: qs("#selectedPhotoBadge"),
  selectedPropertyMeta: qs("#selectedPropertyMeta"),
  selectedPropertyTitle: qs("#selectedPropertyTitle"),
  signInButton: qs("#signInButton"),
  signOutButton: qs("#signOutButton"),
  sourceDocName: qs("#sourceDocName"),
  themeToggle: qs("#themeToggle"),
  trackerRow: qs("#trackerRow"),
  userLabel: qs("#userLabel"),
  validationResults: qs("#validationResults"),
  validationState: qs("#validationState"),
  zipDownload: qs("#zipDownload"),
};

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};
const hostedDomain = import.meta.env.VITE_APG_GOOGLE_DOMAIN;
const firebaseReady = Object.values(firebaseConfig).every(Boolean);
const auth = firebaseReady ? getAuth(initializeApp(firebaseConfig)) : null;
const provider = new GoogleAuthProvider();
if (hostedDomain) {
  provider.setCustomParameters({ hd: hostedDomain });
}

const demoJobs = [
  {
    id: "APG-2401",
    property_name: "Novaliches, 440 Bagbag",
    assigned_by: "Ma'am Jean",
    operator: "Deign",
    due_date: "2026-06-30",
    status: "ready_to_post",
    drive_url: "https://drive.google.com/demo/bagbag",
    caption_document_name: "Bagbag-caption.docx",
    caption_details: "Townhouse for sale in Novaliches with clean title, near transport, schools, and daily essentials.",
    caption: "Novaliches, 440 Bagbag is ready for viewing. This property offers practical access to transport, schools, and daily essentials. Message APG for details and schedule coordination.",
    images: [
      { name: "front-view.jpg", url: "/icon-192.png", selected: true },
      { name: "living-area.jpg", url: "/icon-192.png", selected: true },
      { name: "kitchen.jpg", url: "/icon-192.png", selected: true },
      { name: "street-access.jpg", url: "/icon-192.png", selected: false },
    ],
    variants: [
      "Ready for posting: Novaliches, 440 Bagbag with practical access to transport, schools, and essentials. Message APG for viewing details.",
      "APG listing prepared for Novaliches, 440 Bagbag. Review the photos, confirm details, and coordinate viewing through the assigned operator.",
      "For Facebook posting: Novaliches, 440 Bagbag. Clean property details, selected photos, and tracker preview are ready for manual publishing.",
    ],
    activity: [
      { at: "09:18", text: "Ma'am Jean assigned APG-2401 to Deign." },
      { at: "09:24", text: "Drive validation passed with 4 images and 1 caption doc." },
      { at: "09:32", text: "Caption variants generated with APG rule check." },
    ],
  },
  {
    id: "APG-2402",
    property_name: "Fairview, Dahlia Avenue",
    assigned_by: "Admin",
    operator: "Rhea",
    due_date: "2026-06-30",
    status: "waiting_approval",
    drive_url: "https://drive.google.com/demo/fairview",
    caption_document_name: "Fairview-caption.docx",
    caption_details: "Condo unit near Commonwealth corridor. Needs price confirmation before posting.",
    caption: "Fairview, Dahlia Avenue is queued for caption approval and final asset review.",
    images: [
      { name: "unit-main.jpg", url: "/icon-192.png", selected: true },
      { name: "amenity.jpg", url: "/icon-192.png", selected: false },
    ],
    variants: [],
    activity: [{ at: "10:05", text: "Validation flagged missing third selected photo." }],
  },
];

let currentUser = null;
let selectedJobId = "APG-2401";
let jobs = [...demoJobs];
let session = {
  firebase_project_id: firebaseConfig.projectId || "demo",
  user: { uid: "demo-maam-jean", email: "demo@apg.local", role: "maam_jean", display_name: "Ma'am Jean" },
};
let activeCaption = demoJobs[0].caption;
let activeProperty = demoJobs[0].property_name;

const workflowState = {
  prepared: true,
  downloadedAssets: false,
  generatedCaption: true,
  copiedCaption: false,
  openedFacebook: false,
  enteredFacebookUrl: false,
  loggedPost: false,
};

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js");
}

if (auth) {
  onAuthStateChanged(auth, async (user) => {
    currentUser = user;
    elements.signInButton.hidden = Boolean(user);
    elements.signOutButton.hidden = !user;
    await loadSession();
    await loadJobs();
  });
} else {
  elements.userLabel.textContent = "Demo mode: Firebase config not loaded. Ma'am Jean workflow is available.";
}

elements.signInButton.addEventListener("click", async () => {
  if (!auth) {
    setStatus("Firebase config missing; staying in demo mode");
    return;
  }
  await signInWithPopup(auth, provider);
});

elements.signOutButton.addEventListener("click", async () => {
  if (auth) {
    await signOut(auth);
  }
});

elements.themeToggle.addEventListener("click", () => {
  const nextTheme = doc.documentElement.dataset.theme === "dark" ? "light" : "dark";
  doc.documentElement.dataset.theme = nextTheme;
  localStorage.setItem("apg-theme", nextTheme);
});

elements.refreshJobs.addEventListener("click", loadJobs);
elements.newIntake.addEventListener("click", startNewIntake);
elements.runPipeline.addEventListener("click", () => prepareSelectedJob("button"));
elements.processNextButton.addEventListener("click", async () => {
  const response = await requestJson("/api/queue/next", { method: "POST" });
  if (response.ok && response.data.property_name) {
    elements.propertyInput.value = response.data.property_name;
    await prepareSelectedJob("queue");
    return;
  }
  setStatus("Demo fallback loaded next property");
  selectJob(jobs[0].id);
});

elements.prepareForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await createOrPrepareJob();
});

elements.generateCaptionButton.addEventListener("click", async () => {
  const job = selectedJob();
  const jobId = job.id;
  const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/captions`, { method: "POST" }));
  const variants = response.ok ? normalizeVariants(response.data) : job.variants;
  job.variants = variants.length > 0 ? variants : demoJobs[0].variants;
  workflowState.generatedCaption = true;
  renderCaption(job);
  updateWorkflowGuide();
  addActivity("Caption variants generated with APG rules.");
  setStatus(response.ok ? "Caption variants ready" : "Demo caption variants ready");
});

elements.copyCaption.addEventListener("click", async () => {
  if (!workflowState.generatedCaption) {
    setStatus("Generate the caption first");
    return;
  }
  await navigator.clipboard.writeText(activeCaption);
  workflowState.copiedCaption = true;
  elements.checkCaption.checked = true;
  updateWorkflowGuide();
  setStatus("Caption copied");
});

elements.openFacebook.addEventListener("click", (event) => {
  if (!workflowState.copiedCaption) {
    event.preventDefault();
    setStatus("Copy the caption before opening Facebook");
    return;
  }
  workflowState.openedFacebook = true;
  elements.checkManualPost.checked = true;
  updateWorkflowGuide();
});

elements.zipDownload.addEventListener("click", (event) => {
  if (elements.zipDownload.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
  }
  workflowState.downloadedAssets = true;
  updateWorkflowGuide();
});

elements.facebookInput.addEventListener("input", () => {
  workflowState.enteredFacebookUrl = elements.facebookInput.value.trim().length > 0;
  updateWorkflowGuide();
});

for (const checkbox of [elements.checkCaption, elements.checkPhotos, elements.checkManualPost]) {
  checkbox.addEventListener("change", updateWorkflowGuide);
}

elements.logForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const facebookUrl = elements.facebookInput.value.trim();
  if (!facebookUrl) {
    setStatus("Paste the live Facebook URL first");
    return;
  }
  const job = selectedJob();
  const jobId = job.id;
  const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/mark-posted`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ facebook_url: facebookUrl }),
  }));
  await authFetch("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: activeProperty, facebook_url: facebookUrl }),
  });
  job.status = "posted_today";
  workflowState.loggedPost = true;
  addActivity(response.ok ? "Facebook URL logged to tracker." : "Demo tracker sync completed.");
  renderAll();
  setStatus(response.ok ? "Logged" : "Demo logged");
});

doc.querySelectorAll(".queue-button").forEach((button) => {
  button.addEventListener("click", () => {
    doc.querySelectorAll(".queue-button").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    renderJobList(button.dataset.queue);
  });
});

async function loadSession() {
  const response = await jsonFromResponse(await authFetch("/api/session"));
  if (response.ok && response.data.user) {
    session = response.data;
  }
  renderSession();
}

async function loadJobs() {
  const response = await jsonFromResponse(await authFetch("/api/jobs"));
  if (response.ok && Array.isArray(response.data.jobs)) {
    jobs = response.data.jobs.map((job) => ({ ...demoJobs[0], ...job }));
  }
  if (!jobs.some((job) => job.id === selectedJobId)) {
    selectedJobId = jobs[0].id;
  }
  renderAll();
  setStatus(response.ok ? "Live queue loaded" : "Demo queue loaded");
}

async function createOrPrepareJob() {
  const payload = formPayload();
  const created = await requestJson("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (created.ok && created.data.id) {
    jobs = [created.data, ...jobs];
    selectedJobId = created.data.id;
  }
  await prepareSelectedJob("form");
}

async function prepareSelectedJob(source) {
  const job = selectedJob();
  setStatus("Running pipeline");
  const jobId = job.id;
  await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/validate`, { method: "POST" }));
  const prepared = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/prepare`, { method: "POST" }));
  const legacy = await authFetch("/api/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: elements.propertyInput.value.trim() || job.property_name }),
  });
  if (prepared.ok) {
    Object.assign(job, prepared.data);
  } else if (legacy.ok) {
    Object.assign(job, await legacy.json());
  }
  job.status = source === "form" ? "waiting_approval" : "ready_to_post";
  selectedJobId = job.id;
  workflowState.prepared = true;
  workflowState.generatedCaption = Boolean(job.caption);
  addActivity("Pipeline prepared Drive assets and caption workspace.");
  renderAll();
  setStatus(prepared.ok || legacy.ok ? "Pipeline ready" : "Demo pipeline ready");
}

async function requestJson(url, options = {}) {
  try {
    return await jsonFromResponse(await authFetch(url, options));
  } catch (error) {
    if (error instanceof Error) {
      return { ok: false, data: { detail: error.message } };
    }
    throw error;
  }
}

async function jsonFromResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : { detail: await response.text() };
  return { ok: response.ok, data };
}

async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (currentUser) {
    const token = await currentUser.getIdToken();
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(url, { ...options, headers });
}

function renderAll() {
  renderSession();
  renderCounts();
  renderJobList(activeQueue());
  renderSelectedJob();
  updateWorkflowGuide();
}

function renderSession() {
  const role = session.user?.role || "user";
  const name = session.user?.display_name || session.user?.email || "Demo operator";
  elements.roleBadge.textContent = role;
  elements.userLabel.textContent = `${name} · ${roleCopy(role)} · ${session.firebase_project_id || "demo"}`;
  elements.metricRole.textContent = role === "maam_jean" ? "Ma'am Jean" : role;
}

function renderCounts() {
  const counts = countJobs();
  elements.countAssigned.textContent = String(counts.assigned_today);
  elements.countWaiting.textContent = String(counts.waiting_approval);
  elements.countReady.textContent = String(counts.ready_to_post);
  elements.countPosted.textContent = String(counts.posted_today);
}

function renderJobList(queueName) {
  elements.jobList.replaceChildren();
  const visibleJobs = jobs.filter((job) => queueName === "assigned_today" || job.status === queueName);
  for (const job of visibleJobs) {
    const row = elements.jobTemplate.content.cloneNode(true).querySelector(".job-row");
    row.classList.toggle("selected", job.id === selectedJobId);
    row.querySelector("strong").textContent = job.property_name;
    row.querySelector("em").textContent = job.id;
    row.querySelector(".job-row-meta").textContent = `${job.assigned_by} to ${job.operator} · Due ${job.due_date}`;
    row.querySelector(".job-row-status").textContent = statusLabel(job.status);
    row.addEventListener("click", () => selectJob(job.id));
    elements.jobList.append(row);
  }
  if (visibleJobs.length === 0) {
    const empty = doc.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No jobs in this queue.";
    elements.jobList.append(empty);
  }
}

function renderSelectedJob() {
  const job = selectedJob();
  activeProperty = job.property_name;
  activeCaption = job.caption || "";
  elements.selectedPropertyTitle.textContent = job.property_name;
  elements.selectedPropertyMeta.textContent = `${job.assigned_by} · ${job.operator} · ${job.id}`;
  elements.propertyInput.value = job.property_name;
  elements.assignedBy.value = job.assigned_by;
  elements.operatorName.value = job.operator;
  elements.dueDate.value = job.due_date;
  elements.driveUrl.value = job.drive_url;
  elements.validationState.textContent = statusLabel(job.status);
  elements.validationState.className = `status-badge ${job.status === "ready_to_post" ? "ready" : "review"}`;
  renderValidation(job);
  renderImages(job.images || []);
  renderCaption(job);
  renderTracker(job);
  renderActivity(job.activity || []);
}

function renderValidation(job) {
  const checks = [
    ["Drive folder", job.drive_url ? "Passed" : "Needs attention"],
    ["Caption document", job.caption_document_name ? "Passed" : "Needs attention"],
    ["Photo minimum", selectedImages(job).length >= 3 ? "Passed" : "Needs attention"],
  ];
  elements.validationResults.replaceChildren(...checks.map(([label, state]) => {
    const item = doc.createElement("p");
    item.innerHTML = `<strong>${label}</strong><span>${state}</span>`;
    return item;
  }));
  elements.metricValidation.textContent = checks.every(([, state]) => state === "Passed") ? "Ready" : "Review";
}

function renderImages(images) {
  const job = selectedJob();
  elements.imageGallery.replaceChildren();
  for (const image of images) {
    const card = elements.imageTemplate.content.cloneNode(true).querySelector(".photo-card");
    card.classList.toggle("selected", Boolean(image.selected));
    card.querySelector(".photo-preview").style.backgroundImage = `linear-gradient(rgba(1,105,111,.12), rgba(1,105,111,.04)), url("${image.url}")`;
    card.querySelector(".photo-meta").textContent = image.name;
    card.addEventListener("click", () => {
      image.selected = !image.selected;
      renderImages(job.images || []);
      updateWorkflowGuide();
    });
    elements.imageGallery.append(card);
  }
  const selectedCount = selectedImages(job).length;
  elements.selectedPhotoBadge.textContent = `${selectedCount} selected`;
  elements.metricPhotos.textContent = `${selectedCount} selected`;
  elements.checkPhotos.checked = selectedCount >= 3;
  elements.zipDownload.href = `/prepared/${encodeURIComponent(job.property_name)}.zip`;
  elements.zipDownload.removeAttribute("aria-disabled");
}

function renderCaption(job) {
  activeCaption = job.caption || demoJobs[0].caption;
  elements.sourceDocName.textContent = `Source caption document: ${job.caption_document_name || "No document loaded"}`;
  elements.captionSourceOutput.textContent = job.caption_details || "No caption details found.";
  elements.captionOutput.textContent = activeCaption;
  elements.captionVariants.replaceChildren();
  const variants = normalizeVariants(job);
  for (const [index, variant] of variants.entries()) {
    const article = doc.createElement("article");
    article.className = "caption-variant";
    article.innerHTML = `<h3>Variant ${index + 1}</h3><p></p><button type="button">Use variant</button>`;
    article.querySelector("p").textContent = variant;
    article.querySelector("button").addEventListener("click", () => {
      job.caption = variant;
      renderCaption(job);
      addActivity(`Variant ${index + 1} selected as final caption.`);
    });
    elements.captionVariants.append(article);
  }
  const clean = validateCaption(activeCaption);
  elements.metricCaption.textContent = clean ? "APG clean" : "Needs edit";
}

function renderTracker(job) {
  elements.trackerRow.value = `${job.id} | ${job.property_name} | ${job.operator} | ${statusLabel(job.status)} | Facebook URL pending`;
  elements.dailyReport.value = `${job.property_name}: assets selected, caption checked, manual publish checklist pending.`;
}

function renderActivity(activity) {
  elements.activityLog.replaceChildren();
  for (const item of activity) {
    const row = doc.createElement("li");
    row.innerHTML = `<time>${item.at}</time><span></span>`;
    row.querySelector("span").textContent = item.text;
    elements.activityLog.append(row);
  }
  elements.activityCount.textContent = `${activity.length} events`;
}

function updateWorkflowGuide() {
  const canDownload = workflowState.prepared;
  const canCopyCaption = workflowState.downloadedAssets && workflowState.generatedCaption;
  const canOpenFacebook = workflowState.copiedCaption;
  const canEnterFacebookUrl = workflowState.copiedCaption && workflowState.openedFacebook && elements.checkManualPost.checked;
  const canLogPost = canEnterFacebookUrl && workflowState.enteredFacebookUrl && elements.checkCaption.checked && elements.checkPhotos.checked;
  elements.copyCaption.disabled = !canCopyCaption;
  elements.openFacebook.classList.toggle("disabled", !canOpenFacebook);
  elements.openFacebook.setAttribute("aria-disabled", String(!canOpenFacebook));
  elements.facebookUrlGroup.hidden = !canEnterFacebookUrl;
  elements.logButton.disabled = !canLogPost;
  setStepState("download", workflowState.downloadedAssets, canDownload);
  setStepState("copy", workflowState.copiedCaption, canCopyCaption);
  setStepState("facebook", workflowState.openedFacebook, canOpenFacebook);
  setStepState("url", workflowState.enteredFacebookUrl, canEnterFacebookUrl);
  setStepState("log", workflowState.loggedPost, canLogPost);
}

function setStepState(name, complete, enabled) {
  const step = doc.querySelector(`.workflow-step[data-step="${name}"]`);
  if (!step) {
    return;
  }
  step.dataset.state = complete ? "complete" : enabled ? "active" : "locked";
  const marker = step.querySelector(".step-marker");
  marker.textContent = complete ? "Done" : marker.dataset.number;
}

function startNewIntake() {
  selectedJobId = jobs[0].id;
  elements.propertyInput.value = "";
  elements.assignedBy.value = "Ma'am Jean";
  elements.operatorName.value = "";
  elements.driveUrl.value = "";
  elements.validationResults.innerHTML = "<p><strong>New intake</strong><span>Ready for property details</span></p>";
  setStatus("New intake ready");
}

function selectJob(jobId) {
  selectedJobId = jobId;
  resetWorkflowState();
  renderAll();
  loadActivity(jobId);
}

async function loadActivity(jobId) {
  try {
    const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/activity`));
    if (response.ok && Array.isArray(response.data.activity)) {
      selectedJob().activity = response.data.activity;
      renderActivity(response.data.activity);
    }
  } catch (error) {
    if (!(error instanceof Error)) {
      throw error;
    }
  }
}

function selectedJob() {
  return jobs.find((job) => job.id === selectedJobId) || jobs[0];
}

function selectedImages(job) {
  return (job.images || []).filter((image) => image.selected);
}

function normalizeVariants(data) {
  if (Array.isArray(data)) {
    return data;
  }
  if (Array.isArray(data.variants)) {
    return data.variants;
  }
  if (Array.isArray(data.captions)) {
    return data.captions;
  }
  return [];
}

function validateCaption(caption) {
  const lower = caption.toLowerCase();
  return !lower.includes("least term") && !lower.includes("negotiables") && !/[\u{1f300}-\u{1faff}]/u.test(caption);
}

function formPayload() {
  return {
    property_name: elements.propertyInput.value.trim(),
    assigned_by: elements.assignedBy.value.trim() || "Ma'am Jean",
    operator: elements.operatorName.value.trim() || "Unassigned",
    due_date: elements.dueDate.value,
    drive_url: elements.driveUrl.value.trim(),
  };
}

function countJobs() {
  return {
    assigned_today: jobs.length,
    waiting_approval: jobs.filter((job) => job.status === "waiting_approval").length,
    ready_to_post: jobs.filter((job) => job.status === "ready_to_post").length,
    posted_today: jobs.filter((job) => job.status === "posted_today").length,
  };
}

function activeQueue() {
  return doc.querySelector(".queue-button.active")?.dataset.queue || "assigned_today";
}

function statusLabel(status) {
  return String(status).replaceAll("_", " ");
}

function roleCopy(role) {
  if (role === "admin") {
    return "admin controls";
  }
  if (role === "maam_jean") {
    return "Ma'am Jean approvals";
  }
  return "user posting lane";
}

function addActivity(text) {
  const job = selectedJob();
  const at = new Intl.DateTimeFormat("en-PH", { hour: "2-digit", minute: "2-digit" }).format(new Date());
  job.activity = [{ at, text }, ...(job.activity || [])];
  renderActivity(job.activity);
}

function resetWorkflowState() {
  workflowState.prepared = true;
  workflowState.downloadedAssets = false;
  workflowState.generatedCaption = Boolean(selectedJob().caption);
  workflowState.copiedCaption = false;
  workflowState.openedFacebook = false;
  workflowState.enteredFacebookUrl = false;
  workflowState.loggedPost = false;
  elements.facebookInput.value = "";
  elements.checkCaption.checked = false;
  elements.checkManualPost.checked = false;
}

function setStatus(message) {
  elements.connectionStatus.textContent = message;
}

doc.documentElement.dataset.theme = localStorage.getItem("apg-theme") || "light";
renderAll();
