"""
MCP Protocol - Model Context Protocol for agent communication
"""

import json
import os
from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    """MCP message types."""
    SENSOR_DATA = "sensor_data"
    ACTUATOR_COMMAND = "actuator_command"
    AGENT_QUERY = "agent_query"
    AGENT_RESPONSE = "agent_response"
    USER_COMMAND = "user_command"
    SYSTEM_STATUS = "system_status"
    ERROR = "error"


class MCPPProtocol:
    """
    Model Context Protocol implementation for IoT agent communication.
    
    This protocol defines how agents communicate with each other
    and with sensors/actuators across all layers.
    
    Message Format:
    {
        "version": "1.0",
        "type": "sensor_data|actuator_command|agent_query|...",
        "from": "agent_id",
        "to": "agent_id or * for broadcast",
        "timestamp": "ISO8601 timestamp",
        "payload": { ... },
        "context": { ... }
    }
    """
    
    VERSION = "1.0"
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.subscriptions: Dict[str, List[Callable]] = {}
    
    def create_message(
        self,
        msg_type: MessageType,
        payload: Dict[str, Any],
        to: str = "*",
        context: Dict[str, Any] = None
    ) -> str:
        """
        Create a MCP protocol message.
        
        Args:
            msg_type: Type of message
            payload: Message payload
            to: Destination agent ID or "*" for broadcast
            context: Optional context data
        
        Returns:
            JSON string message
        """
        message = {
            "version": self.VERSION,
            "type": msg_type.value,
            "from": self.agent_id,
            "to": to,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload
        }
        
        if context:
            message["context"] = context
        
        return json.dumps(message)
    
    def parse_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """
        Parse a raw MCP message.
        
        Args:
            raw_message: Raw JSON string
        
        Returns:
            Parsed message dict or None on error
        """
        try:
            message = json.loads(raw_message)
            
            # Validate required fields
            required = ["version", "type", "from", "timestamp", "payload"]
            if not all(field in message for field in required):
                return None
            
            # Check version compatibility
            if message["version"] != self.VERSION:
                logger.warning(f"Message version mismatch: {message['version']}")
            
            return message
            
        except json.JSONDecodeError:
            return None
    
    def is_for_me(self, message: Dict[str, Any]) -> bool:
        """Check if a message is addressed to this agent."""
        return message.get("to") == self.agent_id or message.get("to") == "*"
    
    def subscribe(self, msg_type: MessageType, callback: Callable):
        """Subscribe to a message type."""
        if msg_type.value not in self.subscriptions:
            self.subscriptions[msg_type.value] = []
        self.subscriptions[msg_type.value].append(callback)
    
    async def handle_message(self, raw_message: str) -> Optional[str]:
        """
        Handle an incoming message and optionally return a response.
        
        Args:
            raw_message: Raw JSON string message
        
        Returns:
            Optional response message as JSON string
        """
        message = self.parse_message(raw_message)
        if not message:
            return None
        
        # Check if message is for this agent
        if not self.is_for_me(message):
            return None
        
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        # Call registered callbacks
        if msg_type in self.subscriptions:
            for callback in self.subscriptions[msg_type]:
                result = await callback(payload, message.get("context"))
                if result:
                    return result
        
        return None


# MCP Transport implementations
class MCPTransport:
    """Base class for MCP transport layers."""
    
    async def connect(self):
        """Connect to the transport."""
        raise NotImplementedError
    
    async def disconnect(self):
        """Disconnect from the transport."""
        raise NotImplementedError
    
    async def publish(self, topic: str, message: str):
        """Publish a message to a topic."""
        raise NotImplementedError
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic."""
        raise NotImplementedError


class MQTTPTransport(MCPTransport):
    """MQTT transport for MCP protocol."""
    
    def __init__(self, broker_url: str, client_id: str):
        self.broker_url = broker_url
        self.client_id = client_id
        self._client = None
    
    async def connect(self):
        """Connect to MQTT broker."""
        import paho.mqtt.client as mqtt
        
        broker_host = self.broker_url.replace("mqtt://", "").split(":")[0]
        broker_port = int(self.broker_url.split(":")[-1]) if ":" in self.broker_url else 1883
        
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.connect(broker_host, broker_port, 60)
        self._client.loop_start()
    
    async def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
    
    async def publish(self, topic: str, message: str):
        """Publish message to MQTT topic."""
        if self._client:
            self._client.publish(topic, message, qos=1)
    
    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to MQTT topic."""
        def on_message(client, userdata, msg):
            asyncio.create_task(callback(msg.payload.decode()))
        
        if self._client:
            self._client.subscribe(topic)
            self._client.on_message = on_message


import asyncio
import logging

logger = logging.getLogger(__name__)
