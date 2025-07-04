"""Main entry point and orchestration utilities for the Ghosthand agent.

This module exposes helper functions for executing a natural language goal.
It interacts with the :mod:`planner` to obtain a list of steps and then
dispatches those steps to the appropriate agent modules.
"""

import importlib
import argparse
import os
from datetime import datetime
from typing import Any, List, Optional

from planner import generate_plan, parse_plan_string
from memory import log_goal, log_voice_verification
from loyalty import loyalty
from security import identity_verified
from logger import log
from user_profile import detect_user
import goal_queue
from file_indexer import build_file_index
from skill_loader import load_skills, get_skill
from core_guard import initialize_core, verify_integrity
from voice_auth import record_voice_sample, verify_user, enroll_user, is_enrolled

try:
    import voice_output  # optional
except Exception:
    voice_output = None


def _execute_steps(plan: List[dict], dry_run: bool, speak: bool, user: str) -> List[Any]:
    results: List[Any] = []

    for idx, step in enumerate(plan):
        step = loyalty.enforce_rules(step, user)
        if not step:
            log(f"Step {idx} blocked by loyalty core", "GUARD")
            results.append(None)
            continue

        agent_name = step.get("agent")
        action_name = step.get("action")
        params = step.get("params", {}).copy()

        if speak and voice_output:
            voice_output.speak(f"Step {idx}: {agent_name}.{action_name}")

        for key, val in list(params.items()):
            if isinstance(val, str) and val.startswith("<result_from_step_") and val.endswith(">"):
                try:
                    ref_index = int(val[len("<result_from_step_") : -1])
                    params[key] = results[ref_index]
                except Exception as exc:
                    log(f"Failed to resolve parameter {val}: {exc}", "WARNING")

        params.setdefault("user", user)

        log(f"Executing step {idx}: {agent_name}.{action_name}({params})")
        if dry_run:
            log("Dry-run active: skipping execution")
            results.append(None)
            continue
        try:
            if agent_name.startswith("skill:"):
                skill_name = agent_name.split(":", 1)[1]
                log(f"Running skill {skill_name}", "SKILL")
                skill = get_skill(skill_name)
                if not skill:
                    raise RuntimeError(f"Skill {skill_name} not loaded")
                result = skill.execute(**params)
            else:
                try:
                    module = importlib.import_module(agent_name)
                except ModuleNotFoundError:
                    module = importlib.import_module(f"agents.{agent_name}")
                func = getattr(module, action_name)
                result = func(**params)

            results.append(result)
            log(f"Step {idx} returned: {result}")
            if speak and voice_output:
                voice_output.speak(f"Step {idx} completed")
        except Exception as exc:
            log(f"Step {idx} failed: {exc}", "ERROR")
            break

    return results


def run_goal(goal: str, dry_run: bool = False, speak: bool = False, user: str = "default") -> List[Any]:
    log(f"Goal received for {user}: {goal}")
    if not identity_verified(user):
        log("Identity verification failed", "GUARD")
        return []
    if not loyalty.can_execute(goal, user):
        return []
    if speak and voice_output:
        voice_output.speak(f"Running goal for {user}")

    home = os.path.expanduser("~")
    build_file_index([os.path.join(home, p) for p in ["Downloads", "Documents", "Desktop"]])
    plan = generate_plan(goal, user)
    log(f"Generated plan: {plan}")

    results = _execute_steps(plan, dry_run, speak, user)

    summary = str(results[-1]) if results else "no result"
    try:
        log_goal(goal, summary, user)
    except Exception as exc:
        log(f"Failed to log goal: {exc}", "ERROR")
    if speak and voice_output:
        voice_output.speak("Goal complete")

    return results


def run_plan_direct(plan_text: str, user: str = "default", dry_run: bool = False) -> List[Any]:
    log(f"Running direct plan for {user}")
    if not identity_verified(user) or not loyalty.can_execute("direct", user):
        return []

    try:
        plan = parse_plan_string(plan_text)
    except Exception as exc:
        log(f"Failed to parse plan: {exc}", "ERROR")
        return []

    results = _execute_steps(plan, dry_run, False, user)

    summary = str(results[-1]) if results else "no result"
    try:
        log_goal(f"direct:{plan_text}", summary, user)
    except Exception as exc:
        log(f"Failed to log direct plan: {exc}", "ERROR")
    return results


