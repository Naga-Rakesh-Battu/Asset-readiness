"""Turn risk scores into a stocking plan, then test it against what really happened.

Both policies get the SAME total number of spare parts per part type. They differ only in where
the spares go. Fill rate = share of real failures a region could repair from its own shelf.
"""
import numpy as np
import pandas as pd
from generate_data import REGIONS, PARTS


def allocate(total, weights):
    """Split `total` whole parts across regions in proportion to weights (largest remainder)."""
    w = np.array([weights[r] for r in REGIONS], float)
    w = w / w.sum() if w.sum() > 0 else np.ones(len(REGIONS)) / len(REGIONS)
    raw = w * total; base = np.floor(raw).astype(int)
    for i in np.argsort(-(raw - base))[: int(total - base.sum())]:
        base[i] += 1
    return dict(zip(REGIONS, base.tolist()))


def spares_per_part(assets_per_part, rate=0.05):
    return {p: max(1, round(n * rate)) for p, n in assets_per_part.items()}


def simulate(test, p_risk, spare_rate=0.05):
    """For each test year: place spares by (a) asset count, (b) predicted risk, then count local fills."""
    df = test.copy(); df["risk"] = p_risk
    out = {"asset_count policy": [0, 0], "model-risk policy": [0, 0]}  # [failures covered locally, failures total]
    idle = {"asset_count policy": 0, "model-risk policy": 0}
    for y, g in df.groupby("year"):
        for part in PARTS:
            gp = g[g.part == part]
            total = spares_per_part({part: len(gp)}, spare_rate)[part]
            count_w = gp.groupby("region").size().reindex(REGIONS, fill_value=0).to_dict()
            risk_w = gp.groupby("region").risk.sum().reindex(REGIONS, fill_value=0).to_dict()
            fails = gp.groupby("region").failed.sum().reindex(REGIONS, fill_value=0).to_dict()
            for name, w in (("asset_count policy", count_w), ("model-risk policy", risk_w)):
                stock = allocate(total, w)
                for r in REGIONS:
                    out[name][0] += min(stock[r], fails[r]); out[name][1] += fails[r]
                    idle[name] += max(0, stock[r] - fails[r])
    return {k: {"fill_rate": round(v[0] / v[1], 3), "failures": int(v[1]), "idle_spares": idle[k]} for k, v in out.items()}
