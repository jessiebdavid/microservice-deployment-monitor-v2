from typing import Any


def make_finding(
    *,
    rule_id: str,
    severity: str,
    message: str,
    remediation: str,
    object_reference: str,
    field_path: str,
    documentation_url: str,
) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "severity": severity,
        "object_reference": object_reference,
        "field_path": field_path,
        "message": message,
        "remediation": remediation,
        "documentation_url": documentation_url,
    }


def check_image(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings = []

    image = container.get("image")
    container_name = container.get("name") or "<unnamed>"

    object_reference = (
        f"Deployment/{deployment_name}"
        f" container/{container_name}"
    )

    if not image:
        findings.append(
            make_finding(
                rule_id="K8S-001",
                severity="BLOCK",
                message="Container image must be declared.",
                remediation="Set a container image reference.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].image"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/concepts/containers/images/"
                ),
            )
        )
        return findings

    if ":" not in image and "@sha256:" not in image:
        findings.append(
            make_finding(
                rule_id="K8S-001",
                severity="BLOCK",
                message=(
                    f"Image '{image}' does not contain a tag or digest."
                ),
                remediation=(
                    "Use an explicit image tag or immutable digest."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].image"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/concepts/containers/images/"
                ),
            )
        )

    return findings


def check_probes(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings = []

    container_name = container.get("name") or "<unnamed>"

    object_reference = (
        f"Deployment/{deployment_name}"
        f" container/{container_name}"
    )

    if not container.get("readiness_probe"):
        findings.append(
            make_finding(
                rule_id="K8S-002",
                severity="BLOCK",
                message="Container is missing a readiness probe.",
                remediation="Configure a readiness probe.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].readinessProbe"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"
                ),
            )
        )

    if not container.get("liveness_probe"):
        findings.append(
            make_finding(
                rule_id="K8S-002",
                severity="BLOCK",
                message="Container is missing a liveness probe.",
                remediation="Configure a liveness probe.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].livenessProbe"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"
                ),
            )
        )

    if not container.get("lifecycle"):
        findings.append(
            make_finding(
                rule_id="K8S-003",
                severity="WARN",
                message=(
                    "Container has no graceful shutdown "
                    "lifecycle configuration."
                ),
                remediation=(
                    "Configure a preStop lifecycle hook when "
                    "graceful shutdown requires it."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].lifecycle"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/concepts/containers/container-lifecycle-hooks/"
                ),
            )
        )

    return findings


def check_resources(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings = []

    container_name = container.get("name") or "<unnamed>"

    object_reference = (
        f"Deployment/{deployment_name}"
        f" container/{container_name}"
    )

    resources = container.get("resources") or {}
    requests = resources.get("requests") or {}
    limits = resources.get("limits") or {}

    if not requests.get("cpu") or not requests.get("memory"):
        findings.append(
            make_finding(
                rule_id="K8S-004",
                severity="BLOCK",
                message=(
                    "Container must define CPU and memory requests."
                ),
                remediation=(
                    "Add resources.requests.cpu and "
                    "resources.requests.memory."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].resources.requests"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
                ),
            )
        )

    if not limits.get("cpu") or not limits.get("memory"):
        findings.append(
            make_finding(
                rule_id="K8S-005",
                severity="BLOCK",
                message=(
                    "Container must define CPU and memory limits."
                ),
                remediation=(
                    "Add resources.limits.cpu and "
                    "resources.limits.memory."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].resources.limits"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
                ),
            )
        )

    return findings


def check_security_context(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings = []

    container_name = container.get("name") or "<unnamed>"

    object_reference = (
        f"Deployment/{deployment_name}"
        f" container/{container_name}"
    )

    security_context = container.get("security_context") or {}

    if security_context.get("runAsNonRoot") is not True:
        findings.append(
            make_finding(
                rule_id="K8S-006",
                severity="BLOCK",
                message=(
                    "Container must run as a non-root user."
                ),
                remediation=(
                    "Set securityContext.runAsNonRoot to true."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].securityContext.runAsNonRoot"
                ),
                documentation_url=(
                    "https://kubernetes.io/docs/tasks/configure-pod-container/security-context/"
                ),
            )
        )

    return findings


