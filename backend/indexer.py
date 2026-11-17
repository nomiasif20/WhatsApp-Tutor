"""Read curriculum PDFs and teacher uploads into short, citable passages."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

logging.getLogger("pypdf").setLevel(logging.ERROR)

from pypdf import PdfReader

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "by",
    "is", "are", "was", "were", "be", "this", "that", "it", "as", "at", "from",
    "what", "how", "why", "when", "which", "who", "do", "does", "find", "calculate",
    "please", "show", "explain", "my", "me", "i", "we", "you", "your",
}


def infer_grade(name: str) -> int | None:
    match = re.search(r"grade[\s\-]*([789])", name, re.I)
    if match:
        return int(match.group(1))
    return None


def document_kind(name: str) -> str:
    lower = name.lower()
    if "learner" in lower:
        return "Learner book"
    if "navigation" in lower:
        return "Navigation pack"
    if "caps" in lower or "policy" in lower or "curriculum" in lower:
        return "Curriculum policy"
    return "Uploaded material"


def pretty_title(filename: str) -> str:
    name = Path(filename).stem
    name = name.replace("_", " ")
    name = re.sub(r"(\d)\s*-\s*(\d)", r"\1–\2", name)
    name = name.replace("-", " ")
    name = name.replace("–", "-")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def page_chunks(text: str, limit: int = 1400) -> list[str]:
    text = clean_text(text)
    if len(text) < 80:
        return []
    if len(text) <= limit:
        return [text]
    pieces = []
    start = 0
    while start < len(text):
        end = min(len(text), start + limit)
        if end < len(text):
            break_at = text.rfind(" ", start + 400, end)
            if break_at > start:
                end = break_at
        piece = text[start:end].strip()
        if len(piece) >= 80:
            pieces.append(piece)
        if end >= len(text):
            break
        start = max(end - 160, start + 1)
    return pieces


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def extract_pdf(path: Path) -> tuple[int, list[tuple[int, str]]]:
    reader = PdfReader(str(path))
    passages: list[tuple[int, str]] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            raw = page.extract_text() or ""
        except Exception:
            continue
        for chunk in page_chunks(raw):
            passages.append((index, chunk))
    return len(reader.pages), passages


def upsert_document(conn, *, filename: str, stored_path: str, source: str, kind: str,
                    grade: int | None, title: str, pages: int, sha256: str,
                    file_kind: str) -> int:
    row = conn.execute(
        "SELECT id FROM documents WHERE stored_path = ?",
        (stored_path,),
    ).fetchone()
    if row:
        conn.execute("DELETE FROM chunks WHERE document_id = ?", (row["id"],))
        conn.execute(
            """
            UPDATE documents
               SET filename=?, source=?, kind=?, grade=?, title=?, pages=?,
                   sha256=?, file_kind=?, trained_at=datetime('now')
             WHERE id=?
            """,
            (filename, source, kind, grade, title, pages, sha256, file_kind, row["id"]),
        )
        return row["id"]
    cursor = conn.execute(
        """
        INSERT INTO documents
            (filename, stored_path, source, kind, grade, title, pages, sha256, file_kind, trained_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """,
        (filename, stored_path, source, kind, grade, title, pages, sha256, file_kind),
    )
    return cursor.lastrowid


def train_material_folder(conn, folder: Path) -> dict:
    folder = Path(folder)
    trained = 0
    skipped = 0
    pdfs = sorted(path for path in folder.iterdir() if path.suffix.lower() == ".pdf")
    for path in pdfs:
        digest = file_hash(path)
        existing = conn.execute(
            "SELECT id, sha256 FROM documents WHERE stored_path = ?",
            (str(path),),
        ).fetchone()
        if existing and existing["sha256"] == digest:
            count = conn.execute(
                "SELECT COUNT(*) AS n FROM chunks WHERE document_id = ?",
                (existing["id"],),
            ).fetchone()["n"]
            if count:
                skipped += 1
                continue
        pages, passages = extract_pdf(path)
        title = pretty_title(path.name)
        grade = infer_grade(path.name)
        kind = document_kind(path.name)
        document_id = upsert_document(
            conn,
            filename=path.name,
            stored_path=str(path),
            source="material",
            kind=kind,
            grade=grade,
            title=title,
            pages=pages,
            sha256=digest,
            file_kind="pdf",
        )
        conn.executemany(
            "INSERT INTO chunks (document_id, page, grade, text) VALUES (?, ?, ?, ?)",
            [(document_id, page, grade, text) for page, text in passages],
        )
        conn.execute(
            "UPDATE documents SET chunk_count=? WHERE id=?",
            (len(passages), document_id),
        )
        conn.commit()
        trained += 1
        print(f"Trained {path.name}: {pages} pages, {len(passages)} passages")
    return {"trained": trained, "unchanged": skipped, "files": len(pdfs)}


def train_upload(conn, path: Path, *, grade: int | None, description: str, original_name: str) -> dict:
    suffix = path.suffix.lower()
    title = pretty_title(original_name)
    if description.strip():
        title = f"{title}"
    if suffix == ".pdf":
        pages, passages = extract_pdf(path)
        file_kind = "pdf"
    else:
        pages = 1
        file_kind = "image"
        note = clean_text(description)
        passages = [(1, note)] if len(note) >= 10 else []
    if description.strip() and file_kind == "pdf":
        passages.insert(0, (1, clean_text(description)))
    digest = file_hash(path)
    document_id = upsert_document(
        conn,
        filename=original_name,
        stored_path=str(path),
        source="upload",
        kind="Uploaded material",
        grade=grade,
        title=title,
        pages=pages,
        sha256=digest,
        file_kind=file_kind,
    )
    conn.executemany(
        "INSERT INTO chunks (document_id, page, grade, text) VALUES (?, ?, ?, ?)",
        [(document_id, page, grade, text) for page, text in passages],
    )
    conn.execute(
        "UPDATE documents SET chunk_count=? WHERE id=?",
        (len(passages), document_id),
    )
    conn.commit()
    return {"document_id": document_id, "pages": pages, "passages": len(passages)}


class PassageIndex:
    def __init__(self):
        self.passages: list[dict] = []
        self.inverted: dict[str, list[int]] = {}

    def load(self, conn):
        rows = conn.execute(
            """
            SELECT c.id, c.page, c.grade, c.text, d.title, d.kind, d.filename
              FROM chunks c
              JOIN documents d ON d.id = c.document_id
            """
        ).fetchall()
        self.passages = [dict(row) for row in rows]
        inverted: dict[str, list[int]] = {}
        for index, passage in enumerate(self.passages):
            for token in set(tokenize(passage["text"])):
                if len(token) > 3:
                    inverted.setdefault(token, []).append(index)
        self.inverted = inverted

    def search(self, question: str, grade: int | None, keywords: list[str], limit: int = 3) -> list[dict]:
        if not self.passages:
            return []
        tokens = [token for token in tokenize(question) if len(token) > 3]
        candidates: set[int] = set()
        for token in tokens:
            candidates.update(self.inverted.get(token, [])[:400])
        for phrase in keywords:
            for token in tokenize(phrase):
                if len(token) > 3:
                    candidates.update(self.inverted.get(token, [])[:200])
        if not candidates:
            return []
        keyword_text = " ".join(keywords).lower()
        scored = []
        for index in candidates:
            passage = self.passages[index]
            text = passage["text"].lower()
            if "all rights reserved" in text or "covid-19" in text or "social distancing" in text:
                continue
            score = 0.0
            for token in tokens:
                if token in text:
                    score += 2.0 if len(token) > 4 else 1.0
            for phrase in keywords:
                if phrase.lower() in text:
                    score += 3.0
                else:
                    hits = sum(1 for token in tokenize(phrase) if token in text)
                    score += hits * 0.4
            if score <= 0:
                continue
            passage_grade = passage["grade"]
            if grade and passage_grade == grade:
                score *= 1.35
            elif passage_grade is None:
                score *= 1.08
            else:
                score *= 0.6
            if keyword_text and any(word in text for word in keyword_text.split() if len(word) > 4):
                score += 0.5
            scored.append((score, passage))
        scored.sort(key=lambda item: item[0], reverse=True)
        results = []
        seen = set()
        for score, passage in scored:
            key = (passage["title"], passage["page"])
            if key in seen:
                continue
            seen.add(key)
            excerpt = best_excerpt(passage["text"], tokens, keywords)
            if not excerpt:
                continue
            results.append({
                "title": passage["title"],
                "kind": passage["kind"],
                "page": passage["page"],
                "grade": passage["grade"],
                "excerpt": excerpt,
            })
            if len(results) >= limit:
                break
        return results


def readable(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z]{2,}", sentence)
    if len(words) < 8:
        return False
    letters = re.findall(r"[A-Za-z]", sentence)
    if not letters:
        return False
    short = sum(1 for word in re.findall(r"[A-Za-z]+", sentence) if len(word) == 1)
    return short / max(len(words), 1) < 0.25


def best_excerpt(text: str, tokens: list[str], keywords: list[str], limit: int = 380) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    readable_sentences = [sentence for sentence in sentences if readable(sentence)]
    pool = readable_sentences or sentences

    def score(sentence: str) -> float:
        lower = sentence.lower()
        value = 0.0
        for token in tokens:
            if token in lower:
                value += 1
        for phrase in keywords:
            if phrase.lower() in lower:
                value += 2
        if not readable(sentence):
            value -= 3
        return value

    ranked = sorted(pool, key=score, reverse=True)
    chosen = [sentence for sentence in ranked[:2] if score(sentence) > 0]
    if not chosen and ranked and readable(ranked[0]):
        chosen = [ranked[0]]
    excerpt = " ".join(chosen)
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 1].rsplit(" ", 1)[0] + "…"
    return excerpt
