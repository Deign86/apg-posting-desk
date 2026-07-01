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
const el = (id) => doc.getElementById(id);

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};
const hostedDomain = (import.meta.env.VITE_APG_GOOGLE_DOMAIN || "").trim();
const shouldRestrictDomain = hostedDomain && !hostedDomain.endsWith(".example");
const firebaseReady = Object.values(firebaseConfig).every(Boolean);
const auth = firebaseReady ? getAuth(initializeApp(firebaseConfig)) : null;
const provider = new GoogleAuthProvider();
if (shouldRestrictDomain) {
  provider.setCustomParameters({ hd: hostedDomain });
}

let currentUser = null;
let selectedRole = (doc.querySelector(".role-option.active") || {}).dataset?.role || "user";
let session = {
  firebase_project_id: firebaseConfig.projectId || "demo",
  user: { uid: "demo-operator", email: "demo@apg.local", role: selectedRole, display_name: "Demo operator" },
};

const demoJobs = [
  {
    id: "APG-2401",
    propertyName: "Novaliches, 440 Bagbag",
    assignedBy: "Ma'am Jean",
    operator: "Deign",
    dueDate: "2026-06-30",
    driveUrl: "https://drive.google.com/demo/bagbag",
    imageCount: 4,
    hasCaptionDoc: true,
    docName: "Bagbag-caption.docx",
    status: "ready-to-post",
    trackerStatus: "pending",
    details: "Townhouse for sale in Novaliches with clean title, near transport, schools, and daily essentials.",
    images: [
      { id: "img1", label: "front-view.jpg", selected: true },
      { id: "img2", label: "living-area.jpg", selected: true },
      { id: "img3", label: "kitchen.jpg", selected: true },
      { id: "img4", label: "street-access.jpg", selected: false },
    ],
    variants: [
      "Ready for posting: Novaliches, 440 Bagbag with practical access to transport, schools, and essentials. Message APG for viewing details.",
      "APG listing prepared for Novaliches, 440 Bagbag. Review the photos, confirm details, and coordinate viewing through the assigned operator.",
      "For Facebook posting: Novaliches, 440 Bagbag. Clean property details, selected photos, and tracker preview are ready for manual publishing.",
    ],
    finalCaption: "Novaliches, 440 Bagbag is ready for viewing. This property offers practical access to transport, schools, and daily essentials. Message APG for details and schedule coordination.",
    facebookLink: "",
    activity: [
      { at: "09:18", text: "Ma'am Jean assigned APG-2401 to Deign." },
      { at: "09:24", text: "Drive validation passed with 4 images and 1 caption doc." },
      { at: "09:32", text: "Caption variants generated with APG rule check." },
    ],
  },
  {
    id: "APG-2402",
    propertyName: "Fairview, Dahlia Avenue",
    assignedBy: "Admin",
    operator: "Rhea",
    dueDate: "2026-06-30",
    driveUrl: "https://drive.google.com/demo/fairview",
    imageCount: 2,
    hasCaptionDoc: true,
    docName: "Fairview-caption.docx",
    status: "missing-assets",
    trackerStatus: "blocked",
    details: "Condo unit near Commonwealth corridor. Needs price confirmation before posting.",
    images: [
      { id: "img1", label: "unit-main.jpg", selected: true },
      { id: "img2", label: "amenity.jpg", selected: false },
    ],
    variants: [],
    finalCaption: "",
    facebookLink: "",
    activity: [{ at: "10:05", text: "Validation flagged missing third selected photo." }],
  },
];

let jobs = [...demoJobs];
let activeJobId = jobs[0].id;

