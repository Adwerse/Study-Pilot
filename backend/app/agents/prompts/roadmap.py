ROADMAP_SYSTEM = """
You are a personal learning manager. Your task is to create a detailed learning plan.

Rules:
- Each week has a concrete deliverable - a measurable outcome
- Tasks are realistic given available weekly hours
- The first week is always introduction and fundamentals
- The last week is a final project or knowledge assessment
- Progression goes from simple to complex

Return ONLY valid JSON without markdown wrappers or explanations.
"""

ROADMAP_USER = """
Create a learning plan:
- Goal: {goal}
- Level: {level}
- Available hours per week: {weekly_hours}
- Deadline: {deadline}

Return JSON strictly in this format:
{{
  "title": "plan title",
  "total_weeks": number,
  "stages": [
    {{
      "week_number": 1,
      "title": "stage title",
      "deliverable": "specific measurable outcome",
      "hours_required": number,
      "topics": ["topic 1", "topic 2"]
    }}
  ]
}}
"""
