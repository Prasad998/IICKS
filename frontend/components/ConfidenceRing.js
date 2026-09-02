import { useEffect, useState } from "react";
import { pct } from "../lib/format";

export default function ConfidenceRing({ value }) {
  const radius = 38;
  const circumference = 2 * Math.PI * radius;
  const target = Math.max(0, Math.min(1, value || 0));
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    setOffset(circumference);
    const frame = requestAnimationFrame(() => setOffset(circumference * (1 - target)));
    return () => cancelAnimationFrame(frame);
  }, [target, circumference]);

  return (
    <div className="ring-wrap">
      <svg width="92" height="92" viewBox="0 0 92 92">
        <circle className="ring-track" cx="46" cy="46" r={radius} />
        <circle
          className="ring-value"
          cx="46"
          cy="46"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-label">{pct(target)}</div>
    </div>
  );
}
