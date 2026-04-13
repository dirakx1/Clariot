"""
Sensor Handler - Receives and parses sensor data from MQTT
"""

import json
import logging
from typing import Dict, Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class SensorHandler:
    """
    Handles incoming sensor data via MQTT subscription.
    
    Sensors publish data to topics like:
    - sensors/temperature/factory_floor_1
    - sensors/humidity/warehouse_2
    - sensors/motion/entry_door
    """
    
    def __init__(self, agent_id: str, mqtt_broker: str = None):
        self.agent_id = agent_id
        self.mqtt_broker = mqtt_broker or os.getenv("MQTT_BROKER", "mqtt://localhost:1883")
        self.subscribed_topics = []
        self.callback: Callable[[Dict], Awaitable] = None
        self._client = None
        logger.info(f"SensorHandler initialized for agent {agent_id}")
    
    async def start_listening(self, callback: Callable[[Dict[str, Any]], Awaitable]):
        """
        Start listening to sensor topics and processing data.
        
        Args:
            callback: Async function to call with parsed sensor data
        """
        self.callback = callback
        
        # Import paho-mqtt here to avoid import error if not installed
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning("paho-mqtt not installed, using mock mode")
            await self._start_mock_mode()
            return
        
        # Parse MQTT broker URL
        broker_host = self.mqtt_broker.replace("mqtt://", "").split(":")[0]
        broker_port = int(self.mqtt_broker.split(":")[-1]) if ":" in self.mqtt_broker else 1883
        
        self._client = mqtt.Client(client_id=f"clariot_agent_{self.agent_id}")
        self._client.on_message = self._on_message
        self._client.on_connect = self._on_connect
        
        try:
            self._client.connect(broker_host, broker_port, 60)
            self._client.loop_start()
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}")
        except Exception as e:
            logger.warning(f"Could not connect to MQTT: {e}, using mock mode")
            await self._start_mock_mode()
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            topic = os.getenv("SENSOR_TOPIC", "sensors/#")
            client.subscribe(topic)
            logger.info(f"Subscribed to sensor topic: {topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT message."""
        try:
            # Parse topic: sensors/<type>/<location>
            topic_parts = msg.topic.split("/")
            if len(topic_parts) >= 3:
                sensor_type = topic_parts[1]
                location = topic_parts[2]
            else:
                sensor_type = "unknown"
                location = "unknown"
            
            # Parse payload
            try:
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                payload = {"raw_value": msg.payload.decode()}
            
            sensor_data = {
                "sensor_id": f"{sensor_type}_{location}",
                "type": sensor_type,
                "value": payload.get("value", payload),
                "unit": payload.get("unit", ""),
                "location": location,
                "timestamp": payload.get("timestamp", datetime.utcnow().isoformat()),
                "raw_topic": msg.topic
            }
            
            # Schedule callback
            if self.callback:
                import asyncio
                asyncio.create_task(self.callback(sensor_data))
                
        except Exception as e:
            logger.error(f"Error processing sensor message: {e}")
    
    async def _start_mock_mode(self):
        """Run in mock mode for testing without MQTT."""
        logger.info("Starting mock sensor mode - generating simulated data")
        import asyncio
        
        mock_sensors = [
            {"sensor_id": "temp_factory_1", "type": "temperature", "value": 22.5, "unit": "celsius", "location": "factory_1"},
            {"sensor_id": "humidity_factory_1", "type": "humidity", "value": 65, "unit": "percent", "location": "factory_1"},
            {"sensor_id": "motion_entry", "type": "motion", "value": True, "unit": "boolean", "location": "entry_door"},
        ]
        
        while self.callback:
            import random
            sensor = random.choice(mock_sensors)
            
            # Add some variation to values
            if sensor["type"] == "temperature":
                sensor["value"] = round(20 + random.random() * 10, 1)
            elif sensor["type"] == "humidity":
                sensor["value"] = round(50 + random.random() * 30, 1)
            
            sensor["timestamp"] = datetime.utcnow().isoformat()
            
            await self.callback(sensor.copy())
            await asyncio.sleep(5)  # Emit mock data every 5 seconds
    
    async def stop_listening(self):
        """Stop listening to sensor topics."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        logger.info("Sensor listening stopped")


from datetime import datetime
import os
