from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .firebase_auth import FirebaseTokenVerifier, require_firebase_user, require_role
from .job_store import InMemoryJobStore
from .review_pipeline import PreparedPost, ReviewPipeline

STATIC_DIR = Path(__file__).parent / "static"
DEFAULT_FIREBASE_PROJECT_ID = "apg-posting-desk-deign-2026"


class PrepareRequest(BaseModel):
    property_name: str


class LogRequest(BaseModel):
    property_name: str
    facebook_url: str


class JobIntakeRequest(BaseModel):
    property_name: str
    assigned_by: str
    operator: str
    due_date: str
    drive_url: str


class MarkPostedRequest(BaseModel):
    facebook_url: str


def _now_time() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Manila")).strftime("%H:%M")


def create_app(
    *,
    drive,
    caption_generator,
    tracker,
    auth_verifier: FirebaseTokenVerifier | None = None,
    queue=None,
    job_store=None,
    auth_required: bool = False,
    download_root: Path = Path("prepared"),
    static_dir: Path = STATIC_DIR,
    firebase_project_id: str = DEFAULT_FIREBASE_PROJECT_ID,
) -> FastAPI:
    (download_root / "_public").mkdir(parents=True, exist_ok=True)
    static_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="APG Review Dashboard")
    pipeline = ReviewPipeline(
        drive=drive,
        caption_generator=caption_generator,
        tracker=tracker,
        download_root=download_root,
    )
    preparations: dict[str, PreparedPost] = {}
    jobs = job_store if job_store is not None else InMemoryJobStore()
    _demo_display_names = {
        "admin": "Demo Admin",
        "maam_jean": "Demo Ma'am Jean",
        "user": "Demo User",
    }

    def _demo_user(
        x_demo_role: str | None = Header(default=None, alias="X-Demo-Role"),
    ) -> dict:
        role = x_demo_role if x_demo_role in ("admin", "maam_jean", "user") else "user"
        return {
            "uid": "demo",
            "email": "demo@apg.local",
            "role": role,
            "display_name": _demo_display_names.get(role, "Demo User"),
        }

    user_dependency = (
        require_firebase_user(auth_verifier)
        if auth_required and auth_verifier is not None
        else _demo_user
    )
    admin_dependency = require_role("admin", "maam_jean", user_dependency=user_dependency)

    @app.get("/api/session")
    def session(user=Depends(user_dependency)) -> dict:
        return {"user": user, "firebase_project_id": firebase_project_id}

    @app.post("/api/prepare")
    def prepare(request: PrepareRequest, user=Depends(user_dependency)) -> dict:
        try:
            prepared = pipeline.prepare(request.property_name.strip())
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        preparation_id = uuid.uuid4().hex
        public_dir = download_root / "_public" / preparation_id
        public_dir.mkdir(parents=True, exist_ok=True)
        public_images = []
        for image in prepared.images:
            target = public_dir / image.name
            shutil.copyfile(image, target)
            public_images.append(
                {
                    "name": image.name,
                    "url": f"/prepared/{preparation_id}/{image.name}",
                }
            )

        public_prepared = PreparedPost(
            property_id=prepared.property_id,
            property_name=prepared.property_name,
            caption=prepared.caption,
            caption_document_name=prepared.caption_document_name,
            caption_details=prepared.caption_details,
            images=[public_dir / image["name"] for image in public_images],
            requires_manual_review=prepared.requires_manual_review,
            violations=prepared.violations,
        )
        preparations[preparation_id] = public_prepared
        return {
            "preparation_id": preparation_id,
            "property_name": prepared.property_name,
            "caption": prepared.caption,
            "caption_document_name": prepared.caption_document_name,
            "caption_details": prepared.caption_details,
            "images": public_images,
            "download_zip_url": f"/api/preparations/{preparation_id}/images.zip",
            "requires_manual_review": prepared.requires_manual_review,
            "violations": prepared.violations or [],
        }

    @app.get("/api/preparations/{preparation_id}/images.zip")
    def download_zip(preparation_id: str) -> FileResponse:
        prepared = preparations.get(preparation_id)
        if prepared is None:
            raise HTTPException(status_code=404, detail="Preparation not found")

        zip_path = download_root / "_public" / preparation_id / "images.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for image in prepared.images:
                archive.write(image, arcname=image.name)
        return FileResponse(zip_path, media_type="application/zip", filename="images.zip")

    @app.post("/api/log")
    def log_post(request: LogRequest, user=Depends(user_dependency)) -> dict:
        try:
            pipeline.log_post(request.property_name.strip(), request.facebook_url.strip())
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"status": "logged"}

    @app.get("/api/jobs")
    def list_jobs(user=Depends(user_dependency)) -> dict:
        return {"jobs": jobs.list_jobs(), "counts": jobs.counts()}

    @app.post("/api/jobs", status_code=201)
    def create_job(request: JobIntakeRequest, user=Depends(admin_dependency)) -> dict:
        return jobs.create(
            property_name=request.property_name.strip(),
            assigned_by=request.assigned_by.strip(),
            operator=request.operator.strip(),
            due_date=request.due_date.strip(),
            drive_url=request.drive_url.strip(),
        )

    @app.post("/api/jobs/{job_id}/mark-posted")
    def mark_posted(
        job_id: str,
        request: MarkPostedRequest,
        user=Depends(user_dependency),
    ) -> dict:
        facebook_url = request.facebook_url.strip()
        job = jobs.get_job(job_id)
        property_name = job.property_name if job else job_id
        try:
            pipeline.log_post(property_name, facebook_url)
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return jobs.mark_posted(job_id, facebook_url)

    @app.post("/api/jobs/{job_id}/validate")
    def validate_job(job_id: str, user=Depends(user_dependency)) -> dict:
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            queue = pipeline.queue.build_queue([job.property_name])
            ok = job.property_name not in queue.errors and len(queue.ready) > 0
            errors = queue.errors.get(job.property_name, "")
        except Exception:
            ok = False
            errors = "Unable to validate Drive folder"
        jobs.add_activity(job_id, {"at": _now_time(), "text": f"Validation {'passed' if ok else 'failed'}"})
        return {"ok": ok, "data": {"property_name": job.property_name, "errors": errors}}

    @app.post("/api/jobs/{job_id}/prepare")
    def prepare_job(job_id: str, user=Depends(user_dependency)) -> dict:
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        try:
            prepared = pipeline.prepare(job.property_name.strip())
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

        preparation_id = uuid.uuid4().hex
        public_dir = download_root / "_public" / preparation_id
        public_dir.mkdir(parents=True, exist_ok=True)
        public_images = []
        for image in prepared.images:
            target = public_dir / image.name
            shutil.copyfile(image, target)
            public_images.append({
                "name": image.name,
                "url": f"/prepared/{preparation_id}/{image.name}",
                "selected": True,
            })

        prepared_data = {
            "property_name": prepared.property_name,
            "caption": prepared.caption,
            "caption_document_name": prepared.caption_document_name,
            "caption_details": prepared.caption_details,
            "images": public_images,
            "variants": [prepared.caption],
            "violations": prepared.violations or [],
            "requires_manual_review": prepared.requires_manual_review,
        }
        jobs.set_prepared(job_id, prepared_data)
        jobs.add_activity(job_id, {"at": _now_time(), "text": "Pipeline prepared Drive assets and caption."})
        return prepared_data

    @app.post("/api/jobs/{job_id}/captions")
    def generate_captions(job_id: str, user=Depends(user_dependency)) -> dict:
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        details = job.caption_details or job.property_name
        review = pipeline.caption_generator.generate(details)
        variants = [review.text]
        jobs.add_activity(job_id, {"at": _now_time(), "text": "Caption variants generated with APG rules."})
        return {"variants": variants}

    @app.get("/api/jobs/{job_id}/activity")
    def job_activity(job_id: str, user=Depends(user_dependency)) -> dict:
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"activity": jobs.get_activity(job_id)}

    @app.post("/api/queue/next")
    def next_property(user=Depends(admin_dependency)) -> dict:
        if queue is None:
            raise HTTPException(status_code=404, detail="Queue is not configured")
        item = queue.claim_next(operator_uid=user["uid"])
        if item is None:
            raise HTTPException(status_code=404, detail="No pending properties")
        return {"id": item.id, "property_name": item.property_name}

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/{asset_name}")
    def static_asset(asset_name: str) -> FileResponse:
        allowed = {
            "index.html",
            "styles.css",
            "app.js",
            "manifest.webmanifest",
            "service-worker.js",
            "icon.svg",
        }
        if asset_name not in allowed:
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(static_dir / asset_name)

    app.mount("/prepared", StaticFiles(directory=download_root / "_public"), name="prepared")
    return app
