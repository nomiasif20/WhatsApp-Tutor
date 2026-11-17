const ROLE = { student: "Student", teacher: "Teacher", parent: "Parent", admin: "Administrator" };

export default function Shell({ person, onLeave, section, setSection, sections, meta, children }) {
  return (
    <div>
      <header className="top">
        <div className="who">
          <span className="role">{ROLE[person.role] || person.role}</span>
          <strong>{person.name}</strong>
          {meta ? <span className="meta">{meta}</span> : null}
        </div>
        <nav className="nav">
          {sections.map((item) => (
            <button
              key={item.id}
              className={section === item.id ? "on" : ""}
              onClick={() => setSection(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
        <button className="text leave" type="button" onClick={onLeave}>Sign out</button>
      </header>
      <main>{children}</main>
    </div>
  );
}
