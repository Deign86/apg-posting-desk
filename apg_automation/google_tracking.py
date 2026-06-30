from __future__ import annotations


class GoogleSheetsClient:
    def __init__(self, *, service, range_name: str = "A:E") -> None:
        self.service = service
        self.range_name = range_name

    def append_row(self, spreadsheet_id: str, values: list[str]) -> None:
        (
            self.service.spreadsheets()
            .values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=self.range_name,
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [values]},
            )
            .execute()
        )


class GoogleDocsClient:
    def __init__(self, *, service) -> None:
        self.service = service

    def append_text(self, document_id: str, text: str) -> None:
        document = self.service.documents().get(documentId=document_id).execute()
        end_index = document["body"]["content"][-1]["endIndex"] - 1
        (
            self.service.documents()
            .batchUpdate(
                documentId=document_id,
                body={
                    "requests": [
                        {
                            "insertText": {
                                "location": {"index": end_index},
                                "text": text,
                            }
                        }
                    ]
                },
            )
            .execute()
        )


def build_sheets_service():
    from googleapiclient.discovery import build

    from .google_auth import build_google_credentials

    return build("sheets", "v4", credentials=build_google_credentials())


def build_docs_service():
    from googleapiclient.discovery import build

    from .google_auth import build_google_credentials

    return build("docs", "v1", credentials=build_google_credentials())
