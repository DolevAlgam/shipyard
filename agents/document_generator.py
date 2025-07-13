"""
Document Generator Agent for Shipyard Interview System
Generates the final comprehensive infrastructure planning document
"""

import json
import datetime
from typing import Dict, List, Any, Optional
from core.openai_client import OpenAIClient
from core.state_manager import StateManager
from core.prompts import DOCUMENT_GENERATOR_PROMPT
from utils.helpers import sanitize_filename

class DocumentGeneratorAgent:
    """Agent responsible for generating the final infrastructure document"""
    
    def __init__(self, openai_client: OpenAIClient, state_manager: StateManager):
        self.client = openai_client
        self.state_manager = state_manager
    
    async def generate_document(self, state) -> str:
        """
        Generate the final comprehensive infrastructure planning document
        
        Args:
            state: Current interview state with all collected information
            
        Returns:
            Complete infrastructure planning document in markdown format
        """
        print("Generating your comprehensive infrastructure plan...")
        
        # Build system prompt with all collected information
        system_prompt = self._build_system_prompt(state)
        
        # Create input for document generation
        agent_input = "Generate a comprehensive infrastructure planning document based on all the collected requirements and information."
        
        # Generate document
        document = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.4,  # Balanced temperature for structured but creative output
            max_tokens=4000   # Increased token limit for comprehensive document
        )
        
        # Add metadata header
        document_with_metadata = self._add_document_metadata(document, state)
        
        return document_with_metadata
    
    def _build_system_prompt(self, state) -> str:
        """Build system prompt with all collected information"""
        context = self.state_manager.build_system_prompt_context("document_generator")
        
        try:
            return DOCUMENT_GENERATOR_PROMPT.format(**context)
        except KeyError:
            # If some keys are missing, return base prompt with available context
            return f"{DOCUMENT_GENERATOR_PROMPT}\n\nCONTEXT:\n{json.dumps(context, indent=2)}"
    
    def _add_document_metadata(self, document: str, state) -> str:
        """Add metadata header to the document"""
        user_profile = self.state_manager.get_user_profile()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        metadata_header = f"""---
title: Infrastructure Planning Document
generated_by: Shipyard AI Assistant
date: {timestamp}
user_expertise: {user_profile.get('expertise_level', 'Unknown')}
project: {user_profile.get('project_description', 'Not specified')[:100]}...
---

"""
        
        return metadata_header + document
    
    async def generate_section(self, section_name: str, state) -> str:
        """
        Generate a specific section of the document
        
        Args:
            section_name: Name of the section to generate
            state: Current interview state
            
        Returns:
            Generated section content
        """
        system_prompt = self._build_system_prompt(state)
        
        agent_input = f"Generate only the '{section_name}' section of the infrastructure planning document. Focus specifically on {section_name} requirements and recommendations."
        
        section_content = await self.client.call_agent(
            system_prompt,
            agent_input,
            temperature=0.4,
            max_tokens=2000
        )
        
        return section_content
    
    def get_document_sections(self) -> List[str]:
        """Get list of standard document sections"""
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
        Save document to file
        
        Args:
            document: Document content to save
            filename: Optional custom filename
            
        Returns:
            Saved filename
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"infrastructure_plan_{timestamp}.md"
        
        # Sanitize filename
        filename = sanitize_filename(filename)
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(document)
        
        return filename 