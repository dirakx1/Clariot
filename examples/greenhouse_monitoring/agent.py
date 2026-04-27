"""
Greenhouse Monitoring Agent — Clariot architecture reference example.

Flow: sensors poll → SensorManager callback → GreenhouseAgent.on_reading()
      → LLMGateway.query() → parse actions → ActuatorManager.execute_batch()

Run standalone (mock sensors, no MQTT needed):
    python -m examples.greenhouse_monitoring.agent
"""

import asyncio
import json
import logging
import os
from collections import deque
from datetime import datetime
from typing import Any, Dict, List

from Agentcontainer.llm_gateway.gateway import LLMGateway
from SenActcontainer.sensor import SensorManager, TemperatureSensor, HumiditySensor
from SenActcontainer.actuator import ActuatorManager

from .sensors import SoilMoistureSensor, LightSensor, CO2Sensor
from .actuators import IrrigationValve, GrowLight, VentilationFan

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Thresholds that drive the LLM prompt context
THRESHOLDS = {
    "temperature":    {"min": 15, "max": 30, "unit": "°C"},
    "humidity":       {"min": 50, "max": 80, "unit": "%"},
    "soil_moisture":  {"min": 35, "max": 70, "unit": "%"},
    "light":          {"min": 5_000, "max": 60_000, "unit": "lux"},
    "co2":            {"min": 400, "max": 1_500, "unit": "ppm"},
}


class GreenhouseAgent:
    """
    LLM-powered agent that monitors greenhouse sensors and controls actuators.

    Inherits no base class — it composes Clariot's LLMGateway, SensorManager,
    and ActuatorManager directly, showing how to wire them together.
    """

    def __init__(self):
        self.agent_id = os.getenv("AGENT_ID", "greenhouse_agent_1")
        self._history: deque = deque(maxlen=50)  # short-term memory

        # --- LLM ---
        self.llm = LLMGateway(
            provider=os.getenv("LLM_PROVIDER", "anthropic"),
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-6"),
        )

        # --- Sensors ---
        self.sensors = SensorManager(interval_ms=int(os.getenv("SENSOR_INTERVAL", "5000")))
        self.sensors.add_sensor(TemperatureSensor("temp_gh1", "greenhouse_1"))
        self.sensors.add_sensor(HumiditySensor("hum_gh1", "greenhouse_1"))
        self.sensors.add_sensor(SoilMoistureSensor("soil_gh1", "greenhouse_1"))
        self.sensors.add_sensor(LightSensor("light_gh1", "greenhouse_1"))
        self.sensors.add_sensor(CO2Sensor("co2_gh1", "greenhouse_1"))

        # --- Actuators ---
        self.actuators = ActuatorManager()
        self.actuators.add_actuator(IrrigationValve("irrigation_gh1", "greenhouse_1"))
        self.actuators.add_actuator(GrowLight("lights_gh1", "greenhouse_1"))
        self.actuators.add_actuator(VentilationFan("fan_gh1", "greenhouse_1"))

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self):
        """Start the synchronous sensor polling loop (blocks until stop)."""
        logger.info(f"[{self.agent_id}] Starting greenhouse agent")
        self.sensors.start_polling(self._sync_on_reading)

    def stop(self):
        self.sensors.stop_polling()
        logger.info(f"[{self.agent_id}] Agent stopped")

    async def ask(self, question: str) -> str:
        """Natural-language query about current greenhouse state."""
        state = self._current_state_summary()
        prompt = f"""You are the AI controller for a greenhouse.

Current state:
{state}

User question: {question}

Answer concisely. If an actuator change is warranted, include a JSON block:
```json
[{{"actuator_id": "...", "command": "...", "parameters": {{}}}}]
```"""
        response = await self.llm.query(prompt)
        actions = self._parse_actions(response)
        if actions:
            self.actuators.execute_batch(actions)
        return response

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _sync_on_reading(self, readings: Dict[str, Dict[str, Any]]):
        """Called by SensorManager's polling thread; bridges to async."""
        asyncio.run(self._on_reading(readings))

    async def _on_reading(self, readings: Dict[str, Dict[str, Any]]):
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "readings": readings,
        }
        self._history.append(snapshot)

        prompt = self._build_prompt(readings)
        response = await self.llm.query(prompt)
        actions = self._parse_actions(response)

        if actions:
            results = self.actuators.execute_batch(actions)
            logger.info(f"Actions executed: {results}")
        else:
            logger.debug("No actions required this cycle")

    def _build_prompt(self, readings: Dict[str, Dict[str, Any]]) -> str:
        recent = list(self._history)[-5:]  # last 5 snapshots for context
        return f"""You are an autonomous greenhouse controller.

THRESHOLDS:
{json.dumps(THRESHOLDS, indent=2)}

CURRENT READINGS:
{json.dumps(readings, indent=2)}

RECENT HISTORY (last {len(recent)} cycles):
{json.dumps(recent, indent=2)}

AVAILABLE ACTUATORS:
- irrigation_gh1  → commands: open (percent 0-100), close
- lights_gh1      → commands: set_brightness (percent 0-100), on, off
- fan_gh1         → commands: set_speed (percent 0-100), on, off

Respond with a JSON array of actions only. Use [] if no action is needed.
Example: [{{"actuator_id": "fan_gh1", "command": "set_speed", "parameters": {{"percent": 60}}}}]"""

    def _parse_actions(self, response: str) -> List[Dict]:
        try:
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                return json.loads(response[start:end].strip())
            if "[" in response:
                start = response.find("[")
                end = response.rfind("]") + 1
                return json.loads(response[start:end])
        except Exception as e:
            logger.warning(f"Could not parse actions from LLM response: {e}")
        return []

    def _current_state_summary(self) -> str:
        readings = self.sensors.read_all()
        actuator_states = self.actuators.list_actuators()
        return json.dumps({"sensors": readings, "actuators": actuator_states}, indent=2)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = GreenhouseAgent()
    try:
        agent.start()
        # keep main thread alive while polling thread runs
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
