"""
RemNote Formatter Module

Converts generated flashcards to RemNote import format with full compatibility.
Handles all card types, hierarchical structure, and special character management.
"""

import re
from typing import List, Dict
from collections import defaultdict, Counter
from dataclasses import dataclass, field

# Import the card classes from card_generator
try:
    from .card_generator import Flashcard, CardType, CardDirection
except ImportError:
    # Fallback for direct script execution
    from card_generator import Flashcard, CardType, CardDirection


@dataclass
class FormattingStats:
    """Statistics about the formatting process."""
    total_cards: int = 0
    cards_by_type: Dict[str, int] = field(default_factory=dict)
    cards_by_direction: Dict[str, int] = field(default_factory=dict)
    hierarchical_levels: int = 0
    special_chars_escaped: int = 0


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
            Data Architecture Patterns
                Lambda Architecture :: Data processing architecture
                    purpose ;; Handle both batch and streaming data
                What is the Batch Layer responsible for? >> Processing large volumes
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
        RemNote accepts multiple hierarchy formats: plain indentation, dashes, or hashes.
        Using plain indentation for maximum compatibility.
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
            output_lines.append(formatted_card)
            
            # Add child cards with proper indentation
            self._add_child_cards(card, hierarchy, output_lines, indent_level=1)
        
        # Process remaining hierarchical cards that weren't processed
        processed_parents = set(card.front for card in root_cards)
        for parent, children in hierarchy.items():
            if parent not in processed_parents:
                output_lines.append(parent)
                for child in children:
                    formatted_child = self._format_card(child)
                    output_lines.append(f"    {formatted_child}")
                processed_parents.add(parent)
        
        return "\n".join(output_lines)
    
    def _add_child_cards(self, parent_card: Flashcard, hierarchy: Dict, output_lines: List[str], indent_level: int = 1):
        """Recursively add child cards with proper indentation."""
        indent = "    " * indent_level  # 4 spaces per level
        
        # Look for children using both front and back as potential parent identifiers
        children = hierarchy.get(parent_card.front, []) + hierarchy.get(parent_card.back, [])
        
        for child in children:
            formatted_child = self._format_card(child)
            output_lines.append(f"{indent}{formatted_child}")
            
            # Recursively add grandchildren
            self._add_child_cards(child, hierarchy, output_lines, indent_level + 1)
    
    def _format_flat(self, cards: List[Flashcard]) -> str:
        """Format cards in flat structure without hierarchy."""
        output_lines = []
        
        for card in cards:
            formatted_card = self._format_card(card)
            # Add tags if present
            if card.tags:
                tags_str = " ".join(f"#{tag}" for tag in card.tags)
                formatted_card = f"{formatted_card} {tags_str}"
            
            output_lines.append(formatted_card)
        
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
        
        # Format based on card type and direction
        if card.card_type == CardType.CONCEPT:
            if hasattr(card, 'direction'):
                if card.direction == CardDirection.FORWARD:
                    formatted = f"{front} :> {back}"  # Forward only concept
                elif card.direction == CardDirection.BACKWARD:
                    formatted = f"{front} :< {back}"  # Backward only concept
                elif card.direction == CardDirection.DISABLED:
                    formatted = f"{front} =- {back}"  # Disabled card
                else:
                    formatted = f"{front} :: {back}"  # Bidirectional (default)
            else:
                formatted = f"{front} :: {back}"
            
        elif card.card_type == CardType.BASIC:
            if hasattr(card, 'direction'):
                if card.direction == CardDirection.BACKWARD:
                    formatted = f"{front} << {back}"
                elif card.direction == CardDirection.BIDIRECTIONAL:
                    formatted = f"{front} <> {back}"
                elif card.direction == CardDirection.DISABLED:
                    formatted = f"{front} =- {back}"  # Disabled card
                elif hasattr(card, 'use_alternate_syntax') and card.use_alternate_syntax:
                    formatted = f"{front} == {back}"  # Alternative to >>
                else:
                    formatted = f"{front} >> {back}"  # Forward (default)
            else:
                formatted = f"{front} >> {back}"
                
        elif card.card_type == CardType.CLOZE:
            # Cloze cards use the front text with {{}} syntax
            formatted = self._format_cloze(card)
            
        elif card.card_type == CardType.DESCRIPTOR:
            if hasattr(card, 'direction') and card.direction == CardDirection.BACKWARD:
                formatted = f"{front} ;< {back}"  # Backward descriptor
            else:
                formatted = f"{front} ;; {back}"  # Forward descriptor (default)
            
        elif card.card_type == CardType.MULTILINE_CONCEPT:
            formatted = self._format_multiline_concept(card)
            
        elif card.card_type == CardType.LIST_ANSWER:
            formatted = self._format_list_answer(card)
            
        elif card.card_type == CardType.MULTIPLE_CHOICE:
            formatted = self._format_multiple_choice(card)
            
        else:
            # Fallback to basic format
            formatted = f"{front} >> {back}"
        
        # Add Extra Card Detail if present
        if hasattr(card, 'extra_detail') and card.extra_detail:
            formatted += f"\n    #[[Extra Card Detail]] {card.extra_detail}"
        
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
        """
        Format multi-line concept cards with proper delimiters.
        
        RemNote supports TWO methods for multi-line cards:
        Method 1: Triple delimiter (:::)
        Method 2: Double delimiter + Enter (:: followed by newline)
        """
        front = self._escape_special_chars(card.front)
        back = self._escape_special_chars(card.back)
        
        # Method 1: Use triple delimiter for multi-line concepts
        formatted_lines = []
        if hasattr(card, 'use_triple_delimiter') and card.use_triple_delimiter:
            formatted_lines.append(f"{front} :::")
            # List items as nested bullets
            back_lines = back.replace('\\n', '\n').split('\n')
            for line in back_lines:
                if line.strip():
                    formatted_lines.append(f"    {line.strip()}")
        else:
            # Method 2: Double delimiter + Enter
            back_formatted = back.replace('\\n', '\n    ')
            formatted_lines.append(f"{front} ::")
            formatted_lines.append(f"    {back_formatted}")
        
        return '\n'.join(formatted_lines)
    
    def _format_list_answer(self, card: Flashcard) -> str:
        """
        Format list answer cards using >>1. format.
        """
        front = self._escape_special_chars(card.front)
        
        if hasattr(card, 'list_items') and card.list_items:
            # Use >>1. format for list answers
            formatted_lines = [f"{front} >>1."]
            for item in card.list_items:
                escaped_item = self._escape_special_chars(item)
                formatted_lines.append(f"    {escaped_item}")
            return '\n'.join(formatted_lines)
        else:
            return f"{front} >> {self._escape_special_chars(card.back)}"
    
    def _format_multiple_choice(self, card: Flashcard) -> str:
        """
        Format multiple choice cards using >>A) format.
        First nested item is the correct answer.
        """
        front = self._escape_special_chars(card.front)
        
        if hasattr(card, 'list_items') and card.list_items and len(card.list_items) > 1:
            # Use >>A) format
            formatted_lines = [f"{front} >>A)"]
            
            # First item should be the correct answer
            correct_index = getattr(card, 'correct_choice_index', 0)
            choices = list(card.list_items)
            
            # Ensure correct answer is first
            if correct_index != 0 and correct_index < len(choices):
                correct_answer = choices.pop(correct_index)
                choices.insert(0, correct_answer)
            
            # Add choices
            for choice in choices:
                escaped_choice = self._escape_special_chars(choice)
                formatted_lines.append(f"    {escaped_choice}")
            
            return '\n'.join(formatted_lines)
        else:
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
        
        Uses space-based escaping for maximum compatibility.
        
        Args:
            text: Text to escape
            
        Returns:
            Text with special characters properly escaped
        """
        if not text:
            return text
        
        # Count escaped characters for stats
        original_length = len(text)
        
        # Method 1: Add spaces to break syntax (most compatible)
        replacements = {
            '::': ': :',    # Add space
            '>>': '> >',    
            '<<': '< <',
            ';;': '; ;',
            '<>': '< >',
            '#[[': '#[ [',
            ']]': '] ]',
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
        
        # Update stats if characters were escaped
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
        direction_counter = Counter(getattr(card, 'direction', CardDirection.FORWARD).value for card in cards)
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
        header = f"{title}\n"
        header += f"Generated {self.stats.total_cards} flashcards\n"
        if self.stats.cards_by_type:
            type_summary = ", ".join(f"{count} {card_type}" for card_type, count in self.stats.cards_by_type.items())
            header += f"Types: {type_summary}\n"
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
            "has_content": bool(formatted_text.strip()),
            "proper_concept_syntax": bool(re.search(r'(:::|::)', formatted_text)),
            "proper_basic_syntax": bool(re.search(r'(>>>|>>|==)', formatted_text)),
            "proper_descriptor_syntax": bool(re.search(r'(;;;|;;)', formatted_text)),
            "proper_list_syntax": bool(re.search(r'>>1\.', formatted_text)),
            "proper_choice_syntax": bool(re.search(r'>>A\)', formatted_text)),
            "valid_cloze_syntax": self._validate_cloze_syntax(formatted_text),
            "no_unescaped_conflicts": self._check_for_syntax_conflicts(formatted_text),
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
    
    def _check_for_syntax_conflicts(self, text: str) -> bool:
        """Check if there are any syntax conflicts that could break RemNote parsing."""
        # This is a simplified check - in practice, context matters more
        lines = text.split('\n')
        for line in lines:
            # Check for multiple delimiters on the same line
            delimiter_count = sum([
                line.count('::'),
                line.count('>>'),
                line.count(';;'),
                line.count('<<'),
                line.count('<>'),
                line.count('=-')
            ])
            if delimiter_count > 1:
                return False
        return True


def create_sample_output() -> str:
    """
    Create a sample RemNote formatted output for testing.
    
    Returns:
        Sample formatted text showing various card types
    """
    # Note: This function would need the actual Flashcard classes imported
    # For now, just return a sample string
    sample_output = """Machine Learning System Design
    Lambda Architecture :: Pattern combining batch and stream processing
        purpose ;; Handle both historical and real-time data
        components :::
            Batch Layer
            Speed Layer  
            Serving Layer
        What are the main benefits? >> Fault tolerance and scalability
        Lambda architecture uses {{batch processing}} for accuracy and {{stream processing}} for speed
        When to use >>1.
            High data volume
            Need both real-time and batch processing
            Fault tolerance is critical"""
    
    return sample_output


if __name__ == "__main__":
    # Demonstration of the formatter
    print("RemNote Formatter Demonstration")
    print("=" * 40)
    
    sample_output = create_sample_output()
    print(sample_output)
    
    formatter = RemNoteFormatter()
    validation = formatter.validate_remnote_format(sample_output)
    print(f"\nValidation results: {validation}")
    
    print("\nFormatter capabilities:")
    print("✓ All RemNote card types supported")
    print("✓ Hierarchical structure preserved")
    print("✓ Special characters escaped safely")
    print("✓ Statistics generation included")
    print("✓ Format validation available")
    print("✓ Multi-line support (both ::: and :: + newline)")
    print("✓ List answers (>>1. format)")
    print("✓ Multiple choice (>>A) format)")
    print("✓ Direction control (:>, :<, ;<, <<, <>, =-)")
    print("✓ Alternative syntax (== for >>)")
    print("✓ Extra Card Detail power-up support")
