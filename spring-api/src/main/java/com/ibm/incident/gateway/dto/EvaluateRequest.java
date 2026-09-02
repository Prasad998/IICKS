package com.ibm.incident.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class EvaluateRequest {
    @JsonProperty("test_ratio")
    private Double testRatio = 0.2;

    public Double getTestRatio() {
        return testRatio;
    }

    public void setTestRatio(Double testRatio) {
        this.testRatio = testRatio;
    }
}
