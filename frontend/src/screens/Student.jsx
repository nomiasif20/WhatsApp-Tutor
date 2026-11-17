import { useEffect, useRef, useState } from "react";
import { api, percent, when } from "../api";
import Shell from "../Shell";

const SECTIONS = [
  { id: "ask", label: "Ask" },
  { id: "chat", label: "WhatsApp" },
  { id: "syllabus", label: "Syllabus" },
  { id: "exams", label: "Examinations" },
  { id: "progress", label: "Progress" },
];

export default function Student({ person, onLeave }) {
  const [section, setSection] = useState("ask");
  const [progress, setProgress] = useState(null);
  const refresh = () => api("/api/progress").then(setProgress).catch(() => {});
  useEffect(() => { refresh(); }, []);

  return (
    <Shell person={person} onLeave={onLeave} section={section} setSection={setSection} sections={SECTIONS} meta={`Grade ${person.grade} · Mathematics`}>
      {section === "ask" && <Ask onPractised={refresh} />}
      {section === "chat" && <WhatsApp onPractised={refresh} />}
      {section === "syllabus" && <Syllabus progress={progress} onPractised={refresh} />}
      {section === "exams" && <Exams grade={person.grade} onDone={refresh} />}
      {section === "progress" && <Progress progress={progress} />}
    </Shell>
  );
}

function Ask({ onPractised }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function submit(event, concept) {
    event?.preventDefault();
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      let data;
      if (file && !concept) {
        const body = new FormData();
        body.set("question", text);
        body.set("file", file);
        data = await api("/api/ask", { method: "POST", body });
      } else {
        data = await api("/api/ask", { method: "POST", json: { question: text, concept: concept || "" } });
      }
      setResult(data);
      onPractised();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <p className="kicker">Term 4 is underway</p>
        <h1>Ask a question</h1>
        <p className="lede">Write the question and press Enter. You get the answer, a worked example, and similar questions.</p>
      </div>
      <form className="composer" onSubmit={(event) => submit(event)}>
        <label className="sr" htmlFor="question">Question</label>
        <textarea
          id="question"
          value={text}
          placeholder="Write the question, then press Enter. A photo or PDF can be attached as well."
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (text.trim() || file) submit(event);
            }
          }}
        />
        <div className="row">
          <label className="file quiet">
            <span>{file ? file.name : "Attach a photo or PDF"}</span>
            <input type="file" accept=".pdf,image/png,image/jpeg,image/webp" onChange={(event) => setFile(event.target.files?.[0] || null)} />
          </label>
          <button className="primary" type="submit" disabled={busy || (!text.trim() && !file)}>
            {busy ? "Reading the syllabus…" : "Send"}
          </button>
        </div>
        {error ? <p className="bad">{error}</p> : null}
      </form>
      {result ? <Lesson data={result} onConcept={(concept) => submit(null, concept)} onPractised={onPractised} /> : null}
    </div>
  );
}

