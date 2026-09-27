import {
  useEffect,
  useState,
} from "react";

import {
  getDeployments,
} from "../../services/api";

import type {
  Deployment,
} from "../../types/deployment";

function statusClass(
  status: string,
) {
  switch (status) {
    case "SUCCESS":
      return "history-status success";

    case "FAILED":
      return "history-status failed";

    case "VALIDATING":
    case "RUNNING":
      return "history-status running";

    default:
      return "history-status pending";
  }
}

export default function DeploymentHistory({
  onSelect,
}: {
  onSelect?: (
    deployment: Deployment,
  ) => void;
}) {

  const [
    deployments,
    setDeployments,
  ] = useState<Deployment[]>([]);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  async function load() {

    try {

      setLoading(true);
      setError(null);

      const data =
        await getDeployments();

      setDeployments(data);

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load deployments.",
      );

    } finally {

      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {

    return (
      <div className="glass history-panel">
        <div className="panel-eyebrow">
          DEPLOYMENT HISTORY
        </div>

        <h2>
          Loading deployment history...
        </h2>
      </div>
    );
  }

  if (error) {

    return (
      <div className="glass history-panel">
        <div className="panel-eyebrow">
          DEPLOYMENT HISTORY
        </div>

        <h2>
          Unable to load history
        </h2>

        <p>
          {error}
        </p>

        <button
          className="learn-button"
          onClick={load}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!deployments.length) {

    return (
      <div className="glass history-panel">
        <div className="panel-eyebrow">
          DEPLOYMENT HISTORY
        </div>

        <h2>
          No deployments yet.
        </h2>

        <p>
          Create your first deployment
          validation to begin tracking
          deployment history.
        </p>
      </div>
    );
  }

  return (
    <div className="glass history-panel">

      <div className="history-heading">

        <div>
          <div className="panel-eyebrow">
            DEPLOYMENT HISTORY
          </div>

          <h2>
            Recent deployments
          </h2>
        </div>

        <span className="history-count">
          {deployments.length}
        </span>

      </div>

      <div className="history-list">

        {deployments
          .slice(0, 20)
          .map((deployment) => (

            <button
              key={deployment.id}
              className="history-row"
              onClick={() =>
                onSelect?.(deployment)
              }
            >

              <div className="history-main">

                <strong>
                  {deployment.serviceName}
                </strong>

                <span>
                  v{deployment.version}
                  {" Â· "}
                  {deployment.environment}
                </span>

              </div>

              <span
                className={statusClass(
                  deployment.status,
                )}
              >
                {deployment.status}
              </span>

              <div className="history-duration">
                {deployment.durationMs != null
                  ? `${deployment.durationMs} ms`
                  : "â€”"}
              </div>

              <div className="history-id">
                #{deployment.id}
              </div>

            </button>
          ))}

      </div>

    </div>
  );
}
