"""Study desk API: questions, curriculum training, progress, and term papers."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

import chat
import curriculum
import db
import indexer

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "frontend" / "dist"
INDEX = indexer.PassageIndex()
PAPERS: dict[tuple[int, int], list[dict]] = {}
COVERAGE: list[dict] | None = None

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    db.init_db()
    with db.connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
        if count == 0 and db.MATERIAL.exists():
            indexer.train_material_folder(conn, db.MATERIAL)
        INDEX.load(conn)


def reload_index() -> None:
    global COVERAGE
    COVERAGE = None
    with db.connect() as conn:
        INDEX.load(conn)


def session_token(request: Request) -> str | None:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        token = header[7:].strip()
        return token or None
    return None


def require_person(request: Request, conn, role: str | None = None) -> dict:
    token = session_token(request)
    if not token:
        raise HTTPException(401, "Sign in to continue.")
    found = db.person_for_token(conn, token)
    if not found or not found.get("active", 1):
        raise HTTPException(401, "Sign in again.")
    if role and found["role"] != role:
        raise HTTPException(403, "This view is for a different role.")
    return db.public_person(found)


@app.get("/api/health")
def health():
    with db.connect() as conn:
        documents = conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]
        chunks = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
    return {"ok": True, "documents": documents, "passages": chunks}


@app.get("/api/whatsapp")
def whatsapp_verify(request: Request):
    params = request.query_params
    with db.connect() as conn:
        expected = db.setting(conn, "whatsapp_verify_token")
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    if mode == "subscribe" and expected and token == expected:
        return PlainTextResponse(params.get("hub.challenge", ""))
    raise HTTPException(403, "Verification failed.")


@app.post("/api/whatsapp")
async def whatsapp_inbound(request: Request):
    raw = await request.body()
    with db.connect() as conn:
        secret = db.setting(conn, "whatsapp_app_secret")
        if secret and not _whatsapp_signature(secret, raw, request.headers.get("x-hub-signature-256", "")):
            raise HTTPException(403, "The signature was not valid.")
        try:
            payload = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            return {"ok": True}
        for item in _whatsapp_incoming(payload):
            if item["text"] is None:
                if not chat.remember(conn, item["id"]):
                    continue
                conn.commit()
                _send_whatsapp(
                    conn,
                    item["phone"],
                    "Send the question as a text message. A photo or PDF can be attached on the desk.",
                )
                continue
            replies = chat.accept_whatsapp(conn, item["phone"], item["text"], item["id"])
            conn.commit()
            for reply in replies:
                _send_whatsapp(conn, item["phone"], reply)
    return {"ok": True}


@app.get("/api/chat")
def chat_thread(request: Request):
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        return {"phone": student.get("phone"), "messages": chat.history(conn, student["id"])}


@app.post("/api/chat")
async def chat_send(request: Request):
    body = await request.json()
    text = str(body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "Write a message.")
    if len(text) > 2000:
        raise HTTPException(400, "That message is too long.")
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        chat.turn(conn, student, text, "desk")
        conn.commit()
        messages = chat.history(conn, student["id"])
    return {"messages": messages}


@app.get("/api/admin/whatsapp")
def whatsapp_settings(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "admin")
        return _whatsapp_public(conn)


@app.put("/api/admin/whatsapp")
async def save_whatsapp_settings(request: Request):
    body = await request.json()
    phone_id = re.sub(r"\D", "", str(body.get("phone_number_id") or ""))
    verify = str(body.get("verify_token") or "").strip()
    token = str(body.get("token") or "").strip()
    secret = str(body.get("app_secret") or "").strip()
    if phone_id and not re.fullmatch(r"\d{6,22}", phone_id):
        raise HTTPException(400, "The phone number ID is the number from the WhatsApp business account.")
    if verify and len(verify) < 8:
        raise HTTPException(400, "Use a verify token of at least 8 characters.")
    with db.connect() as conn:
        require_person(request, conn, "admin")
        db.save_setting(conn, "whatsapp_phone_id", phone_id)
        if verify:
            db.save_setting(conn, "whatsapp_verify_token", verify)
        if token:
            db.save_setting(conn, "whatsapp_token", token)
        if secret:
            db.save_setting(conn, "whatsapp_app_secret", secret)
        conn.commit()
        return _whatsapp_public(conn)


@app.get("/api/admin/grok")
def grok_settings(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "admin")
        return {"key_set": bool(db.setting(conn, "grok_api_key"))}


@app.put("/api/admin/grok")
async def save_grok_settings(request: Request):
    body = await request.json()
    key = str(body.get("api_key") or "").strip()
    if key and len(key) < 12:
        raise HTTPException(400, "Paste the full Grok API key.")
    with db.connect() as conn:
        require_person(request, conn, "admin")
        if key:
            db.save_setting(conn, "grok_api_key", key)
        conn.commit()
        return {"key_set": bool(db.setting(conn, "grok_api_key"))}


@app.post("/api/session")
async def sign_in(request: Request):
    body = await request.json()
    username = str(body.get("username") or "")
    password = str(body.get("password") or "")
    with db.connect() as conn:
        status, found = db.authenticate(conn, username, password)
        if status == "inactive":
            raise HTTPException(403, "This account is not active. Ask an administrator.")
        if status != "ok" or not found:
            raise HTTPException(401, "The username or password is not correct.")
        token = db.open_session(conn, found["id"])
        conn.commit()
        person = db.public_person(found)
        if person["role"] == "parent":
            person["children"] = db.children_of(conn, person["id"])
    return {"token": token, "person": person}


@app.delete("/api/session")
def sign_out(request: Request):
    token = session_token(request)
    if token:
        with db.connect() as conn:
            db.close_session(conn, token)
            conn.commit()
    return {"ok": True}


@app.get("/api/admin/users")
def admin_users(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "admin")
        return {"users": db.list_users(conn)}


@app.post("/api/admin/users")
async def admin_create_user(request: Request):
    body = await request.json()
    name, username, password, role, grade, parent_id = _user_fields(body, creating=True)
    phone = _optional_phone(body.get("phone")) if role == "student" else None
    with db.connect() as conn:
        require_person(request, conn, "admin")
        try:
            created = db.create_user(
                conn,
                name=name,
                username=username,
                password=password,
                role=role,
                grade=grade,
                parent_id=parent_id,
                phone=phone,
            )
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        conn.commit()
        users = db.list_users(conn)
        made = next(user for user in users if user["id"] == created["id"])
    return made


@app.patch("/api/admin/users/{user_id}")
async def admin_update_user(user_id: str, request: Request):
    body = await request.json()
    name = _clean_name(body.get("name")) if "name" in body else None
    password = str(body.get("password") or "").strip() or None
    if password is not None and len(password) < 6:
        raise HTTPException(400, "Use a password of at least 6 characters.")
    grade = body.get("grade")
    if grade is not None and grade != "":
        try:
            grade = int(grade)
        except (TypeError, ValueError):
            raise HTTPException(400, "Choose grade 7, 8, or 9.")
        if grade not in (7, 8, 9):
            raise HTTPException(400, "Choose grade 7, 8, or 9.")
    else:
        grade = None
    active = body.get("active")
    if active is not None:
        active = 1 if active else 0
    parent_id = str(body.get("parent_id") or "").strip() or None
    set_phone = "phone" in body
    phone = _optional_phone(body.get("phone")) if set_phone else None
    with db.connect() as conn:
        admin = require_person(request, conn, "admin")
        try:
            updated = db.update_user(
                conn,
                user_id,
                actor_id=admin["id"],
                name=name,
                grade=grade,
                parent_id=parent_id,
                clear_parent=bool(body.get("clear_parent")),
                active=active,
                password=password,
                phone=phone,
                set_phone=set_phone,
            )
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        conn.commit()
    return updated


def _optional_phone(value) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return db.normalise_phone(raw)
    except ValueError as error:
        raise HTTPException(400, str(error)) from error


def _whatsapp_public(conn) -> dict:
    verify = db.setting(conn, "whatsapp_verify_token")
    if not verify:
        verify = secrets.token_urlsafe(18)
        db.save_setting(conn, "whatsapp_verify_token", verify)
        conn.commit()
    return {
        "phone_number_id": db.setting(conn, "whatsapp_phone_id"),
        "verify_token": verify,
        "token_set": bool(db.setting(conn, "whatsapp_token")),
        "secret_set": bool(db.setting(conn, "whatsapp_app_secret")),
        "webhook_path": "/api/whatsapp",
    }


def _whatsapp_signature(secret: str, raw: bytes, header: str) -> bool:
    if not header.startswith("sha256="):
        return False
    digest = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, header[7:])


def _whatsapp_incoming(payload: dict) -> list[dict]:
    found = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            for message in value.get("messages") or []:
                try:
                    phone = db.normalise_phone(str(message.get("from") or ""))
                except ValueError:
                    continue
                kind = message.get("type")
                text = None
                if kind == "text":
                    text = str((message.get("text") or {}).get("body") or "").strip()
                    if not text:
                        continue
                elif kind not in {"image", "document", "audio", "video", "sticker"}:
                    continue
                found.append({"phone": phone, "id": str(message.get("id") or ""), "text": text})
    return found


def _send_whatsapp(conn, to: str, body: str) -> None:
    token = db.setting(conn, "whatsapp_token")
    phone_id = db.setting(conn, "whatsapp_phone_id")
    if not token or not phone_id or not body:
        return
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": body[:4096]},
    }).encode()
    request = urllib.request.Request(
        f"https://graph.facebook.com/v26.0/{phone_id}/messages",
        data=payload,
        method="POST",
    )
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=20):
            return
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:400]
        print(f"WhatsApp send failed: {error.code} {detail}")
    except urllib.error.URLError as error:
        print(f"WhatsApp send failed: {error.reason}")


def _clean_name(value) -> str:
    name = str(value or "").strip()
    if len(name) < 2:
        raise HTTPException(400, "Enter the person's full name.")
    return name


def _user_fields(body: dict, creating: bool):
    name = _clean_name(body.get("name"))
    username = str(body.get("username") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,31}", username):
        raise HTTPException(400, "Usernames use 3 to 32 letters, numbers, dots, or hyphens.")
    password = str(body.get("password") or "")
    if creating and len(password) < 6:
        raise HTTPException(400, "Use a password of at least 6 characters.")
    role = str(body.get("role") or "").strip().lower()
    if role not in {"student", "teacher", "parent", "admin"}:
        raise HTTPException(400, "Choose a student, teacher, parent, or administrator.")
    grade = None
    parent_id = None
    if role == "student":
        try:
            grade = int(body.get("grade"))
        except (TypeError, ValueError):
            grade = 0
        if grade not in (7, 8, 9):
            raise HTTPException(400, "Choose grade 7, 8, or 9.")
        parent_id = str(body.get("parent_id") or "").strip() or None
    return name, username, password, role, grade, parent_id


@app.get("/api/me")
def me(request: Request):
    with db.connect() as conn:
        found = require_person(request, conn)
        if found["role"] == "parent":
            found["children"] = db.children_of(conn, found["id"])
        return found


@app.get("/api/syllabus")
def syllabus(request: Request):
    with db.connect() as conn:
        found = require_person(request, conn, "student")
    return {"grade": found["grade"], "terms": curriculum.syllabus(found["grade"]), "current_term": 4}


@app.get("/api/lesson")
def lesson(concept: str, request: Request):
    if concept not in curriculum.NAMES:
        raise HTTPException(404, "That topic is not in the syllabus.")
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        topic = _topic_for(student["grade"], concept)
        pack = curriculum.lesson(student["grade"], concept)
        similar = db.save_practice(conn, student["id"], topic, pack["practice"][:2])
        sources = INDEX.search(topic["name"] + " " + topic["note"], student["grade"], curriculum.keywords_for(concept))
        conn.commit()
    return {
        "topic": topic,
        "steps": pack["steps"],
        "mistakes": pack["mistakes"],
        "example": _public_worked(pack["example"]),
        "similar": similar,
        "sources": sources,
    }


@app.post("/api/ask")
async def ask(request: Request):
    question, concept, upload = await _read_ask(request)
    attachment = None
    extracted = ""
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        if upload is not None and getattr(upload, "filename", None):
            attachment, extracted = await _store_student_file(upload)
        body = question.strip()
        if not body and extracted:
            body = extracted[:1200]
        if not body:
            raise HTTPException(400, "Write the question, or attach a PDF or photo that includes it.")
        working = body if not extracted else f"{body}\n{extracted[:4000]}"
        judged = curriculum.classify(working, student["grade"], concept or None)
        topic = judged["topic"]
        direct = curriculum.solve_question(working)
        if direct and direct["concept"] != judged["concept"] and not concept:
            judged = curriculum.classify(working, student["grade"], direct["concept"])
            topic = judged["topic"]
        pack = curriculum.lesson(student["grade"], judged["concept"])
        if direct and direct["concept"] != judged["concept"]:
            direct = None
        sources = INDEX.search(working, student["grade"], curriculum.keywords_for(judged["concept"]))
        similar = db.save_practice(conn, student["id"], topic, pack["practice"][:2])
        db.save_question(conn, student["id"], body[:2000], topic["id"], topic["name"], topic.get("term"), attachment)
        db.log_activity(conn, student["id"], "question", topic["id"], topic["name"], topic.get("term"), None)
        conn.commit()
    example = pack["example"]
    return {
        "question": body,
        "attachment": f"/api/files/{attachment}" if attachment else None,
        "read_from_file": bool(extracted),
        "topic": topic,
        "in_grade": judged["in_grade"],
        "confidence": judged["confidence"],
        "reason": judged["reason"],
        "alternatives": judged["alternatives"],
        "steps": pack["steps"],
        "mistakes": pack["mistakes"],
        "direct": _public_worked(direct) if direct else None,
        "example": _public_worked(example),
        "similar": similar,
        "sources": sources,
    }


@app.post("/api/practice/{item_id}/answer")
async def answer_practice(item_id: int, request: Request):
    payload = await request.json()
    given = str(payload.get("answer") or "")
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        row = conn.execute("SELECT * FROM practice_items WHERE id = ?", (item_id,)).fetchone()
        if not row or row["student_id"] != student["id"]:
            raise HTTPException(404, "That practice question is not on this desk.")
        expected = json.loads(row["accept_json"])
        answer_text = row["answer_text"]
        steps = json.loads(row["steps_json"])
        correct = curriculum.answers_match(given, expected)
        if not row["answered"]:
            conn.execute("UPDATE practice_items SET answered = 1 WHERE id = ?", (item_id,))
            db.log_activity(
                conn,
                student["id"],
                "practice",
                row["topic_id"],
                row["topic_name"],
                row["term"],
                1 if correct else 0,
            )
        conn.commit()
    return {"correct": correct, "answer": answer_text, "steps": steps}


@app.get("/api/progress")
def progress(request: Request):
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        return db.progress_for(conn, student, include_questions=True)


@app.get("/api/exams")
def exams(request: Request):
    with db.connect() as conn:
        found = require_person(request, conn)
        if found["role"] == "student":
            return {"grade": found["grade"], "papers": db.exam_list(conn, found["id"], found["grade"])}
        if found["role"] == "parent":
            reports = []
            for child in db.children_of(conn, found["id"]):
                reports.append({
                    "student": {"id": child["id"], "name": child["name"], "grade": child["grade"]},
                    "papers": db.exam_list(conn, child["id"], child["grade"]),
                })
            return {"children": reports}
        papers = []
        for grade in (7, 8, 9):
            for term in (1, 2, 3, 4):
                papers.append({"id": f"g{grade}-t{term}", "grade": grade, "term": term, "total": 50, "minutes": 60})
        return {"papers": papers}


@app.get("/api/exams/{paper_id}")
def exam_paper(paper_id: str, request: Request):
    grade, term = _parse_paper(paper_id)
    with db.connect() as conn:
        found = require_person(request, conn)
        reveal = found["role"] == "teacher"
        if found["role"] == "student" and found["grade"] != grade:
            raise HTTPException(403, "This paper is for another grade.")
        questions = _paper(grade, term)
        latest = None
        if found["role"] == "student":
            latest = _latest_result(conn, found["id"], paper_id)
        return {
            "id": paper_id,
            "grade": grade,
            "term": term,
            "title": "Mathematics",
            "minutes": 60,
            "total": 50,
            "instructions": [
                "Answer all the questions.",
                "Write the final answer in the form asked. Working is recorded in the memorandum after you submit.",
                "A calculator is not required.",
            ],
            "questions": [_public_exam_question(item, reveal) for item in questions],
            "latest": latest,
        }


@app.post("/api/exams/{paper_id}/submit")
async def submit_exam(paper_id: str, request: Request):
    grade, term = _parse_paper(paper_id)
    payload = await request.json()
    answers = payload.get("answers") or {}
    with db.connect() as conn:
        student = require_person(request, conn, "student")
        if student["grade"] != grade:
            raise HTTPException(403, "This paper is for another grade.")
        questions = _paper(grade, term)
        detail = []
        score = 0
        for question in questions:
            given = str(answers.get(question["id"], "") or "")
            correct = curriculum.answers_match(given, question["accept"])
            awarded = question["marks"] if correct else 0
            score += awarded
            detail.append({
                "id": question["id"],
                "prompt": question["prompt"],
                "topic": question["topic"],
                "given": given,
                "answer": question["accept"][0],
                "memo": question["memo"],
                "marks": question["marks"],
                "awarded": awarded,
                "correct": correct,
            })
            db.log_activity(
                conn,
                student["id"],
                "exam",
                question["topic_id"],
                question["topic"],
                term,
                1 if correct else 0,
            )
        conn.execute(
            """
            INSERT INTO exam_results
                (student_id, paper_id, grade, term, score, total, detail_json, submitted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (student["id"], paper_id, grade, term, score, 50, json.dumps(detail), db.now()),
        )
        conn.commit()
    return {"score": score, "total": 50, "questions": detail}


