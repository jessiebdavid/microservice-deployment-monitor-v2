from pathlib import Path

import yaml

from msval_edge.evaluation.rules import evaluate_rules
from msval_edge.normalization.kubernetes import normalize_deployment


EXAMPLES_DIR = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "kubernetes"
)


def load_example(name: str) -> dict:
    path = EXAMPLES_DIR / name

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_rule_ids(findings):
    return [finding["rule_id"] for finding in findings]


def test_golden_deployment_has_no_findings():
    document = load_example("deployment.yaml")

    normalized = normalize_deployment(document)

    findings = evaluate_rules(normalized)

    assert findings == []


def test_bad_deployment_has_blocking_findings():
    document = load_example("bad-deployment.yaml")

    normalized = normalize_deployment(document)

    findings = evaluate_rules(normalized)

    assert len(findings) == 5

    rule_ids = get_rule_ids(findings)

    assert "K8S-002" in rule_ids
    assert "K8S-004" in rule_ids
    assert "K8S-005" in rule_ids
    assert "K8S-006" in rule_ids

    assert all(
        finding["severity"] == "BLOCK"
        for finding in findings
    )


def test_findings_have_required_fields():
    document = load_example("bad-deployment.yaml")

    normalized = normalize_deployment(document)

    findings = evaluate_rules(normalized)

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


def test_architecture_replica_mismatch_is_detected():
    document = load_example("deployment.yaml")

    document["spec"]["replicas"] = 1

    normalized = normalize_deployment(document)

    architecture = {
        "version": "0.1",
        "service": {
            "name": "payments-api",
            "owner": "payments-team",
            "layer": "domain",
            "tier": "critical",
        },
        "exposure": {
            "public": False,
        },
        "dependencies": [],
        "availability": {
            "replicas": 2,
            "requires_health_checks": True,
        },
    }

    findings = evaluate_rules(
        normalized,
        architecture,
    )

    assert len(findings) == 1
    assert findings[0]["rule_id"] == "ARCH-007"
    assert findings[0]["severity"] == "BLOCK"