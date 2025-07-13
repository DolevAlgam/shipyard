"""
Summarizer Agent for Shipyard Interview System
Extracts key information from pillar conversations
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import SUMMARIZER_PROMPT
from utils.helpers import format_chat_history

class SummarizerAgent:
    """Agent responsible for extracting key information from conversations"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
    
    async def summarize_pillar(self, pillar_name: str, chat_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Summarize a pillar conversation to extract key information
        
        Args:
            pillar_name: Name of the pillar (profiler, business, app, tribal)
            chat_history: Chat history for the pillar
            
        Returns:
            Structured summary of key information
        """
        if not chat_history:
            return {}
        
        # Build system prompt
        system_prompt = self._build_system_prompt(pillar_name, chat_history)
        
        # Create input for summarizer
        chat_text = format_chat_history(chat_history)
        agent_input = f"Summarize the key information from this {pillar_name} conversation:\n\n{chat_text}"
        
        # Get summary from AI
        summary_response = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.3  # Lower temperature for more consistent summarization
        )
        
        # Parse response into structured format
        try:
            # Try to parse as JSON if possible
            summary = json.loads(summary_response)
        except json.JSONDecodeError:
            # If not JSON, create structured summary from text
            summary = self._parse_text_summary(summary_response, pillar_name)
        
        return summary
    
    def _build_system_prompt(self, pillar_name: str, chat_history: List[Dict[str, str]]) -> str:
        """Build system prompt for summarization"""
        context = {
            "pillar_name": pillar_name,
            "chat_history": format_chat_history(chat_history)
        }
        
        try:
            return SUMMARIZER_PROMPT.format(**context)
        except KeyError:
            return f"{SUMMARIZER_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    def _parse_text_summary(self, summary_text: str, pillar_name: str) -> Dict[str, Any]:
        """Parse text summary into structured format"""
        summary = {}
        
        # Split into lines and extract key-value pairs
        lines = summary_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                # Clean up key
                key = key.replace('-', '_').replace('(', '').replace(')', '')
                
                if value:
                    summary[key] = value
        
        # Add pillar-specific fallbacks if summary is empty
        if not summary:
            summary = {
                "pillar_completed": pillar_name,
                "information_gathered": "Basic information collected",
                "status": "completed"
            }
        
        return summary
    
    async def create_comprehensive_summary(self, state) -> Dict[str, Any]:
        """
        Create a comprehensive summary of all pillars
        
        Args:
            state: Current interview state
            
        Returns:
            Comprehensive summary of all collected information
        """
        comprehensive_summary = {
            "user_profile": self.state_manager.get_user_profile(),
            "pillar_summaries": self.state_manager.get_all_summaries(),
            "current_document": self.state_manager.get_current_document(),
            "interview_status": "completed"
        }
        
        return comprehensive_summary 