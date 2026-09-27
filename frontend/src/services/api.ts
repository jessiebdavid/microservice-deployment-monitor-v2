const API_BASE =
  "http://localhost:8081/api";

export interface CreateDeploymentRequest {
  serviceName: string;
  version: string;
  environment: string;
  targetUrl: string;
}

export interface Deployment {
  id: number;
  serviceName: string;
  version: string;
  environment: string;
  targetUrl: string;
  status: string;
  durationMs?: number | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ValidationResult {
  id?: number;
  type?: string;
  validationType?: string;
  status?: string;
  message?: string;
  details?: string | Record<string, unknown> | null;
  durationMs?: number | null;
}

export interface DeploymentStats {
  total: number;
  success: number;
  failed: number;
  pending: number;
  validating: number;
}

async function request<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {

  const response =
    await fetch(url, {
      headers: {
        "Content-Type":
          "application/json",
        ...(options?.headers || {}),
      },
      ...options,
    });

  if (!response.ok) {

    let message =
      `Request failed: ${response.status}`;

    try {
      const body =
        await response.json();

      if (body?.message) {
        message = body.message;
      }

      if (body?.detail) {
        message = body.detail;
      }

      if (body?.error) {
        message = body.error;
      }

    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  return response.json();
}

export async function createDeployment(
  payload: CreateDeploymentRequest,
): Promise<Deployment> {

  return request<Deployment>(
    `${API_BASE}/deployments`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export async function getDeployments():
  Promise<Deployment[]> {

  return request<Deployment[]>(
    `${API_BASE}/deployments`,
  );
}

export async function getDeployment(
  id: number,
): Promise<Deployment> {

  return request<Deployment>(
    `${API_BASE}/deployments/${id}`,
  );
}

export async function getDeploymentValidations(
  id: number,
): Promise<ValidationResult[]> {

  return request<ValidationResult[]>(
    `${API_BASE}/deployments/${id}/validations`,
  );
}

export async function getDeploymentStats():
  Promise<DeploymentStats> {

  return request<DeploymentStats>(
    `${API_BASE}/deployments/stats`,
  );
}

export async function checkBackendHealth():
  Promise<unknown> {

  return request<unknown>(
    "http://localhost:8081/actuator/health",
  );
}
