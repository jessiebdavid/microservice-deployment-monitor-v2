from pathlib import Path
from typing import Any

import yaml


class YamlLoadError(Exception):
    """Raised when a YAML document cannot be loaded."""


def load_yaml_file(path: str | Path) -> list[Any]:
    file_path = Path(path)

    if not file_path.exists():
        raise YamlLoadError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise YamlLoadError(f"Not a file: {file_path}")

    try:
        with file_path.open("r", encoding="utf-8") as file:
            documents = list(yaml.safe_load_all(file))

    except yaml.YAMLError as exc:
        raise YamlLoadError(
            f"Invalid YAML in {file_path}: {exc}"
        ) from exc

    return [
        document
        for document in documents
        if document is not None
    ]