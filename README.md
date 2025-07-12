# Functional and Technical Specification - Shipyard MVP

## Project Overview

Shipyard is an AI-powered infrastructure planning assistant that interviews engineers about their infrastructure needs and automatically generates a comprehensive infrastructure planning document. The system adapts its questioning based on the user's expertise level and progressively builds a detailed infrastructure plan.

## Goals and Objectives

### Primary Goals
1. **Simplify Infrastructure Planning**: Guide users through infrastructure decisions without requiring deep technical knowledge
2. **Adaptive Interviewing**: Adjust question complexity based on user expertise
3. **Comprehensive Output**: Generate a detailed infrastructure planning document covering all aspects from architecture to security

### MVP Objectives
- Implement a working prototype using plain Python and OpenAI SDK
- Sequential interview flow through multiple specialized agents
- Generate a complete infrastructure planning markdown document
- Allow users to review and request changes to the final document

## Technical Architecture

### Technology Stack
- **Language**: Python 3.11+
- **LLM**: OpenAI GPT-4o (via OpenAI SDK)
- **Framework**: None (plain Python for MVP)
- **Future Consideration**: Migration to LangGraph for complex workflows

### High-Level Architecture

```
[User] <-> [Main Interview Loop] <-> [OpenAI API]
               |
               v
        [Agent Controllers]
               |
               v
        [State Management]
               |
               v
        [Document Generation]
```

## Agent Definitions and Responsibilities

The flow between agents is illustrated in the diagram below, showing how the Question Agent and Summarizer Agent support the core interview agents throughout the process.

### Core Interview Agents

1. **Profiler Agent**
   - **Purpose**: Assess user's technical expertise and project context
   - **Output**: User expertise level (novice/intermediate/advanced), project type, company context
   - **Topics**: Experience level, project overview, personal vs company use

2. **Business Needs Agent**
   - **Purpose**: Gather business requirements and constraints
   - **Output**: Scale requirements, uptime needs, budget, compliance requirements
   - **Topics**: User scale, availability requirements, performance expectations, budget constraints

3. **App Needs Agent**
   - **Purpose**: Collect technical application requirements
   - **Output**: Tech stack, deployment preferences, data needs
   - **Topics**: Application type, programming languages, databases, external integrations

4. **Tribal Knowledge Agent**
   - **Purpose**: Understand organizational constraints and preferences
   - **Output**: Required tools, existing infrastructure, team preferences
   - **Topics**: Cloud provider preferences, existing tools, security requirements

5. **Best Practices Agent**
   - **Purpose**: Fill gaps with industry best practices
   - **Output**: Default configurations for unspecified requirements
   - **Topics**: Network policies, monitoring, security defaults, disaster recovery

### Support Agents

6. **Question Agent**
   - **Purpose**: Formulate appropriate questions based on user expertise and context
   - **Input**: Topic, user expertise level, previous answers
   - **Output**: 1-3 questions with skip options

7. **Summarizer Agent**
   - **Purpose**: Extract key information after each pillar completes
   - **Input**: Chat history from a pillar
   - **Output**: Structured summary of requirements gathered

8. **Document Generator Agent**
   - **Purpose**: Create the final infrastructure planning document
   - **Input**: All collected requirements and summaries
   - **Output**: Comprehensive markdown document

9. **Feedback Interpreter Agent**
   - **Purpose**: Understand and apply user revision requests
   - **Input**: User feedback on document
   - **Output**: Specific changes to apply

## Data Flow and State Management

### State Structure
```python
state = {
    "chat_history": [],  # Full conversation for context
    "extracted_info": {  # LLM-summarized key points
        "user_profile": {
            "expertise_level": None,  # "novice", "intermediate", "advanced"
            "project_type": None,     # "personal", "startup", "enterprise"
            "domain": None            # "web", "ml", "data", etc.
        },
        "business_context": {},
        "technical_requirements": {},
        "organizational_constraints": {},
        "assumptions_made": []
    },
    "current_document": {}  # Incrementally built sections
}
```

