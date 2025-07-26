import json
import re

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
    # Use largest font, top-most, centered, or bold
    blocks = sorted(blocks, key=lambda b: (-b["font_size"], b["position_y"]))
    for block in blocks:
        if block["text"].strip():
            return block["text"].strip()
    return ""

def is_heading_like(block):
    text = block.get("text", "").strip()
    if not text or len(text) > 120:
        return False
    # Visual cues
    font_name = block.get("font_name", "").lower()
    bold = block.get("bold", False)
    italic = block.get("italic", False)
    is_centered = block.get("is_centered", False)
    font_size = block.get("font_size", 0)
    line_length = block.get("line_length", len(text))
    position_y = block.get("position_y", 9999)
    # Textual cues
    is_numbered = bool(re.match(r"^(\d+\.|[A-Z]\.|[IVXLCDM]+\.|\d+\))", text))
    ends_colon = text.endswith(":")
    is_all_caps = text.isupper() and len(text) > 2
    is_title_case = text.istitle() and len(text.split()) > 1
    short = len(text.split()) <= 10
    no_punct = not re.search(r",|\.|", text)
    # Heuristic scoring
    score = 0
    if font_size >= 14: score += 2
    if bold or "bold" in font_name or "black" in font_name or "heavy" in font_name: score += 2
    if italic: score += 1
    if is_centered: score += 2
    if is_numbered: score += 1
    if ends_colon: score += 1
    if is_all_caps: score += 1
    if is_title_case: score += 1
    if short: score += 1
    if no_punct: score += 1
    if position_y < 200: score += 1
    # Only consider as heading if score is high enough
    return score >= 4

def get_font_sizes(blocks):
    # Only consider blocks that are heading-like for font size ranking
    heading_blocks = [b for b in blocks if is_heading_like(b)]
    return sorted({b["font_size"] for b in heading_blocks}, reverse=True)

def find_headings(blocks, font_sizes, level=1, start_idx=0, end_idx=None, max_level=4):
    if end_idx is None:
        end_idx = len(blocks)
    if level > max_level or level > len(font_sizes):
        return []
    curr_size = font_sizes[level-1]
    # Find all indices of this font size in the range and heading-like
    indices = [i for i in range(start_idx, end_idx) if blocks[i]["font_size"] == curr_size and is_heading_like(blocks[i])]
    if not indices:
        return []
    outline = []
    # For each heading at this level, recurse for next level in between
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