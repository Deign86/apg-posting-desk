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

const APG_LISTINGS_URL = "https://drive.google.com/drive/folders/1GXeGULYswb7jXcMGCCRm2RQ_h0EKsDll";

let currentUser = null;
let session = {
  firebase_project_id: firebaseConfig.projectId || "",
  user: null,
};

let jobs = [];
let activeJobId = null;

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
  return jobs.find((j) => j.id === activeJobId) || jobs[0] || null;
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

function setLoading(isLoading) {
  const spinner = document.getElementById("loadingSpinner");
  if (spinner) spinner.classList.toggle("hidden", !isLoading);
  refs.connectionStatus.setAttribute("aria-busy", String(isLoading));
}

function showError(message) {
  const banner = document.getElementById("errorBanner");
  if (!banner) return;
  const text = banner.querySelector(".error-banner-text");
  if (text) text.textContent = message;
  banner.classList.add("show");
}

function hideError() {
  const banner = document.getElementById("errorBanner");
  if (banner) banner.classList.remove("show");
}

function renderEmptyState() {
  refs.jobList.innerHTML = '<div class="empty-state"><div class="empty-state-icon">!</div><div class="empty-state-title">No jobs assigned</div><div class="empty-state-hint">Click "New intake" or "Process next" to begin.</div></div>';
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
    assignedBy: raw.assigned_by || raw.assignedBy || "",
    operator: raw.operator || "Unassigned",
    dueDate: raw.due_date || raw.dueDate || new Date().toISOString().slice(0, 10),
    driveUrl: raw.drive_url || raw.driveUrl || APG_LISTINGS_URL,
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
  if (jobs.length === 0) {
    renderEmptyState();
    refs.assignedCount.textContent = "0";
    refs.approvalCount.textContent = "0";
    refs.readyCount.textContent = "0";
    refs.postedCount.textContent = "0";
    return;
  }
  jobs.forEach((job) => {
    const [label, cls] = statusBadge(job.status);
    const btn = doc.createElement("button");
    btn.className = "job-row" + (job.id === activeJobId ? " active" : "");
    btn.type = "button";
    btn.setAttribute("aria-current", job.id === activeJobId ? "page" : "false");
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
  if (!job) return;
  refs.propertyName.value = job.propertyName || "";
  refs.assignedBy.value = job.assignedBy;
  refs.operatorName.value = job.operator;
  refs.dueDate.value = job.dueDate;
  refs.driveUrl.value = APG_LISTINGS_URL;
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
  if (!job) return;
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
  if (!job) return;
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
  if (!job) return;
  refs.thumbs.innerHTML = "";
  job.images.forEach((img, index) => {
    const card = doc.createElement("div");
    card.className = "thumb" + (img.selected ? " active" : "");
    card.innerHTML = `
      <button type="button" data-id="${img.id}">
        <img src="${img.url}" alt="${img.label}" class="thumb-img" loading="lazy" />
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
  if (!job) return;
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
  if (!job) return;
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
  if (!job) return;
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
  const name = session.user?.display_name || session.user?.email || "Not signed in";
  refs.roleBadge.textContent = role;
  refs.userLabel.textContent = session.user ? `${name} · ${roleCopy(role)} · ${session.firebase_project_id || ""}` : "Not signed in.";
  refs.sessionTitle.textContent = "Role access";
}

function roleCopy(role) {
  if (role === "admin") return "admin controls";
  if (role === "maam_jean") return "Ma'am Jean approvals";
  return "user posting lane";
}

function updateWorkflowGuide() {
  const job = activeJob();
  if (!job) return;
  const canDownload = workflowState.prepared && job.images.length > 0;
  const canCopyCaption = workflowState.downloadedAssets && workflowState.generatedCaption;
  const canOpenFacebook = workflowState.copiedCaption;
  const canEnterFacebookUrl = workflowState.copiedCaption && workflowState.openedFacebook && refs.checkPostedToFacebook.checked;
  const canLogPost = canEnterFacebookUrl && workflowState.enteredFacebookUrl && refs.checkCaptionApproved.checked && refs.checkPhotosSelected.checked;
  refs.facebookUrlGroup.hidden = !canEnterFacebookUrl;
  if (workflowState.loggedPost) {
    refs.logButton.textContent = "Post logged";
    refs.logButton.disabled = true;
    refs.logButton.setAttribute("aria-disabled", "true");
  } else {
    refs.logButton.textContent = "Log post";
    refs.logButton.disabled = !canLogPost;
    refs.logButton.setAttribute("aria-disabled", String(!canLogPost));
  }
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
  step.setAttribute("aria-current", step.dataset.state === "active" ? "step" : "false");
  const marker = step.querySelector(".step-marker");
  marker.textContent = complete ? "Done" : marker.dataset.number;
}

function resetWorkflowState() {
  const job = activeJob();
  if (job && (job.status === "posted" || job.status === "posted_today" || job.status === "posted-today")) {
    workflowState.prepared = true;
    workflowState.downloadedAssets = true;
    workflowState.generatedCaption = true;
    workflowState.copiedCaption = true;
    workflowState.openedFacebook = true;
    workflowState.enteredFacebookUrl = true;
    workflowState.loggedPost = true;
    refs.facebookUrlGroup.hidden = false;
    refs.checkCaptionApproved.checked = true;
    refs.checkPhotosSelected.checked = true;
    refs.checkPostedToFacebook.checked = true;
    return;
  }
  workflowState.prepared = true;
  workflowState.downloadedAssets = false;
  workflowState.generatedCaption = Boolean(job && (job.finalCaption || job.variants.length));
  workflowState.copiedCaption = false;
  workflowState.openedFacebook = false;
  workflowState.enteredFacebookUrl = false;
  workflowState.loggedPost = false;
  refs.facebookLink.value = "";
  refs.checkCaptionApproved.checked = false;
  refs.checkPostedToFacebook.checked = false;
  refs.logButton.textContent = "Log post";
}

async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (currentUser) {
    const token = await currentUser.getIdToken();
    headers.set("Authorization", `Bearer ${token}`);
  }
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
      showError(error.message);
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
    jobs = response.data.jobs.map((job) => normalizeJob(job));
  }
  if (!jobs.some((job) => job.id === activeJobId)) {
    activeJobId = jobs.length > 0 ? jobs[0].id : null;
  }
  renderAll();
  setStatus(response.ok ? "Live queue loaded" : "Queue not available");
}

async function loadActivity(jobId) {
  try {
    const response = await jsonFromResponse(await authFetch(`/api/jobs/${jobId}/activity`));
    if (response.ok && Array.isArray(response.data.activity)) {
      const job = activeJob();
      if (!job) return;
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
  if (!job) return;
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
  setStatus(prepared.ok || legacy.ok ? "Pipeline ready" : "Pipeline preparation failed");
}

function formPayload() {
  return {
    property_name: refs.propertyName.value.trim(),
    assigned_by: refs.assignedBy.value.trim() || "",
    operator: refs.operatorName.value.trim() || "Unassigned",
    due_date: refs.dueDate.value,
    drive_url: APG_LISTINGS_URL,
  };
}

function setStatus(message) {
  refs.connectionStatus.textContent = message;
  setLoading(message.includes("Running") || message.includes("Loading") || message.includes("Searching"));
}

if (auth) {
  onAuthStateChanged(auth, async (user) => {
    currentUser = user;
    refs.signInButton.hidden = Boolean(user);
    refs.signOutButton.hidden = !user;
    await loadSession();
    await loadJobs();
  });
} else {
  refs.userLabel.textContent = "Firebase config not loaded. Sign in is unavailable.";
}

refs.signInButton.addEventListener("click", async () => {
  if (!auth) {
    setStatus("Firebase config not loaded; sign in unavailable");
    return;
  }
  await signInWithPopup(auth, provider);
});

refs.signOutButton.addEventListener("click", async () => {
  if (auth) {
    await signOut(auth);
  }
});

el("themeToggle").addEventListener("click", () => {
  const root = doc.documentElement;
  const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", nextTheme);
  localStorage.setItem("apg-theme", nextTheme);
});

const errorBannerDismiss = document.getElementById("errorBannerDismiss");
if (errorBannerDismiss) {
  errorBannerDismiss.addEventListener("click", hideError);
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

el("validateAssetsBtn").addEventListener("click", async () => {
  hideError();
  setLoading(true);
  setStatus("Running pipeline");
  syncFormToJob();
  const job = activeJob();
  if (!job) {
    setLoading(false);
    return;
  }
  const isLocalOnly = /^APG-\d{4}-\d+$/i.test(job.id) || (job.status === "missing-assets" && job.images.length === 0);
  if (isLocalOnly) {
    await createOrPrepareJob();
  } else if (job.images.length > 0 || job.status !== "missing-assets") {
    const response = await requestJson(`/api/jobs/${job.id}/validate`, { method: "POST" });
    if (response.ok) {
      Object.assign(job, normalizeJob(response.data));
    }
    renderAll();
    log("Ran API validation for " + job.propertyName);
    toast(response.ok ? "Validation passed." : "Validation failed.");
  } else {
    job.hasCaptionDoc = refs.captionDetails.value.trim().length > 0;
    job.imageCount = job.images.length;
    renderAll();
    log("Ran local validation for " + job.propertyName);
    toast(job.status === "missing-assets" ? "Validation blocked." : "Validation passed.");
  }
  setLoading(false);
});

const generateCaptionButton = el("generateCaption");
generateCaptionButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  if (!job) return;
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
  setStatus(response.ok ? "Caption variants ready" : "Caption generation failed");
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
  if (!job) return;
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

async function executeLogPost() {
  syncFormToJob();
  const job = activeJob();
  if (!job) return;
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
  log(response.ok ? "Facebook URL logged to tracker." : "Tracker sync completed.");
  toast("Job marked as posted.");
}

refs.logButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  if (!job) return;
  const selectedCount = job.images.filter((i) => i.selected).length;
  if (!refs.checkCaptionApproved.checked || selectedCount < 3 || !refs.checkPostedToFacebook.checked || !job.facebookLink.trim()) {
    toast("Complete the manual publish checklist first.");
    return;
  }
  const dialog = document.getElementById("confirmDialog");
  if (dialog) {
    const msg = dialog.querySelector("#confirmDialogText");
    if (msg) msg.textContent = `Log this post to the tracker? Property: ${job.propertyName}, Facebook URL: ${refs.facebookLink.value}. This action cannot be undone.`;
    dialog.showModal();
    return;
  }
  await executeLogPost();
});

const confirmBtn = document.getElementById("confirmLogBtn");
if (confirmBtn) {
  confirmBtn.addEventListener("click", () => {
    const dialog = document.getElementById("confirmDialog");
    if (dialog) dialog.close();
    executeLogPost();
  });
}
const cancelBtn = document.getElementById("cancelLogBtn");
if (cancelBtn) {
  cancelBtn.addEventListener("click", () => {
    const dialog = document.getElementById("confirmDialog");
    if (dialog) dialog.close();
    toast("Log cancelled.");
  });
}

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

el("newJobBtn").addEventListener("click", () => {
  const now = new Date();
  const datePart = String(now.getMonth() + 1).padStart(2, "0") + String(now.getDate()).padStart(2, "0");
  const nextId = `APG-${datePart}-00${jobs.length + 1}`;
  const job = {
    id: nextId,
    propertyName: "",
    assignedBy: "",
    operator: "",
    dueDate: new Date().toISOString().slice(0, 10),
    driveUrl: APG_LISTINGS_URL,
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
  setStatus(response.data?.detail === "Queue is not configured"
    ? "Demo mode: queue unavailable. Use New intake to prepare a property manually."
    : "No queued properties available");
  if (jobs.length > 0) {
    activeJobId = jobs[0].id;
  }
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

doc.documentElement.setAttribute("data-theme", localStorage.getItem("apg-theme") || "dark");
renderAll();
log("Console initialized");
prepareTrackerPreview();
