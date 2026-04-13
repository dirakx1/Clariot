# Industrial Layer - Factory Floor Agents

The Industrial Layer handles heavy machinery, factory automation, and industrial-grade sensor/actuator control with specialized agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Industrial Layer                           │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Industrial Control System               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │   │
│  │  │  PLC 1   │  │  PLC 2   │  │  PLC 3   │  │  HMI    │  │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘  │   │
│  │       │             │             │             │       │   │
│  │       └─────────────┴─────────────┴─────────────┘       │   │
│  │                           │                             │   │
│  │                    ┌──────┴──────┐                      │   │
│  │                    │   Agent     │                      │   │
│  │                    │   Bridge    │                      │   │
│  │                    └──────┬──────┘                      │   │
│  └───────────────────────────┼──────────────────────────────┘   │
│                              │                                    │
│  ┌───────────────────────────┼──────────────────────────────┐   │
│  │              ┌─────────────┴─────────────┐               │   │
│  │              │   Industrial Agent        │               │   │
│  │              │   (LLM-powered)           │               │   │
│  │              └─────────────┬─────────────┘               │   │
│  └─────────────────────────────┼───────────────────────────┘   │
│                                │                                 │
│  Sensors ──────────────────────┼───────────────────── Actuators │
│  (temp, pressure, vibration)    │         (motors, valves)     │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### PLC Bridge
Connects legacy PLCs (Siemens, Allen-Bradley, etc.) to the agent system:
- Modbus TCP/IP support
- OPC-UA integration
- Profinet support

### Industrial Agent
Specialized agent for factory environments:
- Safety-critical decision making
- Real-time response (<100ms)
- Integration with PLCs and SCADA
- Anomaly detection for machinery

### HMI Integration
Human-machine interface connection for:
- Real-time monitoring dashboards
- Manual override controls
- Alarm acknowledgment

## Safety Features

1. **Fail-safe defaults**: All actuators return to safe state on disconnect
2. **Rate limiting**: Prevents rapid cycling of machinery
3. **Manual override**: Physical switches take precedence over agents
4. **Audit logging**: All commands logged for compliance

## Data Flow

```
PLC/Sensors → PLC Bridge → Industrial Agent → LLM Reasoning → PLC Bridge → Actuators
                                              ↑
                            User Commands ─────┘
```

## Example Configuration

```yaml
# Industrial layer docker-compose snippet
services:
  industrial_agent:
    build: ./Agentcontainer
    environment:
      - AGENT_LAYER=industrial
      - SAFETY_MODE=true
      - MAX_CYCLE_RATE=10/minute
    devices:
      - /dev/ttyUSB0:/dev/ttyMODBUS  # PLC connection
```

## Industrial Protocols Supported

| Protocol | Use Case | Support |
|----------|----------|---------|
| Modbus TCP/IP | General PLC communication | Full |
| OPC-UA | SCADA integration | Full |
| Profinet | Siemens PLCs | Via gateway |
| EtherNet/IP | Allen-Bradley PLCs | Via gateway |

## Emergency Stop

All industrial agents implement emergency stop:

```bash
# Emergency stop all actuators
curl -X POST http://agent:8080/agent/emergency-stop

# Check safety status
curl http://agent:8080/agent/safety-status
```

Returns:
```json
{
  "safety_mode": true,
  "actuators_stopped": true,
  "last_safe_state": "2024-01-15T10:30:00Z",
  "emergency_reason": null
}
```
