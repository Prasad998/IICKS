import { categoryColor, pct } from "../lib/format";

export default function SimilarTicketRow({ ticket }) {
  return (
    <div className="row-item" style={{ borderLeftColor: categoryColor(ticket.category) }}>
      <div className="row-top">
        <span className="row-id">{ticket.ticket_id}</span>
        <span className="row-score">{pct(ticket.similarity)} match</span>
      </div>
      <p className="row-title">{ticket.description}</p>
      <p className="row-sub">Resolution: {ticket.resolution}</p>
    </div>
  );
}