const refs = {
  jobList: el("jobList"),
  propertyName: el("propertyName"),
  assignedBy: el("assignedBy"),
  operatorName: el("operatorName"),
  dueDate: el("dueDate"),
  driveUrl: el("driveUrl"),
  validationSteps: el("validationSteps"),
  thumbs: el("thumbs"),
  captionDetails: el("captionDetails"),
  finalCaption: el("finalCaption"),
  captionVariants: el("captionVariants"),
  imageCounterBadge: el("imageCounterBadge"),
  assetSummary: el("assetSummary"),
  captionRuleResult: el("captionRuleResult"),
  folderStatusBadge: el("folderStatusBadge"),
  metricProperty: el("metricProperty"),
  metricAgent: el("metricAgent"),
  metricAssets: el("metricAssets"),
  metricDoc: el("metricDoc"),
  metricStatus: el("metricStatus"),
  metricTracker: el("metricTracker"),
  publishHelper: el("publishHelper"),
  facebookLink: el("facebookLink"),
  trackerPreview: el("trackerPreview"),
  dailyReportPreview: el("dailyReportPreview"),
  trackerStatus: el("trackerStatus"),
  activityLog: el("activityLog"),
  toast: el("toast"),
  checkCaptionApproved: el("checkCaptionApproved"),
  checkPhotosSelected: el("checkPhotosSelected"),
  checkPostedToFacebook: el("checkPostedToFacebook"),
  assignedCount: el("assignedCount"),
  approvalCount: el("approvalCount"),
  readyCount: el("readyCount"),
  postedCount: el("postedCount"),
  sourceDocName: el("sourceDocName"),
  captionSourceOutput: el("captionSourceOutput"),
  zipDownload: el("zipDownload"),
  connectionStatus: el("connectionStatus"),
  roleBadge: el("roleBadge"),
  userLabel: el("userLabel"),
  signInButton: el("signInButton"),
  signOutButton: el("signOutButton"),
  sessionTitle: el("sessionTitle"),
  facebookUrlGroup: el("facebookUrlGroup"),
  logButton: el("logPostButton"),
};

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

function activeJob() {
  return jobs.find((j) => j.id === activeJobId) || jobs[0];
}

function log(message) {
  const item = doc.createElement("div");
  item.className = "log-item";
  item.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + " — " + message;
  refs.activityLog.prepend(item);
}

function toast(message) {
  refs.toast.textContent = message;
  refs.toast.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => refs.toast.classList.remove("show"), 2200);
}

async function copyText(text, message) {
  try {
    await navigator.clipboard.writeText(text);
    toast(message);
  } catch {
    toast("Clipboard unavailable in this environment.");
  }
}

function statusBadge(status) {
  const map = {
    "missing-assets": ["Missing assets", "err"],
    "ready-for-review": ["Ready for review", "warn"],
    "ready-to-post": ["Ready to post", "ready"],
    "posted": ["Posted", "ready"],
    "posted_today": ["Posted today", "ready"],
    "waiting_approval": ["Waiting approval", "warn"],
  };
  return map[status] || [status.replaceAll("-", " ").replaceAll("_", " "), ""];
}

function normalizeJob(raw) {
  const images = Array.isArray(raw.images)
    ? raw.images.map((img, idx) => ({
        id: img.id || `img${idx + 1}`,
        label: img.name || img.label || `Photo ${idx + 1}`,
        selected: Boolean(img.selected),
        url: img.url || "/icon-192.png",
      }))
    : [];
  return {
    id: raw.id || raw.property_id || "unknown",
    propertyName: raw.property_name || raw.propertyName || "Unnamed property",
    assignedBy: raw.assigned_by || raw.assignedBy || "Ma'am Jean",
    operator: raw.operator || "Unassigned",
    dueDate: raw.due_date || raw.dueDate || new Date().toISOString().slice(0, 10),
    driveUrl: raw.drive_url || raw.driveUrl || "",
    imageCount: raw.image_count ?? raw.imageCount ?? images.length,
    hasCaptionDoc: Boolean(raw.caption_document_name || raw.hasCaptionDoc || raw.caption_details || raw.details),
    docName: raw.caption_document_name || raw.docName || "",
    status: (raw.status || "missing-assets").replaceAll("_", "-"),
    trackerStatus: raw.tracker_status || raw.trackerStatus || "pending",
    details: raw.caption_details || raw.details || "",
    images,
    variants: normalizeVariants(raw),
    finalCaption: raw.caption || raw.finalCaption || "",
    facebookLink: raw.facebook_url || raw.facebookLink || "",
    activity: Array.isArray(raw.activity) ? raw.activity : [],
  };
}

function normalizeVariants(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data.variants)) return data.variants;
  if (Array.isArray(data.captions)) return data.captions;
  return [];
}

