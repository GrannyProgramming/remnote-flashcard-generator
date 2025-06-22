# RemNote Flashcard Generator

🧠 **Automate your learning with AI-powered flashcard generation**

Transform your study materials into optimized RemNote flashcards using advanced LLM technology. This tool reads structured YAML content and generates high-quality spaced repetition cards that import directly into RemNote.

## ✨ Features

- 🤖 **LLM-Powered Intelligence**: Uses Anthropic Claude or OpenAI GPT-4 to create pedagogically sound flashcards
- 📚 **Comprehensive Card Types**: Supports concept, basic, cloze, descriptor, multiline, list, and multiple choice cards
- 🎯 **RemNote Native**: Perfect compatibility with RemNote's import format and syntax
- 🧬 **Spaced Repetition Optimized**: Creates atomic, testable cards following cognitive science principles
- 🏗️ **Hierarchical Structure**: Preserves parent-child relationships and topic organization
- 📊 **Detailed Analytics**: Generation statistics, quality metrics, and format validation
- ⚙️ **Fully Configurable**: Customize LLM settings, card types, generation parameters, and output formats
- 🛡️ **Production Ready**: Comprehensive error handling, validation, and special character escaping

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- An API key from either Anthropic or OpenAI
- Internet connection for LLM API calls

### Installation

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd remnote-flashcard-generator
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API key**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your preferred editor
   nano .env
   ```
   
   Add your API key:
   ```env
   # For Anthropic (recommended)
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # OR for OpenAI
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### First Run

Generate flashcards from the included example:

```bash
# Generate cards from example ML content
python src/main.py -i content/ml_system_design.yaml -o output/my_flashcards.txt

# Preview what would be generated (dry run)
python src/main.py -i content/ml_system_design.yaml --dry-run
```

You should see output like:
```
RemNote Flashcard Generator
Processing: content/ml_system_design.yaml
Generating cards... ████████████████████████████████████████ 100%
✓ Generated 47 cards
✓ Saved to output/my_flashcards.txt
```

## 📖 Installation Instructions

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: Version 3.8 or higher
- **Memory**: At least 512MB RAM
- **Storage**: 50MB free space
- **Network**: Internet connection for LLM API calls

### Detailed Installation

1. **Check Python version**:
   ```bash
   python --version
   # Should show Python 3.8.0 or higher
   ```

2. **Create virtual environment (recommended)**:
   ```bash
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python src/main.py --help
   ```

### API Key Setup

#### Option 1: Anthropic Claude (Recommended)
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Create an API key
3. Add to `.env`: `ANTHROPIC_API_KEY=your_key_here`

