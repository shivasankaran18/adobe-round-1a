import json

# --- Helper Functions ---
def load_blocks(parsed_data):
    blocks = []
    for page in parsed_data:
        if page["page_number"] == 1:
            continue  # Skip page 1
        for block in page["content"]:
            block = dict(block)  # Copy to avoid mutating input
            block["page"] = page["page_number"]
            blocks.append(block)
    # Sort by (page_number, position_y)
    blocks.sort(key=lambda b: (b["page"], b["position_y"]))
    return blocks

def extract_title_from_page1(parsed_data):
    page1 = next((p for p in parsed_data if p["page_number"] == 1), None)
    if not page1:
        return ""
    blocks = page1["content"]
    # Use largest font, top-most
    blocks = sorted(blocks, key=lambda b: (-b["font_size"], b["position_y"]))
    for block in blocks:
        if block["text"].strip():
            return block["text"].strip()
    return ""

def get_font_sizes(blocks):
    # Get all unique font sizes, descending
    return sorted({b["font_size"] for b in blocks if b.get("font_size") is not None}, reverse=True)

def find_headings(blocks, font_sizes, level=1, start_idx=0, end_idx=None, max_level=4):
    if end_idx is None:
        end_idx = len(blocks)
    if level > max_level or level > len(font_sizes):
        return []
    curr_size = font_sizes[level-1]
    # Only include blocks whose font size matches the current level
    indices = [i for i in range(start_idx, end_idx) if blocks[i].get("font_size") == curr_size]
    if not indices:
        return []
    outline = []
    for idx, i in enumerate(indices):
        outline.append({
            "level": f"H{level}",
            "text": blocks[i]["text"].strip(),
            "page": blocks[i]["page"]
        })
        next_i = indices[idx+1] if idx+1 < len(indices) else end_idx
        outline.extend(find_headings(blocks, font_sizes, level+1, i+1, next_i, max_level))
    return outline

# --- Main Driver ---
def extract_outline(parsed_json_path, output_path="output_hierarchy.json"):
    with open(parsed_json_path, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)
    blocks = load_blocks(parsed_data)
    if not blocks:
        result = {"title": "", "outline": []}
    else:
        font_sizes = get_font_sizes(blocks)
        outline = find_headings(blocks, font_sizes, max_level=4)
        title = extract_title_from_page1(parsed_data)
        result = {"title": title, "outline": outline}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    print(f"✅ Output saved to {output_path}")

if __name__ == "__main__":
    extract_outline("extracted_cleaned_lines.json") 