@app.get("/api/exams/{paper_id}/script/{student_id}")
def exam_script(paper_id: str, student_id: str, request: Request):
    with db.connect() as conn:
        found = require_person(request, conn)
        if found["role"] == "student" and found["id"] != student_id:
            raise HTTPException(403, "This script belongs to another student.")
        if found["role"] == "parent":
            child_ids = {child["id"] for child in db.children_of(conn, found["id"])}
            if student_id not in child_ids:
                raise HTTPException(403, "This script belongs to another student.")
        result = _latest_result(conn, student_id, paper_id)
        if not result:
            raise HTTPException(404, "This paper has not been written yet.")
        if found["role"] == "parent":
            result = {key: result[key] for key in ("score", "total", "submitted_at")}
        return result


@app.get("/api/class")
def class_view(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "teacher")
        return {"students": db.class_overview(conn)}


@app.get("/api/curriculum")
def curriculum_status(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "teacher")
        documents = conn.execute(
            """
            SELECT id, title, kind, grade, pages, chunk_count, source, file_kind, trained_at, filename
              FROM documents
             ORDER BY source, grade, title
            """
        ).fetchall()
    return {"documents": [dict(row) for row in documents], "coverage": _coverage()}


@app.post("/api/curriculum/train")
def train(request: Request):
    with db.connect() as conn:
        require_person(request, conn, "teacher")
        summary = indexer.train_material_folder(conn, db.MATERIAL)
        rows = conn.execute("SELECT id, stored_path FROM documents WHERE source = 'material'").fetchall()
        removed = 0
        for row in rows:
            if not Path(row["stored_path"]).exists():
                conn.execute("DELETE FROM chunks WHERE document_id = ?", (row["id"],))
                conn.execute("DELETE FROM documents WHERE id = ?", (row["id"],))
                removed += 1
        conn.commit()
        summary["removed"] = removed
    reload_index()
    return summary


