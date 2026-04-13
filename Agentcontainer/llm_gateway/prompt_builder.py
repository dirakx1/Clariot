"""
Prompt Builder - Constructs prompts from sensor data for LLM reasoning
"""

import json
from typing import Dict, List, Any


class PromptBuilder:
    """Builds structured prompts for LLM reasoning about IoT data."""
    
    SYSTEM_PROMPT = """You are an AI agent controlling an IoT system with sensors and actuators.

Your role:
- Analyze sensor data in real-time
- Make decisions based on the data and user goals
- Control actuators to take physical actions
- Report status and alerts to users

You have access to:
- Various sensors (temperature, humidity, motion, pressure, etc.)
- Various actuators (motors, valves, lights, displays, etc.)
- User commands and preferences
- Historical sensor data for context

Always respond with valid JSON that can be parsed programmatically."""

    
    def build_sensor_analysis_prompt(
        self, 
        sensor_data: Dict[str, Any], 
        context: List[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for analyzing a single sensor reading.
        
        Args:
            sensor_data: Current sensor reading
            context: List of recent sensor readings for context
        """
        context_str = ""
        if context:
            context_str = f"\nRECENT HISTORY:\n{json.dumps(context, indent=2)}"
        
        return f"""{self.SYSTEM_PROMPT}

CURRENT SENSOR READING:
{json.dumps(sensor_data, indent=2)}{context_str}

Analyze this sensor reading and determine if any action is needed.

Respond with JSON:
{{
    "reasoning": "Your analysis of the sensor data",
    "alert": true/false,
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

    def build_control_prompt(
        self, 
        user_command: str, 
        current_state: Dict[str, Any],
        recent_events: List[Dict[str, Any]] = None
    ) -> str:
        """
        Build prompt for processing a user control command.
        
        Args:
            user_command: Natural language command from user
            current_state: Current state of all sensors
            recent_events: Recent decisions and actions taken
        """
        events_str = ""
        if recent_events:
            events_str = f"\nRECENT EVENTS:\n{json.dumps(recent_events, indent=2)}"
        
        return f"""{self.SYSTEM_PROMPT}

USER COMMAND: {user_command}

CURRENT SYSTEM STATE:
{json.dumps(current_state, indent=2)}{events_str}

Process this user command and take appropriate actions.

Respond with JSON:
{{
    "response": "Your response to the user",
    "actions": [
        {{
            "actuator_id": "actuator identifier",
            "command": "command to send",
            "parameters": {{}}
        }}
    ],
    "status_update": "Brief status update for the user"
}}
"""
