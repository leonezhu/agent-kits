---
name: laya-system-one
description: Use for fast local judgment (classify/route/gate) without LLM calls.
category: devops
---

# Laya: local System 1 judgment engine

Open-source Jev equivalent (Apache 2.0, ModernBERT backbone). Non-autoregressive,
single forward pass, returns typed probabilities with calibrated confidence.
Use whenever an agent needs to ask "should this / which class / how severe"
without burning an LLM call.

## Environment assumptions (ready beforehand)

- venv: python3.10/3.11 (torch 2.2 dyno breaks on 3.12+)
- weights: `laya_model_slim/` directory (742MB slim pack: main model + tokenizer)
- optional server: `python scripts/laya_server.py` then query `localhost:8600/ask`
- required trio: python <= 3.11 / `device="cpu"` (x86 Mac) / transformers==4.48.0

## Interface (there is only one)

```python
import laya
agent = laya.load("<weights dir>", device="cpu")  # in-process singleton, first load 30-60s
result = agent.predict(state, questions)          # state: str|dict, questions: dict
# result["answers"]["qname"] -> {choice|score|noul, probabilities, confidence}
```

## Three primitives (same names as Jev, interchangeable)

| primitive | asks | returns |
|---|---|---|
| `choice` | multi-class routing | per-option probabilities + confidence |
| `score` | ordered scale | continuous score + distribution + confidence |
| `noul` | yes/no | P(true) + confidence |

questions format:
```python
{
  "qname": {"type": "choice", "instructions": "one-line task",
            "criteria": {"option": "operational description", ...}},  # wording drives quality!
  "qname": {"type": "score",  "instructions": "...",
            "criteria": ["level0", "level1", "level2"]},
  "qname": {"type": "noul",   "instructions": "whether ..."}
}
```

## Built-in presets (no questions to write)

`laya.router_questions()` model routing / `laya.guard_questions()` injection & jailbreak /
`laya.moderation_questions()` content safety / `laya.triage_questions()` ticket triage

## Discipline (empty over wrong)

1. **Confidence three-way branch**: conf >= 0.85 act automatically; 0.3-0.85 escalate to LLM
   or human; < 0.3 take the conservative default and log. Low confidence is a signal, not noise.
2. **Physical constraints belong to code, semantic judgment to Laya**: deterministic rules
   (allowlists, thresholds, exit codes) stay hardcoded; Laya only handles semantic forks rules cannot.
3. **Verified working**: text classification (news/email), failure-retry relative risk ordering,
   injection detection (1.0 confidence).
4. **Verified not working**: hard routing requiring domain rules (token limits),
   judgment needing personal context - keep those on code/LLM.
5. **Backtest before thresholds**: run 20 known-answer cases, inspect the confidence distribution,
   then set thresholds. Do not trust README ECE numbers.
6. English state gives the best quality; Chinese works but calibration is unverified.

## Agent integration patterns

- **HTTP server** (recommended, shared across agents/scripts):
  `LAYA_MODEL_PATH=... python scripts/laya_server.py` then
  `curl localhost:8600/ask -d '{state, questions}'`
- **cron/script pre-filter**: Laya screens the bulk; empty stdout means stay silent,
  only flagged items wake the LLM for wording
- **Tool gate**: judge risk(choice) + needs_approval(noul) before tool execution;
  deny / escalate / allow three-way branch
- **Router**: split requests between small/large models (built-in router_questions: difficulty + domain)
- **Jev-swappable**: same interface; to compare calibration later, point the server at
  api.typesafe.ai - callers change nothing

# References
- laya-server.md - server protocol and curl examples
- integration.md - in-process/HTTP patterns, confidence three-way branch, tool gate template
- scripts/laya_server.py - the runnable server script
