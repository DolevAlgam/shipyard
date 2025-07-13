"""
Shipyard Core Package
Contains core functionality for state management, OpenAI client, and prompts
"""

from .state_manager import StateManager
from .openai_client import OpenAIClient
from .prompts import AGENT_PROMPTS

__all__ = [
    'StateManager',
    'OpenAIClient',
    'AGENT_PROMPTS'
] 