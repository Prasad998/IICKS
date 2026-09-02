package com.ibm.incident.gateway.client;

import com.ibm.incident.gateway.dto.AnalyzeRequest;
import com.ibm.incident.gateway.dto.AnalyzeResponse;
import com.ibm.incident.gateway.dto.EvaluateRequest;
import com.ibm.incident.gateway.dto.HealthResponse;
import java.util.List;
import java.util.Map;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@Component
public class NlpServiceClient {
    private final WebClient nlpWebClient;

    // Creates a client wrapper around the Python inference API.
    public NlpServiceClient(WebClient nlpWebClient) {
        this.nlpWebClient = nlpWebClient;
    }

    // Forwards incident text to the Python service for classification and retrieval.
    // Returns a Mono instead of blocking, so the Netty event-loop thread is never held up.
    public Mono<AnalyzeResponse> analyze(AnalyzeRequest request) {
        return nlpWebClient.post()
                .uri("/api/analyze")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(AnalyzeResponse.class);
    }

    // Reads health and readiness details from the Python service.
    public Mono<HealthResponse> health() {
        return nlpWebClient.get()
                .uri("/health")
                .retrieve()
                .bodyToMono(HealthResponse.class);
    }

    // Fetches sample tickets for the dashboard sample picker.
    // ParameterizedTypeReference preserves the full generic type (no raw List, no unchecked cast).
    public Mono<List<Map<String, String>>> examples() {
        return nlpWebClient.get()
                .uri("/api/examples")
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<List<Map<String, String>>>() {});
    }

    // Forwards a holdout evaluation request to the Python service and returns the raw report.
    public Mono<Map<String, Object>> evaluate(EvaluateRequest request) {
        return nlpWebClient.post()
                .uri("/api/evaluate")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {});
    }
}