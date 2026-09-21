"""Laya 交互式测试器——跑一批贴近你真实场景的判断，看它的效果"""
import warnings; warnings.filterwarnings('ignore')
import laya, json, time

agent = laya.load("convaiinnovations/laya", device="cpu")

print("=" * 60)
print("测试 1: 晨报新闻分类（choice + score）")
print("=" * 60)
news = [
    {"title": "Google releases AX v0.3, moves agent state out of etcd", "topic_hint": "infra"},
    {"title": "明星官宣离婚，热搜第一", "topic_hint": "娱乐"},
]
q_news = {
    "category": {"type": "choice", "instructions": "Categorize this news for a tech reader",
        "criteria": {
            "tech_ai": "AI, agents, infra, programming",
            "business": "funding, market, companies",
            "humanities": "history, philosophy, psychology",
            "fun": "nature, physics, curiosities",
            "skip": "celebrity gossip, spam, irrelevant"
        }},
    "value": {"type": "score", "instructions": "How valuable is this for a backend engineer learning AI agents?",
        "criteria": ["worthless", "mildly interesting", "must read"]}
}
for n in news:
    r = agent.predict(n, q_news)["answers"]
    print(f"\n  「{n['title'][:50]}」")
    print(f"  → 分类: {r['category']['choice']} (conf {r['category']['confidence']}) | 价值分: {r['value']['score']}/2")

print()
print("=" * 60)
print("测试 2: safe_commit 门控（noul 判断重试还是上报）")
print("=" * 60)
failures = [
    {"script": "git push", "exit_code": 7, "stderr": "remote rejected - fetch first, non-fast-forward"},
    {"script": "git push", "exit_code": 128, "stderr": "fatal: could not read Username for 'https://github.com'"},
    {"script": "python3 lint_check.py", "exit_code": 1, "stderr": "AssertionError: topics keys missing in 3 files"},
]
q_gate = {
    "safe_to_retry": {"type": "noul", "instructions": "Is this failure safe to automatically retry without human review?"},
    "needs_human": {"type": "noul", "instructions": "Does this failure need a human to look at it before any retry?"}
}
for f in failures:
    r = agent.predict(f, q_gate)["answers"]
    print(f"\n  exit={f['exit_code']} | {f['stderr'][:45]}")
    print(f"  → 可自动重试: {r['safe_to_retry']['noul']:.2f} | 需人工: {r['needs_human']['noul']:.2f}")

print()
print("=" * 60)
print("测试 3: API 聚合上游路由（你公司的同构问题）")
print("=" * 60)
requests = [
    {"endpoint": "/v1/chat/completions", "payload_tokens": 45000, "sla": "realtime", "upstream_health": {"glm-5.2": "healthy", "glm-4.5-flash": "healthy"}},
    {"endpoint": "/v1/embeddings", "payload_tokens": 800, "sla": "batch", "upstream_health": {"glm-5.2": "degraded_429", "glm-4.5-flash": "healthy"}},
]
q_route = {
    "route_to": {"type": "choice", "instructions": "Which upstream should serve this request?",
        "criteria": {
            "glm-5.2": "flagship model, costly, for complex tasks",
            "glm-4.5-flash": "cheap fast model, for simple or batch tasks",
            "queue_offpeak": "defer to off-peak batch window"
        }},
}
for req in requests:
    r = agent.predict(req, q_route)["answers"]
    print(f"\n  {req['endpoint']} | {req['payload_tokens']}tok | SLA={req['sla']} | 上游5.2={req['upstream_health']['glm-5.2']}")
    print(f"  → 路由到: {r['route_to']['choice']} (conf {r['route_to']['confidence']})")

print()
print("=" * 60)
print("测试 4: 行为哨红黄判定")
print("=" * 60)
situations = [
    {"day": "Tuesday", "entertainment_minutes": 150, "week_avg": 60, "study_minutes": 0, "note": "workday evening, no study done"},
    {"day": "Saturday", "entertainment_minutes": 150, "week_avg": 60, "study_minutes": 90, "note": "weekend, study done first"},
]
q_guard = {
    "level": {"type": "score", "instructions": "Should the behavior sentinel intervene?",
        "criteria": ["green: normal, stay silent", "yellow: gentle nudge", "red: firm intervention"]},
}
for s in situations:
    r = agent.predict(s, q_guard)["answers"]
    print(f"\n  {s['day']} | 娱乐 {s['entertainment_minutes']}min (周均{s['week_avg']}) | 学习 {s['study_minutes']}min")
    print(f"  → 哨兵级别: {r['level']['score']}/2 = {['green','yellow','red'][round(r['level']['score'])]} (conf {r['level']['confidence']})")

print("\n done.")
