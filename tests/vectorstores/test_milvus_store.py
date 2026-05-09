import uuid

from app.vectorstores.base import EmbeddingRecord
from app.vectorstores.milvus import MilvusEmbeddingStore


class FakeMilvusClient:
    def __init__(self, uri: str, token: str | None = None):
        self.uri = uri
        self.token = token
        self.created_collections = []
        self.indexes = []
        self.loaded = []
        self.upsert_calls = []
        self.delete_calls = []
        self.search_calls = []

    def has_collection(self, collection_name: str) -> bool:
        return False

    def prepare_index_params(self):
        return FakeIndexParams()

    def create_collection(self, collection_name: str, schema, index_params):
        self.created_collections.append(
            {
                "collection_name": collection_name,
                "schema": schema,
                "index_params": index_params,
            }
        )

    def create_index(self, collection_name: str, index_params):
        self.indexes.append((collection_name, index_params))

    def load_collection(self, collection_name: str):
        self.loaded.append(collection_name)

    def upsert(self, collection_name: str, data: list[dict]):
        self.upsert_calls.append((collection_name, data))

    def delete(self, collection_name: str, filter: str):
        self.delete_calls.append((collection_name, filter))

    def search(self, collection_name: str, data: list[list[float]], limit: int, filter: str | None):
        self.search_calls.append(
            {
                "collection_name": collection_name,
                "data": data,
                "limit": limit,
                "filter": filter,
            }
        )
        return [[{"id": "chunk-1", "distance": 0.1, "entity": {"chunk_id": "chunk-1"}}]]


class FakeIndexParams:
    def __init__(self):
        self.indexes = []

    def add_index(self, **kwargs):
        self.indexes.append(kwargs)


def test_milvus_store_initializes_collection():
    store = MilvusEmbeddingStore(
        uri="http://milvus:19530",
        token=None,
        collection_name="enterprise_rag_chunks",
        dimension=1536,
        client_factory=FakeMilvusClient,
    )

    store.ensure_collection()

    created_collection = store.client.created_collections[0]
    assert created_collection["collection_name"] == "enterprise_rag_chunks"
    assert created_collection["index_params"].indexes == [
        {"field_name": "vector", "index_type": "AUTOINDEX", "metric_type": "COSINE"}
    ]
    assert store.client.loaded == ["enterprise_rag_chunks"]


def test_milvus_store_upserts_chunk_vectors():
    store = MilvusEmbeddingStore(
        uri="http://milvus:19530",
        token="token",
        collection_name="enterprise_rag_chunks",
        dimension=3,
        client_factory=FakeMilvusClient,
    )
    record = EmbeddingRecord(
        chunk_id=uuid.uuid4(),
        knowledge_base_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_version_id=uuid.uuid4(),
        embedding_model="text-embedding-3-small",
        vector=[0.1, 0.2, 0.3],
    )

    store.upsert([record])

    collection_name, rows = store.client.upsert_calls[0]
    assert collection_name == "enterprise_rag_chunks"
    assert rows[0]["id"] == str(record.chunk_id)
    assert rows[0]["chunk_id"] == str(record.chunk_id)
    assert rows[0]["vector"] == [0.1, 0.2, 0.3]


def test_milvus_store_delete_and_search_use_chunk_metadata_filters():
    store = MilvusEmbeddingStore(
        uri="http://milvus:19530",
        token=None,
        collection_name="enterprise_rag_chunks",
        dimension=3,
        client_factory=FakeMilvusClient,
    )
    chunk_id = uuid.uuid4()
    knowledge_base_id = uuid.uuid4()

    store.delete_by_chunk_ids([chunk_id])
    results = store.search([0.1, 0.2, 0.3], limit=5, knowledge_base_id=knowledge_base_id)

    assert store.client.delete_calls == [
        ("enterprise_rag_chunks", f'chunk_id in ["{chunk_id}"]')
    ]
    assert store.client.search_calls[0]["filter"] == f'knowledge_base_id == "{knowledge_base_id}"'
    assert results[0].chunk_id == "chunk-1"
    assert results[0].score == 0.1
