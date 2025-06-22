"""
Main Application Script for RemNote Flashcard Generator

This module provides a comprehensive CLI interface that orchestrates all components
to transform ML system design content into optimal RemNote flashcards.
"""

import click
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich.table import Table
import time

# Import our components
try:
    from .yaml_parser import YAMLParser
    from .llm_client import create_llm_client
    from .card_generator import CardGenerator, Flashcard
    from .remnote_formatter import RemNoteFormatter, FormattingStats
except ImportError:
    # Fallback for direct execution
    from yaml_parser import YAMLParser
    from llm_client import create_llm_client
    from card_generator import CardGenerator, Flashcard
    from remnote_formatter import RemNoteFormatter, FormattingStats

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flashcard_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize console for rich output
console = Console()


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is malformed
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate essential configuration sections
        required_sections = ['llm', 'generation', 'output']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Set defaults for missing optional values
        config.setdefault('remnote', {})
        config['remnote'].setdefault('include_hierarchy', True)
        config['remnote'].setdefault('default_folder', 'ML System Design')
        
        return config
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error loading configuration: {e}")


def save_output(output_path: Path, content: str, stats: FormattingStats) -> None:
    """
    Save formatted output to file with comprehensive metadata.
    
    Args:
        output_path: Path where to save the output
        content: Formatted RemNote content
        stats: Formatting statistics
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create comprehensive output with metadata
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        header = f"""# RemNote Flashcard Import
# Generated on: {timestamp}
# Total cards: {stats.total_cards}
# Card types: {', '.join(f"{k}: {v}" for k, v in stats.cards_by_type.items())}
# Hierarchical levels: {stats.hierarchical_levels}
# Special characters escaped: {stats.special_chars_escaped}
#
# Instructions:
# 1. Copy the content below (excluding these header comments)
# 2. Paste into RemNote
# 3. The hierarchy and card types will be preserved automatically
#
# ========================================

