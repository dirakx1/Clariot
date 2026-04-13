"""
Mock Sensors - Simulates sensor data for testing without hardware
"""

import os
import json
import time
import logging
import random
from datetime import datetime

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MockSensorSimulator:
    """
    Generates realistic mock sensor data for testing.
    
    Publishes to MQTT topics in the same format as real sensors.
    """
    
    def __init__(self, mqtt_broker: str, agent_id: str = None):
        self.mqtt_broker = mqtt_broker
        self.agent_id = agent_id or os.getenv("AGENT_ID", "clariot_agent_1")
        self.is_running = False
        self._client = None
        self._connected = False
        
        # Parse broker URL
        self._broker_host = mqtt_broker.replace("mqtt://", "").split(":")[0]
        self._broker_port = int(self.mqtt_broker.split(":")[-1]) if ":" in self.mqtt_broker else 1883
        
        # Sensor state
        self._temp_base = 22.0
        self._humidity_base = 55.0
        self._motion_state = False
        self._pressure_base = 101.3
    
    def _connect(self):
        """Connect to MQTT broker."""
        try:
            self._client = mqtt.Client(
                client_id=f"clariot_mock_{self.agent_id}_{int(time.time())}",
                clean_session=True
            )
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            
            self._client.connect(self._broker_host, self._broker_port, 60)
            self._client.loop_start()
            
            timeout = 5
            start = time.time()
            while not self._connected and time.time() - start < timeout:
                time.sleep(0.1)
            
            if self._connected:
                logger.info(f"Mock sensor connected to MQTT at {self.mqtt_broker}")
            
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            logger.info("Mock sensor MQTT connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
    
    def _generate_temperature(self) -> dict:
        """Generate mock temperature reading."""
        variation = random.uniform(-2, 2)
        value = self._temp_base + variation
        
        return {
            "sensor_id": "temp_factory_1",
            "type": "temperature",
            "value": round(value, 1),
            "unit": "celsius",
            "location": "factory_floor_1",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_humidity(self) -> dict:
        """Generate mock humidity reading."""
        variation = random.uniform(-5, 5)
        value = self._humidity_base + variation
        value = max(30, min(80, value))
        
        return {
            "sensor_id": "humidity_factory_1",
            "type": "humidity",
            "value": round(value, 1),
            "unit": "percent",
            "location": "factory_floor_1",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_motion(self) -> dict:
        """Generate mock motion reading."""
        # Random motion event (5% chance)
        if random.random() < 0.05:
            self._motion_state = not self._motion_state
        
        return {
            "sensor_id": "motion_entry",
            "type": "motion",
            "value": self._motion_state,
            "unit": "boolean",
            "location": "entry_door",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_pressure(self) -> dict:
        """Generate mock pressure reading."""
        variation = random.uniform(-0.5, 0.5)
        value = self._pressure_base + variation
        
        return {
            "sensor_id": "pressure_factory_1",
            "type": "pressure",
            "value": round(value, 1),
            "unit": "kPa",
            "location": "factory_floor_1",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _publish(self, topic: str, data: dict):
        """Publish data to MQTT topic."""
        if not self._connected:
            return
        
        try:
            payload = json.dumps(data)
            result = self._client.publish(topic, payload, qos=1)
            if result.rc == 0:
                logger.debug(f"Published to {topic}: {data['value']}")
        except Exception as e:
            logger.error(f"Error publishing: {e}")
    
    def _generate_all(self):
        """Generate and publish all mock sensor readings."""
        # Temperature
        temp = self._generate_temperature()
        self._publish("sensors/temperature/factory_floor_1", temp)
        
        # Humidity
        humidity = self._generate_humidity()
        self._publish("sensors/humidity/factory_floor_1", humidity)
        
        # Motion
        motion = self._generate_motion()
        self._publish("sensors/motion/entry_door", motion)
        
        # Pressure
        pressure = self._generate_pressure()
        self._publish("sensors/pressure/factory_floor_1", pressure)
        
        # Also slowly drift the base values
        self._temp_base += random.uniform(-0.2, 0.2)
        self._temp_base = max(18, min(28, self._temp_base))
        
        self._humidity_base += random.uniform(-0.5, 0.5)
        self._humidity_base = max(40, min(70, self._humidity_base))
    
    def start(self):
        """Start generating mock sensor data."""
        if self.is_running:
            return
        
        self._connect()
        self.is_running = True
        
        logger.info("Mock sensor simulator started")
        
        while self.is_running:
            self._generate_all()
            time.sleep(5)  # Generate new readings every 5 seconds
    
    def stop(self):
        """Stop the simulator."""
        self.is_running = False
        
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        
        self._connected = False
        logger.info("Mock sensor simulator stopped")


def main():
    """Run the mock sensor simulator."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://localhost:1883")
    agent_id = os.getenv("AGENT_ID", "clariot_agent_1")
    
    simulator = MockSensorSimulator(mqtt_broker, agent_id)
    
    def signal_handler(sig, frame):
        print("\nStopping mock sensors...")
        simulator.stop()
        exit(0)
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    simulator.start()


if __name__ == "__main__":
    main()
