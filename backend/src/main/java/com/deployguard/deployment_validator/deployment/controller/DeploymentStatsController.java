package com.deployguard.deployment_validator.deployment.controller;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.deployment.repository.DeploymentRepository;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/deployments")
@CrossOrigin(origins = "http://localhost:5173")
public class DeploymentStatsController {

    private final DeploymentRepository deploymentRepository;

    public DeploymentStatsController(
            DeploymentRepository deploymentRepository
    ) {
        this.deploymentRepository = deploymentRepository;
    }

    @GetMapping("/stats")
    public Map<String, Object> getStatistics() {

        List<Deployment> deployments =
                deploymentRepository.findAll();

        long total = deployments.size();

        long success = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "SUCCESS".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long failed = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "FAILED".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long pending = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        "PENDING".equals(
                                d.getStatus().name()
                        )
                )
                .count();

        long validating = deployments.stream()
                .filter(d ->
                        d.getStatus() != null &&
                        (
                            "VALIDATING".equals(
                                d.getStatus().name()
                            )
                            ||
                            "RUNNING".equals(
                                d.getStatus().name()
                            )
                        )
                )
                .count();

        Map<String, Object> result =
                new HashMap<>();

        result.put("total", total);
        result.put("success", success);
        result.put("failed", failed);
        result.put("pending", pending);
        result.put("validating", validating);

        return result;
    }
}
