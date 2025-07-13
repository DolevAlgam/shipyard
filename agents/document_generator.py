"""
Document Generator Agent for Shipyard Interview System
Generates the final comprehensive infrastructure planning document
Now enhanced with o3 reasoning capabilities for superior architectural analysis
"""

import json
import datetime
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import DOCUMENT_GENERATOR_PROMPT, get_prompt_for_operation
from utils.helpers import sanitize_filename
from agents.base_agent import BaseAgent

class DocumentGeneratorAgent(BaseAgent):
    """Agent responsible for generating comprehensive infrastructure documents using o3 reasoning"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        # Initialize BaseAgent with o3 reasoning configuration
        super().__init__(
            name="DocumentGeneratorAgent",
            topics=["document_generation"],
            prompt="Expert infrastructure architect with advanced reasoning capabilities"
        )
        self.client = openai_client
        self.state_manager = state_manager
    
    async def generate_document(self, all_summaries: str, current_document: str = "") -> str:
        """
        Generate comprehensive infrastructure planning document using o3 reasoning
        Now includes architecture recommendation pre-processing for enhanced accuracy
        
        Args:
            all_summaries: Combined summaries from all interview phases
            current_document: Any existing document content to build upon
            
        Returns:
            Generated infrastructure planning document
        """
        try:
            # Step 1: Generate architecture recommendation first
            architecture_recommendation = await self._generate_architecture_recommendation(all_summaries)
            
            # Step 2: Generate the main document using architecture insights
            return await self._generate_main_document(all_summaries, current_document, architecture_recommendation)
            
        except Exception as e:
            print(f"Error generating document: {str(e)}")
            return f"Error generating document: {str(e)}"
    
    async def _generate_architecture_recommendation(self, all_summaries: str) -> str:
        """
        Generate architecture recommendation to inform document generation
        
        Args:
            all_summaries: Combined summaries from all interview phases
            
        Returns:
            Architecture recommendation content
        """
        try:
            architecture_prompt = f"""
            REQUIREMENTS SUMMARY:
            {all_summaries}
            
            USER PROFILE:
            - Expertise Level: {self.state_manager.get_user_profile().get('expertise_level', 'Unknown')}
            - Project Type: {self.state_manager.get_user_profile().get('project_description', 'Not specified')}
            - Technical Context: Not specified
            """
            
            # Use architecture recommendation operation mode
            architecture_response = await self.get_response(
                system_prompt=get_prompt_for_operation("architecture_recommendation"),
                user_message=architecture_prompt,
                openai_client=self.client,
                operation_mode="architecture_recommendation"
            )
            
            print("Architecture recommendation generated successfully")
            return architecture_response
            
        except Exception as e:
            print(f"Error generating architecture recommendation: {str(e)}")
            return "Architecture recommendation could not be generated due to an error."
    
    async def _generate_main_document(self, all_summaries: str, current_document: str, architecture_recommendation: str) -> str:
        """
        Generate the main infrastructure document using architecture insights
        
        Args:
            all_summaries: Combined summaries from all interview phases
            current_document: Any existing document content
            architecture_recommendation: Pre-generated architecture insights
            
        Returns:
            Complete infrastructure planning document
        """
        # Enhanced document generation prompt with architecture insights
        document_prompt = f"""
        ARCHITECTURE RECOMMENDATION (use as foundation):
        {architecture_recommendation}
        
        COMPLETE REQUIREMENTS SUMMARY:
        {all_summaries}
        
        USER PROFILE:
        - Expertise Level: {self.state_manager.get_user_profile().get('expertise_level', 'Unknown')}
        - Project Complexity: {self.state_manager.get_user_profile().get('project_description', 'Not specified')}
        
        EXISTING DOCUMENT (if any):
        {current_document if current_document else "No existing document"}
        
        INTEGRATION INSTRUCTIONS:
        Incorporate the architecture recommendation insights into a comprehensive infrastructure document.
        Ensure consistency between the recommended architecture and all implementation details.
        Use the architecture rationale to support implementation decisions throughout the document.
        """
        
        response = await self.get_response(
            system_prompt=get_prompt_for_operation("document_generation"),
            user_message=document_prompt,
            openai_client=self.client,
            operation_mode="document_generation"
        )
        
        # Save the generated document
        self.save_document(response)
        
        return response
    
    async def generate_section_with_reasoning(self, section_name: str, state) -> str:
        """
        Generate a specific section using o3 reasoning capabilities
        
        Args:
            section_name: Name of the section to generate
            state: Current interview state
            
        Returns:
            Generated section content with detailed reasoning
        """
        system_prompt = self._build_reasoning_system_prompt(state)
        
        agent_input = f"""Generate the '{section_name}' section of the infrastructure planning document.
        
