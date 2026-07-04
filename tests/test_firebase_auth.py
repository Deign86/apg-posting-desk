from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from apg_automation.firebase_auth import FirebaseTokenVerifier, require_firebase_user, require_role


class FakeFirebaseAuth:
    def __init__(self):
        self.tokens = []

    def verify_id_token(self, token):
        self.tokens.append(token)
        if token == "valid-token":
            return {"uid": "user-1", "email": "agent@apg.example"}
        raise ValueError("bad token")


def test_firebase_token_verifier_returns_decoded_claims():
    fake_auth = FakeFirebaseAuth()
    verifier = FirebaseTokenVerifier(firebase_auth=fake_auth)

    claims = verifier.verify("valid-token")

    assert claims["uid"] == "user-1"
    assert fake_auth.tokens == ["valid-token"]


def test_require_firebase_user_rejects_missing_bearer_token():
    app = FastAPI()
    verifier = FirebaseTokenVerifier(firebase_auth=FakeFirebaseAuth())

    @app.get("/protected")
    def protected(user=Depends(require_firebase_user(verifier))):
        return user

    response = TestClient(app).get("/protected")

    assert response.status_code == 401


def test_require_firebase_user_accepts_valid_bearer_token():
    app = FastAPI()
    verifier = FirebaseTokenVerifier(firebase_auth=FakeFirebaseAuth())

    @app.get("/protected")
    def protected(user=Depends(require_firebase_user(verifier))):
        return {"uid": user["uid"]}

    response = TestClient(app).get(
        "/protected",
        headers={"Authorization": "Bearer valid-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"uid": "user-1"}


def test_require_firebase_user_exposes_apg_role_profile_from_claims():
    class RoleFirebaseAuth(FakeFirebaseAuth):
        def verify_id_token(self, token):
            self.tokens.append(token)
            if token == "admin-token":
                return {
                    "uid": "admin-1",
                    "email": "admin@apg.example",
                    "role": "admin",
                    "name": "Admin",
                }
            raise ValueError("bad token")

    app = FastAPI()
    verifier = FirebaseTokenVerifier(firebase_auth=RoleFirebaseAuth())

    @app.get("/session-user")
    def session_user(user=Depends(require_firebase_user(verifier))):
        return {
            "uid": user["uid"],
            "email": user["email"],
            "role": user["role"],
            "display_name": user.get("display_name"),
        }

    response = TestClient(app).get(
        "/session-user",
        headers={"Authorization": "Bearer admin-token"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "uid": "admin-1",
        "email": "admin@apg.example",
        "role": "admin",
        "display_name": "Admin",
    }


def test_firebase_auth_exports_role_dependency_for_admin_denial():
    import apg_automation.firebase_auth as firebase_auth

    assert hasattr(firebase_auth, "require_role"), (
        "admin-only APIs need a reusable role dependency that rejects "
        "non-admin Firebase users"
    )


def test_require_role_denies_non_admin_user():
    app = FastAPI()
    mock_user_dep = lambda: {"uid": "u1", "email": "u@apg.example", "role": "user", "display_name": "User"}
    admin_dep = require_role("admin", user_dependency=mock_user_dep)

    @app.get("/admin-only")
    def admin_only(user=Depends(admin_dep)):
        return user

    response = TestClient(app).get("/admin-only")
    assert response.status_code == 403


def test_require_role_allows_admin_user():
    app = FastAPI()
    mock_user_dep = lambda: {"uid": "a1", "email": "a@apg.example", "role": "admin", "display_name": "Admin"}
    admin_dep = require_role("admin", user_dependency=mock_user_dep)

    @app.get("/admin-only")
    def admin_only(user=Depends(admin_dep)):
        return {"uid": user["uid"]}

    response = TestClient(app).get("/admin-only")
    assert response.status_code == 200
    assert response.json() == {"uid": "a1"}




