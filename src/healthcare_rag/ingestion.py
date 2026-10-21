"""Read curated local documents and preserve exact page substrings."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    page: int
    chunk_index: int


def load_pages(path: Path) -> Iterator[tuple[int, str]]:
    """Yield one-based pages; text files may contain form-feed separators."""
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        for number, page in enumerate(PdfReader(str(path)).pages, 1):
            yield number, page.extract_text() or ""
    elif path.suffix.lower() in {".txt", ".md"}:
        yield from enumerate(path.read_text(encoding="utf-8").split("\f"), 1)


def chunk_text(text: str, source: str, page: int = 1,
               chunk_size: int = 800, overlap: int = 150) -> list[Chunk]:
    """Slice exact text with overlap; indices are zero-based within each page."""
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require chunk_size > 0 and 0 <= overlap < chunk_size")
    chunks = []
    start = 0
    while start < len(text):
        excerpt = text[start:start + chunk_size]
        if excerpt.strip():
            index = len(chunks)
            identity = f"{source}\0{page}\0{index}\0{excerpt}"
            chunks.append(Chunk(sha256(identity.encode()).hexdigest(), excerpt,
                                source, page, index))
        if start + chunk_size >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def ingest_directory(data_dir: str | Path, chunk_size: int = 800,
                     overlap: int = 150) -> list[Chunk]:
    """Read supported files recursively; source is relative to the corpus root."""
    root = Path(data_dir)
    if not root.is_dir():
        raise ValueError(f"Not a document directory: {root}")
    chunks = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf"}:
            for page, text in load_pages(path):
                chunks.extend(chunk_text(text, path.relative_to(root).as_posix(),
                                         page, chunk_size, overlap))
    return chunks
