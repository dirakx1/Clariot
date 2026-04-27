"""
Greenhouse-specific sensors extending Clariot's base Sensor pattern.

Drop-in replacements: swap MockSensor subclasses for real hardware drivers
(e.g., DHT22 for temperature/humidity, capacitive probe for soil moisture).
"""

import random
from datetime import datetime
from typing import Dict, Any

from SenActcontainer.sensor import MockSensor


class SoilMoistureSensor(MockSensor):
    """Capacitive soil moisture sensor (0-100 %, 100 = saturated)."""

    def __init__(self, sensor_id: str, location: str):
        super().__init__(sensor_id, "soil_moisture", location, "percent",
                         min_val=0, max_val=100)
        self._base_value = 45  # healthy starting moisture


class LightSensor(MockSensor):
    """Ambient light sensor in lux."""

    def __init__(self, sensor_id: str, location: str):
        super().__init__(sensor_id, "light", location, "lux",
                         min_val=0, max_val=100_000)
        self._base_value = 20_000  # overcast daylight baseline

    def read(self) -> Dict[str, Any]:
        reading = super().read()
        reading["value"] = round(max(0, reading["value"]), 0)
        return reading


class CO2Sensor(MockSensor):
    """CO₂ concentration sensor (ppm). Healthy range: 400-1500 ppm."""

    def __init__(self, sensor_id: str, location: str):
        super().__init__(sensor_id, "co2", location, "ppm",
                         min_val=350, max_val=2000)
        self._base_value = 800
