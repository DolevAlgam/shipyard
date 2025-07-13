"""
State Manager for Shipyard Interview System
Manages the state structure including chat history, summaries, and current document
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

@dataclass
class UserProfile:
    """User profile information"""
    expertise_level: Optional[str] = None  # "novice", "intermediate", "advanced"
    project_description: Optional[str] = None
    gauged_complexity: Optional[str] = None  # Our assessment based on responses

@dataclass
class InterviewState:
    """Complete interview state"""
    chat_history: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)

class StateManager:
    """Manages the interview state and data flow"""
    
    def __init__(self):
        self.state: Optional[InterviewState] = None
    
    def initialize_state(self) -> InterviewState:
        """Initialize a new interview state"""
        self.state = InterviewState()
        
        # Initialize state structure
        self.state.state = {
            "user_profile": {
                "expertise_level": None,
                "project_description": None,
                "gauged_complexity": None,
            },
            "current_document": {},
            "all_conversations": [],
            "follow_up_counts": {}
        }
        
        # Initialize summaries for each pillar
        self.state.summaries = {
            "profiler": {},
            "business": {},
            "app": {},
            "tribal": {}
        }
        
        return self.state
    
    def get_chat_history(self, pillar_name: str) -> List[Dict[str, str]]:
        """Get chat history for a specific pillar"""
        if not self.state:
            return []
        
        if pillar_name not in self.state.chat_history:
            self.state.chat_history[pillar_name] = []
        
        return self.state.chat_history[pillar_name]
    
    def add_to_chat_history(self, pillar_name: str, role: str, content: str):
        """Add a message to the chat history for a specific pillar"""
        if not self.state:
            raise ValueError("State not initialized")
        
        if pillar_name not in self.state.chat_history:
            self.state.chat_history[pillar_name] = []
        
        self.state.chat_history[pillar_name].append({
            "role": role,
            "content": content
        })
        
        # Also add to all_conversations for debugging
        self.state.state["all_conversations"].append({
            "agent": pillar_name,
            "role": role,
            "content": content
        })
    
    def update_user_profile(self, updates: Dict[str, Any]):
        """Update user profile information"""
        if not self.state:
            raise ValueError("State not initialized")
        
        self.state.state["user_profile"].update(updates)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        if not self.state:
            return {}
        
        return self.state.state["user_profile"]
    
    def set_pillar_summary(self, pillar_name: str, summary: Dict[str, Any]):
        """Set the summary for a completed pillar"""
        if not self.state:
            raise ValueError("State not initialized")
        
        self.state.summaries[pillar_name] = summary
    
    def get_pillar_summary(self, pillar_name: str) -> Dict[str, Any]:
        """Get summary for a specific pillar"""
        if not self.state:
            return {}
        
        return self.state.summaries.get(pillar_name, {})
    
    def get_all_summaries(self) -> Dict[str, Dict[str, Any]]:
        """Get all pillar summaries"""
        if not self.state:
            return {}
        
        return self.state.summaries
    
    def update_current_document(self, section: str, content: str):
        """Update a section of the current document"""
        if not self.state:
            raise ValueError("State not initialized")
        
        self.state.state["current_document"][section] = content
    
    def get_current_document(self) -> Dict[str, str]:
        """Get the current document sections"""
        if not self.state:
            return {}
        
        return self.state.state["current_document"]
    
    def increment_follow_up_count(self, pillar_name: str, topic: str) -> int:
        """Increment follow-up count for a topic and return new count"""
        if not self.state:
            raise ValueError("State not initialized")
        
        key = f"{pillar_name}.{topic}"
        current_count = self.state.state["follow_up_counts"].get(key, 0)
        new_count = current_count + 1
        self.state.state["follow_up_counts"][key] = new_count
        
        return new_count
    
    def get_follow_up_count(self, pillar_name: str, topic: str) -> int:
        """Get current follow-up count for a topic"""
        if not self.state:
            return 0
        
        key = f"{pillar_name}.{topic}"
        return self.state.state["follow_up_counts"].get(key, 0)
    
    def build_system_prompt_context(self, pillar_name: str) -> Dict[str, Any]:
        """Build context dictionary for system prompt formatting"""
        if not self.state:
            return {}
        
        context = {
            "expertise_level": self.state.state["user_profile"].get("expertise_level", "unknown"),
            "gauged_complexity": self.state.state["user_profile"].get("gauged_complexity", "unknown"),
            "project_description": self.state.state["user_profile"].get("project_description", "No description yet"),
            "all_summaries": json.dumps(self.state.summaries, indent=2),
            "current_document": json.dumps(self.state.state["current_document"], indent=2)
        }
        
        return context
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state for debugging or persistence"""
        if not self.state:
            return {}
        
        return {
            "chat_history": self.state.chat_history,
            "state": self.state.state,
            "summaries": self.state.summaries
        }
    
    def import_state(self, state_data: Dict[str, Any]):
        """Import state from external data"""
        self.state = InterviewState()
        self.state.chat_history = state_data.get("chat_history", {})
        self.state.state = state_data.get("state", {})
        self.state.summaries = state_data.get("summaries", {}) 