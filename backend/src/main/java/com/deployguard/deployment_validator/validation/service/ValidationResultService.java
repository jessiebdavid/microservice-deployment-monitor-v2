package com.deployguard.deployment_validator.validation.service;

import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import com.deployguard.deployment_validator.validation.model.ValidationType;
import com.deployguard.deployment_validator.validation.repository.ValidationResultRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class ValidationResultService {

    private final ValidationResultRepository validationResultRepository;

    public ValidationResultService(
            ValidationResultRepository validationResultRepository) {
        this.validationResultRepository = validationResultRepository;
    }

    public ValidationResult createResult(
            Long deploymentId,
            ValidationType type,
            ValidationStatus status,
            String message,
            String details) {

        ValidationResult result = new ValidationResult();

        result.setDeploymentId(deploymentId);
        result.setType(type);
        result.setStatus(status);
        result.setMessage(message);
        result.setDetails(details);
        result.setCreatedAt(LocalDateTime.now());

        return validationResultRepository.save(result);
    }

    public List<ValidationResult> getResultsForDeployment(Long deploymentId) {
        return validationResultRepository.findByDeploymentId(deploymentId);
    }
}