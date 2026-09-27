package com.deployguard.deployment_validator.validation.repository;

import com.deployguard.deployment_validator.validation.model.ValidationResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ValidationResultRepository
        extends JpaRepository<ValidationResult, Long> {

    List<ValidationResult> findByDeploymentId(Long deploymentId);
}