Use advanced reasoning to:
1. Analyze requirements specific to {section_name}
2. Evaluate multiple approaches and technologies
3. Provide detailed justification for recommendations
4. Consider implementation complexity and trade-offs
5. Include cost implications and optimization opportunities
6. Address potential risks and mitigation strategies

Focus specifically on {section_name} while considering its integration with the overall architecture."""
        
        section_content = await self.get_response(
            system_prompt=system_prompt,
            user_message=agent_input,
            openai_client=self.client,
            operation_mode="document_generation",
            temperature=0.3,
            max_tokens=4000
        )
        
        return section_content
    
    async def process_topic(self, topic: str, state: Dict, openai_client) -> Dict:
        """Required implementation of BaseAgent abstract method"""
        if topic == "document_generation":
            document = await self.generate_document(state)
            return {"document": document, "status": "completed"}
        else:
            raise ValueError(f"Unknown topic for DocumentGeneratorAgent: {topic}")
    
    def _build_reasoning_system_prompt(self, state) -> str:
        """Build system prompt optimized for o3 reasoning models"""
        context = self.state_manager.build_system_prompt_context("document_generator")
        
        # Use o3-specific prompt if available
        if self.supports_reasoning():
            prompt_template = get_prompt_for_operation("document_generation", DOCUMENT_GENERATOR_PROMPT)
        else:
            prompt_template = DOCUMENT_GENERATOR_PROMPT
        
        try:
            return prompt_template.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{prompt_template}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    def _build_system_prompt(self, state) -> str:
        """Legacy method for backward compatibility"""
        return self._build_reasoning_system_prompt(state)
    
    def _add_document_metadata(self, document: str, state) -> str:
        """Add metadata header including reasoning model information"""
        user_profile = self.state_manager.get_user_profile()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        model_info = self.get_model_info()
        
        metadata_header = f"""---
title: Infrastructure Planning Document
generated_by: Shipyard AI Assistant
ai_model: {model_info['model']}
reasoning_enabled: {model_info['is_reasoning_model']}
effort_level: {model_info['effort'] or 'N/A'}
date: {timestamp}
user_expertise: {user_profile.get('expertise_level', 'Unknown')}
project: {user_profile.get('project_description', 'Not specified')[:500]}...
---

"""
        
        return metadata_header + document
    
    async def generate_section(self, section_name: str, state) -> str:
        """
        Generate a specific section of the document
        Maintained for backward compatibility, enhanced with reasoning
        """
        return await self.generate_section_with_reasoning(section_name, state)
    
    def get_document_sections(self) -> List[str]:
        """Get list of standard document sections"""
        if self.supports_reasoning():
            # Enhanced sections for reasoning models
            return [
                "Executive Summary",
                "Architecture Overview with Reasoning",
                "Detailed Technical Specifications",
                "Security Architecture",
                "Scalability Strategy", 
                "Cost Analysis and Optimization",
                "Implementation Roadmap",
                "Monitoring and Observability Strategy",
                "Disaster Recovery and Business Continuity",
                "Risk Assessment and Mitigation",
                "Assumptions and Recommendations"
            ]
        else:
            # Standard sections for legacy models
            return [
                "Executive Summary",
                "Architecture Overview", 
                "Compute Resources",
                "Networking Configuration",
                "Storage Solutions",
                "Security Measures",
                "Monitoring and Observability",
                "Disaster Recovery Plan",
                "CI/CD Pipeline",
                "Cost Estimates",
                "Implementation Timeline",
                "Assumptions and Recommendations"
            ]
    
    def save_document(self, document: str, filename: Optional[str] = None) -> str:
        """
        Save document to file with reasoning model information
        
        Args:
            document: Document content to save
            filename: Optional custom filename
            
        Returns:
            Saved filename
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            model_suffix = "o3" if self.supports_reasoning() else "gpt4o"
            filename = f"infrastructure_plan_{model_suffix}_{timestamp}.md"
        
        # Sanitize filename
        filename = sanitize_filename(filename)
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(document)
        
        print(f"💾 Document saved as: {filename}")
        if self.supports_reasoning():
            print(f"   Generated using: {self.model} reasoning model")
        
        return filename 