def run_test_goal(dry_run: bool = False, speak: bool = False, user: str = "default") -> None:
    goal = "Find the latest screenshot, redact any names, and email it to my teacher."
    results = run_goal(goal, dry_run=dry_run, speak=speak, user=user)
    log(f"Test goal completed with results: {results}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ghosthand AI Agent")
    parser.add_argument("--goal", help="Goal for the agent")
    parser.add_argument("--user", help="Specify user id")
    parser.add_argument("--queue", help="Queue a goal to run later")
    parser.add_argument("--at", help="Time for queued goal (YYYY-MM-DD HH:MM)")
    parser.add_argument("--repeat", help="Goal text to repeat")
    parser.add_argument("--every", type=int, help="Minutes between repeats")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without executing")
    parser.add_argument("--voice", action="store_true", help="Capture goal from microphone")
    parser.add_argument("--speak", action="store_true", help="Speak status updates")
    parser.add_argument("--nogui", action="store_true", help="Do not launch the GUI")
    parser.add_argument("--webgui", action="store_true", help="Launch the web React interface")
    parser.add_argument("--skill", help="Run a specific skill plugin")
    parser.add_argument("--re-enroll", action="store_true", help="Re-enrol the authorised user")
    parser.add_argument("--status", action="store_true", help="Show security status")
    args = parser.parse_args()

    initialize_core()
    try:
        verify_integrity()
    except Exception as exc:
        log(f"Integrity check failed: {exc}", "ERROR")
        return

    if args.status:
        log(f"Voiceprint exists: {is_enrolled('william')}")
        return

    if args.re_enroll:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            record_voice_sample(tmp.name, 5)
            user_match = verify_user(tmp.name)
            log_voice_verification(user_match, user_match == 'william')
            if user_match == 'william':
                enroll_user('william', tmp.name)
                log('Re-enrollment completed', 'GUARD')
            else:
                log('Re-enrollment failed: voice mismatch', 'ERROR')
        return

    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        record_voice_sample(tmp.name, 5)
        user_match = verify_user(tmp.name)
    log_voice_verification(user_match, user_match == 'william')
    if user_match != 'william':
        log('Voice verification failed', 'GUARD')
        return

    user = detect_user(args.user)
    skills = load_skills()

    goal_queue.run_due_goals()

    if args.queue:
        run_time = datetime.fromisoformat(args.at) if args.at else datetime.now()
        goal_queue.add_goal(args.queue, user, run_time)
        return

    if args.repeat:
        interval = args.every if args.every else 60
        goal_queue.set_repeat(args.repeat, user, interval)
        return

    if args.voice:
        try:
            from voice_input import listen_and_transcribe
            goal_text = listen_and_transcribe()
        except Exception as exc:
            log(f"Voice input failed: {exc}", "ERROR")
            goal_text = ""
        if goal_text:
            run_goal(goal_text, dry_run=args.dry_run, speak=args.speak, user=user)
        else:
            log("No voice input captured", "WARNING")
        return

    if args.skill:
        skill = get_skill(args.skill)
        if not skill:
            log(f"Skill {args.skill} not found", "ERROR")
        else:
            res = skill.execute(args.goal or "", user=user)
            log(f"Skill result: {res}", "SKILL")
        return

    if args.goal:
        run_goal(args.goal, dry_run=args.dry_run, speak=args.speak, user=user)
        return

    if args.webgui:
        try:
            import bridge_server
            bridge_server.start_server(open_browser=True)
            return
        except Exception as exc:
            log(f"Web GUI unavailable: {exc}", "WARNING")
            return

    if not args.nogui:
        try:
            import gui
            gui.start_gui()
            return
        except Exception as exc:
            log(f"GUI unavailable: {exc}", "WARNING")

    run_test_goal(dry_run=args.dry_run, speak=args.speak, user=user)


if __name__ == "__main__":
    main()

