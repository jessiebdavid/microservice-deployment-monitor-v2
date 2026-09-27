package com.deployguard.deployment_validator.deployment.controller;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.repository.DeploymentRepository;
import org.springframework.data.domain.Sort;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/deployments")
@CrossOrigin(origins = "http://localhost:5173")
public class DeploymentHistoryController {

    private final DeploymentRepository deploymentRepository;

    public DeploymentHistoryController(
            DeploymentRepository deploymentRepository
    ) {
        this.deploymentRepository = deploymentRepository;
    }

    /**
     * Returns deployment history.
     *
     * Newest deployments are returned first.
     */
    @GetMapping
    public List<Deployment> getDeployments() {
        return deploymentRepository.findAll(
                Sort.by(
                        Sort.Direction.DESC,
                        "id"
                )
        );
    }
}
