import argparse
import json
from pathlib import Path

import yaml

from msval_edge.evaluation.rules import evaluate_rules
from msval_edge.normalization.contract import validate_service_arch
from msval_edge.normalization.kubernetes import normalize_deployment
from msval_edge.normalization.yaml_loader import (
    YamlLoadError,
    load_yaml_file,
)
from msval_edge.policy.rules import RULES


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
        help="Path to rendered Kubernetes YAML",
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

    return {
        "tool": {
            "name": "msval",
            "version": "0.1.0",
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
    rules = {}
    results = []

    severity_to_level = {
        "BLOCK": "error",
        "WARN": "warning",
    }

    for finding in findings:
        rule_id = finding["rule_id"]

        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {
                    "text": finding["message"],
                },
                "help": {
                    "text": finding["remediation"],
                },
            }

        result = {
            "ruleId": rule_id,
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
                            or "kubernetes.yaml",
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
        "$schema": (
            "https://json.schemastore.org/sarif-2.1.0.json"
        ),
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "msval",
                        "version": "0.1.0",
                        "informationUri": (
                            "https://github.com/jessiebdavid/"
                            "microservice-deployment-monitor-v2"
                        ),
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "properties": {
                    "verdict": verdict,
                    "findingCount": len(findings),
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

    print(f"VERDICT: {verdict}")
    print()
    print("Architecture contract: PASS")

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
    if output_format in {"json", "sarif"}:
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
        else:
            print(
                json.dumps(
                    {
                        "$schema": (
                            "https://json.schemastore.org/"
                            "sarif-2.1.0.json"
                        ),
                        "version": "2.1.0",
                        "runs": [
                            {
                                "tool": {
                                    "driver": {
                                        "name": "msval",
                                        "version": "0.1.0",
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


def run_validate(
    architecture_path: str,
    kubernetes_path: str | None,
    output_format: str,
) -> int:
    try:
        architecture = load_yaml_file(architecture_path)
    except YamlLoadError as exc:
        print_machine_error(output_format, str(exc))
        return 2

    architecture_errors = validate_service_arch(architecture)

    if architecture_errors:
        if output_format == "json":
            print(
                json.dumps(
                    {
                        "tool": {
                            "name": "msval",
                            "version": "0.1.0",
                        },
                        "validation": {
                            "verdict": "FAIL",
                            "architecture": {
                                "path": architecture_path,
                                "status": "FAIL",
                            },
                        },
                        "errors": architecture_errors,
                    },
                    indent=2,
                )
            )
        elif output_format == "sarif":
            print(
                json.dumps(
                    {
                        "$schema": (
                            "https://json.schemastore.org/"
                            "sarif-2.1.0.json"
                        ),
                        "version": "2.1.0",
                        "runs": [
                            {
                                "tool": {
                                    "driver": {
                                        "name": "msval",
                                        "version": "0.1.0",
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
                                    for error in architecture_errors
                                ],
                            }
                        ],
                    },
                    indent=2,
                )
            )
        else:
            print(
                "FAIL: service architecture contract is invalid"
            )

            for error in architecture_errors:
                print(f"  - {error}")

        return 1

    findings = []

    if kubernetes_path:
        try:
            kubernetes_document = load_yaml_file(kubernetes_path)
        except YamlLoadError as exc:
            print_machine_error(output_format, str(exc))
            return 2

        if not isinstance(kubernetes_document, dict):
            message = "Kubernetes document must be a YAML mapping"
            print_machine_error(output_format, message)
            return 2

        try:
            normalized = normalize_deployment(
                kubernetes_document
            )
        except Exception as exc:
            message = (
                "Kubernetes normalization failed: "
                f"{exc}"
            )
            print_machine_error(output_format, message)
            return 2

        findings.extend(evaluate_rules(
                normalized,
                architecture,))

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
    rule = RULES.get(rule_id)

    if rule is None:
        print(f"Unknown rule: {rule_id}")
        print("Available rules:")

        for available_rule in RULES:
            print(f"  - {available_rule}")

        return 1

    print(f"Rule: {rule_id}")
    print(f"Severity: {rule['severity']}")
    print(f"Title: {rule['title']}")
    print(f"Description: {rule['description']}")
    print(f"Remediation: {rule['remediation']}")

    return 0


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

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


if __name__ == "__main__":
    main()