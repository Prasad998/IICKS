import { categoryColor, pct } from "../lib/format";

export default function ArticleRow({ article }) {
  return (
    <div className="row-item" style={{ borderLeftColor: categoryColor(article.category) }}>
      <div className="row-top">
        <span className="row-id">{article.article_id}</span>
        <span className="row-score">{pct(article.relevance)} relevance</span>
      </div>
      <p className="row-title">{article.title}</p>
      <p className="row-sub">{article.excerpt}</p>
    </div>
  );
}
