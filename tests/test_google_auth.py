from apg_automation.google_auth import GOOGLE_SCOPES, build_google_credentials


class FakeServiceAccountCredentials:
    @staticmethod
    def from_service_account_file(path, scopes):
        return {"kind": "service-account", "path": path, "scopes": scopes}


def fake_default(scopes):
    return {"kind": "adc", "scopes": scopes}, "project-id"


def test_build_google_credentials_uses_service_account_file(monkeypatch):
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")

    credentials = build_google_credentials(
        service_account_credentials=FakeServiceAccountCredentials,
        default_credentials_loader=fake_default,
    )

    assert credentials == {
        "kind": "service-account",
        "path": "service-account.json",
        "scopes": GOOGLE_SCOPES,
    }


def test_build_google_credentials_falls_back_to_adc(monkeypatch):
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)

    credentials = build_google_credentials(
        service_account_credentials=FakeServiceAccountCredentials,
        default_credentials_loader=fake_default,
    )

    assert credentials == {"kind": "adc", "scopes": GOOGLE_SCOPES}
