"""One command: generate data, train, evaluate on held-out years, test the stocking plan, save results."""
import json, os
from generate_data import make_history, split
from train import train_and_score
from plan import simulate

if __name__ == "__main__":
    pass
    tr, te = split(make_history())
    tr.to_csv("train.csv", index=False); te.to_csv("test.csv", index=False)
    _, p, models, imp = train_and_score(tr, te)
    plan = simulate(te, p)
    out = {"data": {"train_rows": len(tr), "test_rows": len(te), "train_years": "2019-2024", "test_years": "2025-2026",
                    "test_failure_rate": round(float(te.failed.mean()), 3), "synthetic": True},
           "risk_model": models, "feature_importance": imp, "stocking_plan": plan}
    json.dump(out, open("metrics.json", "w"), indent=2)
    print(json.dumps(out, indent=2))
