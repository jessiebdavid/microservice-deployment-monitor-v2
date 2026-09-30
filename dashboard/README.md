# Deployment Dashboard

React + Vite dashboard for the microservice deployment validator. Shows
deployment statistics, the latest deployment and its validation results
from the Spring Boot backend.

Provenance: the source lives in the teammate repository
`Microservice-deployment-dashboard` (original `Dashboard/` app, kept as
backup). It was copied into this repository as `dashboard/` and then
connected to the real backend APIs.

## Run

```bash
npm install
npm run dev
```

The dev server uses Vite's default port **5173**, which is exactly the
origin allowed by the backend CORS configuration — do not change the
port unless the backend CORS config changes too.

The backend must be running on port 8081:

```bash
cd ../backend
mvn spring-boot:run
```

## Data sources (real backend endpoints)

| Dashboard element | Endpoint |
|---|---|
| Summary cards (Total / Successful / Failed / Running) | `GET /api/deployments/stats` |
| Latest deployment card | `GET /api/deployments` (backend returns newest first; first element used) |
| Validation results + check boxes | `GET /api/deployments/{id}/validations` |

Base URL: `http://localhost:8081/api`, overridable with `VITE_API_BASE`
(see `src/services/api.js`).

## Interpretation notes (no fabricated data)

- **Running** = `stats.validating + stats.pending` (the backend's
  in-flight statuses).
- **Pipeline stages**: the backend does not track Build/Test/Deploy
  stages, so the original stage boxes render **validation checks** from
  `/validations` plus the deployment's own status. They are honestly
  labeled; nothing pretends to be a pipeline stage.
- **Validation status** is derived from the results (FAIL if any result
  has status FAIL, otherwise PASS). The backend exposes no governance
  `ALLOW`/`DENY` decision field, so none is displayed.
- **Findings** counts results with status `FAIL`.

## Notes

- Creating a deployment through `POST /api/deployments` currently fails
  unless the governance service (`http://localhost:8080`) is also
  running — the deployment orchestration calls it synchronously. This is
  pre-existing backend behavior, unchanged by the dashboard integration.
