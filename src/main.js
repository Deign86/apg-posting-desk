import "./styles.css";

const doc = document;
const el = (id) => doc.getElementById(id);

import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || "";
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || "";
const supabase = supabaseUrl ? createClient(supabaseUrl, supabaseAnonKey) : null;
let currentUser = null;

const session = {
  supabase_url: supabaseUrl || "demo",
  user: {
    uid: "demo-operator",
    email: "demo@apg.local",
    role: "user",
    display_name: "Demo operator",
  },
};

let jobs = [];
let activeJobId = null;
let isLoggedIn = false;

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
  signOutButton: el("signOutButton"),
  sessionTitle: el("sessionTitle"),
  facebookUrlGroup: el("facebookUrlGroup"),
  logButton: el("logPostButton"),
  loginEmail: el("loginEmail"),
  loginPassword: el("loginPassword"),
  loginError: el("loginError"),
  loginSubmit: el("loginSubmit"),
  loginLoader: el("loginLoader"),
};


let selectedRole = "user";
const workflowState = {
  prepared: true,
  downloadedAssets: false,
  generatedCaption: true,
  copiedCaption: false,
  openedFacebook: false,
  enteredFacebookUrl: false,
  loggedPost: false,
};

const STEP_ORDER = ["details", "photos", "caption", "publish", "log"];
const STEP_PREREQ = {
  photos: () => workflowState.prepared && activeJob()?.images.length > 0,
  caption: () => workflowState.prepared && workflowState.generatedCaption,
  publish: () =>
    workflowState.prepared &&
    workflowState.downloadedAssets &&
    workflowState.generatedCaption,
  log: () =>
    workflowState.prepared &&
    workflowState.downloadedAssets &&
    workflowState.generatedCaption &&
    workflowState.copiedCaption &&
    workflowState.openedFacebook,
};

function setActiveStep(step) {
  const panels = doc.querySelectorAll(".step-panel");
  const tabs = doc.querySelectorAll(".workflow-tab");
  panels.forEach((panel) => {
    panel.hidden = panel.id !== `panel-${step}`;
  });
  tabs.forEach((tab) => {
    const isActive = tab.dataset.step === step;
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
    if (isActive) {
      tab.disabled = false;
    } else if (STEP_PREREQ[tab.dataset.step]) {
      tab.disabled = !STEP_PREREQ[tab.dataset.step]();
    }
  });
}

function updateWorkflowTabs() {
  const activePanel = doc.querySelector(".step-panel:not([hidden])");
  const currentStep = activePanel?.id?.replace("panel-", "") || "details";
  setActiveStep(currentStep);
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/service-worker.js");
}

function activeJob() {
  const found = jobs.find((j) => j.id === activeJobId);
  return found || jobs[0] || null;
}

function log(message) {
  const item = doc.createElement("div");
  item.className = "log-item";
  item.textContent =
    new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) +
    " — " +
    message;
  refs.activityLog.prepend(item);
}

function toast(message) {
  refs.toast.textContent = message;
  refs.toast.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(
    () => refs.toast.classList.remove("show"),
    2200
  );
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
    "missing-assets": ["Photos or caption missing", "err"],
    "ready-for-review": ["Ready for review", "warn"],
    "ready-to-post": ["Ready to post", "ready"],
    posted: ["Posted", "ready"],
    posted_today: ["Posted today", "ready"],
    waiting_approval: ["Waiting approval", "warn"],
  };
  return (
    map[status] || [status.replaceAll("-", " ").replaceAll("_", " "), ""]
  );
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
    hasCaptionDoc: Boolean(
      raw.caption_document_name || raw.hasCaptionDoc || raw.caption_details || raw.details
    ),
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
    refs.jobList.innerHTML = `<div class="muted" style="padding:.5rem;">No properties yet. Create a new property or process the next one from the queue.</div>`;
  } else {
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
  }
  refs.assignedCount.textContent = jobs.length;
  refs.approvalCount.textContent = jobs.filter(
    (j) => j.status === "ready-for-review" || j.status === "waiting-approval"
  ).length;
  refs.readyCount.textContent = jobs.filter((j) => j.status === "ready-to-post").length;
  refs.postedCount.textContent = jobs.filter(
    (j) => j.status === "posted" || j.status === "posted_today"
  ).length;
}

