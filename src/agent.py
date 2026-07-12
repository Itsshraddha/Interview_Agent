"""
agent.py
========
End-to-end orchestration for the Interview Trainer Agent.

Flow
----
1. Optionally parse & summarize the uploaded resume/JD (resume_parser.py).
2. Build a retrieval query from role + experience + resume skills.
3. Retrieve top-k context chunks from ChromaDB (retriever.py).
4. Assemble the structured prompt (prompt_templates.py).
5. Call IBM Granite / Llama via ModelInference (watsonx_client.py).
6. Parse the JSON response into a typed Python dict.
7. Return the structured prep-kit dict to the Flask API.
"""

import io
import json
import re
from typing import Optional, TypedDict

from ibm_watsonx_ai.foundation_models import ModelInference

from src.watsonx_client import get_generation_model
from src.retriever import retrieve_context
from src.resume_parser import extract_resume_text, summarize_resume
from src.prompt_templates import build_prompt


# ── Typed output schema (v2) ──────────────────────────────────────────────────

class TechnicalQuestion(TypedDict):
    question:           str
    difficulty:         str            # "foundational" | "intermediate" | "advanced"
    why_asked:          str
    model_answer:       str
    code_example:       Optional[str]
    tips:               list[str]      # 3 items
    follow_up_question: str


class BehavioralQuestion(TypedDict):
    question:            str
    competency_tested:   str
    star_answer_outline: str
    red_flags_to_avoid:  list[str]     # 2 items
    tips:                list[str]     # 3 items


class PrepKit(TypedDict):
    technical_questions:          list[TechnicalQuestion]
    behavioral_questions:         list[BehavioralQuestion]
    confidence_checklist:         list[str]
    role_study_roadmap:           dict
    questions_to_ask_interviewer: list[str]


# ── JSON extraction / repair ──────────────────────────────────────────────────

