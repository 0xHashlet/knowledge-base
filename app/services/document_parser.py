from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    parser_name: str
    parser_version: str


class DocumentParser:
    parser_version = "1"

    def parse(self, *, file_type: str, content: bytes) -> ParsedDocument:
        if file_type == "text/plain":
            return ParsedDocument(
                text=content.decode("utf-8"),
                parser_name="plain_text",
                parser_version=self.parser_version,
            )
        if file_type == "application/pdf":
            return self._parse_pdf(content)
        raise ValueError(f"Unsupported document file type: {file_type}")

    def _parse_pdf(self, content: bytes) -> ParsedDocument:
        import fitz

        with fitz.open(stream=content, filetype="pdf") as pdf:
            text = "\n".join(page.get_text() for page in pdf)
        return ParsedDocument(text=text, parser_name="pymupdf", parser_version=self.parser_version)
