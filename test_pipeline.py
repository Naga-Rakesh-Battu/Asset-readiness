import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from generate_data import make_history, split, FEATURES, REGIONS
from train import train_and_score
from plan import allocate, simulate

def test_split_is_by_time_no_leak():
    tr, te = split(make_history())
    assert tr.year.max() < te.year.min()
    assert set(tr.asset_id) == set(te.asset_id)  # same assets, later years

def test_no_missing_values():
    assert not make_history().isna().any().any()

def test_allocate_conserves_parts():
    for total in (1, 5, 17):
        a = allocate(total, {"North": 3.2, "South": 0.4, "East": 1.1})
        assert sum(a.values()) == total and all(v >= 0 for v in a.values())

def test_allocate_all_zero_weights_still_places_parts():
    assert sum(allocate(4, {r: 0 for r in REGIONS}).values()) == 4

def test_model_beats_age_only_baseline_on_heldout():
    tr, te = split(make_history())
    _, _, res, _ = train_and_score(tr, te)
    assert res[1]["auc"] > res[0]["auc"] > 0.5

def test_plan_counts_are_consistent():
    tr, te = split(make_history())
    _, p, _, _ = train_and_score(tr, te)
    s = simulate(te, p)
    a, b = s["asset_count policy"], s["model-risk policy"]
    assert a["failures"] == b["failures"] == int(te.failed.sum())
    assert 0 <= a["fill_rate"] <= 1 and 0 <= b["fill_rate"] <= 1
