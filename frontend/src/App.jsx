import { useEffect, useState } from "react";
import { api } from "./api";
import Gate from "./screens/Gate";
import Student from "./screens/Student";
import Teacher from "./screens/Teacher";
import Parent from "./screens/Parent";
import Admin from "./screens/Admin";

const SCREENS = { student: Student, teacher: Teacher, parent: Parent, admin: Admin };

export default function App() {
  const [person, setPerson] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    sessionStorage.removeItem("person");
    const token = sessionStorage.getItem("token");
    if (!token) {
      setReady(true);
      return;
    }
    api("/api/me")
      .then(setPerson)
      .catch(() => sessionStorage.removeItem("token"))
      .finally(() => setReady(true));
  }, []);

  function enter(session) {
    sessionStorage.setItem("token", session.token);
    setPerson(session.person);
  }

  function leave() {
    api("/api/session", { method: "DELETE" }).catch(() => {});
    sessionStorage.removeItem("token");
    setPerson(null);
  }

  if (!ready) return <p className="boot">Loading the desk…</p>;
  if (!person) return <Gate onEnter={enter} />;
  const Screen = SCREENS[person.role] || Student;
  return <Screen person={person} onLeave={leave} />;
}
