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

    assert "createClient" in source
    assert "@supabase/supabase-js" in source
    assert "signInWithPassword" in source
    assert "access_token" in source
    assert "Authorization" in source
    assert 'authFetch("/api/prepare"' in source
    assert 'authFetch("/api/log"' in source
    assert "serviceWorker" in source


def test_caption_panel_shows_source_doc_and_generate_button():
    html = Path("index.html").read_text(encoding="utf-8")
    source = Path("src/main.js").read_text(encoding="utf-8")

    assert "Caption source file" in html
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
    assert "Step 1: Download photos" in html
    assert "Save the selected photos to your device." in html
    assert "Step 2: Copy the caption" in html
    assert "Emojis and restricted words have already been removed by the system." in html
    assert "Step 3: Post to Facebook" in html
    assert "Open Facebook and publish the post manually." in html
    assert "Step 4: Paste the live post URL" in html
    assert "Step 5: Log the post" in html


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

    assert "APG Posting Workspace" in html
    assert "Assigned today" in html
    assert "Waiting approval" in html
    assert "Ready to post" in html
    assert "Posted today" in html
    assert "PROPERTY LIST" in html
    assert "Property details" in html
    assert "Property photos" in html
    assert "Caption drafting" in html
    assert "Facebook posting" in html
    assert "Post log" in html
    assert "Recent actions" in html
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


def test_auth_card_contains_role_selector():
    html = (Path("index.html")).read_text(encoding="utf-8")
    assert "role-selector" in html, "Auth card must contain the role selector container"
    assert "data-role-option" in html, "Auth card must contain role option buttons with data-role-option attribute"
    assert 'data-role="user"' in html, "Must offer the 'user' role option"
    assert 'data-role="admin"' in html, "Must offer the 'admin' role option"


def test_auth_card_role_selector_hidden_when_authenticated():
    html = (Path("index.html")).read_text(encoding="utf-8")
    # Role selector must have id="role-selector" for JS toggling
    assert 'id="role-selector"' in html, "Role selector must have id='role-selector'"


def test_styles_include_role_selector_rules():
    css = (Path("src/styles.css")).read_text(encoding="utf-8")
    assert ".role-selector" in css, "styles.css must contain .role-selector rule"
    assert ".role-option" in css, "styles.css must contain .role-option rule"


def test_admin_buttons_marked_data_admin_only():
    html = Path("index.html").read_text(encoding="utf-8")
    assert 'id="newJobBtn"' in html and "data-admin-only" in html, \
        "newJobBtn must have data-admin-only attribute"
    assert 'id="processNext"' in html and "data-admin-only" in html, \
        "processNext must have data-admin-only attribute"


def test_auth_fetch_sends_x_demo_role_header():
    source = Path("src/main.js").read_text(encoding="utf-8")
    assert "X-Demo-Role" in source, "authFetch must send X-Demo-Role header"
    assert "selectedRole" in source, "main.js must track selectedRole from role selector"


def test_apply_role_gating_function_exists():
    source = Path("src/main.js").read_text(encoding="utf-8")
    assert "applyRoleGating" in source, "main.js must define applyRoleGating function"
    assert 'data-admin-only' in source, "applyRoleGating must toggle [data-admin-only] elements"


def test_role_selector_click_handlers_exist():
    source = Path("src/main.js").read_text(encoding="utf-8")
    assert "data-role-option" in source, "main.js must bind click handlers to [data-role-option] buttons"
    assert "selectedRole = btn.dataset.role" in source, \
        "Click handler must update selectedRole from button dataset"


def test_role_selector_hidden_on_auth():
    source = Path("src/main.js").read_text(encoding="utf-8")
    assert "role-selector" in source and "hidden" in source, \
        "main.js must hide role-selector when user signs in"
    assert "signOut" in source and "role-selector" in source, \
        "main.js must show role-selector on sign out"
