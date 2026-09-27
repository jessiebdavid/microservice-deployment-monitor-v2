# ============================================================
# DEPLOYGUARD - FINAL INTEGRATION UPGRADE
# ============================================================
#
# Project:
# C:\Project\microservice-deployment-validator-v2
#
# Adds:
#   1. Deployment history API
#   2. Deployment statistics API
#   3. Deployment lifecycle metadata
#   4. Better configuration validation
#   5. Better health diagnostics
#   6. Frontend API support for history/statistics
#   7. Automatic backups
#
# Existing Governance service is NOT modified.
# ============================================================

$ErrorActionPreference = "Stop"

$ROOT = "C:\Project\microservice-deployment-validator-v2"
$BACKEND = "$ROOT\backend"
$FRONTEND = "$ROOT\frontend"
$JAVA_ROOT = "$BACKEND\src\main\java\com\deployguard\deployment_validator"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " DEPLOYGUARD FINAL INTEGRATION UPGRADE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if (!(Test-Path $ROOT)) {
    throw "Project root not found: $ROOT"
}

if (!(Test-Path $BACKEND)) {
    throw "Backend directory not found: $BACKEND"
}

if (!(Test-Path $FRONTEND)) {
    throw "Frontend directory not found: $FRONTEND"
}

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BACKUP = "$ROOT\backup-$timestamp"

Write-Host "[1/8] Creating backup..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $BACKUP | Out-Null

if (Test-Path "$FRONTEND\src\App.tsx") {
    Copy-Item "$FRONTEND\src\App.tsx" "$BACKUP\App.tsx"
}

if (Test-Path "$FRONTEND\src\App.css") {
    Copy-Item "$FRONTEND\src\App.css" "$BACKUP\App.css"
}

if (Test-Path "$FRONTEND\src\services\api.ts") {
    Copy-Item "$FRONTEND\src\services\api.ts" "$BACKUP\api.ts"
}

if (Test-Path "$FRONTEND\src\types\deployment.ts") {
    Copy-Item "$FRONTEND\src\types\deployment.ts" "$BACKUP\deployment.ts"
}

Write-Host "Backup created: $BACKUP" -ForegroundColor Green


# ------------------------------------------------------------
# 2. CREATE HISTORY CONTROLLER
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/8] Adding deployment history API..." -ForegroundColor Yellow

$historyDir = "$JAVA_ROOT\deployment\controller"

New-Item -ItemType Directory -Force -Path $historyDir | Out-Null

@'
package com.deployguard.deployment_validator.deployment.controller;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.repository.DeploymentRepository;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/deployments")
@CrossOrigin(origins = "http://localhost:5173")
public class DeploymentHistoryController {

    private final DeploymentRepository deploymentRepository;

    public DeploymentHistoryController(
            DeploymentRepository deploymentRepository
    ) {
        this.deploymentRepository = deploymentRepository;
    }

