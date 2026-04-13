"""
LLM Gateway - Connects to various LLM providers
"""

import os
import logging
from typing import Dict, Any, Optional
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser

logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Gateway for connecting to LLM providers (OpenAI, Anthropic, Ollama, etc.)
    
    Supports:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Ollama (local LLM)
    - Azure OpenAI
    """
    
    def __init__(self, provider: str = None, model: str = None, api_key: str = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai").lower()
        self.model = model or os.getenv("LLM_MODEL", "gpt-4")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
        
        logger.info(f"LLM Gateway initialized with provider={self.provider}, model={self.model}")
    
    async def query(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """
        Send a query to the LLM and return the response.
        
        Args:
            prompt: The prompt to send
            context: Additional context for the query
        
        Returns:
            LLM response as string
        """
        if self.provider == "openai":
            return await self._query_openai(prompt, context)
        elif self.provider == "anthropic":
            return await self._query_anthropic(prompt, context)
        elif self.provider == "ollama":
            return await self._query_ollama(prompt, context)
        else:
            logger.error(f"Unknown LLM provider: {self.provider}")
            return "Error: Unknown LLM provider"
    
    async def _query_openai(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Query OpenAI GPT models."""
        try:
            import openai
            
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [{"role": "user", "content": prompt}]
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error: OpenAI API error - {str(e)}"
    
    async def _query_anthropic(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Query Anthropic Claude models."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=self.api_key)
            
            response = client.messages.create(
                model=self.model or "claude-3-sonnet-20240229",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error: Anthropic API error - {str(e)}"
    
    async def _query_ollama(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Query local Ollama LLM."""
        try:
            import requests
            
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            
            response = requests.post(
                ollama_url,
                json={
                    "model": self.model or "llama2",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"Error: Ollama returned status {response.status_code}"
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error: Ollama error - {str(e)}"
