"""Deterministic evaluator conformance fixtures (Phase F).

These fixtures define the evaluation contract that every msval policy
evaluator must satisfy — including a future WASM/Rego evaluator. They
pin the exact findings (rule IDs, ordering, object references) that the
reference Python evaluator produces for fixed inputs.

A WASM evaluator is accepted only when it reproduces these fixtures
exactly; see ``test_evaluator_conformance_fixtures``.
"""

from __future__ import annotations

from msval_edge.evaluation.evaluator import (
    PythonRuleEvaluator,
    ValidationRequest,
)


ARCHITECTURE = {
    "version": "0.1",
    "service": {
        "name": "payments-api",
        "owner": "payments-team",
        "layer": "domain",
        "tier": "critical",
    },
    "exposure": {"public": False},
    "dependencies": [
        {"name": "orders-api", "layer": "domain", "required": True},
        {"name": "ledger-db", "layer": "data", "required": True},
    ],
    "availability": {
        "replicas": 2,
        "requires_health_checks": True,
    },
}

BAD_DEPLOYMENT = {
    "kind": "Deployment",
    "api_version": "apps/v1",
    "name": "payments-api",
    "namespace": "default",
    "replicas": 1,
    "labels": {"owner": "payments-team"},
    "containers": [
        {
            "name": "payments-api",
            "image": "payments-api",
            "resources": {},
            "readiness_probe": None,
            "liveness_probe": None,
            "lifecycle": None,
            "security_context": {"runAsNonRoot": False},
        }
    ],
}

BAD_KUBERNETES = {
    "deployment": BAD_DEPLOYMENT,
    "deployments": [BAD_DEPLOYMENT],
    "services": [],
    "ingresses": [],
    "ignored_objects": [],
}

# Pinned expected output of the reference evaluator. Order is part of
# the contract: K8S metadata/architecture findings first, then
# container rules in container order.
EXPECTED_BAD_FINDINGS = [
    ("K8S-008", "Deployment/payments-api", "metadata.labels.tier"),
    ("ARCH-007", "Deployment/payments-api", "spec.replicas"),
    ("K8S-001", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].image"),
    ("K8S-002", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].readinessProbe"),
    ("K8S-002", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].livenessProbe"),
    ("K8S-003", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].lifecycle"),
    ("K8S-004", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].resources.requests"),
    ("K8S-005", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].resources.limits"),
    ("K8S-006", "Deployment/payments-api container/payments-api", "spec.template.spec.containers[].securityContext.runAsNonRoot"),
]


def build_bad_request() -> ValidationRequest:
    return ValidationRequest(
        architecture=ARCHITECTURE,
        kubernetes=BAD_KUBERNETES,
        policy_digest="sha256:fixture",
    )


def expected_bad_tuples() -> list[tuple[str, str, str]]:
    return list(EXPECTED_BAD_FINDINGS)
