from __future__ import annotations

from datetime import datetime
from typing import Protocol


class SheetsClient(Protocol):
    def append_row(self, spreadsheet_id: str, values: list[str]) -> None:
        raise NotImplementedError


class DocsClient(Protocol):
    def append_text(self, document_id: str, text: str) -> None:
        raise NotImplementedError


class TrackerUpdater:
    def __init__(
        self,
        *,
        sheets_client: SheetsClient,
        docs_client: DocsClient,
        posting_tracker_sheet_id: str,
        daily_report_doc_id: str,
        posted_by: str,
    ) -> None:
        self.sheets_client = sheets_client
        self.docs_client = docs_client
        self.posting_tracker_sheet_id = posting_tracker_sheet_id
        self.daily_report_doc_id = daily_report_doc_id
        self.posted_by = posted_by

    def record_success(
        self,
        property_name: str,
        post_url: str,
        posted_at: datetime,
    ) -> None:
        self.sheets_client.append_row(
            self.posting_tracker_sheet_id,
            [
                posted_at.strftime("%Y-%m-%d"),
                property_name,
                post_url,
                "Posted",
                self.posted_by,
            ],
        )
        self.docs_client.append_text(
            self.daily_report_doc_id,
            f"\n• {property_name} - Posted at {posted_at.strftime('%H:%M')}"
            f"\n  Link: {post_url}",
        )