### Flow Diagram
![Shipyard Agent Flow Diagram](shipyard_agent_flow.png)

## User Experience Flow

### Interview Process
1. **Welcome & Context Setting**
   ```
   "I'll help you create a comprehensive infrastructure plan. I'll ask about various aspects 
   of your project. Don't worry if you're not sure about something - just tell me what you 
   know, and I'll help fill in the gaps with best practices. You can skip any question 
   by saying 'skip' or 'I don't know'."
   ```

2. **Adaptive Questioning**
   - Start with general questions for all users
   - Dig deeper based on demonstrated expertise
   - Always provide skip option
   - Show empathy for non-technical users

3. **Progressive Document Building**
   - Show document sections as they're completed
   - User sees progress throughout the interview
   - Final review and editing phase

4. **Review Loop**
   - Present complete document
   - Accept natural language feedback
   - Apply changes and regenerate sections
   - Repeat until user approves

## Implementation Details

### Main Flow Structure
```python
async def run_interview():
    state = initialize_state()
    
    # Run each pillar in sequence
    state = await run_pillar("profiler", PROFILER_TOPICS, state)
    state = await run_pillar("business", BUSINESS_TOPICS, state)
    state = await run_pillar("app", APP_TOPICS, state)
    state = await run_pillar("tribal", TRIBAL_TOPICS, state)
    
    # Apply best practices to fill gaps
    state = await apply_best_practices(state)
    
    # Generate complete document
    doc = await generate_document(state)
    
    # Review and revision loop
    final_doc = await review_loop(doc, state)
    
    return final_doc

async def run_pillar(pillar_name, topics, state):
    agent_prompt = AGENT_PROMPTS[pillar_name]
    
    for topic in topics:
        # Use question agent to formulate questions
        questions = await ask_question_agent(topic, state)
        
        # Get user answers
        answers = await get_user_input(questions)
        
        # Update state
        state["chat_history"].extend([
            {"role": "assistant", "content": questions},
            {"role": "user", "content": answers}
        ])
    
    # Summarize after pillar completes
    state["extracted_info"][pillar_name] = await summarize_pillar(
        pillar_name, 
        state["chat_history"]
    )
    
    return state
```

### Topic Lists

```python
PROFILER_TOPICS = [
    "expertise_assessment",
    "project_overview",
    "project_scale",
    "timeline"
]

BUSINESS_TOPICS = [
    "user_base",
    "traffic_patterns",
    "availability_requirements",
    "performance_sla",
    "budget_constraints",
    "compliance_requirements",
    "geographic_distribution"
]

APP_TOPICS = [
    "application_type",
    "programming_languages",
    "frameworks",
    "database_requirements",
    "storage_needs",
    "external_integrations",
    "api_requirements",
    "deployment_model"
]

TRIBAL_TOPICS = [
    "cloud_provider",
    "existing_tools",
    "team_expertise",
    "security_policies",
    "operational_preferences",
    "development_workflow"
]

INFRASTRUCTURE_CHECKLIST = [
    # Compute
    "compute_resources",
    "auto_scaling",
    "load_balancing",
    
    # Networking
    "network_architecture",
    "security_groups",
    "vpn_requirements",
    "cdn_needs",
    
    # Storage
    "database_setup",
    "object_storage",
    "backup_strategy",
    
    # Security
    "authentication",
    "authorization",
    "encryption",
    "secrets_management",
    
    # Monitoring
    "logging_strategy",
    "metrics_collection",
    "alerting_rules",
    
    # Disaster Recovery
    "backup_frequency",
    "recovery_objectives",
    "multi_region_strategy",
    
    # CI/CD
    "deployment_pipeline",
    "testing_strategy",
    "rollback_procedures"
]
```

## System Prompts

