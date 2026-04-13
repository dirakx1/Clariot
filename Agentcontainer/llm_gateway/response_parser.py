"""
Response Parser - Parses LLM responses into structured data
"""

import json
import re
import logging

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses LLM text responses into structured JSON data."""
    
    def parse_json_response(self, text: str) -> dict:
        """
        Parse JSON from LLM response text.
        
        Handles various formats:
        - Raw JSON object
        - JSON inside ```json blocks
        - JSON inside ``` blocks
        - Text with JSON at end
        
        Args:
            text: LLM response text
        
        Returns:
            Parsed dict or empty dict on failure
        """
        if not text:
            return {}
        
        text = text.strip()
        
        # Try direct JSON parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from code blocks
        patterns = [
            r"```json\s*(\{.*?\})\s*```",
            r"```\s*(\{.*?\})\s*```",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # Try finding JSON object in text
        try:
            start = text.find("{")
            if start != -1:
                # Find matching closing brace
                depth = 0
                for i, c in enumerate(text[start:]):
                    if c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                    if depth == 0:
                        end = start + i + 1
                        return json.loads(text[start:end])
        except Exception:
            pass
        
        logger.warning(f"Could not parse JSON from response: {text[:100]}...")
        return {}
    
    def extract_actions(self, parsed_response: dict) -> list:
        """Extract action list from parsed response."""
        return parsed_response.get("actions", [])
    
    def extract_reasoning(self, parsed_response: dict) -> str:
        """Extract reasoning text from parsed response."""
        return parsed_response.get("reasoning", "")
    
    def extract_alert(self, parsed_response: dict) -> tuple:
        """Extract alert status and message."""
        return (
            parsed_response.get("alert", False),
            parsed_response.get("alert_message", "")
        )
