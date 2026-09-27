package com.deployguard.deployment_validator.orchestration.service;

import com.deployguard.deployment_validator.aggregation.service.ResultAggregatorService;
import com.deployguard.deployment_validator.configuration.service.ConfigurationValidationService;
import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.governance.service.GovernanceValidationService;
import com.deployguard.deployment_validator.health.service.HealthCheckService;
import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import com.deployguard.deployment_validator.validation.service.ValidationResultService;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class DeploymentOrchestrationService {

    private final GovernanceValidationService governanceValidationService;
    private final ConfigurationValidationService configurationValidationService;
    private final HealthCheckService healthCheckService;
    private final ValidationResultService validationResultService;
    private final ResultAggregatorService resultAggregatorService;

    public DeploymentOrchestrationService(
            GovernanceValidationService governanceValidationService,
            ConfigurationValidationService configurationValidationService,
            HealthCheckService healthCheckService,
            ValidationResultService validationResultService,
            ResultAggregatorService resultAggregatorService) {

        this.governanceValidationService = governanceValidationService;
        this.configurationValidationService = configurationValidationService;
        this.healthCheckService = healthCheckService;
        this.validationResultService = validationResultService;
        this.resultAggregatorService = resultAggregatorService;
    }

    public ValidationStatus validateDeployment(Deployment deployment) {

        List<ValidationResult> results = new ArrayList<>();

        ValidationResult governanceResult =
                governanceValidationService.validate(deployment);

        validationResultService.createResult(
                deployment.getId(),
                governanceResult.getType(),
                governanceResult.getStatus(),
                governanceResult.getMessage(),
                governanceResult.getDetails()
        );

        results.add(governanceResult);

        ValidationResult configurationResult =
                configurationValidationService.validate(deployment);

        validationResultService.createResult(
                deployment.getId(),
                configurationResult.getType(),
                configurationResult.getStatus(),
                configurationResult.getMessage(),
                configurationResult.getDetails()
        );

        results.add(configurationResult);

        ValidationResult healthResult =
                healthCheckService.checkHealth(deployment);

        validationResultService.createResult(
                deployment.getId(),
                healthResult.getType(),
                healthResult.getStatus(),
                healthResult.getMessage(),
                healthResult.getDetails()
        );

        results.add(healthResult);

        return resultAggregatorService.aggregate(results);
    }
}