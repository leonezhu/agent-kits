# Laya HTTP 服务协议

## 启动

```bash
LAYA_MODEL_PATH=/path/to/laya_model_slim python laya_server.py
# 默认 127.0.0.1:8600，改端口: LAYA_PORT=8700
```

## POST /ask

请求：
```bash
curl -s localhost:8600/ask -H 'Content-Type: application/json' -d '{
  "state": {"tool": "delete_file", "args": {"path": "/shared/config.yaml"}},
  "questions": {
    "risk": {"type": "choice", "instructions": "Assess execution risk.",
             "criteria": {"low": "read-only operations",
                          "medium": "reversible writes",
                          "high": "irreversible or external effects"}},
    "needs_approval": {"type": "noul", "instructions": "Should a human approve this before execution?"}
  }
}'
```

响应：
```json
{
  "risk": {"choice": "high", "probabilities": {...}, "confidence": 0.19},
  "needs_approval": {"noul": 0.42, "confidence": 0.42}
}
```

## GET /health

`{"ok": true, "model": "<路径>"}` —— 部署后先打这个确认权重加载成功。

## 判断器可插拔

把 `/ask` 的实现换成转发 `api.typesafe.ai`（Jev），调用方（Hermes cron/WorkClaw/Copilot 脚本）零改动。
