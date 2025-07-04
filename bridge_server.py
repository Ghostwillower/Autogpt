"""Bridge server exposing HTTP endpoints for the React UI."""

from flask import Flask, request, jsonify
import threading
import webbrowser
from logger import log
from main import run_plan_direct, run_goal
from enrollment import run_enrollment
from memory import list_users, get_recent_goals

app = Flask(__name__, static_folder="react_frontend", static_url_path="")


@app.get("/")
def index():
    """Serve the React interface."""
    return app.send_static_file("index.html")

@app.post('/plan')
def receive_plan():
    data = request.get_json(force=True, silent=True) or {}
    plan_text = data.get('goal_plan', '')
    user = data.get('user', 'default')
    dry_run = bool(data.get('dry_run', False))
    log(f"Bridge received plan for {user}")

    def _run():
        try:
            run_plan_direct(plan_text, user=user, dry_run=dry_run)
        except Exception as exc:  # pragma: no cover - background errors
            log(f"Plan execution failed: {exc}", 'ERROR')

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'status': 'started'})


@app.post('/goal')
def receive_goal():
    data = request.get_json(force=True, silent=True) or {}
    goal = data.get('goal', '')
    user = data.get('user', 'default')
    dry_run = bool(data.get('dry_run', False))
    log(f"Bridge received goal for {user}")

    def _run():
        try:
            run_goal(goal, dry_run=dry_run, user=user)
        except Exception as exc:  # pragma: no cover - background errors
            log(f"Goal execution failed: {exc}", 'ERROR')

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'status': 'started'})


@app.post('/enroll')
def enroll_user():
    log("Enrollment requested via bridge")

    def _run():
        try:
            run_enrollment()
        except Exception as exc:  # pragma: no cover - background errors
            log(f"Enrollment failed: {exc}", 'ERROR')

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'status': 'started'})


@app.get('/users')
def get_users():
    """Return list of known users."""
    users = list_users()
    if 'default' not in users:
        users.insert(0, 'default')
    return jsonify({'users': users})


@app.get('/history')
def get_history():
    """Return recent goal history."""
    limit = int(request.args.get('limit', 5))
    user = request.args.get('user')
    rows = get_recent_goals(limit, user)
    history = [
        {'timestamp': ts, 'goal': g, 'result': r}
        for ts, g, r in rows
    ]
    return jsonify({'history': history})


def start_server(open_browser: bool = False) -> None:
    """Start the bridge Flask server."""
    log("Starting bridge server on port 5169")
    if open_browser:
        webbrowser.open("http://localhost:5169", new=2)
    app.run(port=5169)


if __name__ == '__main__':
    start_server()
