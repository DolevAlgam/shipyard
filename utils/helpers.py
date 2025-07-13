"""
Helper functions for the Shipyard interview system
"""

import json
import re
from typing import Dict, List, Any, Optional

async def needs_follow_up_llm(user_answer: str, question: str, openai_client) -> bool:
    """
    Determine if user's answer indicates they need clarification or follow-up using LLM analysis
    
    Args:
        user_answer: The user's response to a question
        question: The original question that was asked
        openai_client: OpenAI client for LLM analysis
        
    Returns:
        True if the answer suggests confusion or need for clarification
    """
    prompt = f"""You are analyzing a conversation to determine if a follow-up question is needed.

QUESTION ASKED: {question}
USER RESPONSE: {user_answer}

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
            "You are a conversation analysis expert.",
            prompt,
            []  # No chat history needed for this analysis
        )
        return "FOLLOW_UP_NEEDED" in result.upper()
    except Exception as e:
        # Fallback to basic heuristics if LLM fails
        return len(user_answer.strip()) < 3 or "?" in user_answer



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
    
    # Check for common error patterns
    error_patterns = [
        "i apologize, but i'm having trouble",
        "error",
        "failed to",
        "unable to",
        "connection",
        "try again"
    ]
    
    response_lower = response.lower()
    for pattern in error_patterns:
        if pattern in response_lower:
            return False
    
    # Check minimum length (should be at least a sentence)
    if len(response.strip()) < 10:
        return False
    
    return True

def extract_expertise_level(user_input: str) -> Optional[str]:
    """
    Extract expertise level from user input
    
    Args:
        user_input: User's response about their expertise
        
    Returns:
        Detected expertise level or None if not clear
    """
    input_lower = user_input.lower()
    
    # Check for explicit mentions
    if any(word in input_lower for word in ["beginner", "new", "novice", "never", "first time"]):
        return "novice"
    elif any(word in input_lower for word in ["intermediate", "some", "bit of", "limited", "learning"]):
        return "intermediate"
    elif any(word in input_lower for word in ["advanced", "expert", "professional", "years", "experienced"]):
        return "advanced"
    
    return None

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
    
    # Handle common skip phrases
    skip_phrases = ["skip", "i don't know", "idk", "not sure", "pass", "next"]
    if cleaned.lower() in skip_phrases:
        return "skip"
    
    return cleaned

def is_skip_response(user_input: str) -> bool:
    """
    Check if user wants to skip a question
    
    Args:
        user_input: User's response
        
    Returns:
        True if user wants to skip, False otherwise
    """
    skip_phrases = [
        "skip", "i don't know", "idk", "not sure", "pass", "next", 
        "don't know", "no idea", "unclear", "not applicable", "n/a"
    ]
    
    cleaned = clean_user_input(user_input).lower()
    return cleaned in skip_phrases

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

def detect_technical_complexity(text: str) -> str:
    """
    Analyze text to detect technical complexity level
    
    Args:
        text: User's description or response
        
    Returns:
        Detected complexity level: "low", "medium", or "high"
    """
    text_lower = text.lower()
    
    # Technical terms that indicate higher complexity
    advanced_terms = [
        "microservices", "kubernetes", "docker", "containerization", 
        "cicd", "devops", "terraform", "infrastructure as code",
        "load balancer", "auto scaling", "cdn", "api gateway",
        "database sharding", "caching", "redis", "elasticsearch",
        "monitoring", "logging", "metrics", "alerts",
        "security", "authentication", "authorization", "oauth"
    ]
    
    intermediate_terms = [
        "database", "api", "backend", "frontend", "server",
        "hosting", "deployment", "scaling", "performance",
        "users", "traffic", "availability", "backup"
    ]
    
    # Count technical terms
    advanced_count = sum(1 for term in advanced_terms if term in text_lower)
    intermediate_count = sum(1 for term in intermediate_terms if term in text_lower)
    
    if advanced_count >= 2:
        return "high"
    elif intermediate_count >= 3 or advanced_count >= 1:
        return "medium"
    else:
        return "low"

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