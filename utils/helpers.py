"""
Helper functions for the Shipyard interview system
"""

import json
import re
from typing import Dict, List, Any, Optional

async def needs_follow_up_llm(user_answer: str, question: str, openai_client) -> bool:
    """
    Determine if user's answer indicates they need clarification or follow-up using enhanced reasoning model analysis
    
    Args:
        user_answer: The user's response to a question
        question: The original question that was asked
        openai_client: OpenAI client for LLM analysis
        
    Returns:
        True if the answer suggests confusion or need for clarification
    """
    from config.reasoning_config import get_operation_config
    
    # Get configuration for follow-up detection
    config = get_operation_config('follow_up_detection')
    
    prompt = f"""You are analyzing a conversation to determine if a follow-up question is needed.

QUESTION ASKED: "{question}"
USER RESPONSE: "{user_answer}"

Analyze if this response adequately answers the question or if follow-up is needed.

Consider:
- Does the user seem confused or uncertain?
- Is the response vague or incomplete?
- Are they asking for clarification?
- Do they seem to not understand the question?
- Is their answer off-topic or irrelevant?

Respond with exactly "FOLLOW_UP_NEEDED" or "COMPLETE" - nothing else."""

    try:
        result = await openai_client.call_agent(
            system_prompt="You are a conversation analysis expert.",
            user_message=prompt,
            chat_history=[],  # No chat history needed for this analysis
            model=config['model'],
            effort=config['effort'],
            reasoning_summary=config['reasoning_summary']
        )
        
        # Extract content if it's a ReasoningResponse
        content = result.content if hasattr(result, 'content') else result
        return "FOLLOW_UP_NEEDED" in content.upper()
    except Exception as e:
        # Return False if LLM fails - assume no follow-up needed as safe default
        return False

async def is_skip_request_llm(user_answer: str, openai_client) -> bool:
    """
    Determine if user wants to skip a question using enhanced reasoning model analysis
    
    Args:
        user_answer: The user's response
        openai_client: OpenAI client for LLM analysis
        
    Returns:
        True if the user wants to skip the question
    """
    from config.reasoning_config import get_operation_config
    
    # Get configuration for skip detection
    config = get_operation_config('skip_detection')
    
    prompt = f"""You are analyzing a user's response to determine if they want to skip or pass on answering a question.

USER RESPONSE: "{user_answer}"

Analyze if this response indicates the user wants to skip the question.

Consider:
- Explicit skip requests ("skip", "pass", "next question")
- Uncertainty expressions that suggest skipping ("I don't know", "not sure", "no idea")
- Dismissive responses ("not applicable", "n/a", "doesn't apply")
- Lack of information ("can't answer", "don't have info")
- Intent to move on rather than engage with the topic

DO NOT consider as skip requests:
- Genuine attempts to answer, even if incomplete
- Questions asking for clarification
- Expressions of uncertainty but willingness to try

Respond with exactly "SKIP" or "ANSWER" - nothing else."""

    try:
        result = await openai_client.call_agent(
            system_prompt="You are a conversation analysis expert specialized in understanding user intent.",
            user_message=prompt,
            chat_history=[],  # No chat history needed for this analysis
            model=config['model'],
            effort=config['effort'],
            reasoning_summary=config['reasoning_summary']
        )
        
        # Extract content if it's a ReasoningResponse
        content = result.content if hasattr(result, 'content') else result
        return "SKIP" in content.upper()
    except Exception as e:
        # Return False if LLM fails - assume user wants to answer as safe default
        return False

async def extract_expertise_level_llm(user_input: str, openai_client) -> Optional[str]:
    """
    Extract expertise level from user input using enhanced reasoning model analysis
    
    Args:
        user_input: User's response about their expertise
        openai_client: OpenAI client for LLM analysis
        
    Returns:
        Detected expertise level: "novice", "intermediate", "advanced", or None if unclear
    """
    from config.reasoning_config import get_operation_config
    
    # Get configuration for expertise extraction
    config = get_operation_config('expertise_extraction')
    
    prompt = f"""You are analyzing a user's response to determine their technical expertise level.

USER RESPONSE: "{user_input}"

Analyze this response to determine the user's self-described technical expertise level.

Consider:
- Explicit mentions of experience level ("beginner", "expert", "professional")
- Years of experience mentioned
- Technologies and concepts they're familiar with
- Confidence level in their language
- Complexity of problems they've solved
- Self-assessment indicators

Classify as:
- NOVICE: Beginner, new to technology, first time, learning basics, no experience
- INTERMEDIATE: Some experience, limited knowledge, learning, moderate skills
- ADVANCED: Expert, professional, years of experience, deep technical knowledge

If the expertise level is not clear from the response, return UNCLEAR.

Respond with exactly "NOVICE", "INTERMEDIATE", "ADVANCED", or "UNCLEAR" - nothing else."""

    try:
        result = await openai_client.call_agent(
            system_prompt="You are an expert at assessing technical expertise levels.",
            user_message=prompt,
            chat_history=[],  # No chat history needed for this analysis
            model=config['model'],
            effort=config['effort'],
            reasoning_summary=config['reasoning_summary']
        )
        
        # Extract content if it's a ReasoningResponse
        content = result.content if hasattr(result, 'content') else result
        result_upper = content.upper().strip()
        if result_upper in ["NOVICE", "INTERMEDIATE", "ADVANCED"]:
            return result_upper.lower()
        else:
            return None
    except Exception as e:
        # Return None if LLM analysis fails - no fallback keyword logic
        return None