@app.post("/api/curriculum/upload")
async def upload_material(request: Request):
    form = await request.form()
    upload = form.get("file")
    description = str(form.get("description") or "").strip()
    grade_raw = str(form.get("grade") or "").strip()
    grade = int(grade_raw) if grade_raw in {"7", "8", "9"} else None
    if upload is None or not getattr(upload, "filename", None):
        raise HTTPException(400, "Choose a PDF or an image.")
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "Use a PDF or an image.")
    if suffix != ".pdf" and len(description) < 10:
        raise HTTPException(400, "For an image, describe what it teaches so it can be trained.")
    data = await upload.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "That file is larger than 20 MB.")
    with db.connect() as conn:
        require_person(request, conn, "teacher")
    stored = db.UPLOADS / f"{uuid4().hex}{suffix}"
    stored.write_bytes(data)
    with db.connect() as conn:
        result = indexer.train_upload(
            conn,
            stored,
            grade=grade,
            description=description,
            original_name=upload.filename,
        )
    reload_index()
    return result


@app.get("/api/family")
def family(request: Request):
    with db.connect() as conn:
        parent = require_person(request, conn, "parent")
        reports = []
        for child in db.children_of(conn, parent["id"]):
            reports.append(db.progress_for(conn, child))
        return {"parent": parent["name"], "children": reports}


