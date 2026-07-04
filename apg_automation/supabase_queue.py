from __future__ import annotations

from apg_automation.models import PropertyQueueItem


class SupabasePropertyQueue:
    def __init__(self, client, *, rpc_name: str = "claim_next_queue_item") -> None:
        self.client = client
        self.rpc_name = rpc_name

    def claim_next(self, *, operator_uid: str) -> PropertyQueueItem | None:
        result = self.client.rpc(self.rpc_name, {"p_operator": operator_uid}).execute()
        data = result.data if result else None
        if not data:
            return None
        return PropertyQueueItem(
            id=data.get("id", ""), property_name=data.get("property_name", "")
        )
