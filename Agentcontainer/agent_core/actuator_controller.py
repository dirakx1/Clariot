"""
Actuator Controller - Sends commands to actuators via MQTT
"""

import json
import logging
import os
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ActuatorController:
    """
    Controls actuators by publishing commands to MQTT.
    
    Actuators subscribe to topics like:
    - actuators/motor/factory_floor_1
    - actuators/valve/warehouse_2
    - actuators/light/entry_door
    """
    
    def __init__(self, agent_id: str, mqtt_broker: str = None):
        self.agent_id = agent_id
        self.mqtt_broker = mqtt_broker or os.getenv("MQTT_BROKER", "mqtt://localhost:1883")
        self._client = None
        self._connected = False
        logger.info(f"ActuatorController initialized for agent {agent_id}")
    
    def _ensure_connection(self):
        """Ensure MQTT client is connected."""
        if self._connected:
            return
        
        try:
            import paho.mqtt.client as mqtt
            
            broker_host = self.mqtt_broker.replace("mqtt://", "").split(":")[0]
            broker_port = int(self.mqtt_broker.split(":")[-1]) if ":" in self.mqtt_broker else 1883
            
            self._client = mqtt.Client(client_id=f"clariot_actuator_{self.agent_id}")
            self._client.connect(broker_host, broker_port, 60)
            self._client.loop_start()
            self._connected = True
            logger.info(f"Connected to MQTT broker for actuator control")
        except Exception as e:
            logger.warning(f"Could not connect to MQTT for actuators: {e}")
            self._connected = False
    
    async def execute_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute a list of actions on actuators.
        
        Args:
            actions: List of action dicts like:
                [
                    {"actuator_id": "motor_1", "command": "start", "parameters": {"speed": 100}},
                    {"actuator_id": "valve_1", "command": "open", "parameters": {}}
                ]
        
        Returns:
            List of execution results
        """
        results = []
        
        for action in actions:
            result = await self._execute_single_action(action)
            results.append(result)
        
        return results
    
    async def _execute_single_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action on an actuator."""
        actuator_id = action.get("actuator_id")
        command = action.get("command")
        parameters = action.get("parameters", {})
        
        # Parse actuator_id to get type and location
        # Format: <type>_<location> e.g., motor_factory_1
        parts = actuator_id.rsplit("_", 1)
        if len(parts) == 2:
            actuator_type, location = parts
        else:
            actuator_type = actuator_id
            location = "default"
        
        topic = f"actuators/{actuator_type}/{location}"
        
        payload = {
            "command": command,
            "parameters": parameters,
            "agent_id": self.agent_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self._publish_command(topic, payload, actuator_id, command)
    
    async def _publish_command(
        self, 
        topic: str, 
        payload: Dict, 
        actuator_id: str, 
        command: str
    ) -> Dict[str, Any]:
        """Publish a command to an actuator topic."""
        try:
            self._ensure_connection()
            
            if self._client and self._connected:
                result = self._client.publish(
                    topic, 
                    json.dumps(payload),
                    qos=1
                )
                
                if result.rc == 0:
                    logger.info(f"Command '{command}' sent to {actuator_id}")
                    return {
                        "actuator_id": actuator_id,
                        "command": command,
                        "status": "sent",
                        "topic": topic
                    }
                else:
                    logger.error(f"Failed to send command to {actuator_id}")
                    return {
                        "actuator_id": actuator_id,
                        "command": command,
                        "status": "failed",
                        "error": f"MQTT error code: {result.rc}"
                    }
            else:
                # Mock mode
                logger.info(f"[MOCK] Command '{command}' would be sent to {actuator_id}")
                return {
                    "actuator_id": actuator_id,
                    "command": command,
                    "status": "mock",
                    "topic": topic,
                    "payload": payload
                }
                
        except Exception as e:
            logger.error(f"Error publishing to {actuator_id}: {e}")
            return {
                "actuator_id": actuator_id,
                "command": command,
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Close the MQTT connection."""
        if self._client and self._connected:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False


from datetime import datetime
