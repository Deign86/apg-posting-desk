from apg_automation.firebase_queue import FirestorePropertyQueue


class FakeDocument:
    def __init__(self, doc_id, payload):
        self.id = doc_id
        self._payload = payload
        self.updates = []

    def to_dict(self):
        return self._payload

    @property
    def reference(self):
        return self

    def update(self, payload):
        self.updates.append(payload)


class FakeQuery:
    def __init__(self, docs):
        self.docs = docs

    def where(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def stream(self):
        return iter(self.docs)


class FakeFirestoreClient:
    def __init__(self, docs):
        self.docs = docs

    def collection(self, name):
        assert name == "property_queue"
        return FakeQuery(self.docs)


def test_firestore_queue_returns_next_pending_property_and_marks_processing():
    doc = FakeDocument(
        "queue-1",
        {"property_name": "Novaliches, 440 Bagbag", "status": "pending"},
    )
    queue = FirestorePropertyQueue(FakeFirestoreClient([doc]))

    item = queue.claim_next(operator_uid="user-1")

    assert item.id == "queue-1"
    assert item.property_name == "Novaliches, 440 Bagbag"
    assert doc.updates == [{"status": "processing", "claimed_by": "user-1"}]
