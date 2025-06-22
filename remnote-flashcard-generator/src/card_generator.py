"""
Card Generation Logic for RemNote Flashcards

This module transforms ML system design content into optimal spaced repetition flashcards
using LLM-powered intelligence. It generates multiple card types per concept following
learning science principles.
"""

from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib

try:
    from .yaml_parser import Topic
    from .llm_client import LLMClient, LLMError
    from .prompt_loader import PromptLoader
except ImportError:
    # Fallback for standalone execution
    from yaml_parser import Topic
    from llm_client import LLMClient, LLMError
    from prompt_loader import PromptLoader

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CardType(Enum):
    """Enumeration of RemNote flashcard types with full RemNote support."""
    CONCEPT = "concept"                     # Term :: Definition (bidirectional)
    BASIC = "basic"                         # Question >> Answer (forward only)
    CLOZE = "cloze"                         # Text with {{hidden}} parts
    DESCRIPTOR = "descriptor"               # Attribute ;; Value (for hierarchical cards)
    MULTILINE_BASIC = "multiline_basic"     # Question >>> Multi-line answer
    MULTILINE_CONCEPT = "multiline_concept" # Term ::: Multi-line definition
    MULTILINE_DESCRIPTOR = "multiline_descriptor" # Attribute ;;; Multi-line description
    LIST_ANSWER = "list_answer"             # Question >>1. Item 1, Item 2
    MULTIPLE_CHOICE = "multiple_choice"     # Question >>A) Correct answer
    

class CardDirection(Enum):
    """Direction/behavior for RemNote flashcard types."""
    FORWARD = "forward"         # Default direction
    BACKWARD = "backward"       # Reverse direction
    BIDIRECTIONAL = "bidirectional"  # Both directions
    DISABLED = "disabled"       # No flashcard generation (>- syntax)


@dataclass
class Flashcard:
    """
    Represents a single flashcard with full RemNote formatting support.
    
    Attributes:
        card_type: Type of flashcard (concept, basic, cloze, descriptor, etc.)
        front: Front side content (question/prompt)
        back: Back side content (answer/definition)
        parent: Parent topic name for hierarchical organization
        tags: List of tags for categorization
        difficulty: Learning difficulty level
        source_hash: Hash of source content for duplicate detection
        direction: Card direction (forward, backward, bidirectional, disabled)
        list_items: List items for multi-line/list cards
        correct_choice_index: Index of correct choice for multiple choice
        extra_detail: Extra Card Detail power-up content
        is_multiline: Whether this card uses multi-line formatting
    """
    card_type: CardType
    front: str
    back: str
    parent: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    source_hash: str = ""
    direction: CardDirection = CardDirection.FORWARD
    list_items: List[str] = field(default_factory=list)
    correct_choice_index: int = 0
    extra_detail: Optional[str] = None
    is_multiline: bool = False
    
    def __post_init__(self):
        """Generate source hash for duplicate detection."""
        if not self.source_hash:
            # Include more fields in hash for better duplicate detection
            content = f"{self.front}||{self.back}||{self.card_type.value}||{self.direction.value}"
            if self.list_items:
                content += f"||{','.join(self.list_items)}"
            self.source_hash = hashlib.md5(content.encode()).hexdigest()[:8]


