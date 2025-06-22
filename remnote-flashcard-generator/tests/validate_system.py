"""
Simple validation tests that can run without pytest.

These tests validate basic functionality and can be run directly with Python.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        from yaml_parser import YAMLParser, Topic, MLContent
        from card_generator import CardGenerator, Flashcard, CardType
        from remnote_formatter import RemNoteFormatter
        from llm_client import LLMClient
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without external dependencies."""
    try:
        # Test Topic creation
        from yaml_parser import Topic
        topic = Topic(name="Test", content="Test content")
        assert topic.name == "Test"
        assert topic.content == "Test content"
        print("✅ Topic creation works")
          # Test Flashcard creation
        from card_generator import Flashcard, CardType, CardDirection
        card = Flashcard(
            card_type=CardType.CONCEPT,
            front="Test",
            back="Definition",
            direction=CardDirection.BIDIRECTIONAL  # Specify bidirectional for :: syntax
        )
        assert card.front == "Test"
        assert card.back == "Definition"
        print("✅ Flashcard creation works")
        
        # Test formatter basic functionality
        from remnote_formatter import RemNoteFormatter
        formatter = RemNoteFormatter()
        formatted = formatter._format_card(card)
        expected = "Test :: Definition"
        assert formatted == expected, f"Expected '{expected}', got '{formatted}'"
        print("✅ Basic formatting works")
        
        return True
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_file_existence():
    """Test that required files exist."""
    base_path = Path(__file__).parent.parent
    required_files = [
        "src/yaml_parser.py",
        "src/card_generator.py", 
        "src/remnote_formatter.py",
        "src/llm_client.py",
        "src/main.py",
        "config/config.yaml",
        "content/ml_system_design.yaml",
        "requirements.txt"
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            all_exist = False
            
    return all_exist

def main():
    """Run all validation tests."""
    print("🧪 Running RemNote Flashcard Generator Validation Tests")
    print("=" * 60)
    
    tests = [
        ("File Existence", test_file_existence),
        ("Module Imports", test_imports),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All validation tests passed!")
        print("The system appears to be working correctly.")
        return 0
    else:
        print("⚠️  Some validation tests failed.")
        print("Please check the errors above and ensure all components are properly installed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
