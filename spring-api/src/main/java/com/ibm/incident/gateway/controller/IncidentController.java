package com.ibm.incident.gateway.controller;

import com.ibm.incident.gateway.client.NlpServiceClient;
import com.ibm.incident.gateway.dto.AnalyzeRequest;
import com.ibm.incident.gateway.dto.AnalyzeResponse;
import com.ibm.incident.gateway.dto.EvaluateRequest;
import com.ibm.incident.gateway.dto.HealthResponse;
import java.util.List;
import java.util.Map;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Mono;

@CrossOrigin(origins = "*")
@RestController
public class IncidentController {
    private final NlpServiceClient nlpServiceClient;

    // Wires the gateway controller to the downstream NLP client.
    public IncidentController(NlpServiceClient nlpServiceClient) {
        this.nlpServiceClient = nlpServiceClient;
    }

    // Proxies the Python health response through the Spring gateway.
    @GetMapping("/health")
    public Mono<HealthResponse> health() {
        return nlpServiceClient.health();
    }

    // Proxies classification and retrieval requests to the Python service.
    @PostMapping("/api/analyze")
    public Mono<AnalyzeResponse> analyze(@RequestBody AnalyzeRequest request) {
        return nlpServiceClient.analyze(request);
    }

    // Returns dashboard sample tickets through the gateway layer.
    @GetMapping("/api/examples")
    public Mono<List<Map<String, String>>> examples() {
        return nlpServiceClient.examples();
    }

    // Proxies classifier holdout evaluation requests to the Python service.
    @PostMapping("/api/evaluate")
    public Mono<Map<String, Object>> evaluate(@RequestBody EvaluateRequest request) {
        return nlpServiceClient.evaluate(request);
    }
}