async def assess_technical_complexity_llm(text: str, openai_client) -> str:
    """
    Analyze text to detect technical complexity level using LLM semantic analysis
    
    Args:
        text: User's description or response about their project
        openai_client: OpenAI client for LLM analysis
        
    Returns:
        Detected complexity level: "low", "medium", or "high"
    """
    prompt = f"""You are analyzing a user's project description to assess its technical complexity.

PROJECT DESCRIPTION: "{text}"

Analyze this description to determine the technical complexity level of the project.

Consider:
- Infrastructure sophistication (microservices, containers, orchestration)
- Scalability requirements (load balancing, auto-scaling, CDNs)
- Data complexity (multiple databases, caching, analytics)
- Security requirements (authentication, authorization, compliance)
- DevOps practices (CI/CD, monitoring, deployment automation)
- Integration complexity (APIs, third-party services, distributed systems)
- Performance requirements (high traffic, real-time processing)

Classify as:
- LOW: Simple applications, basic functionality, minimal infrastructure needs
- MEDIUM: Moderate complexity, some advanced features, standard infrastructure
- HIGH: Complex systems, advanced architecture, enterprise-scale requirements

Base your assessment on the technical sophistication described, not just the presence of technical terms.

Respond with exactly "LOW", "MEDIUM", or "HIGH" - nothing else."""

    try:
        result = await openai_client.call_agent(
            "You are an expert at assessing software project technical complexity.",
            prompt,
            []  # No chat history needed for this analysis
        )
        result_upper = result.upper().strip()
        if result_upper in ["LOW", "MEDIUM", "HIGH"]:
            return result_upper.lower()
        else:
            return "medium"  # Default fallback
    except Exception as e:
        # Return medium complexity as safe default if LLM fails
        return "medium"

def format_summary(summary_data: Dict[str, Any]) -> str:
    """
    Format a summary dictionary into a readable string
    
    Args:
        summary_data: Dictionary containing summary information
        
    Returns:
        Formatted string representation of the summary
    """
    if not summary_data:
        return "No summary available"
    
    formatted = []
    for key, value in summary_data.items():
        if isinstance(value, dict):
            formatted.append(f"{key.title()}:")
            for sub_key, sub_value in value.items():
                formatted.append(f"  - {sub_key}: {sub_value}")
        else:
            formatted.append(f"{key.title()}: {value}")
    
    return "\n".join(formatted)

def validate_openai_response(response: str) -> bool:
    """
    Validate that an OpenAI response is reasonable and not empty
    
    Args:
        response: The response string from OpenAI
        
    Returns:
        True if the response appears valid, False otherwise
    """
    if not response or not response.strip():
        return False
    
    # Check minimum length (should be at least a sentence)
    if len(response.strip()) < 10:
        return False
    
    # Check for JSON-like structure if expected
    stripped = response.strip()
    if stripped.startswith('{') and not stripped.endswith('}'):
        return False
    
    return True



def clean_user_input(user_input: str) -> str:
    """
    Clean and normalize user input
    
    Args:
        user_input: Raw user input
        
    Returns:
        Cleaned input string
    """
    if not user_input:
        return ""
    
    # Strip whitespace
    cleaned = user_input.strip()
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned



def format_chat_history(chat_history: List[Dict[str, str]]) -> str:
    """
    Format chat history for display or processing
    
    Args:
        chat_history: List of chat messages
        
    Returns:
        Formatted chat history string
    """
    if not chat_history:
        return "No conversation history"
    
    formatted = []
    for message in chat_history:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        if role == "assistant":
            formatted.append(f"Agent: {content}")
        elif role == "user":
            formatted.append(f"User: {content}")
        else:
            formatted.append(f"{role.title()}: {content}")
    
    return "\n".join(formatted)



def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem usage
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized 

def get_user_input(prompt: str = "Your answer: ") -> str:
    """
    Simple user input function for prototype.
    
    Args:
        prompt: The prompt to display to the user
        
    Returns:
        Cleaned user input string
    """
    user_answer = input(prompt).strip()
    return clean_user_input(user_answer) 