### Question Agent Prompt
```python
QUESTION_AGENT_PROMPT = """
You are a question formulation expert for infrastructure planning. Given a topic and user context, create 1-3 questions that are appropriate for the user's expertise level.

Rules:
1. If expertise is unknown/low, start with general framing: "How important is [topic] for your project?"
2. Follow with specific questions only if the user shows understanding
3. Always add: "(Feel free to skip if you don't know or this doesn't apply)"
4. Use simple, jargon-free language for novice users
5. Be more technical and specific for advanced users

Context:
- User expertise: {expertise_level}
- Topic: {topic}
- Previous answers: {context}

Examples for different expertise levels:

Novice + Security:
"How important is security for your application? For example, will you be handling sensitive user data? (Feel free to skip if unsure)"

Intermediate + Scaling:
"What kind of traffic patterns do you expect? Will usage be steady or have peaks? Any specific scaling requirements you've considered?"

Advanced + Networking:
"What are your requirements for network segmentation? Do you need specific ingress/egress rules or VPN connectivity?"

Generate questions for the topic: {topic}
"""

PROFILER_AGENT_PROMPT = """
You are a friendly infrastructure planning assistant starting an interview. Your goal is to understand:
1. The user's technical expertise level
2. What kind of project this is for
3. Basic scale and timeline

Be warm and encouraging. Make it clear that no technical knowledge is required.

Start with:
"Hi! I'm here to help you create a comprehensive infrastructure plan. First, let me learn a bit about you and your project.

Could you tell me:
1. What's your experience level with cloud infrastructure? (Beginner/Some experience/Expert)
2. What kind of project is this for? (Personal project/Startup/Company)
3. Can you briefly describe what you're building?
4. When do you hope to launch?"

Assess their expertise from their language and technical detail, not just their self-assessment.
"""

BEST_PRACTICES_PROMPT = """
You are an infrastructure best practices expert. Review the collected requirements and identify any gaps that need to be filled with sensible defaults.

For any missing requirements, add industry best practices with clear notation: "[AI Recommendation: ...]"

Consider ALL aspects from this checklist:
{infrastructure_checklist}

Current requirements:
{requirements}

Fill in missing pieces with practical, cost-effective defaults appropriate for their project scale and expertise level.
"""

DOCUMENT_GENERATOR_PROMPT = """
You are creating a comprehensive infrastructure planning document. Use the collected requirements to generate a detailed markdown document with these sections:

1. Executive Summary
2. Architecture Overview
3. Compute Resources
4. Networking Configuration
5. Storage Solutions
6. Security Measures
7. Monitoring and Observability
8. Disaster Recovery Plan
9. CI/CD Pipeline
10. Cost Estimates
11. Implementation Timeline
12. Assumptions and Recommendations

For each section:
- Use clear headings and subheadings
- Include specific configurations and services
- Note which decisions came from the user vs AI recommendations
- Add helpful diagrams where appropriate (using mermaid syntax)

Requirements:
{all_requirements}

Generate a professional, actionable infrastructure plan.
"""
```

## Document Structure

### Infrastructure Plan Sections
1. **Executive Summary** - High-level overview of the infrastructure design
2. **Architecture Overview** - System architecture with diagrams
3. **Compute Resources** - Servers, containers, serverless functions
4. **Networking Configuration** - VPC, subnets, load balancers, CDN
5. **Storage Solutions** - Databases, object storage, file systems
6. **Security Measures** - IAM, encryption, compliance, secrets management
7. **Monitoring and Observability** - Logging, metrics, alerts, dashboards
8. **Disaster Recovery Plan** - Backups, failover, RTO/RPO
9. **CI/CD Pipeline** - Build, test, deploy processes
10. **Cost Estimates** - Monthly/annual cost projections
11. **Implementation Timeline** - Phased rollout plan
12. **Assumptions and Recommendations** - AI-filled gaps and suggestions

## MVP Scope

