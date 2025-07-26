import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]

def build_prompt_for_page(blocks, page_number):
    # Only keep text with their metadata
    formatted_text = "\n".join(
        f"- Text: \"{block['text']}\" (font size: {block['font_size']}, x: {block['position_x']}, y: {block['position_y']})"
        for block in blocks
    )

    prompt = f"""
You are a PDF document structure analyzer.

Below are text blocks extracted from **Page {page_number}** of a PDF.
Each block includes font size, position, and text content.

Your job is to detect only the **headings** and classify them as H1, H2, or H3 based on:
- Font size (larger = higher level)
- Position (top of page = more likely to be title or heading)
- Visual formatting and phrasing

Return the result in this format:

[
  {{ "level": "H1", "text": "Heading Text", "page": {page_number} }},
  {{ "level": "H2", "text": "Subheading", "page": {page_number} }},
  ...
]

Here are the text blocks:

{formatted_text}
"""
    return prompt

def process_parsed_pdf(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_headings = []

    for page in data:
        page_number = page["page_number"]
        blocks = page["content"]

        prompt = build_prompt_for_page(blocks, page_number)
        print(f"\n📄 Sending Page {page_number} to Mistral...\n")
        response = ask_ollama(prompt)

        try:
            parsed_headings = json.loads(response)
            all_headings.extend(parsed_headings)
        except Exception as e:
            print(f"⚠️ Failed to parse response for Page {page_number}: {e}")
            print("Raw Response:\n", response)

    final_output = {
        "title": "Extracted Document",
        "outline": all_headings
    }

    # Save result
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    print("\n✅ Saved output to output.json")

# Call this with your parsed file
process_parsed_pdf("extracted_cleaned_lines.json")
