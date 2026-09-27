package com.deployguard.deployment_validator.governance.service;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.governance.client.GovernanceClient;
import com.deployguard.deployment_validator.governance.dto.GovernanceDecisionRequest;
import com.deployguard.deployment_validator.governance.dto.GovernanceDecisionResponse;
import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import com.deployguard.deployment_validator.validation.model.ValidationType;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class GovernanceValidationService {

    private final GovernanceClient governanceClient;

    public GovernanceValidationService(GovernanceClient governanceClient) {
        this.governanceClient = governanceClient;
    }

    public ValidationResult validate(Deployment deployment) {

        Map<String, Object> document = buildCdmDocument(deployment);

        GovernanceDecisionRequest request = new GovernanceDecisionRequest(
                document,
                "cdm",
                deployment.getEnvironment(),
                "runtime"
        );

        GovernanceDecisionResponse response = governanceClient.evaluate(request);

        ValidationResult result = new ValidationResult();

        result.setDeploymentId(deployment.getId());
        result.setType(ValidationType.GOVERNANCE);
        result.setStatus(mapStatus(response.verdict()));
        result.setMessage(buildMessage(response));
        result.setDetails(buildDetails(response));
        result.setCreatedAt(LocalDateTime.now());

        return result;
    }

    private Map<String, Object> buildCdmDocument(Deployment deployment) {

        Map<String, Object> document = new LinkedHashMap<>();

        document.put("cdm_version", "1.0");

        Map<String, Object> service = new LinkedHashMap<>();
        service.put("id", deployment.getServiceName());
        document.put("service", service);

        Map<String, Object> version = new LinkedHashMap<>();
        version.put("tag", deployment.getVersion());
        document.put("version", version);

        document.put("environment", deployment.getEnvironment());

        Map<String, Object> container = new LinkedHashMap<>();
        container.put("name", deployment.getServiceName());

        Map<String, Object> image = new LinkedHashMap<>();
        image.put("repository", deployment.getServiceName());
        image.put("registry", "local");
        image.put("ref", deployment.getVersion());
        image.put("pinned", false);

        container.put("image", image);

        Map<String, Object> workload = new LinkedHashMap<>();
        workload.put("replicas", 1);
        workload.put("containers", List.of(container));

        document.put("workload", workload);

        return document;
    }

    private ValidationStatus mapStatus(String verdict) {

        if (verdict == null) {
            return ValidationStatus.FAIL;
        }

        return switch (verdict.toUpperCase()) {
            case "PASS" -> ValidationStatus.PASS;
            case "WARN" -> ValidationStatus.WARN;
            case "FAIL" -> ValidationStatus.FAIL;
            default -> ValidationStatus.FAIL;
        };
    }

    private String buildMessage(GovernanceDecisionResponse response) {

        if ("FAIL".equalsIgnoreCase(response.verdict())) {
            return "Governance validation failed";
        }

        if ("WARN".equalsIgnoreCase(response.verdict())) {
            return "Governance validation completed with warnings";
        }

        return "Governance validation passed";
    }

    private String buildDetails(GovernanceDecisionResponse response) {

        return "verdict=" + response.verdict()
                + ", blocking=" + response.blocking()
                + ", warnings=" + response.warnings()
                + ", waived=" + response.waived()
                + ", evaluatedRules=" + response.evaluatedRules()
                + ", evaluatedUnder=" + response.evaluatedUnder()
                + ", cdmVersion=" + response.cdmVersion()
                + ", durationMs=" + response.durationMs();
    }
}