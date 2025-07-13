"""
OpenAI Client for Shipyard Interview System
Handles all OpenAI API interactions using the Chat Completions API
Now supports o3 reasoning models with enhanced capabilities and reasoning summary storage
"""

import os
import json
import uuid
from typing import List, Dict, Any, Optional, Union, Tuple
from openai import OpenAI
import time
from dataclasses import dataclass

@dataclass
class ReasoningResponse:
    """Container for o3 reasoning model responses with reasoning content"""
    content: str
    reasoning_summary: Optional[str] = None
    reasoning_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    model_used: Optional[str] = None
    reasoning_effort: Optional[str] = None

class ReasoningTokenTracker:
    """Track reasoning tokens and costs for o3 models"""
    
    def __init__(self):
        self.reasoning_tokens = 0
        self.completion_tokens = 0
        self.total_calls = 0
        self.reasoning_model_calls = 0
        
    def track_usage(self, response):
        """Track token usage from OpenAI response"""
        self.total_calls += 1
        
        if hasattr(response, 'usage'):
            usage = response.usage
            
            # Track reasoning tokens if available (o3 models)
            if hasattr(usage, 'reasoning_tokens') and usage.reasoning_tokens:
                self.reasoning_tokens += usage.reasoning_tokens
                self.reasoning_model_calls += 1
            
            # Track completion tokens
            if hasattr(usage, 'completion_tokens'):
                self.completion_tokens += usage.completion_tokens
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics"""
        return {
            'total_calls': self.total_calls,
            'reasoning_model_calls': self.reasoning_model_calls,
            'reasoning_tokens': self.reasoning_tokens,
            'completion_tokens': self.completion_tokens
        }

class OpenAIClient:
    """OpenAI API client for agent interactions with o3 reasoning model support"""
    
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
        
        # o3 reasoning model configuration
        self.reasoning_models = ['o3', 'o3-mini', 'o4-mini']
        self.legacy_models = ['gpt-4o', 'gpt-4o-mini']
        
        # Token tracking
        self.token_tracker = ReasoningTokenTracker()
        
        # Reasoning summary storage
        self.reasoning_storage = []
        
    async def call_agent(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        # o3 reasoning parameters
        effort: Optional[str] = None,
        reasoning_summary: Optional[str] = None,
        # Context for reasoning storage
        agent_name: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Union[str, ReasoningResponse]:
        """
        Call OpenAI API with support for both reasoning models (Responses API) and GPT models (Chat Completions API)
        
        Args:
            system_prompt: Agent's system prompt (includes state context)
            user_message: Current user input
            chat_history: Chat history for THIS agent/pillar only
            temperature: Override default temperature
            max_tokens: Override default max tokens
            model: Override default model
            effort: Reasoning effort level for o3 models ('low', 'medium', 'high')
            reasoning_summary: Reasoning summary type for o3 models ('auto', 'detailed')
            agent_name: Name of agent for reasoning context storage
            conversation_id: Conversation ID for reasoning context storage
            
        Returns:
            Agent's response content (str for legacy models, ReasoningResponse for o3 models)
        """
        try:
            # Use provided model or default
            selected_model = model or self.model
            
            # Check if this is a reasoning model
            from config.reasoning_config import is_reasoning_model
            is_reasoning = is_reasoning_model(selected_model)
            
            if is_reasoning:
                # Use Responses API for O3 reasoning models
                conversation = []
                
                # Add chat history if provided
                if chat_history:
                    for msg in chat_history:
                        conversation.append({
                            "role": msg["role"],
                            "type": "message", 
                            "content": msg["content"]
                        })
                
                # Add system message (converted to developer message for reasoning models)
                conversation.append({
                    "role": "developer",
                    "type": "message",
                    "content": system_prompt
                })
                
                # Add user message
                conversation.append({
                    "role": "user", 
                    "type": "message",
                    "content": user_message
                })
                
                # Get effort level - use provided or determine from model/config
                reasoning_effort = effort or "medium"
                if not effort:
                    if "o3-mini" in selected_model:
                        reasoning_effort = "low" 
                    elif "o3" in selected_model and "mini" not in selected_model:
                        reasoning_effort = "high"
                
                # Get reasoning summary setting
                summary_type = reasoning_summary or "auto"
                
                # Make API call using Responses API
                response = self.client.responses.create(
                    model=selected_model,
                    input=conversation,
                    reasoning={"effort": reasoning_effort, "summary": summary_type}
                )
                
                # Extract content and reasoning
                content = response.output_text or ""
                reasoning_summary_text = None
                reasoning_tokens = 0
                
                # Look for reasoning items in output
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'reasoning':
                        if hasattr(item, 'summary') and item.summary:
                            reasoning_summary_text = item.summary[0].text if item.summary else None
                        break
                
                # Extract token usage
                if hasattr(response, 'usage'):
                    if hasattr(response.usage, 'output_tokens_details') and hasattr(response.usage.output_tokens_details, 'reasoning_tokens'):
                        reasoning_tokens = response.usage.output_tokens_details.reasoning_tokens
                
                # Create reasoning response
                reasoning_response = ReasoningResponse(
                    content=content,
                    reasoning_summary=reasoning_summary_text,
                    reasoning_tokens=reasoning_tokens,
                    model_used=selected_model,
                    reasoning_effort=reasoning_effort
                )
                
                # Store reasoning summary for future context
                if reasoning_summary_text:
                    context = {
                        'agent_name': agent_name,
                        'conversation_id': conversation_id,
                        'user_message_preview': user_message[:100] + "..." if len(user_message) > 100 else user_message
                    }
                    self.store_reasoning_summary(reasoning_response, context)
                
                return reasoning_response
            else:
                # Use Chat Completions API for GPT models
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add chat history if this agent has previous conversations
                if chat_history:
                    messages.extend(chat_history)
                
                # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                # Make API call using Chat Completions API
                response = self.client.chat.completions.create(
                    model=selected_model,
                    messages=messages,
                    temperature=temperature or self.default_temperature,
                    max_tokens=max_tokens or self.default_max_tokens
                )
                
                # Track token usage
                self.token_tracker.track_usage(response)
                
                return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            # Return a graceful fallback
            fallback_message = f"I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a moment."
            
            # Use provided model or default to determine response type
            selected_model = model or self.model
            if selected_model in self.reasoning_models:
                return ReasoningResponse(content=fallback_message, model_used=selected_model)
            else:
                return fallback_message
    
    async def create_reasoning_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = 'o3', 
        effort: str = 'high', 
        reasoning_summary: str = 'auto',
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Create completion specifically for o3 reasoning models
        
        Args:
            messages: List of message dictionaries
            model: Reasoning model to use ('o3', 'o3-mini', 'o4-mini')
            effort: Reasoning effort level ('low', 'medium', 'high')
            reasoning_summary: Summary type ('auto', 'detailed')
            temperature: Temperature override
            max_tokens: Max tokens override
            **kwargs: Additional parameters
            
        Returns:
            OpenAI response object
        """
        try:
            if model in self.reasoning_models:
                # o3 reasoning model call
                call_params = {
                    "model": model,
                    "messages": messages,
                    "reasoning": {
                        "effort": effort,
                        "summary": reasoning_summary
                    },
                    "temperature": temperature or self.default_temperature,
                    "max_tokens": max_tokens or self.default_max_tokens,
                    **kwargs
                }
            else:
                # Fallback to standard completion for non-reasoning models
                call_params = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature or self.default_temperature,
                    "max_tokens": max_tokens or self.default_max_tokens,
                    **kwargs
                }
            
            response = self.client.chat.completions.create(**call_params)
            
            # Track token usage
            self.token_tracker.track_usage(response)
            
            return response
            
        except Exception as e:
            print(f"Error in reasoning completion: {str(e)}")
            # Fallback to standard GPT-4o call
            return await self.call_agent(
                system_prompt=messages[0]["content"] if messages else "",
                user_message=messages[-1]["content"] if messages else "",
                chat_history=messages[1:-1] if len(messages) > 2 else [],
                model="gpt-4o"
            )
    
    def call_agent_sync(
        self, 
        system_prompt: str, 
        user_message: str, 
        chat_history: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        effort: Optional[str] = None,
        reasoning_summary: Optional[str] = None
    ) -> str:
        """
        Synchronous version of call_agent with o3 support
        
        Args:
            system_prompt: Agent's system prompt (includes state context)
            user_message: Current user input
            chat_history: Chat history for THIS agent/pillar only
            temperature: Override default temperature
            max_tokens: Override default max tokens
            model: Override default model
            effort: Reasoning effort level for o3 models
            reasoning_summary: Reasoning summary type for o3 models
            
        Returns:
            Agent's response content
        """
        try:
            # Use provided model or default
            selected_model = model or self.model
            
            # Build messages object
            messages = [{"role": "system", "content": system_prompt}]
            
            if chat_history:
                messages.extend(chat_history)
            
            messages.append({"role": "user", "content": user_message})
            
            # Prepare API call parameters
            call_params = {
                "model": selected_model,
                "messages": messages,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens or self.default_max_tokens
            }
            
            # Add reasoning parameters for o3 models
            if selected_model in self.reasoning_models and (effort or reasoning_summary):
                reasoning_config = {}
                if effort:
                    reasoning_config['effort'] = effort
                if reasoning_summary:
                    reasoning_config['summary'] = reasoning_summary
                
                call_params['reasoning'] = reasoning_config
            
            # Make API call
            response = self.client.chat.completions.create(**call_params)
            
            # Track token usage
            self.token_tracker.track_usage(response)
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            return f"I apologize, but I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    def is_reasoning_model(self, model: str) -> bool:
        """Check if model supports reasoning capabilities"""
        return model in self.reasoning_models
    
    def get_token_stats(self) -> Dict[str, int]:
        """Get token usage statistics"""
        return self.token_tracker.get_stats()
    
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

    def extract_reasoning_content(self, response, model: str, effort: Optional[str] = None) -> ReasoningResponse:
        """Extract reasoning content from o3 response"""
        reasoning_response = ReasoningResponse(
            content=response.choices[0].message.content,
            model_used=model,
            reasoning_effort=effort
        )
        
        # Extract reasoning information if available
        if hasattr(response, 'usage'):
            usage = response.usage
            if hasattr(usage, 'reasoning_tokens'):
                reasoning_response.reasoning_tokens = usage.reasoning_tokens
            if hasattr(usage, 'completion_tokens'):
                reasoning_response.completion_tokens = usage.completion_tokens
        
        # Extract reasoning summary if available
        # Note: This depends on the actual o3 API response structure
        if hasattr(response.choices[0], 'reasoning'):
            reasoning_response.reasoning_summary = response.choices[0].reasoning
        elif hasattr(response.choices[0].message, 'reasoning'):
            reasoning_response.reasoning_summary = response.choices[0].message.reasoning
        
        return reasoning_response
    
    def store_reasoning_summary(self, reasoning_response: ReasoningResponse, context: Dict[str, Any] = None):
        """Store reasoning summary for potential use in follow-ups or context passing"""
        storage_entry = {
            'timestamp': time.time(),
            'reasoning_summary': reasoning_response.reasoning_summary,
            'model': reasoning_response.model_used,
            'effort': reasoning_response.reasoning_effort,
            'reasoning_tokens': reasoning_response.reasoning_tokens,
            'content_preview': reasoning_response.content[:500] + "..." if len(reasoning_response.content) > 500 else reasoning_response.content,
            'context': context or {}
        }
        
        self.reasoning_storage.append(storage_entry)
        
        # Keep only last 10 reasoning summaries to prevent memory bloat
        if len(self.reasoning_storage) > 10:
            self.reasoning_storage = self.reasoning_storage[-10:]
    
    def get_recent_reasoning_context(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent reasoning summaries for context in follow-ups"""
        return self.reasoning_storage[-limit:] if self.reasoning_storage else [] 