"""
        
        full_content = header + content
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        logger.info(f"Output saved to {output_path}")
        
    except Exception as e:
        raise RuntimeError(f"Failed to save output: {e}")


def show_statistics(stats: FormattingStats, llm_info: Dict[str, Any]) -> None:
    """
    Display comprehensive generation statistics.
    
    Args:
        stats: Formatting statistics
        llm_info: LLM usage information
    """
    # Create statistics table
    table = Table(title="Generation Statistics", show_header=True, header_style="bold blue")
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    # Add formatting stats
    table.add_row("Total Cards Generated", str(stats.total_cards))
    table.add_row("Hierarchical Levels", str(stats.hierarchical_levels))
    table.add_row("Special Characters Escaped", str(stats.special_chars_escaped))
    
    # Add card type breakdown
    if stats.cards_by_type:
        table.add_row("", "")  # Separator
        table.add_row("[bold]Card Types[/bold]", "")
        for card_type, count in stats.cards_by_type.items():
            table.add_row(f"  {card_type.title()}", str(count))
    
    # Add direction breakdown if available
    if stats.cards_by_direction:
        table.add_row("", "")  # Separator
        table.add_row("[bold]Card Directions[/bold]", "")
        for direction, count in stats.cards_by_direction.items():
            table.add_row(f"  {direction.title()}", str(count))
    
    # Add LLM usage stats
    table.add_row("", "")  # Separator
    table.add_row("[bold]LLM Usage[/bold]", "")
    table.add_row("Provider", llm_info.get('provider', 'Unknown'))
    table.add_row("Model", llm_info.get('model', 'Unknown'))
    table.add_row("Total Tokens Used", str(llm_info.get('total_tokens_used', 0)))
    table.add_row("API Requests", str(llm_info.get('request_count', 0)))
    
    console.print(table)


def validate_environment(skip_api_keys: bool = False) -> bool:
    """
    Validate that the environment is properly configured.
    
    Args:
        skip_api_keys: If True, skip API key validation (useful for dry runs)
    
    Returns:
        True if environment is valid
    """
    issues = []
    
    # Check for API keys (unless skipped)
    if not skip_api_keys:
        import os
        if not os.getenv('OPENAI_API_KEY') and not os.getenv('ANTHROPIC_API_KEY'):
            issues.append("No API keys found. Set either OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
    
    # Check required directories
    required_dirs = ['config', 'content', 'output']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            issues.append(f"Required directory missing: {dir_name}")
    
    if issues:
        console.print(Panel("\n".join([f"• {issue}" for issue in issues]), 
                          title="[red]Environment Issues[/red]", 
                          border_style="red"))
        return False
    
    return True


@click.command()
@click.option('--input', '-i', 
              type=click.Path(exists=True, path_type=Path), 
              required=True,
              help='Input YAML file path (e.g., content/ml_system_design.yaml)')
@click.option('--output', '-o', 
              type=click.Path(path_type=Path), 
              default=Path('output/flashcards.txt'),
              help='Output file path (default: output/flashcards.txt)')
@click.option('--config', '-c', 
              type=click.Path(exists=True, path_type=Path), 
              default=Path('config/config.yaml'),
              help='Configuration file path (default: config/config.yaml)')
@click.option('--dry-run', 
              is_flag=True, 
              help='Preview generation without creating cards or using LLM tokens')
@click.option('--verbose', '-v', 
              is_flag=True, 
              help='Enable verbose logging')
@click.option('--validate-only', 
              is_flag=True, 
              help='Only validate input file and configuration')
def main(input: Path, output: Path, config: Path, dry_run: bool, verbose: bool, validate_only: bool):
    """
    Generate RemNote flashcards from ML system design content.
    
    This tool processes YAML files containing ML topics and generates
    optimized flashcards using LLM intelligence. The output is formatted
    for direct import into RemNote.
    
    Examples:
    
        # Basic usage
        python main.py -i content/ml_system_design.yaml
        
        # Dry run to preview without using tokens
        python main.py -i content/ml_system_design.yaml --dry-run
        
        # Custom output location
        python main.py -i content/ml_system_design.yaml -o my_cards.txt
        
        # Validate input only
        python main.py -i content/ml_system_design.yaml --validate-only
    """
    # Configure logging level
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Show header
    console.print(Panel.fit(
        "[bold blue]RemNote Flashcard Generator[/bold blue]\n"
        "Transform ML content into optimal spaced repetition cards",
        border_style="blue"
    ))
    
    try:        # Validate environment first (skip API keys for dry runs and validation-only)
        skip_api_validation = dry_run or validate_only
        if not validate_environment(skip_api_keys=skip_api_validation):
            console.print("[red]Environment validation failed. Please fix the issues above.[/red]")
            raise click.Abort()
        
        # Load and validate configuration
        with console.status("[bold green]Loading configuration..."):
            config_data = load_config(config)
            console.print(f"✓ Configuration loaded from {config}")
        
        # Initialize YAML parser with schema
        schema_path = config.parent / "config_schema.yaml" if (config.parent / "config_schema.yaml").exists() else None
        parser = YAMLParser(schema_path=schema_path)
        
        # Load and validate content
        with console.status("[bold green]Loading and validating content..."):
            content = parser.load_content(input)
            console.print(f"✓ Loaded {len(content.topics)} topics from {input}")
            
            # Count total concepts (including subtopics)
            total_concepts = sum(1 + len(topic.subtopics) for topic in content.topics)
            console.print(f"✓ Found {total_concepts} total concepts to process")
        
        if validate_only:
            console.print(Panel("[green]✓ Validation completed successfully![/green]", 
                               title="Validation Result", border_style="green"))
            return
        
        # Initialize LLM client
        if not dry_run:
            with console.status("[bold green]Initializing LLM client..."):
                llm_client = create_llm_client(
                    provider=config_data['llm']['provider'],
                    model=config_data['llm'].get('model'),
                    temperature=config_data['llm'].get('temperature', 0.3),
                    max_tokens=config_data['llm'].get('max_tokens', 2000),
                    retry_attempts=config_data['llm'].get('retry_attempts', 3),
                    retry_delay=config_data['llm'].get('retry_delay', 2)
                )
                console.print(f"✓ LLM client initialized ({config_data['llm']['provider']})")
        else:
            llm_client = None
            console.print("✓ Dry run mode - LLM client skipped")
        
        # Initialize card generator and formatter
        generator = CardGenerator(llm_client) if llm_client else None
        formatter = RemNoteFormatter()
        
        if dry_run:
            # Dry run mode - just show what would be processed
            console.print(Panel(
                f"[yellow]DRY RUN MODE[/yellow]\n\n"
                f"Would process: {len(content.topics)} main topics\n"
                f"Total concepts: {total_concepts}\n"
                f"Estimated cards: {total_concepts * config_data['generation']['cards_per_concept']['min']}-"
                f"{total_concepts * config_data['generation']['cards_per_concept']['max']}\n"
                f"Output file: {output}\n\n"
                f"[dim]No LLM tokens will be used in dry run mode[/dim]",
                title="Preview",
                border_style="yellow"
            ))
            
            # Show topic structure
            console.print("\n[bold]Topic Structure:[/bold]")
            for i, topic in enumerate(content.topics, 1):
                console.print(f"{i}. {topic.name}")
                for j, subtopic in enumerate(topic.subtopics, 1):
                    console.print(f"   {i}.{j}. {subtopic.name}")
            
            console.print("\n[green]✓ Dry run completed - no files created[/green]")
            return
        
        # Generate cards for all topics
        all_cards: List[Flashcard] = []
        
        with Progress() as progress:
            main_task = progress.add_task("[green]Generating cards...", total=len(content.topics))
            
            for topic in content.topics:
                progress.update(main_task, description=f"[green]Processing: {topic.name[:40]}...")
                
                try:
                    # Generate cards for main topic
                    topic_cards = generator.generate_cards(topic)
                    all_cards.extend(topic_cards)
                    
                    # Generate cards for subtopics
                    for subtopic in topic.subtopics:
                        subtopic_cards = generator.generate_cards(subtopic, parent_context=topic.name)
                        all_cards.extend(subtopic_cards)
                    
                    progress.update(main_task, advance=1)
                    
                except Exception as e:
                    logger.error(f"Failed to generate cards for topic '{topic.name}': {e}")
                    console.print(f"[yellow]⚠ Skipped topic '{topic.name}': {e}[/yellow]")
                    progress.update(main_task, advance=1)
                    continue
        
        console.print(f"✓ Generated {len(all_cards)} cards total")
        
        # Format cards for RemNote
        with console.status("[bold green]Formatting for RemNote..."):
            formatted_output = formatter.format_cards(
                all_cards, 
                hierarchy=config_data['remnote']['include_hierarchy']
            )
            console.print("✓ Cards formatted for RemNote import")
        
        # Save output
        with console.status("[bold green]Saving output..."):
            save_output(output, formatted_output, formatter.get_stats())
            console.print(f"✓ Output saved to {output}")
        
        # Show comprehensive statistics
        console.print("\n")
        show_statistics(formatter.get_stats(), llm_client.get_model_info())
        
        # Show success message with next steps
        console.print(Panel(
            f"[green]✓ Generation completed successfully![/green]\n\n"
            f"📁 Output saved to: [bold]{output}[/bold]\n"
            f"📊 Total cards: [bold]{len(all_cards)}[/bold]\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"1. Open the output file\n"
            f"2. Copy the content (excluding header comments)\n"
            f"3. Paste into RemNote\n"
            f"4. Cards will be imported with proper hierarchy",
            title="Success",
            border_style="green"
        ))
        
    except click.Abort:
        raise
    except Exception as e:
        logger.exception("Generation failed")
        console.print(Panel(
            f"[red]Error: {e}[/red]\n\n"
            f"Check the log file for detailed information:\n"
            f"[dim]flashcard_generator.log[/dim]",
            title="Generation Failed",
            border_style="red"
        ))
        raise click.Abort()


if __name__ == "__main__":
    main()
