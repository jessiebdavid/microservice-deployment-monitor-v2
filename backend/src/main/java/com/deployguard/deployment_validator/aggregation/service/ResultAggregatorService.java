package com.deployguard.deployment_validator.aggregation.service;

import com.deployguard.deployment_validator.validation.model.ValidationResult;
import com.deployguard.deployment_validator.validation.model.ValidationStatus;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ResultAggregatorService {

    public ValidationStatus aggregate(List<ValidationResult> results) {

        if (results == null || results.isEmpty()) {
            return ValidationStatus.SKIPPED;
        }

        boolean hasWarn = false;

        for (ValidationResult result : results) {

            if (result.getStatus() == ValidationStatus.FAIL) {
                return ValidationStatus.FAIL;
            }

            if (result.getStatus() == ValidationStatus.WARN) {
                hasWarn = true;
            }
        }

        if (hasWarn) {
            return ValidationStatus.WARN;
        }

        boolean allPass = results.stream()
                .allMatch(result ->
                        result.getStatus() == ValidationStatus.PASS);

        if (allPass) {
            return ValidationStatus.PASS;
        }

        return ValidationStatus.SKIPPED;
    }
}