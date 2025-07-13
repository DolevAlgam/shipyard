"""
Profiler Agent for Shipyard Interview System
Assesses user's technical expertise and project context
"""

import json
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import PROFILER_AGENT_PROMPT, PROFILER_TOPICS
from utils.helpers import needs_follow_up_llm, clean_user_input, is_skip_response, extract_expertise_level, detect_technical_complexity
from .base_agent import BaseAgent

class ProfilerAgent(BaseAgent):
    """Agent responsible for profiling user expertise and project context"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        super().__init__("profiler", PROFILER_TOPICS, PROFILER_AGENT_PROMPT)
        self.client = openai_client
        self.state_manager = state_manager
        self.pillar_name = "profiler"
        self.max_follow_ups = 3
    
    async def process_topic(self, topic: str, state: Dict, openai_client) -> Dict:
        """Required abstract method from BaseAgent"""
        await self._process_topic(topic, state)
        return state
    
    async def run_pillar(self, state) -> Dict[str, Any]:
        """
        Run the profiler pillar to assess user expertise and project context
        
        Args:
            state: Current interview state
            
        Returns:
            Updated state with profiler information
        """
        print("Let me start by understanding you and your project...")
        
        # Process each topic in the profiler pillar
        for topic in PROFILER_TOPICS:
            await self._process_topic(topic, state)
        
        # Extract and store summary
        summary = await self._extract_summary(state)
        self.state_manager.set_pillar_summary(self.pillar_name, summary)
        
        print(f"✅ Great! I now understand your background and project.")
        
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
            
            # Process the answer and update user profile
            await self._process_user_answer(topic, user_answer, state)
            
            # Check if we need follow-up
            if await needs_follow_up_llm(user_answer, agent_response, self.client):
                follow_up_count += 1
                self.state_manager.increment_follow_up_count(self.pillar_name, topic)
                print("Let me ask a follow-up question to clarify...")
            else:
                topic_complete = True
    
    async def _process_user_answer(self, topic: str, user_answer: str, state) -> None:
        """Process user's answer and update profile accordingly"""
        profile_updates = {}
        
        if topic == "expertise_assessment":
            # Extract stated expertise level
            stated_level = extract_expertise_level(user_answer)
            if stated_level:
                profile_updates["expertise_level"] = stated_level
        
        elif topic == "project_overview":
            # Store project description and assess complexity
            profile_updates["project_description"] = user_answer
            
            # Gauge complexity from how they describe it
            complexity = detect_technical_complexity(user_answer)
            stated_level = self.state_manager.get_user_profile().get("expertise_level", "unknown")
            
            if complexity == "high" and stated_level in ["novice", "intermediate"]:
                profile_updates["gauged_complexity"] = "higher than stated"
            elif complexity == "low" and stated_level == "advanced":
                profile_updates["gauged_complexity"] = "lower than stated"
            else:
                profile_updates["gauged_complexity"] = "matches stated"
        
        # Update user profile if we have updates
        if profile_updates:
            self.state_manager.update_user_profile(profile_updates)
    
    def _build_system_prompt(self, state) -> str:
        """Build system prompt with current context"""
        context = self.state_manager.build_system_prompt_context(self.pillar_name)
        
        try:
            return PROFILER_AGENT_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{PROFILER_AGENT_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    async def _extract_summary(self, state) -> Dict[str, Any]:
        """Extract key information from the profiler conversation"""
        chat_history = self.state_manager.get_chat_history(self.pillar_name)
        user_profile = self.state_manager.get_user_profile()
        
        # Build summary from user profile and conversation
        summary = {
            "expertise_stated": user_profile.get("expertise_level", "unknown"),
            "expertise_observed": user_profile.get("gauged_complexity", "unknown"),
            "project_description": user_profile.get("project_description", "Not provided"),
        }
        
        # Extract additional information from conversation
        for message in chat_history:
            if message["role"] == "user":
                content = message["content"].lower()
                
                # Extract domain/industry info
                if "domain" not in summary:
                    if any(domain in content for domain in ["fintech", "healthcare", "e-commerce", "gaming", "education"]):
                        for domain in ["fintech", "healthcare", "e-commerce", "gaming", "education"]:
                            if domain in content:
                                summary["domain"] = domain
                                break
                
                # Extract timeline info
                if "timeline" not in summary:
                    if any(time in content for time in ["month", "week", "year", "soon", "asap"]):
                        # Extract rough timeline
                        if "month" in content:
                            summary["timeline"] = "months"
                        elif "week" in content:
                            summary["timeline"] = "weeks"
                        elif "year" in content:
                            summary["timeline"] = "year+"
                        else:
                            summary["timeline"] = "soon"
        
        return summary 