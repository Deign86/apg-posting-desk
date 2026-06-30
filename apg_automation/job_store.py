from __future__ import annotations

from dataclasses import dataclass
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
    ) -> dict[str, str]:
        self._sequence += 1
        job_id = f"APG-{date.today():%m%d}-{self._sequence:03d}"
        job = OperationalJob(
            id=job_id,
            property_name=property_name,
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
