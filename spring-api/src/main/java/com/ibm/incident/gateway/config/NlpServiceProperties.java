package com.ibm.incident.gateway.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "nlp.service")
public class NlpServiceProperties {
    private String baseUrl;

    // Returns the configured base URL for the downstream ML service.
    public String getBaseUrl() {
        return baseUrl;
    }

    // Updates the downstream ML service URL from application configuration.
    public void setBaseUrl(String baseUrl) {
        this.baseUrl = baseUrl;
    }
}
