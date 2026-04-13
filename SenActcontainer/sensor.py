"""
Sensor Handler - Reads data from physical sensors or mock inputs
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import threading

logger = logging.getLogger(__name__)


class Sensor:
    """Represents a single sensor with reading capabilities."""
    
    def __init__(self, sensor_id: str, sensor_type: str, location: str, unit: str = ""):
        self.sensor_id = sensor_id
        self.type = sensor_type
        self.location = location
        self.unit = unit
        self._callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable):
        """Set callback to be called when new reading is available."""
        self._callback = callback
    
    def read(self) -> Dict[str, Any]:
        """
        Read the sensor value.
        
        Override this method for actual hardware sensors.
        """
        raise NotImplementedError("Subclass must implement read()")


class MockSensor(Sensor):
    """Mock sensor for testing and development."""
    
    def __init__(self, sensor_id: str, sensor_type: str, location: str, unit: str = "",
                 min_val: float = 0, max_val: float = 100):
        super().__init__(sensor_id, sensor_type, location, unit)
        self.min_val = min_val
        self.max_val = max_val
        self._base_value = (min_val + max_val) / 2
    
    def read(self) -> Dict[str, Any]:
        """Generate mock sensor reading with some randomness."""
        import random
        
        # Generate realistic variation
        variation = random.uniform(-5, 5)
        value = self._base_value + variation
        value = max(self.min_val, min(self.max_val, value))
        
        return {
            "sensor_id": self.sensor_id,
            "type": self.type,
            "value": round(value, 2),
            "unit": self.unit,
            "location": self.location,
            "timestamp": datetime.utcnow().isoformat()
        }


class TemperatureSensor(MockSensor):
    """Mock temperature sensor."""
    
    def __init__(self, sensor_id: str, location: str):
        super().__init__(
            sensor_id, "temperature", location, "celsius",
            min_val=15, max_val=35
        )
        self._base_value = 22  # Room temperature baseline


class HumiditySensor(MockSensor):
    """Mock humidity sensor."""
    
    def __init__(self, sensor_id: str, location: str):
        super().__init__(
            sensor_id, "humidity", location, "percent",
            min_val=30, max_val=80
        )
        self._base_value = 55


class MotionSensor(MockSensor):
    """Mock motion sensor (boolean)."""
    
    def __init__(self, sensor_id: str, location: str):
        super().__init__(
            sensor_id, "motion", location, "boolean",
            min_val=0, max_val=1
        )
        self._triggered = False
    
    def read(self) -> Dict[str, Any]:
        import random
        
        # Random motion events (10% chance)
        if random.random() < 0.1:
            self._triggered = not self._triggered
        
        return {
            "sensor_id": self.sensor_id,
            "type": self.type,
            "value": self._triggered,
            "unit": self.unit,
            "location": self.location,
            "timestamp": datetime.utcnow().isoformat()
        }


class PressureSensor(MockSensor):
    """Mock pressure sensor."""
    
    def __init__(self, sensor_id: str, location: str):
        super().__init__(
            sensor_id, "pressure", location, "kPa",
            min_val=95, max_val=105
        )
        self._base_value = 101.3


class SensorManager:
    """
    Manages multiple sensors and their readings.
    
    Handles:
    - Sensor registration
    - Polling loop
    - Data formatting for MQTT publishing
    """
    
    def __init__(self, interval_ms: int = 1000):
        self.sensors: Dict[str, Sensor] = {}
        self.interval_ms = interval_ms
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
    
    def add_sensor(self, sensor: Sensor):
        """Register a sensor."""
        self.sensors[sensor.sensor_id] = sensor
        logger.info(f"Registered sensor: {sensor.sensor_id} ({sensor.type})")
    
    def remove_sensor(self, sensor_id: str):
        """Remove a sensor."""
        if sensor_id in self.sensors:
            del self.sensors[sensor_id]
            logger.info(f"Removed sensor: {sensor_id}")
    
    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get a sensor by ID."""
        return self.sensors.get(sensor_id)
    
    def read_all(self) -> Dict[str, Dict[str, Any]]:
        """Read all sensors and return their values."""
        readings = {}
        for sensor_id, sensor in self.sensors.items():
            try:
                readings[sensor_id] = sensor.read()
            except Exception as e:
                logger.error(f"Error reading sensor {sensor_id}: {e}")
                readings[sensor_id] = {
                    "sensor_id": sensor_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
        return readings
    
    def start_polling(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start polling all sensors at the configured interval.
        
        Args:
            callback: Function to call with sensor readings dict
        """
        self.is_running = True
        
        def poll_loop():
            while self.is_running:
                readings = self.read_all()
                callback(readings)
                time.sleep(self.interval_ms / 1000.0)
        
        self._thread = threading.Thread(target=poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"Started sensor polling (interval: {self.interval_ms}ms)")
    
    def stop_polling(self):
        """Stop the polling loop."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info("Stopped sensor polling")


# Factory for creating sensors from config
def create_sensors_from_config(config: Dict[str, Any]) -> SensorManager:
    """
    Create sensors from configuration dict.
    
    Args:
        config: Dict with sensor configurations
            {
                "sensors": [
                    {"id": "temp_1", "type": "temperature", "location": "factory_1", ...},
                    ...
                ]
            }
    """
    manager = SensorManager(interval_ms=config.get("interval_ms", 1000))
    
    for sensor_config in config.get("sensors", []):
        sensor_type = sensor_config.get("type", "").lower()
        sensor_id = sensor_config.get("id")
        location = sensor_config.get("location", "default")
        unit = sensor_config.get("unit", "")
        
        # Create appropriate sensor type
        if sensor_type == "temperature":
            sensor = TemperatureSensor(sensor_id, location)
        elif sensor_type == "humidity":
            sensor = HumiditySensor(sensor_id, location)
        elif sensor_type == "motion":
            sensor = MotionSensor(sensor_id, location)
        elif sensor_type == "pressure":
            sensor = PressureSensor(sensor_id, location)
        else:
            # Generic mock sensor
            sensor = MockSensor(sensor_id, sensor_type, location, unit)
        
        manager.add_sensor(sensor)
    
    return manager


if __name__ == "__main__":
    # Test with mock sensors
    logging.basicConfig(level=logging.INFO)
    
    manager = SensorManager(interval_ms=1000)
    
    # Add some mock sensors
    manager.add_sensor(TemperatureSensor("temp_factory_1", "factory_floor_1"))
    manager.add_sensor(HumiditySensor("humidity_factory_1", "factory_floor_1"))
    manager.add_sensor(MotionSensor("motion_entry_door", "entry_door"))
    
    def print_readings(readings):
        print(f"\n[{datetime.now().isoformat()}] Sensor Readings:")
        for sensor_id, reading in readings.items():
            print(f"  {sensor_id}: {reading}")
    
    manager.start_polling(print_readings)
    time.sleep(10)
    manager.stop_polling()
