"""
Tribal Agent for Shipyard Interview System
Understands organizational constraints and preferences
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import TRIBAL_AGENT_PROMPT, TRIBAL_TOPICS
from utils.helpers import needs_follow_up_llm, clean_user_input, is_skip_response

class TribalAgent:
    """Agent responsible for understanding organizational constraints and preferences"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
        self.pillar_name = "tribal"
        self.max_follow_ups = 3
    
    async def run_pillar(self, state) -> Dict[str, Any]:
        """
        Run the tribal pillar to understand organizational constraints
        
        Args:
            state: Current interview state
            
        Returns:
            Updated state with tribal knowledge
        """
        print("Let's learn about your organizational setup and preferences...")
        
        # Process each topic in the tribal pillar
        for topic in TRIBAL_TOPICS:
            await self._process_topic(topic, state)
        
        # Extract and store summary
        summary = await self._extract_summary(state)
        self.state_manager.set_pillar_summary(self.pillar_name, summary)
        
        print(f"✅ Great! I now understand your organizational context.")
        
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
            return TRIBAL_AGENT_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{TRIBAL_AGENT_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    async def _extract_summary(self, state) -> Dict[str, Any]:
        """Extract key information from the tribal conversation"""
        chat_history = self.state_manager.get_chat_history(self.pillar_name)
        
        summary = {}
        
        # Extract key organizational information from conversation
        for message in chat_history:
            if message["role"] == "user":
                content = message["content"].lower()
                
                # Extract cloud provider preferences
                if "cloud_provider" not in summary:
                    providers = ["aws", "azure", "google", "gcp", "amazon", "microsoft"]
                    if any(provider in content for provider in providers):
                        summary["cloud_provider"] = message["content"]
                
                # Extract existing tools
                if "existing_tools" not in summary:
                    tools = ["github", "gitlab", "jenkins", "docker", "kubernetes", "terraform", "ansible"]
                    if any(tool in content for tool in tools):
                        summary["existing_tools"] = message["content"]
                
                # Extract team expertise
                if "team_expertise" not in summary:
                    expertise_terms = ["team", "developer", "engineer", "experience", "skill", "knowledge"]
                    if any(term in content for term in expertise_terms):
                        summary["team_expertise"] = message["content"]
                
                # Extract security policies
                if "security_policies" not in summary:
                    security_terms = ["security", "policy", "compliance", "audit", "governance", "access"]
                    if any(term in content for term in security_terms):
                        summary["security_policies"] = message["content"]
                
                # Extract operational preferences
                if "operational_preferences" not in summary:
                    ops_terms = ["manage", "maintenance", "monitoring", "support", "operations", "devops"]
                    if any(term in content for term in ops_terms):
                        summary["operational_preferences"] = message["content"]
        
        return summary 