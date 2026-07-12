"""
prompt_templates.py
===================
Upgraded structured prompt template for the IBM Granite / Llama generation model.

Output JSON schema (v2)
-----------------------
{
  "technical_questions": [           // EXACTLY 8 items
    {
      "question":            "string",
      "difficulty":          "foundational | intermediate | advanced",
      "why_asked":           "string",   // what skill/concept this tests
      "model_answer":        "string",   // 3-5 sentences, concrete
      "code_example":        "string | null",
      "tips":                ["string", "string", "string"],  // exactly 3
      "follow_up_question":  "string"
    }
  ],
  "behavioral_questions": [          // EXACTLY 5 items
    {
      "question":            "string",
      "competency_tested":   "string",
      "star_answer_outline": "string",
      "red_flags_to_avoid":  ["string", "string"],  // exactly 2
      "tips":                ["string", "string", "string"]   // exactly 3
    }
  ],
  "confidence_checklist":            ["string", ...],  // 7-10 items
  "role_study_roadmap": {
    "week_1":    ["string", "string", "string"],
    "week_2":    ["string", "string", "string"],
    "day_before": ["string", "string"]
  },
  "questions_to_ask_interviewer": ["string", "string", "string", "string"]
}
"""

# ── System instruction ────────────────────────────────────────────────────────

_SYSTEM_INSTRUCTION = """\
You are a world-class interview coach and hiring manager with 15+ years of experience \
at top technology companies and consulting firms. You have conducted over 2,000 technical \
and behavioral interviews. Your task is to generate a COMPREHENSIVE, DEEPLY PERSONALISED \
interview preparation kit for a specific candidate.

ABSOLUTE RULES — follow these exactly or the output is invalid:
1. Respond with ONLY a single valid JSON object. No markdown, no code fences, \
no explanations before or after the JSON.
2. The JSON must match the schema shown in the example below precisely — same keys, same types.
3. Generate EXACTLY 8 technical questions and EXACTLY 5 behavioral questions.
4. Each technical question MUST have exactly 3 tips, a difficulty tag \
(foundational/intermediate/advanced), a why_asked explanation, \
a follow_up_question, and a code_example (string or null).
5. Each behavioral question MUST have exactly 3 tips, a competency_tested tag, \
and exactly 2 red_flags_to_avoid.
6. confidence_checklist must contain 7 to 10 short, actionable bullet points.
7. role_study_roadmap must include week_1 (3 items), week_2 (3 items), \
and day_before (2 items).
8. questions_to_ask_interviewer must contain exactly 4 thoughtful, role-specific questions.
9. ALL answers must be SPECIFIC and ACTIONABLE — never vague, never generic. \
Reference the retrieved context and the candidate's profile explicitly.
10. Do NOT truncate any field. Complete every field fully.
"""

# ── JSON schema example (compact — saves input tokens) ───────────────────────

_FEW_SHOT_EXAMPLE = """\
### REQUIRED JSON SCHEMA — output must follow this structure exactly ###
{
  "technical_questions": [
    {
      "question": "<string>",
      "difficulty": "<foundational|intermediate|advanced>",
      "why_asked": "<1 sentence>",
      "model_answer": "<3-5 sentences>",
      "code_example": "<short code string or null>",
      "tips": ["<tip 1>", "<tip 2>", "<tip 3>"],
      "follow_up_question": "<string>"
    }
  ],
  "behavioral_questions": [
    {
      "question": "<string>",
      "competency_tested": "<string>",
      "star_answer_outline": "<Situation/Task/Action/Result>",
      "red_flags_to_avoid": ["<pitfall 1>", "<pitfall 2>"],
      "tips": ["<tip 1>", "<tip 2>", "<tip 3>"]
    }
  ],
  "confidence_checklist": ["<item 1>", "...", "<item 7-10>"],
  "role_study_roadmap": {
    "week_1": ["<task 1>", "<task 2>", "<task 3>"],
    "week_2": ["<task 1>", "<task 2>", "<task 3>"],
    "day_before": ["<task 1>", "<task 2>"]
  },
  "questions_to_ask_interviewer": ["<q1>", "<q2>", "<q3>", "<q4>"]
}
### END SCHEMA ###
"""

