# Greenhouse Monitoring — Clariot Example

An end-to-end reference implementation showing how to build an LLM-powered IoT agent with Clariot. The agent monitors a greenhouse, reasons about sensor readings, and autonomously controls irrigation, lighting, and ventilation.

## Architecture

```
Browser (port 3000)
      ↓ HTTP / WebSocket
Dashboard App (app.py)
      ↓ HTTP
Agent Control Plane (:8080)
      ↓
GreenhouseAgent (agent.py)
 ├── LLMGateway      → Anthropic / OpenAI / Ollama
 ├── SensorManager   → temperature, humidity, soil moisture, light, CO₂
 └── ActuatorManager → irrigation valve, grow lights, ventilation fan
      ↓ MQTT
SenActcontainer (optional physical layer)
```

## Files

| File | Purpose |
|------|---------|
| `sensors.py` | `SoilMoistureSensor`, `LightSensor`, `CO2Sensor` — domain sensors |
| `actuators.py` | `IrrigationValve`, `GrowLight`, `VentilationFan` — domain actuators |
| `agent.py` | `GreenhouseAgent` — wires LLM + sensors + actuators, drives control loop |
| `app.py` | FastAPI dashboard that proxies the agent's control plane |
| `docker-compose.yml` | Full stack: MQTT + agent + SenAct + dashboard |

## Quickstart

### 1. Set your LLM API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY for OpenAI
```

### 2. Run with Docker Compose

```bash
cd examples/greenhouse_monitoring
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| Agent API | http://localhost:8080 |
| MQTT broker | localhost:1883 |

### 3. Run without Docker (mock sensors, no MQTT)

```bash
# From the repo root
pip install -r examples/greenhouse_monitoring/requirements.txt

# Start the agent (polls mock sensors every 5 s, calls LLM, controls actuators)
python -m examples.greenhouse_monitoring.agent

# In a separate terminal, start the dashboard
uvicorn examples.greenhouse_monitoring.app:app --port 3000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | `anthropic`, `openai`, or `ollama` |
| `LLM_MODEL` | `claude-sonnet-4-6` | Model name for the chosen provider |
| `ANTHROPIC_API_KEY` | — | Required when `LLM_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | — | Required when `LLM_PROVIDER=openai` |
| `SENSOR_INTERVAL` | `5000` | Polling interval in milliseconds |
| `AGENT_URL` | `http://localhost:8080` | Used by `app.py` to reach the agent |
| `MQTT_BROKER` | `mqtt://localhost:1883` | MQTT broker URL |

## Thresholds

The agent is pre-configured with these healthy ranges, passed to the LLM as context:

| Sensor | Min | Max | Unit |
|--------|-----|-----|------|
| Temperature | 15 | 30 | °C |
| Humidity | 50 | 80 | % |
| Soil moisture | 35 | 70 | % |
| Light | 5 000 | 60 000 | lux |
| CO₂ | 400 | 1 500 | ppm |

## Dashboard

Open http://localhost:3000 to see:

- **Live sensor readings** — refreshed every 3 seconds via WebSocket
- **Actuator states** — current status of valve, lights, and fan
- **Natural language query box** — ask the agent anything; it will respond and optionally trigger actuator actions

Example queries:
- *"Should I water the plants right now?"*
- *"The temperature is rising fast, what should I do?"*
- *"Turn off the grow lights for the night"*

## Extending to Real Hardware

Each mock class has a single method to override:

**Custom sensor** — subclass `Sensor` and implement `read()`:

```python
from SenActcontainer.sensor import Sensor

class DHT22Sensor(Sensor):
    def read(self):
        import adafruit_dht, board
        dht = adafruit_dht.DHT22(board.D4)
        return {
            "sensor_id": self.sensor_id,
            "type": "temperature",
            "value": dht.temperature,
            "unit": "celsius",
            "location": self.location,
            "timestamp": datetime.utcnow().isoformat(),
        }
```

**Custom actuator** — subclass `Actuator` and implement `execute()`:

```python
from SenActcontainer.actuator import Actuator
import RPi.GPIO as GPIO

class GPIOValve(Actuator):
    PIN = 17

    def execute(self, command, parameters=None):
        GPIO.setup(self.PIN, GPIO.OUT)
        GPIO.output(self.PIN, GPIO.HIGH if command == "open" else GPIO.LOW)
        self.state = command
        return {"status": "success", "command": command}
```

Swap the mock instances in `agent.py` for your real classes — everything else stays the same.

## Using a Different LLM Provider

```bash
# Ollama (local, no API key needed)
LLM_PROVIDER=ollama LLM_MODEL=llama3 python -m examples.greenhouse_monitoring.agent

# OpenAI
LLM_PROVIDER=openai LLM_MODEL=gpt-4o OPENAI_API_KEY=sk-... python -m examples.greenhouse_monitoring.agent
```
