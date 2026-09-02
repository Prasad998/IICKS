package com.ibm.incident.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class IncidentGatewayApplication {
    // Boots the Spring API gateway that fronts the Python ML service.
    public static void main(String[] args) {
        SpringApplication.run(IncidentGatewayApplication.class, args);
    }
}
