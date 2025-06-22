# RemNote Automation Tasks for LLM Agents

## Task Overview

This document contains implementation tasks optimized for LLM agents. Each task is self-contained with clear inputs, outputs, and validation criteria. Tasks are ordered by dependencies.

## General Instructions for LLM Agents

1. Each task should be completed independently
2. All code should include comprehensive error handling
3. Use type hints for Python code
4. Include docstrings for all functions
5. Provide example usage for each component
6. Follow PEP 8 style guidelines

---

## Task 1: Create Project Structure and Dependencies

**Objective**: Set up the Python project structure with required dependencies.

**Context**: This is a standalone Python application for personal use that processes YAML files and generates RemNote-compatible flashcards.

**Requirements**:
```
Create the following structure:
remnote-flashcard-generator/
├── src/
│   ├── __init__.py
│   ├── yaml_parser.py
│   ├── llm_client.py
│   ├── card_generator.py
│   ├── remnote_formatter.py
│   └── main.py
├── config/
│   ├── config.yaml
│   └── config_schema.yaml
├── content/
│   └── ml_system_design.yaml (example)
├── output/
│   └── .gitkeep
├── tests/
│   └── __init__.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

**Files to create**:

1. `requirements.txt`:
```
pyyaml>=6.0
jsonschema>=4.0
openai>=1.0
python-dotenv>=1.0
click>=8.0
rich>=13.0
pydantic>=2.0
```

2. `.env.example`:
```
OPENAI_API_KEY=your_api_key_here
# Or for Anthropic:
# ANTHROPIC_API_KEY=your_api_key_here
```

3. `.gitignore`:
```
.env
__pycache__/
*.pyc
output/*.txt
output/*.md
.DS_Store
.vscode/
.idea/
```

**Validation**: Directory structure matches specification, all files created.

---

## Task 2: Implement YAML Parser with Validation

**Objective**: Create a robust YAML parser that validates content structure.

**Context**: The parser must handle hierarchical ML content and validate against a schema to ensure LLM processing compatibility.

**File**: `src/yaml_parser.py`

**Implementation requirements**:
1. Load and parse YAML files
2. Validate against schema
3. Convert to standardized internal format
4. Handle nested topics gracefully

**Code template**:
```python
from typing import Dict, List, Any, Optional
import yaml
import jsonschema
from pathlib import Path
from pydantic import BaseModel, Field

class Topic(BaseModel):
    name: str
    content: str
    subtopics: Optional[List['Topic']] = Field(default_factory=list)
    examples: Optional[List[str]] = Field(default_factory=list)
    key_concepts: Optional[List[str]] = Field(default_factory=list)

class MLContent(BaseModel):
    metadata: Dict[str, Any]
    topics: List[Topic]

class YAMLParser:
    """Parse and validate ML system design content from YAML files."""
    
    def __init__(self, schema_path: Optional[Path] = None):
        # Initialize with schema
        pass
    
    def load_content(self, file_path: Path) -> MLContent:
        """Load and validate YAML content."""
        # Implementation here
        pass
    
    def validate_structure(self, data: Dict) -> bool:
        """Validate YAML structure against schema."""
        # Implementation here
        pass

# Include comprehensive docstrings and error handling
```

**Example YAML schema** (`config/config_schema.yaml`):
```yaml
type: object
required: [ml_system_design]
properties:
  ml_system_design:
    type: object
    required: [metadata, topics]
    properties:
      metadata:
        type: object
        required: [subject]
      topics:
        type: array
        items:
          type: object
          required: [name, content]
```

**Validation**: Successfully parse example YAML, handle errors gracefully, validate against schema.

---

## Task 3: Create LLM Client Abstraction

**Objective**: Build a flexible LLM client supporting multiple providers.

**Context**: The client should abstract away provider differences and handle common LLM operations for card generation.

**File**: `src/llm_client.py`

**Implementation requirements**:
1. Support OpenAI and Anthropic APIs
2. Configurable via environment/config
3. Retry logic for failures
4. Token counting and management

**Code template**:
```python
from typing import List, Dict, Optional, Union
from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import time

class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate response from prompt."""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        pass

class OpenAIClient(LLMClient):
    """OpenAI API client implementation."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        # Initialize OpenAI client
        pass
    
    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        # Implement with retry logic
        pass

class AnthropicClient(LLMClient):
    """Anthropic API client implementation."""
    # Similar implementation

def create_llm_client(provider: str = "openai") -> LLMClient:
    """Factory function to create appropriate LLM client."""
    # Implementation here
    pass

# Include rate limiting and error handling
```

**Validation**: Both clients work with respective APIs, retry logic functions correctly, tokens counted accurately.

---

## Task 4: Implement Card Generation Logic

**Objective**: Create intelligent flashcard generation using LLM.

**Context**: This is the core logic that transforms ML content into optimal spaced repetition cards following RemNote's format.

**File**: `src/card_generator.py`

**Implementation requirements**:
1. Generate multiple card types per concept
2. Ensure atomic, testable cards
3. Preserve concept relationships
4. Avoid duplicates

**Code template**:
```python
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class CardType(Enum):
    CONCEPT = "concept"
    BASIC = "basic"
    CLOZE = "cloze"
    DESCRIPTOR = "descriptor"

@dataclass
class Flashcard:
    card_type: CardType
    front: str
    back: str
    parent: Optional[str] = None
    tags: List[str] = None

class CardGenerator:
    """Generate optimized flashcards from ML content."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.generated_cards: Set[str] = set()  # For duplicate detection
    
    def generate_cards(self, topic: Topic) -> List[Flashcard]:
        """Generate multiple flashcards for a topic."""
        cards = []
        
        # Generate concept card
        concept_card = self._generate_concept_card(topic)
        cards.append(concept_card)
        
        # Generate basic cards for key points
        basic_cards = self._generate_basic_cards(topic)
        cards.extend(basic_cards)
        
        # Generate cloze cards for lists/details
        cloze_cards = self._generate_cloze_cards(topic)
        cards.extend(cloze_cards)
        
        return cards
    
    def _create_generation_prompt(self, topic: Topic, card_type: CardType) -> str:
        """Create optimized prompt for card generation."""
        # Sophisticated prompt engineering here
        pass

# Detailed prompt templates for each card type
CONCEPT_CARD_PROMPT = """
Given this ML system design topic, create a concept card:
Topic: {topic_name}
Content: {content}

Rules:
1. Front: Clear, concise concept name
2. Back: Essential definition in 1-2 sentences
3. Focus on understanding, not memorization

Generate in format: FRONT :: BACK
"""

# Include all card type prompts and generation logic
```

**Validation**: Generates 3-5 high-quality cards per topic, no duplicates, follows RemNote syntax.

---

## Task 5: Build RemNote Formatter

**Objective**: Convert generated cards to RemNote import format with comprehensive formatting support.

**Context**: RemNote accepts specific text formatting for importing flashcards. This module ensures perfect compatibility across all card types and maintains hierarchical structure.

**File**: `src/remnote_formatter.py`

**Implementation requirements**:
1. Support all RemNote card types (concept, basic, cloze, descriptor, multiline, list, multiple choice)
2. Preserve hierarchical structure with proper indentation
3. Escape special characters that interfere with RemNote syntax
4. Support card direction control (forward, backward, bidirectional)
5. Generate comprehensive formatting statistics
6. Validate RemNote format compatibility

**Key functionality**:
```python
from typing import List, Dict
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field

class RemNoteFormatter:
    """Format flashcards for RemNote import with full compatibility."""
    
    def format_cards(self, cards: List[Flashcard], hierarchy: bool = True) -> str:
        """Main formatting method - converts cards to RemNote text format."""
        
    def _format_card(self, card: Flashcard) -> str:
        """Format individual cards with proper RemNote syntax."""
        
    def _format_hierarchical(self, cards: List[Flashcard]) -> str:
        """Preserve parent-child relationships with proper indentation."""
        
    def _escape_special_chars(self, text: str) -> str:
        """Escape RemNote syntax characters (::, >>, ;;, {{}}, #[[]])."""
        
    def generate_import_header(self, title: str) -> str:
        """Generate RemNote import header with metadata."""
        
    def validate_remnote_format(self, formatted_text: str) -> Dict[str, bool]:
        """Validate output follows RemNote conventions."""
        
    def get_stats(self) -> FormattingStats:
        """Return detailed formatting statistics."""

# Supports all RemNote card formats:
# Concept: "Name :: Definition"
# Basic: "Question >> Answer" (with direction support)
# Cloze: "Text with {{hidden}} parts"
# Descriptor: "Term ;; Description"
# Plus multiline, list, and multiple choice variants
```

**Validation**: Output imports correctly into RemNote, all card types render properly, hierarchy preserved, special characters escaped safely.

---

## Task 6: Create Main Application Script

**Objective**: Build the main CLI application that orchestrates all components.

**Context**: User-friendly command-line interface for processing YAML files and generating flashcards.

**File**: `src/main.py`

**Implementation requirements**:
1. CLI with sensible defaults
2. Progress indicators
3. Comprehensive logging
4. Error recovery

**Code template**:
```python
import click
from pathlib import Path
from rich.console import Console
from rich.progress import track
import logging

console = Console()

@click.command()
@click.option('--input', '-i', type=click.Path(exists=True), required=True,
              help='Input YAML file path')
@click.option('--output', '-o', type=click.Path(), default='output/flashcards.txt',
              help='Output file path')
@click.option('--config', '-c', type=click.Path(exists=True), default='config/config.yaml',
              help='Configuration file path')
@click.option('--dry-run', is_flag=True, help='Preview without generating cards')
def main(input, output, config, dry_run):
    """Generate RemNote flashcards from ML system design content."""
    
    console.print(f"[bold blue]RemNote Flashcard Generator[/bold blue]")
    console.print(f"Processing: {input}")
    
    try:
        # Load configuration
        config_data = load_config(Path(config))
        
        # Initialize components
        parser = YAMLParser()
        llm_client = create_llm_client(config_data['llm']['provider'])
        generator = CardGenerator(llm_client)
        formatter = RemNoteFormatter()
        
        # Process content
        with console.status("[bold green]Loading content..."):
            content = parser.load_content(Path(input))
        
        # Generate cards
        all_cards = []
        for topic in track(content.topics, description="Generating cards..."):
            cards = generator.generate_cards(topic)
            all_cards.extend(cards)
        
        # Format output
        formatted_output = formatter.format_cards(all_cards)
        
        if dry_run:
            console.print("\n[bold]Preview:[/bold]")
            console.print(formatted_output[:500] + "...")
            console.print(f"\n[green]Would generate {len(all_cards)} cards[/green]")
        else:
            # Save output
            save_output(Path(output), formatted_output)
            console.print(f"\n[green]✓ Generated {len(all_cards)} cards[/green]")
            console.print(f"[green]✓ Saved to {output}[/green]")
            
            # Show statistics
            show_statistics(formatter.stats)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logging.exception("Generation failed")
        raise click.Abort()

if __name__ == "__main__":
    main()
```

**Validation**: CLI works with all options, provides clear feedback, handles errors gracefully.

---

## Task 7: Create Configuration System

**Objective**: Implement flexible configuration management.

**Context**: Users need to customize LLM settings, RemNote preferences, and generation parameters.

**File**: `config/config.yaml`

**Implementation**:
```yaml
# RemNote Flashcard Generator Configuration

llm:
  provider: "anthropic"  # Options: openai, anthropic
  model: ""
  temperature: 0.3
  max_tokens: 2000
  retry_attempts: 3
  retry_delay: 2  # seconds

remnote:
  default_folder: "ML System Design"
  include_hierarchy: true
  
generation:
  cards_per_concept:
    min: 3
    max: 5
  card_types:
    concept: true
    basic: true
    cloze: true
    descriptor: true
  include_examples: true
  difficulty_distribution:
    beginner: 0.3
    intermediate: 0.5
    advanced: 0.2
  
output:
  format: "remnote_text"  # Future: remnote_api
  include_stats: true
  include_metadata: false
  
prompts:
  system_prompt: |
    You are an expert in creating spaced repetition flashcards.
    Generate cards that are atomic, clear, and testable.
    Focus on understanding over memorization.
```

**Validation**: Configuration loads correctly, all settings apply to generation.

---

## Task 8: Add Example Content File

**Objective**: Create comprehensive example YAML with ML system design content.

**Context**: Users need a template showing proper content structure.

**File**: `content/ml_system_design.yaml`

**Implementation**:
```yaml
ml_system_design:
  metadata:
    subject: "ML System Design Interview Prep"
    author: "ML Engineer"
    version: "1.0"
    difficulty: "intermediate"
    card_types: ["concept", "basic", "cloze", "descriptor"]
    
  topics:
    - name: "Lambda Architecture"
      content: |
        Lambda architecture is a data processing architecture designed to handle massive
        quantities of data by taking advantage of both batch and stream processing methods.
        It addresses the need for a robust, fault-tolerant, scalable system that can serve
        a wide range of workloads and use cases.
      subtopics:
        - name: "Batch Layer"
          content: |
            The batch layer precomputes results using a distributed processing system
            that can handle very large quantities of data. Output is typically stored
            in a read-only database, with updates completely replacing existing results.
        - name: "Speed Layer"
          content: |
            The speed layer processes data streams in real time and without the
            requirements of fix-ups or completeness. This layer sacrifices throughput
            for reduced latency.
        - name: "Serving Layer"
          content: |
            The serving layer responds to ad-hoc queries by returning precomputed
            views or building views from the processed data.
      examples:
        - "Netflix recommendation system"
        - "LinkedIn's data infrastructure"
        - "Twitter's trending topics"
      key_concepts:
        - "Immutable data"
        - "Recomputation"
        - "Fault tolerance"
        - "Human fault tolerance"
        
    - name: "Feature Store"
      content: |
        A feature store is a centralized repository where features are stored and
        organized for use across different machine learning models. It ensures
        consistency between training and serving environments.
      key_concepts:
        - "Feature consistency"
        - "Feature versioning"
        - "Online/offline serving"
        - "Feature monitoring"
      examples:
        - "Uber's Michelangelo"
        - "Airbnb's Zipline"
        - "Netflix's Metaflow"
```

**Validation**: Example parses correctly, generates meaningful cards.

---

## Task 9: Write Documentation

**Objective**: Create user-friendly README with examples.

**Context**: Documentation should enable immediate use without deep technical knowledge.

**File**: `README.md`

**Content structure**:
1. Quick start guide
2. Installation instructions
3. Configuration options
4. Usage examples
5. Troubleshooting
6. Example output

**Validation**: New user can set up and use system following only README.

---

## Implementation Notes for LLM Agents

### Error Handling Patterns
- Always use try-except blocks with specific exceptions
- Log errors with context for debugging
- Provide user-friendly error messages
- Include recovery suggestions

### Code Quality Standards
- Type hints on all functions
- Docstrings with examples
- Comments for complex logic
- Consistent naming conventions

### Testing Each Component
After implementing each task, test with:
```bash
# Test individual modules
python -m src.yaml_parser
python -m src.llm_client
# etc.

# Test full system
python src/main.py -i content/ml_system_design.yaml --dry-run
```

### Common Pitfalls to Avoid
1. Don't hardcode paths - use Path objects
2. Don't ignore rate limits - implement backoff
3. Don't skip validation - check all inputs
4. Don't lose data - save incrementally
5. Don't assume success - handle all failures

## Success Criteria

The system is complete when:
1. All components integrate smoothly
2. Generated cards import perfectly into RemNote
3. Card quality is consistently high
4. Error messages are helpful
5. Performance is acceptable (< 1 min for 100 concepts)
6. Documentation is clear and complete
