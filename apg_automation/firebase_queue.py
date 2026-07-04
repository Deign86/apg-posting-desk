from __future__ import annotations

from .models import PropertyQueueItem


class FirestorePropertyQueue:
    def __init__(self, firestore_client, *, collection_name: str = "property_queue") -> None:
        self.firestore_client = firestore_client
        self.collection_name = collection_name

    def claim_next(self, *, operator_uid: str) -> PropertyQueueItem | None:
        docs = (
            self.firestore_client.collection(self.collection_name)
            .where("status", "==", "pending")
            .order_by("assigned_at")
            .limit(1)
            .stream()
        )
        for doc in docs:
            payload = doc.to_dict()
            doc.reference.update({"status": "processing", "claimed_by": operator_uid})
            return PropertyQueueItem(id=doc.id, property_name=payload["property_name"])
        return None


def build_firestore_client():
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.ApplicationDefault())
    return firestore.client()
