"""Tests for the evaluator abstraction (Phase E)."""

from msval_edge.evaluation.evaluator import (
    EvaluationResult,
    PythonRuleEvaluator,
    ValidationRequest,
    create_default_evaluator,
)
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
    "dependencies": [],
    "availability": {
        "replicas": 2,
        "requires_health_checks": True,
    },
}


def good_deployment():
    return {
        "kind": "Deployment",
        "api_version": "apps/v1",
        "name": "payments-api",
        "namespace": "default",
        "replicas": 2,
        "labels": {"owner": "payments-team", "tier": "critical"},
        "containers": [
            {
                "name": "payments-api",
                "image": "payments-api:2.1.0",
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


def test_default_evaluator_is_pinned_python_rules():
    evaluator = create_default_evaluator()

    assert evaluator.evaluator_version == "python-rules"
    assert isinstance(evaluator, PythonRuleEvaluator)


def test_golden_request_has_no_findings():
    evaluator = create_default_evaluator()

    result = evaluator.evaluate(
        ValidationRequest(
            architecture=ARCHITECTURE,
            kubernetes={
                "deployment": good_deployment(),
                "deployments": [good_deployment()],
                "services": [],
                "ingresses": [],
                "ignored_objects": [],
            },
            policy_digest=get_policy_bundle().digest,
        )
    )

    assert isinstance(result, EvaluationResult)
    assert result.findings == []


def test_architecture_only_request_checks_dependencies():
    architecture = dict(ARCHITECTURE)
    architecture["dependencies"] = [
        {"name": "edge-gateway", "layer": "edge", "required": True}
    ]

    evaluator = create_default_evaluator()

    result = evaluator.evaluate(
        ValidationRequest(
            architecture=architecture,
            kubernetes=None,
            policy_digest=get_policy_bundle().digest,
        )
    )

    rule_ids = [finding["rule_id"] for finding in result.findings]

    assert "DEP-002" in rule_ids


def test_evaluator_is_deterministic():
    evaluator = create_default_evaluator()

    request = ValidationRequest(
        architecture=ARCHITECTURE,
        kubernetes={
            "deployment": good_deployment(),
            "deployments": [good_deployment()],
            "services": [],
            "ingresses": [],
            "ignored_objects": [],
        },
        policy_digest=get_policy_bundle().digest,
    )

    first = evaluator.evaluate(request)
    second = evaluator.evaluate(request)

    assert first.findings == second.findings