class CardGenerator:
    """
    Generate optimized flashcards from ML content using LLM intelligence.
    
    This class is responsible ONLY for generating flashcard content and structure.
    Formatting for specific output systems (RemNote, Anki, etc.) is handled 
    by dedicated formatter classes.
    
    Responsibilities:
    - Generate multiple card types per concept using LLM prompts
    - Handle content validation and duplicate detection
    - Preserve topic relationships and hierarchies
    - Follow spaced repetition best practices
    
    NOT Responsible For:
    - Output formatting (handled by RemNoteFormatter, etc.)
    - Special character escaping (handled by formatters)
    - Export format generation (handled by formatters)
    
    Example:
        >>> generator = CardGenerator(llm_client)
        >>> cards = generator.generate_cards(topic)
        >>> formatter = RemNoteFormatter()
        >>> output = formatter.format_cards(cards)
    """
    
    def __init__(self, llm_client: LLMClient, config: Optional[Dict] = None):
        """
        Initialize card generator.
        
        Args:
            llm_client: Configured LLM client for generation
            config: Generation configuration dictionary
        """
        self.llm = llm_client
        self.config = config or {}
        self.prompt_loader = PromptLoader()
        self.generated_cards: Set[str] = set()  # For duplicate detection
        self.generation_stats = {
            "total_cards": 0,
            "by_type": {card_type.value: 0 for card_type in CardType},
            "duplicates_avoided": 0,
            "topics_processed": 0,
            "llm_calls": 0
        }
    
    def generate_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """
        Generate multiple flashcards for a topic.
        
        Args:
            topic: Topic object containing content to convert
            parent_context: Context from parent topic for better generation
            
        Returns:
            List of generated flashcards
            
        Raises:
            LLMError: If card generation fails
        """
        logger.info(f"Generating cards for topic: {topic.name}")
        cards = []
        
        try:
            # Generate concept card (main definition)
            concept_card = self._generate_concept_card(topic, parent_context)
            if concept_card and self._is_unique_card(concept_card):
                cards.append(concept_card)
                self._register_card(concept_card)
            
            # Generate basic cards for key points
            basic_cards = self._generate_basic_cards(topic, parent_context)
            for card in basic_cards:
                if self._is_unique_card(card):
                    cards.append(card)
                    self._register_card(card)
            
            # Generate cloze cards for lists and details
            if topic.key_concepts or topic.examples:
                cloze_cards = self._generate_cloze_cards(topic, parent_context)
                for card in cloze_cards:
                    if self._is_unique_card(card):
                        cards.append(card)
                        self._register_card(card)
              # Generate descriptor cards for attributes
            if self.config.get('card_types', {}).get('descriptor', True):
                descriptor_cards = self._generate_descriptor_cards(topic, parent_context)
                for card in descriptor_cards:
                    if self._is_unique_card(card):
                        cards.append(card)
                        self._register_card(card)
            
            # Generate multi-line cards for complex content
            if self.config.get('card_types', {}).get('multiline', True):
                multiline_cards = self._generate_multiline_cards(topic, parent_context)
                for card in multiline_cards:
                    if self._is_unique_card(card):
                        cards.append(card)
                        self._register_card(card)
            
            # Generate list answer cards
            if self.config.get('card_types', {}).get('list_answer', True):
                list_cards = self._generate_list_answer_cards(topic, parent_context)
                for card in list_cards:
                    if self._is_unique_card(card):
                        cards.append(card)
                        self._register_card(card)
            
            # Generate multiple choice cards
            if self.config.get('card_types', {}).get('multiple_choice', True):
                mc_cards = self._generate_multiple_choice_cards(topic, parent_context)
                for card in mc_cards:
                    if self._is_unique_card(card):
                        cards.append(card)
                        self._register_card(card)
            
            # Process subtopics recursively
            for subtopic in topic.subtopics:
                subtopic_cards = self.generate_cards(subtopic, topic.name)
                cards.extend(subtopic_cards)
            
            self.generation_stats["topics_processed"] += 1
            logger.info(f"Generated {len(cards)} cards for {topic.name}")
            
        except Exception as e:
            logger.error(f"Failed to generate cards for {topic.name}: {e}")
            raise LLMError(f"Card generation failed: {e}")
        
        return cards
    
    def _generate_concept_card(self, topic: Topic, parent_context: Optional[str] = None) -> Optional[Flashcard]:
        """Generate a concept card (Term :: Definition) using YAML prompts."""
        if not self.config.get('card_types', {}).get('concept', True):
            return None
        
        try:
            # Get prompt configuration from YAML
            prompt_config = self.prompt_loader.get_config("concept")
            
            # Format prompt with topic data
            context_info = f" (part of {parent_context})" if parent_context else ""
            formatted_prompt = self.prompt_loader.format_prompt(
                "concept",
                context_info=context_info,
                topic_name=topic.name,
                content=topic.content[:500] + "..." if len(topic.content) > 500 else topic.content
            )
            
            # Generate with LLM using configured temperature
            response = self.llm.generate(
                formatted_prompt, 
                temperature=prompt_config.get('temperature', 0.3)
            )
            self.generation_stats["llm_calls"] += 1
            
            # Parse response using configured separator
            separator = prompt_config.get('separator', '::')
            if separator in response:
                front, back = response.split(separator, 1)
                card = Flashcard(
                    card_type=CardType.CONCEPT,
                    front=front.strip(),
                    back=back.strip(),
                    parent=parent_context,
                    tags=[topic.name],
                    difficulty=getattr(topic, 'difficulty', 'intermediate')
                )
                self.generation_stats["by_type"]["concept"] += 1
                return card
                
        except Exception as e:
            logger.warning(f"Failed to generate concept card for {topic.name}: {e}")
        
        return None
    
    def _generate_basic_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate basic Q&A cards using YAML prompts."""
        if not self.config.get('card_types', {}).get('basic', True):
            return []
        
        cards = []
        
        try:
            # Get prompt configuration from YAML
            prompt_config = self.prompt_loader.get_config("basic")
            
            # Format prompt with topic data
            context_info = f" (part of {parent_context})" if parent_context else ""
            examples_text = f"Examples: {', '.join(topic.examples[:3])}\n" if topic.examples else ""
            concepts_text = f"Key concepts: {', '.join(topic.key_concepts[:5])}\n" if topic.key_concepts else ""
            
            formatted_prompt = self.prompt_loader.format_prompt(
                "basic",
                context_info=context_info,
                topic_name=topic.name,
                content=topic.content,
                examples_text=examples_text,
                concepts_text=concepts_text
            )
            
            # Generate with LLM
            response = self.llm.generate(
                formatted_prompt, 
                temperature=prompt_config.get('temperature', 0.4)
            )
            self.generation_stats["llm_calls"] += 1
            
            # Parse multiple cards using configured separator
            separator = prompt_config.get('separator', '>>')
            lines = [line.strip() for line in response.split('\n') if separator in line]
            
            max_cards = prompt_config.get('max_cards', 3)
            for line in lines[:max_cards]:
                if separator in line:
                    front, back = line.split(separator, 1)
                    card = Flashcard(
                        card_type=CardType.BASIC,
                        front=front.strip(),
                        back=back.strip(),
                        parent=parent_context,
                        tags=[topic.name],
                        difficulty=getattr(topic, 'difficulty', 'intermediate')
                    )
                    cards.append(card)
                    self.generation_stats["by_type"]["basic"] += 1
                    
        except Exception as e:
            logger.warning(f"Failed to generate basic cards for {topic.name}: {e}")
        
        return cards
    
    def _generate_cloze_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate cloze deletion cards using YAML prompts."""
        if not self.config.get('card_types', {}).get('cloze', True):
            return []
        
        cards = []
        
        try:
            # Get prompt configuration from YAML
            prompt_config = self.prompt_loader.get_config("cloze")
            
            # Format prompt with topic data
            context_info = f" (part of {parent_context})" if parent_context else ""
            examples_text = f"Examples: {', '.join(topic.examples[:3])}\n" if topic.examples else ""
            concepts_text = f"Key concepts: {', '.join(topic.key_concepts[:5])}\n" if topic.key_concepts else ""
            
            formatted_prompt = self.prompt_loader.format_prompt(
                "cloze",
                context_info=context_info,
                topic_name=topic.name,
                content=topic.content[:300] + "..." if len(topic.content) > 300 else topic.content,
                examples_text=examples_text,
                concepts_text=concepts_text
            )
            
            # Generate with LLM
            response = self.llm.generate(
                formatted_prompt, 
                temperature=prompt_config.get('temperature', 0.3)
            )
            self.generation_stats["llm_calls"] += 1
            
            # Parse cloze cards (look for lines with cloze deletions)
            lines = [line.strip() for line in response.split('\n') 
                    if '{{' in line and '}}' in line]
            
            max_cards = prompt_config.get('max_cards', 2)
            for line in lines[:max_cards]:
                card = Flashcard(
                    card_type=CardType.CLOZE,
                    front=line,
                    back="",  # Cloze cards don't have separate backs
                    parent=parent_context,
                    tags=[topic.name],
                    difficulty=getattr(topic, 'difficulty', 'intermediate')
                )
                cards.append(card)
                self.generation_stats["by_type"]["cloze"] += 1
                
        except Exception as e:
            logger.warning(f"Failed to generate cloze cards for {topic.name}: {e}")
        
        return cards
    
    def _generate_descriptor_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate descriptor cards for attributes using YAML prompts."""
        if not self.config.get('card_types', {}).get('descriptor', True):
            return []
        
        cards = []
        
        try:
            # Get prompt configuration from YAML
            prompt_config = self.prompt_loader.get_config("descriptor")
              # Generate from key concepts with configured format
            max_descriptors = prompt_config.get('max_cards', 3)
            
            for concept in topic.key_concepts[:max_descriptors]:
                card = Flashcard(
                    card_type=CardType.DESCRIPTOR,
                    front=concept,
                    back=f"Key concept of {topic.name}",
                    parent=topic.name,
                    tags=[topic.name, "key_concept"],
                    difficulty=getattr(topic, 'difficulty', 'intermediate'),
                    direction=CardDirection.BIDIRECTIONAL  # Use ;; syntax for descriptors
                )
                cards.append(card)
                self.generation_stats["by_type"]["descriptor"] += 1
                
        except Exception as e:
            logger.warning(f"Failed to generate descriptor cards for {topic.name}: {e}")
        
        return cards
    
    def _is_unique_card(self, card: Flashcard) -> bool:
        """Check if card is unique (not a duplicate)."""
        if card.source_hash in self.generated_cards:
            self.generation_stats["duplicates_avoided"] += 1
            return False
        return True
    
    def _register_card(self, card: Flashcard) -> None:
        """Register card as generated to avoid duplicates."""
        self.generated_cards.add(card.source_hash)
        self.generation_stats["total_cards"] += 1
      # REMOVED: escape_remnote_syntax method
    # This functionality is now handled by RemNoteFormatter._escape_special_chars()
    def validate_card_format(self, card: Flashcard) -> bool:
        """
        Validate that a card follows proper RemNote formatting rules.
        
        Args:
            card: Flashcard to validate
            
        Returns:
            True if card format is valid for RemNote import
        """
        # Basic content validation
        if not card.front:
            return False
            
        # For most card types, back content is required
        if card.card_type != CardType.CLOZE and not card.back and not card.list_items:
            return False
            
        # Validate cloze cards have proper format
        if card.card_type == CardType.CLOZE:
            if not ('{{' in card.front and '}}' in card.front):
                return False
        
        # List cards should have list items
        if card.card_type in [CardType.LIST_ANSWER, CardType.MULTIPLE_CHOICE]:
            if not card.list_items:
                return False
                
        # Check for unescaped delimiters (only flag if they appear to be unintentional)
        dangerous_patterns = [':::', '>>>', ';;;']  # Multi-line delimiters in single-line content
        for pattern in dangerous_patterns:
            if pattern in card.front or pattern in card.back:
                # Allow if this is actually a multi-line card
                if not (card.is_multiline or 'multiline' in card.card_type.value.lower()):
                    logger.warning(f"Potential delimiter conflict in card: {card.front[:50]}...")
                    return False
                
        return True
      # REMOVED: format_card_for_remnote method
    # This functionality is now handled by RemNoteFormatter._format_card()    # REMOVED: generate_hierarchical_output method
    # This functionality is now handled by RemNoteFormatter.format_cards(hierarchy=True)
    def _generate_multiline_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate multi-line cards for complex content."""
        cards = []
        
        try:
            # Generate multi-line concept card for complex definitions
            if len(topic.content) > 200:  # Long content gets multi-line treatment
                card = Flashcard(
                    card_type=CardType.MULTILINE_CONCEPT,
                    front=topic.name,
                    back=topic.content,
                    parent=parent_context,
                    tags=[topic.name, "multiline"],
                    is_multiline=True
                )
                cards.append(card)
                self.generation_stats["by_type"]["multiline_concept"] += 1
        
        except Exception as e:
            logger.warning(f"Failed to generate multiline cards for {topic.name}: {e}")
        
        return cards
    
    def _generate_list_answer_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate list-answer cards from key concepts or examples."""
        cards = []
        
        try:
            # Generate from key concepts if available
            if topic.key_concepts and len(topic.key_concepts) > 1:
                card = Flashcard(
                    card_type=CardType.LIST_ANSWER,
                    front=f"What are the key concepts of {topic.name}?",
                    back="",  # Will be formatted from list_items
                    parent=parent_context,
                    tags=[topic.name, "list"],
                    list_items=topic.key_concepts
                )
                cards.append(card)
                self.generation_stats["by_type"]["list_answer"] += 1
        
        except Exception as e:
            logger.warning(f"Failed to generate list answer cards for {topic.name}: {e}")
        
        return cards
    
    def _generate_multiple_choice_cards(self, topic: Topic, parent_context: Optional[str] = None) -> List[Flashcard]:
        """Generate multiple choice cards when examples are available."""
        cards = []
        
        try:
            # Generate multiple choice from examples
            if topic.examples and len(topic.examples) >= 3:
                # Use first example as correct answer, others as distractors
                choices = topic.examples[:4]  # Limit to 4 choices
                
                card = Flashcard(
                    card_type=CardType.MULTIPLE_CHOICE,
                    front=f"Which is an example of {topic.name}?",
                    back="",  # Will be formatted from list_items
                    parent=parent_context,
                    tags=[topic.name, "multiple_choice"],
                    list_items=choices,
                    correct_choice_index=0
                )
                cards.append(card)
                self.generation_stats["by_type"]["multiple_choice"] += 1
        
        except Exception as e:
            logger.warning(f"Failed to generate multiple choice cards for {topic.name}: {e}")
        
        return cards
        
    def get_stats(self) -> Dict:
        """Get generation statistics."""
        return self.generation_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset generation statistics."""
        self.generated_cards.clear()
        self.generation_stats = {
            "total_cards": 0,
            "by_type": {card_type.value: 0 for card_type in CardType},
            "duplicates_avoided": 0,
            "topics_processed": 0,
            "llm_calls": 0
        }


def main():
    """
    Demo function showing card generation usage.
    """
    print("Card Generator Demo")
    print("This module uses YAML-based prompts for flexible card generation")
    
    try:
        # Test prompt loader
        loader = PromptLoader()
        available_prompts = loader.list_available_prompts()
        print(f"Available prompt templates: {available_prompts}")
        
        print("Card generator ready for use with LLM client and prompt loader")
        print("Import this module and use CardGenerator class")
        
    except Exception as e:
        print(f"Error initializing prompt loader: {e}")
        print("Make sure prompts/ directory exists with YAML files")


if __name__ == "__main__":
    main()
