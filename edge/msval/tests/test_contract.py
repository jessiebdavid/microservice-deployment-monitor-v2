from msval_edge.normalization.contract import validate_service_arch


def valid_architecture():
    return {
        "version": "0.1",
        "service": {
            "name": "payments-api",
            "owner": "payments-team",
            "layer": "domain",
            "tier": "critical",
        },
        "exposure": {
            "public": False,
        },
        "dependencies": [
            {
                "name": "orders-api",
                "layer": "domain",
                "required": True,
            }
        ],
        "availability": {
            "replicas": 2,
            "requires_health_checks": True,
        },
    }


def test_valid_service_architecture_passes():
    document = valid_architecture()

    errors = validate_service_arch(document)

    assert errors == []


def test_invalid_version_fails():
    document = valid_architecture()
    document["version"] = "0.2"

    errors = validate_service_arch(document)

    assert "version must be '0.1'" in errors


def test_missing_owner_fails():
    document = valid_architecture()
    del document["service"]["owner"]

    errors = validate_service_arch(document)

    assert "service.owner is required" in errors


def test_invalid_replicas_fails():
    document = valid_architecture()
    document["availability"]["replicas"] = 0

    errors = validate_service_arch(document)

    assert (
        "availability.replicas must be an integer >= 1"
        in errors
    )