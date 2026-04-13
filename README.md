# Clariot - AI-Powered IoT Agent Platform

Clariot is an **AI agent-based IoT development platform** that enables containerized LLM-powered agents to interact with sensors and actuators across all layers. The platform uses a **Sensor → Agent (LLM) → Actuator** architecture where AI agents process sensor data and produce actions.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER CONTROL                            │
│            (Chat Interface / API / Voice Commands)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ Natural Language / Commands
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM CONTROL PLANE                            │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │  Agent       │  │  Agent       │  │  Agent       │          │
│   │  Orchestrator│  │  Planner     │  │  Coordinator │          │
│   └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ Agent Messages (MCP/MQTT/AMQP)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT CONTAINERS                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │
│  │ Layer 1     │  │ Layer 2     │  │ Layer N     │               │
│  │ Agent       │  │ Agent       │  │ Agent       │               │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘               │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────────┐         │
│  │              SENSOR / ACTUATOR DATA BUS            │         │
│  └─────────────────────────────────────────────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
    ┌─────────────────┐           ┌─────────────────┐
    │    SENSORS      │           │   ACTUATORS     │
    │  (Data Input)   │           │  (Actions Out)  │
    │  • Temperature  │           │  • Motors       │
    │  • Pressure     │           │  • Valves       │
    │  • Proximity    │           │  • Switches     │
    │  • Camera       │           │  • Displays     │
    └─────────────────┘           └─────────────────┘
```

## Core Concepts

### Agent Architecture
Each layer contains **autonomous AI agents** that:
- **Receive** data from sensors
- **Process** using LLM reasoning
- **Decide** on actions to take
- **Output** commands to actuators

### Data Flow
1. **Sensor Layer**: Collects physical data (temperature, motion, etc.)
2. **Agent Processing**: LLM analyzes data and decides response
3. **Actuator Layer**: Executes physical actions based on agent decisions

### User Control
Users control the entire system through:
- **Natural Language**: Chat with the LLM control plane
- **API**: REST/WebSocket API for programmatic control
- **Rules**: Define automation rules and thresholds

## Layers

| Layer | Purpose | Agent Type |
|-------|---------|------------|
| [Things Layer](ThingsLayer.md) | Edge devices, local processing | Edge Agent |
| [Industrial Layer](IndustrialLayer.md) | Factory, heavy machinery | Industrial Agent |
| [Analytics Layer](AnalyticsLayer.md) | Cloud processing, long-term storage | Analytics Agent |
| [Agent Layer](AgentLayer.md) | LLM orchestration and control | Orchestrator Agent |

## Quick Start

```bash
# Start the full platform
docker-compose up

# Start specific layer
docker-compose up -f SenActcontainer/docker-compose.yml

# Chat with the LLM control plane
curl -X POST http://localhost:8080/api/agent/query \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current temperature in the factory?"}'
```

## Use Cases

- **Smart Manufacturing**: Agents monitor factory sensors and control machinery
- **Environmental Monitoring**: Track conditions and trigger alerts/actions
- **Building Automation**: HVAC, lighting, security via AI agents
- **Agricultural Control**: Monitor soil, weather, control irrigation

## Getting Started

1. [Install](installation.md) the platform
2. Configure your [sensors and actuators](SenActcontainer/README.md)
3. Connect to the [LLM Control Plane](AgentLayer.md)
4. Define your [automation rules](AgentLayer.md#control-plane)

## License

MIT License - See [LICENSE.md](LICENSE.md)