function renderJobList() {
  refs.jobList.innerHTML = "";
  jobs.forEach((job) => {
    const [label, cls] = statusBadge(job.status);
    const btn = doc.createElement("button");
    btn.className = "job-row" + (job.id === activeJobId ? " active" : "");
    btn.type = "button";
    btn.innerHTML = `
      <div class="row-top"><strong>${job.propertyName}</strong><span class="badge ${cls}">${label}</span></div>
      <div class="muted">${job.id}</div>
      <div class="inline faint mono"><span>${job.assignedBy}</span><span>${job.dueDate}</span></div>
    `;
    btn.addEventListener("click", () => {
      activeJobId = job.id;
      resetWorkflowState();
      hydrateForm();
      renderAll();
      loadActivity(job.id);
      log("Switched to " + job.propertyName);
    });
    refs.jobList.appendChild(btn);
  });
  refs.assignedCount.textContent = jobs.length;
  refs.approvalCount.textContent = jobs.filter((j) => j.status === "ready-for-review" || j.status === "waiting-approval").length;
  refs.readyCount.textContent = jobs.filter((j) => j.status === "ready-to-post").length;
  refs.postedCount.textContent = jobs.filter((j) => j.status === "posted" || j.status === "posted_today").length;
}

function hydrateForm() {
  const job = activeJob();
  refs.propertyName.value = job.propertyName;
  refs.assignedBy.value = job.assignedBy;
  refs.operatorName.value = job.operator;
  refs.dueDate.value = job.dueDate;
  refs.driveUrl.value = job.driveUrl;
  refs.captionDetails.value = job.details;
  refs.finalCaption.value = job.finalCaption || "";
  refs.facebookLink.value = job.facebookLink || "";
  refs.checkCaptionApproved.checked = !!job.finalCaption;
  refs.checkPhotosSelected.checked = job.images.filter((i) => i.selected).length >= 3;
  refs.checkPostedToFacebook.checked = !!job.facebookLink;
  refs.sourceDocName.textContent = `Source caption document: ${job.docName || "No document loaded"}`;
  refs.captionSourceOutput.textContent = job.details || "Fetch a property to review the extracted DOCX details here.";
  refs.zipDownload.href = `/prepared/${encodeURIComponent(job.propertyName)}.zip`;
  if (job.images.length > 0) {
    refs.zipDownload.removeAttribute("aria-disabled");
  }
  workflowState.generatedCaption = Boolean(job.finalCaption || job.variants.length);
}

function syncFormToJob() {
  const job = activeJob();
  job.propertyName = refs.propertyName.value.trim();
  job.assignedBy = refs.assignedBy.value.trim();
  job.operator = refs.operatorName.value.trim();
  job.dueDate = refs.dueDate.value;
  job.driveUrl = refs.driveUrl.value.trim();
  job.details = refs.captionDetails.value.trim();
  job.finalCaption = refs.finalCaption.value.trim();
  job.facebookLink = refs.facebookLink.value.trim();
}

function renderValidation() {
  const job = activeJob();
  const checks = [
    { label: "Drive folder URL provided", ok: !!job.driveUrl },
    { label: "At least 3 images found", ok: job.imageCount >= 3 },
    { label: "Caption details document found", ok: !!job.hasCaptionDoc },
    { label: "Operator and due date set", ok: !!job.operator && !!job.dueDate },
  ];
  refs.validationSteps.innerHTML = "";
  checks.forEach((check, idx) => {
    const div = doc.createElement("div");
    div.className = "step " + (check.ok ? "done" : idx === 0 ? "current" : "");
    div.innerHTML = `<strong>${check.label}</strong><div class="muted">${check.ok ? "Passed" : "Needs attention"}</div>`;
    refs.validationSteps.appendChild(div);
  });
  const allGood = checks.every((c) => c.ok);
  refs.folderStatusBadge.className = "badge " + (allGood ? "ready" : "err");
  refs.folderStatusBadge.textContent = allGood ? "Validation passed" : "Validation blocked";
}

