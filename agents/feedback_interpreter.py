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
            # If not JSON, use LLM to create structured format from text
            structured_feedback = await self._parse_text_feedback_llm(interpretation)
        
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
    
    async def _parse_text_feedback_llm(self, interpretation: str) -> Dict[str, Any]:
        """Parse text interpretation into structured format using LLM analysis"""
        prompt = f"""You are analyzing feedback interpretation text to extract structured information.

INTERPRETATION TEXT: {interpretation}

Extract the following information and return as JSON:
{{
    "interpretation": "The full interpretation text",
    "changes_requested": ["List of specific changes or modifications requested"],
    "sections_affected": ["List of document sections that need updates"],
    "priority": "low/medium/high based on urgency and scope"
}}

Analyze the semantic meaning, not just keyword presence. Understand the intent behind the feedback."""

        try:
            result = await self.client.call_agent(
                "You are an expert at analyzing feedback and extracting structured information.",
                prompt,
                []
            )
            return json.loads(result)
        except Exception as e:
            # Fallback structure if LLM fails
            return {
                "interpretation": interpretation,
                "changes_requested": [interpretation],
                "sections_affected": [],
                "priority": "medium"
            }
    
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