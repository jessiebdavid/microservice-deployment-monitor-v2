"""Rule evaluation for msval (MVP-1 Python evaluator).

Implements the catalog rules that operate on the normalized validation
request: Kubernetes Deployment rules (K8S-*), architecture consistency
rules (ARCH-004..007), dependency rules (DEP-*) and exposure rules
(EXP-*). Rule metadata (severity, title, remediation, documentation URL)
always comes from the verified policy catalog, never from this module.
"""

from __future__ import annotations

from typing import Any

from msval_edge.policy.catalog import (
    RuleSpec,
    get_policy_bundle,
    get_rule_spec,
)


def make_finding(
    *,
    rule_id: str,
    message: str,
    object_reference: str,
    field_path: str,
) -> dict[str, Any]:
    """Build one finding, pulling metadata from the verified catalog."""

    spec: RuleSpec = get_rule_spec(rule_id)

    return {
        "rule_id": rule_id,
        "severity": spec.severity,
        "object_reference": object_reference,
        "field_path": field_path,
        "message": message,
        "remediation": spec.remediation,
        "documentation_url": spec.documentation_url,
    }


def _container_reference(
    deployment_name: str,
    container: dict[str, Any],
) -> str:
    container_name = container.get("name") or "<unnamed>"
    return f"Deployment/{deployment_name} container/{container_name}"


def check_image(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    image = container.get("image")
    object_reference = _container_reference(deployment_name, container)
    field_path = "spec.template.spec.containers[].image"

    if not image:
        findings.append(
            make_finding(
                rule_id="K8S-001",
                message="Container image must be declared.",
                object_reference=object_reference,
                field_path=field_path,
            )
        )
        return findings

    if ":" not in image and "@sha256:" not in image:
        findings.append(
            make_finding(
                rule_id="K8S-001",
                message=(
                    f"Image '{image}' does not contain a tag or digest."
                ),
                object_reference=object_reference,
                field_path=field_path,
            )
        )

    return findings


def check_probes(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    object_reference = _container_reference(deployment_name, container)

    if not container.get("readiness_probe"):
        findings.append(
            make_finding(
                rule_id="K8S-002",
                message="Container is missing a readiness probe.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].readinessProbe"
                ),
            )
        )

    if not container.get("liveness_probe"):
        findings.append(
            make_finding(
                rule_id="K8S-002",
                message="Container is missing a liveness probe.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].livenessProbe"
                ),
            )
        )

    if not container.get("lifecycle"):
        findings.append(
            make_finding(
                rule_id="K8S-003",
                message=(
                    "Container has no graceful shutdown "
                    "lifecycle configuration."
                ),
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[].lifecycle"
                ),
            )
        )

    return findings


