from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(slots=True)
class OperationalJob:
    id: str
    property_name: str
    assigned_by: str
    operator: str
    due_date: str
    drive_url: str
    status: str
    created_on: date
    facebook_url: str = ""
    offering_id: str = ""          # canonical offerings.id (uuid); "" if unbound
    caption: str = ""
    caption_details: str = ""
    caption_document_name: str = ""
    images: list = field(default_factory=list)
    variants: list = field(default_factory=list)
    violations: list = field(default_factory=list)
    requires_manual_review: bool = False
    activity: list = field(default_factory=list)

    def to_response(self) -> dict[str, str]:
        payload = {
            "id": self.id,
            "property_name": self.property_name,
            "assigned_by": self.assigned_by,
            "operator": self.operator,
            "due_date": self.due_date,
            "drive_url": self.drive_url,
            "status": self.status,
        }
        if self.facebook_url:
            payload["facebook_url"] = self.facebook_url
        if self.offering_id:
            payload["offering_id"] = self.offering_id
        if self.caption:
            payload["caption"] = self.caption
        if self.caption_details:
            payload["caption_details"] = self.caption_details
        if self.caption_document_name:
            payload["caption_document_name"] = self.caption_document_name
        if self.images:
            payload["images"] = self.images
        if self.variants:
            payload["variants"] = self.variants
        if self.violations:
            payload["violations"] = self.violations
        if self.requires_manual_review:
            payload["requires_manual_review"] = self.requires_manual_review
        return payload


class InMemoryJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, OperationalJob] = {}
        self._sequence = 0

    def list_jobs(self) -> list[dict[str, str]]:
        return [job.to_response() for job in self._jobs.values()]

    def counts(self) -> dict[str, int]:
        return {
            "assigned_today": sum(
                job.status == "assigned" and job.created_on == date.today()
                for job in self._jobs.values()
            ),
            "waiting_approval": sum(
                job.status == "waiting_approval" for job in self._jobs.values()
            ),
            "ready_to_post": sum(
                job.status == "ready_to_post" for job in self._jobs.values()
            ),
            "posted_today": sum(
                job.status == "posted" and job.created_on == date.today()
                for job in self._jobs.values()
            ),
        }

    def create(
        self,
        *,
        property_name: str,
        assigned_by: str,
        operator: str,
        due_date: str,
        drive_url: str,
        offering_id: str = "",
    ) -> dict[str, str]:
        self._sequence += 1
        job_id = f"APG-{date.today():%m%d}-{self._sequence:03d}"
        job = OperationalJob(
            id=job_id,
                        property_name=property_name,
            offering_id=offering_id,
            assigned_by=assigned_by,
            operator=operator,
            due_date=due_date,
            drive_url=drive_url,
            status="assigned",
            created_on=date.today(),
        )
        self._jobs[job_id] = job
        return job.to_response()

    def mark_posted(self, job_id: str, facebook_url: str) -> dict[str, str]:
        job = self._jobs.get(job_id)
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
            self._jobs[job_id] = job
        job.status = "posted"
        job.facebook_url = facebook_url
        return job.to_response()

    def get_job(self, job_id: str) -> OperationalJob | None:
        return self._jobs.get(job_id)

    def update_status(self, job_id: str, status: str) -> dict[str, str]:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.status = status
        return job.to_response()

    def set_prepared(self, job_id: str, prepared_data: dict) -> dict[str, str]:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.caption = prepared_data.get("caption", "")
        job.caption_details = prepared_data.get("caption_details", "")
        job.caption_document_name = prepared_data.get("caption_document_name", "")
        job.images = prepared_data.get("images", [])
        job.variants = prepared_data.get("variants", [])
        job.violations = prepared_data.get("violations", [])
        job.requires_manual_review = prepared_data.get("requires_manual_review", False)
        return job.to_response()

    def add_activity(self, job_id: str, entry: dict) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job.activity.append(entry)

    def get_activity(self, job_id: str) -> list[dict]:
        job = self._jobs.get(job_id)
        if job is None:
            return []
        return list(job.activity)