function WhatsApp({ onPractised }) {
  const [messages, setMessages] = useState(null);
  const [phone, setPhone] = useState("");
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [earlier, setEarlier] = useState(0);
  const [loadingEarlier, setLoadingEarlier] = useState(false);
  const scroller = useRef(null);
  const openedEarlier = useRef(false);

  useEffect(() => {
    let stop = false;
    function pull() {
      api("/api/chat")
        .then((data) => {
          if (stop) return;
          setMessages((current) => mergeMessages(current, data.messages));
          setPhone(data.phone || "");
          if (!openedEarlier.current) setEarlier(data.earlier || 0);
        })
        .catch((err) => {
          if (!stop) setError(err.message);
        });
    }
    pull();
    const timer = setInterval(pull, 4000);
    return () => {
      stop = true;
      clearInterval(timer);
    };
  }, []);

  const lastId = messages?.[messages.length - 1]?.id;
  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = scroller.current.scrollHeight;
  }, [lastId]);

  async function loadEarlier() {
    if (!messages?.length || loadingEarlier) return;
    const pane = scroller.current;
    const beforeHeight = pane ? pane.scrollHeight : 0;
    setLoadingEarlier(true);
    openedEarlier.current = true;
    try {
      const data = await api(`/api/chat?before=${messages[0].id}`);
      setMessages((current) => mergeMessages(data.messages, current));
      setEarlier(data.earlier || 0);
      requestAnimationFrame(() => {
        if (pane) pane.scrollTop = pane.scrollHeight - beforeHeight;
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingEarlier(false);
    }
  }

  async function send(event) {
    event.preventDefault();
    const body = text.trim();
    if (!body || busy) return;
    setBusy(true);
    setError("");
    setText("");
    try {
      const data = await api("/api/chat", { method: "POST", json: { text: body } });
      setMessages((current) => mergeMessages(current, data.messages));
      setEarlier(data.earlier || 0);
      onPractised();
    } catch (err) {
      setError(err.message);
      setText(body);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack">
      <div>
        <p className="kicker">Chat</p>
        <h1>WhatsApp</h1>
        <p className="lede">
          {phone
            ? `This chat is linked to +${phone}. A question on that WhatsApp number is saved here and answered on the phone.`
            : "This chat keeps the conversation. An administrator can add a WhatsApp number so a question from the phone is saved here too."}
        </p>
      </div>
      <div className="thread" ref={scroller}>
        {earlier > 0 ? (
          <button className="quiet earlier" type="button" onClick={loadEarlier} disabled={loadingEarlier}>
            {loadingEarlier ? "Loading…" : "Earlier messages"}
          </button>
        ) : null}
        {messages && messages.length === 0 ? (
          <p className="meta">Send a question, or reply help. You can also send progress or paper.</p>
        ) : null}
        {(messages || []).map((message) => (
          <div key={message.id} className={message.direction === "in" ? "bubble mine" : "bubble theirs"}>
            <span>{message.body}</span>
            <small>{message.source === "whatsapp" ? "WhatsApp · " : ""}{chatWhen(message.created_at)}</small>
          </div>
        ))}
        {!messages ? <p className="meta">Loading the chat…</p> : null}
      </div>
      <form className="chat-compose" onSubmit={send}>
        <input
          value={text}
          placeholder="Write a question or an answer"
          onChange={(event) => setText(event.target.value)}
        />
        <button className="primary" disabled={busy || !text.trim()}>{busy ? "Sending…" : "Send"}</button>
      </form>
      {error ? <p className="bad">{error}</p> : null}
    </div>
  );
}

function mergeMessages(current, incoming) {
  const byId = new Map((current || []).map((message) => [message.id, message]));
  for (const message of incoming || []) byId.set(message.id, message);
  return [...byId.values()].sort((a, b) => a.id - b.id);
}

function chatWhen(value) {
  if (!value) return "";
  const date = new Date(String(value).replace(" ", "T"));
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString("en-ZA", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function Lesson({ data, onConcept, onPractised }) {
  const topic = data.topic;
  return (
    <article className="sheet stack">
      <div>
        <p className="kicker">
          {data.confidence ? `${data.confidence} confidence · ` : ""}
          Grade {topic.grade} · Term {topic.term} · {topic.content_area}
        </p>
        <h2>{topic.name}</h2>
        <p className="reason">{data.reason || topic.note}</p>
        {data.read_from_file ? <p>Text was read from the attached file and used to place the topic.</p> : null}
        {data.attachment && /\.(png|jpe?g|webp)$/i.test(data.attachment) ? <img className="shot" src={data.attachment} alt="Attached work" /> : null}
        {data.alternatives?.length ? (
          <div className="chips">
            {data.alternatives.map((item) => (
              <button key={item.id} type="button" onClick={() => onConcept?.(item.concept)}>
                Use {item.name} instead
              </button>
            ))}
          </div>
        ) : null}
      </div>
      {data.direct ? <Worked title="Your question" item={data.direct} reveal /> : <Method steps={data.steps} />}
      <Worked title="Example" item={data.example} reveal />
      <section>
        <h3>Similar questions</h3>
        {data.similar?.map((item) => <PracticeItem key={item.id} item={item} onDone={onPractised} />)}
      </section>
      <section>
        <h3>Watch for</h3>
        <ul>{data.mistakes?.map((item) => <li key={item}>{item}</li>)}</ul>
      </section>
      <Sources sources={data.sources} />
    </article>
  );
}

function Method({ steps }) {
  if (!steps?.length) return null;
  return (
    <section>
      <h3>Method</h3>
      <ol className="steps">{steps.map((step) => <li key={step}>{step}</li>)}</ol>
    </section>
  );
}

function Worked({ title, item, reveal = false }) {
  const [open, setOpen] = useState(reveal);
  if (!item) return null;
  return (
    <section>
      <h3>{title}</h3>
      {item.prompt ? <p className="prompt">{item.prompt}</p> : null}
      <ol className="steps">{item.steps.map((step) => <li key={step}>{step}</li>)}</ol>
      {open ? <p className="final"><span>Answer</span> {item.answer}</p> : (
        <button className="quiet" type="button" onClick={() => setOpen(true)}>Show the answer</button>
      )}
    </section>
  );
}

function PracticeItem({ item, onDone }) {
  const [value, setValue] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function check(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api(`/api/practice/${item.id}/answer`, { method: "POST", json: { answer: value } });
      setResult(data);
      onDone?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="practice" onSubmit={check}>
      <p className="prompt">{item.prompt}</p>
      <div className="answer-row">
        <input aria-label="Your answer" value={value} disabled={!!result} onChange={(event) => setValue(event.target.value)} />
        {result ? null : <button className="primary" disabled={busy || !value.trim()}>Check</button>}
      </div>
      {error ? <p className="bad">{error}</p> : null}
      {result ? (
        <div className={result.correct ? "verdict good" : "verdict bad"}>
          <strong>{result.correct ? "Correct." : "Not yet."}</strong>
          <span> Answer: {result.answer}</span>
          <ol>{result.steps.map((step) => <li key={step}>{step}</li>)}</ol>
        </div>
      ) : null}
    </form>
  );
}

function Sources({ sources }) {
  return (
    <section>
      <h3>From the trained curriculum</h3>
      {!sources?.length ? <p>No close passage was found in the trained documents for this wording.</p> : null}
      {sources?.map((source) => (
        <blockquote key={`${source.title}-${source.page}-${source.excerpt.slice(0, 24)}`}>
          <p>{source.excerpt}</p>
          <footer>{source.title}{source.page ? ` · page ${source.page}` : ""}</footer>
        </blockquote>
      ))}
    </section>
  );
}

function Syllabus({ progress, onPractised }) {
  const [terms, setTerms] = useState([]);
  const [current, setCurrent] = useState(4);
  const [lesson, setLesson] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/syllabus").then((data) => {
      setTerms(data.terms);
      setCurrent(data.current_term);
    });
  }, []);

  async function openTopic(topic) {
    setBusy(true);
    try {
      const data = await api(`/api/lesson?concept=${topic.concept}`);
      setLesson(data);
    } finally {
      setBusy(false);
    }
  }

  const mastery = new Map((progress?.terms || []).flatMap((term) => term.topics.map((topic) => [topic.id, topic])));

  return (
    <div className="layout">
      <div>
        <p className="kicker">Grade syllabus</p>
        <h1>Topics by term</h1>
        <p className="lede">Term {current} is the current term. Choose a topic for an example and two similar questions.</p>
        <div className="terms">
          {terms.map((term) => (
            <section key={term.term} className="panel term">
              <h3>Term {term.term} {term.term === current ? <span className="kicker">Current</span> : null}</h3>
              {term.topics.map((topic) => {
                const stats = mastery.get(topic.id);
                return (
                  <button key={topic.id} className={lesson?.topic?.id === topic.id ? "topic on" : "topic"} type="button" onClick={() => openTopic(topic)}>
                    <strong>{topic.name}</strong>
                    <small>{topic.note}{stats?.attempted ? ` · ${percent(stats.accuracy)} from ${stats.attempted} answers` : ""}</small>
                  </button>
                );
              })}
            </section>
          ))}
        </div>
      </div>
      <div>
        {busy ? <p>Preparing the example…</p> : null}
        {lesson ? <Lesson data={lesson} onPractised={onPractised} /> : <p className="lede">The example opens here.</p>}
      </div>
    </div>
  );
}

