# Adobe Hackathon – Round 1A  
### Structural Hierarchical Inference from Document Layouts

---

## Problem Statement

The task is to infer a structured, hierarchical outline from a multi-page PDF document (up to 50 pages). The goal is to extract:

- The document's **title** (from the first page)
- A **nested heading hierarchy** (up to three levels: H1 → H2 → H3)
- The **page number** for each identified heading

The system should deduce structure using layout, typography, and semantic signals—without relying on predefined styles or bookmarks.

---

## Solution Overview

The pipeline is divided into four primary stages:

---

### 1. Line Aggregation and Feature Extraction

- Extract visible text spans from each page.
- Merge adjacent spans based on vertical alignment to form line blocks.
- For every line, extract features:
  - Relative font size
  - Font family/type classification
  - Bold or Italic styling
  - Horizontal alignment (e.g., centered)
  - Text casing (e.g., UPPERCASE, Title Case)
  - Character count and token length

These metadata-enriched lines form the candidate pool for structural analysis.

---

### 2. Heuristic Scoring for Heading Detection

Each line is scored based on its typographic and syntactic properties using a weighted heuristic system:

| Attribute                            | Score |
|--------------------------------------|-------|
| Dominant relative font size          | +3    |
| Bold or Italic styling               | +1    |
| Center alignment                     | +1    |
| Ends with terminal punctuation       | +1    |
| Contains enumeration (e.g., 1., A.)  | +1    |
| Title Case or UPPERCASE formatting   | +1    |
| Concise length (< 100 characters)    | +1    |

Lines that exceed a configurable threshold are treated as structural heading candidates.

---

### 3. Hierarchical Outline Construction

- Candidates are sorted by page and vertical position.
- Font size clusters are analyzed to define heading levels:
  - Largest → **H1**
  - Next tier → **H2**
  - Subsequent tier → **H3**
- Recursively assign nested levels:
  - H2 appears under the preceding H1
  - H3 appears under the closest preceding H2
- Headers lacking clear hierarchy are inserted at the nearest logical level

---

### 4. Structured Output Format

The extracted structure is serialized as follows:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "1. Introduction",
      "page": 2
    },
    {
      "level": "H2",
      "text": "1.1 Scope",
      "page": 2
    },
    {
      "level": "H3",
      "text": "1.1.1 Terminology",
      "page": 3
    }
  ]
}
