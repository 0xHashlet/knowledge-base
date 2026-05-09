import hashlib

from app.models.chunk import DocumentChunk
from app.models.document import DocumentVersion


class ChunkService:
    def __init__(self, repository, *, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.repository = repository
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def store_parsed_text(
        self,
        version: DocumentVersion,
        *,
        text: str,
        parser_name: str,
        parser_version: str,
    ) -> DocumentVersion:
        chunks = [
            DocumentChunk(
                knowledge_base_id=version.knowledge_base_id,
                document_id=version.document_id,
                document_version_id=version.id,
                chunk_index=index,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                token_count=len(content.split()),
                embedding_model=None,
                metadata_={},
                acl_snapshot={"knowledge_base_id": str(version.knowledge_base_id)},
                is_active=True,
            )
            for index, content in enumerate(self._split_text(text))
        ]
        self.repository.replace_chunks_for_version(version, chunks)
        return self.repository.mark_version_parsed(version, text, parser_name, parser_version)

    def _split_text(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        chunks: list[str] = []
        current_words: list[str] = []
        current_size = 0
        for word in normalized.split():
            next_size = len(word) if not current_words else current_size + 1 + len(word)
            if current_words and next_size > self.chunk_size:
                chunks.append(" ".join(current_words))
                current_words = [word]
                current_size = len(word)
            else:
                current_words.append(word)
                current_size = next_size
        if current_words:
            chunks.append(" ".join(current_words))
        return chunks
