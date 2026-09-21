import warnings; warnings.filterwarnings('ignore')
import laya, time, json

agent = laya.load("convaiinnovations/laya", device="cpu")

state = {
    "from": "user@acme.com",
    "subject": "Duplicate charge on invoice #4411",
    "body": "Hi, we were billed twice for March. Please refund the duplicate today or we will cancel our plan."
}
questions = {
    "department": {"type": "choice", "instructions": "Which department should handle this email?",
        "criteria": {"billing": "invoices, payments, refunds", "technical": "bugs, outages, system errors",
                     "sales": "pricing, new contracts", "other": "everything else"}},
    "urgency": {"type": "score", "instructions": "How urgent is this request?",
        "criteria": ["not urgent", "soon", "critical deadline or blocking issue"]},
    "churn_risk": {"type": "noul", "instructions": "Does the user threaten to cancel or leave?"},
    "is_phishing": {"type": "noul", "instructions": "Is this email a phishing or scam attempt?"}
}
t0 = time.time()
result = agent.predict(state, questions)
print(f"first run: {(time.time()-t0)*1000:.0f}ms")
times = []
for _ in range(3):
    t0 = time.time()
    result = agent.predict(state, questions)
    times.append((time.time()-t0)*1000)
print(f"steady state: {min(times):.0f}ms per call (CPU, x86_64 Mac)")
print(json.dumps(result["answers"], indent=1))
