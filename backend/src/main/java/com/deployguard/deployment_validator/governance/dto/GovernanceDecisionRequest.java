package com.deployguard.deployment_validator.governance.dto;

import java.util.Map;

public record GovernanceDecisionRequest(
        Map<String, Object> document,
        String format,
        String environment,
        String phase
) {
}