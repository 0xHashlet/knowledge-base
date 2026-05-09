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
        embedding_model: str | None = None,
    ) -> tuple[DocumentVersion, list[DocumentChunk]]:
        chunks = [
            DocumentChunk(
                knowledge_base_id=version.knowledge_base_id,
                document_id=version.document_id,
                document_version_id=version.id,
                chunk_index=index,
                content=content,
                content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
                token_count=len(content.split()),
                embedding_model=embedding_model,
                metadata_={},
                acl_snapshot={"knowledge_base_id": str(version.knowledge_base_id)},
                is_active=True,
            )
            for index, content in enumerate(self._split_text(text))
        ]
        self.repository.replace_chunks_for_version(version, chunks)
        updated_version = self.repository.mark_version_parsed(
            version, text, parser_name, parser_version
        )
        return updated_version, chunks

    def _split_text(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []
        # 先按段落分，再对超长段落按字符数切分
        paragraphs = [p.strip() for p in normalized.split("\n") if p.strip()]
        chunks: list[str] = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                chunks.append(para)
            else:
                for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                    chunks.append(para[i : i + self.chunk_size])
        return chunks
