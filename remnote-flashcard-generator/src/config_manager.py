"""
Configuration Management Module

Handles loading, validation, and management of application configuration.
Provides type-safe access to configuration values with validation.
"""

import yaml
import jsonschema
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    provider: str
    model: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 2000
    retry_attempts: int = 3
    retry_delay: float = 2.0


@dataclass
class RemNoteConfig:
    """Configuration for RemNote integration."""
    default_folder: str = "ML System Design"
    include_hierarchy: bool = True


@dataclass
class CardsPerConceptConfig:
    """Configuration for cards per concept generation."""
    min: int = 3
    max: int = 5


@dataclass
class CardTypesConfig:
    """Configuration for enabled card types."""
    concept: bool = True
    basic: bool = True
    cloze: bool = True
    descriptor: bool = True


@dataclass
class DifficultyDistributionConfig:
    """Configuration for difficulty distribution."""
    beginner: float = 0.3
    intermediate: float = 0.5
    advanced: float = 0.2
    
    def __post_init__(self):
        """Validate that distribution sums to 1.0."""
        total = self.beginner + self.intermediate + self.advanced
        if abs(total - 1.0) > 0.01:  # Allow small floating point differences
            logger.warning(f"Difficulty distribution sums to {total}, not 1.0")


@dataclass
class GenerationConfig:
    """Configuration for card generation."""
    cards_per_concept: CardsPerConceptConfig = field(default_factory=CardsPerConceptConfig)
    card_types: CardTypesConfig = field(default_factory=CardTypesConfig)
    include_examples: bool = True
    difficulty_distribution: DifficultyDistributionConfig = field(default_factory=DifficultyDistributionConfig)


@dataclass
class OutputConfig:
    """Configuration for output formatting."""
    format: str = "remnote_text"
    include_stats: bool = True
    include_metadata: bool = False


@dataclass
class PromptsConfig:
    """Configuration for prompts."""
    system_prompt: str = """You are an expert in creating spaced repetition flashcards.
Generate cards that are atomic, clear, and testable.
Focus on understanding over memorization."""


@dataclass
class AppConfig:
    """Main application configuration."""
    llm: LLMConfig
    remnote: RemNoteConfig = field(default_factory=RemNoteConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)


