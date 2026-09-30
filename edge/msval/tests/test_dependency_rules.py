"""Positive and negative tests for the dependency rules (Phase B).

DEP-001: dependency target must be a valid declared architecture target.
DEP-002: dependency direction must follow the architecture layer model.
"""

from msval_edge.evaluation.rules import (
    check_architecture_consistency,
    check_dependencies,
)


BASE_ARCHITECTURE = {
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


def architecture_with(dependency: dict) -> dict:
    architecture = {
        "version": BASE_ARCHITECTURE["version"],
        "service": dict(BASE_ARCHITECTURE["service"]),
        "exposure": dict(BASE_ARCHITECTURE["exposure"]),
        "availability": dict(BASE_ARCHITECTURE["availability"]),
        "dependencies": [dependency],
    }

    return architecture


def test_valid_same_layer_dependency_has_no_findings():
    findings = check_dependencies(
        architecture_with(
            {"name": "orders-api", "layer": "domain", "required": True}
        )
    )

    assert findings == []


def test_valid_deeper_layer_dependency_has_no_findings():
    findings = check_dependencies(
        architecture_with(
            {"name": "postgres", "layer": "data", "required": True}
        )
    )

    assert findings == []


def test_empty_dependency_name_is_blocked():
    findings = check_dependencies(
        architecture_with({"name": "", "layer": "data", "required": True})
    )

    assert [finding["rule_id"] for finding in findings] == ["DEP-001"]


def test_self_dependency_is_blocked():
    findings = check_dependencies(
        architecture_with(
            {"name": "payments-api", "layer": "data", "required": True}
        )
    )

    assert [finding["rule_id"] for finding in findings] == ["DEP-001"]


def test_duplicate_dependency_is_blocked():
    architecture = architecture_with(
        {"name": "orders-api", "layer": "domain", "required": True}
    )
    architecture["dependencies"].append(
        {"name": "orders-api", "layer": "domain", "required": False}
    )

    findings = check_dependencies(architecture)

    assert [finding["rule_id"] for finding in findings] == ["DEP-001"]
    assert "more than once" in findings[0]["message"]


def test_unknown_dependency_layer_is_blocked():
    findings = check_dependencies(
        architecture_with(
            {"name": "orders-api", "layer": "warp", "required": True}
        )
    )

    assert [finding["rule_id"] for finding in findings] == ["DEP-001"]
    assert "not a valid architecture layer" in findings[0]["message"]


def test_upward_dependency_is_blocked():
    findings = check_dependencies(
        architecture_with(
            {"name": "edge-gateway", "layer": "edge", "required": True}
        )
    )

    assert [finding["rule_id"] for finding in findings] == ["DEP-002"]
    assert "points upward" in findings[0]["message"]


def test_findings_carry_catalog_metadata():
    findings = check_dependencies(
        architecture_with(
            {"name": "edge-gateway", "layer": "edge", "required": True}
        )
    )

    required_fields = {
        "rule_id",
        "severity",
        "object_reference",
        "field_path",
        "message",
        "remediation",
        "documentation_url",
    }

    for finding in findings:
        assert required_fields.issubset(finding.keys())
        assert finding["severity"] == "BLOCK"


def test_sub_deployment_naming_convention_is_not_arch_004():
    """Regression: '<service>-<role>' Deployments belong to the service.

    Found by the false-positive probe (Phase I): a compliant worker
    Deployment named payments-api-worker triggered ARCH-004.
    """

    architecture = architecture_with(
        {"name": "orders-api", "layer": "domain", "required": True}
    )

    deployment = {
        "kind": "Deployment",
        "name": "payments-api-worker",
        "replicas": 2,
        "labels": {"owner": "payments-team", "tier": "critical"},
        "containers": [],
    }

    findings = check_architecture_consistency(architecture, deployment)

    assert [finding["rule_id"] for finding in findings] == []


def test_unrelated_deployment_name_still_triggers_arch_004():
    architecture = architecture_with(
        {"name": "orders-api", "layer": "domain", "required": True}
    )

    deployment = {
        "kind": "Deployment",
        "name": "catalog-api",
        "replicas": 2,
        "labels": {"owner": "payments-team", "tier": "critical"},
        "containers": [],
    }

    findings = check_architecture_consistency(architecture, deployment)

    assert [finding["rule_id"] for finding in findings] == ["ARCH-004"]