function renderThumbs() {
  const job = activeJob();
  refs.thumbs.innerHTML = "";
  job.images.forEach((img, index) => {
    const card = doc.createElement("div");
    card.className = "thumb" + (img.selected ? " active" : "");
    card.innerHTML = `
      <button type="button" data-id="${img.id}">
        <div class="photo">Photo ${index + 1}</div>
        <div class="thumb-meta"><strong>${img.label}</strong><span class="muted mono">${img.selected ? "selected" : "not selected"}</span></div>
      </button>
    `;
    card.querySelector("button").addEventListener("click", () => {
      img.selected = !img.selected;
      renderThumbs();
      renderMetrics();
      updateWorkflowGuide();
      log((img.selected ? "Selected " : "Deselected ") + img.label);
    });
    refs.thumbs.appendChild(card);
  });
  const selected = job.images.filter((i) => i.selected).length;
  refs.imageCounterBadge.textContent = `${selected} selected`;
  refs.assetSummary.textContent = `${job.imageCount} images detected in folder. ${selected} currently selected for the post package. Caption document: ${job.hasCaptionDoc ? job.docName : "missing"}.`;
  refs.checkPhotosSelected.checked = selected >= 3;
}

function buildVariants(details) {
  const compact = details.replace(/\n+/g, "; ");
  return [
    `For lease: ${compact}. For inquiries and viewing schedule, message Alpha Premier Realty.`,
    `Available property listing from Alpha Premier Realty. ${compact}. Contact us for details and site viewing arrangements.`,
    `Featured property: ${compact}. Reach out to Alpha Premier Realty for inquiries, availability, and viewing coordination.`,
  ];
}

