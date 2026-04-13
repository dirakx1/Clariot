# Clariot AI Agent Platform

Clariot is an AI-powered IoT agent platform that uses LLM-powered agents to process sensor data and control actuators across all layers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│            Natural Language / API / Voice Commands                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM CONTROL PLANE                             │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Agent Core: LLM reasoning, decision making, memory     │   │
│   │  Sensor Handler: Receives and parses sensor data        │   │
│   │  Actuator Controller: Sends commands to actuators       │   │
│   └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SENSOR / ACTUATOR LAYER                             │
│     Sensors ────────────────────────────────▶ Actuators         │
│     (Input)    Agent processes & decides       (Output)          │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Start MQTT Broker
```bash
docker-compose up -d mqtt
```

### 2. Start Sensor/Actuator Container
```bash
docker-compose -f SenActcontainer/docker-compose.yml up -d
```

### 3. Start Agent Container
```bash
docker build -t clariot-agent ./Agentcontainer
docker run -e MQTT_BROKER=mqtt://localhost:1883 \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           clariot-agent
```

### 4. Query the Agent
```bash
curl -X POST http://localhost:8080/agent/query \
  -d '{"message": "What is the current temperature?"}'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/agent/status` | GET | Agent status |
| `/agent/query` | POST | Natural language query |
| `/agent/command` | POST | Direct actuator command |
| `/agent/sensors` | GET | Current sensor state |
| `/agent/memory/recent` | GET | Recent agent memory |
| `/ws/agent` | WebSocket | Real-time agent interaction |
| `/ws/sensors` | WebSocket | Real-time sensor streaming |

## Use Cases

- **Smart Manufacturing**: Monitor factory sensors, control machinery
- **Environmental Monitoring**: Track conditions, trigger alerts/actions
- **Building Automation**: HVAC, lighting, security via AI agents
- **Agricultural Control**: Monitor soil, weather, control irrigation
