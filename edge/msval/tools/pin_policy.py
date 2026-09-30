"""Pin the integrity digest of the msval policy artifact.

Usage (from edge/msval):

    python tools/pin_policy.py [path-to-artifact]

Recomputes the SHA-256 digest over the canonical JSON form of the policy
artifact's ``spec`` section and rewrites the ``integrity.rules_digest``
field in place. Run this after every intentional change to the rule
catalog; CI (see .github/workflows/msval.yml) verifies the digest and
fails when an artifact is changed without re-pinning.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

DEFAULT_ARTIFACT = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "msval_edge"
    / "policy"
    / "artifacts"
    / "msval-default-policy-1.0.0.yaml"
)


def canonical_spec_bytes(spec: dict) -> bytes:
    return json.dumps(
        spec,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def pin_digest(path: Path) -> str:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(document, dict):
        raise SystemExit("Policy artifact root must be a YAML mapping")

    spec = document.get("spec")

    if not isinstance(spec, dict):
        raise SystemExit("Policy artifact spec must be a mapping")

    digest = "sha256:" + hashlib.sha256(canonical_spec_bytes(spec)).hexdigest()

    integrity = document.get("integrity")

    if not isinstance(integrity, dict):
        raise SystemExit("Policy artifact integrity section must be a mapping")

    if integrity.get("rules_digest") != digest:
        integrity["rules_digest"] = digest
        text = yaml.safe_dump(
            document,
            sort_keys=False,
            allow_unicode=True,
        )
        path.write_text(text, encoding="utf-8")

    return digest


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_ARTIFACT
    digest = pin_digest(path)
    print(f"Pinned {digest} -> {path}")


if __name__ == "__main__":
    main()
