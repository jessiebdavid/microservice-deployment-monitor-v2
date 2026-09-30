"""Tests for multi-document Kubernetes normalization (Phase A)."""

from pathlib import Path

import yaml

from msval_edge.normalization.kubernetes import (
    KubernetesNormalizationError,
    normalize_deployment,
    normalize_kubernetes_documents,
)


EXAMPLES_DIR = (
    Path(__file__).resolve().parents[1] / "examples" / "kubernetes"
)


def load_example(name: str) -> dict:
    path = EXAMPLES_DIR / name

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def test_single_deployment_document_normalizes():
    documents = load_yaml_file_load("deployment.yaml")

    result = normalize_kubernetes_documents(documents)

    assert result["deployment"]["name"] == "payments-api"
    assert len(result["deployments"]) == 1
    assert result["services"] == []
    assert result["ingresses"] == []


def load_yaml_file_load(name: str) -> list:
    import pytest

    from msval_edge.normalization.yaml_loader import load_yaml_file

    return load_yaml_file(EXAMPLES_DIR / name)


def test_multi_document_manifest_is_supported():
    documents = load_yaml_file_load("multi-doc.yaml")

    result = normalize_kubernetes_documents(documents)

    assert result["deployment"]["name"] == "payments-api"
    assert result["services"][0]["name"] == "payments-api"
    assert result["services"][0]["type"] == "ClusterIP"
    assert result["ignored_objects"] == ["ConfigMap/payments-api-config"]


def test_multiple_deployments_are_supported():
    first = load_example("deployment.yaml")
    second = load_example("deployment.yaml")
    second["metadata"]["name"] = "payments-api-worker"

    result = normalize_kubernetes_documents([first, second])

    assert [d["name"] for d in result["deployments"]] == [
        "payments-api",
        "payments-api-worker",
    ]
    assert result["deployment"]["name"] == "payments-api"


def test_unsupported_kinds_are_safely_ignored():
    documents = load_yaml_file_load("multi-doc.yaml")

    result = normalize_kubernetes_documents(documents)

    assert "ConfigMap/payments-api-config" in result["ignored_objects"]


def test_input_without_deployment_is_rejected():
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "only-service"},
    }

    try:
        normalize_kubernetes_documents([service])
        assert False, "Expected KubernetesNormalizationError"
    except KubernetesNormalizationError as exc:
        assert "at least one Deployment" in str(exc)


def test_document_missing_kind_is_rejected():
    try:
        normalize_kubernetes_documents([{"apiVersion": "v1"}])
        assert False, "Expected KubernetesNormalizationError"
    except KubernetesNormalizationError as exc:
        assert "missing 'kind'" in str(exc)


def test_malformed_deployment_is_rejected():
    deployment = load_example("deployment.yaml")
    del deployment["spec"]["template"]["spec"]["containers"]

    try:
        normalize_kubernetes_documents([deployment])
        assert False, "Expected KubernetesNormalizationError"
    except KubernetesNormalizationError as exc:
        assert "at least one container" in str(exc)


def test_legacy_single_document_normalize_deployment_works():
    document = load_example("deployment.yaml")

    normalized = normalize_deployment(document)

    assert normalized["name"] == "payments-api"
    assert normalized["kind"] == "Deployment"