function hydrateForm() {
  const job = activeJob();
  if (!job) {
    refs.propertyName.value = "";
    refs.assignedBy.value = "";
    refs.operatorName.value = "";
    refs.dueDate.value = "";
    refs.driveUrl.value = "";
    refs.captionDetails.value = "";
    refs.finalCaption.value = "";
    refs.facebookLink.value = "";
    refs.checkCaptionApproved.checked = false;
    refs.checkPhotosSelected.checked = false;
    refs.checkPostedToFacebook.checked = false;
    refs.sourceDocName.textContent = "No document loaded";
    refs.captionSourceOutput.textContent =
      "Select a property to review the extracted details here.";
    refs.zipDownload.href = "#";
    refs.zipDownload.setAttribute("aria-disabled", "true");
    workflowState.generatedCaption = false;
    return;
  }
  refs.propertyName.value = job.propertyName;
  refs.assignedBy.value = job.assignedBy;
  refs.operatorName.value = job.operator;
  refs.dueDate.value = job.dueDate;
  refs.driveUrl.value = job.driveUrl;
  refs.captionDetails.value = job.details;
  refs.finalCaption.value = job.finalCaption || "";
  refs.facebookLink.value = job.facebookLink || "";
  refs.checkCaptionApproved.checked = !!job.finalCaption;
  refs.checkPhotosSelected.checked =
    job.images.filter((i) => i.selected).length >= 3;
  refs.checkPostedToFacebook.checked = !!job.facebookLink;
  refs.sourceDocName.textContent = `Source caption document: ${job.docName || "No document loaded"}`;
  refs.captionSourceOutput.textContent =
    job.details ||
    "Fetch a property to review the extracted DOCX details here.";
  refs.zipDownload.href = `/prepared/${encodeURIComponent(job.propertyName)}.zip`;
  if (job.images.length > 0) {
    refs.zipDownload.removeAttribute("aria-disabled");
  }
  workflowState.generatedCaption = Boolean(
    job.finalCaption || job.variants.length
  );
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
  if (!job) {
    refs.validationSteps.innerHTML = "";
    refs.folderStatusBadge.className = "badge err";
    refs.folderStatusBadge.textContent = "Property check pending";
    return;
  }
  const checks = [
    { label: "Property folder link added", ok: !!job.driveUrl },
    { label: "At least 3 photos found", ok: job.imageCount >= 3 },
    { label: "Caption file found", ok: !!job.hasCaptionDoc },
    { label: "Operator and due date set", ok: !!job.operator && !!job.dueDate },
  ];
  refs.validationSteps.innerHTML = "";
  checks.forEach((check, idx) => {
    const div = doc.createElement("div");
    div.className =
      "step " + (check.ok ? "done" : idx === 0 ? "current" : "");
    div.innerHTML = `<strong>${check.label}</strong><div class="muted">${check.ok ? "Passed" : "Needs attention"}</div>`;
    refs.validationSteps.appendChild(div);
  });
  const allGood = checks.every((c) => c.ok);
  refs.folderStatusBadge.className = "badge " + (allGood ? "ready" : "err");
  refs.folderStatusBadge.textContent = allGood
    ? "Property files ready"
    : "Property files incomplete";
}

