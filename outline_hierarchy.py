import json
from collections import defaultdict
import re

def load_blocks(parsed_data):
    """Load blocks from pages 2 onwards, sorted by reading order"""
    blocks = []
    for page in parsed_data:
        if page["page_number"] == 1:
            continue  # Skip page 1 as per requirements
        for block in page["content"]:
            block = dict(block)  # Copy to avoid mutating input
            block["page"] = page["page_number"]
            blocks.append(block)
    # Sort by (page_number, position_y) for reading order
    blocks.sort(key=lambda b: (b["page"], b["position_y"]))
    return blocks

def extract_title_from_page1(parsed_data):
    """Extract title from page 1 (optional)"""
    page1 = next((p for p in parsed_data if p["page_number"] == 1), None)
    if not page1:
        return ""
    blocks = page1["content"]
    # Use largest font, top-most
    blocks = sorted(blocks, key=lambda b: (-b["font_size"] if b["font_size"] else 0, b["position_y"]))
    for block in blocks:
        if block["text"].strip():
            return block["text"].strip()
    return ""

def get_filename_from_path(pdf_path):
    """Extract filename without extension from PDF path"""
    import os
    filename = os.path.basename(pdf_path)
    # Remove extension
    name_without_ext = os.path.splitext(filename)[0]
    return name_without_ext

def is_likely_heading(block):
    """Determine if a block is likely to be a heading based on various criteria"""
    text = block["text"].strip()
    
    # Skip very short text (likely fragments)
    if len(text) < 3:
        return False
    
    # Skip very long text (likely paragraphs)
    if len(text) > 300:
        return False
    
    # Skip text that ends with punctuation (likely sentences)
    if text.endswith(('.', '!', '?')):
        return False
    
    # Skip text that starts with lowercase (likely sentences)
    if text and text[0].islower():
        return False
    
    # Check for heading patterns
    heading_patterns = [
        r'^[A-Z][A-Z\s]+$',  # ALL CAPS
        r'^\d+\.',  # Numbered headings
        r'^[IVXLCDM]+\.',  # Roman numerals
        r'^[A-Z]\.',  # Letter headings
        r'^(Section|Chapter|Part|Phase|Round)\b',  # Common heading words
        r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$',  # Title Case
    ]
    
    for pattern in heading_patterns:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    
    # Check if text is short and title case
    if len(text) < 150 and text.istitle():
        return True
    
    # Check if text is short and all caps
    if len(text) < 100 and text.isupper():
        return True
    
    # Check if text is short and starts with capital
    if len(text) < 100 and text and text[0].isupper():
        return True
    
    return False

def get_font_sizes_in_range(blocks, start_idx, end_idx):
    """Get unique font sizes in a specific range, sorted descending"""
    font_sizes = set()
    for i in range(start_idx, end_idx):
        if blocks[i].get("font_size") is not None:
            font_sizes.add(blocks[i]["font_size"])
    return sorted(font_sizes, reverse=True)

def find_headings_in_range(blocks, start_idx, end_idx, level=1, max_level=3):
    """
    Find headings in a specific range using font size hierarchy.
    
    Algorithm:
    1. Find the largest font size in the range - these are H1
    2. For each pair of adjacent H1 headings, analyze the range between them
    3. Find the next largest font size in that sub-range - these are H2
    4. Repeat recursively for H3 (max_level=3)
    """
    if end_idx <= start_idx or level > max_level:
        return []
    
    # Get font sizes in this range
    font_sizes = get_font_sizes_in_range(blocks, start_idx, end_idx)
    if not font_sizes:
        return []
    
    # Find the largest font size (current level)
    current_font_size = font_sizes[0]
    
    # Find all blocks with this font size in the range that are likely headings
    heading_indices = []
    for i in range(start_idx, end_idx):
        if blocks[i].get("font_size") == current_font_size:
            # For level 1 and 2, be more lenient with heading detection
            if level <= 2 or is_likely_heading(blocks[i]):
                heading_indices.append(i)
    
    if not heading_indices:
        return []
    
    outline = []
    
    # Process each heading at current level
    for idx, heading_idx in enumerate(heading_indices):
        # Add current heading
        outline.append({
            "level": f"H{level}",
            "text": blocks[heading_idx]["text"].strip(),
            "page": blocks[heading_idx]["page"]
        })
        
        # Find the range for next level (between current heading and next heading at same level)
        next_heading_idx = heading_indices[idx + 1] if idx + 1 < len(heading_indices) else end_idx
        sub_start = heading_idx + 1
        sub_end = next_heading_idx
        
        # Recursively find sub-headings in this range
        if sub_start < sub_end:
            sub_outline = find_headings_in_range(blocks, sub_start, sub_end, level + 1, max_level)
            outline.extend(sub_outline)
    
    return outline

def extract_outline(parsed_json_path, output_path="output_hierarchy.json"):
    """Main function to extract hierarchical outline from parsed PDF data"""
    with open(parsed_json_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    
    # Load blocks from pages 2 onwards
    blocks = load_blocks(parsed_data)
    
    if not blocks:
        result = {"title": "", "outline": []}
    else:
        # Use filename as title
        title = get_filename_from_path(parsed_json_path)
        
        # Find headings using the hierarchical algorithm
        outline = find_headings_in_range(blocks, 0, len(blocks), level=1, max_level=3)
        
        result = {"title": title, "outline": outline}
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Output saved to {output_path}")
    print(f"📊 Found {len(result['outline'])} headings")
    
    # Print summary
    level_counts = defaultdict(int)
    for item in result['outline']:
        level_counts[item['level']] += 1
    
    print("\n📈 Level Distribution:")
    for level in sorted(level_counts.keys()):
        print(f"   {level}: {level_counts[level]} headings")

if __name__ == "__main__":
    extract_outline("extracted_cleaned_lines.json") 
