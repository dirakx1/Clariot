# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Clariot is an AI-powered IoT agent platform where LLM-powered agents process sensor data and control actuators. The core flow is: **Sensor → MQTT → LLM Agent → MQTT → Actuator**.

## Running the Project

```bash
# Full platform (all containers)
docker-compose up

# Individual containers
docker-compose -f SenActcontainer/docker-compose.yml up
docker-compose -f Agentcontainer/docker-compose.yml up

# Install Docker on ARM devices
bash installation.sh
```

There is no Makefile. The project has no test suite yet.

## Architecture

Three-layer system communicating over MQTT:

```
User (REST/WebSocket) → Control Plane (FastAPI :8080)
                               ↓
                         Agent Core (LLM Reasoning)
                         ├── Memory (short-term deque + long-term JSONL)
                         ├── LLM Gateway (OpenAI / Anthropic / Ollama)
                         └── MCP Protocol (message format standardization)
                               ↓ MQTT
                    Sensor/Actuator Container
                    ├── Sensors → publishes to sensors/<type>/<location>
                    └── Actuators ← subscribes to actuators/<type>/<location>
```

### Container Roles

| Container | Purpose |
|-----------|---------|
| `Agentcontainer/` | LLM reasoning engine + REST/WebSocket control plane |
| `SenActcontainer/` | Sensor polling and actuator command execution |
| `Comcontainer/` | Communication/messaging infrastructure |
| `Indcontainer/` | Industrial/PLC-specific integration layer |
| `Appcontainer/` | Application deployment container |

### Key Source Files

**Agent (`Agentcontainer/agent_core/`)**
- `agent.py` — `ClariotAgent`: receives sensor data, builds LLM prompt, parses JSON actions, dispatches actuator commands
- `memory.py` — `AgentMemory`: short-term in-memory deque (last 100 readings) + long-term file-based JSONL (last 24h, 1000 entries)
- `sensor_handler.py` — MQTT subscriber for `sensors/#`; falls back to mock mode if broker unavailable
- `actuator_controller.py` — MQTT publisher to `actuators/<type>/<location>`

**LLM Gateway (`Agentcontainer/llm_gateway/`)**
- `gateway.py` — `LLMGateway`: unified async `query()` dispatching to `_query_openai()`, `_query_anthropic()`, or `_query_ollama()`
- `prompt_builder.py` — constructs reasoning prompts from sensor context and memory
- `response_parser.py` — extracts JSON action arrays from free-form LLM text

**Control Plane (`Agentcontainer/control_plane/server.py`)**
- REST: `GET /health`, `GET /agent/status`, `POST /agent/query`, `POST /agent/command`, `GET /agent/memory/recent`, `GET /agent/sensors`
- WebSocket: `WS /ws/agent` (bidirectional), `WS /ws/sensors` (streaming)

**SenActcontainer/**
- `sensor.py` — `TemperatureSensor`, `HumiditySensor`, `MotionSensor`, `PressureSensor` with mock implementations
- `actuator.py` — `MotorActuator`, `ValveActuator`, `RelayActuator`
- `data_ingest.py` — polls sensors and publishes to MQTT (QoS=1)
- `command_router.py` — routes MQTT `actuators/+/+` messages to local actuators; publishes responses to `agent/responses/<actuator_id>`

**MCP Protocol (`Agentcontainer/mcp_protocol/transport.py`)** — message envelope (version, from, to, timestamp, payload, context) with subscription-based handlers

## Environment Variables

```
LLM_PROVIDER=openai|anthropic|ollama
LLM_MODEL=gpt-4|claude-3-sonnet-20240229|llama2
MQTT_BROKER=mqtt://localhost:1883
SENSOR_INTERVAL=1000          # milliseconds
CONTROL_PLANE_PORT=8080
AGENT_ID=clariot_agent_1
AGENT_LAYER=things|industrial|analytics
LOG_LEVEL=INFO
```

## MQTT Topic Conventions

- Sensor data: `sensors/<type>/<location>` (e.g., `sensors/temperature/factory_1`)
- Actuator commands: `actuators/<type>/<location>`
- Agent responses: `agent/responses/<actuator_id>`
- Broadcast commands: `agent/commands`

## LLM Action Format

The LLM returns JSON arrays that `response_parser.py` extracts:

```json
[{"actuator_id": "valve_1", "command": "open", "parameters": {"percent": 50}}]
```

## Layers

- **Things Layer** — edge devices (Raspberry Pi), GPIO/I2C/SPI via `RPi.GPIO`, `smbus`, `spidev`
- **Industrial Layer** — factory/PLC integration (Modbus, OPC-UA planned)
- **Analytics Layer** — cloud-side processing and dashboards
