from flask import Flask, request, jsonify
import threading
from logger import log
from main import run_plan_direct

app = Flask(__name__)

@app.post('/plan')
def receive_plan():
    data = request.get_json(force=True, silent=True) or {}
    plan_text = data.get('goal_plan', '')
    user = data.get('user', 'default')
    log(f"Bridge received plan for {user}")

    def _run():
        try:
            run_plan_direct(plan_text, user=user)
        except Exception as exc:  # pragma: no cover - background errors
            log(f"Plan execution failed: {exc}", 'ERROR')

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'status': 'started'})


def start_server():
    """Start the bridge Flask server."""
    log("Starting bridge server on port 5169")
    app.run(port=5169)


if __name__ == '__main__':
    start_server()
