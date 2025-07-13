"""
Reasoning Model Configuration for OpenAI o3 Integration
Defines which operations use reasoning models vs fast GPT-4o models
"""

from typing import Dict, Optional, List

# Configuration for which agents/operations use reasoning models
REASONING_AGENT_CONFIG = {
    # High-value reasoning operations - use o3 models for deep thinking
    'DocumentGeneratorAgent': {
        'model': 'o3', 
        'effort': 'high', 
        'reasoning_summary': 'detailed',
        'description': 'Document generation requires deep reasoning for infrastructure planning'
    },
    'ArchitectureAgent': {
        'model': 'o3', 
        'effort': 'high', 
        'reasoning_summary': 'detailed',
        'description': 'Architecture decisions need comprehensive analysis of trade-offs'
    },
    'ProfilerAgent': {
        'model': 'o3', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'User profiling requires reasoning about technical expertise and project context'
    },
    'BusinessAgent': {
        'model': 'o3', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Business requirements analysis benefits from structured reasoning'
    },
    'AppAgent': {
        'model': 'o3', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Application architecture decisions require systematic analysis'
    },
    'TribalAgent': {
        'model': 'o3', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Team dynamics and cultural factors need thoughtful reasoning'
    },
    'BestPracticesAgent': {
        'model': 'o3', 
        'effort': 'high', 
        'reasoning_summary': 'auto',
        'description': 'Best practices recommendations require structured analysis of options'
    },
    'SummarizerAgent': {
        'model': 'o3-mini', 
        'effort': 'high', 
        'reasoning_summary': 'auto',
        'description': 'Summarization benefits from reasoning about key insights and connections'
    },
    'FeedbackInterpreterAgent': {
        'model': 'o3', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Interpreting user feedback requires understanding nuanced communication'
    },
    
    # Upgraded operations to use reasoning models for better performance
    'follow_up_detection': {
        'model': 'o3-mini', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Enhanced follow-up detection using reasoning for better conversational flow'
    },
    'skip_detection': {
        'model': 'o3-mini', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Improved skip request identification using reasoning capabilities'
    },
    'expertise_extraction': {
        'model': 'o3-mini', 
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Enhanced expertise level assessment using reasoning'
    }
}

# Operation modes that can override agent defaults
OPERATION_MODE_CONFIG = {
    'document_generation': {
        'model': 'o3',
        'effort': 'high',
        'reasoning_summary': 'detailed',
        'description': 'Deep reasoning for comprehensive documentation'
    },
    'question_formulation': {
        'model': 'o3',
        'effort': 'medium', 
        'reasoning_summary': 'auto',
        'description': 'Context-aware intelligent question generation'
    },
    'architecture_recommendation': {
        'model': 'o3',
        'effort': 'high',
        'reasoning_summary': 'detailed',
        'description': 'Complex architectural decision making'
    },
    'fast_operation': {
        'model': 'gpt-4o',
        'effort': None,
        'reasoning_summary': None,
        'description': 'Fast operations for user experience'
    }
}

# Model capabilities and cost information
MODEL_INFO = {
    'o3': {
        'capabilities': 'Advanced reasoning, complex problem solving',
        'best_for': 'Document generation, architecture planning, complex decisions',
        'effort_levels': ['low', 'medium', 'high'],
        'cost_tier': 'high'
    },
    'o3-mini': {
        'capabilities': 'Good reasoning, faster than o3',
        'best_for': 'Question formulation, medium complexity analysis',
        'effort_levels': ['low', 'medium', 'high'],
        'cost_tier': 'medium'
    },
    'o4-mini': {
        'capabilities': 'Basic reasoning, very fast',
        'best_for': 'Simple reasoning tasks',
        'effort_levels': ['low', 'medium'],
        'cost_tier': 'low'
    },
    'gpt-4o': {
        'capabilities': 'Standard language model, very fast',
        'best_for': 'Follow-ups, skip detection, summarization, simple Q&A',
        'effort_levels': None,
        'cost_tier': 'low'
    },
    'gpt-4o-mini': {
        'capabilities': 'Standard language model, extremely fast',
        'best_for': 'Simple operations, basic text processing',
        'effort_levels': None,
        'cost_tier': 'very_low'
    }
}

def get_agent_config(agent_name: str) -> Dict[str, Optional[str]]:
    """Get configuration for a specific agent"""
    return REASONING_AGENT_CONFIG.get(agent_name, {
        'model': 'gpt-4o',
        'effort': None,
        'reasoning_summary': None,
        'description': 'Default configuration'
    })

def get_operation_config(operation_mode: str) -> Dict[str, Optional[str]]:
    """Get configuration for a specific operation mode"""
    # First check REASONING_AGENT_CONFIG for fast operations like skip_detection, follow_up_detection
    if operation_mode in REASONING_AGENT_CONFIG:
        return REASONING_AGENT_CONFIG[operation_mode]
    
    # Then check OPERATION_MODE_CONFIG for other operation modes
    return OPERATION_MODE_CONFIG.get(operation_mode, {
        'model': 'gpt-4o',
        'effort': None,
        'reasoning_summary': None,
        'description': 'Default operation'
    })

def is_reasoning_model(model: str) -> bool:
    """Check if a model is a reasoning model"""
    return model in ['o3', 'o3-mini', 'o4-mini']

def get_supported_reasoning_models() -> List[str]:
    """Get list of supported reasoning models"""
    return ['o3', 'o3-mini', 'o4-mini']

def get_legacy_models() -> List[str]:
    """Get list of legacy (non-reasoning) models"""
    return ['gpt-4o', 'gpt-4o-mini'] 