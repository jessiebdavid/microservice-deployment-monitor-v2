from pathlib import Path

import yaml

from msval_edge.normalization.kubernetes import (
    KubernetesNormalizationError,
    normalize_deployment,
)


EXAMPLES_DIR = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "kubernetes"
)


def load_example(name: str) -> dict:
    path = EXAMPLES_DIR / name

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_valid_deployment_normalizes():
    document = load_example("deployment.yaml")

    normalized = normalize_deployment(document)

    assert normalized["kind"] == "Deployment"
    assert normalized["api_version"] == "apps/v1"
    assert normalized["name"] == "payments-api"
    assert normalized["namespace"] == "default"
    assert normalized["replicas"] == 2
    assert len(normalized["containers"]) == 1

    container = normalized["containers"][0]

    assert container["name"] == "payments-api"
    assert container["image"] == "payments-api:2.1.0"
    assert container["readiness_probe"] is not None
    assert container["liveness_probe"] is not None
    assert container["lifecycle"] is not None
    assert container["security_context"]["runAsNonRoot"] is True


def test_bad_deployment_still_normalizes():
    document = load_example("bad-deployment.yaml")

    normalized = normalize_deployment(document)

    assert normalized["name"] == "payments-api"
    assert len(normalized["containers"]) == 1

    container = normalized["containers"][0]

    assert container["readiness_probe"] is None
    assert container["liveness_probe"] is None
    assert container["resources"] == {}
    assert container["security_context"]["runAsNonRoot"] is False


def test_wrong_kind_is_rejected():
    document = load_example("deployment.yaml")
    document["kind"] = "Service"

    try:
        normalize_deployment(document)
        assert False, "Expected KubernetesNormalizationError"
    except KubernetesNormalizationError as exc:
        assert "Expected a Kubernetes Deployment" in str(exc)


def test_missing_containers_is_rejected():
    document = load_example("deployment.yaml")

    del document["spec"]["template"]["spec"]["containers"]

    try:
        normalize_deployment(document)
        assert False, "Expected KubernetesNormalizationError"
    except KubernetesNormalizationError as exc:
        assert "at least one container" in str(exc)