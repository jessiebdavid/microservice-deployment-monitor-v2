package com.deployguard.deployment_validator.deployment.repository;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DeploymentRepository extends JpaRepository<Deployment, Long> {
}