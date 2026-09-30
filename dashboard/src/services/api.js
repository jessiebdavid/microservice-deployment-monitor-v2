// API helper for the deployment dashboard.
//
// All endpoints below are the REAL endpoints implemented by the Spring
// Boot backend (backend/src/main/java/com/deployguard/.../deployment/).
// The endpoint list sketched in the teammate repository's
// docs/api-integration.md describes a different (not implemented) API
// and is intentionally NOT used here.
//
// Backend base: http://localhost:8081 (see
// backend/src/main/resources/application.properties).

const API_BASE =
  import.meta.env.VITE_API_BASE ||
  "http://localhost:8081/api";

export async function getDeploymentStats() {
  const response = await fetch(`${API_BASE}/deployments/stats`);

  if (!response.ok) {
    throw new Error(`Stats request failed: ${response.status}`);
  }

  return response.json();
}

export async function getDeployments() {
  const response = await fetch(`${API_BASE}/deployments`);

  if (!response.ok) {
    throw new Error(`Deployments request failed: ${response.status}`);
  }

  return response.json();
}

export async function getDeploymentValidations(id) {
  const response = await fetch(`${API_BASE}/deployments/${id}/validations`);

  if (!response.ok) {
    throw new Error(`Validations request failed: ${response.status}`);
  }

  return response.json();
}
