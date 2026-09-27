package com.deployguard.deployment_validator.deployment.controller;

import com.deployguard.deployment_validator.deployment.dto.CreateDeploymentRequest;
import com.deployguard.deployment_validator.deployment.dto.DeploymentResponse;
import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.service.DeploymentService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.service.ValidationResultService;

import java.util.List;

@RestController
@RequestMapping("/api/deployments")
public class DeploymentController {

    private final DeploymentService deploymentService;
    private final ValidationResultService validationResultService;

    public DeploymentController(
        DeploymentService deploymentService,
        ValidationResultService validationResultService) {
        this.deploymentService = deploymentService;
        this.validationResultService = validationResultService;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public DeploymentResponse createDeployment(
            @Valid @RequestBody CreateDeploymentRequest request) {

        Deployment deployment = deploymentService.createDeployment(request);

        return new DeploymentResponse(deployment);
    }

    @GetMapping("/{id}")
    public DeploymentResponse getDeployment(@PathVariable Long id) {

        Deployment deployment = deploymentService.getDeployment(id);

        return new DeploymentResponse(deployment);
    }

    @GetMapping("/{id}/validations") 
    public List<ValidationResult> getValidationResults(
            @PathVariable Long id) {
            
        return validationResultService.getResultsForDeployment(id);
}
}