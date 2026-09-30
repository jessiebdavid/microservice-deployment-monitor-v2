"""Positive and negative tests for the exposure rules (Phase B).

EXP-001: public service must be exposed through an approved edge.
EXP-002: non-public service must not be publicly exposed.
"""

from msval_edge.evaluation.rules import check_exposure


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


def kubernetes_with(
    services: list,
    ingresses: list,
) -> dict:
    deployment = {
        "kind": "Deployment",
        "name": "payments-api",
        "labels": {},
        "containers": [],
    }

    return {
        "deployment": deployment,
        "deployments": [deployment],
        "services": services,
        "ingresses": ingresses,
        "ignored_objects": [],
    }


def load_balancer_service(name: str) -> dict:
    return {"kind": "Service", "name": name, "type": "LoadBalancer"}


def ingress_backend(name: str) -> dict:
    return {"kind": "Ingress", "name": f"{name}-ingress", "backends": [name]}


def test_public_service_with_ingress_has_no_findings():
    architecture = dict(BASE_ARCHITECTURE)
    architecture["exposure"] = {"public": True}

    findings = check_exposure(
        architecture,
        kubernetes_with([], [ingress_backend("payments-api")]),
    )

    assert findings == []


def test_public_service_with_load_balancer_has_no_findings():
    architecture = dict(BASE_ARCHITECTURE)
    architecture["exposure"] = {"public": True}

    findings = check_exposure(
        architecture,
        kubernetes_with([load_balancer_service("payments-api")], []),
    )

    assert findings == []


def test_public_service_without_edge_is_blocked():
    architecture = dict(BASE_ARCHITECTURE)
    architecture["exposure"] = {"public": True}

    findings = check_exposure(architecture, kubernetes_with([], []))

    assert [finding["rule_id"] for finding in findings] == ["EXP-001"]
    assert findings[0]["severity"] == "BLOCK"


def test_nonpublic_service_with_ingress_is_blocked():
    findings = check_exposure(
        BASE_ARCHITECTURE,
        kubernetes_with([], [ingress_backend("payments-api")]),
    )

    assert [finding["rule_id"] for finding in findings] == ["EXP-002"]


def test_nonpublic_service_with_load_balancer_is_blocked():
    findings = check_exposure(
        BASE_ARCHITECTURE,
        kubernetes_with([load_balancer_service("payments-api")], []),
    )

    assert [finding["rule_id"] for finding in findings] == ["EXP-002"]


def test_other_service_public_edge_is_ignored():
    findings = check_exposure(
        BASE_ARCHITECTURE,
        kubernetes_with(
            [load_balancer_service("catalog-api")],
            [ingress_backend("catalog-api")],
        ),
    )

    assert findings == []


def test_findings_carry_catalog_metadata():
    architecture = dict(BASE_ARCHITECTURE)
    architecture["exposure"] = {"public": True}

    findings = check_exposure(architecture, kubernetes_with([], []))

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
