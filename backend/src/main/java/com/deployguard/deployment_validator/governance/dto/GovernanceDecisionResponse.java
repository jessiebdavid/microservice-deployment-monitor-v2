package com.deployguard.deployment_validator.governance.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

public record GovernanceDecisionResponse(
        String verdict,
        List<String> blocking,
        List<String> warnings,
        List<String> waived,

        @JsonProperty("evaluated_rules")
        List<String> evaluatedRules,

        @JsonProperty("evaluated_under")
        String evaluatedUnder,

        @JsonProperty("cdm_version")
        String cdmVersion,

        @JsonProperty("duration_ms")
        Long durationMs
) {}