from datetime import datetime, timezone

from apg_automation.google_workspace_mcp import GoogleWorkspaceMcpGateway


class FakeMcpClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def call_tool(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return self.responses.pop(0)


def test_mcp_gateway_fetches_property_assets_and_caption_details():
    client = FakeMcpClient(
        [
            {"files": [{"id": "folder-1", "name": "Novaliches, 440 Bagbag"}]},
            {
                "files": [
                    {"id": "img-1", "name": "2.png", "mimeType": "image/png"},
                    {"id": "img-2", "name": "3.png", "mimeType": "image/png"},
                    {"id": "img-3", "name": "4.png", "mimeType": "image/png"},
                    {
                        "id": "doc-1",
                        "name": "Untitled doc",
                        "mimeType": "application/vnd.google-apps.document",
                    },
                ]
            },
            {"content": "image-1"},
            {"content": "image-2"},
            {"content": "image-3"},
            {"text": "Caption details from Google Doc."},
        ]
    )
    gateway = GoogleWorkspaceMcpGateway(
        mcp_client=client,
        listings_folder_id="listing-root",
    )

    bundle = gateway.fetch_property_bundle("Novaliches, 440 Bagbag")

    assert bundle.property_name == "Novaliches, 440 Bagbag"
    assert bundle.caption_details == "Caption details from Google Doc."
    assert [asset.name for asset in bundle.images] == ["2.png", "3.png", "4.png"]
    assert client.calls == [
        (
            "search_files",
            {
                "query": "name = 'Novaliches, 440 Bagbag'",
                "parentId": "listing-root",
                "mimeType": "application/vnd.google-apps.folder",
            },
        ),
        ("search_files", {"parentId": "folder-1"}),
        ("download_file_content", {"fileId": "img-1"}),
        ("download_file_content", {"fileId": "img-2"}),
        ("download_file_content", {"fileId": "img-3"}),
        ("readDocument", {"documentId": "doc-1", "format": "text"}),
    ]


def test_mcp_gateway_logs_tracker_and_daily_report():
    client = FakeMcpClient([{"updatedRows": 1}, {"ok": True}])
    gateway = GoogleWorkspaceMcpGateway(
        mcp_client=client,
        listings_folder_id="listing-root",
        posting_tracker_sheet_id="sheet-1",
        daily_report_doc_id="doc-2",
    )
    posted_at = datetime(2026, 6, 29, 9, 30, tzinfo=timezone.utc)

    gateway.log_success(
        property_name="Novaliches, 440 Bagbag",
        post_url="https://facebook.com/post",
        posted_at=posted_at,
    )

    assert client.calls == [
        (
            "appendRows",
            {
                "spreadsheetId": "sheet-1",
                "range": "A:C",
                "values": [
                    [
                        "Novaliches, 440 Bagbag",
                        "2026-06-29",
                        "https://facebook.com/post",
                    ]
                ],
            },
        ),
        (
            "appendText",
            {
                "documentId": "doc-2",
                "text": "\n• Novaliches, 440 Bagbag - Posted at 09:30\n  Link: https://facebook.com/post",
            },
        ),
    ]
