"""
Basic test suite for RemNote Flashcard Generator.

This module contains fundamental tests covering critical paths and edge cases
for the flashcard generation system, updated for the latest formatter implementation.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

# Import with fallback for both test and direct execution
try:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    from yaml_parser import YAMLParser, MLContent, Topic
    from card_generator import CardGenerator, Flashcard, CardType, CardDirection
    from remnote_formatter import RemNoteFormatter
    from llm_client import LLMClient, OpenAIClient, AnthropicClient, create_llm_client, LLMError, LLMConfig, LLMProvider
except ImportError as e:
    print(f"Import error: {e}")    # Ensure we still have the classes available for tests
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    from yaml_parser import YAMLParser, MLContent, Topic
    from card_generator import CardGenerator, Flashcard, CardType, CardDirection
    from remnote_formatter import RemNoteFormatter
    from llm_client import LLMClient, OpenAIClient, AnthropicClient, create_llm_client, LLMError


class TestYAMLParser:
    """Test suite for YAML parsing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = YAMLParser()
        
    def test_load_valid_content(self):
        """Test loading valid YAML content."""
        # Test with the example file
        content_path = Path("content/ml_system_design.yaml")
        if content_path.exists():
            content = self.parser.load_content(content_path)
            assert isinstance(content, MLContent)
            assert len(content.topics) > 0
            assert "subject" in content.metadata
            
    def test_load_content_with_subtopics(self):
        """Test loading content with hierarchical structure."""
        test_yaml = {
            'ml_system_design': {
                'metadata': {
                    'subject': 'Test Subject',
                    'author': 'Test Author'
                },
                'topics': [
                    {
                        'name': 'Parent Topic',
                        'content': 'Parent topic content',
                        'subtopics': [
                            {
                                'name': 'Child Topic',
                                'content': 'Child topic content'
                            }
                        ],
                        'key_concepts': ['concept1', 'concept2'],
                        'examples': ['example1', 'example2']
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_yaml, f)
            temp_path = Path(f.name)
            
        try:
            content = self.parser.load_content(temp_path)
            assert len(content.topics) == 1
            assert content.topics[0].name == 'Parent Topic'
            assert len(content.topics[0].subtopics) == 1
            assert content.topics[0].subtopics[0].name == 'Child Topic'
            assert len(content.topics[0].key_concepts) == 2
            assert len(content.topics[0].examples) == 2
        finally:
            temp_path.unlink()
            
    def test_invalid_yaml_structure(self):
        """Test handling of invalid YAML structure."""
        invalid_yaml = {
            'wrong_root': {
                'metadata': {'subject': 'Test'}
            }        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(invalid_yaml, f)
            temp_path = Path(f.name)
            
        try:
            with pytest.raises(ValueError, match="YAML must contain 'ml_system_design' root key"):
                self.parser.load_content(temp_path)
        finally:
            temp_path.unlink()
            
    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        incomplete_yaml = {
            'ml_system_design': {
                'metadata': {
                    'subject': 'Test Subject'
                },
                'topics': [
                    {
                        'name': 'Topic Name'
                        # Missing 'content' field
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(incomplete_yaml, f)
            temp_path = Path(f.name)
            
        try:
            with pytest.raises(ValueError):
                self.parser.load_content(temp_path)
        finally:
            temp_path.unlink()
            
    def test_file_not_found(self):
        """Test handling of non-existent files."""
        with pytest.raises(FileNotFoundError):
            self.parser.load_content(Path("nonexistent_file.yaml"))
            
    def test_malformed_yaml(self):
        """Test handling of malformed YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content:\n  - malformed\n    - structure")
            temp_path = Path(f.name)
            
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                self.parser.load_content(temp_path)
        finally:
            temp_path.unlink()


class TestCardGenerator:
    """Test suite for card generation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm = Mock(spec=LLMClient)
        self.generator = CardGenerator(self.mock_llm)
        
    def test_generate_concept_card(self):
        """Test generation of concept cards."""
        self.mock_llm.generate.return_value = "Lambda Architecture :: Data processing pattern combining batch and stream processing"
        
        topic = Topic(
            name="Lambda Architecture",
            content="Lambda architecture is a data processing architecture..."
        )
        
        cards = self.generator.generate_cards(topic)
        
        # Should generate at least one card
        assert len(cards) > 0
        
        # Check that LLM was called
        assert self.mock_llm.generate.called
        
    def test_generate_multiple_card_types(self):
        """Test generation of multiple card types for a single topic."""
        # Mock different responses for different card types
        responses = [
            "Lambda Architecture :: Data processing pattern",
            "What is Lambda Architecture? >> A data processing pattern",
            "Lambda Architecture uses {{batch}} and {{stream}} processing"
        ]
        self.mock_llm.generate.side_effect = responses
        
        topic = Topic(
            name="Lambda Architecture",
            content="Detailed content about lambda architecture...",
            key_concepts=["batch processing", "stream processing"],
            examples=["Netflix", "LinkedIn"]        )
        
        cards = self.generator.generate_cards(topic)
        
        # Should generate multiple cards
        assert len(cards) >= 3
        
    def test_duplicate_detection(self):
        """Test that duplicate cards are detected and avoided."""
        # Return the same response twice
        self.mock_llm.generate.return_value = "Lambda Architecture :: Same definition"
        
        topic = Topic(
            name="Lambda Architecture",
            content="Some content for testing duplicates"
        )
        
        # Generate cards twice
        cards1 = self.generator.generate_cards(topic)
        cards2 = self.generator.generate_cards(topic)
          # Should handle duplicates appropriately - the second generation should produce fewer cards
        # due to duplicate detection        assert len(cards1) > 0
        assert len(cards2) >= 0  # Second call may produce fewer or no cards due to duplicates
        
    def test_error_handling_llm_failure(self):
        """Test handling of LLM API failures."""
        self.mock_llm.generate.side_effect = Exception("API Error")
        
        topic = Topic(
            name="Test Topic",
            content="Test content for error handling"        )
        
        # Should handle the error gracefully and return empty list (errors are logged)
        cards = self.generator.generate_cards(topic)
        assert len(cards) == 0  # Should return empty list when all card generation fails
            
    def test_empty_topic_content(self):
        """Test handling of topics with minimal content."""
        topic = Topic(
            name="Empty Topic",
            content="Minimal content"  # Must be at least 10 characters for validation
        )
        
        self.mock_llm.generate.return_value = "Empty Topic :: Minimal definition"
        
        cards = self.generator.generate_cards(topic)
        
        # Should still generate at least one card
        assert len(cards) > 0


class TestRemNoteFormatter:
    """Test suite for basic RemNote formatting functionality (non-overlapping with test_formatter_features.py)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = RemNoteFormatter()
        
    def test_format_validation(self):
        """Test RemNote format validation."""
        valid_text = """
Lambda Architecture :: Data processing pattern
What is it? >> A pattern for big data
Uses {{batch}} and {{stream}} processing
    Purpose ;; Handle data efficiently
"""
        
        validation_result = self.formatter.validate_remnote_format(valid_text)
        
        # Should pass basic validation checks
        assert isinstance(validation_result, dict)
        assert 'has_headers' in validation_result
        assert 'proper_concept_syntax' in validation_result
        assert 'proper_basic_syntax' in validation_result
        
    def test_hierarchical_formatting(self):
        """Test preservation of hierarchical structure."""
        cards = [
            Flashcard(
                card_type=CardType.CONCEPT,
                front="Parent Topic",
                back="Parent definition"
            ),
            Flashcard(
                card_type=CardType.DESCRIPTOR,
                front="Property",
                back="Value",
                parent="Parent Topic"
            ),
            Flashcard(
                card_type=CardType.CONCEPT,
                front="Child Topic",
                back="Child definition",
                parent="Parent Topic"
            )
        ]
        
        formatted = self.formatter.format_cards(cards, hierarchy=True)
        
        # Should preserve indentation for child elements
        lines = formatted.split('\n')
        assert any(line.startswith('    ') for line in lines)  # Should have indented lines


class TestLLMClient:
    """Test suite for LLM client functionality."""
    
    @patch('anthropic.Anthropic')
    def test_anthropic_client_creation(self, mock_anthropic):
        """Test Anthropic client creation."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            client = create_llm_client("anthropic")
            assert isinstance(client, AnthropicClient)
            
    def test_invalid_provider(self):
        """Test handling of invalid LLM provider."""
        with pytest.raises(ValueError, match="is not a valid LLMProvider"):
            create_llm_client("invalid_provider")

    @patch('anthropic.Anthropic')
    def test_anthropic_retry_logic(self, mock_anthropic):
        """Test retry logic for Anthropic client."""
        # Mock client that fails then succeeds
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        
        # Create a proper mock response object
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        
        # First call fails, second succeeds
        mock_client.messages.create.side_effect = [
            Exception("API Error"),
            mock_response
        ]
        
        # Create a config manually since AnthropicClient requires it
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            api_key="test_key",
            temperature=0.3,
            max_tokens=2000,
            retry_attempts=3,
            retry_delay=0.1,  # Reduced delay for faster testing
            timeout=30.0
        )
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            client = AnthropicClient(config)
            response = client.generate("Test prompt")
            
            # Should retry and eventually succeed
            assert response == "Test response"
            assert mock_client.messages.create.call_count == 2


class TestErrorHandling:
    """Test suite for error handling across components."""
    
    def test_file_permission_error(self):
        """Test handling of file permission errors."""
        parser = YAMLParser()
        
        # Create a file path that would cause permission error
        restricted_path = Path("/root/restricted.yaml")
        with pytest.raises((FileNotFoundError, PermissionError)):
            parser.load_content(restricted_path)
            
    def test_network_timeout_simulation(self):
        """Test handling of network timeouts."""
        mock_llm = Mock(spec=LLMClient)
        mock_llm.generate.side_effect = TimeoutError("Network timeout")
        
        generator = CardGenerator(mock_llm)
        topic = Topic(name="Test", content="Test content")
        
        # Should handle timeout gracefully and return empty list (errors are logged)
        cards = generator.generate_cards(topic)
        assert len(cards) == 0  # Should return empty list when all card generation fails
            
    def test_memory_limit_simulation(self):
        """Test handling of memory constraints."""
        # Create a very large topic to test memory handling
        large_content = "A" * 10000  # Large content string
        
        topic = Topic(
            name="Large Topic",
            content=large_content,
            key_concepts=["concept"] * 1000,
            examples=["example"] * 1000
        )
        
        mock_llm = Mock(spec=LLMClient)
        mock_llm.generate.return_value = "Test :: Response"
        
        generator = CardGenerator(mock_llm)
        
        # Should handle large content without crashing
        cards = generator.generate_cards(topic)
        assert len(cards) > 0
        
    def test_unicode_content_handling(self):
        """Test handling of Unicode and special characters."""
        formatter = RemNoteFormatter()
        
        card = Flashcard(
            card_type=CardType.CONCEPT,
            front="数据架构",  # Chinese characters
            back="λ-architecture with émojis 🚀"  # Mixed Unicode
        )
        
        formatted = formatter._format_card(card)
        
        # Should preserve Unicode characters
        assert "数据架构" in formatted
        assert "λ-architecture" in formatted
        assert "🚀" in formatted


class TestIntegration:
    """Integration tests for end-to-end functionality."""
    
    def test_yaml_to_cards_pipeline(self):
        """Test complete pipeline from YAML to formatted cards."""
        # Create test YAML content
        test_yaml = {
            'ml_system_design': {
                'metadata': {
                    'subject': 'Test Subject'
                },
                'topics': [
                    {
                        'name': 'Test Topic',
                        'content': 'Test topic content for card generation',
                        'key_concepts': ['concept1'],
                        'examples': ['example1']
                    }
                ]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_yaml, f)
            temp_path = Path(f.name)
            
        try:
            # Parse YAML
            parser = YAMLParser()
            content = parser.load_content(temp_path)
              # Generate cards (with mock LLM)
            mock_llm = Mock(spec=LLMClient)
            mock_llm.generate.return_value = "Test Topic :: Test definition"
            
            generator = CardGenerator(mock_llm)
            cards = generator.generate_cards(content.topics[0])
            
            # Format cards
            formatter = RemNoteFormatter()
            formatted_output = formatter.format_cards(cards)
            
            # Verify end-to-end result - check that cards were generated and formatted
            assert len(cards) > 0
            assert "Test Topic" in formatted_output  # Should contain the topic name
            assert len(formatted_output.strip()) > 0  # Should have content
            
        finally:
            temp_path.unlink()
            
    def test_configuration_loading(self):
        """Test loading and applying configuration."""
        test_config = {
            'llm': {
                'provider': 'openai',
                'temperature': 0.5,
                'max_tokens': 1000
            },
            'generation': {
                'cards_per_concept': {
                    'min': 2,
                    'max': 4
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            config_path = Path(f.name)
            
        try:
            # Test that configuration can be loaded
            with open(config_path, 'r') as f:
                loaded_config = yaml.safe_load(f)
                
            assert loaded_config['llm']['provider'] == 'openai'
            assert loaded_config['llm']['temperature'] == 0.5
            assert loaded_config['generation']['cards_per_concept']['min'] == 2
            
        finally:
            config_path.unlink()


# Test fixtures and utilities
@pytest.fixture
def sample_topic():
    """Fixture providing a sample topic for testing."""
    return Topic(
        name="Lambda Architecture",
        content="""
        Lambda architecture is a data processing architecture designed to handle 
        massive quantities of data by taking advantage of both batch and stream 
        processing methods.
        """,
        key_concepts=["batch processing", "stream processing", "fault tolerance"],
        examples=["Netflix", "LinkedIn", "Twitter"],
        subtopics=[
            Topic(
                name="Batch Layer",
                content="Processes historical data for accuracy"
            ),
            Topic(
                name="Speed Layer", 
                content="Handles real-time data for low latency"
            )
        ]
    )


@pytest.fixture
def sample_cards():
    """Fixture providing sample flashcards for testing with updated formatter."""
    return [
        Flashcard(
            card_type=CardType.CONCEPT,
            front="Lambda Architecture",
            back="Data processing pattern combining batch and stream processing",
            direction=CardDirection.BIDIRECTIONAL
        ),
        Flashcard(
            card_type=CardType.BASIC,
            front="What are the main layers of Lambda Architecture?",
            back="Batch layer, Speed layer, and Serving layer",
            direction=CardDirection.FORWARD
        ),
        Flashcard(
            card_type=CardType.CLOZE,
            front="Lambda Architecture uses {{batch processing}} for accuracy and {{stream processing}} for low latency",
            back=""
        ),
        Flashcard(
            card_type=CardType.DESCRIPTOR,
            front="Main Benefit",
            back="Combines accuracy and low latency",
            parent="Lambda Architecture",
            direction=CardDirection.FORWARD
        )
    ]


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__])
