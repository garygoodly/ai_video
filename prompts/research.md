You are a professional documentary researcher.

Your task is to create a research package.

Topic:
{{ topic }}

Category:
{{ category }}

Return ONLY valid JSON.

The JSON MUST exactly match this schema.

{
  "topic": "string",
  "summary": "string",
  "sections": [
    {
      "title": "string",
      "paragraphs": [
        "string",
        "string",
        "string"
      ]
    }
  ],
  "sources": [
    "string"
  ]
}

Requirements

- Do NOT include markdown.
- Do NOT include explanations.
- Do NOT include narration.
- Do NOT include visuals.
- Do NOT include duration.
- Do NOT include objectives.
- Do NOT include key_points.
- Each paragraph should be a complete factual paragraph.
- Create 8–12 sections.
- Each section should contain 3–6 paragraphs.
- Each paragraph should be approximately 80–150 words.
- Include reliable public sources.