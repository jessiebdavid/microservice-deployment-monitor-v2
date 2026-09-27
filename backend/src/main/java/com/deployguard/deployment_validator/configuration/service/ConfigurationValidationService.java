package com.deployguard.deployment_validator.configuration.service;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import com.deployguard.deployment_validator.validation.model.ValidationType;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class ConfigurationValidationService {

    public ValidationResult validate(Deployment deployment) {

        ValidationResult result = new ValidationResult();

        result.setDeploymentId(deployment.getId());
        result.setType(ValidationType.CONFIGURATION);
        result.setCreatedAt(LocalDateTime.now());

        StringBuilder details = new StringBuilder();

        boolean valid = true;

        if (isBlank(deployment.getServiceName())) {
            valid = false;
            details.append("serviceName is missing; ");
        }

        if (isBlank(deployment.getVersion())) {
            valid = false;
            details.append("version is missing; ");
        }

        if (isBlank(deployment.getEnvironment())) {
            valid = false;
            details.append("environment is missing; ");
        }

        if (isBlank(deployment.getTargetUrl())) {
            valid = false;
            details.append("targetUrl is missing; ");
        }

        if (valid) {
            result.setStatus(ValidationStatus.PASS);
            result.setMessage("Configuration validation passed");
            result.setDetails(
                    "Required deployment configuration fields are present"
            );
        } else {
            result.setStatus(ValidationStatus.FAIL);
            result.setMessage("Configuration validation failed");
            result.setDetails(details.toString());
        }

        return result;
    }

    private boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}