### Included in MVP
- Sequential interview flow
- Adaptive questioning based on expertise
- All five core agents (Profiler, Business, App, Tribal, Best Practices)
- Support agents (Question, Summarizer, Document Generator, Feedback Interpreter)
- Incremental document building
- Single review/revision loop
- Plain Python implementation
- OpenAI GPT-4o integration

### Excluded from MVP (Future Enhancements)
- Web search capabilities
- Checkpointing/resume functionality
- Complex routing between agents
- Reflection loops within pillars
- Multiple LLM support
- Terraform/IaC generation
- Real-time collaboration
- Version control for documents

## Error Handling and Edge Cases

### User Abandonment
- Save state periodically (future enhancement)
- For MVP: Warn users that closing will lose progress

### Unclear Answers
- Question Agent should detect ambiguity
- Follow up with clarifying questions
- Mark assumptions clearly in document

### Technical Errors
- OpenAI API failures: Implement exponential backoff
- Rate limiting: Add delays between API calls
- Malformed responses: Basic retry logic

## Success Metrics

### MVP Success Criteria
1. Complete interview in < 15 minutes
2. Generate comprehensive 10+ page infrastructure document
3. Cover all infrastructure checklist items
4. Successful adaptation to different expertise levels
5. User can review and request changes

### Quality Metrics
- Document completeness (all sections filled)
- Assumption ratio (user-provided vs AI-filled)
- User satisfaction with final document
- Time to completion

## Development Timeline

### Phase 1: Core Implementation (Week 1)
- Basic state management
- Question Agent with adaptive prompting
- Profiler and Business agents
- Simple console interface

### Phase 2: Agent Development (Week 2)
- App, Tribal, and Best Practices agents
- Summarizer Agent
- Incremental document building

### Phase 3: Document Generation (Week 3)
- Document Generator Agent
- Feedback Interpreter Agent
- Review loop implementation
- Polish and testing

## Future Roadmap

1. **LangGraph Migration** - For complex workflows and better state management
2. **Web Search Integration** - For latest best practices and pricing
3. **IaC Generation** - Terraform/CloudFormation output
4. **Collaboration Features** - Multiple stakeholders input
5. **Template Library** - Pre-built patterns for common architectures
6. **Cost Optimization** - Real-time cost analysis and recommendations
7. **Compliance Modules** - HIPAA, SOC2, GDPR specific guidance

## Appendix A: Example User Journey

### Novice User - Personal Blog
```
Profiler: "What's your experience with cloud infrastructure?"
User: "I've only used shared hosting before"
[System notes: expertise_level = novice]

Business: "How many visitors do you expect for your blog?"
User: "Maybe 1000 per month?"
[System adapts to simple questions]

App: "What platform will your blog use? WordPress, custom code, or something else?"
User: "WordPress"
[System fills in typical WordPress infrastructure needs]

Final document includes beginner-friendly explanations and managed service recommendations.
```

### Advanced User - SaaS Platform
```
Profiler: "What's your experience with cloud infrastructure?"
User: "I've architected several microservices platforms on AWS"
[System notes: expertise_level = advanced]

Business: "What are your specific SLA requirements?"
User: "99.95% uptime, <100ms p95 latency, SOC2 compliance needed"
[System asks detailed technical questions]

App: "What's your microservices communication pattern? REST, gRPC, event-driven?"
User: "Event-driven with Kafka, some synchronous gRPC for critical paths"
[System dives deep into technical specifications]

Final document includes detailed technical specifications and advanced patterns.
```

## Appendix B: Quick Start Guide for Developers

```bash
# Clone repository
git clone https://github.com/yourorg/shipyard.git
cd shipyard

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Run the interview
python main.py

# For development
python main.py --debug --mock-llm
```

## Contact and Support

- Project Lead: [Your Name]
- Technical Questions: [Email/Slack]
- Repository: [GitHub URL]

---

*This document is version 1.0 of the Shipyard MVP specification. Last updated: [Current Date]* 