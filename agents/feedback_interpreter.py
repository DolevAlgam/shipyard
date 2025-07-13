"""
Feedback Interpreter Agent for Shipyard Interview System
Interprets user feedback and applies changes to the infrastructure document
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import FEEDBACK_INTERPRETER_PROMPT

class FeedbackInterpreterAgent:
    """Agent responsible for interpreting user feedback and applying changes"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
    
    async def apply_feedback(self, document: str, feedback: str, state) -> str:
        """
        Apply user feedback to the infrastructure document
        
        Args:
            document: Current infrastructure document
            feedback: User's feedback about changes needed
            state: Current interview state
            
        Returns:
            Updated document with feedback applied
        """
        print("Analyzing your feedback and applying changes...")
        
        # Build system prompt with current context
        system_prompt = self._build_system_prompt(document, feedback, state)
        
        # Create input for feedback interpretation
        agent_input = f"Apply the following feedback to the document:\n\nFeedback: {feedback}\n\nProvide the updated document."
        
        # Get updated document
        updated_document = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.3,  # Lower temperature for more consistent changes
            max_tokens=4000   # Increased token limit for full document
        )
        
        return updated_document
    
    async def interpret_feedback(self, feedback: str, state) -> Dict[str, Any]:
        """
        Interpret user feedback to understand what changes are needed
        
        Args:
            feedback: User's feedback
            state: Current interview state
            
        Returns:
            Structured interpretation of the feedback
        """
        # Build simple prompt for interpretation
        system_prompt = "You are a feedback interpreter. Analyze user feedback and identify what specific changes they want to make to their infrastructure document."
        
        agent_input = f"Interpret this feedback and identify the specific changes requested:\n\nFeedback: {feedback}\n\nProvide a structured analysis of what needs to be changed."
        
        interpretation = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.3
        )
        
        # Parse interpretation into structured format
        try:
            # Try to parse as JSON if possible
            structured_feedback = json.loads(interpretation)
        except json.JSONDecodeError:
            # If not JSON, create structured format from text
            structured_feedback = self._parse_text_feedback(interpretation)
        
        return structured_feedback
    
    def _build_system_prompt(self, document: str, feedback: str, state) -> str:
        """Build system prompt with document and feedback context"""
        context = self.state_manager.build_system_prompt_context("feedback_interpreter")
        
        # Add document and feedback to context
        context["document"] = document
        context["feedback"] = feedback
        
        try:
            return FEEDBACK_INTERPRETER_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{FEEDBACK_INTERPRETER_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    def _parse_text_feedback(self, interpretation: str) -> Dict[str, Any]:
        """Parse text interpretation into structured format"""
        feedback_analysis = {
            "interpretation": interpretation,
            "changes_requested": [],
            "sections_affected": [],
            "priority": "medium"
        }
        
        lines = interpretation.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line:
                # Look for common change indicators
                if any(word in line.lower() for word in ['change', 'update', 'modify', 'add', 'remove']):
                    feedback_analysis["changes_requested"].append(line)
                
                # Look for section references
                sections = [
                    "executive summary", "architecture", "compute", "networking", 
                    "storage", "security", "monitoring", "disaster recovery", 
                    "ci/cd", "cost", "timeline", "assumptions"
                ]
                
                for section in sections:
                    if section in line.lower():
                        feedback_analysis["sections_affected"].append(section)
        
        return feedback_analysis
    
    async def clarify_feedback(self, feedback: str, state) -> str:
        """
        Ask for clarification if feedback is unclear
        
        Args:
            feedback: User's unclear feedback
            state: Current interview state
            
        Returns:
            Clarification question for the user
        """
        system_prompt = "You are a helpful assistant. The user has provided unclear feedback about their infrastructure document. Ask a clarifying question to understand what they want to change."
        
        agent_input = f"The user said: '{feedback}'\n\nThis is unclear. Ask a helpful clarifying question to understand what specific changes they want to make."
        
        clarification = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.7
        )
        
        return clarification 