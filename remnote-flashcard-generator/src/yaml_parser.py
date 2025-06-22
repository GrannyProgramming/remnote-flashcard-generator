"""
YAML Parser with Schema Validation for ML System Design Content

This module provides robust YAML parsing and validation capabilities for structured
ML content, ensuring data integrity before LLM processing.
"""

from typing import Dict, List, Any, Optional
import yaml
import jsonschema
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import logging
from rich.console import Console

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()


class Topic(BaseModel):
    """
    Represents a single ML topic with hierarchical content structure.
    
    Attributes:
        name: The topic name/title
        content: Detailed explanation of the topic
        subtopics: Nested child topics (optional)
        examples: Real-world examples or use cases (optional)
        key_concepts: Important concepts to emphasize (optional)
        difficulty: Learning difficulty level (optional)
    """
    name: str = Field(..., min_length=1, description="Topic name")
    content: str = Field(..., min_length=10, description="Topic content")
    subtopics: List['Topic'] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    difficulty: str = Field(default="intermediate")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure topic name is properly formatted."""
        if not v.strip():
            raise ValueError("Topic name cannot be empty")
        return v.strip()
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Ensure content is substantial enough for card generation."""
        if len(v.strip()) < 10:
            raise ValueError("Topic content must be at least 10 characters")
        return v.strip()
    
    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v):
        """Validate difficulty level."""
        if v and v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError("Difficulty must be 'beginner', 'intermediate', or 'advanced'")
        return v


class MLContent(BaseModel):
    """
    Root container for ML system design content.
    
    Attributes:
        metadata: Content metadata and configuration
        topics: List of main topics to process
    """
    metadata: Dict[str, Any] = Field(..., description="Content metadata")
    topics: List[Topic] = Field(..., min_length=1, description="Main topics")
    
    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        """Ensure required metadata fields are present."""
        required_fields = ['subject']
        for field in required_fields:
            if field not in v:
                raise ValueError(f"Missing required metadata field: {field}")
        return v
    
    @field_validator('topics')
    @classmethod
    def validate_topics(cls, v):
        """Ensure at least one topic is provided."""
        if not v:
            raise ValueError("At least one topic must be provided")
        return v


# Enable forward references for recursive Topic model
Topic.model_rebuild()


