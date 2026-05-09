import uuid

import pytest

from app.models.chunk import DocumentChunk
from app.models.document import DocumentVersion, DocumentVersionStatus
from app.services.chunk_service import ChunkService
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_parser import DocumentParser


def test_text_parser_decodes_plain_text():
    parser = DocumentParser()

    parsed = parser.parse(file_type="text/plain", content=b"hello\nworld")

    assert parsed.text == "hello\nworld"
    assert parsed.parser_name == "plain_text"


def test_parser_rejects_unsupported_file_type():
    parser = DocumentParser()

    with pytest.raises(ValueError, match="Unsupported document file type"):
        parser.parse(file_type="application/msword", content=b"x")


def test_chunk_service_creates_chunks_and_marks_version_parsed():
    version = DocumentVersion(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        knowledge_base_id=uuid.uuid4(),
        version_number=1,
        file_name="policy.txt",
        file_type="text/plain",
        file_size=12,
        storage_path="objects/policy.txt",
        content_hash="hash",
        uploaded_by_id=uuid.uuid4(),
    )
    written_chunks: list[DocumentChunk] = []

    class FakeRepository:
        def replace_chunks_for_version(self, document_version, chunks):
            written_chunks.extend(chunks)
            return chunks

        def mark_version_parsed(self, document_version, raw_text, parser_name, parser_version):
            document_version.status = DocumentVersionStatus.PARSED
            document_version.raw_text = raw_text
            document_version.parser_name = parser_name
            document_version.parser_version = parser_version
            return document_version

    service = ChunkService(FakeRepository(), chunk_size=5, chunk_overlap=0)

    updated_version, created_chunks = service.store_parsed_text(
        version,
        text="alpha beta gamma",
        parser_name="plain_text",
        parser_version="1",
    )

    assert updated_version.status == DocumentVersionStatus.PARSED
    assert [chunk.chunk_index for chunk in written_chunks] == [0, 1, 2]
    assert all(chunk.knowledge_base_id == version.knowledge_base_id for chunk in written_chunks)
    assert all(chunk.acl_snapshot["knowledge_base_id"] == str(version.knowledge_base_id) for chunk in written_chunks)


def test_document_processing_service_marks_version_failed_on_parse_error():
    version = DocumentVersion(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        knowledge_base_id=uuid.uuid4(),
        version_number=1,
        file_name="policy.doc",
        file_type="application/msword",
        file_size=12,
        storage_path="objects/policy.doc",
        content_hash="hash",
        uploaded_by_id=uuid.uuid4(),
    )

    class FakeRepository:
        def get_version(self, version_id):
            return version

        def mark_version_parsing(self, document_version):
            document_version.status = DocumentVersionStatus.PARSING
            return document_version

        def mark_version_failed(self, document_version, error_message):
            document_version.status = DocumentVersionStatus.FAILED
            document_version.error_message = error_message
            return document_version

    class FakeStorage:
        def get_object(self, *, object_key):
            return b"not supported"

    class FakeChunkService:
        def store_parsed_text(self, *args, **kwargs):
            raise AssertionError("chunking should not run after parser failure")

    service = DocumentProcessingService(
        FakeRepository(),
        FakeStorage(),
        DocumentParser(),
        FakeChunkService(),
    )

    result = service.process_version(version.id)

    assert result == {"document_version_id": str(version.id), "status": "failed"}
    assert version.status == DocumentVersionStatus.FAILED
    assert "Unsupported document file type" in version.error_message
