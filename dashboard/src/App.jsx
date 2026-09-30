import { useEffect, useState } from "react";
import "./App.css";
import {
  getDeploymentStats,
  getDeployments,
  getDeploymentValidations,
} from "./services/api.js";

export default function App() {
  const [stats, setStats] = useState(null);
  const [latest, setLatest] = useState(null);
  const [validations, setValidations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        // Summary cards: the backend exposes running/in-flight work as
        // 'validating' (and 'pending' for not-yet-started work), so
        // "Running" is their sum. No invented statuses.
        const [statsData, deployments] = await Promise.all([
          getDeploymentStats(),
          getDeployments(),
        ]);

        // The backend returns deployments newest first (id DESC), so the
        // first element is the latest deployment.
        const latestDeployment = deployments[0] || null;

        let validationResults = [];

        if (latestDeployment) {
          validationResults = await getDeploymentValidations(
            latestDeployment.id,
          );
        }

        if (!cancelled) {
          setStats(statsData);
          setLatest(latestDeployment);
          setValidations(validationResults);
          setLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err);
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="dashboard">
        <header className="header">
          <h1>Microservice Deployment Dashboard</h1>
          <p>Deployment monitoring and validation overview</p>
        </header>
        <section className="deployment-card">
          <p className="status-note">Loading deployment data…</p>
        </section>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <header className="header">
          <h1>Microservice Deployment Dashboard</h1>
          <p>Deployment monitoring and validation overview</p>
        </header>
        <section className="deployment-card">
          <p className="status-note error">
            Could not reach the backend API. Is it running on port 8081?
          </p>
          <p className="status-note">{String(error.message || error)}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="header">
        <h1>Microservice Deployment Dashboard</h1>
        <p>Deployment monitoring and validation overview</p>
      </header>

      <section className="summary">
        <div className="card">
          <h3>Total Deployments</h3>
          <h2>{stats?.total ?? "—"}</h2>
        </div>

        <div className="card">
          <h3>Successful</h3>
          <h2>{stats?.success ?? "—"}</h2>
        </div>

        <div className="card">
          <h3>Failed</h3>
          <h2>{stats?.failed ?? "—"}</h2>
        </div>

        <div className="card">
          <h3>Running</h3>
          <h2>{(stats?.validating ?? 0) + (stats?.pending ?? 0)}</h2>
        </div>
      </section>

      <section className="deployment-card">
        <h2>Latest Deployment</h2>

        {latest ? (
          <div className="deployment-info">
            <p>
              <strong>Service:</strong> {latest.serviceName}
            </p>
            <p>
              <strong>Version:</strong> {latest.version}
            </p>
            <p>
              <strong>Environment:</strong> {latest.environment}
            </p>
            <p>
              <strong>Status:</strong> {latest.status}
            </p>
            {latest.startedAt && (
              <p>
                <strong>Started:</strong>{" "}
                {new Date(latest.startedAt).toLocaleString()}
              </p>
            )}
            {latest.completedAt && (
              <p>
                <strong>Completed:</strong>{" "}
                {new Date(latest.completedAt).toLocaleString()}
              </p>
            )}
          </div>
        ) : (
          <p className="status-note">No deployments recorded yet.</p>
        )}

        {latest && (
          <>
            <h3>Pipeline Stage &amp; Validation Checks</h3>

            {/* The backend has no pipeline-stage model (Build/Test/Deploy
                are not tracked), so the original stage boxes are rendered
                as validation checks derived from real data. Overall status
                comes from the deployment itself; check rows come from
                /validations. Nothing here is fabricated. */}
            <div className="stages">
              <div
                className={
                  "stage " +
                  (latest.status === "SUCCESS"
                    ? "success"
                    : latest.status === "FAILED"
                      ? "failure"
                      : "pending")
                }
              >
                <strong>Deployment status</strong>
                <span>{latest.status}</span>
              </div>

              {validations.map((validation) => (
                <div
                  key={validation.id}
                  className={
                    "stage " +
                    (validation.status === "PASS"
                      ? "success"
                      : validation.status === "FAIL"
                        ? "failure"
                        : "pending")
                  }
                >
                  <strong>{validation.type}</strong>
                  <span>
                    {validation.status}
                    {validation.message
                      ? ` — ${validation.message}`
                      : ""}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}
      </section>

      <section className="deployment-card">
        <h2>Validation Results</h2>

        {latest ? (
          validations.length > 0 ? (
            <>
              {/* Finding count = results with status FAIL. Overall status
                  is derived: PASS only when nothing failed. No governance
                  ALLOW/DENY semantics are claimed — the backend does not
                  expose a decision field. */}
              <div className="validation">
                <p>
                  <strong>Validation status:</strong>{" "}
                  {validations.some((v) => v.status === "FAIL")
                    ? "FAIL"
                    : "PASS"}
                </p>
                <p>
                  <strong>Findings:</strong>{" "}
                  {validations.filter((v) => v.status === "FAIL").length}
                </p>
                <p>
                  <strong>Checks recorded:</strong> {validations.length}
                </p>
              </div>

              <div className="validation-rows">
                {validations.map((validation) => (
                  <div className="validation-row" key={validation.id}>
                    <strong>{validation.type}</strong>
                    <span>
                      {validation.status} — {validation.message}
                    </span>
                    {validation.details && (
                      <code>{validation.details}</code>
                    )}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="status-note">
              No validation results recorded for this deployment yet.
            </p>
          )
        ) : (
          <p className="status-note">
            Validation results appear once a deployment exists.
          </p>
        )}
      </section>
    </div>
  );
}
