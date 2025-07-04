"""Planner module for Ghosthand.

This module contains logic to translate a natural language instruction
into a list of concrete actions for the other agent modules. The main
entry point is :func:`generate_plan` which performs naive keyword based
planning.
"""

import ast
import re
from typing import Dict, List

from memory import query_memory, get_preference
from logger import log
from skill_loader import load_skills


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
    """Generate a step-by-step plan from a natural language goal."""

    g = goal.lower()
    plan: List[Dict[str, object]] = []

    # Check past memory for similar goals
    history = query_memory(goal, user=user)
    if history:
        log("Found similar past goals:")
        for ts, gtext, res in history:
            log(f"  {ts}: {gtext} -> {res}")

    # Skills take priority if one can handle it
    skills = load_skills()
    for name, mod in skills.items():
        try:
            if mod.can_handle(goal):
                log(f"Skill {name} will handle goal", "SKILL")
                return [{
                    "agent": f"skill:{name}",
                    "action": "execute",
                    "params": {"goal": goal, "user": user},
                }]
        except Exception as exc:
            log(f"Skill {name} check failed: {exc}", "ERROR")

    # Keyword search-based heuristics

    if "search" in g or "look up" in g:
        query_match = re.search(r"search (for )?(?P<q>.+)", g)
        query = query_match.group("q") if query_match else goal
        plan.append({
            "agent": "web_search",
            "action": "search_web",
            "params": {"query": query, "user": user}
        })

    url_match = re.search(r"https?://\S+", goal)
    if "download" in g and url_match:
        url = url_match.group(0)
        plan.append({
            "agent": "file_downloader",
            "action": "download_file",
            "params": {"url": url, "user": user}
        })
        download_idx = len(plan) - 1
        if "extract" in g or "unzip" in g:
            plan.append({
                "agent": "file_downloader",
                "action": "extract_file",
                "params": {
                    "path": f"<result_from_step_{download_idx}>",
                    "extract_to": "./downloads",
                    "user": user,
                },
            })

    if ("go to" in g or "open" in g or "fill" in g) and url_match:
        steps = [{"action": "go_to", "url": url_match.group(0)}]
        plan.append({
            "agent": "browser_agent",
            "action": "run_browser_task",
            "params": {"task": {"steps": steps}, "user": user},
        })

    if "screenshot" in g:
        plan.append({"agent": "file_agent", "action": "find_recent_screenshot", "params": {"user": user}})
        last_ref = "<result_from_step_0>"

        if "text" in g or "ocr" in g:
            plan.append({
                "agent": "utils.ocr",
                "action": "extract_text",
                "params": {"image_path": last_ref, "user": user}
            })
            last_ref = f"<result_from_step_{len(plan)-1}>"

        if "redact" in g:
            plan.append({
                "agent": "file_agent",
                "action": "redact_names",
                "params": {"image_path": last_ref, "user": user}
            })
            last_ref = f"<result_from_step_{len(plan)-1}>"

        if "email" in g or "mail" in g:
            recipient = "teacher@school.uk" if "teacher" in g else get_preference(user, "comms", "default_recipient") or "<recipient>"
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

    # Fallback to LLM if nothing matches
    if not plan:
        try:
            import openai
            import json
            log("Using GPT-4 for plan generation")
            completion = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": goal}],
            )
            gpt_plan = completion["choices"][0]["message"]["content"]
            plan = json.loads(gpt_plan)
        except Exception as exc:
            log(f"GPT planning failed: {exc}", "WARNING")
            plan = [{
                "agent": "builtins",
                "action": "print",
                "params": {"text": "Goal not understood.", "user": user},
            }]

    for step in plan:
        step.setdefault("params", {}).setdefault("user", user)

    return plan
