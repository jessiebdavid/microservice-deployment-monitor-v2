"""msval CLI (MVP-1).

Commands:

- ``msval init``      -- create a starter service.arch.yaml
- ``msval validate``  -- validate architecture + rendered Kubernetes input
- ``msval explain``   -- explain one rule from the pinned policy catalog

Output formats: human, json, sarif. Exit codes: 0 = PASS/WARN,
1 = FAIL (blocking findings or contract errors), 2 = input error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from msval_edge.evaluation.evaluator import (
    ValidationRequest,
    create_default_evaluator,
)
from msval_edge.normalization.contract import validate_service_arch
from msval_edge.normalization.kubernetes import (
    KubernetesNormalizationError,
    normalize_kubernetes_documents,
)
from msval_edge.normalization.yaml_loader import (
    YamlLoadError,
    load_yaml_file,
)
from msval_edge.policy.catalog import (
    PolicyArtifactError,
    get_policy_bundle,
)

SARIF_SCHEMA = (
    "https://json.schemastore.org/sarif-2.1.0.json"
)
SARIF_VERSION = "2.1.0"
MSVAL_README_URL = (
    "https://github.com/jessiebdavid/"
    "microservice-deployment-monitor-v2/blob/main/edge/msval/README.md"
)
TOOL_NAME = "msval"
TOOL_VERSION = "0.1.0"

DEFAULT_SERVICE_ARCH = {
    "version": "0.1",
    "service": {
        "name": "my-service",
        "owner": "platform-team",
        "layer": "domain",
        "tier": "standard",
    },
    "exposure": {
        "public": False,
    },
    "dependencies": [],
    "availability": {
        "replicas": 1,
        "requires_health_checks": True,
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msval",
        description="Microservices architecture and deployment validator",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a service architecture validation contract",
    )

    init_parser.add_argument(
        "--output",
        default="service.arch.yaml",
        help="Output contract path",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate architecture and deployment inputs",
    )

    validate_parser.add_argument(
        "--architecture",
        default="service.arch.yaml",
        help="Path to service.arch.yaml",
    )

    validate_parser.add_argument(
        "--kubernetes",
        help="Path to rendered Kubernetes YAML (multi-document)",
    )

    validate_parser.add_argument(
        "--format",
        choices=["human", "json", "sarif"],
        default="human",
        help="Validation output format",
    )

    explain_parser = subparsers.add_parser(
        "explain",
        help="Explain a validation rule",
    )

    explain_parser.add_argument(
        "rule_id",
        help="Rule ID to explain",
    )

    return parser


def run_init(path: str) -> int:
    output_path = Path(path)

    if output_path.exists():
        print(f"ERROR: file already exists: {output_path}")
        print("Use a different --output path or remove the existing file.")
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            DEFAULT_SERVICE_ARCH,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    print(f"Created service architecture contract: {output_path}")
    return 0


def _policy_metadata() -> dict:
    bundle = get_policy_bundle()

    return {
        "name": bundle.name,
        "version": bundle.version,
        "digest": bundle.digest,
    }


def build_result(
    architecture_path: str,
    kubernetes_path: str | None,
    findings: list[dict],
    verdict: str,
) -> dict:
    blocking = [
        finding
        for finding in findings
        if finding["severity"] == "BLOCK"
    ]

    warnings = [
        finding
        for finding in findings
        if finding["severity"] == "WARN"
    ]

    policy = _policy_metadata()

    return {
        "tool": {
            "name": TOOL_NAME,
            "version": TOOL_VERSION,
        },
        "policy": {
            "artifact": policy["name"],
            "version": policy["version"],
            "digest": policy["digest"],
            "evaluator": "python-rules",
        },
        "validation": {
            "verdict": verdict,
            "architecture": {
                "path": architecture_path,
                "status": "PASS",
            },
            "kubernetes": {
                "path": kubernetes_path,
                "status": "PASS" if not blocking else "FAIL",
            },
        },
        "summary": {
            "findings": len(findings),
            "blocking": len(blocking),
            "warnings": len(warnings),
        },
        "findings": findings,
    }


def build_sarif_result(
    findings: list[dict],
    verdict: str,
    kubernetes_path: str | None,
) -> dict:
    """Build a SARIF 2.1.0 run from the verified policy catalog."""

    bundle = get_policy_bundle()

    reported_ids = dict.fromkeys(
        finding["rule_id"] for finding in findings
    )

    rules = []

    for rule_id in reported_ids:
        spec = bundle.rules[rule_id]

        rule = {
            "id": rule_id,
            "name": spec.title,
            "shortDescription": {
                "text": spec.title,
            },
            "fullDescription": {
                "text": spec.description,
            },
            "help": {
                "text": spec.remediation,
            },
            "properties": {
                "category": spec.category,
                "severity": spec.severity,
            },
        }

        if spec.documentation_url:
            rule["helpUri"] = spec.documentation_url

        rules.append(rule)

    severity_to_level = {
        "BLOCK": "error",
        "WARN": "warning",
    }

    results = []

    for finding in findings:
        result = {
            "ruleId": finding["rule_id"],
            "level": severity_to_level.get(
                finding["severity"],
                "warning",
            ),
            "message": {
                "text": finding["message"],
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": kubernetes_path
                            or "service.arch.yaml",
                        }
                    },
                    "logicalLocations": [
                        {
                            "fullyQualifiedName": (
                                finding["object_reference"]
                            )
                        }
                    ],
                }
            ],
            "properties": {
                "severity": finding["severity"],
                "fieldPath": finding["field_path"],
                "remediation": finding["remediation"],
            },
        }

        if finding.get("documentation_url"):
            result["helpUri"] = finding["documentation_url"]

        results.append(result)

    return {
        "$schema": SARIF_SCHEMA,
        "version": SARIF_VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                        "informationUri": MSVAL_README_URL,
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": {
                    "verdict": verdict,
                    "findingCount": len(findings),
                    "policy": _policy_metadata(),
                    "evaluator": "python-rules",
                },
            }
        ],
    }


def print_human_result(
    architecture_path: str,
    kubernetes_path: str | None,
    findings: list[dict],
    verdict: str,
) -> None:
    blocking = [
        finding
        for finding in findings
        if finding["severity"] == "BLOCK"
    ]

    warnings = [
        finding
        for finding in findings
        if finding["severity"] == "WARN"
    ]

    policy = _policy_metadata()

    print(f"VERDICT: {verdict}")
    print()
    print("Architecture contract: PASS")
    print(
        f"Policy: {policy['name']} v{policy['version']} "
        f"({policy['digest'][:19]}...)"
    )
    print("Evaluator: python-rules")

    if kubernetes_path:
        print(f"Kubernetes input: {kubernetes_path}")
        print(f"Findings: {len(findings)}")
        print(f"Blocking: {len(blocking)}")
        print(f"Warnings: {len(warnings)}")

        for finding in findings:
            print(
                f"- {finding['rule_id']} | "
                f"{finding['severity']} | "
                f"{finding['message']}"
            )

            print(
                f"  Object: {finding['object_reference']}"
            )

            print(
                f"  Field: {finding['field_path']}"
            )

            print(
                f"  Remediation: {finding['remediation']}"
            )

            if finding.get("documentation_url"):
                print(
                    f"  Documentation: "
                    f"{finding['documentation_url']}"
                )


def print_machine_error(
    output_format: str,
    message: str,
) -> None:
    if output_format == "json":
        print(
            json.dumps(
                {
                    "status": "ERROR",
                    "message": message,
                },
                indent=2,
            )
        )
    elif output_format == "sarif":
        print(
            json.dumps(
                {
                    "$schema": SARIF_SCHEMA,
                    "version": SARIF_VERSION,
                    "runs": [
                        {
                            "tool": {
                                "driver": {
                                    "name": TOOL_NAME,
                                    "version": TOOL_VERSION,
                                }
                            },
                            "results": [
                                {
                                    "level": "error",
                                    "message": {
                                        "text": message,
                                    },
                                }
                            ],
                        }
                    ],
                },
                indent=2,
            )
        )
    else:
        print(f"ERROR: {message}")


def _print_contract_errors(
    output_format: str,
    architecture_path: str,
    errors: list[str],
) -> None:
    if output_format == "json":
        print(
            json.dumps(
                {
                    "tool": {
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                    },
                    "validation": {
                        "verdict": "FAIL",
                        "architecture": {
                            "path": architecture_path,
                            "status": "FAIL",
                        },
                    },
                    "errors": errors,
                },
                indent=2,
            )
        )
    elif output_format == "sarif":
        print(
            json.dumps(
                {
                    "$schema": SARIF_SCHEMA,
                    "version": SARIF_VERSION,
                    "runs": [
                        {
                            "tool": {
                                "driver": {
                                    "name": TOOL_NAME,
                                    "version": TOOL_VERSION,
                                }
                            },
                            "results": [
                                {
                                    "ruleId": "ARCH-CONTRACT",
                                    "level": "error",
                                    "message": {
                                        "text": error,
                                    },
                                }
                                for error in errors
                            ],
                        }
                    ],
                },
                indent=2,
            )
        )
    else:
        print("FAIL: service architecture contract is invalid")

        for error in errors:
            print(f"  - {error}")


def run_validate(
    architecture_path: str,
    kubernetes_path: str | None,
    output_format: str,
) -> int:
    try:
        architecture_documents = load_yaml_file(architecture_path)
    except YamlLoadError as exc:
        print_machine_error(output_format, str(exc))
        return 2

    if len(architecture_documents) != 1:
        message = (
            "service.arch.yaml must contain exactly one YAML document"
        )
        print_machine_error(output_format, message)
        return 2

    architecture = architecture_documents[0]
    architecture_errors = validate_service_arch(architecture)

    if architecture_errors:
        _print_contract_errors(
            output_format,
            architecture_path,
            architecture_errors,
        )
        return 1

    findings: list[dict] = []
    kubernetes_request: dict | None = None

    if kubernetes_path:
        try:
            kubernetes_documents = load_yaml_file(kubernetes_path)
        except YamlLoadError as exc:
            print_machine_error(output_format, str(exc))
            return 2

        try:
            kubernetes_request = normalize_kubernetes_documents(
                kubernetes_documents
            )
        except KubernetesNormalizationError as exc:
            message = (
                "Kubernetes normalization failed: "
                f"{exc}"
            )
            print_machine_error(output_format, message)
            return 2

        evaluator = create_default_evaluator()

        evaluation = evaluator.evaluate(
            ValidationRequest(
                architecture=architecture,
                kubernetes=kubernetes_request,
                policy_digest=get_policy_bundle().digest,
            )
        )

        findings = evaluation.findings

    else:
        evaluator = create_default_evaluator()

        evaluation = evaluator.evaluate(
            ValidationRequest(
                architecture=architecture,
                kubernetes=None,
                policy_digest=get_policy_bundle().digest,
            )
        )

        findings = evaluation.findings

    blocking = [
        finding
        for finding in findings
        if finding["severity"] == "BLOCK"
    ]

    warnings = [
        finding
        for finding in findings
        if finding["severity"] == "WARN"
    ]

    if blocking:
        verdict = "FAIL"
    elif warnings:
        verdict = "WARN"
    else:
        verdict = "PASS"

    if output_format == "json":
        result = build_result(
            architecture_path,
            kubernetes_path,
            findings,
            verdict,
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    elif output_format == "sarif":
        result = build_sarif_result(
            findings,
            verdict,
            kubernetes_path,
        )

        print(
            json.dumps(
                result,
                indent=2,
            )
        )

    else:
        print_human_result(
            architecture_path,
            kubernetes_path,
            findings,
            verdict,
        )

    return 1 if blocking else 0


def run_explain(rule_id: str) -> int:
    try:
        bundle = get_policy_bundle()
        rule = bundle.rules.get(rule_id)
    except PolicyArtifactError as exc:
        print(f"ERROR: {exc}")
        return 2

    if rule is None:
        print(f"Unknown rule: {rule_id}")
        print("Available rules:")

        for available_rule in bundle.rules:
            spec = bundle.rules[available_rule]
            print(
                f"  - {available_rule} "
                f"[{spec.severity}] {spec.title}"
            )

        return 1

    print(f"Rule: {rule.rule_id}")
    print(f"Severity: {rule.severity}")
    print(f"Category: {rule.category}")
    print(f"Title: {rule.title}")
    print(f"Description: {rule.description}")
    print(f"Remediation: {rule.remediation}")
    print(f"Documentation: {rule.documentation_url}")

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "init":
            raise SystemExit(run_init(args.output))

        if args.command == "validate":
            raise SystemExit(
                run_validate(
                    args.architecture,
                    args.kubernetes,
                    args.format,
                )
            )

        if args.command == "explain":
            raise SystemExit(run_explain(args.rule_id))

    except YamlLoadError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2)

    except PolicyArtifactError as exc:
        print(f"ERROR: policy artifact: {exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
