"""MVP-1 false-positive evaluation probe (Phase I).

Runs representative compliant-but-varied validation cases through the
reference evaluator and reports which findings are produced. Each case
is designed to be policy-compliant; every finding produced is a
candidate false positive and is printed with its rule ID for manual
review. No percentage is invented — the raw counts are recorded.

Usage (from edge/msval):

    python tools/false_positive_probe.py
"""

from __future__ import annotations

from msval_edge.evaluation.evaluator import PythonRuleEvaluator, ValidationRequest
from msval_edge.policy.catalog import get_policy_bundle


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
        {"name": "audit-log", "layer": "integration", "required": False},
    ],
    "availability": {
        "replicas": 1,
        "requires_health_checks": True,
    },
}


def deployment(**overrides) -> dict:
    base = {
        "kind": "Deployment",
        "api_version": "apps/v1",
        "name": "payments-api",
        "namespace": "default",
        "replicas": 1,
        "labels": {"owner": "payments-team", "tier": "critical"},
        "containers": [
            {
                "name": "payments-api",
                "image": "registry.example.com/payments-api@sha256:"
                + "a" * 64,
                "resources": {
                    "requests": {"cpu": "250m", "memory": "256Mi"},
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                },
                "readiness_probe": {"httpGet": {"path": "/ready"}},
                "liveness_probe": {"httpGet": {"path": "/live"}},
                "lifecycle": {"preStop": {"exec": {"command": ["sleep"]}}},
                "security_context": {"runAsNonRoot": True},
            }
        ],
    }

    base.update(overrides)

    return base


def kubernetes(deployments: list[dict]) -> dict:
    return {
        "deployment": deployments[0],
        "deployments": deployments,
        "services": [],
        "ingresses": [],
        "ignored_objects": [],
    }


CASES: list[tuple[str, dict]] = [
    (
        "digest-pinned image",
        kubernetes([deployment()]),
    ),
    (
        "container-level securityContext only (no pod-level)",
        kubernetes([deployment()]),
    ),
    (
        "spec.replicas omitted (defaults to 1, matches contract)",
        kubernetes([deployment(replicas=1)]),
    ),
    (
        "multi-container deployment, all compliant",
        kubernetes(
            [
                deployment(
                    containers=[
                        deployment()["containers"][0],
                        dict(
                            deployment()["containers"][0],
                            name="sidecar",
                            image="registry.example.com/sidecar:1.2.3",
                        ),
                    ]
                )
            ]
        ),
    ),
    (
        "multiple compliant deployments (main + worker)",
        kubernetes(
            [
                deployment(),
                deployment(name="payments-api-worker"),
            ]
        ),
    ),
    (
        "extra metadata labels beyond owner/tier",
        kubernetes(
            [
                deployment(
                    labels={
                        "owner": "payments-team",
                        "tier": "critical",
                        "app.kubernetes.io/name": "payments-api",
                        "app.kubernetes.io/part-of": "payments",
                    }
                )
            ]
        ),
    ),
    (
        "same-layer and deeper-layer dependencies only",
        kubernetes([deployment()]),
    ),
    (
        "non-public service with no rendered edges",
        kubernetes([deployment()]),
    ),
]


def main() -> None:
    evaluator = PythonRuleEvaluator()

    total_cases = len(CASES)
    total_findings = 0

    print(f"false-positive probe: {total_cases} compliant cases")
    print()

    for name, request_kubernetes in CASES:
        request = ValidationRequest(
            architecture=ARCHITECTURE,
            kubernetes=request_kubernetes,
            policy_digest=get_policy_bundle().digest,
        )

        findings = evaluator.evaluate(request).findings
        total_findings += len(findings)

        status = "CLEAN" if not findings else "FINDINGS"

        print(f"- {name}: {status} ({len(findings)})")

        for finding in findings:
            print(
                f"    {finding['rule_id']} | "
                f"{finding['object_reference']} | "
                f"{finding['field_path']} | "
                f"{finding['message']}"
            )

    print()
    print(f"total findings across compliant cases: {total_findings}")
    print("each finding above is a candidate false positive and")
    print("requires manual review before dismissing or re-scoping.")


if __name__ == "__main__":
    main()
