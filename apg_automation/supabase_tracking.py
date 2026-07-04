from __future__ import annotations

from datetime import datetime


class SupabaseTracker:
    def __init__(self, client, *, posted_by: str = "APG Automation") -> None:
        self.client = client
        self.posted_by = posted_by

    def record_success(self, property_name: str, post_url: str, posted_at: datetime) -> None:
        self.client.table("posted_log").insert(
            {
                "posted_on": posted_at.strftime("%Y-%m-%d"),
                "property_name": property_name,
                "post_url": post_url,
                "status": "Posted",
                "posted_by": self.posted_by,
                "posted_at": posted_at.isoformat(),
            }
        ).execute()