#### Option 2: OpenAI GPT-4
1. Sign up at [platform.openai.com](https://platform.openai.com)
2. Create an API key
3. Add to `.env`: `OPENAI_API_KEY=your_key_here`

## ⚙️ Configuration Options

The system is configured via `config/config.yaml`. Here are the key settings:

### LLM Configuration
```yaml
llm:
  provider: "anthropic"  # or "openai"
  model: ""  # Auto-selected based on provider
  temperature: 0.3  # Controls creativity (0.0-1.0)
  max_tokens: 2000  # Maximum response length
  retry_attempts: 3  # API failure retries
  retry_delay: 2  # Seconds between retries
```

### Card Generation Settings
```yaml
generation:
  cards_per_concept:
    min: 3  # Minimum cards per topic
    max: 5  # Maximum cards per topic
  card_types:
    concept: true      # Enable "Topic :: Definition" cards
    basic: true        # Enable "Question >> Answer" cards
    cloze: true        # Enable "Text with {{gaps}}" cards
    descriptor: true   # Enable "Attribute ;; Value" cards
  include_examples: true  # Include real-world examples
  difficulty_distribution:
    beginner: 0.3      # 30% beginner-level cards
    intermediate: 0.5  # 50% intermediate-level cards
    advanced: 0.2      # 20% advanced-level cards
```

### Output Formatting
```yaml
output:
  format: "remnote_text"  # Output format
  include_stats: true     # Show generation statistics
  include_metadata: false # Include YAML metadata in output

remnote:
  default_folder: "ML System Design"  # Default RemNote folder
  include_hierarchy: true             # Preserve topic structure
```

## 💡 Usage Examples

### Basic Generation
```bash
# Generate cards from YAML content
python src/main.py -i content/ml_system_design.yaml

# Specify custom output location
python src/main.py -i my_content.yaml -o output/custom_cards.txt

# Use custom configuration
python src/main.py -i content.yaml -c my_config.yaml
```

### Advanced Usage
```bash
# Preview mode (no actual generation)
python src/main.py -i content.yaml --dry-run

# Generate with verbose output
python src/main.py -i content.yaml --verbose

# Process multiple files
for file in content/*.yaml; do
    python src/main.py -i "$file" -o "output/$(basename "$file" .yaml)_cards.txt"
done
```

### Creating Your Own Content

1. **Copy the example structure**:
   ```bash
   cp content/ml_system_design.yaml content/my_topic.yaml
   ```

2. **Edit with your content**:
   ```yaml
   ml_system_design:  # Keep this root key
     metadata:
       subject: "Your Subject Name"
       author: "Your Name"
       difficulty: "intermediate"
       
     topics:
       - name: "First Topic"
         content: |
           Comprehensive explanation of the topic.
           Include key concepts, definitions, and context.
         key_concepts:
           - "Important concept 1"
           - "Important concept 2"
         examples:
           - "Real-world example 1"
           - "Real-world example 2"
         subtopics:
           - name: "Subtopic"
             content: "Detailed subtopic explanation..."
   ```

3. **Generate your cards**:
   ```bash
   python src/main.py -i content/my_topic.yaml
   ```

## 🎯 Card Types and Examples

The system generates various card types optimized for different learning objectives:

### Concept Cards (`::`)
**Purpose**: Define fundamental terms and concepts
```
Lambda Architecture :: A data processing architecture that combines batch and stream processing for handling massive quantities of data with both high throughput and low latency.
```

### Basic Cards (`>>`)
**Purpose**: Test factual knowledge and relationships
```
What are the three layers of Lambda Architecture? >> Batch layer (accuracy), Speed layer (low latency), and Serving layer (query interface)

Which companies use Lambda Architecture? >> Netflix (recommendations), LinkedIn (data infrastructure), Twitter (trending topics)
```

### Cloze Cards (`{{}}`)
**Purpose**: Fill-in-the-blank for memorizing lists and details
```
Lambda Architecture uses {{batch processing}} for accuracy and {{stream processing}} for low latency, serving queries through the {{serving layer}}.

The three key benefits of Lambda Architecture are {{fault tolerance}}, {{scalability}}, and {{human fault tolerance}}.
```

### Descriptor Cards (`;;`)
**Purpose**: Attribute-value relationships (nested under parent topics)
```
Lambda Architecture
    Purpose ;; Handle both historical and real-time data processing
    Main Benefit ;; Combines accuracy of batch with speed of streaming
    Use Cases ;; Large-scale data processing, real-time analytics
```

### Multiline Cards
**Purpose**: Complex explanations requiring formatting
```
How does the Lambda Architecture handle data consistency? >>
The batch layer provides the authoritative data store by:
• Processing complete datasets for accuracy
• Immutable append-only storage
• Periodic recomputation to fix errors

The speed layer compensates by:
• Processing recent data in real-time
• Eventually consistent with batch layer
• Garbage collected after batch updates
```

### List Answer Cards
**Purpose**: Ordered or unordered lists as answers
```
What are the key principles of Lambda Architecture design? >>
1. Immutability: Data is never updated, only appended
2. Recomputation: Ability to recompute views from scratch
3. Fault tolerance: System continues despite component failures
4. Human fault tolerance: Easy recovery from human errors
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### API Key Problems
**Problem**: `Authentication failed` or `API key not found`
```bash
Error: OpenAI API authentication failed
```

**Solutions**:
1. Verify your API key is correctly set in `.env`:
   ```bash
   cat .env | grep API_KEY
   ```
2. Check your API key has sufficient credits
3. Ensure no extra spaces or quotes around the key
4. Try regenerating your API key from the provider's dashboard

#### Import Issues in RemNote
**Problem**: Cards don't import correctly or show formatting errors

**Solutions**:
1. **Check file encoding**: Ensure output file is UTF-8
2. **Validate format**: Run format validation
   ```bash
   python src/main.py -i content.yaml --validate-only
   ```
3. **Special characters**: The system automatically escapes problematic characters
4. **File size**: Large files may need to be split for RemNote

#### Generation Quality Issues
**Problem**: Generated cards are too simple/complex or have errors

**Solutions**:
1. **Adjust temperature**: Lower values (0.1-0.3) for more focused cards
2. **Modify prompts**: Edit prompt templates in `prompts/` directory
3. **Content quality**: Ensure source YAML has detailed, well-structured content
4. **Card type selection**: Disable problematic card types in config

#### Performance Issues
**Problem**: Generation takes too long or times out

**Solutions**:
1. **Reduce content size**: Process topics in smaller batches
2. **Adjust token limits**: Lower `max_tokens` in config
3. **Network issues**: Check internet connection stability
4. **API rate limits**: Add delays between requests

#### YAML Parsing Errors
**Problem**: `Invalid YAML structure` or parsing failures

**Solutions**:
1. **Validate YAML syntax**: Use online YAML validators
2. **Check indentation**: YAML is indentation-sensitive
3. **Quote special strings**: Wrap problematic text in quotes
4. **Escape characters**: Use `\` to escape special YAML characters

### Getting Help

1. **Check logs**: Look in `flashcard_generator.log` for detailed error information
2. **Validate configuration**: Ensure `config/config.yaml` follows the schema
3. **Test with example**: Try generating from `content/ml_system_design.yaml`
4. **Minimal reproduction**: Create a small test case that reproduces the issue

### Debug Mode

Enable verbose logging for troubleshooting:
```bash
# Set log level in config.yaml
logging:
  level: DEBUG
  
# Or use environment variable
PYTHONPATH=. python src/main.py -i content.yaml --debug
```

## 📋 Example Output

Here's what you'll get when importing into RemNote:

```
# ML System Design

## Lambda Architecture
Lambda Architecture :: A data processing architecture that combines batch and stream processing methods to handle massive quantities of data

What is the main benefit of Lambda Architecture? >> Provides both high accuracy from batch processing and low latency from stream processing

Lambda Architecture consists of three layers: {{batch layer}}, {{speed layer}}, and {{serving layer}}

    Purpose ;; Handle both historical and real-time data processing
    Main Components ;; Batch layer, Speed layer, Serving layer
    
    ### Batch Layer
    Batch Layer :: The component that processes historical data in large batches for high accuracy and completeness
    
    What does the batch layer provide? >> Authoritative data store with complete accuracy through batch processing
    
    ### Speed Layer  
    Speed Layer :: Real-time processing component that handles streaming data for low latency responses
    
    How does the speed layer complement the batch layer? >> Processes recent data in real-time while batch layer handles historical data

## Feature Store
Feature Store :: Centralized repository for storing, serving, and managing machine learning features for training and inference

What problem does a feature store solve? >> Training-serving skew by ensuring consistent features between model training and production serving

Feature stores provide {{feature consistency}}, {{feature versioning}}, and {{feature monitoring}} capabilities

    Key Benefits ;; Eliminates training-serving skew, enables feature reuse, provides feature lineage
    Components ;; Feature registry, feature serving, feature monitoring
```

## 📊 Generation Statistics

After each run, you'll see detailed statistics:

```
📊 Generation Statistics:
┌─────────────────┬───────┐
│ Card Type       │ Count │
├─────────────────┼───────┤
│ Concept         │ 15    │
│ Basic           │ 23    │
│ Cloze           │ 18    │
│ Descriptor      │ 12    │
├─────────────────┼───────┤
│ Total Cards     │ 68    │
│ Total Topics    │ 12    │
│ Average/Topic   │ 5.7   │
└─────────────────┴───────┘

🎯 Quality Metrics:
• Format validation: ✓ 100% valid
• Character escaping: ✓ 15 instances
• Hierarchy preserved: ✓ 3 levels
• Duplicate detection: ✓ 0 duplicates

⚡ Performance:
• Processing time: 2.3 minutes
• API calls: 24
• Tokens used: 12,847
• Average per topic: 187ms
```

## 🔮 Advanced Features

### Custom Prompt Templates

Create custom prompt templates in the `prompts/` directory:

```yaml
# prompts/custom_card.yaml
name: "custom_card"
description: "Custom card type for specific domain"
system_prompt: |
  You are an expert in creating domain-specific flashcards.
  Focus on practical application and real-world scenarios.
  
user_prompt_template: |
  Topic: {topic_name}
  Content: {content}
  
  Create a {card_type} card that emphasizes practical application.
  Format: {format_instruction}
  
validation_rules:
  - "Must include practical example"
  - "Should reference real-world application"
  - "Format must be valid RemNote syntax"
```

### Batch Processing

Process multiple files efficiently:

```python
# batch_process.py
from pathlib import Path
from src.main import process_file

content_dir = Path("content")
output_dir = Path("output")

for yaml_file in content_dir.glob("*.yaml"):
    output_file = output_dir / f"{yaml_file.stem}_cards.txt"
    process_file(yaml_file, output_file)
    print(f"Processed {yaml_file.name}")
```

### Integration with RemNote

1. **Generate cards**: Run the tool to create formatted text
2. **Copy content**: Copy the generated text file content
3. **Import to RemNote**: 
   - Open RemNote
   - Navigate to desired folder
   - Paste the content   - RemNote automatically creates flashcards

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/test_basic.py::TestYAMLParser -v
python -m pytest tests/test_formatter_features.py -v
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/) and [OpenAI GPT-4](https://openai.com/)
- Inspired by spaced repetition research and [RemNote](https://www.remnote.com/)
- Special thanks to the open-source community for excellent Python libraries

---

**Made with ❤️ for better learning**

Transform your study materials into effective flashcards and accelerate your learning journey!
