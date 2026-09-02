package com.ibm.incident.gateway.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class HealthResponse {
    private String status;

    @JsonProperty("incidents_loaded")
    private Integer incidentsLoaded;

    @JsonProperty("articles_loaded")
    private Integer articlesLoaded;

    @JsonProperty("model_backend")
    private String modelBackend;

    @JsonProperty("redis_cache")
    private String redisCache;

    @JsonProperty("kafka_events")
    private String kafkaEvents;

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Integer getIncidentsLoaded() {
        return incidentsLoaded;
    }

    public void setIncidentsLoaded(Integer incidentsLoaded) {
        this.incidentsLoaded = incidentsLoaded;
    }

    public Integer getArticlesLoaded() {
        return articlesLoaded;
    }

    public void setArticlesLoaded(Integer articlesLoaded) {
        this.articlesLoaded = articlesLoaded;
    }

    public String getModelBackend() {
        return modelBackend;
    }

    public void setModelBackend(String modelBackend) {
        this.modelBackend = modelBackend;
    }

    public String getRedisCache() {
        return redisCache;
    }

    public void setRedisCache(String redisCache) {
        this.redisCache = redisCache;
    }

    public String getKafkaEvents() {
        return kafkaEvents;
    }

    public void setKafkaEvents(String kafkaEvents) {
        this.kafkaEvents = kafkaEvents;
    }
}
