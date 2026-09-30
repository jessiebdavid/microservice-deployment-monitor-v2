from pathlib import Path

import pytest

from msval_edge.normalization.yaml_loader import (
    YamlLoadError,
    load_yaml_file,
)


EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"


def test_single_document_still_loads_as_list():
    documents = load_yaml_file(
        EXAMPLES_DIR / "kubernetes" / "deployment.yaml"
    )

    assert isinstance(documents, list)
    assert len(documents) == 1
    assert documents[0]["kind"] == "Deployment"


def test_multi_document_loads_all_documents(tmp_path):
    multi = tmp_path / "multi.yaml"
    multi.write_text(
        "---\n"
        "apiVersion: apps/v1\n"
        "kind: Deployment\n"
        "metadata:\n"
        "  name: a\n"
        "---\n"
        "apiVersion: v1\n"
        "kind: Service\n"
        "metadata:\n"
        "  name: b\n",
        encoding="utf-8",
    )

    documents = load_yaml_file(multi)

    assert [document["kind"] for document in documents] == [
        "Deployment",
        "Service",
    ]


def test_empty_documents_are_ignored(tmp_path):
    multi = tmp_path / "empties.yaml"
    multi.write_text(
        "---\n"
        "---\n"
        "apiVersion: v1\n"
        "kind: Service\n"
        "metadata:\n"
        "  name: only\n"
        "---\n"
        "# just a comment\n",
        encoding="utf-8",
    )

    documents = load_yaml_file(multi)

    assert len(documents) == 1
    assert documents[0]["metadata"]["name"] == "only"


def test_missing_file_raises_clean_error():
    with pytest.raises(YamlLoadError) as excinfo:
        load_yaml_file("does-not-exist.yaml")

    assert "File not found" in str(excinfo.value)


def test_invalid_yaml_raises_clean_error(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        "kind: Deployment\n  bad: [unclosed\n",
        encoding="utf-8",
    )

    with pytest.raises(YamlLoadError) as excinfo:
        load_yaml_file(bad)

    assert "Invalid YAML" in str(excinfo.value)
