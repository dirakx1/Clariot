"""
Greenhouse-specific actuators extending Clariot's base Actuator pattern.

To connect real hardware, subclass Actuator directly and implement execute()
with your GPIO/relay/PWM logic instead of inheriting from MockActuator.
"""

from typing import Dict, Any

from SenActcontainer.actuator import MockActuator


class IrrigationValve(MockActuator):
    """Solenoid valve controlling drip irrigation (0-100 % open)."""

    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "irrigation_valve", location)
        self._open_percent = 0

    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        parameters = parameters or {}
        if command == "open":
            self._open_percent = parameters.get("percent", 100)
            self.state = "open"
            return {"status": "success", "open_percent": self._open_percent}
        if command == "close":
            self._open_percent = 0
            self.state = "closed"
            return {"status": "success", "open_percent": 0}
        return super().execute(command, parameters)


class GrowLight(MockActuator):
    """LED grow-light panel with dimming (0-100 % brightness)."""

    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "grow_light", location)
        self._brightness = 0

    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        parameters = parameters or {}
        if command == "set_brightness":
            self._brightness = max(0, min(100, parameters.get("percent", 0)))
            self.state = "on" if self._brightness > 0 else "off"
            return {"status": "success", "brightness": self._brightness}
        if command in ("on", "off"):
            self._brightness = 100 if command == "on" else 0
            self.state = command
            return {"status": "success", "brightness": self._brightness}
        return super().execute(command, parameters)


class VentilationFan(MockActuator):
    """Roof ventilation fan (speed 0-100 %)."""

    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "vent_fan", location)
        self._speed = 0

    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        parameters = parameters or {}
        if command == "set_speed":
            self._speed = max(0, min(100, parameters.get("percent", 0)))
            self.state = "running" if self._speed > 0 else "idle"
            return {"status": "success", "speed": self._speed}
        if command in ("on", "off"):
            self._speed = 100 if command == "on" else 0
            self.state = "running" if self._speed else "idle"
            return {"status": "success", "speed": self._speed}
        return super().execute(command, parameters)