function checkCaptionRules(text) {
  const issues = [];
  const lowered = text.toLowerCase();
  if (/[^\w\s.,:/()\-₱#]/u.test(text)) issues.push("Possible emoji or unsupported symbol detected.");
  if (lowered.includes("negotiables")) issues.push("Contains banned term: negotiables.");
  if (lowered.includes("negotioables")) issues.push("Contains banned term: negotioables.");
  if (lowered.includes("least term")) issues.push("Contains banned term: least term.");
  return issues;
}

function renderVariants() {
  const job = activeJob();
  refs.captionVariants.innerHTML = "";
  job.variants.forEach((text, idx) => {
    const card = doc.createElement("div");
    card.className = "variant" + (job.finalCaption === text ? " active" : "");
    card.innerHTML = `
      <div class="status-line"><strong>Variant ${idx + 1}</strong><span class="badge">candidate</span></div>
      <div class="variant-text">${text}</div>
      <div class="toolbar">
        <button class="mini-btn" data-use="${idx}" type="button">Use this caption</button>
        <button class="mini-btn" data-copy="${idx}" type="button">Copy</button>
      </div>
    `;
    card.querySelector("[data-use]").addEventListener("click", () => {
      job.finalCaption = text;
      refs.finalCaption.value = text;
      refs.checkCaptionApproved.checked = true;
      renderVariants();
      renderMetrics();
      updateWorkflowGuide();
      log("Selected caption variant " + (idx + 1));
      toast("Caption applied.");
    });
    card.querySelector("[data-copy]").addEventListener("click", () => copyText(text, "Caption copied."));
    refs.captionVariants.appendChild(card);
  });
}

function renderMetrics() {
  const job = activeJob();
  refs.metricProperty.textContent = job.propertyName || "-";
  refs.metricAgent.textContent = "Assigned by " + (job.assignedBy || "-");
  refs.metricAssets.textContent = `${job.imageCount} images / ${job.images.filter((i) => i.selected).length} selected`;
  refs.metricDoc.textContent = job.hasCaptionDoc ? job.docName : "Caption file missing";
  refs.metricStatus.textContent = job.status.replaceAll("-", " ");
  refs.metricTracker.textContent = "Tracker sync " + job.trackerStatus;
  refs.publishHelper.textContent = job.facebookLink ? "Facebook URL captured. Ready to prepare tracker updates." : "Waiting for approval and manual publish.";
}

function prepareTrackerPreview() {
  const job = activeJob();
  const selectedImages = job.images.filter((i) => i.selected).length;
  refs.trackerPreview.value = [
    job.id,
    job.propertyName,
    job.assignedBy,
    job.operator,
    job.dueDate,
    selectedImages + " selected images",
    job.facebookLink || "[pending facebook link]",
    job.status,
    job.trackerStatus,
  ].join(" | ");

  refs.dailyReportPreview.value = `Posted property: ${job.propertyName}\nAssigned by: ${job.assignedBy}\nOperator: ${job.operator}\nAsset package: ${selectedImages} selected images; caption doc ${job.hasCaptionDoc ? "present" : "missing"}\nFacebook URL: ${job.facebookLink || "[pending]"}\nStatus: ${job.status}`;
  refs.trackerStatus.textContent = "Preview prepared. Ready for copy or future API sync.";
  log("Prepared tracker and daily report preview");
}

function renderActivity(activity) {
  refs.activityLog.innerHTML = "";
  (activity || []).forEach((item) => {
    const row = doc.createElement("div");
    row.className = "log-item";
    row.textContent = `${item.at || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })} — ${item.text}`;
    refs.activityLog.appendChild(row);
  });
}

function renderAll() {
  renderSession();
  renderJobList();
  hydrateForm();
  renderValidation();
  renderThumbs();
  renderVariants();
  renderMetrics();
  prepareTrackerPreview();
  updateWorkflowGuide();
}

function renderSession() {
  const role = session.user?.role || "user";
  const name = session.user?.display_name || session.user?.email || "Demo operator";
  refs.roleBadge.textContent = role;
  refs.userLabel.textContent = `${name} · ${roleCopy(role)} · ${session.firebase_project_id || "demo"}`;
  refs.sessionTitle.textContent = "Role access";
  applyRoleGating();
}

function roleCopy(role) {
  if (role === "admin") return "admin controls";
  if (role === "maam_jean") return "Ma'am Jean approvals";
  return "user posting lane";
}

function updateWorkflowGuide() {
  const job = activeJob();
  const canDownload = workflowState.prepared && job.images.length > 0;
  const canCopyCaption = workflowState.downloadedAssets && workflowState.generatedCaption;
  const canOpenFacebook = workflowState.copiedCaption;
  const canEnterFacebookUrl = workflowState.copiedCaption && workflowState.openedFacebook && refs.checkPostedToFacebook.checked;
  const canLogPost = canEnterFacebookUrl && workflowState.enteredFacebookUrl && refs.checkCaptionApproved.checked && refs.checkPhotosSelected.checked;
  refs.facebookUrlGroup.hidden = !canEnterFacebookUrl;
  refs.logButton.disabled = !canLogPost;
  setStepState("download", workflowState.downloadedAssets, canDownload);
  setStepState("copy", workflowState.copiedCaption, canCopyCaption);
  setStepState("facebook", workflowState.openedFacebook, canOpenFacebook);
  setStepState("url", workflowState.enteredFacebookUrl, canEnterFacebookUrl);
  setStepState("log", workflowState.loggedPost, canLogPost);
}

function setStepState(name, complete, enabled) {
  const step = doc.querySelector(`.workflow-step[data-step="${name}"]`);
  if (!step) return;
  step.dataset.state = complete ? "complete" : enabled ? "active" : "locked";
  const marker = step.querySelector(".step-marker");
  marker.textContent = complete ? "Done" : marker.dataset.number;
}

function resetWorkflowState() {
  const job = activeJob();
  workflowState.prepared = true;
  workflowState.downloadedAssets = false;
  workflowState.generatedCaption = Boolean(job.finalCaption || job.variants.length);
  workflowState.copiedCaption = false;
  workflowState.openedFacebook = false;
  workflowState.enteredFacebookUrl = false;
  workflowState.loggedPost = false;
  refs.facebookLink.value = "";
  refs.checkCaptionApproved.checked = false;
  refs.checkPostedToFacebook.checked = false;
}

async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (currentUser) {
    const token = await currentUser.getIdToken();
    headers.set("Authorization", `Bearer ${token}`);
  }
  headers.set("X-Demo-Role", selectedRole);
  return fetch(url, { ...options, headers });
}

async function jsonFromResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : { detail: await response.text() };
  return { ok: response.ok, data };
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
    jobs = response.data.jobs.map((job) => ({ ...demoJobs[0], ...normalizeJob(job) }));
  }
  if (!jobs.some((job) => job.id === activeJobId)) {
    activeJobId = jobs[0].id;
  }
  renderAll();
  setStatus(response.ok ? "Live queue loaded" : "Demo queue loaded");
}

