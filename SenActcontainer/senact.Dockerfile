FROM python:3.11-slim

LABEL maintainer="clariot team"
LABEL description="Clariot Sensor & Actuator Container"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    mosquitto-clients \
    mosquitto \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    paho-mqtt \
    requests \
    RPi.GPIO \
    smbus \
    spidev

# Create app directory
WORKDIR /app

# Copy sensor and actuator handlers
COPY sensor.py /app/sensor.py
COPY actuator.py /app/actuator.py
COPY data_ingest.py /app/data_ingest.py
COPY command_router.py /app/command_router.py
COPY senact_entrypoint.sh /app/senact_entrypoint.sh

RUN chmod +x /app/senact_entrypoint.sh

# Create directories for data
RUN mkdir -p /app/data/sensors /app/data/actuators

# Environment defaults
ENV MQTT_BROKER=mqtt://localhost:1883
ENV SENSOR_INTERVAL=1000
ENV AGENT_ID=clariot_agent_1

# Entry point
ENTRYPOINT ["/app/senact_entrypoint.sh"]
