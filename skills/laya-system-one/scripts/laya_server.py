"""
Laya System 1 judgment server.

Run:    LAYA_MODEL_PATH=/path/to/laya_model_slim python laya_server.py
Query:  curl -s localhost:8600/ask -H 'Content-Type: application/json' \
        -d '{"state": "text or dict", "questions": {"q": {"type": "noul", "instructions": "..."}}}'

Any agent can consume judgments via HTTP; swap the /ask implementation to
forward api.typesafe.ai (Jev) later with zero caller changes.
"""
import warnings

warnings.filterwarnings("ignore")
import os

import laya
from flask import Flask, jsonify, request

MODEL_PATH = os.environ.get("LAYA_MODEL_PATH", "/path/to/laya_model_slim")
PORT = int(os.environ.get("LAYA_PORT", 8600))

agent = laya.load(MODEL_PATH, device="cpu")
app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "model": MODEL_PATH})


@app.route("/ask", methods=["POST"])
def ask():
    body = request.get_json(silent=True) or {}
    if "state" not in body or "questions" not in body:
        return jsonify({"error": "body must contain 'state' and 'questions'"}), 400
    try:
        result = agent.predict(body["state"], body["questions"])
        return jsonify(result["answers"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT)