async function loadActivity(jobId) {
  try {
    const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/activity`));
    if (response.ok && Array.isArray(response.data.activity)) {
      const job = activeJob();
      job.activity = response.data.activity;
      renderActivity(job.activity);
    }
  } catch (error) {
    if (!(error instanceof Error)) throw error;
  }
}

async function createOrPrepareJob() {
  const payload = formPayload();
  const created = await requestJson("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (created.ok && created.data.id) {
    jobs = [normalizeJob(created.data), ...jobs];
    activeJobId = created.data.id;
  }
  await prepareSelectedJob("form");
}

async function prepareSelectedJob(source) {
  const job = activeJob();
  setStatus("Running pipeline");
  const jobId = job.id;
  await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/validate`, { method: "POST" }));
  const prepared = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/prepare`, { method: "POST" }));
  const legacy = await authFetch("/api/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: refs.propertyName.value.trim() || job.propertyName }),
  });
  if (prepared.ok) {
    Object.assign(job, normalizeJob(prepared.data));
  } else if (legacy.ok) {
    Object.assign(job, normalizeJob(await legacy.json()));
  }
  job.status = source === "form" ? "waiting_approval" : "ready-to-post";
  activeJobId = job.id;
  workflowState.prepared = true;
  workflowState.generatedCaption = Boolean(job.finalCaption || job.variants.length);
  hydrateForm();
  renderAll();
  setStatus(prepared.ok || legacy.ok ? "Pipeline ready" : "Demo pipeline ready");
}

function formPayload() {
  return {
    property_name: refs.propertyName.value.trim(),
    assigned_by: refs.assignedBy.value.trim() || "Ma'am Jean",
    operator: refs.operatorName.value.trim() || "Unassigned",
    due_date: refs.dueDate.value,
    drive_url: refs.driveUrl.value.trim(),
  };
}

function setStatus(message) {
  refs.connectionStatus.textContent = message;
}

if (auth) {
  onAuthStateChanged(auth, async (user) => {
    currentUser = user;
    refs.signInButton.hidden = Boolean(user);
    refs.signOutButton.hidden = !user;
    const roleSelector = doc.getElementById("role-selector");
    if (roleSelector) roleSelector.hidden = Boolean(user);
    if (user) applyRoleGating();
    await loadSession();
    await loadJobs();
  });
} else {
  refs.userLabel.textContent = "Demo mode: Firebase config not loaded. Ma'am Jean workflow is available.";
}

refs.signInButton.addEventListener("click", async () => {
  if (!auth) {
    setStatus("Firebase config missing; staying in demo mode");
    return;
  }
  await signInWithPopup(auth, provider);
});

refs.signOutButton.addEventListener("click", async () => {
  if (auth) {
    await signOut(auth);
  }
  const roleSelector = doc.getElementById("role-selector");
  if (roleSelector) roleSelector.hidden = false;
});

el("themeToggle").addEventListener("click", () => {
  const root = doc.documentElement;
  const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", nextTheme);
  localStorage.setItem("apg-theme", nextTheme);
});

doc.querySelectorAll("[data-role-option]").forEach((btn) => {
  btn.addEventListener("click", () => {
    doc.querySelectorAll("[data-role-option]").forEach((b) => {
      b.classList.remove("active");
      b.setAttribute("aria-pressed", "false");
    });
    btn.classList.add("active");
    btn.setAttribute("aria-pressed", "true");
    selectedRole = btn.dataset.role || "user";
    session.user.role = selectedRole;
    renderSession();
    applyRoleGating();
  });
});

function applyRoleGating() {
  const isAdmin = selectedRole === "admin";
  doc.querySelectorAll("[data-admin-only]").forEach((el) => {
    el.hidden = !isAdmin;
  });
}

doc.querySelectorAll(".nav-btn").forEach((button) => {
  button.addEventListener("click", () => {
    doc.querySelectorAll(".nav-btn").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
  });
});

["propertyName", "assignedBy", "operatorName", "dueDate", "driveUrl", "captionDetails", "finalCaption", "facebookLink"].forEach((id) => {
  el(id).addEventListener("input", () => {
    syncFormToJob();
    renderMetrics();
    renderJobList();
    if (id === "facebookLink") {
      workflowState.enteredFacebookUrl = refs.facebookLink.value.trim().length > 0;
      refs.checkPostedToFacebook.checked = workflowState.enteredFacebookUrl;
      updateWorkflowGuide();
    }
  });
});

el("validateAssetsBtn").addEventListener("click", () => {
  syncFormToJob();
  const job = activeJob();
  job.hasCaptionDoc = refs.captionDetails.value.trim().length > 0;
  job.imageCount = job.images.length;
  renderAll();
  log("Ran validation for " + job.propertyName);
  toast(job.status === "missing-assets" ? "Validation blocked." : "Validation passed.");
});

const generateCaptionButton = el("generateCaption");
generateCaptionButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  const jobId = job.id;
  const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/captions`, { method: "POST" }));
  const variants = response.ok ? normalizeVariants(response.data) : [];
  if (variants.length > 0) {
    job.variants = variants;
  } else if (!job.variants.length) {
    job.variants = buildVariants(job.details || refs.captionDetails.value || "Property details pending");
  }
  workflowState.generatedCaption = true;
  renderVariants();
  renderMetrics();
  updateWorkflowGuide();
  log("Generated " + job.variants.length + " caption variants");
  setStatus(response.ok ? "Caption variants ready" : "Demo caption variants ready");
  toast("Caption variants generated.");
});

