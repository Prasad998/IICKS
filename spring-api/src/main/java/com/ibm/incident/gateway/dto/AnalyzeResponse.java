package com.ibm.incident.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public class AnalyzeResponse {
    private String category;
    private Double confidence;

    @JsonProperty("similar_tickets")
    private List<SimilarTicket> similarTickets;

    @JsonProperty("knowledge_articles")
    private List<KnowledgeArticle> knowledgeArticles;

    private Boolean cached;

    @JsonProperty("model_backend")
    private String modelBackend;

    public String getCategory() {
        return category;
    }

    public void setCategory(String category) {
        this.category = category;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public List<SimilarTicket> getSimilarTickets() {
        return similarTickets;
    }

    public void setSimilarTickets(List<SimilarTicket> similarTickets) {
        this.similarTickets = similarTickets;
    }

    public List<KnowledgeArticle> getKnowledgeArticles() {
        return knowledgeArticles;
    }

    public void setKnowledgeArticles(List<KnowledgeArticle> knowledgeArticles) {
        this.knowledgeArticles = knowledgeArticles;
    }

    public Boolean getCached() {
        return cached;
    }

    public void setCached(Boolean cached) {
        this.cached = cached;
    }

    public String getModelBackend() {
        return modelBackend;
    }

    public void setModelBackend(String modelBackend) {
        this.modelBackend = modelBackend;
    }
}
