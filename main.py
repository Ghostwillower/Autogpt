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
from memory import log_goal
from logger import log
from user_profile import detect_user
import goal_queue
from file_indexer import build_file_index

try:
    import voice_output  # optional
except Exception:
    voice_output = None


def _execute_steps(plan: List[dict], dry_run: bool, speak: bool, user: str) -> List[Any]:
    """Execute a prepared plan and return step results."""

    results: List[Any] = []

    for idx, step in enumerate(plan):
        agent_name = step.get("agent")
        action_name = step.get("action")
        params = step.get("params", {}).copy()
        if speak and voice_output:
            voice_output.speak(f"Step {idx}: {agent_name}.{action_name}")

        # Replace references to previous results
        for key, val in list(params.items()):
            if (
                isinstance(val, str)
                and val.startswith("<result_from_step_")
                and val.endswith(">")
            ):
                try:
                    ref_index = int(val[len("<result_from_step_") : -1])
                    params[key] = results[ref_index]
                except Exception as exc:  # pragma: no cover - defensive
                    log(f"Failed to resolve parameter {val}: {exc}", "WARNING")

        params.setdefault("user", user)

        log(f"Executing step {idx}: {agent_name}.{action_name}({params})")
        if dry_run:
            log("Dry-run active: skipping execution")
            results.append(None)
            continue
        try:
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
    """Execute a goal using the planner and agent modules.

    Parameters
    ----------
    goal : str
        Natural language instruction from the user.
    dry_run : bool, optional
        When ``True`` just print the planned actions without executing them.
    speak : bool, optional
        When ``True`` provide spoken status updates after each step.

    Returns
    -------
    list
        A list of results from each executed step.
    """

    log(f"Goal received for {user}: {goal}")
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
    except Exception as exc:  # pragma: no cover - log errors only
        log(f"Failed to log goal: {exc}", "ERROR")
    if speak and voice_output:
        voice_output.speak("Goal complete")

    return results


def run_plan_direct(plan_text: str, user: str = "default", dry_run: bool = False) -> List[Any]:
    """Execute a plan provided as a stringified list of steps."""

    log(f"Running direct plan for {user}")
    try:
        plan = parse_plan_string(plan_text)
    except Exception as exc:
        log(f"Failed to parse plan: {exc}", "ERROR")
        return []

    results = _execute_steps(plan, dry_run, False, user)

    summary = str(results[-1]) if results else "no result"
    try:
        log_goal(f"direct:{plan_text}", summary, user)
    except Exception as exc:  # pragma: no cover
        log(f"Failed to log direct plan: {exc}", "ERROR")
    return results


def run_test_goal(dry_run: bool = False, speak: bool = False, user: str = "default") -> None:
    """Run the built-in test scenario."""

    goal = "Find the latest screenshot, redact any names, and email it to my teacher."
    results = run_goal(goal, dry_run=dry_run, speak=speak, user=user)
    log(f"Test goal completed with results: {results}")


def main() -> None:
    """CLI entry point for the Ghosthand agent."""

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
    args = parser.parse_args()

    user = detect_user(args.user)

    # check queued goals first
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

    if args.goal:
        run_goal(args.goal, dry_run=args.dry_run, speak=args.speak, user=user)
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
