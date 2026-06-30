import json
from pathlib import Path


def test_package_json_has_npm_dev_script_for_pwa():
    package = json.loads(Path("package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["dev"].startswith("concurrently")
    assert "vite --host 0.0.0.0" in package["scripts"]["dev"]
    assert "python -m apg_automation.main --serve" in package["scripts"]["dev"]


def test_vite_config_proxies_api_and_prepared_assets():
    config = Path("vite.config.js").read_text(encoding="utf-8")

    assert '"/api"' in config
    assert '"/prepared"' in config
    assert "http://127.0.0.1:8000" in config


def test_frontend_entry_exists_and_calls_prepare_and_log_routes():
    source = Path("src/main.js").read_text(encoding="utf-8")

    assert "GoogleAuthProvider" in source
    assert "setCustomParameters" in source
    assert "hd:" in source
    assert "getIdToken" in source
    assert "Authorization" in source
    assert 'authFetch("/api/prepare"' in source
    assert 'authFetch("/api/log"' in source
    assert "serviceWorker" in source


def test_caption_panel_shows_source_doc_and_generate_button():
    html = Path("index.html").read_text(encoding="utf-8")
    source = Path("src/main.js").read_text(encoding="utf-8")

    assert "Source Caption Document" in html
    assert "sourceDocName" in html
    assert "captionSourceOutput" in html
    assert "generateCaption" in html
    assert "Generate Caption" in html
    assert "captionGuidance" in html
    assert "No emojis" in html
    assert "least term" in html
    assert "negotiables" in html
    assert "negotioables" in source
    assert "workflowState.generatedCaption" in source
    assert "generateCaptionButton.addEventListener" in source


def test_workflow_progress_guide_markup_lists_required_operator_steps():
    html = Path("index.html").read_text(encoding="utf-8")

    assert "Workflow Progress Guide" in html
    assert "Step 1: Download Assets" in html
    assert "Save these 3+ images to your local device." in html
    assert "Step 2: Copy the Caption" in html
    assert "The AI has automatically stripped emojis and restricted words." in html
    assert "Step 3: Post to Facebook" in html
    assert "Open Facebook Profile/Alt Account" in html
    assert "Step 4: Copy &amp; Paste Live URL" in html
    assert "Step 5: Finalize &amp; Log" in html


def test_workflow_progress_logic_gates_steps_in_order():
    source = Path("src/main.js").read_text(encoding="utf-8")

    assert "workflowState.downloadedAssets" in source
    assert "workflowState.copiedCaption" in source
    assert "workflowState.openedFacebook" in source
    assert "updateWorkflowGuide()" in source
    assert "canEnterFacebookUrl" in source
    assert "facebookUrlGroup.hidden = !canEnterFacebookUrl" in source
    assert "logButton.disabled = !canLogPost" in source


def test_frontend_markup_matches_prototype_console_sections():
    html = Path("index.html").read_text(encoding="utf-8")

    assert "APG Posting Console" in html
    assert "Assigned today" in html
    assert "Waiting approval" in html
    assert "Ready to post" in html
    assert "Posted today" in html
    assert "JOB LIST" in html
    assert "Intake and validation" in html
    assert "Drive assets" in html
    assert "Caption workbench" in html
    assert "Human-in-the-loop publish" in html
    assert "Tracker sync preview" in html
    assert "Activity log" in html
    assert "Toggle theme" in html


def test_frontend_source_declares_role_and_job_api_contracts():
    source = Path("src/main.js").read_text(encoding="utf-8")

    assert "admin" in source
    assert "maam_jean" in source
    assert "user" in source
    assert 'authFetch("/api/session"' in source
    assert 'authFetch("/api/jobs"' in source
    assert 'authFetch(`/api/jobs/${jobId}/validate`' in source
    assert 'authFetch(`/api/jobs/${jobId}/prepare`' in source
    assert 'authFetch(`/api/jobs/${jobId}/captions`' in source
    assert 'authFetch(`/api/jobs/${jobId}/mark-posted`' in source
    assert 'authFetch(`/api/jobs/${jobId}/activity`' in source
