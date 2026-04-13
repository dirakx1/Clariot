# Clariot Use Cases

Clariot enables AI-powered IoT control across multiple domains through containerized agents with LLM reasoning.

## Smart Manufacturing

**Scenario**: Factory floor with temperature sensors, pressure monitors, and motor actuators.

```
Temperature Sensor → [Agent] → Decision: Adjust cooling → Motor Actuator
                    ↑
              User: "Keep factory below 25°C"
```

```bash
# Deploy industrial agents
docker-compose -f Agentcontainer/docker-compose.yml up -d

# Set temperature threshold
curl -X POST http://localhost:8080/agent/command \
  -d '{"actuator_id": "cooling_fan_factory", "command": "set_speed", "parameters": {"target_temp": 25}}'
```

## Environmental Monitoring

**Scenario**: Agricultural field monitoring with soil sensors, weather stations, and irrigation actuators.

```
Soil Moisture Sensor → [Agent] → Decision: Start irrigation → Water Valve
                              → [Agent] → Weather API check → Delay/Cancel
```

## Building Automation

**Scenario**: Smart office with occupancy sensors, HVAC control, and lighting.

```
Motion Sensor → [Agent] → Decision: Lights on, AC adjust → Relay, HVAC
               ↑
         User: "Meeting in conference room in 15 minutes"
```

## Multi-Layer Coordination

**Scenario**: Coordinating across Things Layer (edge), Industrial Layer (factory), and Analytics Layer (cloud).

```
Cloud Analytics: Predict high demand → Industrial Agent: Ramp up production
                                              ↓
Edge Agent: Monitor quality sensors → Flag deviations → Industrial Agent: Adjust parameters
```

## User Control Examples

### Natural Language Commands

```bash
# Query current state
curl -X POST http://localhost:8080/agent/query \
  -d '{"message": "What is the current temperature in the factory?"}'

# Response:
# {
#   "response": "The current temperature in factory_floor_1 is 23.5°C. 
#                The cooling system is running at 60% speed.",
#   "current_state": {
#     "temp_factory_1": {"value": 23.5, "unit": "celsius"}
#   }
# }
```

### WebSocket Real-Time Interaction

```javascript
// Connect to agent via WebSocket
const ws = new WebSocket("ws://localhost:8080/ws/agent");

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "Turn on all lights in warehouse 1"
  }));
};

ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log(response.data);
};
```

### Structured Commands

```bash
# Direct actuator command
curl -X POST http://localhost:8080/agent/command \
  -d '{
    "actuator_id": "motor_production_line_1",
    "command": "start",
    "parameters": {"speed": 75}
  }'
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│            Natural Language / API / Dashboard                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM CONTROL PLANE                             │
│   Agents process commands, reason about sensor data,            │
│   and decide on actions to take                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ MQTT / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              AGENT CONTAINERS (per layer)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Things      │  │  Industrial  │  │  Analytics   │         │
│  │  Layer       │  │  Layer       │  │  Layer        │         │
│  │  (Edge)      │  │  (Factory)   │  │  (Cloud)      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              SENSOR / ACTUATOR LAYER                             │
│     Sensors ───────────────────────────────────▶ Actuators      │
│     (Input)                                  (Output)            │
└─────────────────────────────────────────────────────────────────┘
```

## TEOS Reference Architecture

The TEOS (Things, Edge, Operations, Services) pattern implemented by Clariot:

<img src="./images/TEOS(3).png">

For more information on TEOS, see [references](references.md).
