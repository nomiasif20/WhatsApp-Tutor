import { useEffect, useState } from "react";
import { api } from "../api";
import Shell from "../Shell";

const ROLES = [
  { id: "student", label: "Student" },
  { id: "teacher", label: "Teacher" },
  { id: "parent", label: "Parent" },
  { id: "admin", label: "Administrator" },
];

export default function Admin({ person, onLeave }) {
  const [section, setSection] = useState("users");
  const sections = [
    { id: "users", label: "Accounts" },
    { id: "whatsapp", label: "WhatsApp" },
  ];
  return (
    <Shell person={person} onLeave={onLeave} section={section} setSection={setSection} sections={sections} meta={section === "whatsapp" ? "WhatsApp" : "Accounts"}>
      {section === "users" ? <Users actorId={person.id} /> : <WhatsAppLine />}
    </Shell>
  );
}

function Users({ actorId }) {
  const [users, setUsers] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selected, setSelected] = useState(null);

  function load() {
    return api("/api/admin/users").then((data) => setUsers(data.users));
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
  }, []);

  const parents = (users || []).filter((user) => user.role === "parent" && user.active);

  return (
    <div className="stack">
      <div>
        <p className="kicker">Administrator</p>
        <h1>Accounts</h1>
        <p className="lede">Create a student, teacher, parent, or another administrator. Each person signs in with the username and password you set.</p>
      </div>
      {error ? <p className="bad">{error}</p> : null}
      {notice ? <p>{notice}</p> : null}
      <div className="split">
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Username</th>
                <th>Role</th>
                <th>Detail</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(users || []).map((user) => (
                <tr key={user.id} className="button" onClick={() => { setSelected(user); setNotice(""); }}>
                  <td><strong>{user.name}</strong></td>
                  <td>{user.username}</td>
                  <td>{labelFor(user.role)}</td>
                  <td>{detailFor(user)}</td>
                  <td>{user.active ? "Active" : "Inactive"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!users ? <p>Loading accounts…</p> : null}
        </div>
        <CreateAccount parents={parents} onCreated={async (user) => {
          setNotice(`${user.name} can sign in as ${user.username}.`);
          setError("");
          await load();
        }} onError={setError} />
      </div>
      {selected ? (
        <EditAccount
          user={selected}
          parents={parents}
          isSelf={selected.id === actorId}
          onSaved={async (updated) => {
            setNotice(`${updated.name} was updated.`);
            setSelected(updated);
            await load();
          }}
          onError={setError}
          onClose={() => setSelected(null)}
        />
      ) : null}
    </div>
  );
}

function CreateAccount({ parents, onCreated, onError }) {
  const [form, setForm] = useState({
    name: "",
    username: "",
    password: "",
    role: "student",
    grade: "8",
    parent_id: "",
    phone: "",
  });
  const [busy, setBusy] = useState(false);

  function set(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    onError("");
    try {
      const created = await api("/api/admin/users", {
        method: "POST",
        json: {
          ...form,
          grade: form.role === "student" ? Number(form.grade) : null,
          parent_id: form.role === "student" ? form.parent_id : "",
          phone: form.role === "student" ? form.phone : "",
        },
      });
      setForm({ name: "", username: "", password: "", role: form.role, grade: form.grade, parent_id: "", phone: "" });
      await onCreated(created);
    } catch (err) {
      onError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel" onSubmit={submit}>
      <h2>New account</h2>
      <label className="field">
        <span>Full name</span>
        <input value={form.name} onChange={(event) => set("name", event.target.value)} required />
      </label>
      <label className="field">
        <span>Username</span>
        <input value={form.username} autoComplete="off" onChange={(event) => set("username", event.target.value)} required />
      </label>
      <label className="field">
        <span>Password</span>
        <input type="password" autoComplete="new-password" value={form.password} onChange={(event) => set("password", event.target.value)} required />
      </label>
      <label className="field">
        <span>Role</span>
        <select value={form.role} onChange={(event) => set("role", event.target.value)}>
          {ROLES.map((role) => <option key={role.id} value={role.id}>{role.label}</option>)}
        </select>
      </label>
      {form.role === "student" ? (
        <>
          <label className="field">
            <span>Grade</span>
            <select value={form.grade} onChange={(event) => set("grade", event.target.value)}>
              <option value="7">Grade 7</option>
              <option value="8">Grade 8</option>
              <option value="9">Grade 9</option>
            </select>
          </label>
          <label className="field">
            <span>Parent</span>
            <select value={form.parent_id} onChange={(event) => set("parent_id", event.target.value)}>
              <option value="">No parent linked yet</option>
              {parents.map((parent) => <option key={parent.id} value={parent.id}>{parent.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span>WhatsApp number</span>
            <input value={form.phone} placeholder="27821234567" onChange={(event) => set("phone", event.target.value)} />
          </label>
        </>
      ) : null}
      <button className="primary" disabled={busy}>Create account</button>
    </form>
  );
}

function EditAccount({ user, parents, isSelf, onSaved, onError, onClose }) {
  const [name, setName] = useState(user.name);
  const [grade, setGrade] = useState(String(user.grade || 8));
  const [parentId, setParentId] = useState(user.parent_id || "");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState(user.phone || "");
  const [active, setActive] = useState(Boolean(user.active));
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setName(user.name);
    setGrade(String(user.grade || 8));
    setParentId(user.parent_id || "");
    setPassword("");
    setPhone(user.phone || "");
    setActive(Boolean(user.active));
  }, [user]);

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    onError("");
    try {
      const updated = await api(`/api/admin/users/${user.id}`, {
        method: "PATCH",
        json: {
          name,
          active,
          password,
          grade: user.role === "student" ? Number(grade) : null,
          parent_id: user.role === "student" ? parentId : "",
          clear_parent: user.role === "student" && !parentId,
          phone: user.role === "student" ? phone : "",
        },
      });
      await onSaved(updated);
    } catch (err) {
      onError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel" onSubmit={save}>
      <div className="row">
        <h2>{user.name}</h2>
        <button className="quiet" type="button" onClick={onClose}>Close</button>
      </div>
      <p className="meta">{labelFor(user.role)} · {user.username}</p>
      <label className="field">
        <span>Full name</span>
        <input value={name} onChange={(event) => setName(event.target.value)} required />
      </label>
      {user.role === "student" ? (
        <>
          <label className="field">
            <span>Grade</span>
            <select value={grade} onChange={(event) => setGrade(event.target.value)}>
              <option value="7">Grade 7</option>
              <option value="8">Grade 8</option>
              <option value="9">Grade 9</option>
            </select>
          </label>
          <label className="field">
            <span>Parent</span>
            <select value={parentId} onChange={(event) => setParentId(event.target.value)}>
              <option value="">No parent linked</option>
              {parents.map((parent) => <option key={parent.id} value={parent.id}>{parent.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span>WhatsApp number</span>
            <input value={phone} placeholder="27821234567" onChange={(event) => setPhone(event.target.value)} />
          </label>
        </>
      ) : null}
      <label className="field">
        <span>New password</span>
        <input type="password" autoComplete="new-password" value={password} placeholder="Leave blank to keep the current password" onChange={(event) => setPassword(event.target.value)} />
      </label>
      <label className="check">
        <input type="checkbox" checked={active} disabled={isSelf} onChange={(event) => setActive(event.target.checked)} />
        <span>{isSelf ? "This is the account you are using" : "Account is active"}</span>
      </label>
      <button className="primary" disabled={busy}>{busy ? "Saving…" : "Save changes"}</button>
    </form>
  );
}

function labelFor(role) {
  return ROLES.find((item) => item.id === role)?.label || role;
}

function detailFor(user) {
  if (user.role !== "student") return "—";
  const bits = [`Grade ${user.grade}`];
  if (user.parent_name) bits.push(user.parent_name);
  if (user.phone) bits.push(`+${user.phone}`);
  return bits.join(" · ");
}

function WhatsAppLine() {
  const [form, setForm] = useState(null);
  const [token, setToken] = useState("");
  const [secret, setSecret] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/admin/whatsapp").then(setForm).catch((err) => setError(err.message));
  }, []);

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const saved = await api("/api/admin/whatsapp", {
        method: "PUT",
        json: {
          phone_number_id: form.phone_number_id,
          verify_token: form.verify_token,
          token,
          app_secret: secret,
        },
      });
      setForm(saved);
      setToken("");
      setSecret("");
      setNotice(saved.token_set && saved.phone_number_id ? "The WhatsApp line is ready." : "The details were saved.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!form) return error ? <p className="bad">{error}</p> : <p>Loading the WhatsApp line…</p>;
  const ready = form.token_set && form.phone_number_id;
  return (
    <div className="stack">
      <div>
        <p className="kicker">Administrator</p>
        <h1>WhatsApp</h1>
        <p className="lede">
          Students message the business number and receive the topic, a worked example, and similar questions.
          Link each student number on their account. The desk chat uses the same replies.
        </p>
      </div>
      {error ? <p className="bad">{error}</p> : null}
      {notice ? <p>{notice}</p> : null}
      <p>{ready ? "The line can send replies." : "Add the phone number ID and access token before live messages can be sent."}</p>
      <form className="panel stack" onSubmit={save}>
        <label className="field">
          <span>Phone number ID</span>
          <input value={form.phone_number_id} onChange={(event) => setForm({ ...form, phone_number_id: event.target.value })} />
        </label>
        <label className="field">
          <span>Access token</span>
          <input type="password" autoComplete="new-password" value={token} placeholder={form.token_set ? "Saved. Enter a new token to replace it." : "Permanent token from the business account"} onChange={(event) => setToken(event.target.value)} />
        </label>
        <label className="field">
          <span>App secret</span>
          <input type="password" autoComplete="new-password" value={secret} placeholder={form.secret_set ? "Saved. Enter a new secret to replace it." : "Used to check that messages come from WhatsApp"} onChange={(event) => setSecret(event.target.value)} />
        </label>
        <label className="field">
          <span>Verify token</span>
          <input value={form.verify_token} onChange={(event) => setForm({ ...form, verify_token: event.target.value })} />
        </label>
        <p className="meta">Webhook path: {form.webhook_path}. Meta needs this on a public https address. This desk is also available at {window.location.origin}{form.webhook_path}.</p>
        <button className="primary" disabled={busy}>{busy ? "Saving…" : "Save line"}</button>
      </form>
      <GrokKey />
    </div>
  );
}

function GrokKey() {
  const [ready, setReady] = useState(false);
  const [key, setKey] = useState("");
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api("/api/admin/grok").then((data) => {
      setSaved(Boolean(data.key_set));
      setReady(true);
    }).catch((err) => setError(err.message));
  }, []);

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const data = await api("/api/admin/grok", { method: "PUT", json: { api_key: key } });
      setSaved(Boolean(data.key_set));
      setKey("");
      setNotice(data.key_set ? "Grok can reply to conversation in the chat." : "No key is saved yet.");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!ready) return error ? <p className="bad">{error}</p> : null;
  return (
    <form className="panel stack" onSubmit={save}>
      <h2>Conversation</h2>
      <p className="lede">Grok replies when a student is chatting rather than asking for a calculation. A sum such as add 2+3 is still answered from the curriculum.</p>
      {error ? <p className="bad">{error}</p> : null}
      {notice ? <p>{notice}</p> : null}
      <p>{saved ? "A key is saved. Conversation in the chat uses it." : "Add an xAI or Groq key before conversational replies can be sent."}</p>
      <label className="field">
        <span>Grok API key</span>
        <input type="password" autoComplete="new-password" value={key} placeholder={saved ? "Saved. Enter a new key to replace it." : "xAI key, or a Groq key starting with gsk_"} onChange={(event) => setKey(event.target.value)} />
      </label>
      <button className="primary" disabled={busy || !key.trim()}>{busy ? "Saving…" : "Save key"}</button>
    </form>
  );
}
