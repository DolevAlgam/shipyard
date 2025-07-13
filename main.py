#!/usr/bin/env python3
"""
Shipyard - AI-powered Infrastructure Planning Assistant
Main entry point for the interview system
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.state_manager import StateManager
from core.openai_client import OpenAIClient
from agents.profiler import ProfilerAgent
from agents.business import BusinessAgent
from agents.app import AppAgent
from agents.tribal import TribalAgent
from agents.best_practices import BestPracticesAgent
from agents.document_generator import DocumentGeneratorAgent
from agents.feedback_interpreter import FeedbackInterpreterAgent

async def main():
    """Main interview loop"""
    print("🚢 Welcome to Shipyard - AI Infrastructure Planning Assistant")
    print("=" * 60)
    print()
    
    # Initialize components
    client = OpenAIClient()
    state_manager = StateManager()
    
    # Initialize agents
    profiler = ProfilerAgent(client, state_manager)
    business = BusinessAgent(client, state_manager)
    app = AppAgent(client, state_manager)
    tribal = TribalAgent(client, state_manager)
    best_practices = BestPracticesAgent(client, state_manager)
    document_generator = DocumentGeneratorAgent(client, state_manager)
    feedback_interpreter = FeedbackInterpreterAgent(client, state_manager)
    
    try:
        # Initialize state
        state = state_manager.initialize_state()
        
        print("I'll help you create a comprehensive infrastructure plan.")
        print("I'll ask about various aspects of your project.")
        print("Don't worry if you're not sure about something - just tell me what you know,")
        print("and I'll help fill in the gaps with best practices.")
        print("You can skip any question by saying 'skip' or 'I don't know'.")
        print()
        print("📝 Note: Please type your responses (avoid copy-pasting or multi-line text)")
        print()
        
        # Sequential pillar execution
        print("📋 Step 1: Understanding you and your project...")
        state = await profiler.run_pillar(state)
        
        print("\n💼 Step 2: Gathering business requirements...")
        state = await business.run_pillar(state)
        
        print("\n🖥️ Step 3: Understanding your application needs...")
        state = await app.run_pillar(state)
        
        print("\n🏢 Step 4: Learning about your organization...")
        state = await tribal.run_pillar(state)
        
        print("\n⭐ Step 5: Applying best practices...")
        state = await best_practices.run_pillar(state)
        
        print("\n📄 Step 6: Generating your infrastructure document...")
        document = await document_generator.generate_document(state)
        
        print("\n🎉 Your infrastructure plan is ready!")
        print("=" * 60)
        
        # Review and revision loop
        final_document = await review_loop(document, state, feedback_interpreter)
        
        # Save final document
        save_document(final_document)
        
        print("\n✅ All done! Your infrastructure plan has been saved.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interview interrupted. Your progress has been lost.")
        print("Run the program again to start over.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")
        print("Please try running the program again.")
        sys.exit(1)

async def review_loop(document, state, feedback_interpreter):
    """Handle document review and revision"""
    print("\nHere's your infrastructure plan:")
    print("-" * 40)
    print(document)
    print("-" * 40)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Save this document as-is")
        print("2. Request changes")
        print("3. View specific section")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            return document
        elif choice == "2":
            feedback = input("\nWhat changes would you like to make? ")
            if feedback.strip():
                print("Applying your feedback...")
                document = await feedback_interpreter.apply_feedback(document, feedback, state)
                print("\nUpdated document:")
                print("-" * 40)
                print(document)
                print("-" * 40)
        elif choice == "3":
            section = input("\nWhich section would you like to view? ")
            # TODO: Implement section viewing
            print("Section viewing not yet implemented.")
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def save_document(document):
    """Save the final document to a file"""
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"infrastructure_plan_{timestamp}.md"
    
    with open(filename, 'w') as f:
        f.write(document)
    
    print(f"Document saved as: {filename}")

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set it in your .env file or environment")
        sys.exit(1)
    
    asyncio.run(main()) 