function renderThumbs() {
  const job = activeJob();
  if (!job) {
    refs.thumbs.innerHTML = "";
    refs.imageCounterBadge.textContent = "0 selected";
    refs.assetSummary.textContent = "No asset package loaded yet.";
    return;
  }
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
      log(img.selected ? "Selected " : "Deselected " + img.label);
    });
    refs.thumbs.appendChild(card);
  });
  const selected = job.images.filter((i) => i.selected).length;
  refs.imageCounterBadge.textContent = `${selected} selected`;
  refs.assetSummary.textContent = `${job.imageCount} photos found. ${selected} selected for the post. Caption file: ${job.hasCaptionDoc ? job.docName : "missing"}.`;
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
  if (/[^\w\s.,:/()\-₱#]/u.test(text))
    issues.push("Possible emoji or unsupported symbol detected.");
  if (lowered.includes("negotiables"))
    issues.push("Contains banned term: negotiables.");
  if (lowered.includes("negotioables"))
    issues.push("Contains banned term: negotioables.");
  if (lowered.includes("least term"))
    issues.push("Contains banned term: least term.");
  return issues;
}

function renderVariants() {
  const job = activeJob();
  refs.captionVariants.innerHTML = "";
  job.variants.forEach((text, idx) => {
    const card = doc.createElement("div");
    card.className =
      "variant" + (job.finalCaption === text ? " active" : "");
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
    card.querySelector("[data-copy]").addEventListener("click", () =>
      copyText(text, "Caption copied.")
    );
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
  refs.metricTracker.textContent = "Post log " + job.trackerStatus;
  refs.publishHelper.textContent = job.facebookLink
    ? "Facebook URL captured. Ready to prepare tracker updates."
    : "Waiting for approval and manual publish.";
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
    selectedImages + " selected photos",
    job.facebookLink || "[pending facebook link]",
    job.status,
    job.trackerStatus,
  ].join(" | ");

  refs.dailyReportPreview.value = `Posted property: ${job.propertyName}
Assigned by: ${job.assignedBy}
Operator: ${job.operator}
Photo package: ${selectedImages} selected photos; caption file ${job.hasCaptionDoc ? "present" : "missing"}
Facebook URL: ${job.facebookLink || "[pending]"}
Status: ${job.status}`;
  refs.trackerStatus.textContent =
    "Preview ready. You can copy and paste the summary or save it later.";
  log("Prepared tracker and daily report preview");
}

function renderActivity(activity) {
  refs.activityLog.innerHTML = "";
  (activity || []).forEach((item) => {
    const row = doc.createElement("div");
    row.className = "log-item";
    row.textContent = `${
      item.at || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    } — ${item.text}`;
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
  updateWorkflowTabs();
}

function renderSession() {
  const role = session.user?.role || "user";
  const name = session.user?.display_name || session.user?.email || "Demo operator";
  refs.roleBadge.textContent = role;
  refs.userLabel.textContent = `${name} · ${roleCopy(role)} · ${session.supabase_url || "demo"}`;
  refs.sessionTitle.textContent = "Role access";
  applyRoleGating();
}

function roleCopy(role) {
  if (role === "admin") return "admin access";
  return "user access";
}

function updateWorkflowGuide() {
  const job = activeJob();
  const canDownload = workflowState.prepared && job.images.length > 0;
  const canCopyCaption =
    workflowState.downloadedAssets && workflowState.generatedCaption;
  const canOpenFacebook = workflowState.copiedCaption;
  const canEnterFacebookUrl =
    workflowState.copiedCaption &&
    workflowState.openedFacebook &&
    refs.checkPostedToFacebook.checked;
  const canLogPost =
    canEnterFacebookUrl &&
    workflowState.enteredFacebookUrl &&
    refs.checkCaptionApproved.checked &&
    refs.checkPhotosSelected.checked;
  refs.facebookUrlGroup.hidden = !canEnterFacebookUrl;
  refs.logButton.disabled = !canLogPost;
  setWorkflowStep("download", workflowState.downloadedAssets, canDownload);
  setWorkflowStep("copy", workflowState.copiedCaption, canCopyCaption);
  setWorkflowStep("facebook", workflowState.openedFacebook, canOpenFacebook);
  setWorkflowStep("url", workflowState.enteredFacebookUrl, canEnterFacebookUrl);
  setWorkflowStep("log", workflowState.loggedPost, canLogPost);
}

function setWorkflowStep(name, complete, enabled) {
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
  workflowState.generatedCaption = Boolean(
    job.finalCaption || job.variants.length
  );
  workflowState.copiedCaption = false;
  workflowState.openedFacebook = false;
  workflowState.enteredFacebookUrl = false;
  workflowState.loggedPost = false;
  refs.facebookLink.value = "";
  refs.checkCaptionApproved.checked = false;
  refs.checkPostedToFacebook.checked = false;
  updateWorkflowTabs();
}

async function authFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  if (currentUser) {
    const token = await currentUser.access_token;
    headers.set("Authorization", `Bearer ${token}`);
  }
  headers.set("X-Demo-Role", selectedRole);
  return fetch(url, { ...options, headers });
}

async function jsonFromResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : { detail: await response.text() };
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

async function handleLoginSubmit() {
  const email = refs.loginEmail.value.trim();
  const password = refs.loginPassword.value;
  if (!email || !password) {
    refs.loginError.textContent = "Enter both email and password.";
    refs.loginError.hidden = false;
    return;
  }
  refs.loginLoader.hidden = false;
  refs.loginError.hidden = true;
  try {
    const response = await jsonFromResponse(
      await authFetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      })
    );
    if (!response.ok) {
      refs.loginError.textContent = response.data?.detail || "Login failed.";
      refs.loginError.hidden = false;
      return;
    }
    session.user = {
      uid: response.data.email,
      email: response.data.email,
      role: response.data.role || "user",
      display_name: response.data.email,
    };
    isLoggedIn = true;
    renderSession();
    syncLoginView();
    log("Signed in as " + session.user.email);
  } catch (error) {
    refs.loginError.textContent = error.message || "Unable to reach the server.";
    refs.loginError.hidden = false;
  } finally {
    refs.loginLoader.hidden = true;
  }
}

async function handleSignOut() {
  try {
    await authFetch("/api/logout", { method: "POST" });
  } catch {
    // best-effort logout
  }
  session.user = {
    uid: "demo-operator",
    email: "demo@apg.local",
    role: "user",
    display_name: "Demo operator",
  };
  isLoggedIn = false;
  renderSession();
  syncLoginView();
  log("Signed out");
}

async function refreshSession() {
  const response = await jsonFromResponse(await authFetch("/api/session"));
  if (response.ok && response.data.user) {
    session.user = response.data.user;
    session.supabase_url = response.data.supabase_url;
  }
  renderSession();
  syncLoginView();
}

function syncLoginView() {
  const loggedIn = isLoggedIn;
  const loginScreen = doc.getElementById("loginScreen");
  const appContent = doc.getElementById("appContent");
  if (loginScreen) loginScreen.hidden = loggedIn;
  if (appContent) appContent.hidden = !loggedIn;
  refs.signOutButton.hidden = !loggedIn;
  refs.sessionTitle.textContent = loggedIn ? "Signed in" : "Sign in required";
  if (loggedIn) {
    refs.loginEmail.value = "";
    refs.loginPassword.value = "";
    loginError = "";
    renderLoginError();
  }
}

async function loadSession() {
  await refreshSession();
}

async function loadJobs() {
  const response = await jsonFromResponse(await authFetch("/api/jobs"));
  if (response.ok && Array.isArray(response.data.jobs)) {
    jobs = response.data.jobs.map((job) => normalizeJob(job));
  }
  if (jobs.length > 0 && !jobs.some((job) => job.id === activeJobId)) {
    activeJobId = jobs[0].id;
  }
  if (!jobs.length) activeJobId = null;
  renderAll();
  setStatus(response.ok ? "Property list ready" : "Property list unavailable");
}

async function loadActivity(jobId) {
  try {
    const response = await jsonFromResponse(
      await authFetch(`/api/jobs/${jobId}/activity`)
    );
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
  setStatus("Checking property files");
  const jobId = job.id;
  await jsonFromResponse(
    await authFetch(`/api/jobs/${jobId}/validate`, { method: "POST" })
  );
  const prepared = await jsonFromResponse(
    await authFetch(`/api/jobs/${jobId}/prepare`, { method: "POST" })
  );
  const legacy = await authFetch("/api/prepare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      property_name: refs.propertyName.value.trim() || job.propertyName,
    }),
  });
  if (prepared.ok) {
    Object.assign(job, normalizeJob(prepared.data));
  } else if (legacy.ok) {
    Object.assign(job, normalizeJob(await legacy.json()));
  }
  job.status = source === "form" ? "waiting_approval" : "ready-to-post";
  activeJobId = job.id;
  workflowState.prepared = true;
  workflowState.generatedCaption = Boolean(
    job.finalCaption || job.variants.length
  );
  hydrateForm();
  renderAll();
  setStatus(
    prepared.ok || legacy.ok
      ? "Property files ready"
      : "Demo property files ready"
  );
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

