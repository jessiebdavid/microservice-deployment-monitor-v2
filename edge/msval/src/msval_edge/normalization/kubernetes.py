"""Kubernetes normalization for msval (MVP-1).

Converts a multi-document rendered Kubernetes YAML input into the
normalized validation request consumed by the evaluator. The normalizer
supports Deployments (required), and Services and Ingresses for the
exposure rules. Empty documents and unsupported kinds are safely
ignored; malformed Deployments abort validation.
"""

from __future__ import annotations

from typing import Any

SUPPORTED_API_VERSIONS = {
    "apps/v1": {"Deployment"},
    "v1": {"Service"},
    "networking.k8s.io/v1": {"Ingress"},
}

IGNORED_KINDS = {"List", "ConfigMap", "Secret", "ServiceAccount"}


class KubernetesNormalizationError(Exception):
    """Raised when Kubernetes input cannot be normalized."""


def _require_mapping(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise KubernetesNormalizationError(
            f"{description} must be a mapping"
        )
    return value


def _document_identity(document: dict[str, Any]) -> str:
    kind = document.get("kind") or "<unknown>"
    metadata = document.get("metadata")
    name = "<unnamed>"

    if isinstance(metadata, dict) and metadata.get("name"):
        name = metadata["name"]

    return f"{kind}/{name}"


def _normalize_deployment(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Normalize one Deployment document (apps/v1).

    Raises KubernetesNormalizationError for malformed Deployments:
    a broken Deployment is a hard input error, not a rule finding.
    """

    if document.get("apiVersion") != "apps/v1":
        raise KubernetesNormalizationError(
            "Deployment must use apiVersion apps/v1"
        )

    if document.get("kind") != "Deployment":
        raise KubernetesNormalizationError(
            "Expected a Kubernetes Deployment"
        )

    metadata = _require_mapping(
        document.get("metadata"), "Deployment metadata"
    )
    spec = _require_mapping(document.get("spec"), "Deployment spec")
    template = _require_mapping(
        spec.get("template"), "Deployment spec.template"
    )
    pod_spec = _require_mapping(
        template.get("spec"), "Deployment spec.template.spec"
    )

    containers = pod_spec.get("containers")

    if not isinstance(containers, list) or not containers:
        raise KubernetesNormalizationError(
            "Deployment must contain at least one container"
        )

    normalized_containers: list[dict[str, Any]] = []

    for container in containers:
        if not isinstance(container, dict):
            raise KubernetesNormalizationError(
                "Each container must be a mapping"
            )

        normalized_containers.append(
            {
                "name": container.get("name"),
                "image": container.get("image"),
                "resources": container.get("resources", {}),
                "readiness_probe": container.get("readinessProbe"),
                "liveness_probe": container.get("livenessProbe"),
                "lifecycle": container.get("lifecycle"),
                "security_context": container.get(
                    "securityContext",
                    pod_spec.get("securityContext", {}),
                ),
            }
        )

    return {
        "kind": "Deployment",
        "api_version": document["apiVersion"],
        "name": metadata.get("name"),
        "namespace": metadata.get("namespace", "default"),
        "replicas": spec.get("replicas", 1),
        "labels": metadata.get("labels", {}),
        "containers": normalized_containers,
    }


def normalize_deployment(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Normalize a single Deployment document.

    Kept for backwards compatibility with existing callers and tests.
    """

    return _normalize_deployment(document)


def _normalize_service(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Normalize one v1 Service document for the exposure rules."""

    metadata = document.get("metadata")

    return {
        "kind": "Service",
        "name": (
            metadata.get("name")
            if isinstance(metadata, dict)
            else None
        ),
        "namespace": (
            metadata.get("namespace", "default")
            if isinstance(metadata, dict)
            else "default"
        ),
        "type": (document.get("spec") or {}).get("type", "ClusterIP"),
    }


def _normalize_ingress(
    document: dict[str, Any],
) -> dict[str, Any]:
    """Normalize one networking.k8s.io/v1 Ingress document."""

    metadata = document.get("metadata")
    spec = document.get("spec") or {}

    backends: set[str] = set()

    for rule in spec.get("rules") or []:
        if not isinstance(rule, dict):
            continue

        paths = (rule.get("http") or {}).get("paths") or []

        for path in paths:
            if not isinstance(path, dict):
                continue

            backend = path.get("backend") or {}
            service_backend = backend.get("service") or {}
            name = service_backend.get("name")

            if isinstance(name, str) and name:
                backends.add(name)

    return {
        "kind": "Ingress",
        "name": (
            metadata.get("name")
            if isinstance(metadata, dict)
            else None
        ),
        "namespace": (
            metadata.get("namespace", "default")
            if isinstance(metadata, dict)
            else "default"
        ),
        "backends": sorted(backends),
    }


def normalize_kubernetes_documents(
    documents: list[Any],
) -> dict[str, Any]:
    """Normalize a list of parsed YAML documents into the validation request.

    - Empty documents are ignored.
    - Deployments are normalized strictly; multiple Deployments are
      supported and normalized individually.
    - Services and Ingresses are normalized for the exposure rules.
    - Unsupported kinds are safely ignored.
    - The first valid Deployment is exposed as ``deployment`` for the
      architecture consistency rules; all of them are listed under
      ``deployments`` so findings can be identified per object.
    """

    deployments: list[dict[str, Any]] = []
    services: list[dict[str, Any]] = []
    ingresses: list[dict[str, Any]] = []
    ignored: list[dict[str, Any]] = []

    for index, document in enumerate(documents):
        if document is None:
            continue

        if not isinstance(document, dict):
            raise KubernetesNormalizationError(
                f"Kubernetes document {index} must be a YAML mapping"
            )

        kind = document.get("kind")

        if not isinstance(kind, str) or not kind:
            raise KubernetesNormalizationError(
                f"Kubernetes document {index} is missing 'kind'"
            )

        if kind in IGNORED_KINDS:
            ignored.append(_document_identity(document))
            continue

        api_version = document.get("apiVersion")
        supported_kinds = SUPPORTED_API_VERSIONS.get(api_version, set())

        if kind not in supported_kinds:
            ignored.append(_document_identity(document))
            continue

        if kind == "Deployment":
            deployments.append(_normalize_deployment(document))
        elif kind == "Service":
            services.append(_normalize_service(document))
        elif kind == "Ingress":
            ingresses.append(_normalize_ingress(document))

    if not deployments:
        raise KubernetesNormalizationError(
            "Kubernetes input must contain at least one Deployment"
        )

    return {
        "deployment": deployments[0],
        "deployments": deployments,
        "services": services,
        "ingresses": ingresses,
        "ignored_objects": ignored,
    }
