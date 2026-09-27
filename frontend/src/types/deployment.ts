export type DeploymentStatus =
  | "PENDING"
  | "RUNNING"
  | "VALIDATING"
  | "SUCCESS"
  | "FAILED";

export type ValidationStatus =
  | "PASS"
  | "FAIL"
  | "WARN"
  | "SKIPPED";

export type ValidationType =
  | "GOVERNANCE"
  | "CONFIGURATION"
  | "HEALTH";

export interface Deployment {
  id: number;
  serviceName: string;
  version: string;
  environment: string;
  targetUrl: string;
  status: DeploymentStatus | string;
  durationMs?: number | null;
  createdAt?: string | null;
  updatedAt?: string | null;
}

export interface ValidationResult {
  id?: number;
  deploymentId?: number;

  type?:
    | ValidationType
    | string;

  validationType?:
    | ValidationType
    | string;

  status?:
    | ValidationStatus
    | string;

  message?: string;

  details?:
    | string
    | Record<string, unknown>
    | null;

  durationMs?: number | null;
}
