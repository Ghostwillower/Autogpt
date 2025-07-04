"""Planner module for Ghosthand.

This module contains logic to translate a natural language instruction
into a list of concrete actions for the other agent modules. The main
entry point is :func:`generate_plan` which performs naive keyword based
planning.
"""

import ast
from typing import Dict, List

from memory import query_memory, get_preference
from logger import log


def parse_plan_string(plan_text: str) -> List[Dict[str, object]]:
    """Parse a plan string into a list of step dictionaries."""

    try:
        plan = ast.literal_eval(plan_text)
    except Exception as exc:
        raise ValueError(f"Invalid plan string: {exc}") from exc
    if not isinstance(plan, list):
        raise ValueError("Plan is not a list")
    return plan


def generate_plan(goal: str, user: str) -> List[Dict[str, object]]:
    """Generate a step-by-step plan from a natural language goal.

    Each step is represented as a dictionary with ``agent``, ``action`` and
    ``params`` keys. The function relies on very simple heuristics to map
    common keywords to agent actions. If no keywords are recognised a
    fallback step is returned which passes the goal to a generic LLM
    agent for interpretation.

    Parameters
    ----------
    goal:
        The natural language instruction provided by the user.

    Returns
    -------
    list of dict
        A sequential list of action dictionaries.
    """

    g = goal.lower()
    plan: List[Dict[str, object]] = []

    # Display similar past goals if any
    history = query_memory(goal, user=user)
    if history:
        log("Found similar past goals:")
        for ts, gtext, res in history:
            log(f"  {ts}: {gtext} -> {res}")

    # Example heuristic for screenshot tasks
    if "screenshot" in g:
        plan.append({"agent": "file_agent", "action": "find_recent_screenshot", "params": {"user": user}})
        last_ref = "<result_from_step_0>"

        if "text" in g or "ocr" in g:
            plan.append({
                "agent": "utils.ocr",
                "action": "extract_text",
                "params": {"image_path": last_ref, "user": user},
            })
            last_ref = f"<result_from_step_{len(plan)-1}>"

        if "redact" in g:
            plan.append({
                "agent": "file_agent",
                "action": "redact_names",
                "params": {"image_path": last_ref, "user": user},
            })
            last_ref = f"<result_from_step_{len(plan)-1}>"

        if "email" in g or "mail" in g:
            recipient = "teacher@school.uk" if "teacher" in g else None
            if not recipient:
                pref = get_preference(user, "comms", "default_recipient")
                recipient = pref if pref else "<recipient>"
            plan.append({
                "agent": "comms_agent",
                "action": "send_email",
                "params": {
                    "to": recipient,
                    "subject": "Latest screenshot",
                    "attachment": last_ref,
                    "user": user,
                },
            })

    if not plan:
        try:
            import openai  # Lazy import
            import json
            log("Using GPT-4 for plan generation")
            # openai.ChatCompletion.create(...)
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": goal}],
            )
            gpt_plan = completion["choices"][0]["message"]["content"]
            plan = json.loads(gpt_plan)
        except Exception as exc:
            log(f"GPT planning failed: {exc}", "WARNING")
            plan = [
                {
                    "agent": "builtins",
                    "action": "print",
                    "params": {"text": "Goal not understood.", "user": user},
                }
            ]

    # Ensure user parameter is propagated to all steps
    for step in plan:
        step.setdefault("params", {}).setdefault("user", user)

    return plan

