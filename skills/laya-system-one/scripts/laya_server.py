"""
Laya System 1 judgment server, runnable from the command line.

Start:  python laya_server.py
        LAYA_MODEL_PATH=/path/to/laya_model_slim LAYA_PORT=8600 python laya_server.py
        LAYA_FOREGROUND=0 python laya_server.py   # detach: log to file, PID to laya_server.pid

Startup check: if a healthy server already answers on the port, this process exits 0
with a message instead of starting a duplicate. Logs go to stdout (foreground) or
laya_server.log (detached), one line per request with latency, plus /ask results.

Query:  curl -s localhost:8600/ask -H 'Content-Type: application/json' \
        -d '{"state": "text or dict", "questions": {"q": {"type": "noul", "instructions": "..."}}}'

Any agent can consume judgments via HTTP; swap the /ask implementation to
forward api.typesafe.ai (Jev) later with zero caller changes.
"""
import json
import os
import sys
import time
import urllib.request
import warnings
from datetime import datetime

warnings.filterwarnings("ignore")

MODEL_PATH = os.environ.get("LAYA_MODEL_PATH", "/path/to/laya_model_slim")
PORT = int(os.environ.get("LAYA_PORT", 8600))
FOREGROUND = os.environ.get("LAYA_FOREGROUND", "1") == "1"
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laya_server.pid")
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "laya_server.log")


def already_running():
    """True if a healthy laya server answers on the target port."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3) as r:
            return json.load(r).get("ok") is True
    except Exception:
        return False


def log(msg):
    """Write to stdout (foreground) and the log file (detached).

    All writes are guarded: a closed/broken stdout must never take the server
    down (a detached process whose original terminal vanished would otherwise
    500 every request the moment it tries to log)."""
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    if not FOREGROUND:
        try:
            with open(LOG_FILE, "a") as f:
                f.write(line + "\n")
        except Exception:
            pass


if already_running():
    print(f"laya server already healthy on :{PORT} - nothing to do", flush=True)
    sys.exit(0)

import laya
from flask import Flask, jsonify, request

t0 = time.time()
log(f"loading weights from {MODEL_PATH} (cpu) ...")
agent = laya.load(MODEL_PATH, device="cpu")
log(f"weights loaded in {time.time() - t0:.1f}s, serving on :{PORT}")

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "model": MODEL_PATH})


@app.route("/ask", methods=["POST"])
def ask():
    t = time.time()
    body = request.get_json(silent=True) or {}
    if "state" not in body or "questions" not in body:
        return jsonify({"error": "body must contain 'state' and 'questions'"}), 400
    try:
        result = agent.predict(body["state"], body["questions"])
        answers = result["answers"]
        summary = {k: v.get("choice") or v.get("score") or v.get("noul") for k, v in answers.items()}
        confs = {k: round(v.get("confidence", 0), 3) for k, v in answers.items()}
        log(f"ask {time.time() - t:.2f}s results={summary} conf={confs}")
        return jsonify(answers)
    except Exception as e:
        log(f"ask FAILED after {time.time() - t:.2f}s: {type(e).__name__}: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if FOREGROUND:
        app.run(host="127.0.0.1", port=PORT)
    else:
        if os.fork():
            sys.exit(0)  # parent exits, child carries on
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        log(f"detached, pid {os.getpid()}, log {LOG_FILE}")
        app.run(host="127.0.0.1", port=PORT)
