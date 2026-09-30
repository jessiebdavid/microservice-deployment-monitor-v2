"""MVP-1 acceptance tests (Phase I).

End-to-end CLI verification: golden path, known-bad deployments,
architecture/dependency/exposure violations, malformed input,
multi-document manifests, output formats, determinism and explain.
"""

import json
import subprocess
import sys
from pathlib import Path

import yaml


MSVAL_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = MSVAL_ROOT / "examples"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "msval_edge.cli.main", *args],
        capture_output=True,
        text=True,
        cwd=MSVAL_ROOT,
    )


def write_yaml(tmp_path: Path, name: str, document) -> str:
    path = tmp_path / name
    path.write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )
    return str(path)


# --- Golden path -------------------------------------------------------


def test_golden_deployment_passes():
    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "deployment.yaml"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: PASS" in result.stdout


def test_bad_deployment_fails_with_blocking_findings():
    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "bad-deployment.yaml"),
    )

    assert result.returncode == 1
    assert "VERDICT: FAIL" in result.stdout
    assert "Blocking:" in result.stdout

    for rule_id in ("K8S-002", "K8S-004", "K8S-005", "K8S-006"):
        assert rule_id in result.stdout


# --- Architecture / dependency / exposure violations -------------------


def test_architecture_name_mismatch_fails(tmp_path):
    document = yaml.safe_load(
        (EXAMPLES / "kubernetes" / "deployment.yaml").read_text(
            encoding="utf-8"
        )
    )
    document["metadata"]["name"] = "renamed-payments-api"

    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        write_yaml(tmp_path, "mismatch.yaml", document),
    )

    assert result.returncode == 1
    assert "ARCH-004" in result.stdout


def test_replica_mismatch_fails(tmp_path):
    document = yaml.safe_load(
        (EXAMPLES / "kubernetes" / "deployment.yaml").read_text(
            encoding="utf-8"
        )
    )
    document["spec"]["replicas"] = 5

    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        write_yaml(tmp_path, "replicas.yaml", document),
    )

    assert result.returncode == 1
    assert "ARCH-007" in result.stdout


def test_dependency_violation_fails(tmp_path):
    architecture = yaml.safe_load(
        (EXAMPLES / "service.arch.yaml").read_text(encoding="utf-8")
    )
    architecture["dependencies"].append(
        {"name": "edge-gateway", "layer": "edge", "required": True}
    )

    result = run_cli(
        "validate",
        "--architecture",
        write_yaml(tmp_path, "arch-dep.yaml", architecture),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "deployment.yaml"),
    )

    assert result.returncode == 1
    assert "DEP-002" in result.stdout


def test_exposure_violation_fails(tmp_path):
    deployment = yaml.safe_load(
        (EXAMPLES / "kubernetes" / "deployment.yaml").read_text(
            encoding="utf-8"
        )
    )
    public_service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "payments-api"},
        "spec": {"type": "LoadBalancer"},
    }

    manifest = tmp_path / "exposed.yaml"
    manifest.write_text(
        yaml.safe_dump(deployment, sort_keys=False)
        + "---\n"
        + yaml.safe_dump(public_service, sort_keys=False),
        encoding="utf-8",
    )

    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(manifest),
    )

    assert result.returncode == 1
    assert "EXP-002" in result.stdout


# --- Multi-document -----------------------------------------------------


def test_multi_document_manifest_passes():
    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "multi-doc.yaml"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "VERDICT: PASS" in result.stdout


# --- Malformed input ----------------------------------------------------


def test_missing_architecture_file_is_clean_error():
    result = run_cli(
        "validate",
        "--architecture",
        "does-not-exist.yaml",
    )

    assert result.returncode == 2
    assert "File not found" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_invalid_yaml_is_clean_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("kind: Deployment\n  broken: [unclosed\n", encoding="utf-8")

    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(bad),
    )

    assert result.returncode == 2
    assert "Invalid YAML" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_malformed_architecture_contract_fails(tmp_path):
    bad_architecture = {
        "version": "0.1",
        "service": {"name": "payments-api"},
    }

    result = run_cli(
        "validate",
        "--architecture",
        write_yaml(tmp_path, "bad-arch.yaml", bad_architecture),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "deployment.yaml"),
    )

    assert result.returncode == 1
    assert "service.owner is required" in result.stdout


