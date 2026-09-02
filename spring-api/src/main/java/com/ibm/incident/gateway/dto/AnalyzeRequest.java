package com.ibm.incident.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AnalyzeRequest {
    private String description;

    @JsonProperty("top_k")
    private Integer topK = 5;

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public Integer getTopK() {
        return topK;
    }

    public void setTopK(Integer topK) {
        this.topK = topK;
    }
}
