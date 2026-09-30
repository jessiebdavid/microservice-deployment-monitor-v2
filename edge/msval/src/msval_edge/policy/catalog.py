"""Authoritative rule catalog for msval.

Single source of truth for all rule metadata. The catalog is loaded from
the pinned policy artifact under ``msval_edge/policy/artifacts/`` and is
integrity-verified with a SHA-256 digest over the canonical JSON form of
the ``spec`` section before use.

Every rule that msval can report is defined in the policy artifact. The
evaluator, the CLI ``explain`` command, JSON output and SARIF output all
read metadata from this catalog, so there are no orphaned rules and no
duplicated metadata.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib import resources
from typing import Any

import yaml

from msval_edge.normalization.yaml_loader import YamlLoadError, load_yaml_file


POLICY_PACKAGE = "msval_edge.policy"
POLICY_ARTIFACT_DIR = "artifacts"
PINNED_POLICY_ARTIFACT = "msval-default-policy-1.0.0.yaml"
PINNED_POLICY_DIGEST = "sha256:033ac69277e702bf9edcadecb64b4daab8eaffccd96e7cc56a07954217ab134c"

POLICY_SCHEMA_VERSION = "msval.policy/v1"


class PolicyArtifactError(Exception):
    """Raised when the pinned policy artifact is missing or invalid."""


class PolicyIntegrityError(PolicyArtifactError):
    """Raised when the policy artifact fails digest verification."""


@dataclass(frozen=True)
class RuleSpec:
    """Immutable metadata for one validation rule."""

    rule_id: str
    severity: str
    title: str
    description: str
    remediation: str
    documentation_url: str
    category: str


@dataclass(frozen=True)
class LayerModel:
    """Pinned architecture layer ranking used by dependency rules."""

    ranking: dict[str, int]
    dependency_direction: str


@dataclass(frozen=True)
class PolicyBundle:
    """A verified policy artifact."""

    name: str
    version: str
    digest: str
    evaluator: str
    layers: LayerModel
    rules: dict[str, RuleSpec]


def _canonical_spec_bytes(spec: dict[str, Any]) -> bytes:
    return json.dumps(
        spec,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _sha256_digest(spec: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_spec_bytes(spec)).hexdigest()


def parse_policy_document(document: Any) -> PolicyBundle:
    """Validate and parse a policy bundle document into a PolicyBundle."""

    if not isinstance(document, dict):
        raise PolicyArtifactError("Policy artifact root must be a YAML mapping")

    if document.get("apiVersion") != POLICY_SCHEMA_VERSION:
        raise PolicyArtifactError(
            f"Policy artifact apiVersion must be '{POLICY_SCHEMA_VERSION}'"
        )

    if document.get("kind") != "PolicyBundle":
        raise PolicyArtifactError("Policy artifact kind must be 'PolicyBundle'")

    metadata = document.get("metadata")

    if not isinstance(metadata, dict):
        raise PolicyArtifactError("Policy artifact metadata must be a mapping")

    name = metadata.get("name")
    version = metadata.get("version")

    if not isinstance(name, str) or not name:
        raise PolicyArtifactError("Policy artifact metadata.name must be a non-empty string")

    if not isinstance(version, str) or not version:
        raise PolicyArtifactError("Policy artifact metadata.version must be a non-empty string")

    spec = document.get("spec")

    if not isinstance(spec, dict):
        raise PolicyArtifactError("Policy artifact spec must be a mapping")

    integrity = document.get("integrity")

    if not isinstance(integrity, dict):
        raise PolicyArtifactError("Policy artifact integrity section must be a mapping")

    algorithm = integrity.get("algorithm")

    if algorithm != "sha256":
        raise PolicyArtifactError(
            "Policy artifact integrity.algorithm must be 'sha256'"
        )

    declared_digest = integrity.get("rules_digest")

    if not isinstance(declared_digest, str) or not declared_digest.startswith("sha256:"):
        raise PolicyArtifactError(
            "Policy artifact integrity.rules_digest must be a 'sha256:<hex>' digest"
        )

    actual_digest = _sha256_digest(spec)

    if actual_digest != declared_digest:
        raise PolicyIntegrityError(
            "Policy artifact integrity verification failed: "
            f"declared {declared_digest}, actual {actual_digest}"
        )

    evaluator = spec.get("evaluator")

    if not isinstance(evaluator, str) or not evaluator:
        raise PolicyArtifactError("Policy artifact spec.evaluator must be a non-empty string")

    layers_spec = spec.get("layers")

    if not isinstance(layers_spec, dict) or not layers_spec:
        raise PolicyArtifactError("Policy artifact spec.layers must be a non-empty mapping")

    ranking: dict[str, int] = {}

    for layer, rank in layers_spec.items():
        if not isinstance(layer, str) or not layer:
            raise PolicyArtifactError("Policy artifact layer names must be non-empty strings")

        if not isinstance(rank, int) or isinstance(rank, bool):
            raise PolicyArtifactError(f"Policy artifact layer '{layer}' must map to an integer rank")

        ranking[layer] = rank

    if len(set(ranking.values())) != len(ranking):
        raise PolicyArtifactError("Policy artifact layer ranks must be unique")

    dependency_direction = spec.get("dependency_direction")

    if dependency_direction != "same-or-deeper":
        raise PolicyArtifactError(
            "Policy artifact spec.dependency_direction must be 'same-or-deeper'"
        )

    rules_spec = spec.get("rules")

    if not isinstance(rules_spec, list) or not rules_spec:
        raise PolicyArtifactError("Policy artifact spec.rules must be a non-empty list")

    rules: dict[str, RuleSpec] = {}

    for index, entry in enumerate(rules_spec):
        if not isinstance(entry, dict):
            raise PolicyArtifactError(f"Policy artifact rules[{index}] must be a mapping")

        rule_id = entry.get("id")

        if not isinstance(rule_id, str) or not rule_id:
            raise PolicyArtifactError(f"Policy artifact rules[{index}].id must be a non-empty string")

        if rule_id in rules:
            raise PolicyArtifactError(f"Policy artifact contains duplicate rule id '{rule_id}'")

        for field in ("severity", "title", "description", "remediation", "documentation_url", "category"):
            value = entry.get(field)

            if not isinstance(value, str) or not value:
                raise PolicyArtifactError(
                    f"Policy artifact rule '{rule_id}' field '{field}' must be a non-empty string"
                )

        if entry["severity"] not in ("BLOCK", "WARN"):
            raise PolicyArtifactError(
                f"Policy artifact rule '{rule_id}' severity must be 'BLOCK' or 'WARN'"
            )

        rules[rule_id] = RuleSpec(
            rule_id=rule_id,
            severity=entry["severity"],
            title=entry["title"],
            description=entry["description"],
            remediation=entry["remediation"],
            documentation_url=entry["documentation_url"],
            category=entry["category"],
        )

    return PolicyBundle(
        name=name,
        version=version,
        digest=actual_digest,
        evaluator=evaluator,
        layers=LayerModel(
            ranking=ranking,
            dependency_direction=dependency_direction,
        ),
        rules=rules,
    )


def load_policy_artifact(path: str | None = None) -> PolicyBundle:
    """Load and verify the pinned policy artifact.

    With no argument the artifact pinned in the package is used. The
    digest declared inside the artifact is verified against the canonical
    form of its spec section; a mismatch aborts validation.
    """

    try:
        if path is None:
            resource = resources.files(POLICY_PACKAGE).joinpath(
                POLICY_ARTIFACT_DIR, PINNED_POLICY_ARTIFACT
            )
            document = yaml.safe_load(resource.read_text(encoding="utf-8"))
        else:
            documents = load_yaml_file(path)
            if len(documents) != 1:
                raise PolicyArtifactError(
                    "Policy artifact file must contain exactly one YAML document"
                )
            document = documents[0]
    except YamlLoadError as exc:
        raise PolicyArtifactError(str(exc)) from exc

    return parse_policy_document(document)


_BUNDLE: PolicyBundle | None = None


def get_policy_bundle() -> PolicyBundle:
    """Return the verified pinned policy bundle (cached, deterministic)."""

    global _BUNDLE

    if _BUNDLE is None:
        _BUNDLE = load_policy_artifact()

    return _BUNDLE


def get_rule_spec(rule_id: str) -> RuleSpec:
    """Return catalog metadata for one rule, raising on unknown IDs."""

    bundle = get_policy_bundle()
    rule = bundle.rules.get(rule_id)

    if rule is None:
        raise KeyError(rule_id)

    return rule
