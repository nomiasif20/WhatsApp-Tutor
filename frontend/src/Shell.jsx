const ROLE = { student: "Student", teacher: "Teacher", parent: "Parent", admin: "Administrator" };

export default function Shell({ person, onLeave, section, setSection, sections, meta, children }) {
  return (
    <div className="app">
      <aside className="side">
        <div className="brand">
          <span className="role">{ROLE[person.role] || person.role}</span>
          <strong>{person.name}</strong>
          {meta ? <span className="meta">{meta}</span> : null}
        </div>
        <nav className="nav" aria-label="Sections">
          {sections.map((item) => (
            <button
              key={item.id}
              className={section === item.id ? "on" : ""}
              onClick={() => setSection(item.id)}
              type="button"
              aria-current={section === item.id ? "page" : undefined}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <button className="text leave" type="button" onClick={onLeave}>Sign out</button>
      </aside>
      <div className="workspace">
        <main>{children}</main>
      </div>
    </div>
  );
}
