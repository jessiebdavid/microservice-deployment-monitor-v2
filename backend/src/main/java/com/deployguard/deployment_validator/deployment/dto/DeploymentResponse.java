package com.deployguard.deployment_validator.deployment.dto;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.model.DeploymentStatus;

import java.time.LocalDateTime;

public class DeploymentResponse {

    private Long id;
    private String serviceName;
    private String version;
    private String environment;
    private String targetUrl;
    private DeploymentStatus status;
    private LocalDateTime startedAt;
    private LocalDateTime completedAt;
    private Long durationMs;

    public DeploymentResponse(Deployment deployment) {
        this.id = deployment.getId();
        this.serviceName = deployment.getServiceName();
        this.version = deployment.getVersion();
        this.environment = deployment.getEnvironment();
        this.targetUrl = deployment.getTargetUrl();
        this.status = deployment.getStatus();
        this.startedAt = deployment.getStartedAt();
        this.completedAt = deployment.getCompletedAt();
        this.durationMs = deployment.getDurationMs();
    }

    public Long getId() {
        return id;
    }

    public String getServiceName() {
        return serviceName;
    }

    public String getVersion() {
        return version;
    }

    public String getEnvironment() {
        return environment;
    }

    public String getTargetUrl() {
        return targetUrl;
    }

    public DeploymentStatus getStatus() {
        return status;
    }

    public LocalDateTime getStartedAt() {
        return startedAt;
    }

    public LocalDateTime getCompletedAt() {
        return completedAt;
    }

    public Long getDurationMs() {
        return durationMs;
    }
}