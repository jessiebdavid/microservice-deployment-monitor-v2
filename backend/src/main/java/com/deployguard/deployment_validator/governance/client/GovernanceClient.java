package com.deployguard.deployment_validator.governance.client;

import com.deployguard.deployment_validator.governance.dto.GovernanceDecisionRequest;
import com.deployguard.deployment_validator.governance.dto.GovernanceDecisionResponse;
import org.springframework.web.client.RestClient;

public class GovernanceClient {

    private final RestClient restClient;

    public GovernanceClient(RestClient restClient) {
        this.restClient = restClient;
    }

    public GovernanceDecisionResponse evaluate(
            GovernanceDecisionRequest request) {

        return restClient.post()
                .uri("/api/v1/decisions")
                .body(request)
                .retrieve()
                .body(GovernanceDecisionResponse.class);
    }
}