@app.get("/api/files/{name}")
def uploaded_file(name: str):
    if not re.fullmatch(r"[a-f0-9]{32}\.(pdf|png|jpg|jpeg|webp)", name):
        raise HTTPException(404, "File not found.")
    path = db.UPLOADS / name
    if not path.exists():
        raise HTTPException(404, "File not found.")
    return FileResponse(path)


def _topic_for(grade: int, concept: str) -> dict:
    if curriculum.term_of(grade, concept):
        return curriculum.describe(grade, concept)
    home = curriculum.first_home(concept)
    if not home:
        raise HTTPException(404, "That topic is not in the syllabus.")
    return curriculum.describe(home[0], concept)


def _public_worked(item: dict | None) -> dict | None:
    if not item:
        return None
    return {"prompt": item.get("prompt"), "steps": item["steps"], "answer": item["answer"]}


def _paper(grade: int, term: int) -> list[dict]:
    key = (grade, term)
    if key not in PAPERS:
        PAPERS[key] = curriculum.paper_questions(grade, term)
    return PAPERS[key]


def _parse_paper(paper_id: str) -> tuple[int, int]:
    match = re.fullmatch(r"g([789])-t([1-4])", paper_id)
    if not match:
        raise HTTPException(404, "That paper does not exist.")
    return int(match.group(1)), int(match.group(2))


