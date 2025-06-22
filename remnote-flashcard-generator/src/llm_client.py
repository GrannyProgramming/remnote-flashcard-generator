"""
LLM Client Abstraction for Multiple Providers

This module provides a unified interface for different LLM providers (OpenAI and Anthropic),
handling API calls, retry logic, token counting, and rate limiting.
"""

from typing import List, Dict, Optional, Union, Any
from abc import ABC, abstractmethod
import os
import time
import logging
from dataclasses import dataclass
from enum import Enum
import asyncio
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: LLMProvider
    model: str
    api_key: str
    temperature: float = 0.3
    max_tokens: int = 2000
    retry_attempts: int = 3
    retry_delay: float = 2.0
    timeout: float = 30.0


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class RateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass


class TokenLimitError(LLMError):
    """Raised when token limit is exceeded."""
    pass


class LLMClient(ABC):
    """
    Abstract base class for LLM clients.
    
    This provides a unified interface for different LLM providers,
    abstracting away provider-specific implementation details.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM client with configuration.
        
        Args:
            config: LLM configuration object
        """
        self.config = config
        self.total_tokens_used = 0
        self.request_count = 0
        self.last_request_time = 0.0
    
    @abstractmethod
    def generate(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate response from prompt.
        
        Args:
            prompt: Input prompt for generation
            temperature: Sampling temperature (overrides config if provided)
            
        Returns:
            Generated response text
            
        Raises:
            LLMError: If generation fails
            RateLimitError: If rate limit exceeded
            TokenLimitError: If token limit exceeded
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    def _handle_rate_limiting(self) -> None:
        """
        Handle rate limiting between requests.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        # Minimum delay between requests (adjust based on provider limits)
        min_delay = 0.1  # 100ms minimum
        
        if time_since_last_request < min_delay:
            sleep_time = min_delay - time_since_last_request
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            LLMError: If all retry attempts fail
        """
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limit hit, retrying in {delay}s (attempt {attempt + 1})")
                    time.sleep(delay)
                else:
                    raise
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    raise LLMError(f"All retry attempts failed: {e}") from e
        
        raise LLMError(f"All retry attempts failed: {last_exception}") from last_exception


class OpenAIClient(LLMClient):
    """
    OpenAI API client implementation.
    
    Supports GPT-3.5, GPT-4, and other OpenAI models with proper token counting
    and error handling.
    
    Example:
        >>> config = LLMConfig(LLMProvider.OPENAI, "gpt-4", api_key="your-key")
        >>> client = OpenAIClient(config)
        >>> response = client.generate("Explain machine learning")
        >>> print(response)
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize OpenAI client."""
        super().__init__(config)
        
        try:
            import openai
            import tiktoken
            self.openai = openai
            self.tiktoken = tiktoken
        except ImportError as e:
            raise LLMError(f"OpenAI dependencies not installed: {e}")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=config.api_key)
        
        # Initialize tokenizer for the model
        try:
            self.encoding = tiktoken.encoding_for_model(config.model)
        except KeyError:
            # Fallback to a default encoding
            logger.warning(f"No tokenizer found for {config.model}, using cl100k_base")
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def generate(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate response using OpenAI API.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        temp = temperature if temperature is not None else self.config.temperature
        
        # Check token count
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > self.config.max_tokens * 0.8:  # Leave room for response
            raise TokenLimitError(f"Prompt too long: {prompt_tokens} tokens")
        
        def _make_request():
            self._handle_rate_limiting()
            
            try:
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates high-quality educational flashcards."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temp,
                    max_tokens=self.config.max_tokens - prompt_tokens,
                    timeout=self.config.timeout
                )
                
                # Update usage statistics
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens_used += response.usage.total_tokens
                
                self.request_count += 1
                
                return response.choices[0].message.content
                
            except Exception as e:
                if "rate_limit" in str(e).lower():
                    raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
                elif "timeout" in str(e).lower():
                    raise LLMError(f"OpenAI request timeout: {e}")
                else:
                    raise LLMError(f"OpenAI API error: {e}")
        
        return self._retry_with_backoff(_make_request)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token counting failed, using estimate: {e}")
            # Rough estimate: ~4 characters per token
            return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get OpenAI model information."""
        return {
            "provider": "OpenAI",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "total_tokens_used": self.total_tokens_used,
            "request_count": self.request_count
        }


class AnthropicClient(LLMClient):
    """
    Anthropic API client implementation.
    
    Supports Claude models with proper token counting and error handling.
    
    Example:
        >>> config = LLMConfig(LLMProvider.ANTHROPIC, "claude-3-sonnet-20240229", api_key="your-key")
        >>> client = AnthropicClient(config)
        >>> response = client.generate("Explain machine learning")
        >>> print(response)
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize Anthropic client."""
        super().__init__(config)
        
        try:
            import anthropic
            self.anthropic = anthropic
        except ImportError as e:
            raise LLMError(f"Anthropic dependencies not installed: {e}")
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=config.api_key)
    
    def generate(self, prompt: str, temperature: Optional[float] = None) -> str:
        """
        Generate response using Anthropic API.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        temp = temperature if temperature is not None else self.config.temperature
        
        # Check token count (rough estimate for Claude)
        prompt_tokens = self.count_tokens(prompt)
        if prompt_tokens > self.config.max_tokens * 0.8:
            raise TokenLimitError(f"Prompt too long: {prompt_tokens} tokens")
        
        def _make_request():
            self._handle_rate_limiting()
            
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens - prompt_tokens,
                    temperature=temp,
                    system="You are a helpful assistant that generates high-quality educational flashcards.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Update usage statistics
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens_used += response.usage.input_tokens + response.usage.output_tokens
                
                self.request_count += 1
                
                return response.content[0].text
                
            except Exception as e:
                if "rate_limit" in str(e).lower():
                    raise RateLimitError(f"Anthropic rate limit exceeded: {e}")
                elif "timeout" in str(e).lower():
                    raise LLMError(f"Anthropic request timeout: {e}")
                else:
                    raise LLMError(f"Anthropic API error: {e}")
        
        return self._retry_with_backoff(_make_request)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Claude (approximation).
        
        Args:
            text: Text to count
            
        Returns:
            Approximate number of tokens
        """
        try:
            # Claude uses a different tokenizer, so we approximate
            # Based on Anthropic's documentation: ~3.5 characters per token
            return int(len(text) / 3.5)
        except Exception as e:
            logger.warning(f"Token counting failed, using estimate: {e}")
            return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Anthropic model information."""
        return {
            "provider": "Anthropic",
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "total_tokens_used": self.total_tokens_used,
            "request_count": self.request_count
        }


