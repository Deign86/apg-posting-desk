from __future__ import annotations

import os

import requests


def build_supabase_client(
    *, url: str | None = None, service_role_key: str | None = None
):
    url = (url or os.getenv("SUPABASE_URL", "")).rstrip("/")
    key = service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    return _SupabaseClient(url=url, key=key)


class _SupabaseClient:
    def __init__(self, *, url: str, key: str):
        self._url = url
        self._key = key
    @property
    def auth(self):
        return _AuthClient(self)
    def table(self, name: str):
        return _TableBuilder(self, name)
    def rpc(self, fn: str, params: dict | None = None):
        return _TableBuilder(self, "rpc/" + fn, rpc=params)
    @property
    def storage(self):
        return _StorageClient(self)
    def _headers(self, extra=None):
        h = {"apiKey": self._key, "Authorization": "Bearer " + self._key}
        if extra:
            h.update(extra)
        return h


class _AuthClient:
    def __init__(self, client):
        self._client = client
    def get_user(self, token):
        import requests as req
        resp = req.get(
            self._client._url + "/auth/v1/user",
            headers={"apiKey": self._client._key, "Authorization": "Bearer " + token},
        )
        return _wrap_auth(resp)
    def sign_in_with_password(self, credentials):
        import requests as req
        resp = req.post(
            self._client._url + "/auth/v1/token?grant_type=password",
            json=credentials,
            headers={"apiKey": self._client._key, "Content-Type": "application/json"},
        )
        return resp.json()
    @property
    def admin(self):
        return _AdminClient(self._client)


class _AdminClient:
    def __init__(self, client):
        self._client = client
    def create_user(self, attributes):
        import requests as req
        resp = req.post(
            self._client._url + "/auth/v1/admin/users",
            json=attributes,
            headers=self._client._headers({"Content-Type": "application/json"}),
        )
        data = resp.json() if resp.status_code < 300 else {}
        return _wrap_admin(data)
    def list_users(self):
        import requests as req
        resp = req.get(
            self._client._url + "/auth/v1/admin/users",
            headers=self._client._headers(),
        )
        data = resp.json() if resp.status_code < 300 else []
        return [_wrap_admin(u) for u in data]


class _TableBuilder:
    def __init__(self, client, name, *, rpc=None):
        self._client = client
        self._name = name
        self._rpc = rpc
        self._params = {}
        self._json = None
        self._method = "GET"
    def select(self, cols="*"):
        self._params["select"] = cols
        return self
    def insert(self, data):
        self._method = "POST"
        self._json = data
        return self
    def update(self, data):
        self._method = "PATCH"
        self._json = data
        return self
    def upsert(self, data):
        self._method = "POST"
        self._json = data
        self._params["on_conflict"] = "id"
        return self
    def delete(self):
        self._method = "DELETE"
        return self
    def eq(self, col, val):
        self._params[col] = "eq." + str(val)
        return self
    def like(self, col, pat):
        self._params[col] = "like." + pat
        return self
    def ilike(self, col, pat):
        self._params[col] = "ilike." + pat
        return self
    def is_(self, col, val):
        self._params[col] = "is." + str(val)
        return self
    def order(self, col, *, desc=False):
        self._params["order"] = (col + ".desc") if desc else (col + ".asc")
        return self
    def limit(self, cnt):
        self._params["limit"] = str(cnt)
        return self
    def execute(self):
        import requests as req
        if self._rpc is not None:
            url = self._client._url + "/rest/v1/rpc/" + self._name
            resp = req.post(url, json=self._rpc, headers=self._client._headers({"Content-Type": "application/json"}))
            return _TableResult(resp)
        url = self._client._url + "/rest/v1/" + self._name
        hdrs = self._client._headers()
        if self._json is not None:
            hdrs.update({"Content-Type": "application/json", "Prefer": "return=representation"})
            resp = req.request(self._method, url, json=self._json, headers=hdrs)
        else:
            resp = req.request(self._method, url, params=self._params, headers=hdrs)
        return _TableResult(resp)


class _TableResult:
    def __init__(self, resp):
        self.data = None
        self.count = None
        if resp.status_code < 300:
            try:
                self.data = resp.json()
            except Exception:
                self.data = None
            cr = resp.headers.get("content-range", "")
            if "/" in cr:
                try:
                    self.count = int(cr.split("/")[1])
                except (ValueError, IndexError):
                    pass


class _StorageClient:
    def __init__(self, client):
        self._client = client
    def from_(self, bucket):
        return _Bucket(self._client, bucket)


class _Bucket:
    def __init__(self, client, bucket):
        self._client = client
        self._bucket = bucket
    def download(self, path):
        import requests as req
        resp = req.get(
            self._client._url + "/storage/v1/object/" + self._bucket + "/" + path,
            headers=self._client._headers(),
        )
        return resp.content
    def upload(self, path, data, file_options=None):
        import requests as req
        ct = (file_options or {}).get("content-type", "application/octet-stream")
        resp = req.post(
            self._client._url + "/storage/v1/object/" + self._bucket + "/" + path,
            data=data,
            headers=self._client._headers({"Content-Type": ct}),
        )
        resp.raise_for_status()
    def get_public_url(self, path):
        return self._client._url + "/storage/v1/object/public/" + self._bucket + "/" + path
    def create_signed_url(self, path, expires_in=3600):
        import requests as req
        resp = req.post(
            self._client._url + "/storage/v1/object/sign/" + self._bucket + "/" + path,
            json={"expiresIn": str(expires_in)},
            headers=self._client._headers({"Content-Type": "application/json"}),
        )
        if resp.status_code < 300:
            return resp.json()
        return {"signedURL": ""}


class _AuthUser:
    def __init__(self, uid, email):
        self.id = uid
        self.email = email
    @property
    def user(self):
        return self


class _AdminUser:
    def __init__(self, uid, email):
        self.id = uid
        self.email = email


def _wrap_auth(resp):
    try:
        d = resp.json() if resp.status_code < 300 else {}
    except Exception:
        d = {}
    return _AuthUser(d.get("id", ""), d.get("email", ""))


def _wrap_admin(d):
    return _AdminUser(d.get("id", ""), d.get("email", ""))
