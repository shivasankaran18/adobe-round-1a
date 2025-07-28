# Adobe Hackathon - Round 1B: Persona-Based Document Intelligence

---

## Challenge Goal

Given a persona and their task, automatically analyze a set of PDFs (3–10) and extract:
- Most relevant sections with ranked importance
- Sub-sections with refined summaries

---

## Use Case Example

**Persona**: Investment Analyst  
**Job-to-be-done**: "Analyze revenue trends, R&D investments, and market positioning strategies."  
**Input**: 3 tech company financial reports  
**Output**: Structured JSON with most relevant sections/subsections, ranked by importance.

---

## Approach Overview

This solution combines the structured parsing pipeline from Round 1A with semantic similarity techniques and compact LLM-based summarization.

---

### 1. PDF Preprocessing

- Leverage the existing Round 1A extractor to obtain:
  - Document titles
  - Headings (H1–H3)
  - Associated paragraph-level content

---

### 2. Vector Embedding

- Compute embeddings using Sentence Transformers for:
  - Each heading and its corresponding content block
  - The persona profile and job description

---

### 3. Semantic Matching

- Use cosine similarity to score each section against the persona-job query
- Generate a relevance ranking based on:
  - Content-query alignment
  - Contextual cues from headings and summaries

---

### 4. Refined Summarization

- For top-ranked sections, generate summaries using a lightweight LLM (e.g., `phi-2`, `tiny-llama`)
- Output includes:
  - Clean, human-readable abstracts
  - Compact, factual insights tailored to the persona’s goals

---

### 5. JSON Output Format

```json
{
  "metadata": {
    "documents": ["company1.pdf", "company2.pdf", "company3.pdf"],
    "persona": "Investment Analyst",
    "job_to_be_done": "Analyze revenue trends, R&D investments, and market positioning strategies.",
    "timestamp": "2025-07-28T14:00:00Z"
  },
  "section_rankings": [
    {
      "document": "company1.pdf",
      "page": 12,
      "section_title": "Revenue Analysis",
      "importance_rank": 1
    },
    {
      "document": "company2.pdf",
      "page": 9,
      "section_title": "Market Strategy Overview",
      "importance_rank": 2
    }
  ],
  "subsection_analysis": [
    {
      "document": "company1.pdf",
      "page": 12,
      "section_title": "Revenue Analysis",
      "refined_text": "Company revenue increased by 18% YoY, driven primarily by cloud service subscriptions."
    },
    {
      "document": "company2.pdf",
      "page": 9,
      "section_title": "Market Strategy Overview",
      "refined_text": "The company shifted its focus to emerging markets, improving share in APAC by 11%."
    }
  ]
}
