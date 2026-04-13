"""
Actuator Handler - Controls physical actuators based on commands
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
import threading

logger = logging.getLogger(__name__)


class Actuator:
    """Represents a single actuator with command execution capabilities."""
    
    def __init__(self, actuator_id: str, actuator_type: str, location: str):
        self.actuator_id = actuator_id
        self.type = actuator_type
        self.location = location
        self.state = "idle"
        self.last_command: Optional[Dict[str, Any]] = None
    
    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a command on the actuator.
        
        Override this method for actual hardware actuators.
        
        Args:
            command: Command to execute (e.g., "start", "stop", "set_position")
            parameters: Optional parameters for the command
        
        Returns:
            Result dict with status and details
        """
        raise NotImplementedError("Subclass must implement execute()")


class MockActuator(Actuator):
    """Mock actuator for testing and development."""
    
    def __init__(self, actuator_id: str, actuator_type: str, location: str):
        super().__init__(actuator_id, actuator_type, location)
        self._is_on = False
        self._position = 0  # 0-100 for servo-like actuators
        self._speed = 0  # For motors
    
    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute mock command."""
        import random
        
        parameters = parameters or {}
        self.last_command = {
            "command": command,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if command.lower() in ["on", "start", "enable"]:
            self._is_on = True
            self.state = "running"
            result = {"status": "success", "message": f"{self.actuator_id} started"}
        
        elif command.lower() in ["off", "stop", "disable"]:
            self._is_on = False
            self._speed = 0
            self.state = "stopped"
            result = {"status": "success", "message": f"{self.actuator_id} stopped"}
        
        elif command.lower() in ["speed", "set_speed"]:
            speed = parameters.get("speed", 50)
            self._speed = max(0, min(100, speed))
            self.state = "running"
            result = {"status": "success", "speed": self._speed}
        
        elif command.lower() in ["position", "set_position"]:
            position = parameters.get("position", 0)
            self._position = max(0, min(100, position))
            result = {"status": "success", "position": self._position}
        
        elif command.lower() == "status":
            result = {
                "status": "success",
                "is_on": self._is_on,
                "speed": self._speed,
                "position": self._position,
                "state": self.state
            }
        
        else:
            result = {"status": "error", "message": f"Unknown command: {command}"}
            self.state = "error"
        
        logger.info(f"Actuator {self.actuator_id}: {command} -> {result['status']}")
        return result


class MotorActuator(MockActuator):
    """Mock motor actuator."""
    
    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "motor", location)
        self._speed = 0
    
    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute motor-specific commands."""
        parameters = parameters or {}
        
        if command.lower() == "speed":
            return super().execute("speed", parameters)
        
        return super().execute(command, parameters)


class ValveActuator(MockActuator):
    """Mock valve actuator (0-100% open)."""
    
    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "valve", location)
        self._open_percent = 0
    
    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute valve-specific commands."""
        parameters = parameters or {}
        
        if command.lower() == "open":
            self._open_percent = parameters.get("percent", 100)
            self.state = "open"
            return {"status": "success", "open_percent": self._open_percent}
        
        elif command.lower() == "close":
            self._open_percent = 0
            self.state = "closed"
            return {"status": "success", "open_percent": self._open_percent}
        
        elif command.lower() == "set":
            percent = parameters.get("percent", 0)
            self._open_percent = max(0, min(100, percent))
            self.state = "partially_open" if 0 < self._open_percent < 100 else ("open" if self._open_percent == 100 else "closed")
            return {"status": "success", "open_percent": self._open_percent}
        
        return super().execute(command, parameters)


class RelayActuator(MockActuator):
    """Mock relay actuator (simple on/off)."""
    
    def __init__(self, actuator_id: str, location: str):
        super().__init__(actuator_id, "relay", location)
    
    def execute(self, command: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute relay-specific commands."""
        if command.lower() in ["on", "off", "toggle"]:
            return super().execute(command.lower() if command.lower() in ["on", "off"] else "toggle", parameters)
        return super().execute(command, parameters)


