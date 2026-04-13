"""
Clariot Agent Core - LLM-powered IoT agent with sensor/actuator control
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from .memory import AgentMemory
from .sensor_handler import SensorHandler
from .actuator_controller import ActuatorController

logger = logging.getLogger(__name__)


class ClariotAgent:
    """
    Main AI agent class that processes sensor data and controls actuators.
    
    Data flow: Sensor → process_sensor_data() → LLM reasoning → decide_action() → Actuator
    """
    
    def __init__(self, agent_id: str, layer: str, llm_gateway):
        self.agent_id = agent_id
        self.layer = layer
        self.llm_gateway = llm_gateway
        self.memory = AgentMemory(agent_id)
        self.sensor_handler = SensorHandler(agent_id)
        self.actuator_controller = ActuatorController(agent_id)
        self.is_running = False
        logger.info(f"Agent {agent_id} initialized for layer {layer}")
    
    async def process_sensor_data(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming sensor data through the agent pipeline.
        
        Args:
            sensor_data: Dict containing sensor readings
                {
                    "sensor_id": "temp_001",
                    "type": "temperature",
                    "value": 25.5,
                    "unit": "celsius",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "location": "factory_floor_1"
                }
        
        Returns:
            Agent response with decisions and actions
        """
        # Store sensor reading in memory
        self.memory.add_sensor_reading(sensor_data)
        
        # Build context from recent readings
        context = self.memory.get_recent_context(window_minutes=10)
        
        # Construct prompt for LLM
        prompt = self._build_reasoning_prompt(sensor_data, context)
        
        # Get LLM response
        llm_response = await self.llm_gateway.query(
            prompt=prompt,
            context={"agent_id": self.agent_id, "layer": self.layer}
        )
        
        # Parse actions from LLM response
        actions = self._parse_actions(llm_response)
        
        # Execute actions via actuators
        executed_actions = await self.actuator_controller.execute_actions(actions)
        
        # Store decision in memory
        self.memory.add_decision({
            "sensor_data": sensor_data,
            "llm_response": llm_response,
            "actions": executed_actions,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "agent_id": self.agent_id,
            "sensor_id": sensor_data.get("sensor_id"),
            "reasoning": llm_response,
            "actions": executed_actions,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _build_reasoning_prompt(self, sensor_data: Dict, context: List[Dict]) -> str:
        """Build prompt for LLM reasoning based on sensor data and history."""
        return f"""You are an AI agent controlling a {self.layer} layer in an IoT system.

CURRENT SENSOR DATA:
{json.dumps(sensor_data, indent=2)}

RECENT SENSOR HISTORY (last 10 minutes):
{json.dumps(context, indent=2)}

Your task:
1. Analyze the sensor data
2. Determine if any action is needed
3. If action is needed, specify the actuator and command

Respond in JSON format:
{{
    "reasoning": "Your analysis and reasoning",
    "action_needed": true/false,
    "actions": [
        {{
            "actuator_id": "actuator identifier",
            "command": "command to send",
            "parameters": {{}}
        }}
    ]
}}
"""
    
    def _parse_actions(self, llm_response: str) -> List[Dict]:
        """Parse actions from LLM response."""
        try:
            # Try to extract JSON from response
            if "```json" in llm_response:
                start = llm_response.find("```json") + 7
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            elif "{" in llm_response:
                start = llm_response.find("{")
                # Find matching closing brace
                depth = 0
                for i, c in enumerate(llm_response[start:]):
                    if c == "{": depth += 1
                    elif c == "}": depth -= 1
                    if depth == 0:
                        end = start + i + 1
                        break
                json_str = llm_response[start:end]
            else:
                return []
            
            parsed = json.loads(json_str)
            return parsed.get("actions", [])
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return []
    
    async def handle_user_command(self, command: str) -> Dict[str, Any]:
        """
        Handle natural language commands from users.
        
        Args:
            command: Natural language command (e.g., "What's the temperature in factory?")
        
        Returns:
            Response to the user
        """
        # Build prompt for user command
        current_state = self.memory.get_current_state()
        
        prompt = f"""You are an AI agent in a {self.layer} IoT layer.
        
Current system state:
{json.dumps(current_state, indent=2)}

User command: {command}

Respond helpfully with current readings and any actions taken.
"""
        
        response = await self.llm_gateway.query(prompt=prompt)
        
        return {
            "agent_id": self.agent_id,
            "command": command,
            "response": response,
            "current_state": current_state,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def start(self):
        """Start the agent's sensor listening and processing loop."""
        self.is_running = True
        await self.sensor_handler.start_listening(self.process_sensor_data)
    
    async def stop(self):
        """Stop the agent."""
        self.is_running = False
        await self.sensor_handler.stop_listening()
