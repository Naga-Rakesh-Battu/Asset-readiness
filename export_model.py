"""Export the trained gradient-boosting model and the 2026 assets so the website can score them in the browser."""
import json, numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from generate_data import FEATURES
from train import train_and_score

tr, te = pd.read_csv("train.csv"), pd.read_csv("test.csv")
gbm, p, _, _ = train_and_score(tr, te)
init = float(gbm.init_.class_prior_[1]); init = float(np.log(init / (1 - init)))
trees = []
for est in gbm.estimators_[:, 0]:
    t = est.tree_
    trees.append({"f": t.feature.tolist(), "t": [float(x) for x in t.threshold], "l": t.children_left.tolist(),
                  "r": t.children_right.tolist(), "v": [round(float(x[0][0]), 6) for x in t.value]})
model = {"features": FEATURES, "init": init, "lr": gbm.learning_rate, "trees": trees}
y26 = te[te.year == 2026].reset_index(drop=True)
cols = ["asset_id", "region", "part"] + FEATURES + ["failed"]
assets = {"cols": cols, "rows": y26[cols].values.tolist()}
open("data.js", "w").write("window.AR_MODEL=" + json.dumps(model, separators=(",", ":")) + ";\nwindow.AR_ASSETS=" + json.dumps(assets, separators=(",", ":")) + ";\n")
np.save("/tmp/p_test.npy", p)
print(len(trees), "trees", len(y26), "assets in 2026")