async function ensureFirebase() {
  setStatus("Demo mode is active");
  refs.userLabel.textContent =
    "Demo mode is active. You can explore the workspace with sample data right away.";
  return false;
}

async function signInWithEmail() {
  loginError = "";
  renderLoginError();
  refs.loginLoader.hidden = false;
  refs.loginSubmit.disabled = true;
  try {
    if (supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: refs.loginEmail.value.trim(),
        password: refs.loginPassword.value,
      });
      if (error) throw error;
      session.user = {
        uid: data.user.id,
        email: data.user.email,
        role: "user",
        display_name: data.user.email,
      };
    } else {
      const response = await jsonFromResponse(
        await authFetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: refs.loginEmail.value.trim(),
            password: refs.loginPassword.value,
          }),
        })
      );
      if (!response.ok) {
        loginError = response.data?.detail || "Sign-in failed. Please try again.";
        renderLoginError();
        setStatus("Sign-in failed");
        return;
      }
      session.user = {
        uid: response.data.email,
        email: response.data.email,
        role: response.data.role || "user",
        display_name: response.data.email,
      };
    }
    isLoggedIn = true;
    syncLoginView();
    await refreshSession();
    await loadJobs();
    setStatus("Signed in");
  } catch (error) {
    loginError = error?.message || "Sign-in failed. Please try again.";
    renderLoginError();
    setStatus("Sign-in failed");
  } finally {
    refs.loginLoader.hidden = true;
    refs.loginSubmit.disabled = false;
  }
}

