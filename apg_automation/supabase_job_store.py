from __future__ import annotations

from datetime import date

from .job_store import OperationalJob


class SupabaseJobStore:
    """Posting workflow store backed by posting_jobs + posting_job_assets + activity_log.

    Jobs are bound to canonical offerings via offering_id. Per-job operator activity is
    written to the shared activity_log (entity='posting_job'); selected images live in
    posting_job_assets referencing canonical assets.id (no byte duplication).
    """

    def __init__(self, client) -> None:
        self.client = client

    def list_jobs(self) -> list[dict]:
        rows = (
            self.client.table("posting_jobs")
            .select("*")
            .order("created_on", desc=True)
            .order("id", desc=True)
            .execute()
        )
        return [self._row_to_response(r) for r in (rows.data or [])]

    def counts(self) -> dict[str, int]:
        rows = self.client.table("posting_jobs").select("status,created_on").execute()
        today = date.today()
        assigned_today = waiting = ready = posted_today = 0
        for r in rows.data or []:
            s = r.get("status", "")
            co = r.get("created_on", "")
            on_today = co == today.isoformat() if isinstance(co, str) else False
            if s == "assigned" and on_today:
                assigned_today += 1
            elif s == "preparing":
                waiting += 1
            elif s == "ready":
                ready += 1
            elif s == "posted" and on_today:
                posted_today += 1
        return {
            "assigned_today": assigned_today,
            "waiting_approval": waiting,
            "ready_to_post": ready,
            "posted_today": posted_today,
        }

    def create(self, *, property_name: str, assigned_by: str, operator: str,
               due_date: str, drive_url: str = "", offering_id: str = "") -> dict:
        today = date.today()
        prefix = f"APG-{today:%m%d}-"
        count = (
            self.client.table("posting_jobs")
            .select("id", count="exact")
            .like("id", f"{prefix}%")
            .execute()
        )
        seq = (count.count or 0) + 1
        job_id = f"{prefix}{seq:03d}"
        payload = {
            "id": job_id,
            "property_name": property_name,
            "offering_id": offering_id or None,
            "assigned_by": assigned_by,
            "operator": operator,
            "due_date": due_date or None,
            "status": "assigned",
            "created_on": today.isoformat(),
        }
        self.client.table("posting_jobs").insert(payload).execute()
        return OperationalJob(
            id=job_id, property_name=property_name, offering_id=offering_id,
            assigned_by=assigned_by, operator=operator, due_date=due_date,
            drive_url=drive_url, status="assigned", created_on=today,
        ).to_response()

    def mark_posted(self, job_id: str, facebook_url: str) -> dict:
        self.client.table("posting_jobs").update({
            "status": "posted", "final_facebook_url": facebook_url,
        }).eq("id", job_id).execute()
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        return job.to_response()

    def get_job(self, job_id: str) -> OperationalJob | None:
        res = self.client.table("posting_jobs").select("*").eq("id", job_id).limit(1).execute()
        rows = res.data if res and res.data else []
        return self._row_to_job(rows[0]) if rows else None

    def update_status(self, job_id: str, status: str) -> dict:
        self.client.table("posting_jobs").update({"status": status}).eq("id", job_id).execute()
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        return job.to_response()

    def set_prepared(self, job_id: str, prepared_data: dict) -> dict:
        update = {
            "caption": prepared_data.get("caption", ""),
            "selected_caption": prepared_data.get("caption", ""),
            "caption_details": prepared_data.get("caption_details", ""),
            "caption_document_name": prepared_data.get("caption_document_name", ""),
            "variants": prepared_data.get("variants", []),
            "violations": prepared_data.get("violations", []),
            "requires_manual_review": prepared_data.get("requires_manual_review", False),
        }
        if update["caption"]:
            update["status"] = "ready"
        self.client.table("posting_jobs").update(update).eq("id", job_id).execute()
        job = self.get_job(job_id)
        return job.to_response() if job else update

    def select_job_assets(self, job_id: str, asset_ids: list[str]) -> list[dict]:
        """Replace a job's selected canonical assets (ordered subset for one FB post)."""
        self.client.table("posting_job_assets").delete().eq("job_id", job_id).execute()
        for idx, aid in enumerate(asset_ids):
            self.client.table("posting_job_assets").insert({
                "job_id": job_id, "asset_id": aid, "display_order": idx, "selected": True,
            }).execute()
        res = self.client.table("posting_job_assets").select("*, asset:assets(*)").eq("job_id", job_id).order("display_order").execute()
        return res.data or []

    def get_prepared_image_assets(self, job_id: str) -> list[dict]:
        """Return selected assets for a job with full asset metadata, including
        storage_path and storage_bucket for zip streaming."""
        res = (
            self.client.table("posting_job_assets")
            .select("*, asset:assets(*)")
            .eq("job_id", job_id)
            .eq("selected", True)
            .order("display_order")
            .execute()
        )
        rows = res.data or []
        results = []
        for row in rows:
            a = row.get("asset") or {}
            results.append({
                "asset_id": row["asset_id"],
                "display_order": row.get("display_order", 0),
                "original_name": a.get("original_name", ""),
                "storage_path": a.get("storage_path", ""),
                "storage_bucket": a.get("storage_bucket", "apg-public"),
                "mime_type": a.get("mime_type", "application/octet-stream"),
            })
        return results

    def approve(self, job_id: str, *, actor_uid: str | None = None) -> dict:
        from datetime import datetime
        self.client.table("posting_jobs").update({
            "status": "ready", "approved_by": actor_uid,
            "approved_at": datetime.utcnow().isoformat(),
        }).eq("id", job_id).execute()
        job = self.get_job(job_id)
        return job.to_response() if job else {}

    def add_activity(self, job_id: str, entry: dict) -> None:
        try:
            self.client.table("activity_log").insert({
                "action": "job_activity", "entity": "posting_job",
                "entity_id": job_id, "meta": {"at": entry.get("at", ""), "text": entry.get("text", "")},
            }).execute()
        except Exception:
            pass

    def get_activity(self, job_id: str) -> list[dict]:
        res = (
            self.client.table("activity_log")
            .select("meta,created_at")
            .eq("entity", "posting_job")
            .eq("entity_id", job_id)
            .order("created_at")
            .execute()
        )
        out = []
        for r in res.data or []:
            meta = r.get("meta") or {}
            out.append({"at": meta.get("at", ""), "text": meta.get("text", "")})
        return out

    def _row_to_job(self, r: dict) -> OperationalJob:
        from datetime import date as dt_date
        co = r.get("created_on")
        if isinstance(co, str):
            parts = co.split("-")
            try:
                co = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))
            except Exception:
                co = dt_date.today()
        return OperationalJob(
            id=r.get("id", ""),
            property_name=r.get("property_name", ""),
            offering_id=r.get("offering_id") or "",
            assigned_by=r.get("assigned_by", ""),
            operator=r.get("operator", ""),
            due_date=r.get("due_date") or "",
            drive_url=r.get("drive_url", ""),
            status=r.get("status", "assigned"),
            created_on=co or dt_date.today(),
            facebook_url=r.get("final_facebook_url", ""),
            caption=r.get("caption", ""),
            caption_details=r.get("caption_details", ""),
            caption_document_name=r.get("caption_document_name", ""),
            variants=r.get("variants", []) or [],
            violations=r.get("violations", []) or [],
            requires_manual_review=r.get("requires_manual_review", False),
        )

    def _row_to_response(self, r: dict) -> dict:
        return self._row_to_job(r).to_response()