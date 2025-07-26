import fitz
import json
from collections import defaultdict
import re

def normalize_font_size(size):
    return round(size, 1) if size else None

def round_coord(value, precision=1):
    return round(value, precision) if value is not None else None

def detect_line_case(text):
    if text.isupper():
        return "UPPER"
    elif text.istitle():
        return "TITLE"
    elif text.islower():
        return "LOWER"
    else:
        return "MIXED"


def has_number_marker(text):
    patterns = [
        r"\b(round|phase|section|chapter|part)\s+\d+\b",      # round 1
        r"\b\d+\s+(round|phase|section|chapter|part)\b",      # 1 round
        r"\b(round|phase|section|chapter|part)\s+[IVXLCDM]+\b",  # Phase II
        r"\b[IVXLCDM]+\b"                                     # stand-alone roman numerals
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def has_special_prefix(text):
    text = text.strip()
    patterns = [
        r"^(\d+[\.\)])+",             # 1. 1.1. 2.2.3)
        r"^[IVXLCDM]+\.",             # Roman numerals like I. II. III.
        r"^[A-Z]\.",                  # A. B. C.
        r"^[:_]",                     # Only dash, colon, underline at start
        # r"^(Section|Chapter|Article)\b",  # Remove keywords if not required
        r":+"                         # Anywhere in the line — internal colon
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def is_centered(x, page_width=595.0, tolerance=50):
    center = page_width / 2
    return abs(x - center) < tolerance


def score_line_features(line):
    score = 0.0

    # Bold/Italic
    if line["bold"]:
        score += 1.0
    if line["italic"]:
        score += 0.3

    # Centered
    if line["is_centered"]:
        score += 1.2

    # Case
    if line["line_case"] == "TITLE":
        score += 0.6
    elif line["line_case"] == "UPPER":
        score += 0.5

    # Line length
    if line["line_length"] < 60:
        score += 0.5

    # Starts with number or roman
    if re.match(r"^(\d+[\.\)]|[IVXLCDM]+\.)", line["text"].strip()):
        score += 2.5
    # Contains phase/round/section/chapter/part with number/roman
    if re.search(r"\b(round|phase|section|chapter|part)\s+(\d+|[IVXLCDM]+)", line["text"], re.IGNORECASE):
        score += 0.7

    # Contains colon anywhere
    if ':' in line["text"]:
        score += 0.5

    # Starts with A. B. etc.
    if re.match(r"^[A-Z]\.", line["text"].strip()):
        score += 0.4

    # Ends with colon
    if line["text"].strip().endswith(':'):
        score += 0.5

    # Top of page
    if line.get("position_y", 9999) < 200:
        score += 0.3

    # No punctuation
    if not re.search(r",|\\.|;|!|\\?", line["text"]):
        score += 0.2

    # Punctuation penalty
    if len(re.findall(r",|\\.|;|!|\\?", line["text"])) > 2:
        score -= 0.5

    return score

def extract_pdf_lines_cleaned_and_merged(pdf_path):
    doc = fitz.open(pdf_path)
    pages_data = []

    for page_num, page in enumerate(doc):
        y_line_map = defaultdict(list)
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if block['type'] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue

                    y_key = round(span["bbox"][1], 1)
                    y_line_map[y_key].append({
                        "text": text,
                        "font_size": normalize_font_size(span["size"]),
                        "font_name": span["font"],
                        "bold": "Bold" in span["font"],
                        "italic": "Italic" in span["font"] or "Oblique" in span["font"],
                        "position_x": round(span["bbox"][0], 1),
                        "position_y": y_key,
                        "page_number": page_num + 1
                    })

        page_lines = []
        for y_key in sorted(y_line_map.keys()):
            line_spans = sorted(y_line_map[y_key], key=lambda s: s["position_x"])
            merged_text = " ".join([s["text"] for s in line_spans])
            font_sizes = [s["font_size"] for s in line_spans if s["font_size"] is not None]
            fonts = [s["font_name"] for s in line_spans if s["font_name"]]
            bold = any(s["bold"] for s in line_spans)
            italic = any(s["italic"] for s in line_spans)
            x = min([s["position_x"] for s in line_spans])
            y = y_key

            line_dict = {
                "text": merged_text,
                "font_size": max(font_sizes) if font_sizes else None,
                "font_name": fonts[0] if fonts else None,
                "bold": bold,
                "italic": italic,
                "position_x": x,
                "position_y": y,
                "page_number": page_num + 1,
                "line_length": len(merged_text),
                "is_centered": is_centered(x),
                "line_case": detect_line_case(merged_text)
            }

            # Score and label
            line_dict["heading_score"] = score_line_features(line_dict)
            # line_dict["is_heading"] = line_dict["heading_score"] >= 2.5

            page_lines.append(line_dict)


            # page_lines.append({
            #     "text": merged_text,
            #     "font_size": max(font_sizes) if font_sizes else None,
            #     "font_name": fonts[0] if fonts else None,
            #     "bold": bold,
            #     "italic": italic,
            #     "position_x": x,
            #     "position_y": y,
            #     "page_number": page_num + 1,
            #     "line_length": len(merged_text),
            #     "is_centered": is_centered(x),
            #     "is_heading": is_heading(merged_text)>=2.5
            # })
            print(merged_text)
            print(has_special_prefix(merged_text))

        pages_data.append({
            "page_number": page_num + 1,
            "content": page_lines
        })

    return pages_data

if __name__ == "__main__":
    pdf_path = "Adobe-India-Hackathon25/Challenge_1a/sample_dataset/pdfs/file03.pdf"
    output_path = "extracted_cleaned_lines.json"
    extracted_data = extract_pdf_lines_cleaned_and_merged(pdf_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)