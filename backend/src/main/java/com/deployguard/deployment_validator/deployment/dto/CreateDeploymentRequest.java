package com.deployguard.deployment_validator.deployment.dto;

import jakarta.validation.constraints.NotBlank;

public class CreateDeploymentRequest {

    @NotBlank
    private String serviceName;

    @NotBlank
    private String version;

    @NotBlank
    private String environment;

    @NotBlank
    private String targetUrl;

    public CreateDeploymentRequest() {
    }

    public String getServiceName() {
        return serviceName;
    }

    public void setServiceName(String serviceName) {
        this.serviceName = serviceName;
    }

    public String getVersion() {
        return version;
    }

    public void setVersion(String version) {
        this.version = version;
    }

    public String getEnvironment() {
        return environment;
    }

    public void setEnvironment(String environment) {
        this.environment = environment;
    }

    public String getTargetUrl() {
        return targetUrl;
    }

    public void setTargetUrl(String targetUrl) {
        this.targetUrl = targetUrl;
    }
}