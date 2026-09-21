"""
WorkClaw × Laya 集成最小骨架 —— 供你明天在公司电脑上参考改写
两个接入点：
  A. Tool Gate  ：WorkClaw 的工具调用执行前，Laya 判风险
  B. Router     ：WorkClaw 收到请求后，Laya 判该用哪个模型
用法：pip install laya 后，把 LAYA_GATE 段拷进你的代码即可。
"""
import warnings; warnings.filterwarnings('ignore')
import laya

# ---------- 初始化（进程级单例，全局加载一次）----------
_agent = None

def get_laya():
    global _agent
    if _agent is None:
        # 公司电脑若无 GPU: device="cpu"；有 NVIDIA 卡: 不传参自动 cuda
        _agent = laya.load("convaiinnovations/laya", device="cpu")
    return _agent

# ---------- A. Tool Gate：工具调用前置风险判断 ----------
TOOL_GATE_QUESTIONS = {
    "risk": {
        "type": "choice",
        "instructions": "Assess the risk of executing this tool call in a work environment.",
        "criteria": {
            "low": "read-only operations: search, fetch, list, get",
            "medium": "reversible writes: create draft, append note, save file to workspace",
            "high": "irreversible or external effects: send message, delete, publish, modify shared resources"
        }
    },
    "needs_approval": {
        "type": "noul",
        "instructions": "Should a human approve this call before execution?"
    }
}

def tool_gate(tool_name: str, args: dict, threshold: float = 0.85):
    """在 WorkClaw 执行任何工具前调用。返回 (allow, reason)"""
    result = get_laya().predict(
        {"tool": tool_name, "args": args},
        TOOL_GATE_QUESTIONS
    )["answers"]
    risk = result["risk"]
    needs_approval = result["needs_approval"]["noul"]
    # 三分支：高置信低风险→放行；需审批→人工；其余→放行但记录
    if needs_approval >= threshold:
        return False, f"escalate: needs_approval={needs_approval:.2f}"
    if risk["choice"] == "high" and risk["confidence"] >= 0.7:
        return False, f"deny: high risk (conf={risk['confidence']:.2f})"
    return True, f"allow: {risk['choice']} (conf={risk['confidence']:.2f})"

# ---------- B. Router：请求分流大/小模型 ----------
ROUTER_QUESTIONS = laya.router_questions()  # 内置: difficulty(0-3) + domain

def route_model(user_request: str, fast="glm-4.5-flash", powerful="glm-5.2") -> str:
    result = get_laya().predict({"request": user_request}, ROUTER_QUESTIONS)["answers"]
    difficulty = result["difficulty"]
    if difficulty["score"] >= 2.0:          # moderate 以上走强模型
        return powerful, f"difficulty={difficulty['score']:.2f}"
    if difficulty["confidence"] < 0.3:      # 判断不确定→保守走强模型
        return powerful, f"uncertain (conf={difficulty['confidence']:.2f}), default powerful"
    return fast, f"difficulty={difficulty['score']:.2f} (conf={difficulty['confidence']:.2f})"

# ---------- 演示 ----------
if __name__ == "__main__":
    print("A. Tool Gate 测试:")
    for tool, args in [
        ("search_web", {"query": "GLM-5.2 pricing"}),
        ("send_email", {"to": "team@acme.com", "body": "deploy done"}),
        ("delete_file", {"path": "/shared/config.yaml"}),
    ]:
        allow, why = tool_gate(tool, args)
        print(f"  {tool:12s} → {'ALLOW' if allow else 'BLOCK'} | {why}")

    print("\nB. Router 测试:")
    for req in ["Fix this typo in the README", "Design a rate limiter for our API gateway"]:
        model, why = route_model(req)
        print(f"  「{req[:40]}」 → {model} | {why}")
