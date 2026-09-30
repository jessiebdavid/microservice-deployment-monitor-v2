# msval — Microservices Deployment Validator (MVP-1)

`msval` is a repository validation tool ("Repo Guard") for microservice
architectures. It validates a service architecture contract
(`service.arch.yaml`) together with rendered Kubernetes manifests against
a repository-pinned policy, and produces deterministic human, JSON and
SARIF output.

```
service.arch.yaml
        +
rendered Kubernetes YAML
        +
repository-pinned policy
        |
        v
      msval
        |
        +---- PASS
        |
        +---- WARN
        |
        +---- FAIL
        |
        v
human / JSON / SARIF output
```

MVP-1 scope is **local/CI validation only**. Centralized governance
(policy activation, waivers, findings storage) is out of scope and
belongs to later MVPs.

---

## What msval does

- Loads `service.arch.yaml` (the architecture contract) and validates it
  against the contract schema (`ARCH-CONTRACT`).
- Loads rendered Kubernetes YAML — **single- or multi-document** — and
  evaluates it against the pinned rule pack (`K8S-*`, `ARCH-004..007`).
- Validates dependency declarations (`DEP-001`, `DEP-002`) and public
  exposure consistency (`EXP-001`, `EXP-002`).
- Emits findings with full context: what is wrong, where, why it
  matters, how to fix it, and where to read more.
- Exits `1` when blocking findings exist (so CI fails), `2` on input
  errors, `0` on PASS/WARN.

