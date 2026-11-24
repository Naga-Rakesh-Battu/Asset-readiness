"""Generate SYNTHETIC grid-asset data. No real utility data is used anywhere.

Each row is one asset in one year. The label is whether it failed that year.
The failure probability comes from a known formula plus noise, so every result
in this repo shows the PIPELINE works. It does not show how real equipment behaves.
"""
import numpy as np
import pandas as pd

REGIONS = ["North", "South", "East"]
PARTS = {  # part type -> (share of assets, lead time in weeks)
    "dist_25kva": (0.45, 18),
    "dist_75kva": (0.30, 26),
    "substation_xfmr": (0.10, 128),
    "breaker_69kv": (0.15, 52),
}
YEARS = list(range(2019, 2027))  # 2019-2024 train, 2025-2026 test (later years, never seen)
FEATURES = ["age", "load_factor", "inspection_score", "oil_acidity", "past_failures", "storm_severity"]


def make_assets(n=900, seed=7):
    rng = np.random.default_rng(seed)
    region = rng.choice(REGIONS, n, p=[0.30, 0.38, 0.32])
    part = rng.choice(list(PARTS), n, p=[v[0] for v in PARTS.values()])
    # South is older on average, North newer: regions differ, so stock placement matters
    age_base = {"North": 18, "South": 38, "East": 27}
    age = np.clip(rng.normal([age_base[r] for r in region], 9), 2, 60)
    load = np.clip(rng.normal(0.62, 0.15, n), 0.2, 1.0)
    return pd.DataFrame({"asset_id": [f"A{i:04d}" for i in range(n)], "region": region,
                         "part": part, "install_age": age, "load_base": load})


def failure_prob(age, load, insp, oil, past, storm):
    z = (-7.4 + 0.05 * age + 1.6 * load - 0.022 * (insp - 70)
         + 1.3 * oil + 0.55 * past + 2.4 * storm)
    return 1 / (1 + np.exp(-z))


def make_history(seed=7):
    rng = np.random.default_rng(seed + 1)
    assets = make_assets(seed=seed)
    storm_shape = {"North": (1.0, 7), "South": (2.0, 4), "East": (1.2, 6)}  # South is more storm-prone (made up)
    storm = {(r, y): float(np.clip(rng.beta(*storm_shape[r]), 0, 1)) for r in REGIONS for y in YEARS}
    past = np.zeros(len(assets))
    rows = []
    for y in YEARS:
        age = assets.install_age.values + (y - YEARS[0])
        load = np.clip(assets.load_base.values + rng.normal(0, 0.04, len(assets)), 0.2, 1)
        # Inspection and oil readings are noisy views of hidden condition that also drives failures
        cond = rng.normal(0, 1, len(assets))
        insp = np.clip(78 - 0.35 * age + 6 * cond * -1 + rng.normal(0, 6, len(assets)), 20, 100)
        oil = np.clip(0.05 + 0.004 * age + 0.03 * cond + rng.normal(0, 0.02, len(assets)), 0, 0.6)
        sev = np.array([storm[(r, y)] for r in assets.region])
        p = failure_prob(age, load, insp, oil, past, sev)
        fail = (rng.random(len(assets)) < p).astype(int)
        df = assets[["asset_id", "region", "part"]].copy()
        df["year"] = y
        df["age"] = age.round(1); df["load_factor"] = load.round(3)
        df["inspection_score"] = insp.round(1); df["oil_acidity"] = oil.round(3)
        df["past_failures"] = past.copy(); df["storm_severity"] = sev.round(3)
        df["failed"] = fail
        rows.append(df)
        past = past + fail  # failures accumulate as history
    return pd.concat(rows, ignore_index=True)


def split(df, test_from=2025):
    return df[df.year < test_from].reset_index(drop=True), df[df.year >= test_from].reset_index(drop=True)


if __name__ == "__main__":
    import os
    d = make_history()
    tr, te = split(d)
    tr.to_csv("train.csv", index=False); te.to_csv("test.csv", index=False)
    print(f"train {len(tr)} rows ({tr.failed.mean():.1%} failed), test {len(te)} rows ({te.failed.mean():.1%} failed)")