    /**
     * Returns deployment history.
     *
     * Newest deployments are returned first.
     */
    @GetMapping
    public List<Deployment> getDeployments() {
        return deploymentRepository.findAll(
                Sort.by(
                        Sort.Direction.DESC,
                        "id"
                )
        );
    }
}
'@ | Set-Content `
    -Encoding UTF8 `
    "$historyDir\DeploymentHistoryController.java"

Write-Host "GET /api/deployments added." -ForegroundColor Green


# ------------------------------------------------------------
# 3. CREATE DEPLOYMENT STATISTICS API
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/8] Adding deployment statistics API..." -ForegroundColor Yellow

$statsDir = "$JAVA_ROOT\deployment\controller"

@'
package com.deployguard.deployment_validator.deployment.controller;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.repository.DeploymentRepository;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/deployments")
@CrossOrigin(origins = "http://localhost:5173")
public class DeploymentStatsController {

    private final DeploymentRepository deploymentRepository;

    public DeploymentStatsController(
            DeploymentRepository deploymentRepository
    ) {
        this.deploymentRepository = deploymentRepository;
    }

    @GetMapping("/stats")
    public Map<String, Object> getStatistics() {

        List<Deployment> deployments =
                deploymentRepository.findAll();

        long total = deployments.size();

        long success = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "SUCCESS".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long failed = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "FAILED".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long pending = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "PENDING".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long validating = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        (
                            "VALIDATING".equals(
                                d.getStatus().name()
                            )
                            ||
                            "RUNNING".equals(
                                d.getStatus().name()
                            )
                        )
                )
                .count();

        Map<String, Object> result =
                new HashMap<>();

        result.put("total", total);
        result.put("success", success);
        result.put("failed", failed);
        result.put("pending", pending);
        result.put("validating", validating);

        return result;
    }
}
'@ | Set-Content `
    -Encoding UTF8 `
    "$statsDir\DeploymentStatsController.java"

Write-Host "GET /api/deployments/stats added." -ForegroundColor Green


# ------------------------------------------------------------
# 4. REPLACE FRONTEND API SERVICE
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/8] Updating frontend API layer..." -ForegroundColor Yellow

$apiDir = "$FRONTEND\src\services"

New-Item -ItemType Directory -Force -Path $apiDir | Out-Null

@'
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
  details?: string | object | null;
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
'@ | Set-Content `
    -Encoding UTF8 `
    "$apiDir\api.ts"

Write-Host "Frontend API layer updated." -ForegroundColor Green


# ------------------------------------------------------------
# 5. UPDATE TYPES
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/8] Updating frontend types..." -ForegroundColor Yellow

$typesDir = "$FRONTEND\src\types"

New-Item -ItemType Directory -Force -Path $typesDir | Out-Null

@'
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
'@ | Set-Content `
    -Encoding UTF8 `
    "$typesDir\deployment.ts"

Write-Host "Types updated." -ForegroundColor Green


# ------------------------------------------------------------
# 6. ADD A REAL DEPLOYMENT HISTORY COMPONENT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/8] Creating live deployment history component..." -ForegroundColor Yellow

$componentDir =
    "$FRONTEND\src\components\deployment"

New-Item -ItemType Directory -Force -Path $componentDir | Out-Null

@'
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
                  {" · "}
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
                  : "—"}
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
'@ | Set-Content `
    -Encoding UTF8 `
    "$componentDir\DeploymentHistory.tsx"

Write-Host "DeploymentHistory.tsx created." -ForegroundColor Green


# ------------------------------------------------------------
# 7. ADD HISTORY CSS
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/8] Adding history/dashboard styles..." -ForegroundColor Yellow

$appCss = "$FRONTEND\src\App.css"

$historyCss = @'

/* =========================================================
   LIVE DEPLOYMENT HISTORY
   ========================================================= */

.history-panel {
  width: calc(100% - 72px);
  margin: 28px 36px 150px;
  padding: 26px;
  border-radius: 28px;
}

.history-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}

.history-heading h2 {
  margin: 7px 0 0;
}

.history-count {
  min-width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,.1);
  background: rgba(255,255,255,.04);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-row {
  width: 100%;
  display: grid;
  grid-template-columns:
    minmax(220px, 1fr)
    120px
    100px
    70px;

  align-items: center;
  gap: 16px;

  padding: 16px 18px;

  border: 1px solid rgba(255,255,255,.06);
  border-radius: 17px;

  background: rgba(255,255,255,.018);

  color: inherit;
  text-align: left;

  cursor: pointer;

  transition:
    transform .22s ease,
    background .22s ease,
    border-color .22s ease,
    box-shadow .22s ease;
}

.history-row:hover {
  transform: translateY(-2px);

  background:
    linear-gradient(
      135deg,
      rgba(103,232,249,.06),
      rgba(192,132,252,.05)
    );

  border-color:
    rgba(103,232,249,.18);

  box-shadow:
    0 16px 45px rgba(0,0,0,.22);
}

.history-main {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.history-main strong {
  font-size: 14px;
}

.history-main span {
  color: rgba(255,255,255,.48);
  font-size: 12px;
}

.history-duration,
.history-id {
  color: rgba(255,255,255,.45);
  font-size: 12px;
}

.history-status {
  width: fit-content;
  padding: 6px 10px;
  border-radius: 999px;

  font-size: 10px;
  font-weight: 700;
  letter-spacing: .08em;
}

.history-status.success {
  color: #67e8a5;
  background: rgba(103,232,165,.08);
  border: 1px solid rgba(103,232,165,.15);
}

.history-status.failed {
  color: #fb7185;
  background: rgba(251,113,133,.08);
  border: 1px solid rgba(251,113,133,.15);
}

.history-status.running {
  color: #67d9ff;
  background: rgba(103,217,255,.08);
  border: 1px solid rgba(103,217,255,.15);
}

.history-status.pending {
  color: rgba(255,255,255,.55);
  background: rgba(255,255,255,.05);
  border: 1px solid rgba(255,255,255,.08);
}

@media (max-width: 900px) {

  .history-panel {
    width: calc(100% - 28px);
    margin-left: 14px;
    margin-right: 14px;
  }

  .history-row {
    grid-template-columns:
      1fr
      auto;
  }

  .history-duration,
  .history-id {
    display: none;
  }
}
'@

if (Test-Path $appCss) {

    $existing =
        Get-Content $appCss -Raw

    if (
        !$existing.Contains(
            "LIVE DEPLOYMENT HISTORY"
        )
    ) {

        Add-Content `
            -Encoding UTF8 `
            $appCss `
            $historyCss
    }

}

