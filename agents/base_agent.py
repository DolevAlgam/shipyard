from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from config.reasoning_config import (
    get_agent_config, 
    get_operation_config, 
    is_reasoning_model,
    REASONING_AGENT_CONFIG,
    OPERATION_MODE_CONFIG
)
from core.openai_client import ReasoningResponse

class BaseAgent(ABC):
    def __init__(self, name: str, topics: List[str], prompt: str):
        self.name = name
        self.topics = topics
        self.prompt = prompt
        
        # Get reasoning configuration for this agent
        self.reasoning_config = get_agent_config(self.__class__.__name__)
        self.model = self.reasoning_config.get('model', 'gpt-4o')
        self.effort = self.reasoning_config.get('effort')
        self.reasoning_summary = self.reasoning_config.get('reasoning_summary')
        
        # Initialize reasoning summaries storage
        self._reasoning_summaries = []
    
    # Keep the existing abstract method that agents actually implement
    @abstractmethod
    async def process_topic(self, topic: str, state: Dict, openai_client) -> Dict:
        """Process a single topic using LLM-based analysis"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model configuration for this agent"""
        return {
            'agent_name': self.__class__.__name__,
            'model': self.model,
            'effort': self.effort,
            'reasoning_summary': self.reasoning_summary,
            'is_reasoning_model': is_reasoning_model(self.model),
            'description': self.reasoning_config.get('description', 'No description available')
        }
    
    def supports_reasoning(self) -> bool:
        """Check if this agent uses reasoning models"""
        return is_reasoning_model(self.model)
    
    async def get_response(
        self, 
        system_prompt: str, 
        user_message: str, 
        openai_client, 
        operation_mode: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Get response from OpenAI using agent's configured model and settings
        Handles both reasoning and non-reasoning models transparently
        
        Args:
            system_prompt: System prompt for the request
            user_message: User message
            openai_client: OpenAI client instance
            operation_mode: Optional operation mode override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            chat_history: Optional chat history
            
        Returns:
            Response content as string (extracted from ReasoningResponse if needed)
        """
        # Get operation-specific config if provided
        if operation_mode:
            op_config = get_operation_config(operation_mode)
            model = op_config.get('model', self.model)
            effort = op_config.get('effort', self.effort)
            reasoning_summary = op_config.get('reasoning_summary', self.reasoning_summary)
        else:
            model = self.model
            effort = self.effort
            reasoning_summary = self.reasoning_summary
        
        # Call OpenAI with appropriate parameters
        response = await openai_client.call_agent(
            system_prompt=system_prompt,
            user_message=user_message,
            chat_history=chat_history,
            model=model,
            effort=effort,
            reasoning_summary=reasoning_summary,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_name=self.__class__.__name__,
            conversation_id=getattr(self, '_conversation_id', None)
        )
        
        # Extract content from ReasoningResponse or return string directly
        if isinstance(response, ReasoningResponse):
            # Store reasoning summary if available for potential later use
            if hasattr(self, '_reasoning_summaries'):
                self._reasoning_summaries.append({
                    'timestamp': __import__('time').time(),
                    'operation_mode': operation_mode,
                    'reasoning_summary': response.reasoning_summary,
                    'reasoning_tokens': response.reasoning_tokens
                })
            return response.content
        else:
            # Legacy string response from GPT-4o
            return response
    
    def set_conversation_id(self, conversation_id: str):
        """Set conversation ID for reasoning context tracking"""
        self._conversation_id = conversation_id
        
    def get_reasoning_summaries(self) -> List[Dict[str, Any]]:
        """Get stored reasoning summaries for this agent"""
        return getattr(self, '_reasoning_summaries', [])
    
    def clear_reasoning_summaries(self):
        """Clear stored reasoning summaries"""
        self._reasoning_summaries = [] 