# 任意 Agent 代码集成模式

## 模式一：进程内（单脚本，最简单）

```python
import warnings; warnings.filterwarnings('ignore')
import laya

agent = laya.load("/path/to/laya_model_slim", device="cpu")  # 进程级单例，只 load 一次

result = agent.predict(state, questions)["answers"]
```

适合：单个 cron 脚本、一次性批处理。

## 模式二：HTTP 服务（多 agent/多脚本共用，推荐）

启动见 laya-server.md。任何语言 curl 即用，判断器可插拔（Laya↔Jev 零改动切换）。

适合：多个脚本/agent 共用同一判断层；不想每个进程都加载 30-60s 权重。

## 通用决策模式：置信度三分支

```python
r = answers["q名"]
if r["confidence"] >= 0.85:
    do_auto(r)          # 高置信：自动执行
elif r["confidence"] >= 0.3:
    do_llm_fallback(r)  # 中间带：升级 LLM 或人工
else:
    do_conservative(r)  # 低置信：默认保守动作+记录日志
```

阈值 0.85/0.3 是起点，**新场景先拿 20 个已知答案的 case 回测 conf 分布再定**。

## Tool Gate 模板（任意 agent 工具执行前）

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
