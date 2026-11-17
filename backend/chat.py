"""Conversation used by the desk chat and by WhatsApp."""

from __future__ import annotations

import json
import re

import curriculum
import db
import grok

CURRENT_TERM = 4


def history(conn, student_id: str, limit: int = 40) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, direction, body, source, created_at
          FROM (
            SELECT id, direction, body, source, created_at
              FROM chat_messages
             WHERE student_id = ?
             ORDER BY id DESC
             LIMIT ?
          )
         ORDER BY id ASC
        """,
        (student_id, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def turn(conn, student: dict, text: str, source: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    _add(conn, student["id"], "in", cleaned[:2000], source)
    parts = _chunks(_respond(conn, student, cleaned))
    for part in parts:
        _add(conn, student["id"], "out", part, source)
    return parts


def remember(conn, message_id: str) -> bool:
    """Return True when this WhatsApp message has not been handled yet."""
    if not message_id:
        return True
    seen = conn.execute(
        "SELECT message_id FROM whatsapp_seen WHERE message_id = ?",
        (message_id,),
    ).fetchone()
    if seen:
        return False
    conn.execute(
        "INSERT INTO whatsapp_seen (message_id, received_at) VALUES (?, ?)",
        (message_id, db.now()),
    )
    return True


def accept_whatsapp(conn, phone: str, text: str, message_id: str) -> list[str]:
    if not remember(conn, message_id):
        return []
    row = conn.execute("SELECT * FROM people WHERE phone = ?", (phone,)).fetchone()
    if not row or row["role"] != "student":
        return [
            "This WhatsApp number is not linked to a student account. "
            "Ask an administrator to add it."
        ]
    student = dict(row)
    if not student.get("active", 1):
        return ["This account is not active. Ask an administrator."]
    return turn(conn, student, text, "whatsapp")


def _add(conn, student_id: str, direction: str, body: str, source: str) -> None:
    conn.execute(
        """
        INSERT INTO chat_messages (student_id, direction, body, source, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (student_id, direction, body, source, db.now()),
    )


def _chunks(text: str, limit: int = 3500) -> list[str]:
    text = text.strip()
    if len(text) <= limit:
        return [text]
    parts = []
    current = ""
    for block in text.split("\n\n"):
        piece = block if not current else f"{current}\n\n{block}"
        if len(piece) <= limit:
            current = piece
            continue
        if current:
            parts.append(current)
        current = block[:limit]
    if current:
        parts.append(current)
    return parts or [text[:limit]]


def _state(conn, student_id: str) -> dict:
    row = conn.execute(
        "SELECT state_json FROM chat_state WHERE student_id = ?",
        (student_id,),
    ).fetchone()
    if not row:
        return {"mode": "idle", "practice": []}
    try:
        data = json.loads(row["state_json"])
    except json.JSONDecodeError:
        data = {}
    data.setdefault("mode", "idle")
    data.setdefault("practice", [])
    return data


def _save_state(conn, student_id: str, state: dict) -> None:
    conn.execute(
        """
        INSERT INTO chat_state (student_id, state_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(student_id) DO UPDATE SET
            state_json = excluded.state_json,
            updated_at = excluded.updated_at
        """,
        (student_id, json.dumps(state), db.now()),
    )


