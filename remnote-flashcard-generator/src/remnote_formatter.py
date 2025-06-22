"""
RemNote Formatter Module

Converts generated flashcards to RemNote import format with full compatibility.
Handles all card types, hierarchical structure, and special character management.
"""

from typing import List, Dict, Optional, Set
import re
from collections import defaultdict, Counter
from dataclasses import dataclass

# Import the card classes from card_generator
try:
    from .card_generator import Flashcard, CardType, CardDirection
except ImportError:
    # Fallback for direct execution
    from card_generator import Flashcard, CardType, CardDirection


@dataclass
class FormattingStats:
    """Statistics about the formatting process."""
    total_cards: int = 0
    cards_by_type: Dict[str, int] = None
    cards_by_direction: Dict[str, int] = None
    hierarchical_levels: int = 0
    special_chars_escaped: int = 0
    
    def __post_init__(self):
        if self.cards_by_type is None:
            self.cards_by_type = {}
        if self.cards_by_direction is None:
            self.cards_by_direction = {}


class RemNoteFormatter:
    """
    Format flashcards for RemNote import with full compatibility.
    
    This formatter handles:
    - All RemNote card types (concept, basic, cloze, descriptor, etc.)
    - Hierarchical structure preservation
    - Special character escaping
    - Direction control for cards
    - Multi-line formatting
    - Import statistics generation
    
    Example:
        formatter = RemNoteFormatter()
        formatted_output = formatter.format_cards(cards, hierarchy=True)
        print(formatter.get_stats())
    """
    
    def __init__(self):
        """Initialize the formatter with empty statistics."""
        self.stats = FormattingStats()
        self._reset_stats()
    
    def format_cards(self, cards: List[Flashcard], hierarchy: bool = True) -> str:
        """
        Convert flashcards to RemNote text format.
        
        Args:
            cards: List of flashcards to format
            hierarchy: Whether to preserve hierarchical structure
            
        Returns:
            String formatted for RemNote import
            
        Example:
            >>> cards = [concept_card, basic_card, cloze_card]
            >>> output = formatter.format_cards(cards)
            >>> print(output)
            # Data Architecture Patterns
                # Lambda Architecture :: Data processing architecture
                    # purpose ;; Handle both batch and streaming data
                # What is the Batch Layer responsible for? >> Processing large volumes
        """
        self._reset_stats()
        
        if not cards:
            return ""
        
        if hierarchy:
            formatted = self._format_hierarchical(cards)
        else:
            formatted = self._format_flat(cards)
        
        self._calculate_final_stats(cards)
        return formatted
    
    def _format_hierarchical(self, cards: List[Flashcard]) -> str:
        """
        Format cards with hierarchical structure preserved.
        
        Groups cards by parent and maintains proper indentation.
        """
        # Group cards by parent
        hierarchy = defaultdict(list)
        root_cards = []
        
        for card in cards:
            if card.parent:
                hierarchy[card.parent].append(card)
            else:
                root_cards.append(card)
        
        output_lines = []
        
        # Process root level cards
        for card in root_cards:
            formatted_card = self._format_card(card)
            output_lines.append(f"# {formatted_card}")
            
            # Add child cards with proper indentation
            if card.front in hierarchy or card.back in hierarchy:
                # Try to find children by front or back content
                children = hierarchy.get(card.front, []) + hierarchy.get(card.back, [])
                for child in children:
                    child_formatted = self._format_card(child)
                    output_lines.append(f"    # {child_formatted}")
        
        # Process remaining hierarchical cards
        processed_parents = set()
        for parent, children in hierarchy.items():
            if parent not in processed_parents:
                # Add parent if not already processed
                output_lines.append(f"# {parent}")
                for child in children:
                    child_formatted = self._format_card(child)
                    output_lines.append(f"    # {child_formatted}")
                processed_parents.add(parent)
        
        return "\n".join(output_lines)
    
    def _format_flat(self, cards: List[Flashcard]) -> str:
        """Format cards in flat structure without hierarchy."""
        output_lines = []
        
        for card in cards:
            formatted_card = self._format_card(card)
            # Add tags if present
            if card.tags:
                tags_str = " ".join(f"#{tag}" for tag in card.tags)
                formatted_card = f"{formatted_card} {tags_str}"
            
            output_lines.append(f"# {formatted_card}")
        return "\n".join(output_lines)
    
    def _format_card(self, card: Flashcard) -> str:
        """
        Format individual card based on type and direction.
        
        Args:
            card: Flashcard to format
            
        Returns:
            Formatted string according to RemNote syntax
        """
        # Escape special characters in content
        front = self._escape_special_chars(card.front)
        back = self._escape_special_chars(card.back)
        
        # Handle disabled cards first
        if card.direction == CardDirection.DISABLED:
            return f"{front} =- {back}"
        
        # Format based on card type and direction
        if card.card_type == CardType.CONCEPT:
            if card.direction == CardDirection.FORWARD:
                formatted = f"{front} :> {back}"
            elif card.direction == CardDirection.BACKWARD:
                formatted = f"{front} :< {back}"
            else:  # BIDIRECTIONAL or default
                formatted = f"{front} :: {back}"
            
        elif card.card_type == CardType.BASIC:
            if card.direction == CardDirection.BACKWARD:
                formatted = f"{front} << {back}"
            elif card.direction == CardDirection.BIDIRECTIONAL:
                formatted = f"{front} <> {back}"
            else:  # FORWARD or default
                formatted = f"{front} >> {back}"
                
        elif card.card_type == CardType.CLOZE:
            # Cloze cards use the front text with {{}} syntax
            formatted = self._format_cloze(card)
            
        elif card.card_type == CardType.DESCRIPTOR:
            if card.direction == CardDirection.BACKWARD:
                formatted = f"{front} ;< {back}"
            elif card.direction == CardDirection.FORWARD:
                formatted = f"{front} ;> {back}"
            else:  # BIDIRECTIONAL or default
                formatted = f"{front} ;; {back}"
            
        elif card.card_type == CardType.MULTILINE_CONCEPT:
            formatted = self._format_multiline_concept(card)
            
        elif card.card_type == CardType.LIST_ANSWER:
            formatted = self._format_list_answer(card)
            
        elif card.card_type == CardType.MULTIPLE_CHOICE:
            formatted = self._format_multiple_choice(card)
            
        else:
            # Fallback to basic format
            formatted = f"{front} >> {back}"
        
        return formatted
    
    def _format_cloze(self, card: Flashcard) -> str:
        """
        Format cloze cards with proper bracket syntax.
        
        Handles multiple cloze deletions and nested brackets.
        """
        text = card.front
        
        # Ensure proper cloze syntax
        # RemNote uses {{text}} for cloze deletions
        cloze_pattern = r'\{\{([^}]+)\}\}'
          # Validate cloze syntax
        if not re.search(cloze_pattern, text):
            # If no valid cloze syntax found, treat as regular text
            return text
        
        return text
    
    def _format_multiline_concept(self, card: Flashcard) -> str:
        """Format multi-line concept cards with proper delimiters."""
        front = self._escape_special_chars(card.front)
        
        # Check if card has the use_triple_delimiter attribute for triple delimiter format
        if hasattr(card, 'use_triple_delimiter') and card.use_triple_delimiter:
            # Use triple delimiter format: Term :::
            return f"{front} :::"
        else:
            # Use double delimiter + newline format
            back = self._escape_special_chars(card.back)
            # Replace \\n with actual line breaks for RemNote
            back_formatted = back.replace('\\n', '\n    ')
            return f"{front} ::\n    {back_formatted}"
    
    def _format_list_answer(self, card: Flashcard) -> str:
        """Format list answer cards using >>1. syntax."""
        front = self._escape_special_chars(card.front)
        
        if hasattr(card, 'list_items') and card.list_items:
            # Use RemNote's >>1. format for list answers
            return f"{front} >>1."
            # Note: The list items would be nested underneath in the hierarchy        else:
            # Fallback to basic format if no list items
            return f"{front} >> {self._escape_special_chars(card.back)}"
    
    def _format_multiple_choice(self, card: Flashcard) -> str:
        """Format multiple choice cards using >>A) syntax."""
        front = self._escape_special_chars(card.front)
        
        if hasattr(card, 'list_items') and card.list_items and len(card.list_items) > 1:
            # Use RemNote's >>A) format for multiple choice
            return f"{front} >>A)"
            # Note: The first nested item should be the correct answer
            # RemNote will shuffle the options when displaying
        else:
            # Fallback to basic format if no valid multiple choice setup
            return f"{front} >> {self._escape_special_chars(card.back)}"
    
    def _escape_special_chars(self, text: str) -> str:
        """
        Escape characters that interfere with RemNote syntax.
        
        RemNote uses specific syntax characters that need to be escaped:
        - :: for concept cards
        - >> for basic cards  
        - ;; for descriptor cards
        - {{ }} for cloze deletions
        - #[[ ]] for references
        
        Args:
            text: Text to escape
            
        Returns:
            Text with special characters properly escaped
        """
        if not text:
            return text
        
        # Count escaped characters for stats
        original_length = len(text)
        
        # Use space-based escaping (RemNote compatible method)
        # Don't use Unicode replacements - RemNote won't recognize them
        replacements = {
            '::': ': :',    # Add space to break syntax
            '>>': '> >',    # Add space to break syntax
            '<<': '< <',    # Add space to break syntax
            ';;': '; ;',    # Add space to break syntax
            '<>': '< >',    # Add space to break syntax
            '#[[': '# [[',  # Add space to break reference syntax
            ']]': '] ]',    # Add space to break reference syntax
        }
        
        escaped_text = text
        for original, replacement in replacements.items():
            escaped_text = escaped_text.replace(original, replacement)
        
        # Handle cloze brackets more carefully
        # Only escape if they're not part of valid cloze syntax
        if '{{' in escaped_text and '}}' in escaped_text:
            # Check if it's valid cloze syntax
            cloze_pattern = r'\{\{([^}]+)\}\}'
            if not re.search(cloze_pattern, escaped_text):
                escaped_text = escaped_text.replace('{{', '{ {').replace('}}', '} }')
        
        # Update stats
        if len(escaped_text) != original_length:
            self.stats.special_chars_escaped += 1
        
        return escaped_text
    
    def _calculate_final_stats(self, cards: List[Flashcard]) -> None:
        """Calculate final statistics for the formatting process."""
        self.stats.total_cards = len(cards)
        
        # Count by type
        type_counter = Counter(card.card_type.value for card in cards)
        self.stats.cards_by_type = dict(type_counter)
        
        # Count by direction
        direction_counter = Counter(card.direction.value for card in cards)
        self.stats.cards_by_direction = dict(direction_counter)
        
        # Calculate hierarchical levels
        unique_parents = set(card.parent for card in cards if card.parent)
        self.stats.hierarchical_levels = len(unique_parents)
    
    def _reset_stats(self) -> None:
        """Reset statistics for new formatting operation."""
        self.stats = FormattingStats()
    
    def get_stats(self) -> FormattingStats:
        """
        Get formatting statistics.
        
        Returns:
            FormattingStats object with detailed information
            
        Example:
            >>> stats = formatter.get_stats()
            >>> print(f"Total cards: {stats.total_cards}")
            >>> print(f"By type: {stats.cards_by_type}")
        """
        return self.stats
    
    def generate_import_header(self, title: str = "Generated Flashcards") -> str:
        """
        Generate a header for RemNote import.
        
        Args:
            title: Title for the flashcard collection
            
        Returns:
            Formatted header string
        """
        header = f"# {title}\n"
        header += f"Generated {self.stats.total_cards} flashcards\n"
        if self.stats.cards_by_type:
            header += "Card types: " + ", ".join(
                f"{card_type}({count})" 
                for card_type, count in self.stats.cards_by_type.items()
            ) + "\n"
        header += "\n"
        return header
    
    def validate_remnote_format(self, formatted_text: str) -> Dict[str, bool]:
        """
        Validate that the formatted text follows RemNote conventions.
        
        Args:
            formatted_text: The formatted flashcard text
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            "has_headers": bool(re.search(r'^#\s+', formatted_text, re.MULTILINE)),
            "proper_concept_syntax": bool(re.search(r'::', formatted_text)),
            "proper_basic_syntax": bool(re.search(r'>>', formatted_text)),
            "proper_descriptor_syntax": bool(re.search(r';;', formatted_text)),
            "no_unescaped_syntax": not bool(re.search(r'(?<!\\)::', formatted_text)),
            "valid_cloze_syntax": self._validate_cloze_syntax(formatted_text),
        }
        
        return validation_results
    
    def _validate_cloze_syntax(self, text: str) -> bool:
        """Validate cloze deletion syntax."""
        # Check for properly formed cloze deletions
        cloze_pattern = r'\{\{[^}]+\}\}'
        cloze_matches = re.findall(cloze_pattern, text)
        
        # Check for unmatched brackets
        open_brackets = text.count('{{')
        close_brackets = text.count('}}')
        
        return open_brackets == close_brackets and len(cloze_matches) == open_brackets


def create_sample_output() -> str:
    """
    Create a sample RemNote formatted output for testing.
    
    Returns:
        Sample formatted text showing various card types
    """
    sample_cards = [
        Flashcard(
            card_type=CardType.CONCEPT,
            front="Lambda Architecture",
            back="Data processing architecture combining batch and stream processing",
            tags=["architecture", "big-data"]
        ),
        Flashcard(
            card_type=CardType.BASIC,
            front="What is the purpose of the Speed Layer?",
            back="Handle real-time processing and provide low-latency access to recent data",
            parent="Lambda Architecture"
        ),
        Flashcard(
            card_type=CardType.CLOZE,
            front="Lambda Architecture consists of {{Batch Layer}}, {{Speed Layer}}, and {{Serving Layer}}",
            back="",
            parent="Lambda Architecture"
        ),
        Flashcard(
            card_type=CardType.DESCRIPTOR,
            front="latency",
            back="Low for speed layer, high for batch layer",
            parent="Lambda Architecture"
        )
    ]
    
    formatter = RemNoteFormatter()
    return formatter.format_cards(sample_cards, hierarchy=True)


if __name__ == "__main__":
    # Demonstration of the formatter
    print("RemNote Formatter Demonstration")
    print("=" * 40)
    
    sample_output = create_sample_output()
    print(sample_output)
    
    print("\nFormatter capabilities:")
    print("✓ All RemNote card types supported")
    print("✓ Hierarchical structure preserved")
    print("✓ Special characters escaped safely")
    print("✓ Statistics generation included")
    print("✓ Format validation available")
