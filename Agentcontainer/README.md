# Agent Container

The Agent Container is the core LLM-powered agent layer that processes sensor data and controls actuators.

## Components

### agent_core/
- `agent.py` - Main agent class with LLM reasoning
- `sensor_handler.py` - Receives and parses sensor data
- `actuator_controller.py` - Sends commands to actuators
- `memory.py` - Short and long-term memory for agents

### llm_gateway/
- `gateway.py` - Connects to LLM providers (OpenAI, Anthropic, local LLM)
- `prompt_builder.py` - Constructs prompts from sensor data
- `response_parser.py` - Parses LLM responses into actionable commands

### control_plane/
- `server.py` - REST/WebSocket API for user interaction
- `chat_interface.py` - Natural language interface
- `rules_engine.py` - Automation rules and thresholds

### mcp_protocol/
- `protocol.py` - Model Context Protocol implementation
- `messages.py` - Message types for agent communication
- `transport.py` - MQTT/HTTP transport layer

## Architecture

```
Sensors → [Ingest] → Agent Core → [LLM Reasoning] → Actuator Commands → Actuators
                ↑                                                    ↓
                └──────────── LLM Control Plane ◄───────────────┘
                                    ↑
                              User Commands
```

## Usage

```bash
# Build agent container
docker build -t clariot-agent -f agent.Dockerfile .

# Run with LLM provider
docker run -e LLM_PROVIDER=openai \
           -e OPENAI_API_KEY=$OPENAI_API_KEY \
           clariot-agent
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (openai, anthropic, ollama) | openai |
| `LLM_MODEL` | Model name | gpt-4 |
| `MQTT_BROKER` | MQTT broker URL | mqtt://localhost:1883 |
| `SENSOR_TOPIC` | Topic to subscribe for sensor data | sensors/# |
| `ACTUATOR_TOPIC` | Topic to publish actuator commands | actuators/# |
