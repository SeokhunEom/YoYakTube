"""
LLM client implementations for YoYakTube

Provides OpenAI client and factory functions for LLM interactions.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import openai
import os


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "system", "user", or "assistant"
    content: str


@dataclass 
class ChatResponse:
    """Represents a chat response from LLM."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class LLMClient:
    """Base LLM client interface."""
    
    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        """Send chat messages and get response."""
        raise NotImplementedError


class OpenAIClient(LLMClient):
    """OpenAI API client implementation."""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., "gpt-4", "gpt-3.5-turbo")
        """
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    def chat(self, messages: List[ChatMessage], temperature: float = 0.2) -> ChatResponse:
        """
        Send chat messages to OpenAI and get response.
        
        Args:
            messages: List of ChatMessage objects
            temperature: Sampling temperature (0.0 to 2.0)
            
        Returns:
            ChatResponse with the model's reply
        """
        try:
            # Convert ChatMessage objects to OpenAI format
            openai_messages = []
            for msg in messages:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=temperature
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Extract usage information if available
            usage = None
            if hasattr(response, 'usage') and response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return ChatResponse(
                content=content,
                model=self.model,
                usage=usage
            )
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API call failed: {str(e)}")


def get_or_create_llm(provider: str, model: str, openai_key: str) -> LLMClient:
    """
    Create LLM client instance.
    
    Args:
        provider: LLM provider ("openai")
        model: Model name
        openai_key: OpenAI API key
        
    Returns:
        LLMClient instance
        
    Raises:
        ValueError: If provider is not supported
        RuntimeError: If client creation fails
    """
    if provider.lower() == "openai":
        if not openai_key:
            raise ValueError("OpenAI API key is required")
        return OpenAIClient(openai_key, model)
    else:
        raise ValueError(f"Unsupported provider: {provider}. Only 'openai' is supported.")