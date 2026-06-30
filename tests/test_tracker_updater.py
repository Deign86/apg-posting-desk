from datetime import datetime, timezone

from apg_automation.tracker_updater import TrackerUpdater


class FakeSheetsClient:
    def __init__(self):
        self.rows = []

    def append_row(self, spreadsheet_id, values):
        self.rows.append((spreadsheet_id, values))


class FakeDocsClient:
    def __init__(self):
        self.entries = []

    def append_text(self, document_id, text):
        self.entries.append((document_id, text))


def test_tracker_updater_appends_sheet_row_and_daily_report_entry():
    sheets = FakeSheetsClient()
    docs = FakeDocsClient()
    updater = TrackerUpdater(
        sheets_client=sheets,
        docs_client=docs,
        posting_tracker_sheet_id="sheet-1",
        daily_report_doc_id="doc-1",
        posted_by="APG Automation",
    )
    posted_at = datetime(2026, 6, 29, 9, 30, tzinfo=timezone.utc)

    updater.record_success("Sample Property", "https://facebook.com/post", posted_at)

    assert sheets.rows == [
        (
            "sheet-1",
            [
                "2026-06-29",
                "Sample Property",
                "https://facebook.com/post",
                "Posted",
                "APG Automation",
            ],
        )
    ]
    assert docs.entries == [
        (
            "doc-1",
            "\n• Sample Property - Posted at 09:30\n  Link: https://facebook.com/post",
        )
    ]
