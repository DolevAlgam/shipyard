"""
Best Practices Agent for Shipyard Interview System
Fills gaps with industry best practices and sensible defaults
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import BEST_PRACTICES_PROMPT, INFRASTRUCTURE_CHECKLIST
from utils.helpers import format_summary

class BestPracticesAgent:
    """Agent responsible for filling gaps with industry best practices"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
        self.pillar_name = "best_practices"
    
    async def run_pillar(self, state) -> Dict[str, Any]:
        """
        Run the best practices pillar to fill gaps with sensible defaults
        
        Args:
            state: Current interview state
            
        Returns:
            Updated state with best practices applied
        """
        print("Now I'll review everything and fill in any gaps with best practices...")
        
        # Build comprehensive requirements summary
        requirements = self._build_requirements_summary(state)
        
        # Apply best practices to fill gaps
        best_practices_additions = await self._apply_best_practices(requirements, state)
        
        # Update current document with best practices
        self.state_manager.update_current_document("best_practices", best_practices_additions)
        
        # Store summary
        summary = {
            "applied_practices": "Industry best practices applied for missing requirements",
            "requirements_reviewed": len(requirements),
            "gaps_filled": "Security, monitoring, backup, and deployment defaults added"
        }
        self.state_manager.set_pillar_summary(self.pillar_name, summary)
        
        print(f"✅ All set! I've added industry best practices where needed.")
        
        return state
    
    def _build_requirements_summary(self, state) -> Dict[str, Any]:
        """Build comprehensive requirements summary from all pillars"""
        requirements = {
            "user_profile": self.state_manager.get_user_profile(),
            "summaries": self.state_manager.get_all_summaries(),
            "current_document": self.state_manager.get_current_document()
        }
        
        return requirements
    
    async def _apply_best_practices(self, requirements: Dict[str, Any], state) -> str:
        """Apply best practices to fill gaps in requirements"""
        
        # Build system prompt with current context
        system_prompt = self._build_system_prompt(state)
        
        # Create input for best practices agent
        requirements_text = json.dumps(requirements, indent=2)
        agent_input = f"Review these requirements and fill any gaps with best practices:\n\n{requirements_text}"
        
        # Get best practices recommendations
        best_practices_response = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.3  # Lower temperature for more consistent recommendations
        )
        
        return best_practices_response
    
    def _build_system_prompt(self, state) -> str:
        """Build system prompt with current context"""
        context = self.state_manager.build_system_prompt_context(self.pillar_name)
        
        # Add infrastructure checklist to context
        context["infrastructure_checklist"] = json.dumps(INFRASTRUCTURE_CHECKLIST, indent=2)
        
        try:
            return BEST_PRACTICES_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{BEST_PRACTICES_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}" 