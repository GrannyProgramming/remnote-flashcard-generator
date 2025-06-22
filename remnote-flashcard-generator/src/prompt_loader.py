"""
Prompt Template Loader for Card Generation

This module loads and manages YAML-based prompt templates for different card types,
providing a clean separation between prompt content and Python logic.
"""

from typing import Dict, Any, Optional
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """
    Load and manage prompt templates from YAML files.
    
    This class provides a centralized way to load prompt templates,
    allowing for easy maintenance and customization of prompts without
    modifying Python code.
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt YAML files
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent / "prompts"
        
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Validate prompts directory exists
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
    
    def load_prompt(self, card_type: str) -> Dict[str, Any]:
        """
        Load prompt template for specified card type.
        
        Args:
            card_type: Type of card (concept, basic, cloze, descriptor)
            
        Returns:
            Dictionary containing prompt template and configuration
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
            ValueError: If prompt file is malformed
        """
        # Check cache first
        if card_type in self._cache:
            return self._cache[card_type]
        
        prompt_file = self.prompts_dir / f"{card_type}_card.yaml"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_data = yaml.safe_load(f)
            
            # Validate required fields
            required_fields = ['system_prompt', 'user_prompt', 'config']
            for field in required_fields:
                if field not in prompt_data:
                    raise ValueError(f"Missing required field '{field}' in {prompt_file}")
            
            # Cache the loaded prompt
            self._cache[card_type] = prompt_data
            logger.debug(f"Loaded prompt template for {card_type} cards")
            
            return prompt_data
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {prompt_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading prompt {prompt_file}: {e}")
    
    def get_system_prompt(self, card_type: str) -> str:
        """Get system prompt for card type."""
        prompt_data = self.load_prompt(card_type)
        return prompt_data['system_prompt'].strip()
    
    def get_user_prompt(self, card_type: str) -> str:
        """Get user prompt template for card type."""
        prompt_data = self.load_prompt(card_type)
        return prompt_data['user_prompt'].strip()
    
    def get_config(self, card_type: str) -> Dict[str, Any]:
        """Get configuration for card type."""
        prompt_data = self.load_prompt(card_type)
        return prompt_data['config']
    
    def format_prompt(self, card_type: str, **kwargs) -> str:
        """
        Format user prompt with provided variables.
        
        Args:
            card_type: Type of card
            **kwargs: Variables to substitute in prompt template
            
        Returns:
            Formatted prompt string
        """
        prompt_template = self.get_user_prompt(card_type)
        
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable {e} for {card_type} prompt")
            raise ValueError(f"Missing required variable {e} for {card_type} prompt")
    
    def reload_prompts(self):
        """Clear cache and reload all prompts."""
        self._cache.clear()
        logger.info("Prompt cache cleared - will reload on next access")
    
    def list_available_prompts(self) -> list[str]:
        """List all available prompt types."""
        prompt_files = list(self.prompts_dir.glob("*_card.yaml"))
        return [f.stem.replace("_card", "") for f in prompt_files]


def main():
    """Demo function for prompt loader."""
    loader = PromptLoader()
    
    print("Available prompt types:")
    for prompt_type in loader.list_available_prompts():
        print(f"  - {prompt_type}")
    
    # Example usage
    try:
        concept_config = loader.get_config("concept")
        print(f"\nConcept card config: {concept_config}")
        
        formatted_prompt = loader.format_prompt(
            "concept",
            context_info=" (part of Data Processing)",
            topic_name="Lambda Architecture", 
            content="Lambda architecture combines batch and stream processing..."
        )
        print(f"\nFormatted prompt preview:\n{formatted_prompt[:200]}...")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
