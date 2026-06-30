from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


class McpToolClient(Protocol):
    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        raise NotImplementedError


@dataclass(frozen=True)
class WorkspaceAsset:
    id: str
    name: str
    mime_type: str
    content: str | bytes


@dataclass(frozen=True)
class WorkspacePropertyBundle:
    property_id: str
    property_name: str
    images: list[WorkspaceAsset]
    caption_details: str


class GoogleWorkspaceMcpGateway:
    def __init__(
        self,
        *,
        mcp_client: McpToolClient,
        listings_folder_id: str,
        posting_tracker_sheet_id: str = "",
        daily_report_doc_id: str = "",
        min_images: int = 3,
    ) -> None:
        self.mcp_client = mcp_client
        self.listings_folder_id = listings_folder_id
        self.posting_tracker_sheet_id = posting_tracker_sheet_id
        self.daily_report_doc_id = daily_report_doc_id
        self.min_images = min_images

    def fetch_property_bundle(self, property_name: str) -> WorkspacePropertyBundle:
        folder = self._find_property_folder(property_name)
        files = self._list_folder(folder["id"])
        image_files = [
            file_info
            for file_info in files
            if file_info.get("mimeType", "").startswith("image/")
        ][: self.min_images]
        document = self._first_caption_document(files)

        if len(image_files) < self.min_images:
            raise ValueError("Insufficient images")
        if document is None:
            raise ValueError("Missing caption document")

        images = [
            WorkspaceAsset(
                id=file_info["id"],
                name=file_info["name"],
                mime_type=file_info.get("mimeType", ""),
                content=self.mcp_client.call_tool(
                    "download_file_content",
                    {"fileId": file_info["id"]},
                ).get("content", ""),
            )
            for file_info in image_files
        ]
        caption_details = self.mcp_client.call_tool(
            "readDocument",
            {"documentId": document["id"], "format": "text"},
        ).get("text", "")

        return WorkspacePropertyBundle(
            property_id=folder["id"],
            property_name=property_name,
            images=images,
            caption_details=caption_details,
        )

    def log_success(
        self,
        *,
        property_name: str,
        post_url: str,
        posted_at: datetime,
    ) -> None:
        self.mcp_client.call_tool(
            "appendRows",
            {
                "spreadsheetId": self.posting_tracker_sheet_id,
                "range": "A:C",
                "values": [
                    [
                        property_name,
                        posted_at.strftime("%Y-%m-%d"),
                        post_url,
                    ]
                ],
            },
        )
        self.mcp_client.call_tool(
            "appendText",
            {
                "documentId": self.daily_report_doc_id,
                "text": (
                    f"\n• {property_name} - Posted at {posted_at.strftime('%H:%M')}"
                    f"\n  Link: {post_url}"
                ),
            },
        )

    def _find_property_folder(self, property_name: str) -> dict:
        result = self.mcp_client.call_tool(
            "search_files",
            {
                "query": f"name = '{property_name}'",
                "parentId": self.listings_folder_id,
                "mimeType": "application/vnd.google-apps.folder",
            },
        )
        files = result.get("files", [])
        if not files:
            raise ValueError("Property not found")
        return files[0]

    def _list_folder(self, folder_id: str) -> list[dict]:
        result = self.mcp_client.call_tool("search_files", {"parentId": folder_id})
        return result.get("files", [])

    def _first_caption_document(self, files: list[dict]) -> dict | None:
        for file_info in files:
            mime_type = file_info.get("mimeType", "")
            name = file_info.get("name", "").lower()
            if mime_type == "application/vnd.google-apps.document":
                return file_info
            if "caption" in name and mime_type in {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/pdf",
                "text/plain",
            }:
                return file_info
        return None
