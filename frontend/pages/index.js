import { useCallback, useEffect, useState } from "react";
import Head from "next/head";
import StatusPill from "../components/StatusPill";
import ConfidenceRing from "../components/ConfidenceRing";
import SimilarTicketRow from "../components/SimilarTicketRow";
import ArticleRow from "../components/ArticleRow";
import SkeletonRows from "../components/SkeletonRows";
import { GATEWAY_BASE, fetchJson } from "../lib/api";
import { categoryColor } from "../lib/format";

const FALLBACK_SAMPLES = [
  { description: "Unable to login to SAP after password reset", expected_category: "Authentication" },
  { description: "VPN disconnects every 10 minutes on Cisco AnyConnect", expected_category: "Network" },
  { description: "Payroll batch job failed overnight with database timeout", expected_category: "Application" },
];

function gatewayStatusLabel(state) {
  if (state === "checking") return "Gateway — checking";
  if (state === "online") return "Gateway online";
  return "Gateway offline";
}

function inferenceStatusLabel(state, detail) {
  if (state === "checking") return "Inference — checking";
  if (state === "unknown") return "Inference — unknown";
  if (state === "online") return detail ? `Inference online · ${detail}` : "Inference online";
  return "Inference offline";
}

export default function Home() {
  const [description, setDescription] = useState(FALLBACK_SAMPLES[0].description);
  const [samples, setSamples] = useState(FALLBACK_SAMPLES);
  const [activeSample, setActiveSample] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [resultVersion, setResultVersion] = useState(0);
  const [error, setError] = useState(null);
  const [gatewayStatus, setGatewayStatus] = useState("checking");
  const [inferenceStatus, setInferenceStatus] = useState("checking");
  const [healthDetail, setHealthDetail] = useState("");

  const checkHealth = useCallback(async () => {
    setGatewayStatus("checking");
    setInferenceStatus("checking");
    try {
      const health = await fetchJson(`${GATEWAY_BASE}/health`);
      setGatewayStatus("online");
      setInferenceStatus(health.status === "ok" ? "online" : "offline");
      setHealthDetail(`${health.incidents_loaded} tickets indexed · ${health.model_backend}`);
    } catch (err) {
      if (err.kind === "network") {
        setGatewayStatus("offline");
        setInferenceStatus("unknown");
        setHealthDetail("");
      } else {
        // The gateway answered (so it's up), it just couldn't reach the inference service.
        setGatewayStatus("online");
        setInferenceStatus("offline");
        setHealthDetail("");
      }
    }
  }, []);

  useEffect(() => {
    checkHealth();

    fetchJson(`${GATEWAY_BASE}/api/examples`)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          setSamples(data);
        }
      })
      .catch(() => {
        /* keep FALLBACK_SAMPLES if the gateway isn't reachable yet */
      });
  }, [checkHealth]);

  const runAnalysis = async () => {
    if (description.trim().length < 5) {
      setError({
        title: "Ticket text is too short",
        detail: "Enter at least 5 characters describing the incident.",
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await fetchJson(`${GATEWAY_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, top_k: 5 }),
      });
      setResult(data);
      setResultVersion((version) => version + 1);
    } catch (err) {
      if (err.kind === "network") {
        setError({
          title: "Can't reach the gateway",
          detail: `No response from ${GATEWAY_BASE}. Start it with "mvn spring-boot:run" from spring-api/.`,
        });
      } else {
        setError({
          title: `Gateway returned an error (HTTP ${err.status})`,
          detail: "The gateway is running, but the inference service at :8000 may be down or failed to process this request. Check its terminal output.",
        });
      }
      checkHealth();
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>IICKS — Incident Categorization & Knowledge Search</title>
      </Head>

      <div className="shell">
        <header className="topbar">
          <div className="brand">
            <h1>IICKS</h1>
            <p>
              Incident Categorization & Knowledge Search — routes a ticket through the Spring gateway to the
              Python inference service for classification and retrieval.
            </p>
          </div>
          <div className="status-row">
            <StatusPill label={gatewayStatusLabel(gatewayStatus)} state={gatewayStatus} />
            <StatusPill
              label={inferenceStatusLabel(inferenceStatus, healthDetail)}
              state={inferenceStatus === "unknown" ? "checking" : inferenceStatus}
            />
          </div>
        </header>

        <div className="workspace">
          <div className="panel">
            <h2>Incoming ticket</h2>
            <p className="hint">Describe the issue the way a user would report it.</p>
            <textarea
              className="ticket-input"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />

            <div className="sample-list">
              <span className="sample-list-label">Sample tickets</span>
              {samples.map((sample, index) => (
                <button
                  key={sample.description}
                  className={`sample-chip ${index === activeSample ? "active" : ""}`}
                  onClick={() => {
                    setActiveSample(index);
                    setDescription(sample.description);
                  }}
                >
                  {sample.description}
                </button>
              ))}
            </div>

            <button className="analyze-btn" onClick={runAnalysis} disabled={loading}>
              {loading && <span className="spinner" />}
              {loading ? "Analyzing" : "Analyze ticket"}
            </button>
          </div>

          <div className="panel">
            {error && (
              <div className="error-banner">
                <div>
                  <strong>{error.title}</strong>
                  <p>{error.detail}</p>
                </div>
              </div>
            )}

            <div className="verdict">
              {result ? (
                <div className="verdict-inner" key={resultVersion}>
                  <ConfidenceRing value={result.confidence} />
                  <div className="verdict-text">
                    <p className="category-name">
                      <span className="category-dot" style={{ background: categoryColor(result.category) }} />
                      {result.category}
                    </p>
                    <p className="category-sub">
                      {result.cached ? "Served from cache · " : ""}
                      model: {result.model_backend}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="verdict-placeholder">Run an analysis to see the predicted category and confidence.</p>
              )}
            </div>

            <div className="result-columns" key={`cols-${resultVersion}-${loading}`}>
              <div>
                <h3>Similar historical tickets</h3>
                {loading ? (
                  <SkeletonRows />
                ) : result && result.similar_tickets.length > 0 ? (
                  <div className="row-list">
                    {result.similar_tickets.map((ticket) => (
                      <SimilarTicketRow key={ticket.ticket_id} ticket={ticket} />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">{result ? "No similar tickets found." : "Results will appear here."}</div>
                )}
              </div>
              <div>
                <h3>Recommended knowledge articles</h3>
                {loading ? (
                  <SkeletonRows />
                ) : result && result.knowledge_articles.length > 0 ? (
                  <div className="row-list">
                    {result.knowledge_articles.map((article) => (
                      <ArticleRow key={article.article_id} article={article} />
                    ))}
                  </div>
                ) : (
                  <div className="empty-state">{result ? "No articles matched." : "Results will appear here."}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
