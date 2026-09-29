RULES = {
    "ARCH-001": {
        "severity": "BLOCK",
        "title": "Service owner must be declared",
        "description": "Every service must declare an owning team.",
        "remediation": "Set service.owner to the responsible team.",
    },
    "ARCH-002": {
        "severity": "BLOCK",
        "title": "Service layer must be declared",
        "description": "Every service must declare its architectural layer.",
        "remediation": "Set service.layer to the appropriate architecture layer.",
    },
    "ARCH-003": {
        "severity": "WARN",
        "title": "Availability requirements must be declared",
        "description": "The service should declare its availability expectations.",
        "remediation": "Define availability.replicas and health-check requirements.",
    },
}