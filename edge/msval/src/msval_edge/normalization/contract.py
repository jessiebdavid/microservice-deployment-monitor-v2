from typing import Any


REQUIRED_SERVICE_FIELDS = {
    "name",
    "owner",
    "layer",
    "tier",
}


class ContractValidationError(Exception):
    """Raised when service.arch.yaml violates the contract."""


def validate_service_arch(document: Any) -> list[str]:
    errors: list[str] = []

    if not isinstance(document, dict):
        return ["Root document must be a YAML mapping"]

    if document.get("version") != "0.1":
        errors.append("version must be '0.1'")

    service = document.get("service")

    if not isinstance(service, dict):
        errors.append("service must be a mapping")
    else:
        missing = REQUIRED_SERVICE_FIELDS - service.keys()

        for field in sorted(missing):
            errors.append(f"service.{field} is required")

    exposure = document.get("exposure")

    if not isinstance(exposure, dict):
        errors.append("exposure must be a mapping")
    elif not isinstance(exposure.get("public"), bool):
        errors.append("exposure.public must be a boolean")

    dependencies = document.get("dependencies")

    if not isinstance(dependencies, list):
        errors.append("dependencies must be a list")
    else:
        for index, dependency in enumerate(dependencies):
            if not isinstance(dependency, dict):
                errors.append(
                    f"dependencies[{index}] must be a mapping"
                )
                continue

            for field in ("name", "layer", "required"):
                if field not in dependency:
                    errors.append(
                        f"dependencies[{index}].{field} is required"
                    )

    availability = document.get("availability")

    if not isinstance(availability, dict):
        errors.append("availability must be a mapping")
    else:
        replicas = availability.get("replicas")

        if not isinstance(replicas, int) or replicas < 1:
            errors.append(
                "availability.replicas must be an integer >= 1"
            )

        if not isinstance(
            availability.get("requires_health_checks"),
            bool,
        ):
            errors.append(
                "availability.requires_health_checks "
                "must be a boolean"
            )

    return errors