class ActuatorManager:
    """
    Manages multiple actuators and command execution.
    
    Handles:
    - Actuator registration
    - Command routing
    - State tracking
    """
    
    def __init__(self):
        self.actuators: Dict[str, Actuator] = {}
    
    def add_actuator(self, actuator: Actuator):
        """Register an actuator."""
        self.actuators[actuator.actuator_id] = actuator
        logger.info(f"Registered actuator: {actuator.actuator_id} ({actuator.type})")
    
    def remove_actuator(self, actuator_id: str):
        """Remove an actuator."""
        if actuator_id in self.actuators:
            del self.actuators[actuator_id]
            logger.info(f"Removed actuator: {actuator_id}")
    
    def get_actuator(self, actuator_id: str) -> Optional[Actuator]:
        """Get an actuator by ID."""
        return self.actuators.get(actuator_id)
    
    def list_actuators(self) -> Dict[str, Dict[str, Any]]:
        """List all registered actuators with their states."""
        return {
            actuator_id: {
                "type": actuator.type,
                "location": actuator.location,
                "state": actuator.state,
                "last_command": actuator.last_command
            }
            for actuator_id, actuator in self.actuators.items()
        }
    
    def execute_command(
        self, 
        actuator_id: str, 
        command: str, 
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a command on an actuator.
        
        Args:
            actuator_id: ID of the actuator
            command: Command string
            parameters: Optional parameters
        
        Returns:
            Result dict from actuator
        """
        actuator = self.actuators.get(actuator_id)
        
        if not actuator:
            return {"status": "error", "message": f"Unknown actuator: {actuator_id}"}
        
        try:
            return actuator.execute(command, parameters)
        except Exception as e:
            logger.error(f"Error executing command on {actuator_id}: {e}")
            return {"status": "error", "message": str(e)}
    
    def execute_batch(self, commands: list) -> list:
        """
        Execute multiple commands in batch.
        
        Args:
            commands: List of {"actuator_id": "...", "command": "...", "parameters": {...}}
        
        Returns:
            List of result dicts
        """
        results = []
        for cmd in commands:
            result = self.execute_command(
                cmd.get("actuator_id"),
                cmd.get("command"),
                cmd.get("parameters")
            )
            result["actuator_id"] = cmd.get("actuator_id")
            result["command"] = cmd.get("command")
            results.append(result)
        return results


# Factory for creating actuators from config
def create_actuators_from_config(config: Dict[str, Any]) -> ActuatorManager:
    """
    Create actuators from configuration dict.
    
    Args:
        config: Dict with actuator configurations
            {
                "actuators": [
                    {"id": "motor_1", "type": "motor", "location": "factory_1", ...},
                    ...
                ]
            }
    """
    manager = ActuatorManager()
    
    for actuator_config in config.get("actuators", []):
        actuator_type = actuator_config.get("type", "").lower()
        actuator_id = actuator_config.get("id")
        location = actuator_config.get("location", "default")
        
        # Create appropriate actuator type
        if actuator_type == "motor":
            actuator = MotorActuator(actuator_id, location)
        elif actuator_type == "valve":
            actuator = ValveActuator(actuator_id, location)
        elif actuator_type == "relay":
            actuator = RelayActuator(actuator_id, location)
        else:
            actuator = MockActuator(actuator_id, actuator_type, location)
        
        manager.add_actuator(actuator)
    
    return manager


if __name__ == "__main__":
    # Test with mock actuators
    logging.basicConfig(level=logging.INFO)
    
    manager = ActuatorManager()
    
    # Add some mock actuators
    manager.add_actuator(MotorActuator("motor_factory_1", "factory_floor_1"))
    manager.add_actuator(ValveActuator("valve_warehouse_1", "warehouse_1"))
    manager.add_actuator(RelayActuator("relay_entry_door", "entry_door"))
    
    # Test commands
    print("\n=== Actuator Commands ===")
    
    result = manager.execute_command("motor_factory_1", "start", {"speed": 75})
    print(f"motor_factory_1 start: {result}")
    
    result = manager.execute_command("valve_warehouse_1", "open", {"percent": 50})
    print(f"valve_warehouse_1 open 50%: {result}")
    
    result = manager.execute_command("relay_entry_door", "on")
    print(f"relay_entry_door on: {result}")
    
    print("\n=== All Actuators Status ===")
    for aid, info in manager.list_actuators().items():
        print(f"  {aid}: {info['state']}")
