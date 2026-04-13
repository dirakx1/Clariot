#!/bin/bash
# Clariot Sensor/Actuator Container Entry Point

set -e

echo "==================================="
echo "Clariot Sensor & Actuator Container"
echo "==================================="
echo "MQTT Broker: $MQTT_BROKER"
echo "Sensor Interval: $SENSOR_INTERVAL ms"
echo "Agent ID: $AGENT_ID"
echo ""

# Start MQTT broker in background (for standalone mode)
if [ "$STANDALONE_MODE" = "true" ]; then
    echo "Starting embedded MQTT broker..."
    mosquitto -c /etc/mosquitto/mosquitto.conf &
    sleep 2
fi

# Run the data ingest and command router services
python /app/data_ingest.py &
python /app/command_router.py &

# If mock mode, run mock sensor simulator
if [ "$MOCK_MODE" = "true" ]; then
    echo "Starting mock sensor simulator..."
    python /app/mock_sensors.py &
fi

# Keep container running
echo "Container started. Press Ctrl+C to stop."
wait
