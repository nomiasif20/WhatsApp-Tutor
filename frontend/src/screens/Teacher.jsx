import { Fragment, useEffect, useState } from "react";
import { api, gradeLabel, percent } from "../api";
import Shell from "../Shell";

const SECTIONS = [
  { id: "class", label: "Class" },
  { id: "curriculum", label: "Curriculum" },
  { id: "papers", label: "Examinations" },
];

export default function Teacher({ person, onLeave }) {
  const [section, setSection] = useState("class");
  return (
    <Shell person={person} onLeave={onLeave} section={section} setSection={setSection} sections={SECTIONS} meta="Mathematics · Grades 7–9">
      {section === "class" && <ClassView />}
      {section === "curriculum" && <Curriculum />}
      {section === "papers" && <Papers />}
    </Shell>
  );
}

function ClassView() {
  const [students, setStudents] = useState(null);
  const [grade, setGrade] = useState(0);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/class").then((data) => setStudents(data.students)).catch((err) => setError(err.message));
  }, []);

  if (error) return <p className="bad">{error}</p>;
  if (!students) return <p>Loading the class…</p>;
  const visible = students.filter((student) => !grade || student.grade === grade);

  return (
    <div className="stack">
      <div>
        <p className="kicker">Grades 7–9</p>
        <h1>Class</h1>
        <p className="lede">Progress is shown by topic and examination score. The wording of a student’s question stays with the student.</p>
      </div>
      <div className="row">
        {[0, 7, 8, 9].map((value) => (
          <button key={value} className={grade === value ? "primary" : "quiet"} type="button" onClick={() => setGrade(value)}>
            {value ? `Grade ${value}` : "All grades"}
          </button>
        ))}
      </div>
      <table>
        <thead>
          <tr>
            <th>Student</th>
            <th>Grade</th>
            <th>This week</th>
            <th>Accuracy</th>
            <th>Focus</th>
            <th>Latest paper</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((student) => {
            const latest = student.exams.filter((paper) => paper.score !== null).sort((a, b) => (a.submitted_at < b.submitted_at ? 1 : -1))[0];
            return (
              <Fragment key={student.id}>
                <tr className="button" onClick={() => setOpen(open === student.id ? null : student.id)}>
                  <td><strong>{student.name}</strong><br /><span className="meta">{student.parent}</span></td>
                  <td>{student.grade}</td>
                  <td>{student.week.questions} questions · {student.week.practised} marked</td>
                  <td>{percent(student.week.accuracy)}</td>
                  <td>{student.focus.map((item) => item.name).join(", ") || "—"}</td>
                  <td>{latest ? `Term ${latest.term} · ${latest.score}/${latest.total}` : "None yet"}</td>
                </tr>
                {open === student.id ? (
                  <tr>
                    <td colSpan={6} className="detail">
                      {student.terms.map((term) => (
                        <div key={term.term}>
                          <strong>Term {term.term}</strong>
                          {term.topics.map((topic) => (
                            <div className="topic-line" key={topic.id}>
                              <span>{topic.name}</span>
                              <span>{topic.attempted ? `${topic.correct}/${topic.attempted}` : "Not yet"}</span>
                              <div className="track"><span style={{ width: `${Math.round((topic.accuracy || 0) * 100)}%` }} /></div>
                            </div>
                          ))}
                        </div>
                      ))}
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Curriculum() {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [grade, setGrade] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState(null);
  const [filter, setFilter] = useState(8);

  function load() {
    return api("/api/curriculum").then(setStatus);
  }
  useEffect(() => { load().catch((err) => setError(err.message)); }, []);

  async function retrain() {
    setBusy(true);
    setError("");
    setMessage("Reading the curriculum folder. This can take a few minutes.");
    try {
      const summary = await api("/api/curriculum/train", { method: "POST" });
      setMessage(`Trained ${summary.trained} document${summary.trained === 1 ? "" : "s"}. ${summary.unchanged} were already current.`);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function upload(event) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.set("file", file);
      body.set("description", description);
      body.set("grade", grade);
      await api("/api/curriculum/upload", { method: "POST", body });
      setDescription("");
      setFile(null);
      setMessage("The file is now part of the training set.");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!status && !error) return <p>Loading the curriculum…</p>;

  const coverage = (status?.coverage || []).filter((item) => item.grade === filter);

  return (
    <div className="stack">
      <div>
        <p className="kicker">Training set</p>
        <h1>Curriculum</h1>
        <p className="lede">Learner books, navigation packs, and the curriculum policy in the curriculum folder are read into short passages. A question is matched to a topic, then a passage from those documents is shown with its page.</p>
      </div>
      <div className="row">
        <button className="primary" type="button" onClick={retrain} disabled={busy}>
          {busy ? "Training…" : "Train from the curriculum folder"}
        </button>
      </div>
      {message ? <p>{message}</p> : null}
      {error ? <p className="bad">{error}</p> : null}
      <div className="split">
        <table>
          <thead>
            <tr><th>Document</th><th>Kind</th><th>Grade</th><th>Pages</th><th>Passages</th></tr>
          </thead>
          <tbody>
            {(status?.documents || []).map((document) => (
              <tr key={document.id}>
                <td>{document.title}</td>
                <td>{document.kind}</td>
                <td>{gradeLabel(document.grade)}</td>
                <td>{document.pages}</td>
                <td>{document.chunk_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <form className="panel" onSubmit={upload}>
          <h2>Add a document</h2>
          <p>PDF files are read as text. For an image, describe what it teaches so the topic match can use it.</p>
          <label className="field">
            <span>File</span>
            <input type="file" accept=".pdf,image/png,image/jpeg,image/webp" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          </label>
          <label className="field">
            <span>Grade</span>
            <select value={grade} onChange={(event) => setGrade(event.target.value)}>
              <option value="">Grades 7–9</option>
              <option value="7">Grade 7</option>
              <option value="8">Grade 8</option>
              <option value="9">Grade 9</option>
            </select>
          </label>
          <label className="field">
            <span>What should be learned from this file?</span>
            <textarea rows={4} value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <button className="primary" disabled={busy || !file}>Add to the training set</button>
        </form>
      </div>
      <section>
        <div className="row">
          <h2>Passages by topic</h2>
          {[7, 8, 9].map((value) => (
            <button key={value} className={filter === value ? "primary" : "quiet"} type="button" onClick={() => setFilter(value)}>Grade {value}</button>
          ))}
        </div>
        <div className="coverage">
          {coverage.map((item) => (
            <div className="cov" key={`${item.grade}-${item.concept}`}>
              <span>Term {item.term} · {item.name}</span>
              <span>{item.passages}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function Papers() {
  const [grade, setGrade] = useState(8);
  const [term, setTerm] = useState(1);
  const [paper, setPaper] = useState(null);

  useEffect(() => {
    setPaper(null);
    api(`/api/exams/g${grade}-t${term}`).then(setPaper);
  }, [grade, term]);

  return (
    <div className="stack">
      <div>
        <p className="kicker">Memorandum included</p>
        <h1>Examinations</h1>
        <p className="lede">Term papers for Grades 7, 8 and 9. Students write them on their own desk. This view shows the memorandum.</p>
      </div>
      <div className="row">
        {[7, 8, 9].map((value) => (
          <button key={value} className={grade === value ? "primary" : "quiet"} type="button" onClick={() => setGrade(value)}>Grade {value}</button>
        ))}
        {[1, 2, 3, 4].map((value) => (
          <button key={value} className={term === value ? "primary" : "quiet"} type="button" onClick={() => setTerm(value)}>Term {value}</button>
        ))}
      </div>
      {!paper ? <p>Opening the paper…</p> : (
        <article className="paper">
          <header className="paper-top">
            <div>
              <p className="kicker">Mathematics</p>
              <h2>Grade {paper.grade} · Term {paper.term}</h2>
            </div>
            <p>{paper.total} marks · {paper.minutes} minutes</p>
          </header>
          {paper.questions.map((question, index) => (
            <div className="question" key={question.id}>
              <div className="q-head">
                <p><strong>{index + 1}.</strong> {question.prompt}</p>
                <span className="marks">{question.marks}</span>
              </div>
              <p className="memo"><strong>Answer:</strong> {question.answer}</p>
              <ol>{question.memo?.map((step) => <li key={step}>{step}</li>)}</ol>
            </div>
          ))}
        </article>
      )}
    </div>
  );
}