def _public_exam_question(item: dict, reveal: bool) -> dict:
    data = {
        "id": item["id"],
        "prompt": item["prompt"],
        "marks": item["marks"],
        "topic": item["topic"],
    }
    if reveal:
        data["answer"] = item["accept"][0]
        data["memo"] = item["memo"]
    return data


def _latest_result(conn, student_id: str, paper_id: str) -> dict | None:
    row = conn.execute(
        """
        SELECT score, total, detail_json, submitted_at
          FROM exam_results
         WHERE student_id = ? AND paper_id = ?
         ORDER BY id DESC
         LIMIT 1
        """,
        (student_id, paper_id),
    ).fetchone()
    if not row:
        return None
    return {
        "score": row["score"],
        "total": row["total"],
        "submitted_at": row["submitted_at"],
        "questions": json.loads(row["detail_json"]),
    }


def _coverage() -> list[dict]:
    global COVERAGE
    if COVERAGE is not None:
        return COVERAGE
    rows = []
    for grade in (7, 8, 9):
        for term, concepts in curriculum.PLACEMENT[grade].items():
            for concept in concepts:
                phrases = [phrase for phrase, weight in curriculum.PHRASES[concept] if weight >= 5][:4]
                count = 0
                for passage in INDEX.passages:
                    passage_grade = passage["grade"]
                    if passage_grade not in (None, grade):
                        continue
                    text = passage["text"].lower()
                    if any(phrase in text for phrase in phrases):
                        count += 1
                rows.append({
                    "grade": grade,
                    "term": term,
                    "name": curriculum.NAMES[concept],
                    "concept": concept,
                    "passages": count,
                })
    COVERAGE = rows
    return rows


async def _read_ask(request: Request):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        return str(form.get("question") or ""), str(form.get("concept") or ""), form.get("file")
    payload = await request.json()
    return str(payload.get("question") or ""), str(payload.get("concept") or ""), None


async def _store_student_file(upload) -> tuple[str | None, str]:
    suffix = Path(upload.filename).suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(400, "Attach a PDF or an image.")
    data = await upload.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "That file is larger than 20 MB.")
    name = f"{uuid4().hex}{suffix}"
    path = db.UPLOADS / name
    path.write_bytes(data)
    extracted = ""
    if suffix == ".pdf":
        try:
            reader = PdfReader(str(path))
            parts = []
            for page in reader.pages[:4]:
                parts.append(page.extract_text() or "")
            extracted = re.sub(r"\s+", " ", " ".join(parts)).strip()
        except Exception:
            extracted = ""
    return name, extracted


@app.get("/")
def root():
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse({"detail": "The interface has not been built yet."}, status_code=503)


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
def frontend(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(404, "Not found.")
    candidate = DIST / full_path
    if full_path and candidate.is_file():
        return FileResponse(candidate)
    index = DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(503, "The interface has not been built yet.")