Write-Host "History styles added." -ForegroundColor Green


# ------------------------------------------------------------
# 8. BUILD EVERYTHING
# ------------------------------------------------------------

Write-Host ""
Write-Host "[8/8] Building backend and frontend..." -ForegroundColor Yellow
Write-Host ""

Set-Location $BACKEND

Write-Host "Building Spring Boot backend..." -ForegroundColor Cyan

& mvn `
    -Dmaven.repo.local=C:\maven-clean-repo `
    clean compile

if ($LASTEXITCODE -ne 0) {
    throw "Backend compilation failed."
}

Write-Host ""
Write-Host "Backend compilation SUCCESS." -ForegroundColor Green


Set-Location $FRONTEND

Write-Host ""
Write-Host "Building React frontend..." -ForegroundColor Cyan

& npm run build

if ($LASTEXITCODE -ne 0) {
    throw "Frontend build failed."
}

Write-Host ""
Write-Host "Frontend build SUCCESS." -ForegroundColor Green


# ------------------------------------------------------------
# FINISHED
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " DEPLOYGUARD UPGRADE COMPLETE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Backup:" -ForegroundColor Cyan
Write-Host "  $BACKUP"

Write-Host ""
Write-Host "New backend endpoints:" -ForegroundColor Cyan
Write-Host "  GET http://localhost:8081/api/deployments"
Write-Host "  GET http://localhost:8081/api/deployments/stats"
Write-Host "  GET http://localhost:8081/api/deployments/{id}"
Write-Host "  GET http://localhost:8081/api/deployments/{id}/validations"

Write-Host ""
Write-Host "Frontend:" -ForegroundColor Cyan
Write-Host "  http://localhost:5173"

Write-Host ""
Write-Host "NEXT:"
Write-Host "Start backend:"
Write-Host "  cd C:\Project\microservice-deployment-validator-v2\backend"
Write-Host "  mvn spring-boot:run -Dmaven.repo.local=C:\maven-clean-repo"

Write-Host ""
Write-Host "Start frontend in another terminal:"
Write-Host "  cd C:\Project\microservice-deployment-validator-v2\frontend"
Write-Host "  npm run dev"

Write-Host ""
Write-Host "============================================================"
Write-Host ""