def check_resources(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    object_reference = _container_reference(deployment_name, container)
    field_path = "spec.template.spec.containers[].resources"

    resources = container.get("resources") or {}
    requests = resources.get("requests") or {}
    limits = resources.get("limits") or {}

    if not requests.get("cpu") or not requests.get("memory"):
        findings.append(
            make_finding(
                rule_id="K8S-004",
                message=(
                    "Container must define CPU and memory requests."
                ),
                object_reference=object_reference,
                field_path=f"{field_path}.requests",
            )
        )

    if not limits.get("cpu") or not limits.get("memory"):
        findings.append(
            make_finding(
                rule_id="K8S-005",
                message=(
                    "Container must define CPU and memory limits."
                ),
                object_reference=object_reference,
                field_path=f"{field_path}.limits",
            )
        )

    return findings


def check_security_context(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    object_reference = _container_reference(deployment_name, container)

    security_context = container.get("security_context") or {}

    if security_context.get("runAsNonRoot") is not True:
        findings.append(
            make_finding(
                rule_id="K8S-006",
                message="Container must run as a non-root user.",
                object_reference=object_reference,
                field_path=(
                    "spec.template.spec.containers[]"
                    ".securityContext.runAsNonRoot"
                ),
            )
        )

    return findings


def check_metadata(deployment: dict[str, Any]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    deployment_name = deployment.get("name") or "<unnamed>"
    labels = deployment.get("labels") or {}
    object_reference = f"Deployment/{deployment_name}"

    if not labels.get("owner"):
        findings.append(
            make_finding(
                rule_id="K8S-007",
                message="Deployment must declare an owner.",
                object_reference=object_reference,
                field_path="metadata.labels.owner",
            )
        )

    if not labels.get("tier"):
        findings.append(
            make_finding(
                rule_id="K8S-008",
                message="Deployment should declare a service tier.",
                object_reference=object_reference,
                field_path="metadata.labels.tier",
            )
        )

    return findings


def check_architecture_consistency(
    architecture: dict[str, Any],
    deployment: dict[str, Any],
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

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

    # A Deployment belongs to the service when it is named after the
    # service or is a sub-deployment using the '<service>-<role>'
    # convention (e.g. payments-api-worker). Anything else is a
    # consistency violation (ARCH-004).
    belongs_to_service = (
        service_name
        and deployment_name
        and (
            service_name == deployment_name
            or deployment_name.startswith(f"{service_name}-")
        )
    )

    if (
        service_name
        and deployment_name
        and not belongs_to_service
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-004",
                message=(
                    f"Architecture service name '{service_name}' "
                    f"does not match Deployment name "
                    f"'{deployment_name}'."
                ),
                object_reference=object_reference,
                field_path="metadata.name",
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
                message=(
                    f"Architecture owner '{service_owner}' "
                    f"does not match deployment owner "
                    f"'{labels.get('owner')}'."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.owner",
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
                message=(
                    f"Architecture tier '{service_tier}' "
                    f"does not match deployment tier "
                    f"'{labels.get('tier')}'."
                ),
                object_reference=object_reference,
                field_path="metadata.labels.tier",
            )
        )

    if (
        isinstance(expected_replicas, int)
        and not isinstance(expected_replicas, bool)
        and isinstance(actual_replicas, int)
        and not isinstance(actual_replicas, bool)
        and expected_replicas != actual_replicas
    ):
        findings.append(
            make_finding(
                rule_id="ARCH-007",
                message=(
                    f"Architecture requires {expected_replicas} "
                    f"replicas but Deployment declares "
                    f"{actual_replicas}."
                ),
                object_reference=object_reference,
                field_path="spec.replicas",
            )
        )

    return findings


def check_dependencies(architecture: dict[str, Any]) -> list[dict[str, Any]]:
    """DEP-001/DEP-002: dependency target validity and layer direction."""

    findings: list[dict[str, Any]] = []
    service = architecture.get("service") or {}
    service_name = service.get("name")
    service_layer = service.get("layer")
    dependencies = architecture.get("dependencies") or []

    layers = get_policy_bundle().layers.ranking

    seen: set[str] = set()

    for index, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            continue

        prefix = f"dependencies[{index}]"
        name = dependency.get("name")
        layer = dependency.get("layer")

        if not isinstance(name, str) or not name.strip():
            findings.append(
                make_finding(
                    rule_id="DEP-001",
                    message=(
                        f"{prefix} must declare a non-empty target "
                        "service name."
                    ),
                    object_reference=(
                        f"service.arch/{service_name or '<unnamed>'}"
                    ),
                    field_path=f"{prefix}.name",
                )
            )
            continue

        prefix = f"dependencies[{index}] ({name})"

        if service_name and name == service_name:
            findings.append(
                make_finding(
                    rule_id="DEP-001",
                    message=(
                        f"{prefix} declares a dependency on the "
                        "service itself."
                    ),
                    object_reference=f"service.arch/{service_name}",
                    field_path=f"dependencies[{index}].name",
                )
            )

        if name in seen:
            findings.append(
                make_finding(
                    rule_id="DEP-001",
                    message=f"{prefix} is declared more than once.",
                    object_reference=(
                        f"service.arch/{service_name or '<unnamed>'}"
                    ),
                    field_path=f"dependencies[{index}].name",
                )
            )

        seen.add(name)

        if layer not in layers:
            findings.append(
                make_finding(
                    rule_id="DEP-001",
                    message=(
                        f"{prefix} declares layer '{layer}' which is "
                        f"not a valid architecture layer (expected "
                        f"one of: {', '.join(sorted(layers))})."
                    ),
                    object_reference=(
                        f"service.arch/{service_name or '<unnamed>'}"
                    ),
                    field_path=f"dependencies[{index}].layer",
                )
            )
            continue

        if isinstance(service_layer, str) and service_layer in layers:
            service_rank = layers[service_layer]
            dependency_rank = layers[layer]

            if dependency_rank < service_rank:
                findings.append(
                    make_finding(
                        rule_id="DEP-002",
                        message=(
                            f"{prefix} points upward: layer "
                            f"'{layer}' (rank {dependency_rank}) is "
                            f"higher than the service layer "
                            f"'{service_layer}' (rank "
                            f"{service_rank}). Dependencies must "
                            "point to the same or a deeper layer."
                        ),
                        object_reference=(
                            f"service.arch/{service_name}"
                        ),
                        field_path=f"dependencies[{index}].layer",
                    )
                )

    return findings


def check_exposure(
    architecture: dict[str, Any],
    kubernetes: dict[str, Any],
) -> list[dict[str, Any]]:
    """EXP-001/EXP-002: declared exposure versus rendered public edges."""

    findings: list[dict[str, Any]] = []
    service = architecture.get("service") or {}
    service_name = service.get("name") or "<unnamed>"
    exposure = architecture.get("exposure") or {}
    declared_public = exposure.get("public")

    if not isinstance(declared_public, bool):
        return findings

    deployment = kubernetes.get("deployment")
    deployment_name = (
        deployment.get("name") if isinstance(deployment, dict) else None
    )
    services = kubernetes.get("services") or []
    ingresses = kubernetes.get("ingresses") or []

    ingress_backends = _collect_ingress_backends(ingresses)
    load_balancer_targets = _collect_load_balancer_targets(services)

    object_reference = (
        f"Deployment/{deployment_name}"
        if deployment_name
        else f"service.arch/{service_name}"
    )

    if declared_public:
        exposed = (
            service_name in ingress_backends
            or service_name in load_balancer_targets
        )

        if not exposed:
            findings.append(
                make_finding(
                    rule_id="EXP-001",
                    message=(
                        f"Service '{service_name}' is declared public "
                        "but no rendered Ingress or "
                        "LoadBalancer/NodePort Service exposes it."
                    ),
                    object_reference=object_reference,
                    field_path="exposure.public",
                )
            )
    else:
        for backend in sorted(ingress_backends):
            if backend == service_name:
                findings.append(
                    make_finding(
                        rule_id="EXP-002",
                        message=(
                            f"Service '{service_name}' is declared "
                            "non-public but an Ingress routes to it."
                        ),
                        object_reference=(
                            f"service.arch/{service_name}"
                        ),
                        field_path="exposure.public",
                    )
                )

        for target in sorted(load_balancer_targets):
            if target == service_name:
                findings.append(
                    make_finding(
                        rule_id="EXP-002",
                        message=(
                            f"Service '{service_name}' is declared "
                            "non-public but a "
                            "LoadBalancer/NodePort Service targets "
                            "it."
                        ),
                        object_reference=(
                            f"service.arch/{service_name}"
                        ),
                        field_path="exposure.public",
                    )
                )

    return findings


def _collect_ingress_backends(
    ingresses: list[dict[str, Any]],
) -> set[str]:
    backends: set[str] = set()

    for ingress in ingresses:
        backends.update(ingress.get("backends") or [])

    return backends


def _collect_load_balancer_targets(
    services: list[dict[str, Any]],
) -> set[str]:
    """Collect names of public Services from the normalized shape."""

    targets: set[str] = set()

    for service in services:
        service_type = service.get("type", "ClusterIP")

        if service_type in ("LoadBalancer", "NodePort"):
            name = service.get("name")

            if isinstance(name, str) and name:
                targets.add(name)

    return targets


def evaluate_rules(
    deployment: dict[str, Any],
    architecture: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Evaluate Deployment-level rules (K8S-*, ARCH-004..007).

    Kept for backwards compatibility with existing callers and tests.
    """

    findings: list[dict[str, Any]] = []

    findings.extend(check_metadata(deployment))

    if architecture is not None:
        findings.extend(
            check_architecture_consistency(architecture, deployment)
        )

    deployment_name = deployment.get("name") or "<unnamed>"

    for container in deployment.get("containers", []):
        findings.extend(check_image(container, deployment_name))
        findings.extend(check_probes(container, deployment_name))
        findings.extend(check_resources(container, deployment_name))
        findings.extend(
            check_security_context(container, deployment_name)
        )

    return findings