async function signOut() {
  currentUser = null;
  isLoggedIn = false;
  if (supabase) {
    await supabase.auth.signOut();
  }
  try {
    await authFetch("/api/logout", { method: "POST" });
  } catch {
    // best-effort logout
  }
  session.user = {
    uid: "demo-operator",
    email: "demo@apg.local",
    role: "user",
    display_name: "Demo operator",
  };
  syncLoginView();
  await refreshSession();
  await loadJobs();
  setStatus("Signed out");
}

function renderLoginError() {
  refs.loginError.textContent = loginError;
  refs.loginError.hidden = !loginError;
}

await ensureFirebase();
syncLoginView();
await refreshSession();
await loadJobs();

refs.signOutButton.addEventListener("click", signOut);
refs.loginSubmit.addEventListener("click", signInWithEmail);

function toggleTheme() {
  const root = doc.documentElement;
  const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", nextTheme);
  localStorage.setItem("apg-theme", nextTheme);
}

el("themeToggle").addEventListener("click", toggleTheme);
el("loginThemeToggle").addEventListener("click", toggleTheme);

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
    demoSignIn();
  });
});

async function demoSignIn() {
  isLoggedIn = true;
  session.user = {
    uid: "demo-" + selectedRole,
    email: "demo-" + selectedRole + "@apg.local",
    role: selectedRole,
    display_name: "Demo " + selectedRole,
  };
  syncLoginView();
  await refreshSession();
  await loadJobs();
  setStatus("Signed in as " + selectedRole);
}