def create_llm_client(provider: str = "anthropic", model: Optional[str] = None, **kwargs) -> LLMClient:
    """
    Factory function to create appropriate LLM client.
    
    Args:
        provider: LLM provider ("openai" or "anthropic")
        model: Model name (uses defaults if not provided)
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLM client instance
        
    Raises:
        ValueError: If provider is not supported
        LLMError: If configuration is invalid
        
    Example:
        >>> client = create_llm_client("openai", model="gpt-4")
        >>> response = client.generate("Hello, world!")
    """
    provider_enum = LLMProvider(provider.lower())
    
    # Get API key from environment or kwargs
    if provider_enum == LLMProvider.OPENAI:
        api_key = kwargs.get('api_key') or os.getenv('OPENAI_API_KEY')
        default_model = model or "gpt-4"
        if not api_key:
            raise LLMError("OpenAI API key not found in environment or kwargs")
    elif provider_enum == LLMProvider.ANTHROPIC:
        api_key = kwargs.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
        default_model = model or "claude-3-sonnet-20240229"
        if not api_key:
            raise LLMError("Anthropic API key not found in environment or kwargs")
    else:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # Create configuration
    config = LLMConfig(
        provider=provider_enum,
        model=default_model,
        api_key=api_key,
        temperature=kwargs.get('temperature', 0.3),
        max_tokens=kwargs.get('max_tokens', 2000),
        retry_attempts=kwargs.get('retry_attempts', 3),
        retry_delay=kwargs.get('retry_delay', 2.0),
        timeout=kwargs.get('timeout', 30.0)
    )
    
    # Create appropriate client
    if provider_enum == LLMProvider.OPENAI:
        return OpenAIClient(config)
    elif provider_enum == LLMProvider.ANTHROPIC:
        return AnthropicClient(config)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def test_llm_connection(client: LLMClient) -> bool:
    """
    Test LLM connection with a simple request.
    
    Args:
        client: LLM client to test
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response = client.generate("Hello, please respond with 'Connection successful!'")
        return "connection successful" in response.lower()
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def main():
    """
    Demo function showing LLM client usage.
    """
    console.print("[bold blue]LLM Client Demo[/bold blue]")
    
    try:
        # Try to create an Anthropic client
        client = create_llm_client("anthropic")
        console.print("✓ Anthropic client created successfully")
        
        # Test connection
        if test_llm_connection(client):
            console.print("✓ Connection test passed")
        else:
            console.print("[yellow]⚠ Connection test failed[/yellow]")
        
        # Show model info
        info = client.get_model_info()
        console.print(f"Model: {info['model']}")
        console.print(f"Provider: {info['provider']}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure to set your API key in .env file[/yellow]")


if __name__ == "__main__":
    main()
