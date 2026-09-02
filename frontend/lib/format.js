export const CATEGORY_COLORS = {
  Authentication: "var(--cat-authentication)",
  Network: "var(--cat-network)",
  Application: "var(--cat-application)",
  Endpoint: "var(--cat-endpoint)",
  Database: "var(--cat-database)",
};

export function categoryColor(category) {
  return CATEGORY_COLORS[category] || "var(--text-muted)";
}

export function pct(value) {
  return `${Math.round((value || 0) * 100)}%`;
}