function applyRoleGating() {
  const isAdmin = selectedRole === "admin";
  doc.querySelectorAll("[data-admin-only]").forEach((node) => {
    node.hidden = !isAdmin;
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
  log("Property check for " + job.propertyName);
  toast(job.status === "missing-assets" ? "Property check blocked." : "Property check passed.");
});

const generateCaptionButton = el("generateCaption");
generateCaptionButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  const jobId = job.id;
  const response = await jsonFromResponse(
    await authFetch(`/api/jobs/${jobId}/captions`, { method: "POST" })
  );
  const variants = response.ok ? normalizeVariants(response.data) : [];
  if (variants.length > 0) {
    job.variants = variants;
  } else if (!job.variants.length) {
    job.variants = buildVariants(
      job.details || refs.captionDetails.value || "Property details pending"
    );
  }
  workflowState.generatedCaption = true;
  renderVariants();
  renderMetrics();
  updateWorkflowGuide();
  log("Generated " + job.variants.length + " caption options");
  setStatus(response.ok ? "Caption options ready" : "Demo caption options ready");
  toast("Caption options generated.");
});

el("checkRulesBtn").addEventListener("click", () => {
  syncFormToJob();
  const issues = checkCaptionRules(refs.finalCaption.value.trim());
  refs.captionRuleResult.textContent = issues.length
    ? "Caption check: " + issues.join(" ")
    : "Caption check passed. No restricted words or symbols found.";
  if (!issues.length && refs.finalCaption.value.trim()) {
    activeJob().status = "ready-to-post";
    refs.checkCaptionApproved.checked = true;
  }
  renderMetrics();
  renderJobList();
  updateWorkflowGuide();
  log("Ran caption check");
  toast(issues.length ? "Caption has issues." : "Caption check passed.");
});

el("copyCaptionBtn").addEventListener("click", async () => {
  if (!workflowState.generatedCaption) {
    toast("Generate the caption first");
    return;
  }
  await copyText(refs.finalCaption.value.trim(), "Caption copied.");
  workflowState.copiedCaption = true;
  refs.checkCaptionApproved.checked = true;
  updateWorkflowGuide();
});

el("copyChecklistBtn").addEventListener("click", () => {
  const job = activeJob();
  const packet = `Property: ${job.propertyName}
Assigned by: ${job.assignedBy}
Photos: ${job.images.filter((i) => i.selected).length}
Caption:
${job.finalCaption || "[pending caption]"}

Reminder:
1. Post to Facebook manually
2. Paste the live Facebook URL back here`;
  copyText(packet, "Posting checklist copied.");
});

el("openFacebookBtn").addEventListener("click", () => {
  if (!workflowState.copiedCaption) {
    toast("Copy the caption before opening Facebook");
    return;
  }
  window.open(
    "https://www.facebook.com/alphapremierRealty/",
    "_blank",
    "noopener,noreferrer"
  );
  workflowState.openedFacebook = true;
  refs.checkPostedToFacebook.checked = true;
  updateWorkflowGuide();
  log("Opened Facebook page");
  toast("Facebook page opened in a new tab.");
});