def test_kubernetes_input_without_deployment_is_clean_error(tmp_path):
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": "only"},
    }

    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        write_yaml(tmp_path, "service-only.yaml", service),
    )

    assert result.returncode == 2
    assert "at least one Deployment" in result.stdout
    assert "Traceback" not in result.stdout


# --- JSON output --------------------------------------------------------


def test_json_output_is_valid_and_stable():
    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "bad-deployment.yaml"),
        "--format",
        "json",
    )

    assert result.returncode == 1

    payload = json.loads(result.stdout)

    assert payload["tool"]["name"] == "msval"
    assert payload["policy"]["version"] == "1.0.0"
    assert payload["policy"]["digest"].startswith("sha256:")
    assert payload["policy"]["evaluator"] == "python-rules"
    assert payload["validation"]["verdict"] == "FAIL"
    assert payload["summary"]["blocking"] >= 4

    required_fields = {
        "rule_id",
        "severity",
        "object_reference",
        "field_path",
        "message",
        "remediation",
        "documentation_url",
    }

    for finding in payload["findings"]:
        assert required_fields.issubset(finding.keys())


def test_json_output_is_deterministic():
    args = (
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "bad-deployment.yaml"),
        "--format",
        "json",
    )

    first = run_cli(*args)
    second = run_cli(*args)

    assert first.stdout == second.stdout


# --- SARIF output --------------------------------------------------------


def test_sarif_output_is_valid_structure():
    result = run_cli(
        "validate",
        "--architecture",
        str(EXAMPLES / "service.arch.yaml"),
        "--kubernetes",
        str(EXAMPLES / "kubernetes" / "bad-deployment.yaml"),
        "--format",
        "sarif",
    )

    assert result.returncode == 1

    sarif = json.loads(result.stdout)

    assert sarif["version"] == "2.1.0"
    assert sarif["$schema"].endswith("sarif-2.1.0.json")
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    driver = run["tool"]["driver"]

    assert driver["name"] == "msval"
    assert driver["version"] == "0.1.0"

    rule_ids = {rule["id"] for rule in driver["rules"]}
    result_rule_ids = {item["ruleId"] for item in run["results"]}

    assert result_rule_ids.issubset(rule_ids)

    for item in run["results"]:
        assert item["level"] in ("error", "warning")
        assert "locations" in item

    assert run["properties"]["verdict"] == "FAIL"
    assert run["properties"]["policy"]["version"] == "1.0.0"


# --- Explain -------------------------------------------------------------


def test_explain_known_rule():
    result = run_cli("explain", "K8S-001")

    assert result.returncode == 0
    assert "Rule: K8S-001" in result.stdout
    assert "Severity: BLOCK" in result.stdout
    assert "Remediation:" in result.stdout
    assert "Documentation:" in result.stdout


def test_explain_unknown_rule_lists_rules():
    result = run_cli("explain", "NOT-A-RULE")

    assert result.returncode == 1
    assert "Unknown rule" in result.stdout
    assert "K8S-001" in result.stdout
    assert "DEP-001" in result.stdout
    assert "EXP-001" in result.stdout


# --- Init ---------------------------------------------------------------


def test_init_creates_contract(tmp_path):
    output = tmp_path / "service.arch.yaml"

    result = run_cli("init", "--output", str(output))

    assert result.returncode == 0

    document = yaml.safe_load(output.read_text(encoding="utf-8"))

    assert document["version"] == "0.1"
    assert document["service"]["name"] == "my-service"


def test_init_refuses_to_overwrite(tmp_path):
    output = tmp_path / "service.arch.yaml"
    output.write_text("existing\n", encoding="utf-8")

    result = run_cli("init", "--output", str(output))

    assert result.returncode == 2