el("checkRulesBtn").addEventListener("click", () => {
  syncFormToJob();
  const issues = checkCaptionRules(refs.finalCaption.value.trim());
  refs.captionRuleResult.textContent = issues.length ? "Rule check: " + issues.join(" ") : "Rule check passed. No banned wording or emoji-like symbols found.";
  if (!issues.length && refs.finalCaption.value.trim()) {
    activeJob().status = "ready-to-post";
    refs.checkCaptionApproved.checked = true;
  }
  renderMetrics();
  renderJobList();
  updateWorkflowGuide();
  log("Ran caption rule check");
  toast(issues.length ? "Caption has rule issues." : "Caption rules passed.");
});

el("copyCaptionBtn").addEventListener("click", () => {
  if (!workflowState.generatedCaption) {
    toast("Generate the caption first");
    return;
  }
  copyText(refs.finalCaption.value.trim(), "Final caption copied.");
  workflowState.copiedCaption = true;
  refs.checkCaptionApproved.checked = true;
  updateWorkflowGuide();
});

el("copyChecklistBtn").addEventListener("click", () => {
  const job = activeJob();
  const packet = `PROPERTY: ${job.propertyName}\nASSIGNED BY: ${job.assignedBy}\nIMAGES SELECTED: ${job.images.filter((i) => i.selected).length}\nCAPTION:\n${job.finalCaption || "[pending caption]"}\n\nPOSTING REMINDER:\n1. Open Facebook page\n2. Upload selected images manually\n3. Paste caption\n4. Publish post\n5. Paste Facebook link back into console`;
  copyText(packet, "Posting packet copied.");
});

el("openFacebookBtn").addEventListener("click", () => {
  if (!workflowState.copiedCaption) {
    toast("Copy the caption before opening Facebook");
    return;
  }
  window.open("https://www.facebook.com/alphapremierRealty/", "_blank", "noopener,noreferrer");
  workflowState.openedFacebook = true;
  refs.checkPostedToFacebook.checked = true;
  updateWorkflowGuide();
  log("Opened Alpha Premier Realty Facebook page");
  toast("Facebook page opened in a new tab.");
});

