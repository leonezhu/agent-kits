# Laya HTTP server protocol

## Start

```bash
LAYA_MODEL_PATH=/path/to/laya_model_slim python scripts/laya_server.py
# default 127.0.0.1:8600, override with LAYA_PORT=8700
```

## POST /ask

Request:
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

Response:
```json
{
  "risk": {"choice": "high", "probabilities": {}, "confidence": 0.19},
  "needs_approval": {"noul": 0.42, "confidence": 0.42}
}
```

## GET /health

`{"ok": true, "model": "<path>"}` - hit this after deploy to confirm weights loaded.

## Swappable judge

Point `/ask` at api.typesafe.ai (Jev) instead; callers change nothing.