def _key(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9 ]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _respond(conn, student: dict, text: str) -> str:
    state = _state(conn, student["id"])
    key = _key(text)
    paper_term = _paper_request(key)
    if key in {"help", "menu", "commands"}:
        extra = ""
        if state.get("mode") == "paper":
            extra = "\n\nA paper is in progress. Reply with the answer, or stop to leave it."
        return _help(student) + extra
    if key in {"progress", "report"}:
        extra = ""
        if state.get("mode") == "paper":
            extra = "\n\nA paper is still in progress."
        return _progress(conn, student) + extra
    if key == "stop":
        if state.get("mode") != "paper":
            return "There is no paper in progress. Send a mathematics question, or reply paper."
        state["mode"] = "idle"
        state.pop("paper", None)
        _save_state(conn, student["id"], state)
        return "The paper was left unfinished, and no score was saved. Send a question, or reply paper to start again."
    if key in {"paper again", "exam again"} or (paper_term and key.endswith("again")):
        return _start_paper(conn, student, state, paper_term or CURRENT_TERM)
    if paper_term and state.get("mode") == "paper" and state.get("paper", {}).get("term") == paper_term:
        return "This question is still open.\n\n" + _paper_question(state["paper"])
    if paper_term:
        existing = _latest_paper(conn, student["id"], student["grade"], paper_term)
        if existing and "again" not in key:
            return (
                f"The Term {paper_term} paper is already marked {existing['score']}/{existing['total']}.\n"
                f"Reply paper again to write it once more."
            )
        return _start_paper(conn, student, state, paper_term)
    if state.get("mode") == "paper":
        if _looks_like_answer(text):
            return _paper_answer(conn, student, state, text)
        if _is_conversation(text):
            return (
                _conversation(conn, student, text, "A term paper is still open.")
                + "\n\nThe paper is still open.\n\n"
                + _paper_question(state["paper"])
            )
        return "This paper is still open. Reply with the answer, or stop to leave it.\n\n" + _paper_question(state["paper"])
    if state.get("practice") and _looks_like_answer(text):
        return _practice_answer(conn, student, state, text)
    if _is_conversation(text):
        note = ""
        if state.get("practice"):
            note = "Practice questions are still open. After the reply, one sentence can invite an answer such as 1 15."
        return _conversation(conn, student, text, note)
    state["practice"] = []
    state["mode"] = "idle"
    _save_state(conn, student["id"], state)
    return _question(conn, student, state, text)


def _help(student: dict) -> str:
    first = student["name"].split()[0]
    return (
        f"{first}, send a mathematics question. I will name the syllabus topic, "
        "show a worked example, and set two similar questions.\n\n"
        "You can also say:\n"
        "progress — this week's work\n"
        "paper — the Term 4 paper, one question at a time\n"
        "paper 2 — a paper for another term\n"
        "stop — leave a paper without a score\n"
        "help — show this again\n\n"
        "When practice questions are open, reply 15, or 1 15 if two are open."
    )


def _progress(conn, student: dict) -> str:
    report = db.progress_for(conn, student)
    week = report["week"]
    lines = [
        f"This week: {week['questions']} question{'s' if week['questions'] != 1 else ''}, "
        f"{week['correct']} of {week['practised']} marked answers correct."
    ]
    written = [item for item in report["exams"] if item["score"] is not None]
    if written:
        latest = written[-1]
        lines.append(f"Latest paper: Term {latest['term']} · {latest['score']}/{latest['total']}.")
    else:
        lines.append("No term paper has been submitted yet.")
    if report["focus"]:
        lines.append("")
        lines.append("Focus")
        for item in report["focus"]:
            lines.append(f"{item['name']}: {item['reason']}")
    return "\n".join(lines)


def _paper_request(key: str) -> int | None:
    if key in {"paper", "exam", "test", "examination"}:
        return CURRENT_TERM
    match = re.fullmatch(r"(?:term|paper|exam|test)\s*([1-4])(?:\s+again)?", key)
    if match:
        return int(match.group(1))
    return None


def _latest_paper(conn, student_id: str, grade: int, term: int) -> dict | None:
    row = conn.execute(
        """
        SELECT score, total FROM exam_results
         WHERE student_id = ? AND paper_id = ?
         ORDER BY id DESC LIMIT 1
        """,
        (student_id, f"g{grade}-t{term}"),
    ).fetchone()
    return dict(row) if row else None


def _start_paper(conn, student: dict, state: dict, term: int) -> str:
    questions = []
    for item in curriculum.paper_questions(student["grade"], term):
        questions.append({
            "prompt": item["prompt"],
            "accept": item["accept"],
            "memo": item["memo"],
            "marks": item["marks"],
            "topic_id": item["topic_id"],
            "topic": item["topic"],
        })
    state["mode"] = "paper"
    state["practice"] = []
    state["paper"] = {"term": term, "index": 0, "answers": [], "questions": questions}
    _save_state(conn, student["id"], state)
    return (
        f"Term {term} paper\n"
        f"{len(questions)} questions · 50 marks\n"
        "Reply with each answer when it is asked. Reply stop to leave the paper.\n\n"
        + _paper_question(state["paper"])
    )


def _paper_question(paper: dict) -> str:
    question = paper["questions"][paper["index"]]
    number = paper["index"] + 1
    total = len(paper["questions"])
    return f"Question {number} of {total} · {question['marks']} marks\n{question['prompt']}"


