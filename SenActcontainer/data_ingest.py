"""
Data Ingest Service - Publishes sensor readings to MQTT
"""

import os
import json
import logging
import time
from datetime import datetime
import threading

import paho.mqtt.client as mqtt

from sensor import SensorManager, TemperatureSensor, HumiditySensor, MotionSensor, PressureSensor

logger = logging.getLogger(__name__)


class DataIngestService:
    """
    Collects sensor readings and publishes them to MQTT.
    
    Data Flow:
    Sensor -> SensorManager -> DataIngestService -> MQTT Broker -> Agent
    """
    
    def __init__(self, mqtt_broker: str, sensor_manager: SensorManager, agent_id: str = None):
        self.mqtt_broker = mqtt_broker
        self.sensor_manager = sensor_manager
        self.agent_id = agent_id or os.getenv("AGENT_ID", "clariot_agent_1")
        self.is_running = False
        self._client = None
        self._thread = None
        self._connected = False
        
        # Parse broker URL
        self._broker_host = mqtt_broker.replace("mqtt://", "").split(":")[0]
        self._broker_port = int(mqtt_broker.split(":")[-1]) if ":" in mqtt_broker else 1883
    
    def _connect(self):
        """Connect to MQTT broker."""
        try:
            self._client = mqtt.Client(
                client_id=f"clariot_ingest_{self.agent_id}",
                clean_session=True
            )
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            
            self._client.connect(self._broker_host, self._broker_port, 60)
            self._client.loop_start()
            
            # Wait for connection
            timeout = 5
            start = time.time()
            while not self._connected and time.time() - start < timeout:
                time.sleep(0.1)
            
            if self._connected:
                logger.info(f"Connected to MQTT broker at {self.mqtt_broker}")
            else:
                logger.warning("Could not connect to MQTT broker")
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected."""
        if rc == 0:
            self._connected = True
            logger.info("MQTT ingest connected")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected."""
        self._connected = False
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly (code {rc})")
    
    def _publish_reading(self, readings: dict):
        """Publish sensor readings to MQTT topics."""
        if not self._connected:
            return
        
        for sensor_id, reading in readings.items():
            # Topic format: sensors/<type>/<location>
            topic = f"sensors/{reading['type']}/{reading['location']}"
            
            try:
                payload = json.dumps(reading)
                result = self._client.publish(topic, payload, qos=1)
                
                if result.rc == 0:
                    logger.debug(f"Published {sensor_id} to {topic}")
                else:
                    logger.warning(f"Failed to publish {sensor_id}")
                    
            except Exception as e:
                logger.error(f"Error publishing {sensor_id}: {e}")
    
    def start(self):
        """Start the ingest service."""
        if self.is_running:
            return
        
        self._connect()
        self.is_running = True
        
        # Start sensor polling with publish callback
        self.sensor_manager.start_polling(self._publish_reading)
        
        logger.info("Data ingest service started")
    
    def stop(self):
        """Stop the ingest service."""
        self.is_running = False
        self.sensor_manager.stop_polling()
        
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        
        self._connected = False
        logger.info("Data ingest service stopped")


def main():
    """Run the data ingest service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration from environment
    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://localhost:1883")
    sensor_interval = int(os.getenv("SENSOR_INTERVAL", "1000"))
    agent_id = os.getenv("AGENT_ID", "clariot_agent_1")
    
    # Create sensor manager
    sensor_mgr = SensorManager(interval_ms=sensor_interval)
    
    # Register sensors
    sensor_mgr.add_sensor(TemperatureSensor("temp_factory_1", "factory_floor_1"))
    sensor_mgr.add_sensor(HumiditySensor("humidity_factory_1", "factory_floor_1"))
    sensor_mgr.add_sensor(MotionSensor("motion_entry", "entry_door"))
    sensor_mgr.add_sensor(PressureSensor("pressure_factory_1", "factory_floor_1"))
    
    # Create and start ingest service
    ingest = DataIngestService(mqtt_broker, sensor_mgr, agent_id)
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        ingest.stop()
        exit(0)
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    ingest.start()
    
    # Keep running
    logger.info("Data ingest running. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