Everything that msval reports is defined in one authoritative rule
catalog shipped as a pinned, SHA-256-verified policy artifact (see
[Policy versioning](#policy-versioning)).

## Installation

Requirements: Python 3.11+ (3.12 recommended, 3.14 used for the current
baseline measurements).

```bash
# from the repository root
pip install ./edge/msval

# development install with test tooling
pip install -e "./edge/msval[dev]"
```

This installs the `msval` command-line tool.

## CLI usage

```
msval init [--output PATH]
msval validate --architecture PATH [--kubernetes PATH] [--format human|json|sarif]
msval explain RULE_ID
```

### `msval init`

Create a starter architecture contract:

```bash
msval init --output service.arch.yaml
```

The command refuses to overwrite an existing file (exit code 2).

### `msval validate`

```bash
# golden path (exit 0, PASS)
msval validate \
  --architecture examples/service.arch.yaml \
  --kubernetes examples/kubernetes/deployment.yaml

# machine-readable JSON
msval validate \
  --architecture examples/service.arch.yaml \
  --kubernetes examples/kubernetes/deployment.yaml \
  --format json

# SARIF 2.1.0
msval validate \
  --architecture examples/service.arch.yaml \
  --kubernetes examples/kubernetes/deployment.yaml \
  --format sarif

# architecture-only validation (dependency + contract rules)
msval validate --architecture service.arch.yaml
```

Exit codes:

| Code | Meaning                                                     |
|------|-------------------------------------------------------------|
| 0    | PASS or WARN (no blocking findings)                          |
| 1    | FAIL — blocking findings or invalid architecture contract    |
| 2    | Input error (missing/invalid files, malformed manifests)     |

### `msval explain`

```bash
msval explain K8S-001
```

Prints severity, category, title, description, remediation and
documentation URL for one rule — read from the same pinned policy
catalog that produces findings. An unknown rule ID lists all available
rules and exits 1.

## service.arch.yaml format

```yaml
version: "0.1"

service:
  name: payments-api        # must match the Deployment name (or '<name>-<role>')
  owner: payments-team      # team responsible for the service
  layer: domain             # one of: edge, application, domain, integration, data
  tier: critical            # service criticality

exposure:
  public: false             # is this service reachable from the public internet?

dependencies:               # services this service calls
  - name: orders-api
    layer: domain           # layer of the dependency target
    required: true          # is the dependency required for operation?

availability:
  replicas: 2               # required replica count (must match spec.replicas)
  requires_health_checks: true
```

Validation is strict: missing fields, wrong types, invalid version,
invalid layers and invalid replica values are reported under
`ARCH-CONTRACT` and fail validation with exit code 1.

## Kubernetes input expectations

- Input is **rendered** Kubernetes YAML: what you would apply to a
  cluster. Templates (Helm, Kustomize) must be rendered first.
- **Multi-document manifests are supported** (`---` separated). Empty
  documents are ignored.
- Supported object kinds:
  - `apps/v1 Deployment` — fully validated (required: at least one
    Deployment must be present; multiple Deployments are supported).
  - `v1 Service` — used by the exposure rules (`type` must be
    `ClusterIP`, `LoadBalancer` or `NodePort`).
  - `networking.k8s.io/v1 Ingress` — used by the exposure rules
    (`spec.rules[].http.paths[].backend.service.name`).
- Other kinds (ConfigMap, Secret, etc.) are safely ignored and listed
  under `ignored_objects` in the normalized request; they never produce
  findings.
- Malformed Deployments (missing metadata/spec/containers) are **input
  errors** (exit 2), not findings: a broken manifest cannot be trusted
  for rule evaluation.

## Rule catalog

The authoritative catalog lives in the pinned policy artifact
[`src/msval_edge/policy/artifacts/msval-default-policy-1.0.0.yaml`](src/msval_edge/policy/artifacts/msval-default-policy-1.0.0.yaml).
Every finding, the `explain` command, JSON output and SARIF output read
metadata from this catalog.

### Kubernetes rules

| ID       | Severity | Title                                                    |
|----------|----------|----------------------------------------------------------|
| K8S-001  | BLOCK    | Container image must be pinned by tag or digest           |
| K8S-002  | BLOCK    | Container must define readiness and liveness probes       |
| K8S-003  | WARN     | Container should configure graceful shutdown              |
| K8S-004  | BLOCK    | Container must declare CPU and memory requests            |
| K8S-005  | BLOCK    | Container must declare CPU and memory limits              |
| K8S-006  | BLOCK    | Container must run as a non-root user                     |
| K8S-007  | BLOCK    | Deployment must declare an owner                          |
| K8S-008  | WARN     | Deployment should declare a service tier                  |

### Architecture consistency rules

| ID       | Severity | Title                                                    |
|----------|----------|----------------------------------------------------------|
| ARCH-004 | BLOCK    | Deployment must belong to the declared service (name or `<service>-<role>`) |
| ARCH-005 | BLOCK    | Deployment owner must match the declared service owner    |
| ARCH-006 | BLOCK    | Deployment tier must match the declared service tier      |
| ARCH-007 | BLOCK    | Deployment replicas must match the declared availability  |

### Dependency rules

| ID       | Severity | Title                                                    |
|----------|----------|----------------------------------------------------------|
| DEP-001  | BLOCK    | Dependency target must be a valid declared target (non-empty, not self, not duplicate, valid layer) |
| DEP-002  | BLOCK    | Dependency direction must follow the layer model (same-or-deeper) |

Layer ranking (pinned in the policy artifact): `edge (0)`,
`application (1)`, `domain (2)`, `integration (3)`, `data (4)`. A
service may only depend on services in the same or a deeper layer.

### Exposure rules

| ID       | Severity | Title                                                    |
|----------|----------|----------------------------------------------------------|
| EXP-001  | BLOCK    | Public service must be exposed through an approved edge (Ingress or LoadBalancer/NodePort Service) |
| EXP-002  | BLOCK    | Non-public service must not be publicly exposed          |

### Architecture contract

| ID            | Severity | Title                                    |
|---------------|----------|------------------------------------------|
| ARCH-CONTRACT | BLOCK    | service.arch.yaml violates the contract schema |

Legacy IDs `ARCH-001..003` remain in the catalog as documented aliases
of the contract validation for backwards compatibility of
`msval explain`; they are never emitted as findings.

## JSON output

`--format json` emits a stable, deterministic structure:

```json
{
  "tool": {"name": "msval", "version": "0.1.0"},
  "policy": {
    "artifact": "msval-default-policy",
    "version": "1.0.0",
    "digest": "sha256:...",
    "evaluator": "python-rules"
  },
  "validation": {
    "verdict": "FAIL",
    "architecture": {"path": "...", "status": "PASS"},
    "kubernetes": {"path": "...", "status": "FAIL"}
  },
  "summary": {"findings": 9, "blocking": 7, "warnings": 2},
  "findings": [
    {
      "rule_id": "K8S-004",
      "severity": "BLOCK",
      "object_reference": "Deployment/payments-api container/payments-api",
      "field_path": "spec.template.spec.containers[].resources.requests",
      "message": "Container must define CPU and memory requests.",
      "remediation": "Add resources.requests.cpu and resources.requests.memory to the container.",
      "documentation_url": "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
    }
  ]
}
```

The output contains no timestamps, no random IDs and no environment
data: identical inputs always produce byte-identical output (verified by
tests).

## SARIF output

`--format sarif` emits SARIF 2.1.0:

- `runs[].tool.driver.rules` carries full catalog metadata for every
  reported rule (title, description, remediation, category, severity,
  helpUri).
- `runs[].results` carry level (`error` for BLOCK, `warning` for WARN),
  message, physical artifact location and logical object reference, plus
  `properties.severity`, `properties.fieldPath` and
  `properties.remediation`.
- `runs[].properties` carries the verdict and policy/evaluator
  versions.

The output can be consumed by SARIF viewers and GitHub code scanning
pipelines.

## Policy versioning

The rule catalog ships as a **pinned policy artifact**:

- File: `src/msval_edge/policy/artifacts/msval-default-policy-1.0.0.yaml`
- `metadata.version` — semantic policy version (`1.0.0`), reported in
  JSON/SARIF output and human output.
- `integrity.rules_digest` — SHA-256 over the canonical JSON form of the
  artifact's `spec` section. It is verified **at every load**; a
  mismatch aborts validation with a clean error (no partial validation).
- `PINNED_POLICY_DIGEST` in `src/msval_edge/policy/catalog.py` pins the
  expected digest of the shipped artifact.

To change the rule catalog intentionally:

1. Edit the artifact (`spec.rules` or the layer model).
2. Re-pin the digest: `python tools/pin_policy.py`
3. Update `PINNED_POLICY_DIGEST` in `catalog.py` to the printed digest.
4. Bump `metadata.version` (this is the policy version surfaced to
   consumers).
5. Run the test suite.

> Signature verification: **not implemented**. The artifact is
> integrity-protected with SHA-256 only. msval does not claim and must
> not be described as performing cryptographic signature verification.
> The verification boundary (`PolicyIntegrityError`) is in place for a
> future signature scheme.

## Evaluator behavior

The validation pipeline is decoupled from the evaluation
implementation:

```
ValidationRequest (normalized architecture + Kubernetes + policy digest)
        |
        v
PolicyEvaluator (Protocol: evaluate(request) -> EvaluationResult)
        |
        v
EvaluationResult (structured findings + evaluator version)
```

- Default implementation: `PythonRuleEvaluator` (`python-rules`) —
  deterministic, offline, no network.
- The evaluator name is pinned in the policy artifact (`spec.evaluator`)
  and verified at startup: a policy pinning an unimplemented evaluator
  aborts with a clean error.
- Deterministic conformance fixtures
  (`src/msval_edge/evaluation/fixtures.py`) pin the exact findings
  (rule IDs, object references, field paths, ordering) for a fixed bad
  input. Any future evaluator must reproduce them exactly
  (see `tests/test_evaluator_fixtures.py`).

## WASM status

**Status: blocked in the current environment — not implemented, not
faked.**

Actual Rego/OPA-WASM evaluation requires:

1. The `opa` binary (Open Policy Agent) to compile a Rego policy into an
   OPA-WASM module: `opa build -t wasm -e msval/policy`.
   **Blocker:** `opa` is not installed in this environment, and no
   compiled policy artifact exists to evaluate.
2. A Python WASM runtime (for example `wasmtime`, which is pip-installable)
   plus an OPA-WASM ABI host implementation (memory management, `opa_eval`
   entrypoints, JSON marshalling between host and guest).

What exists today (Phase F deliverables):

- The evaluator abstraction (above) is WASM-ready: a
  `WasmPolicyEvaluator` can implement the same `PolicyEvaluator`
  protocol without touching the pipeline or CLI.
- Deterministic conformance fixtures define the evaluation contract that
  a WASM evaluator must satisfy before it is trusted.
- The Python evaluator remains fully functional and is the pinned
  default.

Required tooling to lift the blocker: install `opa` (>= 0.60), author
the Rego policy with semantics matching the conformance fixtures, add
`wasmtime` + an OPA-WASM ABI host, and pin the compiled artifact with
the same digest-verification mechanism.

## CI integration

Examples for both systems are included:

- GitHub Actions: [`.github/workflows/msval.yml`](.github/workflows/msval.yml)
- Jenkins: [`ci/Jenkinsfile.example`](ci/Jenkinsfile.example)

Both demonstrate the full flow: obtain/render Kubernetes manifests →
validate with `msval` → generate machine-readable output (JSON + SARIF
artifacts) → fail the job when blocking findings exist (msval exit 1).

### Pinned CI environment (Phase H)

- Python version is pinned in both examples (`3.12`).
- Dependency versions are pinned in
  [`requirements/ci-requirements.txt`](requirements/ci-requirements.txt)
  (`PyYAML==6.0.3`, `jsonschema==4.26.0`, `pytest==9.1.1`).
- No container infrastructure is required.

## Performance

Measured with [`tools/benchmark.py`](tools/benchmark.py) (end-to-end CLI
invocation, JSON output, including Python startup):

| Metric            | Value                          |
|-------------------|--------------------------------|
| Objects validated | 101 rendered Kubernetes objects |
| Target            | < 30 s                          |
| Measured (best)   | ~0.41 s                         |
| Measured (mean)   | ~0.42 s                         |
| Environment       | Windows, Python 3.14.6, no network |

Reproduce with: `python tools/benchmark.py 3`

### False-positive evaluation

Measured with
[`tools/false_positive_probe.py`](tools/false_positive_probe.py):
8 representative compliant-but-varied cases (digest-pinned images,
container-level security context, omitted replicas, multi-container,
multiple sub-Deployments, extra labels, same/deeper-layer dependencies,
no public edges) produce **0 findings** in total after the ARCH-004
naming-convention fix. Every finding produced by the probe on future
rule changes must be reviewed manually; the tool reports raw counts, no
percentage is invented.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ERROR: File not found: ...` | Input path does not exist | Check the path; note it is relative to the working directory |
| `ERROR: Invalid YAML in ...` | Manifest or contract is not valid YAML | Fix the YAML syntax error (line/column is included) |
| `service.arch.yaml must contain exactly one YAML document` | Contract file contains multiple documents | One contract per file |
| `Kubernetes normalization failed: ... at least one container` | Malformed Deployment | Fix the manifest; malformed Deployments are input errors, not findings |
| `Policy artifact integrity verification failed` | The policy artifact was edited without re-pinning | Re-pin with `python tools/pin_policy.py` (and review the change) |
| `Policy artifact pins evaluator '...' but only 'python-rules' is implemented` | Artifact pins an evaluator that is not shipped | Pin `python-rules` or implement the evaluator |
| CI fails with exit 1 but no crash | Blocking findings exist | Inspect the JSON/SARIF report; run `msval explain <RULE_ID>` |
| `VERDICT: WARN` with exit 0 | Only WARN-severity findings (K8S-003, K8S-008) | Review; warnings do not fail CI |

## Limitations

- MVP-1 validates **rendered** manifests only; it does not render Helm
  or Kustomize itself.
- Service/Ingress normalization supports the fields needed by the
  exposure rules; other fields are not interpreted.
- Deployment-level rules are evaluated per Deployment; pod-template
  labels beyond `metadata.labels` are not used for owner/tier checks.
- Integrity verification is SHA-256 only; no signature verification
  (documented boundary, see [Policy versioning](#policy-versioning)).
- WASM/Rego evaluation is blocked (see [WASM status](#wasm-status)).
- The exposure rules evaluate only the declared service; exposure of
  other services in the same manifest is not cross-checked against their
  own contracts (MVP-1 validates one contract per run).

## Development

```bash
# run the full test suite (from edge/msval)
python -m pytest -q

# re-pin the policy artifact after catalog changes
python tools/pin_policy.py

# performance benchmark
python tools/benchmark.py 3

# false-positive probe
python tools/false_positive_probe.py
```

Project layout:

```
edge/msval/
├── pyproject.toml
├── .github/workflows/msval.yml     # GitHub Actions example
├── ci/Jenkinsfile.example          # Jenkins example
├── requirements/ci-requirements.txt
├── examples/
│   ├── service.arch.yaml
│   └── kubernetes/
│       ├── deployment.yaml         # golden example
│       ├── bad-deployment.yaml     # known-bad example
│       └── multi-doc.yaml          # multi-document example
├── src/msval_edge/
│   ├── cli/main.py                 # CLI (init, validate, explain)
│   ├── normalization/              # YAML loading, contract, K8s normalization
│   ├── evaluation/                 # rules, evaluator abstraction, fixtures
│   └── policy/                     # catalog loader + pinned artifact
├── tests/                          # 74 tests (unit + acceptance)
└── tools/                          # pin_policy, benchmark, false_positive_probe
```
