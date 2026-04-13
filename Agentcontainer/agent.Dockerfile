FROM python:3.11-slim

LABEL maintainer="clariot team"
LABEL description="Clariot AI Agent Container with LLM reasoning"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mosquitto-clients \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    mqtt \
    paho-mqtt \
    requests \
    anthropic \
    openai \
    fastapi \
    uvicorn \
    websockets \
    pydantic \
    python-dotenv

# Create app directory
WORKDIR /app

# Copy agent code
COPY agent_core/ /app/agent_core/
COPY llm_gateway/ /app/llm_gateway/
COPY control_plane/ /app/control_plane/
COPY mcp_protocol/ /app/mcp_protocol/

# Create directories for data
RUN mkdir -p /app/data/memory /app/logs

# Set environment defaults
ENV LLM_PROVIDER=openai
ENV LLM_MODEL=gpt-4
ENV MQTT_BROKER=mqtt://localhost:1883
ENV SENSOR_TOPIC=sensors/#
ENV ACTUATOR_TOPIC=actuators/#
ENV LOG_LEVEL=INFO

# Expose control plane port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Entry point
ENTRYPOINT ["python", "/app/control_plane/server.py"]
