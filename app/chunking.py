import re

import frontmatter

from app.config import CHUNK_OVERLAP_CHARS, MAX_CHUNK_CHARS

HEADING_RE = re.compile(r"^##\s+(.*)$", re.MULTILINE)


def parse_document(path):
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def split_into_sections(body):
    """Split markdown body into (heading, text) sections on '## ' headings."""
    matches = list(HEADING_RE.finditer(body))
    sections = []

    intro_end = matches[0].start() if matches else len(body)
    intro = body[:intro_end].strip()
    if intro:
        sections.append(("개요", intro))

    for i, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        text = body[start:end].strip()
        if text:
            sections.append((heading, text))

    return sections


def split_long_text(text, max_chars=MAX_CHUNK_CHARS, overlap=CHUNK_OVERLAP_CHARS):
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    pieces = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) + 2 > max_chars:
            pieces.append(current)
            tail = current[-overlap:] if overlap < len(current) else current
            current = tail + "\n\n" + para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        pieces.append(current)

    return pieces


def build_chunks(relative_path, metadata, body):
    """Return a list of {id, text, metadata} chunk records for one document."""
    chunks = []
    sections = split_into_sections(body)
    chunk_index = 0

    for heading, section_text in sections:
        for piece in split_long_text(section_text):
            chunk_id = f"{relative_path}#{chunk_index}"
            self_describing_text = f"[{heading}]\n{piece}"
            chunk_metadata = {
                **metadata,
                "source_path": relative_path,
                "heading": heading,
                "chunk_index": chunk_index,
            }
            chunks.append({
                "id": chunk_id,
                "text": self_describing_text,
                "metadata": chunk_metadata,
            })
            chunk_index += 1

    return chunks
