---
name: laya-system-one
description: Use for fast local judgment without LLM calls.
category: devops
---

# Laya：本地 System 1 判断引擎

Jev 的开源复刻（Apache 2.0，ModernBERT 底座）。非自回归、单次前向传播，返回类型化概率+校准置信度。**替代场景**：凡是在 agent 里想问「这个该不该/是哪类/多严重」但不想烧一次 LLM 调用时。

## 环境约定（假定已就绪）

- venv: `/tmp/laya_venv`（python3.11，公司电脑按 setup_env.sh 重建）
- 权重: `laya_model_slim/` 目录（742MB slim 包，已含主模型+tokenizer）
- 可选服务: `python laya_server.py` 后 curl `localhost:8600/ask`
- 必须三元组：python≤3.11 / `device="cpu"`（Mac x86）/ transformers==4.48.0

## 接口（就一个）

```python
import laya
agent = laya.load("<权重目录>", device="cpu")   # 进程内单例，首次 30-60s
result = agent.predict(state, questions)          # state: str|dict, questions: dict
# result["answers"]["qname"] → {choice|score|noul, probabilities, confidence}
```

## 三原语（与 Jev 同名，可互换）

| 原语 | 问什么 | 返回 |
|---|---|---|
| `choice` | 多选一分流 | 每选项概率 + confidence |
| `score` | 有序刻度打分 | 连续分 + 分布 + confidence |
| `noul` | 是/否 | P(true) + confidence |

questions 格式：
```python
{
  "q名": {"type": "choice", "instructions": "一句话任务",
          "criteria": {"选项": "操作性描述", ...}},       # criteria 措辞决定判断质量！
  "q名": {"type": "score",  "instructions": "...",
          "criteria": ["level0", "level1", "level2"]},
  "q名": {"type": "noul",   "instructions": "是否…"}
}
```

## 内置 presets（免写 questions）

`laya.router_questions()` 模型路由 / `laya.guard_questions()` 注入越狱检测 / `laya.moderation_questions()` 内容安全 / `laya.triage_questions()` 工单分诊

## 使用纪律（宁空勿错）

1. **置信度三分支**：conf≥0.85 自动执行；0.3-0.85 升级 LLM 或人工；<0.3 默认保守动作并记录。低 conf 是信号不是噪音。
2. **物理约束归代码，语义判断归 Laya**：确定性规则（白名单/阈值/exit code）永远写死在代码里，Laya 只管规则管不了的语义分叉。
3. **已验证可用**：文本分类（新闻/邮件）、失败重试相对风险排序、注入检测（1.0 conf）。
4. **已验证不可用**：需要领域规则的硬路由（token 上限类）、需要个人语境的行为判定——这些继续代码/LLM。
5. **新场景先回测**：拿 20 个已知答案的 case 跑 conf 分布，再定阈值；不信 README 的 ECE。
6. 英文 state 判断质量最好；中文可跑但未验证校准度。

## Agent 接入姿势

- **HTTP 服务**（推荐，多 agent/多脚本共用）：`LAYA_MODEL_PATH=... python laya_server.py` → `curl localhost:8600/ask -d '{state, questions}'`
- **cron/script 前置**：Laya 筛大多数，stdout 空=不打扰，有事才唤醒 LLM 生成文案
- **Tool Gate**：工具执行前判 risk(choice)+needs_approval(noul)，deny/escalate/allow 三分支
- **Router**：请求分流大小模型（内置 router_questions：difficulty+domain）
- **Jev 可互换**：接口同构，哪天要对比校准度，把 server 换成转发 api.typesafe.ai，调用方零改动

# References
- laya-server.md — HTTP 服务完整协议与 curl 示例
- integration.md — 任意 agent 代码集成模式（进程内/HTTP/置信度三分支）
