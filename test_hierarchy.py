#!/usr/bin/env python3
"""
Test script for hierarchical heading detection
"""

import json
from outline_hierarchy import extract_outline

def main():
    print("🔍 Testing Hierarchical Heading Detection")
    print("=" * 50)
    
    # Extract outline
    extract_outline("extracted_cleaned_lines.json", "test_output.json")
    
    # Load and display results
    with open("test_output.json", 'r', encoding='utf-8') as f:
        result = json.load(f)
    
    print(f"\n📄 Document Title: {result['title']}")
    print(f"📊 Total Headings Found: {len(result['outline'])}")
    
    # Display hierarchy
    print("\n📋 Document Structure:")
    print("-" * 50)
    
    for i, heading in enumerate(result['outline'][:20]):  # Show first 20 headings
        indent = "  " * (len(heading['level']) - 1)
        print(f"{indent}{heading['level']}: {heading['text']} (Page {heading['page']})")
    
    if len(result['outline']) > 20:
        print(f"  ... and {len(result['outline']) - 20} more headings")
    
    # Show statistics
    level_counts = {}
    for heading in result['outline']:
        level = heading['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    print(f"\n📈 Heading Distribution:")
    for level in sorted(level_counts.keys()):
        print(f"   {level}: {level_counts[level]} headings")

if __name__ == "__main__":
    main() 