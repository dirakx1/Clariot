# Things Layer - Edge Device Agents

The Things Layer is the edge computing layer where physical IoT devices interact with sensors and actuators through AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Things Layer                                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Raspberry  │  │  Raspberry  │  │   Edge       │             │
│  │  Pi 1       │  │  Pi 2       │  │   Gateway    │             │
│  │             │  │             │  │             │             │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │             │
│  │ │ Agent   │ │  │ │ Agent   │ │  │ │ Agent   │ │             │
│  │ └────┬────┘ │  │ └────┬────┘ │  │ └────┬────┘ │             │
│  │      │      │  │      │      │  │      │      │             │
│  │ ┌────┴────┐ │  │ ┌────┴────┐ │  │ ┌────┴────┐ │             │
│  │ │SenAct   │ │  │ │SenAct   │ │  │ │SenAct   │ │             │
│  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │             │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘             │
│        │                │                │                      │
│        └────────────────┼────────────────┘                      │
│                         │                                       │
│                    MQTT Bus                                      │
│                         │                                       │
│                         ▼                                       │
│              ┌────────────────────┐                              │
│              │  LLM Control Plane │                              │
│              │  (Cloud/Local)     │                              │
│              └────────────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### Edge Agent
Each edge device runs an **Agent Container** that:
- Processes local sensor data with LLM reasoning
- Makes real-time decisions without cloud round-trip
- Caches data for offline operation
- Syncs with cloud control plane when connected

### Sensor/Actuator Layer
- **Sensors**: Temperature, humidity, motion, pressure, etc.
- **Actuators**: Motors, valves, relays, displays, etc.
- All communicate via MQTT with standardized topics

## Data Flow

```
Sensor → MQTT → Agent (LLM reasoning) → Decision → MQTT → Actuator
              ↑
              │
User Command ─┘
```

1. **Sensor** collects physical data
2. **MQTT** publishes to `sensors/<type>/<location>`
3. **Agent** subscribes, processes with LLM, decides action
4. **MQTT** publishes command to `actuators/<type>/<location>`
5. **Actuator** executes the command

## Deployment

### Single Device
```bash
# Build agent container
docker build -t clariot-agent ./Agentcontainer

# Run with sensor/actuator
docker-compose -f SenActcontainer/docker-compose.yml up -d

# Run agent
docker run -e MQTT_BROKER=mqtt://localhost:1883 \
           -e LLM_PROVIDER=openai \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           clariot-agent
```

### Multi-Device Cluster
```bash
# On each Raspberry Pi
docker-compose up -d

# Agents automatically discover and communicate via MQTT
```

## Configuration

Environment variables for the Things Layer:

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_ID` | Unique agent identifier | `clariot_agent_1` |
| `AGENT_LAYER` | Layer identifier | `things` |
| `LLM_PROVIDER` | LLM provider | `openai` |
| `MQTT_BROKER` | MQTT broker URL | `mqtt://localhost:1883` |
| `SYNC_INTERVAL` | Cloud sync interval (seconds) | `60` |

## Topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `sensors/<type>/<location>` | Device → Broker | Sensor readings |
| `actuators/<type>/<location>` | Broker → Device | Actuator commands |
| `agent/commands` | Cloud → Device | Agent commands |
| `agent/status` | Device → Cloud | Agent status updates |

## Example

```bash
# Publish a sensor reading (from device)
mosquitto_pub -t sensors/temperature/factory_1 -m '{"value": 25.5, "unit": "celsius"}'

# Send actuator command (from cloud)
mosquitto_pub -t actuators/motor/factory_1 -m '{"command": "start", "parameters": {"speed": 50}}'
```
