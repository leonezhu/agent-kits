"""
Laya 判断层 HTTP 服务 —— 一次部署, Hermes/WorkClaw/Copilot 全部 curl 即用
启动: python laya_server.py          (默认 8600 端口)
调用: curl -s localhost:8600/ask -H 'Content-Type: application/json' \
      -d '{"state":{"tool":"delete_file","args":{"path":"/x"}},
           "questions":{"risk":{"type":"choice","instructions":"...",
             "criteria":{"low":"read-only","high":"irreversible"}}}}'
返回: {"risk": {"choice": "...", "probabilities": {...}, "confidence": 0.xx}}
"""
import warnings; warnings.filterwarnings('ignore')
import os, laya
from flask import Flask, request, jsonify

MODEL_PATH = os.environ.get("LAYA_MODEL_PATH", "/path/to/laya_model_slim")
agent = laya.load(MODEL_PATH, device="cpu")
app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    body = request.json
    if not body or "state" not in body or "questions" not in body:
        return jsonify({"error": "need {state, questions}"}), 400
    try:
        r = agent.predict(body["state"], body["questions"])
        return jsonify(r["answers"])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "model": MODEL_PATH})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("LAYA_PORT", 8600)))
