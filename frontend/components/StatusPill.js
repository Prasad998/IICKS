export default function StatusPill({ label, state }) {
  return (
    <span className={`status-pill ${state}`}>
      <span className="status-dot" />
      {label}
    </span>
  );
}
