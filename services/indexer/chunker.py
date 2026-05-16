"""Code chunking with AST-aware parsing."""

import hashlib
from pathlib import Path
from typing import Optional, Generator
import logging

from .models import ChunkMetadata

logger = logging.getLogger(__name__)

# Token estimation: rough average of 1.3 characters per token
CHARS_PER_TOKEN = 1.3
TARGET_CHUNK_SIZE = 512  # tokens
TARGET_CHUNK_CHARS = int(TARGET_CHUNK_SIZE * CHARS_PER_TOKEN)  # ~666 chars
OVERLAP_SIZE = 64  # tokens for context overlap
OVERLAP_CHARS = int(OVERLAP_SIZE * CHARS_PER_TOKEN)  # ~83 chars


class ChunkingError(Exception):
    """Base exception for chunking operations."""

    pass


def _hash_deterministic_id(file_path: str, start_line: int) -> int:
    """
    Generate deterministic chunk ID from file path and line number.

    Uses hash to create a 63-bit unsigned integer for deduplication.
    Same file_path + start_line always produces same ID.

    Args:
        file_path: Path to source file.
        start_line: Starting line number (1-indexed).

    Returns:
        Deterministic ID as 63-bit unsigned integer.
    """
    key = f"{file_path}:{start_line}".encode()
    hash_bytes = hashlib.md5(key).digest()
    # Convert first 8 bytes to 63-bit integer (avoid sign bit)
    hash_int = int.from_bytes(hash_bytes[:8], byteorder="big") & 0x7FFFFFFFFFFFFFFF
    return hash_int


def _try_parse_python(content: str) -> Optional[list[tuple[int, int, str]]]:
    """
    Attempt to parse Python code and extract semantic chunks.

    Tries to import tree-sitter; if unavailable, returns None.

    Args:
        content: Python source code.

    Returns:
        List of (start_line, end_line, text) tuples, or None if parsing fails.
    """
    try:
        import tree_sitter as ts  # type: ignore[import-not-found]
        from tree_sitter import Language, Parser
    except ImportError:
        logger.debug("tree-sitter not available; falling back to token-window chunking")
        return None

    try:
        # Note: This requires tree-sitter-python to be installed
        # For production, ensure: pip install tree-sitter tree-sitter-python
        language = Language("build/my-languages.so", "python")  # type: ignore[call-overload]
        parser = Parser()
        parser.set_language(language)  # type: ignore[attr-defined]

        tree = parser.parse(content.encode())
        root = tree.root_node

        chunks = []
        lines = content.split("\n")

        # Extract top-level definitions (classes, functions, async functions)
        for child in root.children:
            if child.type in (
                "class_definition",
                "function_definition",
                "async_function_definition",
            ):
                start_line = child.start_point[0] + 1  # Convert to 1-indexed
                end_line = child.end_point[0] + 1
                chunk_text = "\n".join(lines[child.start_point[0] : child.end_point[0]])
                chunks.append((start_line, end_line, chunk_text))

        return chunks if chunks else None

    except Exception as e:
        logger.debug(f"Python AST parsing failed: {e}; falling back to token-window chunking")
        return None


def chunk_file(
    file_path: Path, language: str, content: str
) -> Generator[ChunkMetadata, None, None]:
    """
    Chunk a source file into semantic pieces.

    For Python files, attempts AST-aware chunking. Falls back to
    token-window splitting for all languages.

    Args:
        file_path: Path to source file.
        language: Programming language (e.g., 'python', 'javascript').
        content: File contents.

    Yields:
        ChunkMetadata objects for each chunk.

    Raises:
        ChunkingError: If chunking fails unexpectedly.
    """
    try:
        chunks_to_yield = []

        # Try AST-based chunking for Python
        if language == "python":
            ast_chunks = _try_parse_python(content)
            if ast_chunks:
                for start_line, end_line, chunk_text in ast_chunks:
                    if len(chunk_text.strip()) > 0:
                        deterministic_id = _hash_deterministic_id(str(file_path), start_line)
                        chunks_to_yield.append((start_line, end_line, chunk_text, deterministic_id))

        # Fall back to token-window chunking if AST parsing didn't work
        if not chunks_to_yield:
            chunks_to_yield = _chunk_by_token_window(file_path, content)

        # Yield chunks
        for start_line, end_line, chunk_text, deterministic_id in chunks_to_yield:
            yield ChunkMetadata(
                file_path=str(file_path),
                language=language,
                start_line=start_line,
                end_line=end_line,
                chunk_text=chunk_text,
                deterministic_id=deterministic_id,
            )

    except ChunkingError:
        raise
    except Exception as e:
        raise ChunkingError(f"Chunking failed for {file_path}: {str(e)}") from e


def _chunk_by_token_window(
    file_path: Path,
    content: str,
    chunk_size_chars: int = TARGET_CHUNK_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
) -> list[tuple[int, int, str, int]]:
    """
    Split file into overlapping token-window chunks.

    Respects line boundaries and attempts to avoid splitting mid-token.

    Args:
        file_path: Path to source file.
        content: File contents.
        chunk_size_chars: Target chunk size in characters (~tokens).
        overlap_chars: Overlap between chunks in characters.

    Returns:
        List of (start_line, end_line, chunk_text, deterministic_id) tuples.
    """
    lines = content.split("\n")
    chunks = []
    line_idx = 0

    while line_idx < len(lines):
        # Find chunk boundaries by lines
        chunk_lines: list[str] = []
        chunk_chars = 0

        start_idx = line_idx

        # Accumulate lines until we hit chunk_size
        while line_idx < len(lines):
            line = lines[line_idx]
            if chunk_chars + len(line) + 1 > chunk_size_chars and chunk_lines:
                # Would exceed limit; stop here
                break
            chunk_lines.append(line)
            chunk_chars += len(line) + 1  # +1 for newline
            line_idx += 1

        if not chunk_lines:
            # Single line is too long; include it anyway
            chunk_lines.append(lines[line_idx])
            line_idx += 1

        chunk_text = "\n".join(chunk_lines)
        if chunk_text.strip():  # Skip empty chunks
            start_line = start_idx + 1  # Convert to 1-indexed
            end_line = line_idx
            deterministic_id = _hash_deterministic_id(str(file_path), start_line)
            chunks.append((start_line, end_line, chunk_text, deterministic_id))

        # Back up by overlap for next chunk
        line_idx = max(start_idx + 1, line_idx - max(1, int(overlap_chars / CHARS_PER_TOKEN)))

    return chunks


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text using character-based heuristic.

    Args:
        text: Input text.

    Returns:
        Approximate token count.
    """
    return max(1, int(len(text) / CHARS_PER_TOKEN))
