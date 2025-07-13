"""
Business Agent for Shipyard Interview System
Gathers business requirements and constraints
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import BUSINESS_AGENT_PROMPT, BUSINESS_TOPICS
from utils.helpers import needs_follow_up_llm, clean_user_input, is_skip_response

class BusinessAgent:
    """Agent responsible for gathering business requirements and constraints"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
        self.pillar_name = "business"
        self.max_follow_ups = 3
    
    async def run_pillar(self, state) -> Dict[str, Any]:
        """
        Run the business pillar to gather business requirements
        
        Args:
            state: Current interview state
            
        Returns:
            Updated state with business requirements
        """
        print("Now let's discuss your business requirements and constraints...")
        
        # Process each topic in the business pillar
        for topic in BUSINESS_TOPICS:
            await self._process_topic(topic, state)
        
        # Extract and store summary
        summary = await self._extract_summary(state)
        self.state_manager.set_pillar_summary(self.pillar_name, summary)
        
        print(f"✅ Perfect! I now understand your business needs.")
        
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
            user_answer = input("\nYour answer: ").strip()
            user_answer = clean_user_input(user_answer)
            
            # Add to chat history
            self.state_manager.add_to_chat_history(self.pillar_name, "assistant", agent_response)
            self.state_manager.add_to_chat_history(self.pillar_name, "user", user_answer)
            
            # Check if user wants to skip
            if is_skip_response(user_answer):
                print("No problem, skipping this question.")
                topic_complete = True
                continue
            
            # Check if we need follow-up
            if await needs_follow_up_llm(user_answer, agent_response, self.client):
                follow_up_count += 1
                self.state_manager.increment_follow_up_count(self.pillar_name, topic)
                print("Let me ask a follow-up question to clarify...")
            else:
                topic_complete = True
    
    def _build_system_prompt(self, state) -> str:
        """Build system prompt with current context"""
        context = self.state_manager.build_system_prompt_context(self.pillar_name)
        
        try:
            return BUSINESS_AGENT_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{BUSINESS_AGENT_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    async def _extract_summary(self, state) -> Dict[str, Any]:
        """Extract key information from the business conversation"""
        chat_history = self.state_manager.get_chat_history(self.pillar_name)
        
        summary = {}
        
        # Extract key business information from conversation
        for message in chat_history:
            if message["role"] == "user":
                content = message["content"].lower()
                
                # Extract user scale information
                if "user_scale" not in summary:
                    if any(scale in content for scale in ["thousand", "million", "hundred", "k", "m"]):
                        summary["user_scale"] = message["content"]
                
                # Extract uptime requirements
                if "uptime_requirement" not in summary:
                    if any(uptime in content for uptime in ["99", "uptime", "availability", "sla"]):
                        summary["uptime_requirement"] = message["content"]
                
                # Extract budget information
                if "budget" not in summary:
                    if any(budget in content for budget in ["budget", "cost", "dollar", "$", "expensive", "cheap"]):
                        summary["budget"] = message["content"]
                
                # Extract compliance requirements
                if "compliance" not in summary:
                    if any(comp in content for comp in ["compliance", "regulation", "pci", "hipaa", "gdpr", "sox"]):
                        summary["compliance"] = message["content"]
                
                # Extract geographic distribution
                if "geographic" not in summary:
                    if any(geo in content for geo in ["region", "country", "global", "international", "local"]):
                        summary["geographic"] = message["content"]
        
        return summary 