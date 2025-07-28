# Adobe Hackathon – Round 1A: Structural Hierarchical Inference from Document Layouts

---

## Problem Statement

This task involves the extraction of a precise hierarchical outline from a multi-page PDF document (up to 50 pages). The goal is to reconstruct the document’s latent structure by generating:

- The document’s title
- A nested heading architecture (up to three levels: H1 → H2 → H3)
- Explicit page number references for each identified heading

The primary objective is to algorithmically infer a logical document outline grounded in typographic, geometric, and stylistic signals.

---

## Methodological Framework

The implemented pipeline synthesizes low-level layout data with semantic heuristics to infer a document’s structural hierarchy. It leverages layout geometry, visual typographic cues, and rule-based logic to systematically organize section headers.

---

### Stage 1: Visual Line Aggregation and Feature Extraction

- Extract and normalize visible text spans from the document.
- Cluster spans based on vertical alignment to form logical line groups.
- Merge adjacent spans to construct complete line blocks.
- For each line, extract a comprehensive feature set:
  - Relative font size
  - Font family classification
  - Bold/Italic presence
  - Textual length
  - Horizontal alignment (centered or not)
  - Text case (UPPER, Title Case, etc.)

Each line is transformed into a metadata-enriched candidate unit for structural analysis.

---

### Stage 2: Probabilistic Heuristic Scoring

Lines are evaluated for their likelihood of being structural headings based on a weighted scoring schema derived from typographic and syntactic cues:

| Attribute                              | Score Contribution |
|----------------------------------------|--------------------|
| Dominant font size (contextual)        | +3                 |
| Bold or Italic typography              | +1                 |
| Center alignment                       | +1                 |
| Terminal punctuation (e.g., colon)     | +1                 |
| Enumeration markers (e.g., 1., A., I.) | +1                 |
| Title or UPPER case                    | +1                 |
| Concise length (< 100 characters)      | +1                 |

Any line that exceeds a configurable cumulative threshold is promoted as a likely section header, irrespective of relative font size.

---

### Stage 3: Recursive Hierarchy Construction

- Sort candidate blocks by page order and vertical coordinates.
- Analyze distribution of font sizes to identify tiered heading levels:
  - H1 → Maximum font size category
  - H2 → Next highest tier within H1 subranges
  - H3 → Further subdivision within H2 partitions

- Headings qualifying through heuristic scoring (but not font-based hierarchy) are embedded at the same hierarchical level but do not initiate recursive depth expansion.

---

### Stage 4: Structured Output Serialization

The final document structure is emitted in a standardized JSON format:

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
