package com.deployguard.deployment_validator.deployment.service;

import com.deployguard.deployment_validator.deployment.dto.CreateDeploymentRequest;
import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.model.DeploymentStatus;
import com.deployguard.deployment_validator.deployment.repository.DeploymentRepository;
import com.deployguard.deployment_validator.orchestration.service.DeploymentOrchestrationService;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;

@Service
public class DeploymentService {

    private final DeploymentRepository deploymentRepository;
    private final DeploymentOrchestrationService orchestrationService;

    public DeploymentService(
            DeploymentRepository deploymentRepository,
            DeploymentOrchestrationService orchestrationService) {

        this.deploymentRepository = deploymentRepository;
        this.orchestrationService = orchestrationService;
    }

    public Deployment createDeployment(CreateDeploymentRequest request) {

        Deployment deployment = new Deployment();

        deployment.setServiceName(request.getServiceName());
        deployment.setVersion(request.getVersion());
        deployment.setEnvironment(request.getEnvironment());
        deployment.setTargetUrl(request.getTargetUrl());

        deployment.setStatus(DeploymentStatus.VALIDATING);
        deployment.setStartedAt(LocalDateTime.now());

        deployment = deploymentRepository.save(deployment);

        ValidationStatus overallStatus =
                orchestrationService.validateDeployment(deployment);

        if (overallStatus == ValidationStatus.FAIL) {
            deployment.setStatus(DeploymentStatus.FAILED);
        } else if (overallStatus == ValidationStatus.PASS
                || overallStatus == ValidationStatus.WARN) {
            deployment.setStatus(DeploymentStatus.SUCCESS);
        } else {
            deployment.setStatus(DeploymentStatus.FAILED);
        }

        deployment.setCompletedAt(LocalDateTime.now());

        long duration = Duration.between(
                deployment.getStartedAt(),
                deployment.getCompletedAt()
        ).toMillis();

        deployment.setDurationMs(duration);

        return deploymentRepository.save(deployment);
    }

    public Deployment getDeployment(Long id) {
        return deploymentRepository.findById(id)
                .orElseThrow(() ->
                        new RuntimeException("Deployment not found: " + id));
    }
}