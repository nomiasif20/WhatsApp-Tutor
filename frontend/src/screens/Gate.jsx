import { useState } from "react";
import { api } from "../api";

export default function Gate({ onEnter }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const session = await api("/api/session", {
        method: "POST",
        json: { username, password },
      });
      onEnter(session);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="signin">
      <form onSubmit={submit}>
        <p className="kicker">Mathematics</p>
        <h1>Sign in</h1>
        <p className="lede">Use the username and password an administrator gave you.</p>
        <label className="field">
          <span>Username</span>
          <input
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error ? <p className="bad">{error}</p> : null}
        <button className="primary" type="submit" disabled={busy || !username.trim() || !password}>
          {busy ? "Checking…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
