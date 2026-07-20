from __future__ import annotations

import json
import os

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]


def build_google_credentials(
    *,
    service_account_credentials=None,
    default_credentials_loader=None,
):
    if service_account_credentials is None:
        from google.oauth2 import service_account as service_account_module

        service_account_credentials = service_account_module.Credentials
    if default_credentials_loader is None:
        import google.auth

        default_credentials_loader = google.auth.default

    # Prefer GOOGLE_SERVICE_ACCOUNT_JSON (env var holding the full JSON string)
    # over GOOGLE_APPLICATION_CREDENTIALS (file path) over ADC.
    svc_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if svc_json:
        info = json.loads(svc_json)
        return service_account_credentials.from_service_account_info(
            info, scopes=GOOGLE_SCOPES,
        )

    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    if credentials_path:
        return service_account_credentials.from_service_account_file(
            credentials_path,
            scopes=GOOGLE_SCOPES,
        )

    credentials, _ = default_credentials_loader(scopes=GOOGLE_SCOPES)
    return credentials
