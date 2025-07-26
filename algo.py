import json
import re

# Heuristic for deciding if a block is heading-like
def is_heading_like(text, line_length):
    text = text.strip()
    if not text or len(text) > 100 or line_length > 100:
        return False
    if re.match(r"^\d+(\.\d+)*[\s:]?", text):  # numbered sections
        return True
    if text.isupper():
        return True
    if text.istitle():
        return True
    if text.endswith(":"):
        return True
    return False

# Main algorithm: font-based heading detection from page 2 onward
def extract_outline_from_page2_onwards(parsed_data):
    all_blocks = []
    
    # Collect all blocks except from page 1
    for page in parsed_data:
        if page["page_number"] == 1:
            continue
        for block in page["content"]:
            block["page"] = page["page_number"]
            all_blocks.append(block)
    
    # Sort all blocks top to bottom
    all_blocks.sort(key=lambda b: (b["page"], b["position_y"]))

    # Get unique font sizes
    font_sizes = sorted({b["font_size"] for b in all_blocks}, reverse=True)

    # Map top 3 sizes to H1, H2, H3
    size_to_level = {}
    if len(font_sizes) > 0:
        size_to_level[font_sizes[0]] = 'H1'
    if len(font_sizes) > 1:
        size_to_level[font_sizes[1]] = 'H2'
    if len(font_sizes) > 2:
        size_to_level[font_sizes[2]] = 'H3'

    # Extract headings
    outline = []
    for block in all_blocks:
        text = block.get("text", "").strip()
        font_size = block.get("font_size", 0)
        line_length = block.get("line_length", len(text))

        if font_size in size_to_level and is_heading_like(text, line_length):
            outline.append({
                "level": size_to_level[font_size],
                "text": text,
                "page": block["page"]
            })

    return outline

# Optional: title from page 1
def extract_title_from_page1(parsed_data):
    page1 = next((p for p in parsed_data if p["page_number"] == 1), None)
    if not page1:
        return "Untitled Document"
    
    blocks = page1["content"]
    top_blocks = sorted([b for b in blocks if b["font_size"] >= 18], key=lambda b: b["position_y"])[:3]
    lines = [b["text"].strip() for b in top_blocks if b["text"].strip()]
    return " ".join(lines) if lines else "Untitled Document"

# Full driver
def process_document(parsed_json_path, output_path="output_rule_based.json"):
    with open(parsed_json_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)

    outline = extract_outline_from_page2_onwards(parsed_data)
    title = extract_title_from_page1(parsed_data)

    final_result = {
        "title": title,
        "outline": outline
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2)

    print(f"✅ Output saved to {output_path}")

# Run this
process_document("extracted_cleaned_lines.json")
