"""MVP-1 performance benchmark (Phase I).

Generates a deterministic multi-document Kubernetes manifest with
slightly more than 100 objects (Deployments plus Services and a
ConfigMap), then measures end-to-end CLI validation wall time.

The documented MVP-1 target is: under 30 seconds for 100 rendered
Kubernetes objects. This script measures and prints the actual numbers;
nothing is asserted here, record the output in the README.

Usage (from edge/msval):

    python tools/benchmark.py [runs]
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MSVAL_ROOT = Path(__file__).resolve().parents[1]

DEPLOYMENT_TEMPLATE = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: svc-{index}
  labels:
    app: svc-{index}
    owner: team-{owner}
    tier: {tier}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: svc-{index}
  template:
    metadata:
      labels:
        app: svc-{index}
    spec:
      securityContext:
        runAsNonRoot: true
      containers:
        - name: svc-{index}
          image: registry.example.com/svc-{index}:{tag}
          resources:
            requests:
              cpu: "{cpu}m"
              memory: "{memory}Mi"
            limits:
              cpu: "{limit_cpu}m"
              memory: "{limit_memory}Mi"
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5"]
"""

SERVICE_TEMPLATE = """\
apiVersion: v1
kind: Service
metadata:
  name: svc-{index}
spec:
  type: ClusterIP
  selector:
    app: svc-{index}
  ports:
    - port: 80
      targetPort: 8080
"""

CONFIGMAP_TEMPLATE = """\
apiVersion: v1
kind: ConfigMap
metadata:
  name: platform-config
data:
  LOG_LEVEL: "info"
"""


def generate_manifest(object_count: int) -> str:
    """Deterministically render `object_count` Kubernetes objects."""

    documents: list[str] = []
    deployments = 0

    while len(documents) < object_count:
        index = deployments
        documents.append(
            DEPLOYMENT_TEMPLATE.format(
                index=index,
                owner=index % 5,
                tier=("critical", "standard", "standard")[index % 3],
                replicas=1 + index % 3,
                tag=f"1.{index % 9}.{index % 7}",
                cpu=100 + index % 200,
                memory=128 + (index % 4) * 64,
                limit_cpu=200 + index % 400,
                limit_memory=256 + (index % 4) * 128,
            )
        )
        documents.append(SERVICE_TEMPLATE.format(index=index))
        deployments += 1

    documents.append(CONFIGMAP_TEMPLATE)

    return "---\n".join(documents)


def write_architecture(path: Path) -> None:
    path.write_text(
        (
            "version: \"0.1\"\n"
            "service:\n"
            "  name: benchmark\n"
            "  owner: platform-team\n"
            "  layer: domain\n"
            "  tier: standard\n"
            "exposure:\n"
            "  public: false\n"
            "dependencies: []\n"
            "availability:\n"
            "  replicas: 1\n"
            "  requires_health_checks: true\n"
        ),
        encoding="utf-8",
    )


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    object_count = 100

    manifest = generate_manifest(object_count)
    document_count = manifest.count("apiVersion:")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manifest_path = tmp_path / "manifests.yaml"
        manifest_path.write_text(manifest, encoding="utf-8")

        architecture_path = tmp_path / "service.arch.yaml"
        write_architecture(architecture_path)

        timings: list[float] = []
        verdicts: set[str] = set()

        for _ in range(runs):
            start = time.perf_counter()

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "msval_edge.cli.main",
                    "validate",
                    "--architecture",
                    str(architecture_path),
                    "--kubernetes",
                    str(manifest_path),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                cwd=MSVAL_ROOT,
            )

            elapsed = time.perf_counter() - start
            timings.append(elapsed)

            if result.returncode not in (0, 1):
                print(result.stdout)
                print(result.stderr)
                raise SystemExit(f"Benchmark run failed: exit {result.returncode}")

            payload = json.loads(result.stdout)
            verdicts.add(payload["validation"]["verdict"])

        print(f"objects validated : {document_count}")
        print(f"runs              : {runs}")
        print(f"verdict           : {sorted(verdicts)}")
        print(
            "times (s)         : "
            + ", ".join(f"{t:.2f}" for t in timings)
        )
        print(f"best (s)          : {min(timings):.2f}")
        print(f"mean (s)          : {sum(timings) / len(timings):.2f}")
        print(f"target            : < 30.00 s for 100 objects")

        ok = min(timings) < 30.0
        print(f"target met        : {ok}")


if __name__ == "__main__":
    main()