class YAMLParser:
    """
    Parse and validate ML system design content from YAML files.
    
    This parser handles hierarchical content structures, validates against schemas,
    and provides comprehensive error reporting for malformed content.
    
    Example:
        >>> parser = YAMLParser()
        >>> content = parser.load_content(Path("content/ml_topics.yaml"))
        >>> print(f"Loaded {len(content.topics)} topics")
        Loaded 5 topics
    """
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize the YAML parser with optional schema validation.
        
        Args:
            schema_path: Path to JSON schema file for validation
        """
        self.schema_path = schema_path
        self.schema = None
        
        if schema_path and schema_path.exists():
            try:
                with open(schema_path, 'r', encoding='utf-8') as f:
                    self.schema = yaml.safe_load(f)
                logger.info(f"Loaded schema from {schema_path}")
            except Exception as e:
                logger.warning(f"Failed to load schema: {e}")
    
    def load_content(self, file_path: Path) -> MLContent:
        """
        Load and validate YAML content from file.
        
        Args:
            file_path: Path to the YAML file containing ML topics
            
        Returns:
            MLContent object with parsed and validated content
            
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If YAML structure is invalid
            ValidationError: If content doesn't match expected schema
            
        Example:
            >>> parser = YAMLParser()
            >>> content = parser.load_content(Path("ml_topics.yaml"))
            >>> print(content.topics[0].name)
            'Lambda Architecture'
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in {file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read file {file_path}: {e}")
        
        if not isinstance(raw_data, dict):
            raise ValueError("YAML root must be a dictionary")
        
        # Validate against schema if available
        if self.schema:
            try:
                jsonschema.validate(raw_data, self.schema)
                logger.info("Content passed schema validation")
            except jsonschema.ValidationError as e:
                raise ValueError(f"Schema validation failed: {e.message}")
        
        # Extract ML content section
        if 'ml_system_design' not in raw_data:
            raise ValueError("YAML must contain 'ml_system_design' root key")
        
        ml_data = raw_data['ml_system_design']
        
        # Validate structure
        if not self.validate_structure(ml_data):
            raise ValueError("Invalid content structure")
        
        try:
            # Convert to structured format
            content = self._convert_to_ml_content(ml_data)
            logger.info(f"Successfully parsed {len(content.topics)} topics")
            return content
        except Exception as e:
            raise ValueError(f"Failed to parse content structure: {e}")
    
    def validate_structure(self, data: Dict) -> bool:
        """
        Validate YAML structure against expected format.
        
        Args:
            data: Parsed YAML data dictionary
            
        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check required top-level keys
            required_keys = ['metadata', 'topics']
            for key in required_keys:
                if key not in data:
                    logger.error(f"Missing required key: {key}")
                    return False
            
            # Validate metadata structure
            metadata = data['metadata']
            if not isinstance(metadata, dict):
                logger.error("Metadata must be a dictionary")
                return False
            
            if 'subject' not in metadata:
                logger.error("Metadata must contain 'subject' field")
                return False
            
            # Validate topics structure
            topics = data['topics']
            if not isinstance(topics, list) or len(topics) == 0:
                logger.error("Topics must be a non-empty list")
                return False
            
            # Validate each topic
            for i, topic in enumerate(topics):
                if not self._validate_topic_structure(topic, f"topics[{i}]"):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Structure validation error: {e}")
            return False
    
    def _validate_topic_structure(self, topic: Dict, path: str) -> bool:
        """
        Validate individual topic structure.
        
        Args:
            topic: Topic dictionary to validate
            path: Path context for error reporting
            
        Returns:
            True if topic structure is valid
        """
        if not isinstance(topic, dict):
            logger.error(f"{path}: Topic must be a dictionary")
            return False
        
        # Check required fields
        required_fields = ['name', 'content']
        for field in required_fields:
            if field not in topic:
                logger.error(f"{path}: Missing required field '{field}'")
                return False
            
            if not isinstance(topic[field], str) or not topic[field].strip():
                logger.error(f"{path}: Field '{field}' must be a non-empty string")
                return False
        
        # Validate optional fields
        optional_fields = {
            'subtopics': list,
            'examples': list,
            'key_concepts': list,
            'difficulty': str
        }
        
        for field, expected_type in optional_fields.items():
            if field in topic and not isinstance(topic[field], expected_type):
                logger.error(f"{path}: Field '{field}' must be of type {expected_type.__name__}")
                return False
        
        # Recursively validate subtopics
        if 'subtopics' in topic:
            for i, subtopic in enumerate(topic['subtopics']):
                if not self._validate_topic_structure(subtopic, f"{path}.subtopics[{i}]"):
                    return False
        
        return True
    
    def _convert_to_ml_content(self, data: Dict) -> MLContent:
        """
        Convert validated YAML data to MLContent model.
        
        Args:
            data: Validated YAML data dictionary
            
        Returns:
            MLContent instance with parsed topics
        """
        # Extract metadata
        metadata = data['metadata']
        
        # Convert topics recursively
        topics = []
        for topic_data in data['topics']:
            topic = self._convert_to_topic(topic_data)
            topics.append(topic)
        
        return MLContent(metadata=metadata, topics=topics)
    
    def _convert_to_topic(self, topic_data: Dict) -> Topic:
        """
        Convert topic dictionary to Topic model.
        
        Args:
            topic_data: Topic dictionary from YAML
            
        Returns:
            Topic instance
        """
        # Extract required fields
        name = topic_data['name']
        content = topic_data['content']
        
        # Extract optional fields with defaults
        examples = topic_data.get('examples', [])
        key_concepts = topic_data.get('key_concepts', [])
        difficulty = topic_data.get('difficulty', 'intermediate')
        
        # Convert subtopics recursively
        subtopics = []
        if 'subtopics' in topic_data:
            for subtopic_data in topic_data['subtopics']:
                subtopic = self._convert_to_topic(subtopic_data)
                subtopics.append(subtopic)
        
        return Topic(
            name=name,
            content=content,
            subtopics=subtopics,
            examples=examples,
            key_concepts=key_concepts,
            difficulty=difficulty
        )
    
    def get_content_stats(self, content: MLContent) -> Dict[str, Any]:
        """
        Generate statistics about the loaded content.
        
        Args:
            content: MLContent instance to analyze
            
        Returns:
            Dictionary containing content statistics
        """
        def count_topics_recursive(topics: List[Topic]) -> int:
            """Count topics including subtopics."""
            count = len(topics)
            for topic in topics:
                count += count_topics_recursive(topic.subtopics)
            return count
        
        total_topics = count_topics_recursive(content.topics)
        total_examples = sum(len(topic.examples) for topic in content.topics)
        total_concepts = sum(len(topic.key_concepts) for topic in content.topics)
        
        # Calculate content length
        def calculate_content_length(topics: List[Topic]) -> int:
            """Calculate total content length."""
            length = 0
            for topic in topics:
                length += len(topic.content)
                length += calculate_content_length(topic.subtopics)
            return length
        
        total_content_length = calculate_content_length(content.topics)
        
        return {
            'total_topics': total_topics,
            'main_topics': len(content.topics),
            'total_examples': total_examples,
            'total_key_concepts': total_concepts,
            'total_content_chars': total_content_length,
            'estimated_reading_time_minutes': total_content_length // 1000,  # Rough estimate
            'subject': content.metadata.get('subject', 'Unknown'),
            'difficulty_distribution': self._get_difficulty_distribution(content.topics)
        }
    
    def _get_difficulty_distribution(self, topics: List[Topic]) -> Dict[str, int]:
        """
        Calculate difficulty distribution across topics.
        
        Args:
            topics: List of topics to analyze
            
        Returns:
            Dictionary with difficulty level counts
        """
        distribution = {'beginner': 0, 'intermediate': 0, 'advanced': 0}
        
        def count_difficulty(topic_list: List[Topic]):
            for topic in topic_list:
                difficulty = topic.difficulty or 'intermediate'
                distribution[difficulty] += 1
                count_difficulty(topic.subtopics)
        
        count_difficulty(topics)
        return distribution


def main():
    """
    Demo function showing parser usage.
    """
    console.print("[bold blue]YAML Parser Demo[/bold blue]")
    
    # Example of how to use the parser
    try:
        parser = YAMLParser()
        console.print("✓ Parser initialized successfully")
        console.print("Use parser.load_content(Path('your_file.yaml')) to load content")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
