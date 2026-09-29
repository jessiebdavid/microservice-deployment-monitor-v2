from typing import Any


class KubernetesNormalizationError(Exception):
    """Raised when Kubernetes input cannot be normalized."""


def normalize_deployment(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("apiVersion") != "apps/v1":
        raise KubernetesNormalizationError(
            "Deployment must use apiVersion apps/v1"
        )

    if document.get("kind") != "Deployment":
        raise KubernetesNormalizationError(
            "Expected a Kubernetes Deployment"
        )

    metadata = document.get("metadata")

    if not isinstance(metadata, dict):
        raise KubernetesNormalizationError(
            "Deployment metadata must be a mapping"
        )

    spec = document.get("spec")

    if not isinstance(spec, dict):
        raise KubernetesNormalizationError(
            "Deployment spec must be a mapping"
        )

    template = spec.get("template")

    if not isinstance(template, dict):
        raise KubernetesNormalizationError(
            "Deployment spec.template must be a mapping"
        )

    pod_spec = template.get("spec")

    if not isinstance(pod_spec, dict):
        raise KubernetesNormalizationError(
            "Deployment spec.template.spec must be a mapping"
        )

    containers = pod_spec.get("containers")

    if not isinstance(containers, list) or not containers:
        raise KubernetesNormalizationError(
            "Deployment must contain at least one container"
        )

    normalized_containers = []

    for container in containers:
        if not isinstance(container, dict):
            raise KubernetesNormalizationError(
                "Each container must be a mapping"
            )

        image = container.get("image")

        normalized_containers.append(
            {
                "name": container.get("name"),
                "image": image,
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