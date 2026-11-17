import { useEffect, useState } from "react";
import { api, percent, when } from "../api";
import Shell from "../Shell";

const SECTIONS = [
  { id: "progress", label: "Progress" },
  { id: "exams", label: "Examinations" },
];

export default function Parent({ person, onLeave }) {
  const [section, setSection] = useState("progress");
  const [family, setFamily] = useState(null);
  const [childId, setChildId] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/family")
      .then((data) => {
        setFamily(data);
        setChildId(data.children[0]?.student.id || null);
      })
      .catch((err) => setError(err.message));
  }, []);

  const child = family?.children.find((item) => item.student.id === childId);

  return (
    <Shell person={person} onLeave={onLeave} section={section} setSection={setSection} sections={SECTIONS} meta={child ? `Parent of ${child.student.name}` : "Parent"}>
      {error ? <p className="bad">{error}</p> : null}
      {!family ? <p>Loading progress…</p> : null}
      {family && family.children.length > 1 ? (
        <div className="row">
          {family.children.map((item) => (
            <button key={item.student.id} className={item.student.id === childId ? "primary" : "quiet"} type="button" onClick={() => setChildId(item.student.id)}>
              {item.student.name}
            </button>
          ))}
        </div>
      ) : null}
      {child && section === "progress" ? <ChildProgress child={child} /> : null}
      {child && section === "exams" ? <ChildExams child={child} /> : null}
    </Shell>
  );
}

function ChildProgress({ child }) {
  return (
    <div className="stack">
      <div>
        <p className="kicker">Grade {child.student.grade} · Mathematics</p>
        <h1>{child.student.name}</h1>
        <p className="lede">This view shows topics, accuracy, and examination scores. It does not include the wording of questions.</p>
      </div>
      <div className="stats">
        <div className="stat"><b>{child.week.questions}</b><span>Questions this week</span></div>
        <div className="stat"><b>{child.week.practised}</b><span>Answers marked</span></div>
        <div className="stat"><b>{percent(child.week.accuracy)}</b><span>Accuracy this week</span></div>
      </div>
      <section className="panel">
        <h2>Suggested focus</h2>
        {child.focus.length === 0 ? <p>No focus area yet. New work will appear here.</p> : null}
        {child.focus.map((item) => (
          <p key={item.id}><strong>{item.name}</strong> · Term {item.term} · {item.reason}</p>
        ))}
      </section>
      {child.terms.map((term) => (
        <section key={term.term}>
          <h2>Term {term.term}</h2>
          {term.topics.map((topic) => (
            <div className="topic-line" key={topic.id}>
              <span>{topic.name}</span>
              <span>{topic.attempted ? `${topic.correct} correct of ${topic.attempted}` : "Not yet"}</span>
              <div className="track"><span style={{ width: `${Math.round((topic.accuracy || 0) * 100)}%` }} /></div>
            </div>
          ))}
        </section>
      ))}
      <section>
        <h2>Recent activity</h2>
        <ul className="activity">
          {child.recent.map((item, index) => (
            <li key={`${item.created_at}-${index}`}>
              <span>
                {item.kind === "paper" ? item.topic_name : item.kind === "question" ? `Asked about ${item.topic_name}` : item.kind === "exam" ? `Examination · ${item.topic_name}` : `Practice · ${item.topic_name}`}
                {item.correct === 1 ? <span className="good"> · correct</span> : null}
                {item.correct === 0 ? <span className="bad"> · to revisit</span> : null}
                {item.score !== undefined ? ` · ${item.score}/${item.total}` : ""}
              </span>
              <span>{when(item.created_at)}</span>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function ChildExams({ child }) {
  return (
    <div>
      <p className="kicker">Grade {child.student.grade}</p>
      <h1>Examinations</h1>
      <p className="lede">Scores for each term paper. The memorandum stays with the student and the teacher.</p>
      <div className="cards">
        {child.exams.map((paper) => (
          <article key={paper.id} className="card">
            <strong>Term {paper.term}</strong>
            <span>{paper.score === null ? "Not written yet" : `${paper.score} / ${paper.total}`}</span>
            {paper.submitted_at ? <span> · {when(paper.submitted_at)}</span> : null}
          </article>
        ))}
      </div>
    </div>
  );
}
