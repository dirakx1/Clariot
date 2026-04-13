"""
Command Router - Receives actuator commands from agents via MQTT and executes them
"""

import os
import json
import logging
import time

import paho.mqtt.client as mqtt

from actuator import ActuatorManager, MotorActuator, ValveActuator, RelayActuator

logger = logging.getLogger(__name__)


class CommandRouter:
    """
    Routes actuator commands from agents to physical actuators.
    
    Data Flow:
    Agent -> MQTT (actuators/<type>/<location>) -> CommandRouter -> ActuatorManager -> Actuator
    """
    
    def __init__(self, mqtt_broker: str, actuator_manager: ActuatorManager, agent_id: str = None):
        self.mqtt_broker = mqtt_broker
        self.actuator_manager = actuator_manager
        self.agent_id = agent_id or os.getenv("AGENT_ID", "clariot_agent_1")
        self.is_running = False
        self._client = None
        self._connected = False
        
        # Parse broker URL
        self._broker_host = mqtt_broker.replace("mqtt://", "").split(":")[0]
        self._broker_port = int(mqtt_broker.split(":")[-1]) if ":" in mqtt_broker else 1883
        
        # Track subscription topics
        self._subscribed_topics = []
    
    def _connect(self):
        """Connect to MQTT broker."""
        try:
            self._client = mqtt.Client(
                client_id=f"clariot_router_{self.agent_id}",
                clean_session=True
            )
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message
            
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
            logger.info("MQTT command router connected")
            
            # Subscribe to actuator command topics
            for topic in self._subscribed_topics:
                client.subscribe(topic)
                logger.info(f"Subscribed to {topic}")
        else:
            logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected."""
        self._connected = False
        if rc != 0:
            logger.warning(f"MQTT disconnected unexpectedly (code {rc})")
    
    def _on_message(self, client, userdata, msg):
        """
        Handle incoming actuator command message.
        
        Expected message format:
        {
            "command": "start",
            "parameters": {"speed": 100},
            "agent_id": "clariot_agent_1"
        }
        """
        try:
            # Parse topic to get actuator type and location
            # Topic: actuators/<type>/<location>
            topic_parts = msg.topic.split("/")
            if len(topic_parts) >= 3:
                actuator_type = topic_parts[1]
                location = topic_parts[2]
            else:
                logger.warning(f"Invalid actuator topic: {msg.topic}")
                return
            
            # Parse payload
            try:
                payload = json.loads(msg.payload.decode())
            except json.JSONDecodeError:
                payload = {"command": msg.payload.decode()}
            
            command = payload.get("command", "")
            parameters = payload.get("parameters", {})
            
            # Construct actuator ID
            actuator_id = f"{actuator_type}_{location}"
            
            # Execute command
            logger.info(f"Routing command '{command}' to {actuator_id}")
            result = self.actuator_manager.execute_command(actuator_id, command, parameters)
            
            # Publish response to agent response topic
            response_topic = f"agent/responses/{actuator_id}"
            response_payload = {
                "actuator_id": actuator_id,
                "command": command,
                "result": result,
                "timestamp": time.time()
            }
            self._client.publish(response_topic, json.dumps(response_payload), qos=1)
            
        except Exception as e:
            logger.error(f"Error handling command message: {e}")
    
    def subscribe_to_commands(self, topic: str):
        """Subscribe to a specific command topic."""
        self._subscribed_topics.append(topic)
        
        if self._connected and self._client:
            self._client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
    
    def start(self):
        """Start the command router."""
        if self.is_running:
            return
        
        # Subscribe to all actuator command topics
        self.subscribe_to_commands("actuators/+/+")
        self.subscribe_to_commands("agent/commands")
        
        self._connect()
        self.is_running = True
        
        logger.info("Command router started")
    
    def stop(self):
        """Stop the command router."""
        self.is_running = False
        
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
        
        self._connected = False
        logger.info("Command router stopped")


def main():
    """Run the command router service."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration from environment
    mqtt_broker = os.getenv("MQTT_BROKER", "mqtt://localhost:1883")
    agent_id = os.getenv("AGENT_ID", "clariot_agent_1")
    
    # Create actuator manager
    actuator_mgr = ActuatorManager()
    
    # Register actuators
    actuator_mgr.add_actuator(MotorActuator("motor_factory_1", "factory_floor_1"))
    actuator_mgr.add_actuator(ValveActuator("valve_warehouse_1", "warehouse_1"))
    actuator_mgr.add_actuator(RelayActuator("relay_entry_door", "entry_door"))
    
    # Create and start command router
    router = CommandRouter(mqtt_broker, actuator_mgr, agent_id)
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        router.stop()
        exit(0)
    
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    router.start()
    
    # Keep running
    logger.info("Command router running. Press Ctrl+C to stop.")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