function Exams({ grade, onDone }) {
  const [papers, setPapers] = useState([]);
  const [open, setOpen] = useState(null);

  function load() {
    api("/api/exams").then((data) => setPapers(data.papers || []));
  }
  useEffect(load, []);

  if (open) {
    return <Paper paperId={open} onClose={() => { setOpen(null); load(); onDone(); }} />;
  }

  return (
    <div>
      <p className="kicker">Grade {grade}</p>
      <h1>Examinations</h1>
      <p className="lede">Each term paper is 50 marks. The marked script, including the memorandum, is shown after you submit. Parents see the score.</p>
      <div className="cards">
        {papers.map((paper) => (
          <button key={paper.id} className="card" type="button" onClick={() => setOpen(paper.id)}>
            <strong>Term {paper.term}</strong>
            <span>{paper.score === null ? "Not written" : `${paper.score}/${paper.total} · ${when(paper.submitted_at)}`}</span>
            <span> · {paper.minutes} minutes</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function Paper({ paperId, onClose }) {
  const [paper, setPaper] = useState(null);
  const [answers, setAnswers] = useState({});
  const [marked, setMarked] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api(`/api/exams/${paperId}`).then(setPaper);
  }, [paperId]);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api(`/api/exams/${paperId}/submit`, { method: "POST", json: { answers } });
      setMarked(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!paper) return <p>Opening the paper…</p>;
  const questions = marked?.questions || paper.questions;

  return (
    <form onSubmit={submit}>
      <div className="row">
        <button className="quiet" type="button" onClick={onClose}>Back to the term list</button>
        <button className="quiet" type="button" onClick={() => window.print()}>Print</button>
      </div>
      <article className="paper">
        <header className="paper-top">
          <div>
            <p className="kicker">Mathematics</p>
            <h1>Grade {paper.grade} · Term {paper.term}</h1>
          </div>
          <div>
            <p>{paper.total} marks</p>
            <p>{paper.minutes} minutes</p>
          </div>
        </header>
        <ul>{paper.instructions.map((line) => <li key={line}>{line}</li>)}</ul>
        {paper.latest?.score !== undefined && paper.latest?.score !== null && !marked ? (
          <p>Previous result: {paper.latest.score}/{paper.latest.total} on {when(paper.latest.submitted_at)}. A new submission becomes the result parents and teachers see.</p>
        ) : null}
        {marked ? <p className="final"><span>Result</span> {marked.score}/{marked.total}</p> : null}
        {questions.map((question, index) => (
          <div className="question" key={question.id}>
            <div className="q-head">
              <p className="prompt"><strong>{index + 1}.</strong> {question.prompt}</p>
              <span className="marks">{question.marks} {question.marks === 1 ? "mark" : "marks"}</span>
            </div>
            {marked ? (
              <div className={question.correct ? "verdict good" : "verdict bad"}>
                <strong>{question.correct ? "Correct" : "Incorrect"} · {question.awarded}/{question.marks}</strong>
                <p>Your answer: {question.given || "—"}</p>
                <p>Answer: {question.answer}</p>
                <ol>{question.memo?.map((step) => <li key={step}>{step}</li>)}</ol>
              </div>
            ) : (
              <input
                aria-label={`Answer ${index + 1}`}
                value={answers[question.id] || ""}
                onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })}
              />
            )}
          </div>
        ))}
        {error ? <p className="bad">{error}</p> : null}
        {marked ? null : <button className="primary" type="submit" disabled={busy}>{busy ? "Marking…" : "Submit the paper"}</button>}
      </article>
    </form>
  );
}