def check_metadata(
    deployment: dict[str, Any],
) -> list[dict[str, Any]]:
    findings = []

    deployment_name = deployment.get("name") or "<unnamed>"
    labels = deployment.get("labels") or {}

    object_reference = f"Deployment/{deployment_name}"

    if not labels.get("owner"):
        findings.append(
            make_finding(
                rule_id="K8S-007",
                severity="BLOCK",
                message="Deployment must declare an owner.",
                remediation=(
                    "Add the owner label to deployment metadata."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.owner",
                documentation_url="",
            )
        )

    if not labels.get("tier"):
        findings.append(
            make_finding(
                rule_id="K8S-008",
                severity="WARN",
                message="Deployment should declare a service tier.",
                remediation=(
                    "Add the tier label to deployment metadata."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.tier",
                documentation_url="",
            )
        )

    return findings


def check_architecture_consistency(
    architecture: dict[str, Any],
    deployment: dict[str, Any],
) -> list[dict[str, Any]]:
    findings = []

    service = architecture.get("service") or {}
    availability = architecture.get("availability") or {}

    service_name = service.get("name")
    service_owner = service.get("owner")
    service_tier = service.get("tier")
    expected_replicas = availability.get("replicas")

    deployment_name = deployment.get("name") or "<unnamed>"
    labels = deployment.get("labels") or {}
    actual_replicas = deployment.get("replicas")

    object_reference = f"Deployment/{deployment_name}"

    if (
        service_name
        and deployment_name
        and service_name != deployment_name
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-004",
                severity="BLOCK",
                message=(
                    f"Architecture service name '{service_name}' "
                    f"does not match Deployment name "
                    f"'{deployment_name}'."
                ),
                remediation=(
                    "Make service.name and metadata.name "
                    "refer to the same service."
                ),
                object_reference=object_reference,
                field_path="metadata.name",
                documentation_url="",
            )
        )

    if (
        service_owner
        and labels.get("owner")
        and service_owner != labels.get("owner")
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-005",
                severity="BLOCK",
                message=(
                    f"Architecture owner '{service_owner}' "
                    f"does not match deployment owner "
                    f"'{labels.get('owner')}'."
                ),
                remediation=(
                    "Make service.owner and metadata.labels.owner "
                    "refer to the same owning team."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.owner",
                documentation_url="",
            )
        )

    if (
        service_tier
        and labels.get("tier")
        and service_tier != labels.get("tier")
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-006",
                severity="BLOCK",
                message=(
                    f"Architecture tier '{service_tier}' "
                    f"does not match deployment tier "
                    f"'{labels.get('tier')}'."
                ),
                remediation=(
                    "Make service.tier and metadata.labels.tier "
                    "refer to the same service classification."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.tier",
                documentation_url="",
            )
        )

    if (
        isinstance(expected_replicas, int)
        and isinstance(actual_replicas, int)
        and expected_replicas != actual_replicas
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-007",
                severity="BLOCK",
                message=(
                    f"Architecture requires {expected_replicas} "
                    f"replicas but Deployment declares "
                    f"{actual_replicas}."
                ),
                remediation=(
                    "Make availability.replicas and "
                    "spec.replicas consistent."
                ),
                object_reference=object_reference,
                field_path="spec.replicas",
                documentation_url="",
            )
        )

    return findings


def evaluate_rules(
    deployment: dict[str, Any],
    architecture: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    findings = []

    findings.extend(check_metadata(deployment))

    if architecture is not None:
        findings.extend(
            check_architecture_consistency(
                architecture,
                deployment,
            )
        )

    deployment_name = deployment.get("name") or "<unnamed>"

    for container in deployment.get("containers", []):
        findings.extend(
            check_image(
                container,
                deployment_name,
            )
        )

        findings.extend(
            check_probes(
                container,
                deployment_name,
            )
        )

        findings.extend(
            check_resources(
                container,
                deployment_name,
            )
        )

        findings.extend(
            check_security_context(
                container,
                deployment_name,
            )
        )

    return findings