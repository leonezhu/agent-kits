# Agent code integration patterns

## Pattern 1: in-process (single script, simplest)

```python
import warnings

warnings.filterwarnings("ignore")
import laya

agent = laya.load("/path/to/laya_model_slim", device="cpu")  # process-level singleton
result = agent.predict(state, questions)["answers"]
```

Fits: single cron scripts, one-off batch jobs.

## Pattern 2: HTTP server (shared across agents/scripts, recommended)

Start via scripts/laya_server.py (see laya-server.md). Any language queries via curl;
the judge is swappable (Laya <-> Jev with zero caller changes).

Fits: multiple scripts/agents sharing one judgment layer; avoids loading
weights 30-60s per process.

## Universal decision pattern: confidence three-way branch

```python
r = answers["qname"]
if r["confidence"] >= 0.85:
    do_auto(r)          # high confidence: act automatically
elif r["confidence"] >= 0.3:
    do_llm_fallback(r)  # middle band: escalate to LLM or human
else:
    do_conservative(r)  # low confidence: conservative default + log
```

Thresholds 0.85/0.3 are starting points. **Backtest 20 known-answer cases per new
scenario before fixing them.**

## Tool gate template (before any agent tool execution)

```python
GATE_Q = {
    "risk": {"type": "choice", "instructions": "Assess execution risk.",
             "criteria": {"low": "read-only operations",
                          "medium": "reversible writes",
                          "high": "irreversible or external effects"}},
    "needs_approval": {"type": "noul", "instructions": "Should a human approve this?"}
}


def gate(tool, args):
    a = agent.predict({"tool": tool, "args": args}, GATE_Q)["answers"]
    if a["needs_approval"]["noul"] >= 0.85:
        return False, "escalate"
    if a["risk"]["choice"] == "high" and a["risk"]["confidence"] >= 0.7:
        return False, "deny"
    return True, a["risk"]["choice"]
```
