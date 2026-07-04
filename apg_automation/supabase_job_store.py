from __future__ import annotations

from datetime import date

from .job_store import OperationalJob


class SupabaseJobStore:
    def __init__(self, client) -> None:
        self.client = client

    def list_jobs(self) -> list[dict]:
        rows = (
            self.client.table("jobs")
            .select("*")
            .order("created_on", desc=True)
            .order("id", desc=True)
            .execute()
        )
        return [self._row_to_response(r) for r in (rows.data or [])]

    def counts(self) -> dict[str, int]:
        rows = self.client.table("jobs").select("status,created_on").execute()
        today = date.today()
        assigned_today = 0
        waiting = 0
        ready = 0
        posted_today = 0
        for r in rows.data or []:
            s = r.get("status", "")
            co = r.get("created_on", "")
            on_today = co == today.isoformat() if isinstance(co, str) else False
            if s == "assigned" and on_today:
                assigned_today += 1
            elif s == "waiting_approval":
                waiting += 1
            elif s == "ready_to_post":
                ready += 1
            elif s == "posted" and on_today:
                posted_today += 1
        return {
            "assigned_today": assigned_today,
            "waiting_approval": waiting,
            "ready_to_post": ready,
            "posted_today": posted_today,
        }

    def create(
        self,
        *,
        property_name: str,
        assigned_by: str,
        operator: str,
        due_date: str,
        drive_url: str,
    ) -> dict:
        today = date.today()
        prefix = f"APG-{today:%m%d}-"
        count = (
            self.client.table("jobs")
            .select("id", count="exact")
            .like("id", f"{prefix}%")
            .execute()
        )
        seq = (count.count or 0) + 1
        job_id = f"{prefix}{seq:03d}"
        payload = {
            "id": job_id,
            "property_name": property_name,
            "assigned_by": assigned_by,
            "operator": operator,
            "due_date": due_date,
            "drive_url": drive_url,
            "status": "assigned",
            "created_on": today.isoformat(),
        }
        self.client.table("jobs").insert(payload).execute()
        return OperationalJob(
            id=job_id,
            property_name=property_name,
            assigned_by=assigned_by,
            operator=operator,
            due_date=due_date,
            drive_url=drive_url,
            status="assigned",
            created_on=today,
        ).to_response()

    def mark_posted(self, job_id: str, facebook_url: str) -> dict:
        job = self.get_job(job_id)
        if job is None:
            job = OperationalJob(
                id=job_id,
                property_name=job_id,
                assigned_by="",
                operator="",
                due_date="",
                drive_url="",
                status="assigned",
                created_on=date.today(),
            )
        self.client.table("jobs").upsert(
            {
                "id": job_id,
                "property_name": job.property_name,
                "assigned_by": job.assigned_by,
                "operator": job.operator,
                "due_date": job.due_date or None,
                "drive_url": job.drive_url,
                "status": "posted",
                "created_on": job.created_on.isoformat(),
                "facebook_url": facebook_url,
                "caption": job.caption,
                "caption_details": job.caption_details,
                "caption_document_name": job.caption_document_name,
                "images": job.images,
                "variants": job.variants,
                "violations": job.violations,
                "requires_manual_review": job.requires_manual_review,
            }
        ).execute()
        job.status = "posted"
        job.facebook_url = facebook_url
        return job.to_response()
    def get_job(self, job_id: str) -> OperationalJob | None:
        rows = (
            self.client.table("jobs").select("*").eq("id", job_id).limit(1).execute()
        )
        if not rows.data:
            return None
        r = rows.data[0]
        return self._row_to_job(r)

    def update_status(self, job_id: str, status: str) -> dict:
        self.client.table("jobs").update({"status": status}).eq(
            "id", job_id
        ).execute()
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        return job.to_response()

    def set_prepared(self, job_id: str, prepared_data: dict) -> dict:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(job_id)
        update = {
            "caption": prepared_data.get("caption", ""),
            "caption_details": prepared_data.get("caption_details", ""),
            "caption_document_name": prepared_data.get("caption_document_name", ""),
            "images": prepared_data.get("images", []),
            "variants": prepared_data.get("variants", []),
            "violations": prepared_data.get("violations", []),
            "requires_manual_review": prepared_data.get("requires_manual_review", False),
        }
        if update["caption"]:
            update["status"] = "ready_to_post"
        self.client.table("jobs").update(update).eq("id", job_id).execute()
        job = self.get_job(job_id)
        return job.to_response() if job else update

    def add_activity(self, job_id: str, entry: dict) -> None:
        self.client.table("job_activity").insert(
            {
                "job_id": job_id,
                "at": entry.get("at", ""),
                "text": entry.get("text", ""),
            }
        ).execute()

    def get_activity(self, job_id: str) -> list[dict]:
        rows = (
            self.client.table("job_activity")
            .select("at,text")
            .eq("job_id", job_id)
            .order("id")
            .execute()
        )
        return [
            {"at": r.get("at", ""), "text": r.get("text", "")}
            for r in (rows.data or [])
        ]

    def _row_to_job(self, r: dict) -> OperationalJob:
        import json
        from datetime import date as dt_date

        co = r.get("created_on")
        if isinstance(co, str):
            parts = co.split("-")
            co = dt_date(int(parts[0]), int(parts[1]), int(parts[2]))

        def _list(v):
            if isinstance(v, list):
                return v
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return []

        return OperationalJob(
            id=r.get("id", ""),
            property_name=r.get("property_name", ""),
            assigned_by=r.get("assigned_by", ""),
            operator=r.get("operator", ""),
            due_date=r.get("due_date", "") or "",
            drive_url=r.get("drive_url", ""),
            status=r.get("status", "assigned"),
            created_on=co or dt_date.today(),
            facebook_url=r.get("facebook_url", ""),
            caption=r.get("caption", ""),
            caption_details=r.get("caption_details", ""),
            caption_document_name=r.get("caption_document_name", ""),
            images=_list(r.get("images", [])),
            variants=_list(r.get("variants", [])),
            violations=_list(r.get("violations", [])),
            requires_manual_review=r.get("requires_manual_review", False),
        )

    def _row_to_response(self, r: dict) -> dict:
        job = self._row_to_job(r)
        return job.to_response()
