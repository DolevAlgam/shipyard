"""
Feedback Interpreter Agent for Shipyard Interview System
Interprets user feedback and modifies the generated document accordingly
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import FEEDBACK_INTERPRETER_PROMPT
from .base_agent import BaseAgent

class FeedbackInterpreterAgent(BaseAgent):
    """Agent responsible for interpreting feedback and updating documents"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        super().__init__("feedback_interpreter", [], FEEDBACK_INTERPRETER_PROMPT)
        self.client = openai_client
        self.state_manager = state_manager
    
    async def process_topic(self, topic: str, state: Dict, openai_client) -> Dict:
        """Required abstract method from BaseAgent - not used for this agent"""
        return state
    
    async def apply_feedback(self, document: str, feedback: str, state) -> str:
        """
        Apply user feedback to the document
        
        Args:
            document: Current document content
            feedback: User's feedback
            state: Current interview state
            
        Returns:
            Updated document with feedback applied
        """
        # Build system prompt with context
        system_prompt = self._build_system_prompt(document, feedback, state)
        
        # Create input for feedback interpretation
        agent_input = f"Apply the following feedback to the document:\n\nFeedback: {feedback}\n\nProvide the updated document."
        
        # Get updated document using reasoning model
        updated_document = await self.get_response(
            system_prompt=system_prompt,
            user_message=agent_input,
            openai_client=self.client,
            temperature=0.3,  # Lower temperature for more consistent changes
            max_tokens=4000   # Increased token limit for full document
        )
        
        return updated_document
    
    async def interpret_feedback(self, feedback: str, state) -> Dict[str, Any]:
        """
        Interpret user feedback to understand what changes are needed
        
        Args:
            feedback: User's feedback text
            state: Current interview state
            
        Returns:
            Dictionary with interpretation results
        """
        # Build system prompt for feedback interpretation
        system_prompt = f"""You are an expert at interpreting user feedback about technical documents.
        
        Analyze the feedback and determine:
        1. What sections need to be changed
        2. What specific changes are requested
        3. Whether the feedback is clear or needs clarification
        
        USER PROFILE:
        - Expertise Level: {state.get('user_profile', {}).get('expertise_level', 'unknown')}
        - Project Type: {state.get('user_profile', {}).get('project_description', 'unknown')}
        
        Provide your analysis in a clear, structured format."""
        
        # Create input for interpretation
        agent_input = f"Interpret this feedback: {feedback}"
        
        # Get interpretation using reasoning model
        interpretation = await self.get_response(
            system_prompt=system_prompt,
            user_message=agent_input,
            openai_client=self.client,
            temperature=0.2  # Lower temperature for consistent interpretation
        )
        
        # Parse the interpretation into structured data
        parsed_feedback = await self._parse_text_feedback_llm(interpretation)
        
        return {
            'raw_feedback': feedback,
            'interpretation': interpretation,
            'structured_feedback': parsed_feedback,
            'needs_clarification': len(feedback.strip()) < 10 or "unclear" in interpretation.lower()
        }
    
    def _build_system_prompt(self, document: str, feedback: str, state) -> str:
        """Build system prompt with current context"""
        context = self.state_manager.build_system_prompt_context("feedback_interpreter")
        
        prompt = f"""{FEEDBACK_INTERPRETER_PROMPT}

CURRENT DOCUMENT:
{document[:2000]}{'...' if len(document) > 2000 else ''}

USER FEEDBACK:
{feedback}

CONTEXT:
{json.dumps(context, indent=2)}"""
        
        return prompt
    
    async def _parse_text_feedback_llm(self, interpretation: str) -> Dict[str, Any]:
        """Parse text feedback interpretation into structured data using LLM"""
        prompt = f"""Parse this feedback interpretation into structured data:

{interpretation}

Extract and return a JSON object with:
- sections_to_change: list of section names
- change_type: "add", "remove", "modify", or "clarify"
- priority: "high", "medium", or "low"
- specific_requests: list of specific changes mentioned

Return only valid JSON."""
        
        # Parse using reasoning model for better structure understanding
        result = await self.get_response(
            system_prompt="You are a JSON parser. Return only valid JSON objects.",
            user_message=prompt,
            openai_client=self.client,
            temperature=0.1,  # Very low temperature for consistent JSON
            max_tokens=500
        )
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "sections_to_change": ["unknown"],
                "change_type": "modify",
                "priority": "medium",
                "specific_requests": [interpretation[:100]]
            }
    
    async def clarify_feedback(self, feedback: str, state) -> str:
        """
        Generate clarifying questions for unclear feedback
        
        Args:
            feedback: Original feedback that needs clarification
            state: Current interview state
            
        Returns:
            Clarifying question(s) for the user
        """
        system_prompt = f"""You are helping clarify user feedback about a technical document.
        
        The user gave unclear feedback. Generate 1-2 specific questions to understand what they want.
        
        USER PROFILE:
        - Expertise Level: {state.get('user_profile', {}).get('expertise_level', 'unknown')}
        - Project Type: {state.get('user_profile', {}).get('project_description', 'unknown')}
        
        Ask questions appropriate for their technical level."""
        
        agent_input = f"The user said: '{feedback}'\n\nWhat clarifying questions should I ask?"
        
        # Generate clarification using reasoning model
        clarification = await self.get_response(
            system_prompt=system_prompt,
            user_message=agent_input,
            openai_client=self.client,
            temperature=0.4,  # Moderate temperature for natural questions
            max_tokens=200
        )
        
        return clarification 