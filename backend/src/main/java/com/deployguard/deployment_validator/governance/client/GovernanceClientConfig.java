package com.deployguard.deployment_validator.governance.client;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class GovernanceClientConfig {

    @Bean
    public RestClient governanceRestClient(
            @Value("${governance.service.url}") String governanceServiceUrl) {

        return RestClient.builder()
                .baseUrl(governanceServiceUrl)
                .build();
    }

    @Bean
    public GovernanceClient governanceClient(RestClient governanceRestClient) {
        return new GovernanceClient(governanceRestClient);
    }
}