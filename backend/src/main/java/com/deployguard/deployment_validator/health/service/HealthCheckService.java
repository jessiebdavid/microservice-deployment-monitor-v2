package com.deployguard.deployment_validator.health.service;

import com.deployguard.deployment_validator.deployment.model.Deployment;
import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import com.deployguard.deployment_validator.validation.model.ValidationType;
import org.springframework.stereotype.Service;

import java.net.HttpURLConnection;
import java.net.URI;
import java.time.LocalDateTime;

@Service
public class HealthCheckService {

    public ValidationResult checkHealth(Deployment deployment) {

        ValidationResult result = new ValidationResult();

        result.setDeploymentId(deployment.getId());
        result.setType(ValidationType.HEALTH);
        result.setCreatedAt(LocalDateTime.now());

        if (isBlank(deployment.getTargetUrl())) {
            result.setStatus(ValidationStatus.FAIL);
            result.setMessage("Health check failed");
            result.setDetails("Target URL is missing");
            return result;
        }

        try {
            String healthUrl = buildHealthUrl(deployment.getTargetUrl());

            URI uri = URI.create(healthUrl);

            HttpURLConnection connection =
                    (HttpURLConnection) uri.toURL().openConnection();

            connection.setRequestMethod("GET");
            connection.setConnectTimeout(3000);
            connection.setReadTimeout(3000);

            int statusCode = connection.getResponseCode();

            connection.disconnect();

            if (statusCode >= 200 && statusCode < 400) {
                result.setStatus(ValidationStatus.PASS);
                result.setMessage("Health check passed");
                result.setDetails(
                        "Health endpoint responded with HTTP " + statusCode
                );
            } else {
                result.setStatus(ValidationStatus.FAIL);
                result.setMessage("Health check failed");
                result.setDetails(
                        "Health endpoint responded with HTTP " + statusCode
                );
            }

        } catch (Exception e) {
            result.setStatus(ValidationStatus.FAIL);
            result.setMessage("Health check failed");
            result.setDetails(
                    "Unable to reach health endpoint: " + e.getMessage()
            );
        }

        return result;
    }

    private String buildHealthUrl(String targetUrl) {
        String url = targetUrl.trim();

        if (url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }

        if (url.endsWith("/actuator/health")) {
            return url;
        }

        return url + "/actuator/health";
    }

    private boolean isBlank(String value) {
        return value == null || value.trim().isEmpty();
    }
}