class ConfigurationManager:
    """
    Manages application configuration with validation and type safety.
    
    Features:
    - YAML configuration loading
    - Schema validation using JSON Schema
    - Environment variable override
    - Type-safe configuration access
    - Default value handling
    
    Example:
        config_manager = ConfigurationManager()
        config = config_manager.load_config("config/config.yaml")
        print(config.llm.provider)  # Type-safe access
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            schema_path: Path to configuration schema file
        """
        self.schema_path = schema_path or Path(__file__).parent.parent / "config" / "app_config_schema.yaml"
        self.schema = self._load_schema()
    
    def load_config(self, config_path: Union[str, Path]) -> AppConfig:
        """
        Load and validate configuration from YAML file.
        
        Args:
            config_path: Path to configuration YAML file
            
        Returns:
            Validated AppConfig object
            
        Raises:
            FileNotFoundError: If configuration file not found
            ValueError: If configuration is invalid
            
        Example:
            >>> config = manager.load_config("config/config.yaml")
            >>> print(config.llm.provider)
            'anthropic'
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in configuration file: {e}")
        
        # Validate against schema
        if self.schema:
            try:
                jsonschema.validate(raw_config, self.schema)
            except jsonschema.ValidationError as e:
                raise ValueError(f"Configuration validation failed: {e.message}")
        
        # Apply environment variable overrides
        self._apply_env_overrides(raw_config)
        
        # Convert to typed configuration
        return self._create_typed_config(raw_config)
    
    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load configuration schema for validation."""
        if not self.schema_path.exists():
            logger.warning(f"Schema file not found: {self.schema_path}")
            return None
        
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return None
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> None:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables follow the pattern:
        REMNOTE_LLM_PROVIDER, REMNOTE_LLM_MODEL, etc.
        """
        env_mappings = {
            'REMNOTE_LLM_PROVIDER': ['llm', 'provider'],
            'REMNOTE_LLM_MODEL': ['llm', 'model'],
            'REMNOTE_LLM_TEMPERATURE': ['llm', 'temperature'],
            'REMNOTE_LLM_MAX_TOKENS': ['llm', 'max_tokens'],
            'REMNOTE_OUTPUT_FORMAT': ['output', 'format'],
            'OPENAI_API_KEY': None,  # Special handling
            'ANTHROPIC_API_KEY': None,  # Special handling
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value and config_path:
                # Navigate to the nested config location
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convert value to appropriate type
                converted_value = self._convert_env_value(value, config_path)
                current[config_path[-1]] = converted_value
                
                logger.info(f"Applied environment override: {env_var}")
    
    def _convert_env_value(self, value: str, config_path: list) -> Union[str, int, float, bool]:
        """Convert environment variable string to appropriate type."""
        # Type conversion based on configuration path
        if 'temperature' in config_path:
            return float(value)
        elif 'max_tokens' in config_path or 'retry_attempts' in config_path:
            return int(value)
        elif 'retry_delay' in config_path:
            return float(value)
        elif value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        else:
            return value
    
    def _create_typed_config(self, raw_config: Dict[str, Any]) -> AppConfig:
        """Convert raw configuration dictionary to typed AppConfig object."""
        try:
            # Extract LLM configuration
            llm_data = raw_config.get('llm', {})
            llm_config = LLMConfig(
                provider=llm_data.get('provider', 'anthropic'),
                model=llm_data.get('model'),
                temperature=llm_data.get('temperature', 0.3),
                max_tokens=llm_data.get('max_tokens', 2000),
                retry_attempts=llm_data.get('retry_attempts', 3),
                retry_delay=llm_data.get('retry_delay', 2.0)
            )
            
            # Extract RemNote configuration
            remnote_data = raw_config.get('remnote', {})
            remnote_config = RemNoteConfig(
                default_folder=remnote_data.get('default_folder', 'ML System Design'),
                include_hierarchy=remnote_data.get('include_hierarchy', True)
            )
            
            # Extract generation configuration
            gen_data = raw_config.get('generation', {})
            
            cards_per_concept_data = gen_data.get('cards_per_concept', {})
            cards_per_concept = CardsPerConceptConfig(
                min=cards_per_concept_data.get('min', 3),
                max=cards_per_concept_data.get('max', 5)
            )
            
            card_types_data = gen_data.get('card_types', {})
            card_types = CardTypesConfig(
                concept=card_types_data.get('concept', True),
                basic=card_types_data.get('basic', True),
                cloze=card_types_data.get('cloze', True),
                descriptor=card_types_data.get('descriptor', True)
            )
            
            difficulty_data = gen_data.get('difficulty_distribution', {})
            difficulty_distribution = DifficultyDistributionConfig(
                beginner=difficulty_data.get('beginner', 0.3),
                intermediate=difficulty_data.get('intermediate', 0.5),
                advanced=difficulty_data.get('advanced', 0.2)
            )
            
            generation_config = GenerationConfig(
                cards_per_concept=cards_per_concept,
                card_types=card_types,
                include_examples=gen_data.get('include_examples', True),
                difficulty_distribution=difficulty_distribution
            )
            
            # Extract output configuration
            output_data = raw_config.get('output', {})
            output_config = OutputConfig(
                format=output_data.get('format', 'remnote_text'),
                include_stats=output_data.get('include_stats', True),
                include_metadata=output_data.get('include_metadata', False)
            )
            
            # Extract prompts configuration
            prompts_data = raw_config.get('prompts', {})
            prompts_config = PromptsConfig(
                system_prompt=prompts_data.get('system_prompt', PromptsConfig.system_prompt)
            )
            
            return AppConfig(
                llm=llm_config,
                remnote=remnote_config,
                generation=generation_config,
                output=output_config,
                prompts=prompts_config
            )
            
        except Exception as e:
            raise ValueError(f"Failed to create typed configuration: {e}")
    
    def validate_config(self, config: AppConfig) -> bool:
        """
        Validate a configuration object for logical consistency.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        errors = []
        
        # Validate LLM configuration
        if config.llm.provider not in ['openai', 'anthropic']:
            errors.append(f"Invalid LLM provider: {config.llm.provider}")
        
        if config.llm.temperature < 0 or config.llm.temperature > 2:
            errors.append(f"Invalid temperature: {config.llm.temperature}")
        
        if config.llm.max_tokens < 100 or config.llm.max_tokens > 8000:
            errors.append(f"Invalid max_tokens: {config.llm.max_tokens}")
        
        # Validate generation configuration
        if config.generation.cards_per_concept.min > config.generation.cards_per_concept.max:
            errors.append("Minimum cards per concept cannot exceed maximum")
        
        # Validate difficulty distribution
        total_difficulty = (
            config.generation.difficulty_distribution.beginner +
            config.generation.difficulty_distribution.intermediate +
            config.generation.difficulty_distribution.advanced
        )
        if abs(total_difficulty - 1.0) > 0.01:
            errors.append(f"Difficulty distribution must sum to 1.0, got {total_difficulty}")
        
        # Validate output format
        if config.output.format not in ['remnote_text', 'remnote_api']:
            errors.append(f"Invalid output format: {config.output.format}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
        
        return True
    
    def save_config(self, config: AppConfig, output_path: Union[str, Path]) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration to save
            output_path: Path to save configuration
        """
        output_path = Path(output_path)
        
        # Convert config to dictionary
        config_dict = {
            'llm': {
                'provider': config.llm.provider,
                'model': config.llm.model,
                'temperature': config.llm.temperature,
                'max_tokens': config.llm.max_tokens,
                'retry_attempts': config.llm.retry_attempts,
                'retry_delay': config.llm.retry_delay
            },
            'remnote': {
                'default_folder': config.remnote.default_folder,
                'include_hierarchy': config.remnote.include_hierarchy
            },
            'generation': {
                'cards_per_concept': {
                    'min': config.generation.cards_per_concept.min,
                    'max': config.generation.cards_per_concept.max
                },
                'card_types': {
                    'concept': config.generation.card_types.concept,
                    'basic': config.generation.card_types.basic,
                    'cloze': config.generation.card_types.cloze,
                    'descriptor': config.generation.card_types.descriptor
                },
                'include_examples': config.generation.include_examples,
                'difficulty_distribution': {
                    'beginner': config.generation.difficulty_distribution.beginner,
                    'intermediate': config.generation.difficulty_distribution.intermediate,
                    'advanced': config.generation.difficulty_distribution.advanced
                }
            },
            'output': {
                'format': config.output.format,
                'include_stats': config.output.include_stats,
                'include_metadata': config.output.include_metadata
            },
            'prompts': {
                'system_prompt': config.prompts.system_prompt
            }
        }
        
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Configuration saved to {output_path}")


def load_default_config() -> AppConfig:
    """
    Load default configuration from the default location.
    
    Returns:
        Default AppConfig object
    """
    config_manager = ConfigurationManager()
    default_config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    return config_manager.load_config(default_config_path)


def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for the specified provider from environment variables.
    
    Args:
        provider: LLM provider name ('openai' or 'anthropic')
        
    Returns:
        API key string or None if not found
    """
    if provider.lower() == 'openai':
        return os.getenv('OPENAI_API_KEY')
    elif provider.lower() == 'anthropic':
        return os.getenv('ANTHROPIC_API_KEY')
    else:
        logger.warning(f"Unknown provider for API key lookup: {provider}")
        return None


if __name__ == "__main__":
    # Demonstration of configuration management
    print("Configuration Management Demonstration")
    print("=" * 45)
    
    try:        # Load default configuration
        config = load_default_config()
        print("✓ Loaded configuration successfully")
        print(f"  LLM Provider: {config.llm.provider}")
        print(f"  Temperature: {config.llm.temperature}")
        print(f"  Cards per concept: {config.generation.cards_per_concept.min}-{config.generation.cards_per_concept.max}")
        print(f"  Include hierarchy: {config.remnote.include_hierarchy}")
        
        # Test validation
        config_manager = ConfigurationManager()
        is_valid = config_manager.validate_config(config)
        print(f"✓ Configuration validation: {'Passed' if is_valid else 'Failed'}")
        
        # Test API key retrieval
        api_key = get_api_key(config.llm.provider)
        print(f"✓ API key available: {'Yes' if api_key else 'No'}")
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