function Progress({ progress }) {
  if (!progress) return <p>Gathering progress…</p>;
  return (
    <div className="stack">
      <div>
        <p className="kicker">This week</p>
        <h1>Progress</h1>
      </div>
      <div className="stats">
        <div className="stat"><b>{progress.week.questions}</b><span>Questions asked</span></div>
        <div className="stat"><b>{progress.week.practised}</b><span>Answers marked</span></div>
        <div className="stat"><b>{percent(progress.week.accuracy)}</b><span>Accuracy</span></div>
      </div>
      <section className="panel">
        <h2>Focus</h2>
        {progress.focus.length === 0 ? <p>Keep working through the current term.</p> : null}
        {progress.focus.map((item) => (
          <p key={item.id}><strong>{item.name}</strong> · Term {item.term} · {item.reason}</p>
        ))}
      </section>
      {progress.terms.map((term) => (
        <section key={term.term}>
          <h2>Term {term.term}</h2>
          {term.topics.map((topic) => (
            <div className="topic-line" key={topic.id}>
              <span>{topic.name}</span>
              <span>{topic.attempted ? `${topic.correct}/${topic.attempted}` : "Not yet"}</span>
              <div className="track"><span style={{ width: `${Math.round((topic.accuracy || 0) * 100)}%` }} /></div>
            </div>
          ))}
        </section>
      ))}
      <section>
        <h2>Recent questions</h2>
        <ul className="activity">
          {progress.questions.map((item) => (
            <li key={item.id}><span>{item.body}</span><span>{item.topic_name} · {when(item.created_at)}</span></li>
          ))}
        </ul>
      </section>
    </div>
  );
}
