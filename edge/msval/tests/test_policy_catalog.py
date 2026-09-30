"""Tests for the pinned policy catalog (Phases C+D)."""

from pathlib import Path

import pytest

from msval_edge.policy.catalog import (
    PINNED_POLICY_ARTIFACT,
    PINNED_POLICY_DIGEST,
    PolicyArtifactError,
    PolicyIntegrityError,
    _sha256_digest,
    get_policy_bundle,
    load_policy_artifact,
)


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def test_pinned_artifact_loads_and_verifies():
    bundle = get_policy_bundle()

    assert bundle.name == "msval-default-policy"
    assert bundle.version == "1.0.0"
    assert bundle.digest == f"sha256:{PINNED_POLICY_DIGEST.removeprefix('sha256:')}"
    assert bundle.evaluator == "python-rules"
    assert bundle.layers.ranking["edge"] < bundle.layers.ranking["domain"]


def test_pinned_digest_constant_matches_artifact():
    bundle = get_policy_bundle()

    assert bundle.digest == PINNED_POLICY_DIGEST


def test_catalog_contains_all_mvp1_rules():
    bundle = get_policy_bundle()

    expected = {
        "ARCH-001",
        "ARCH-002",
        "ARCH-003",
        "ARCH-CONTRACT",
        "ARCH-004",
        "ARCH-005",
        "ARCH-006",
        "ARCH-007",
        "DEP-001",
        "DEP-002",
        "EXP-001",
        "EXP-002",
        "K8S-001",
        "K8S-002",
        "K8S-003",
        "K8S-004",
        "K8S-005",
        "K8S-006",
        "K8S-007",
        "K8S-008",
    }

    assert expected.issubset(bundle.rules.keys())


def test_every_rule_has_complete_metadata():
    bundle = get_policy_bundle()

    for rule_id, rule in bundle.rules.items():
        assert rule.severity in ("BLOCK", "WARN"), rule_id
        assert rule.title, rule_id
        assert rule.description, rule_id
        assert rule.remediation, rule_id
        assert rule.category, rule_id
        assert rule.documentation_url.startswith("https://"), rule_id


def test_findings_reference_existing_catalog_rules():
    """All emitted rule IDs must exist in the catalog, and every BLOCK
    rule (except the public-service EXP-001 and the legacy aliases) must
    be exercisable end-to-end.
    """
    bundle = get_policy_bundle()

    architecture = {
        "version": "0.1",
        "service": {
            "name": "payments-api",
            "owner": "payments-team",
            "layer": "domain",
            "tier": "critical",
        },
        "exposure": {"public": False},
        "dependencies": [
            {"name": "edge-gateway", "layer": "edge", "required": True},
            {"name": "payments-api", "layer": "data", "required": True},
            {"name": "", "layer": "data", "required": True},
            {"name": "dup", "layer": "data", "required": True},
            {"name": "dup", "layer": "data", "required": True},
            {"name": "valid", "layer": "nope", "required": True},
        ],
        "availability": {
            "replicas": 2,
            "requires_health_checks": True,
        },
    }

    deployment = {
        "kind": "Deployment",
        "name": "other-name",
        "replicas": 1,
        "labels": {"owner": "wrong-team", "tier": "standard"},
        "containers": [
            {
                "name": "app",
                "image": "app",
                "resources": {},
                "readiness_probe": None,
                "liveness_probe": None,
                "lifecycle": None,
                "security_context": {},
            }
        ],
    }

    unlabeled_deployment = dict(deployment)
    unlabeled_deployment["name"] = "payments-api-worker"
    unlabeled_deployment["labels"] = {}

    kubernetes = {
        "deployment": deployment,
        "deployments": [deployment, unlabeled_deployment],
        "services": [
            {
                "kind": "Service",
                "name": "payments-api",
                "type": "LoadBalancer",
                "namespace": "default",
            }
        ],
        "ingresses": [],
        "ignored_objects": [],
    }

    from msval_edge.evaluation.rules import (
        check_architecture_consistency,
        check_dependencies,
        check_exposure,
        check_image,
        check_metadata,
        check_probes,
        check_resources,
        check_security_context,
    )

    findings = []
    findings.extend(check_dependencies(architecture))
    findings.extend(check_metadata(deployment))
    findings.extend(check_metadata(unlabeled_deployment))
    findings.extend(check_architecture_consistency(architecture, deployment))
    findings.extend(check_exposure(architecture, kubernetes))

    for container in deployment["containers"]:
        findings.extend(check_image(container, deployment["name"]))
        findings.extend(check_probes(container, deployment["name"]))
        findings.extend(check_resources(container, deployment["name"]))
        findings.extend(
            check_security_context(container, deployment["name"])
        )

    emitted = {finding["rule_id"] for finding in findings}

    assert emitted.issubset(bundle.rules.keys())

    # Every BLOCK rule except EXP-001 (requires a public service) and the
    # legacy aliases ARCH-001..003 (reported as ARCH-CONTRACT) must be
    # exercisable end-to-end:
    blocking = {
        rule_id
        for rule_id, rule in bundle.rules.items()
        if rule.severity == "BLOCK"
    }

    missing = blocking - emitted - {"EXP-001", "ARCH-001", "ARCH-002", "ARCH-003", "ARCH-CONTRACT"}

    assert not missing


def test_tampered_artifact_fails_integrity(tmp_path):
    source = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "msval_edge"
        / "policy"
        / "artifacts"
        / PINNED_POLICY_ARTIFACT
    )

    import yaml

    document = yaml.safe_load(source.read_text(encoding="utf-8"))
    document["spec"]["rules"][0]["title"] = "Tampered Title"

    tampered = tmp_path / "tampered.yaml"
    tampered.write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(PolicyIntegrityError):
        load_policy_artifact(str(tampered))


def test_artifact_missing_spec_is_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("apiVersion: msval.policy/v1\nkind: PolicyBundle\n", encoding="utf-8")

    with pytest.raises(PolicyArtifactError):
        load_policy_artifact(str(bad))
