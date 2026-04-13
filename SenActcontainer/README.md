# Sensor & Actuator Container

This container handles the data acquisition (sensors) and action execution (actuators) layer.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SenAct Container                          │
│                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│   │   Sensors    │───▶│  Data Ingest │───▶│   Agent      │  │
│   │  (Input)     │    │   Service    │    │   Bus        │  │
│   └──────────────┘    └──────────────┘    └──────┬───────┘  │
│                                                  │           │
│   ┌──────────────┐    ┌──────────────┐          │           │
│   │  Actuators   │◀───│Command Router│◀─────────┘           │
│   │  (Output)    │    │              │                      │
│   └──────────────┘    └──────────────┘                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │    MQTT      │
                    │    Broker    │
                    └──────────────┘
```

## Data Flow

1. **Sensors** collect physical data (temperature, humidity, motion, etc.)
2. **Data Ingest Service** publishes sensor readings to MQTT
3. **Agent** subscribes, processes data, makes decisions
4. **Command Router** routes actuator commands from agent
5. **Actuators** execute physical actions based on commands

## Sensor Types Supported

| Type | Description | Example |
|------|-------------|---------|
| `temperature` | Temperature readings | 25.5°C |
| `humidity` | Humidity levels | 65% |
| `motion` | Motion detection | true/false |
| `pressure` | Pressure sensors | 101.3 kPa |
| `distance` | Distance measurements | 10.5 cm |
| `light` | Light level | 500 lux |
| `gas` | Gas concentration | 100 ppm |

## Actuator Types Supported

| Type | Description | Commands |
|------|-------------|----------|
| `motor` | Electric motors | start, stop, speed |
| `valve` | Control valves | open, close |
| `relay` | On/off relay | on, off |
| `servo` | Servo motors | set_position |
| `display` | Display screens | show_text, clear |
| `buzzer` | Audio alerts | beep, silent |

## Configuration

### MQTT Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sensors/<type>/<location>` | Publish | Sensor readings |
| `actuators/<type>/<location>` | Subscribe | Actuator commands |
| `agent/commands` | Publish | Commands from agent |
| `agent/responses` | Subscribe | Responses from actuators |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER` | MQTT broker URL | mqtt://localhost:1883 |
| `SENSOR_INTERVAL` | Sensor polling interval (ms) | 1000 |
| `AGENT_ID` | Associated agent ID | clariot_agent_1 |

## Usage

### Standalone

```bash
# Build and run
docker build -t clariot-senact -f senact.Dockerfile .
docker run -e MQTT_BROKER=mqtt://broker:1883 clariot-senact
```

### With Docker Compose

```yaml
services:
  mqtt:
    image: eclipse-mosquitto
  
  senact:
    build: ./SenActcontainer
    depends_on:
      - mqtt
  
  agent:
    build: ./Agentcontainer
    depends_on:
      - mqtt
      - senact
```

## Testing

```bash
# Publish test sensor reading
mosquitto_pub -h localhost -t sensors/temperature/factory_1 -m '{"value": 25.5, "unit": "celsius"}'

# Subscribe to actuator commands
mosquitto_sub -h localhost -t actuators/+/+
```