def _extract_json(raw: str) -> str:
    """
    Extract the first complete, balanced JSON object from raw model output.

    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - Preamble text before the opening brace
    - Extra text / second JSON block AFTER the closing brace  ← key fix
    - Nested braces inside field values (e.g. code_example with dicts)

    Uses a depth counter instead of rfind("}") so we stop at the exact
    closing brace that matches the opening one — not the last "}" in the
    entire string (which may belong to appended text from the model).
    """
    # 1. Strip markdown code fences
    fenced = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    fenced = fenced.replace("```", "")

    # 2. Find the first opening brace
    start = fenced.find("{")
    if start == -1:
        raise ValueError(
            "Could not locate a JSON object in the model's response.\n"
            f"Raw output (first 500 chars):\n{raw[:500]}"
        )

    # 3. Walk forward from start, tracking brace depth.
    #    Stop as soon as depth returns to 0 — that is the matching '}'.
    depth = 0
    in_string = False
    escape_next = False
    end = -1

    for i, ch in enumerate(fenced[start:], start=start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    if end == -1:
        raise ValueError(
            "JSON object in model response is not properly closed (truncated output).\n"
            "Try regenerating — the response may have been cut off by token limit.\n"
            f"Raw output (first 500 chars):\n{raw[:500]}"
        )

    return fenced[start: end + 1]


def _parse_response(raw: str) -> PrepKit:
    """
    Parse the model's raw text output into a PrepKit dict.
    Falls back to a structured error dict if parsing fails completely.
    """
    try:
        cleaned = _extract_json(raw)
        data = json.loads(cleaned)
    except (ValueError, json.JSONDecodeError) as exc:
        return PrepKit(
            technical_questions=[
                TechnicalQuestion(
                    question="⚠️ The model returned an unparseable response.",
                    difficulty="intermediate",
                    why_asked="N/A",
                    model_answer=f"Raw model output (first 800 chars):\n\n{raw[:800]}",
                    code_example=None,
                    tips=[
                        "Try regenerating — the model occasionally produces malformed JSON.",
                        f"Parse error detail: {exc}",
                        "If the error persists, check your watsonx.ai API status.",
                    ],
                    follow_up_question="N/A",
                )
            ],
            behavioral_questions=[],
            confidence_checklist=[
                "Regenerate the prep kit using the Generate button.",
                "If the error persists, check the watsonx.ai API status.",
            ],
            role_study_roadmap={
                "week_1": ["Regenerate the prep kit to get your study plan."],
                "week_2": [],
                "day_before": [],
            },
            questions_to_ask_interviewer=[],
        )

    # ── Normalise technical questions ────────────────────────────────────────
    normalised_technical: list[TechnicalQuestion] = []
    for item in data.get("technical_questions", []):
        normalised_technical.append(
            TechnicalQuestion(
                question=item.get("question", "(no question)"),
                difficulty=item.get("difficulty", "intermediate"),
                why_asked=item.get("why_asked", ""),
                model_answer=item.get("model_answer", "(no answer provided)"),
                code_example=item.get("code_example", None),
                tips=item.get("tips", []),
                follow_up_question=item.get("follow_up_question", ""),
            )
        )

    # ── Normalise behavioral questions ───────────────────────────────────────
    normalised_behavioral: list[BehavioralQuestion] = []
    for item in data.get("behavioral_questions", []):
        normalised_behavioral.append(
            BehavioralQuestion(
                question=item.get("question", "(no question)"),
                competency_tested=item.get("competency_tested", ""),
                star_answer_outline=item.get("star_answer_outline", "(no outline provided)"),
                red_flags_to_avoid=item.get("red_flags_to_avoid", []),
                tips=item.get("tips", []),
            )
        )

    # ── Extract new top-level fields ─────────────────────────────────────────
    roadmap = data.get("role_study_roadmap", {})
    if not isinstance(roadmap, dict):
        roadmap = {}

    q_to_ask = data.get("questions_to_ask_interviewer", [])
    if not isinstance(q_to_ask, list):
        q_to_ask = []

    checklist = data.get("confidence_checklist", [])

    return PrepKit(
        technical_questions=normalised_technical,
        behavioral_questions=normalised_behavioral,
        confidence_checklist=checklist if isinstance(checklist, list) else [],
        role_study_roadmap=roadmap,
        questions_to_ask_interviewer=q_to_ask,
    )


# ── Main orchestration function ───────────────────────────────────────────────

def generate_prep_kit(
    candidate_name: str,
    target_role: str,
    experience_level: str,
    uploaded_file: Optional[io.BytesIO] = None,
    top_k: int = 5,
) -> PrepKit:
    """
    Generate a tailored interview preparation kit for the candidate.

    Parameters
    ----------
    candidate_name   : The candidate's name.
    target_role      : The job role they are interviewing for.
    experience_level : Self-reported level (e.g. "Mid Level (2-5 years)").
    uploaded_file    : Optional PDF or .txt file-like object.
    top_k            : Number of knowledge-base chunks to retrieve (default 5).

    Returns
    -------
    A PrepKit TypedDict with technical questions, behavioral questions,
    confidence checklist, study roadmap, and questions to ask the interviewer.
    """
    # ── Step 1: Load the generation model ────────────────────────────────────
    model: ModelInference = get_generation_model()

    # ── Step 2: Parse & summarise the uploaded resume/JD (optional) ──────────
    resume_summary = ""
    if uploaded_file is not None:
        try:
            raw_text = extract_resume_text(uploaded_file)
            if raw_text.strip():
                resume_summary = summarize_resume(raw_text, model)
        except Exception as exc:
            resume_summary = f"[Resume parsing error: {exc}]"

    # ── Step 3: Build the retrieval query ─────────────────────────────────────
    retrieval_query = f"{target_role} interview questions {experience_level}"
    if resume_summary and not resume_summary.startswith("["):
        retrieval_query += f" skills: {resume_summary[:200]}"

    # ── Step 4: Retrieve context from ChromaDB ────────────────────────────────
    try:
        context_chunks = retrieve_context(retrieval_query, k=top_k)
    except RuntimeError as exc:
        raise RuntimeError(str(exc)) from exc

    # ── Step 5: Build the prompt ──────────────────────────────────────────────
    prompt = build_prompt(
        candidate_name=candidate_name,
        target_role=target_role,
        experience_level=experience_level,
        context_chunks=context_chunks,
        resume_summary=resume_summary,
    )

    # ── Step 6: Call the model ────────────────────────────────────────────────
    try:
        raw_output = model.generate_text(prompt=prompt)
    except Exception as exc:
        raise RuntimeError(
            f"watsonx.ai API call failed: {exc}\n"
            "Check your credentials in .env and that your Watson Machine "
            "Learning instance is active on IBM Cloud."
        ) from exc

    # ── Step 7: Parse the JSON response ──────────────────────────────────────
    prep_kit = _parse_response(raw_output)

    return prep_kit