def _paper_answer(conn, student: dict, state: dict, text: str) -> str:
    paper = state["paper"]
    question = paper["questions"][paper["index"]]
    given = _answer_body(text)
    correct = curriculum.answers_match(given, question["accept"])
    paper["answers"].append({
        "given": given,
        "correct": correct,
        "awarded": question["marks"] if correct else 0,
        "marks": question["marks"],
        "answer": question["accept"][0],
        "prompt": question["prompt"],
        "topic_id": question["topic_id"],
        "topic": question["topic"],
        "memo": question["memo"],
    })
    paper["index"] += 1
    if paper["index"] < len(paper["questions"]):
        _save_state(conn, student["id"], state)
        return "Recorded.\n\n" + _paper_question(paper)
    return _finish_paper(conn, student, state)


def _finish_paper(conn, student: dict, state: dict) -> str:
    paper = state["paper"]
    term = paper["term"]
    detail = []
    score = 0
    lines = []
    for index, item in enumerate(paper["answers"], start=1):
        score += item["awarded"]
        detail.append({
            "id": str(index),
            "prompt": item["prompt"],
            "topic": item["topic"],
            "given": item["given"],
            "answer": item["answer"],
            "memo": item["memo"],
            "marks": item["marks"],
            "awarded": item["awarded"],
            "correct": item["correct"],
        })
        mark = "correct" if item["correct"] else "not correct"
        lines.append(f"{index}. {mark} · {item['awarded']}/{item['marks']} · answer {item['answer']}")
        db.log_activity(
            conn,
            student["id"],
            "exam",
            item["topic_id"],
            item["topic"],
            term,
            1 if item["correct"] else 0,
        )
    conn.execute(
        """
        INSERT INTO exam_results
            (student_id, paper_id, grade, term, score, total, detail_json, submitted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            student["id"],
            f"g{student['grade']}-t{term}",
            student["grade"],
            term,
            score,
            50,
            json.dumps(detail),
            db.now(),
        ),
    )
    state["mode"] = "idle"
    state.pop("paper", None)
    _save_state(conn, student["id"], state)
    return f"Term {term} paper\n{score}/50\n\n" + "\n".join(lines)


def _looks_like_answer(text: str) -> bool:
    """A practice or paper reply carries a value, such as 15 or 1 15."""
    if curriculum.solve_question(text):
        return False
    if re.search(r"\d\s*[\+\-\*/x×÷]\s*\d", text):
        return False
    if re.search(r"\b(add|plus|sum|subtract|minus|multiply|times|divide|calculate|find|simplify|solve|what|how|which|write|evaluate|determine|explain)\b", text, re.I):
        return False
    if _practice_choice(text):
        return True
    if "?" in text or len(text) > 40:
        return False
    return bool(re.search(r"\d", text))


def _conversation(conn, student: dict, text: str, note: str = "") -> str:
    recent = history(conn, student["id"], limit=8)
    if recent and recent[-1]["direction"] == "in":
        recent = recent[:-1]
    return grok.reply(conn, student, text, recent, note)


def _is_conversation(text: str) -> bool:
    if curriculum.solve_question(text):
        return False
    if re.search(r"\d\s*[\+\-\*/x×÷=]\s*\d", text):
        return False
    if re.search(r"\b(why|explain|understand|mean|thanks|thank you|how are you|who are you|can you talk|hello there)\b", text, re.I):
        return True
    if re.search(r"\d", text):
        return False
    if re.search(r"\b(find|calculate|simplify|solve|hcf|lcm|factor|equation|fraction|percent)\b", text, re.I):
        return False
    return len(text.split()) <= 40


def _practice_choice(text: str) -> tuple[int, str] | None:
    match = re.fullmatch(r"([12])\s*[:.)-]?\s+(.+)", text.strip(), re.S)
    if not match:
        return None
    return int(match.group(1)), _answer_body(match.group(2))


def _answer_body(text: str) -> str:
    body = text.strip()
    body = re.sub(r"^(the\s+)?answer\s*(is|=|:)\s*", "", body, flags=re.I)
    return body.strip()


def _practice_answer(conn, student: dict, state: dict, text: str) -> str:
    rows = []
    for item_id in state.get("practice") or []:
        row = conn.execute(
            "SELECT * FROM practice_items WHERE id = ? AND student_id = ?",
            (item_id, student["id"]),
        ).fetchone()
        if row and not row["answered"]:
            rows.append(dict(row))
    if not rows:
        state["practice"] = []
        _save_state(conn, student["id"], state)
        return _question(conn, student, state, text)
    choice = _practice_choice(text)
    if choice:
        number, given = choice
        if number > len(rows):
            return f"There is no question {number}. Reply 1 and the answer."
        return _mark_practice(conn, student, state, rows, rows[number - 1], given)
    given = _answer_body(text)
    matched = [row for row in rows if curriculum.answers_match(given, json.loads(row["accept_json"]))]
    if len(rows) > 1 and len(matched) != 1:
        lines = ["Reply with the question number and the answer, for example 1 15.", ""]
        for index, row in enumerate(rows, start=1):
            lines.append(f"{index}. {row['prompt']}")
        return "\n".join(lines)
    target = matched[0] if matched else rows[0]
    return _mark_practice(conn, student, state, rows, target, given)


def _mark_practice(conn, student, state, rows, row, given: str) -> str:
    expected = json.loads(row["accept_json"])
    correct = curriculum.answers_match(given, expected)
    if not row["answered"]:
        conn.execute("UPDATE practice_items SET answered = 1 WHERE id = ?", (row["id"],))
        db.log_activity(
            conn,
            student["id"],
            "practice",
            row["topic_id"],
            row["topic_name"],
            row["term"],
            1 if correct else 0,
        )
    remaining = [item["id"] for item in rows if item["id"] != row["id"]]
    state["practice"] = remaining
    _save_state(conn, student["id"], state)
    head = "Correct." if correct else "Not this time."
    lines = [head, f"The answer is {row['answer_text']}."]
    if remaining:
        pending = next(item for item in rows if item["id"] in remaining)
        number = rows.index(pending) + 1
        lines.append("")
        lines.append(f"Question {number} is still open.")
        lines.append(pending["prompt"])
    else:
        lines.append("")
        lines.append("Send another mathematics question when you are ready.")
    return "\n".join(lines)


def _question(conn, student: dict, state: dict, text: str) -> str:
    judged = curriculum.classify(text, student["grade"])
    direct = curriculum.solve_question(text)
    if direct and direct.get("concept") != judged["concept"]:
        judged = curriculum.classify(text, student["grade"], direct["concept"])
        if direct.get("concept") != judged["concept"]:
            direct = None
    elif not (direct and direct.get("concept") == judged["concept"]):
        direct = None
    if direct and not direct.get("prompt"):
        direct = {**direct, "prompt": text.strip()}
    topic = _topic(student["grade"], judged["concept"])
    pack = curriculum.lesson(student["grade"], judged["concept"])
    saved = db.save_practice(conn, student["id"], topic, pack["practice"][:2])
    db.save_question(conn, student["id"], text[:2000], topic["id"], topic["name"], topic.get("term"), None)
    db.log_activity(conn, student["id"], "question", topic["id"], topic["name"], topic.get("term"), None)
    state["mode"] = "idle"
    state["practice"] = [item["id"] for item in saved]
    _save_state(conn, student["id"], state)
    where = f"Grade {topic['grade']}"
    if topic.get("term"):
        where += f" · Term {topic['term']}"
    blocks = [where, topic["name"], judged["reason"], ""]
    if direct:
        blocks.append(_worked("Your question", direct))
    else:
        blocks.append("Method")
        blocks.extend(pack["steps"])
    blocks.append("")
    blocks.append(_worked("Example", pack["example"]))
    blocks.append("")
    blocks.append("Similar questions")
    for index, item in enumerate(pack["practice"][:2], start=1):
        blocks.append(f"{index}. {item['prompt']}")
    blocks.append("")
    blocks.append("Reply with the answer. Put 1 or 2 in front when two questions are open.")
    return "\n".join(blocks)


def _topic(grade: int, concept: str) -> dict:
    if curriculum.term_of(grade, concept):
        return curriculum.describe(grade, concept)
    home = curriculum.first_home(concept)
    if not home:
        return curriculum.describe(grade, concept)
    return curriculum.describe(home[0], concept)


def _worked(title: str, item: dict) -> str:
    steps = item.get("steps") or []
    if isinstance(steps, str):
        steps = [steps]
    lines = [title, item.get("prompt") or "", *steps, f"Answer: {item.get('answer')}"]
    return "\n".join(line for line in lines if line is not None)