refs.logButton.addEventListener("click", async () => {
  syncFormToJob();
  const job = activeJob();
  const selectedCount = job.images.filter((i) => i.selected).length;
  if (
    !refs.checkCaptionApproved.checked ||
    selectedCount < 3 ||
    !refs.checkPostedToFacebook.checked ||
    !job.facebookLink.trim()
  ) {
    toast("Complete the posting checklist first.");
    return;
  }
  const jobId = job.id;
  const response = await jsonFromResponse(
    await authFetch(`/api/jobs/${jobId}/mark-posted`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ facebook_url: job.facebookLink }),
    })
  );
  await authFetch("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ property_name: job.propertyName, facebook_url: job.facebookLink }),
  });
  job.status = "posted";
  job.trackerStatus = "logged";
  workflowState.loggedPost = true;
  renderAll();
  prepareTrackerPreview();
  log(response.ok ? "Facebook post saved to log." : "Demo post log completed.");
  toast("Property marked as posted.");
});

el("prepareTrackerBtn").addEventListener("click", () => {
  syncFormToJob();
  prepareTrackerPreview();
  toast("Post log preview prepared.");
});

el("copyTrackerRowBtn").addEventListener("click", () =>
  copyText(refs.trackerPreview.value, "Posted summary copied.")
);
el("copyDailyReportBtn").addEventListener("click", () =>
  copyText(refs.dailyReportPreview.value, "End-of-day note copied.")
);

el("clearLogBtn").addEventListener("click", () => {
  refs.activityLog.innerHTML = "";
  toast("Recent actions cleared.");
});

el("simulatePipelineBtn").addEventListener("click", async () => {
  const job = activeJob();
  setStatus("Running pipeline");
  const jobId = job.id;
  const prepared = await jsonFromResponse(
    await authFetch(`/api/jobs/${jobId}/prepare`, { method: "POST" })
  );
  if (prepared.ok) {
    Object.assign(job, normalizeJob(prepared.data));
    if (!job.variants.length) {
      job.variants = buildVariants(
        job.details || refs.captionDetails.value || "Property details pending"
      );
    }
    if (!job.finalCaption && job.variants.length) {
      job.finalCaption = job.variants[0];
    }
  } else {
    toast(prepared.data?.detail || "Property check failed. Please review the details and try again.");
  }
  workflowState.prepared = Boolean(prepared.ok);
  workflowState.generatedCaption = Boolean(
    job.finalCaption || job.variants.length
  );
  hydrateForm();
  renderAll();
  setStatus(prepared.ok ? "Property files ready" : "Property check failed");
  toast(prepared.ok ? "Property check complete." : "Property check failed.");
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
  log("Created a new property");
  toast("New property added.");
});

el("processNext").addEventListener("click", async () => {
  const response = await requestJson("/api/queue/next", { method: "POST" });
  if (response.ok && response.data.property_name) {
    refs.propertyName.value = response.data.property_name;
    await prepareSelectedJob("queue");
    return;
  }
  setStatus(response.data?.detail || "No properties waiting in the queue");
  toast(response.data?.detail || "No properties available right now.");
});

refs.zipDownload.addEventListener("click", (event) => {
  if (refs.zipDownload.getAttribute("aria-disabled") === "true") {
    event.preventDefault();
    return;
  }
  workflowState.downloadedAssets = true;
  updateWorkflowGuide();
  log("Photo package downloaded");
});

[refs.checkCaptionApproved, refs.checkPhotosSelected, refs.checkPostedToFacebook].forEach(
  (checkbox) => {
    checkbox.addEventListener("change", updateWorkflowGuide);
  }
);

doc.documentElement.setAttribute(
  "data-theme",
  localStorage.getItem("apg-theme") || "light"
);

const workflowNav = {
  nextToPhotos: "photos",
  backToDetails: "details",
  nextToCaption: "caption",
  backToPhotos: "photos",
  nextToPublish: "publish",
  backToCaption: "caption",
  nextToLog: "log",
  backToPublish: "publish",
};

Object.entries(workflowNav).forEach(([buttonId, targetStep]) => {
  const btn = el(buttonId);
  if (!btn) return;
  btn.addEventListener("click", () => {
    setActiveStep(targetStep);
    updateWorkflowTabs();
  });
});

setStatus("Ready when you are");
renderAll();
log("Console initialized");
prepareTrackerPreview();
