"""Policy evaluator abstraction for msval (MVP-1).

Defines the boundary between the validation pipeline and the policy
evaluation implementation. The pipeline hands a normalized
``ValidationRequest`` to a ``PolicyEvaluator`` and receives a structured
``EvaluationResult``. The default implementation is the deterministic
Python rule evaluator (``python-rules``).

The interface is intentionally small so a future WASM/Rego evaluator can
be added without touching the pipeline. The current WASM status (blocked
in this environment) and the exact tooling required are documented in
``edge/msval/README.md`` (section "WASM status").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from msval_edge.policy.catalog import get_policy_bundle


EVALUATOR_PYTHON_RULES = "python-rules"


@dataclass(frozen=True)
class ValidationRequest:
    """Normalized, structured input for one validation run."""

    architecture: dict[str, Any]
    kubernetes: dict[str, Any] | None
    policy_digest: str


@dataclass(frozen=True)
class EvaluationResult:
    """Structured output of one policy evaluation."""

    findings: list[dict[str, Any]] = field(default_factory=list)
    evaluator_version: str = EVALUATOR_PYTHON_RULES


class PolicyEvaluator(Protocol):
    """Interface every policy evaluator must satisfy.

    A future WASM/Rego evaluator implements the same protocol: it
    receives the normalized request and returns a structured result.
    """

    evaluator_version: str

    def evaluate(self, request: ValidationRequest) -> EvaluationResult:
        ...


class PythonRuleEvaluator:
    """Deterministic Python implementation of the MVP-1 rule pack."""

    evaluator_version = EVALUATOR_PYTHON_RULES

    def evaluate(self, request: ValidationRequest) -> EvaluationResult:
        from msval_edge.evaluation.rules import (
            check_architecture_consistency,
            check_dependencies,
            check_exposure,
            check_metadata,
        )

        findings: list[dict[str, Any]] = []

        findings.extend(check_dependencies(request.architecture))

        kubernetes = request.kubernetes

        if kubernetes is not None:
            for deployment in kubernetes.get("deployments") or []:
                findings.extend(check_metadata(deployment))

                findings.extend(
                    check_architecture_consistency(
                        request.architecture,
                        deployment,
                    )
                )

                deployment_name = deployment.get("name") or "<unnamed>"

                for container in deployment.get("containers", []):
                    findings.extend(
                        _check_container_rules(
                            container,
                            deployment_name,
                        )
                    )

            findings.extend(
                check_exposure(
                    request.architecture,
                    kubernetes,
                )
            )

        return EvaluationResult(
            findings=findings,
            evaluator_version=self.evaluator_version,
        )


def _check_container_rules(
    container: dict[str, Any],
    deployment_name: str,
) -> list[dict[str, Any]]:
    from msval_edge.evaluation.rules import (
        check_image,
        check_probes,
        check_resources,
        check_security_context,
    )

    findings: list[dict[str, Any]] = []

    findings.extend(check_image(container, deployment_name))
    findings.extend(check_probes(container, deployment_name))
    findings.extend(check_resources(container, deployment_name))
    findings.extend(
        check_security_context(container, deployment_name)
    )

    return findings


def create_default_evaluator() -> PolicyEvaluator:
    """Return the evaluator pinned by the policy artifact."""

    bundle = get_policy_bundle()

    if bundle.evaluator != EVALUATOR_PYTHON_RULES:
        raise ValueError(
            f"Policy artifact pins evaluator '{bundle.evaluator}' "
            f"but only '{EVALUATOR_PYTHON_RULES}' is implemented"
        )

    return PythonRuleEvaluator()
