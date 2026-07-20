from __future__ import annotations

import io
import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from .job_store import InMemoryJobStore
from .auth_deps import require_role

from .review_pipeline import PreparedPost, ReviewPipeline

STATIC_DIR = Path(__file__).parent / "static"


class PrepareRequest(BaseModel):
    property_name: str


class LogRequest(BaseModel):
    property_name: str
    facebook_url: str


class JobIntakeRequest(BaseModel):
    property_name: str
    offering_id: str = ""
    assigned_by: str
    operator: str
    due_date: str
    drive_url: str


class MarkPostedRequest(BaseModel):
    facebook_url: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateUserRequest(BaseModel):
    email: str
    password: str
    role: str = "user"
    display_name: str | None = None


def _now_time() -> str:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    return datetime.now(ZoneInfo("Asia/Manila")).strftime("%H:%M")




def create_app(
    *,
    drive,
    caption_generator,
    tracker,
    auth_verifier=None,
    queue=None,
    job_store=None,
    asset_service=None,
    auth_required: bool = False,
    download_root: Path = Path("prepared"),
    static_dir: Path = STATIC_DIR,
) -> FastAPI:
    try:
        (download_root / "_public").mkdir(parents=True, exist_ok=True)
        static_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    app = FastAPI(title="APG Review Dashboard")
    pipeline = ReviewPipeline(
        drive=drive,
        caption_generator=caption_generator,
        tracker=tracker,
        download_root=download_root,
    )
    preparations: dict[str, PreparedPost] = {}
    jobs = job_store if job_store is not None else InMemoryJobStore()
    def _user_from_header_or_token(
        authorization: str | None = Header(default=None, alias="Authorization"),
        x_demo_role: str | None = Header(default=None, alias="X-Demo-Role"),
    ) -> dict:
        # X-Demo-Role support for tests and demo environments
        if x_demo_role and x_demo_role in ("admin", "user"):
            return {
                "uid": "demo-" + x_demo_role,
                "email": x_demo_role + "@apg.local",
                "role": x_demo_role,
                "display_name": x_demo_role.title(),
            }
        if auth_required and auth_verifier is None:
            raise HTTPException(status_code=401, detail="Auth not configured")
        if auth_verifier is not None:
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing access token")
            token = authorization.removeprefix("Bearer ").strip()
            try:
                return auth_verifier.verify(token)
            except Exception as err:
                raise HTTPException(status_code=401, detail="Invalid access token") from err
        import uuid
        return {
            "uid": str(uuid.uuid4()),
            "email": "anonymous@apg.local",
            "role": "user",
            "display_name": "Anonymous",
        }

    user_dependency = _user_from_header_or_token
    admin_dependency = require_role("admin", user_dependency=user_dependency)

    @app.get("/api/session")
    def session(user=Depends(user_dependency)) -> dict:
        return {"user": user}

    @app.post("/api/admin/users", status_code=201)
    def create_user(request: CreateUserRequest, user=Depends(admin_dependency)) -> dict:
        if auth_verifier is None:
            return {
                "uid": "seed-admin",
                "email": request.email,
                "role": request.role,
                "display_name": request.display_name or request.email,
                "status": "demo-created",
            }
        return auth_verifier.create_user(
            email=request.email,
            password=request.password,
            role=request.role,
            display_name=request.display_name,
        )

    @app.post("/api/admin/seed")
    def seed_accounts(user=Depends(admin_dependency)) -> dict:
        return auth_verifier.seed_accounts()

    @app.post("/api/prepare")
    def prepare(request: PrepareRequest, user=Depends(user_dependency)) -> dict:
        prop_name = request.property_name.strip()
        # In Supabase mode, the frontend flow uses /api/jobs/{id}/prepare;
            # this legacy route returns a lightweight placeholder.
        try:
            prepared = pipeline.prepare(prop_name)
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
        public_dir = download_root / "_public" / preparation_id
        if not public_dir.is_dir():
            raise HTTPException(status_code=404, detail="Preparation not found")
        images = [p for p in public_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not images:
            raise HTTPException(status_code=404, detail="No images in preparation")
        zip_path = public_dir / "images.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for image in images:
                archive.write(image, arcname=image.name)
        return FileResponse(zip_path, media_type="application/zip", filename="images.zip")

    @app.get("/api/jobs/{job_id}/prepared.zip")
    def download_job_zip(job_id: str, user=Depends(user_dependency)) -> StreamingResponse:
        """Stream a ZIP of the job's selected images from Supabase Storage."""
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        if asset_service is None:
            raise HTTPException(status_code=503, detail="Asset service not configured")
        assets = jobs.get_prepared_image_assets(job_id)
        if not assets:
            raise HTTPException(status_code=404, detail="No prepared assets for job")
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for a in assets:
                sp = a.get("storage_path", "")
                bucket = a.get("storage_bucket", "apg-public")
                name = a.get("original_name", a["asset_id"])
                if not sp:
                    continue
                try:
                    raw = asset_service.client.storage.from_(bucket).download(sp)
                    if isinstance(raw, bytes):
                        zf.writestr(name, raw)
                    elif raw:
                        zf.writestr(name, b"".join(raw))
                except Exception:
                    pass
        buf.seek(0)
        return StreamingResponse(
            buf,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=\"{job_id}-images.zip\""},
        )

    @app.get("/api/drive/files/{file_id}")
    def drive_file(file_id: str, user=Depends(user_dependency)) -> FileResponse:
        """Stream a Drive file bytes directly to the browser."""
        from fastapi.responses import StreamingResponse
        try:
            import io
            from googleapiclient.http import MediaIoBaseDownload
            request = drive.service.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)
            return StreamingResponse(buf, media_type="image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found: {e}")

    @app.post("/api/log")
    def log_post(request: LogRequest, user=Depends(user_dependency)) -> dict:
        try:
            pipeline.log_post(request.property_name.strip(), request.facebook_url.strip())
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"status": "logged"}

    @app.get("/api/drive/properties")
    def drive_properties(user=Depends(user_dependency)) -> dict:
        folders = []
        try:
            folders = drive.list_property_folders()
        except Exception as e:
            pass
        return {"properties": folders}

    @app.get("/api/jobs")
    def list_jobs(user=Depends(user_dependency)) -> dict:
        return {"jobs": jobs.list_jobs(), "counts": jobs.counts()}

    @app.post("/api/jobs", status_code=201)
    def create_job(request: JobIntakeRequest, user=Depends(admin_dependency)) -> dict:
        drive_url = request.drive_url.strip()
        property_name = request.property_name.strip()
        if drive_url:
            folder_id = drive.resolve_folder_id(drive_url)
            if folder_id and not folder_id.startswith("https://"):
                drive_url = f"https://drive.google.com/drive/folders/{folder_id}"
        return jobs.create(
            property_name=property_name,
            offering_id=request.offering_id.strip(),
            assigned_by=request.assigned_by.strip(),
            operator=request.operator.strip(),
            due_date=request.due_date.strip(),
            drive_url=drive_url,
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
            folder = drive.find_property_folder(job.property_name)
            if folder is None:
                return {"valid": False, "image_count": 0, "has_caption_doc": False, "errors": ["Property folder not found in Drive"]}
            image_count = len(folder.get("image_files", []))
            has_caption_doc = len(folder.get("document_files", [])) > 0
            errors = []
            if image_count < 3:
                errors.append(f"Only {image_count} image(s) found (minimum 3 required)")
            if not has_caption_doc:
                errors.append("No caption document found")
            valid = len(errors) == 0
            jobs.add_activity(job_id, {"at": _now_time(), "text": f"Validation {'passed' if valid else 'failed'}: {image_count} images, caption doc {'present' if has_caption_doc else 'missing'}"})
            return {"valid": valid, "image_count": image_count, "has_caption_doc": has_caption_doc, "errors": errors}
        except Exception as e:
            return {"valid": False, "image_count": 0, "has_caption_doc": False, "errors": [f"Validation error: {e}"]}

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
            "id": job_id,
            "property_name": prepared.property_name,
            "caption": prepared.caption,
            "caption_document_name": prepared.caption_document_name,
            "caption_details": prepared.caption_details,
            "images": public_images,
            "variants": [prepared.caption],
            "violations": prepared.violations or [],
            "requires_manual_review": prepared.requires_manual_review,
            "drive_url": job.drive_url,
            "status": job.status,
            "download_zip_url": f"/api/preparations/{preparation_id}/images.zip",
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
        warnings = list(review.violations or [])
        jobs.add_activity(job_id, {"at": _now_time(), "text": "Caption generated with APG rules."})
        return {"caption": review.text, "warnings": warnings}

    @app.get("/api/jobs/{job_id}/activity")
    def job_activity(job_id: str, user=Depends(user_dependency)) -> dict:
        job = jobs.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        raw = jobs.get_activity(job_id)
        events = []
        for entry in raw:
            events.append({
                "timestamp": entry.get("at", ""),
                "action": entry.get("text", ""),
                "actor": entry.get("actor", "system"),
            })
        return {"events": events}

    @app.post("/api/queue/next")
    def next_property(user=Depends(admin_dependency)) -> dict:
        if queue is None:
            raise HTTPException(status_code=404, detail="Queue is not configured")
        item = queue.claim_next(operator_uid=user["uid"])
        if item is None:
            raise HTTPException(status_code=404, detail="No pending properties")
        return {"id": item.id, "property_name": item.property_name}

    @app.get("/api/offerings")
    def list_offerings(user=Depends(user_dependency)) -> dict:
        if asset_service is None:
            return {"offerings": []}
        res = asset_service.client.table("offerings").select("id,title,slug,location,category_id,transaction_type_id,is_published,deleted_at").is_("deleted_at", "null").order("title").limit(200).execute()
        return {"offerings": res.data or []}

    @app.post("/api/assets/signed-url")
    def asset_signed_url(payload: dict, user=Depends(user_dependency)) -> dict:
        if asset_service is None:
            raise HTTPException(status_code=503, detail="Asset service not configured")
        asset_id = (payload or {}).get("asset_id")
        expires_in = int((payload or {}).get("expires_in", 3600))
        asset = asset_service._get_asset(asset_id) if asset_id else None
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        sp = asset.get("storage_path")
        bucket = asset.get("storage_bucket", asset_service.bucket_private)
        if asset.get("is_public") and bucket == asset_service.bucket_public:
            url = asset_service.client.storage.from_(bucket).get_public_url(sp)
            return {"url": url}
        res = asset_service.client.storage.from_(bucket).create_signed_url(sp, expires_in)
        url = res.get("signedURL") if isinstance(res, dict) else getattr(res, "signedURL", "")
        return {"url": url}
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

    # In Supabase mode the /prepared mount is unused (images come from Storage
    # signed URLs). In demo/local mode, mount the _public directory for
    # /prepared/{id}/{name} image serving.
    try:
        app.mount("/prepared", StaticFiles(directory=download_root / "_public"), name="prepared")
    except Exception:
        pass
    return app