refs.logButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  const selectedCount = job.images.filter((i) => i.selected).length;
  if (!refs.checkCaptionApproved.checked || selectedCount < 3 || !refs.checkPostedToFacebook.checked || !job.facebookLink.trim()) {
    toast("Complete the manual publish checklist first.");
    return;
  }
  const jobId = job.id;
  const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/mark-posted`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ facebook_url: job.facebookLink }),
  }));
  await authFetch("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: job.propertyName, facebook_url: job.facebookLink }),
  });
  job.status = "posted";
  job.trackerStatus = "ready";
  workflowState.loggedPost = true;
  renderAll();
  prepareTrackerPreview();
  log(response.ok ? "Facebook URL logged to tracker." : "Demo tracker sync completed.");
  toast("Job marked as posted.");
});

el("prepareTrackerBtn").addEventListener("click", () => {
  syncFormToJob();
  prepareTrackerPreview();
  toast("Tracker preview prepared.");
});

el("copyTrackerRowBtn").addEventListener("click", () => copyText(refs.trackerPreview.value, "Tracker row copied."));
el("copyDailyReportBtn").addEventListener("click", () => copyText(refs.dailyReportPreview.value, "Daily report entry copied."));

el("clearLogBtn").addEventListener("click", () => {
  refs.activityLog.innerHTML = "";
  toast("Activity log cleared.");
});

el("simulatePipelineBtn").addEventListener("click", () => {
  const job = activeJob();
  job.hasCaptionDoc = true;
  if (job.images.length < 3) {
    job.images.push({ id: "extra1", label: "Auto-added sample angle", selected: true });
  }
  job.imageCount = job.images.length;
  if (!job.variants.length) job.variants = buildVariants(job.details || refs.captionDetails.value || "Property details pending");
  if (!job.finalCaption) job.finalCaption = job.variants[0];
  workflowState.prepared = true;
  workflowState.generatedCaption = true;
  hydrateForm();
  renderAll();
  refs.captionRuleResult.textContent = "Pipeline simulation completed. Review the generated caption and selected images.";
  log("Simulated the automation pipeline");
  toast("Pipeline simulation complete.");
});

el("seedGoodDataBtn").addEventListener("click", () => {
  const job = activeJob();
  job.imageCount = 4;
  job.hasCaptionDoc = true;
  job.docName = "Clean-sample-caption.txt";
  if (job.images.length < 4) {
    job.images = [
      { id: "img1", label: "Main facade", selected: true },
      { id: "img2", label: "Interior shot", selected: true },
      { id: "img3", label: "Secondary angle", selected: true },
      { id: "img4", label: "Map context", selected: false },
    ];
  }
  job.details = "Property Type: Commercial Unit\nLocation: Pasig\nFloor Area: 95 sqm\nRental: PHP 68,000/month\nNotes: visible frontage, move-in ready, near major roads";
  hydrateForm();
  renderAll();
  log("Loaded clean sample data");
  toast("Clean sample data loaded.");
});

el("seedBadDataBtn").addEventListener("click", () => {
  const job = activeJob();
  job.imageCount = 2;
  job.hasCaptionDoc = false;
  job.docName = "";
  job.images = [
    { id: "img1", label: "Only photo 1", selected: true },
    { id: "img2", label: "Only photo 2", selected: true },
  ];
  job.details = "";
  job.finalCaption = "Negotiables available 😊";
  hydrateForm();
  renderAll();
  log("Loaded broken sample data");
  toast("Broken sample data loaded.");
});

el("newJobBtn").addEventListener("click", () => {
  const nextId = "APG-0629-00" + (jobs.length + 1);
  const job = {
    id: nextId,
    propertyName: "New Assigned Property",
    assignedBy: "Ma'am Jean",
    operator: "Unassigned",
    dueDate: new Date().toISOString().slice(0, 10),
    driveUrl: "",
    imageCount: 0,
    hasCaptionDoc: false,
    docName: "",
    status: "missing-assets",
    trackerStatus: "pending",
    details: "",
    images: [],
    variants: [],
    finalCaption: "",
    facebookLink: "",
    activity: [],
  };
  jobs.unshift(job);
  activeJobId = job.id;
  resetWorkflowState();
  hydrateForm();
  renderAll();
  log("Created a new intake job");
  toast("New job created.");
});

el("processNext").addEventListener("click", async () => {
  const response = await requestJson("/api/queue/next", { method: "POST" });
  if (response.ok && response.data.property_name) {
    refs.propertyName.value = response.data.property_name;
    await prepareSelectedJob("queue");
    return;
  }
  setStatus("Demo fallback loaded next property");
  activeJobId = jobs[0].id;
  resetWorkflowState();
  renderAll();
});

refs.zipDownload.addEventListener("click", (event) => {
  if (refs.zipDownload.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
    return;
  }
  workflowState.downloadedAssets = true;
  updateWorkflowGuide();
  log("Downloaded image package");
});

[refs.checkCaptionApproved, refs.checkPhotosSelected, refs.checkPostedToFacebook].forEach((checkbox) => {
  checkbox.addEventListener("change", updateWorkflowGuide);
});

doc.documentElement.setAttribute("data-theme", localStorage.getItem("apg-theme") || "light");
renderAll();
log("Console initialized");
prepareTrackerPreview();
