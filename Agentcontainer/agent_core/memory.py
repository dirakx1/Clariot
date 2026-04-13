"""
Agent Memory - Short and long-term memory for IoT agent context
"""

import json
import os
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any, Optional


class AgentMemory:
    """Manages short and long-term memory for agent context."""
    
    def __init__(self, agent_id: str, memory_dir: str = "/app/data/memory"):
        self.agent_id = agent_id
        self.memory_dir = memory_dir
        os.makedirs(memory_dir, exist_ok=True)
        
        # Short-term memory (deque, last 100 readings)
        self.short_term = deque(maxlen=100)
        
        # Long-term memory (file-based, last 24 hours)
        self.long_term_file = os.path.join(memory_dir, f"{agent_id}_memory.jsonl")
        self._load_long_term()
    
    def _load_long_term(self):
        """Load recent long-term memories from disk."""
        self.long_term = deque(maxlen=1000)  # Last 1000 entries
        if os.path.exists(self.long_term_file):
            try:
                with open(self.long_term_file, 'r') as f:
                    cutoff = datetime.utcnow() - timedelta(hours=24)
                    for line in f:
                        entry = json.loads(line.strip())
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time > cutoff:
                            self.long_term.append(entry)
            except Exception:
                pass
    
    def add_sensor_reading(self, reading: Dict[str, Any]):
        """Add a sensor reading to memory."""
        entry = {
            "type": "sensor",
            "data": reading,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.short_term.append(entry)
        self._persist_to_long_term(entry)
    
    def add_decision(self, decision: Dict[str, Any]):
        """Add an agent decision to memory."""
        entry = {
            "type": "decision",
            "data": decision,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.short_term.append(entry)
        self._persist_to_long_term(entry)
    
    def _persist_to_long_term(self, entry: Dict):
        """Write entry to long-term storage."""
        try:
            with open(self.long_term_file, 'a') as f:
                f.write(json.dumps(entry) + "\n")
            self.long_term.append(entry)
        except Exception:
            pass
    
    def get_recent_context(self, window_minutes: int = 10) -> List[Dict]:
        """Get sensor readings from the last N minutes."""
        cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
        context = []
        
        # First check short-term
        for entry in self.short_term:
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time > cutoff:
                context.append(entry)
        
        # Then check long-term if needed
        if len(context) < 10:
            for entry in self.long_term:
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time > cutoff and entry not in context:
                    context.append(entry)
        
        return context[-10:]  # Return last 10 entries
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get the current state of all known sensors."""
        state = {}
        
        # Get most recent reading per sensor from short-term
        for entry in reversed(self.short_term):
            if entry['type'] == 'sensor':
                sensor_id = entry['data'].get('sensor_id')
                if sensor_id:
                    state[sensor_id] = entry['data']
        
        return state