# ── Main prompt template ──────────────────────────────────────────────────────

_MAIN_TEMPLATE = """\
{system_instruction}

{few_shot_example}

### YOUR TASK ###

Generate a personalised interview preparation kit for the following candidate.

CANDIDATE PROFILE:
- Name: {candidate_name}
- Target Role: {target_role}
- Experience Level: {experience_level}

{resume_section}

RETRIEVED KNOWLEDGE BASE CONTEXT (use this to ground your questions and answers):
---
{context}
---

INSTRUCTIONS:
- Generate 8 technical questions spanning fundamentals (2), applied/project skills (3), \
system design (2), and one growth/culture-fit question (1).
  Calibrate difficulty to experience level:
    Entry Level  → 3 foundational, 4 intermediate, 1 advanced
    Mid Level    → 1 foundational, 4 intermediate, 3 advanced
    Senior Level → 0 foundational, 2 intermediate, 6 advanced
- Generate 5 behavioral questions covering: Collaboration, Leadership/Initiative, \
Problem-solving under pressure, Adaptability/Learning, and Communication/Feedback.
- For EACH technical question, include:
  * difficulty: one of "foundational", "intermediate", "advanced"
  * why_asked: 1 sentence explaining what skill this tests
  * model_answer: 3-5 sentences, concrete and specific
  * code_example: a short relevant code snippet string, or null if not applicable
  * tips: exactly 3 specific, actionable improvement tips (NOT generic advice)
  * follow_up_question: the likely follow-up the interviewer will ask to probe depth
- For EACH behavioral question, include:
  * competency_tested: the core competency (e.g., "Leadership", "Resilience")
  * star_answer_outline: Situation → Task → Action → Result framework filled in
  * red_flags_to_avoid: exactly 2 specific pitfalls candidates make on this question
  * tips: exactly 3 specific, actionable tips
- confidence_checklist: 7-10 short actionable preparation items for this specific profile.
- role_study_roadmap: realistic 2-week study plan + day-before checklist tailored to \
gaps implied by the candidate's level and role.
- questions_to_ask_interviewer: 4 insightful, role-specific questions (not generic).
- If a resume summary is provided, anchor at least 3 technical questions directly to \
the candidate's stated skills and projects.
- Base questions and model answers on the retrieved context chunks above.
- Return ONLY the JSON object. No markdown fences. No text before or after the JSON.

JSON OUTPUT:"""


def build_prompt(
    candidate_name: str,
    target_role: str,
    experience_level: str,
    context_chunks: list[str],
    resume_summary: str = "",
) -> str:
    """
    Assemble the full prompt from the template and runtime values.

    Parameters
    ----------
    candidate_name   : The user's name (personalises the output).
    target_role      : e.g. "Software Engineer", "Data Analyst".
    experience_level : e.g. "Entry Level (0-2 years)".
    context_chunks   : Top-k text chunks from the Chroma retrieval step.
    resume_summary   : Optional condensed skills summary from the resume parser.

    Returns
    -------
    A fully assembled prompt string ready to pass to ModelInference.generate_text().
    """
    formatted_context = "\n\n".join(
        f"[Chunk {i + 1}]\n{chunk.strip()}"
        for i, chunk in enumerate(context_chunks)
    )

    if resume_summary and resume_summary.strip():
        resume_section = (
            f"CANDIDATE RESUME / JD SUMMARY:\n{resume_summary.strip()}\n"
        )
    else:
        resume_section = (
            "CANDIDATE RESUME / JD SUMMARY: Not provided — use role and "
            "experience level only.\n"
        )

    return _MAIN_TEMPLATE.format(
        system_instruction=_SYSTEM_INSTRUCTION,
        few_shot_example=_FEW_SHOT_EXAMPLE,
        candidate_name=candidate_name,
        target_role=target_role,
        experience_level=experience_level,
        resume_section=resume_section,
        context=formatted_context,
    )
