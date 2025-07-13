"""
OpenAI Client for Shipyard Interview System
Handles all OpenAI API interactions using the Chat Completions API
"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
import time

class OpenAIClient:
    """OpenAI API client for agent interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key. If not provided, will use OPENAI_API_KEY env var
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
        self.default_temperature = 0.7
        self.default_max_tokens = 1000
        
    async def call_agent(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call OpenAI Chat Completions API with natural conversation flow
        
        Args:
            system_prompt: Agent's system prompt (includes state context)
            user_message: Current user input
            chat_history: Chat history for THIS agent/pillar only
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Agent's response content
        """
        try:
            # Build messages object - always start with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if this agent has previous conversations
            if chat_history:
                messages.extend(chat_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            # Return a graceful fallback
            return f"I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    def call_agent_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Synchronous version of call_agent for when async is not needed
        
        Args:
            system_prompt: Agent's system prompt (includes state context)
            user_message: Current user input
            chat_history: Chat history for THIS agent/pillar only
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Agent's response content
        """
        try:
            # Build messages object
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history)
            
            messages.append({"role": "user", "content": user_message})
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return f"I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello, this is a test."}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"OpenAI API connection test failed: {str(e)}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            print(f"Error fetching models: {str(e)}")
            return []
    
    def set_model(self, model: str):
        """Set the model to use for API calls"""
        self.model = model
    
    def set_default_temperature(self, temperature: float):
        """Set default temperature for API calls"""
        self.default_temperature = temperature
    
    def set_default_max_tokens(self, max_tokens: int):
        """Set default max tokens for API calls"""
        self.default_max_tokens = max_tokens 