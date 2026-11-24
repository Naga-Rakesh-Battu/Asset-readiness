"""Train a failure-risk model on the training years and score it on the later, held-out years."""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss
from generate_data import FEATURES


def precision_at_k(y, p, k=0.10):
    n = max(1, int(len(y) * k)); idx = np.argsort(-p)[:n]
    return float(np.mean(y[idx]))


def evaluate(name, y, p):
    return {"model": name, "auc": round(float(roc_auc_score(y, p)), 3),
            "brier": round(float(brier_score_loss(y, p)), 4),
            "precision_top10pct": round(precision_at_k(y, p), 3)}


def train_and_score(train, test):
    Xtr, ytr, Xte, yte = train[FEATURES], train.failed.values, test[FEATURES], test.failed.values
    # Baseline: the usual rule of thumb, "older equipment is riskier" (age only)
    base = LogisticRegression(max_iter=1000).fit(train[["age"]], ytr)
    p_base = base.predict_proba(test[["age"]])[:, 1]
    gbm = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.08, random_state=0).fit(Xtr, ytr)
    p_gbm = gbm.predict_proba(Xte)[:, 1]
    res = [evaluate("age-only baseline", yte, p_base), evaluate("gradient boosting", yte, p_gbm)]
    imp = sorted(zip(FEATURES, gbm.feature_importances_.round(3).tolist()), key=lambda t: -t[1])
    return gbm, p_gbm, res, imp


if __name__ == "__main__":
    tr, te = pd.read_csv("train.csv"), pd.read_csv("test.csv")
    _, _, res, imp = train_and_score(tr, te)
    print(json.dumps({"results": res, "feature_importance": imp}, indent=2))
