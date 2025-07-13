"""
App Agent for Shipyard Interview System
Collects technical application requirements
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import APP_AGENT_PROMPT, APP_TOPICS
from utils.helpers import needs_follow_up_llm, get_user_input, is_skip_request_llm

class AppAgent:
    """Agent responsible for collecting technical application requirements"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
        self.pillar_name = "app"
        self.max_follow_ups = 3
    
    async def run_pillar(self, state) -> Dict[str, Any]:
        """
        Run the app pillar to collect technical application requirements
        
        Args:
            state: Current interview state
            
        Returns:
            Updated state with app requirements
        """
        print("Now let's dive into your application's technical requirements...")
        
        # Process each topic in the app pillar
        for topic in APP_TOPICS:
            await self._process_topic(topic, state)
        
        # Note: Summary will be handled by SummarizerAgent when called by the main orchestrator
        
        print(f"✅ Excellent! I now understand your technical requirements.")
        
        return state
    
    async def _process_topic(self, topic: str, state) -> None:
        """Process a single topic with follow-up handling"""
        follow_up_count = 0
        topic_complete = False
        
        while not topic_complete and follow_up_count < self.max_follow_ups:
            # Build system prompt with current context
            system_prompt = self._build_system_prompt(state)
            
            # Determine the message for the agent
            if follow_up_count == 0:
                # First time asking about this topic
                agent_input = f"Ask the user about: {topic}"
            else:
                # Follow-up based on user's response
                agent_input = "The user needs clarification or you need to probe deeper. Provide a follow-up question or explanation."
            
            # Get agent's question/response
            agent_response = await self.client.call_agent(
                system_prompt, 
                agent_input,
                self.state_manager.get_chat_history(self.pillar_name)
            )
            
            # Display agent's question
            print(f"\n{agent_response}")
            
            # Get user's answer
            user_answer = get_user_input("\nYour answer: ")
            
            # Add to chat history
            self.state_manager.add_to_chat_history(self.pillar_name, "assistant", agent_response)
            self.state_manager.add_to_chat_history(self.pillar_name, "user", user_answer)
            
            # Check if user wants to skip
            if await is_skip_request_llm(user_answer, self.client):
                print("No problem, skipping this question.")
                topic_complete = True
                continue
            
            # Check if we need follow-up
            if await needs_follow_up_llm(user_answer, agent_response, self.client):
                follow_up_count += 1
                self.state_manager.increment_follow_up_count(self.pillar_name, topic)
            else:
                topic_complete = True
    
    def _build_system_prompt(self, state) -> str:
        """Build system prompt with current context"""
        context = self.state_manager.build_system_prompt_context(self.pillar_name)
        
        try:
            return APP_AGENT_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{APP_AGENT_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
 