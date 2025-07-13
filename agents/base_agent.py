from abc import ABC, abstractmethod
from typing import Dict, List

class BaseAgent(ABC):
    def __init__(self, name: str, topics: List[str], prompt: str):
        self.name = name
        self.topics = topics
        self.prompt = prompt
    
    @abstractmethod
    async def process_topic(self, topic: str, state: Dict, openai_client) -> Dict:
        """Process a single topic using LLM-based analysis"""
        pass 