# Databricks notebook source
# MAGIC %md
# MAGIC # Asset Readiness on Databricks
# MAGIC **The right part, in the right place, before it breaks.**
# MAGIC
# MAGIC This notebook runs the whole pipeline on Databricks: bronze, silver and gold Delta tables, an MLflow-tracked
# MAGIC failure-risk model tested on held-out years, and a Spark SQL check of where spare parts should go.
# MAGIC
# MAGIC * All data here is **synthetic**. We generate it in the first cell. No real utility data is used.
# MAGIC * To run: import this file into a Databricks workspace (Workspace, Import), attach a cluster or serverless compute, Run all.
# MAGIC * Written for Databricks and tested on local Spark. It has not yet been run in a Databricks workspace.

# COMMAND ----------

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F

try:
    spark  # provided by Databricks
except NameError:
    spark = SparkSession.builder.master("local[2]").appName("asset-readiness").config("spark.ui.enabled", "false").getOrCreate()
try:
    display  # provided by Databricks
except NameError:
    display = lambda df: df.show(truncate=False)

SCHEMA = "asset_readiness"
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
spark.sql(f"USE {SCHEMA}")
ON_DATABRICKS = "DATABRICKS_RUNTIME_VERSION" in os.environ
print("Running on Databricks" if ON_DATABRICKS else "Running on local Spark", "| schema:", SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Bronze: raw synthetic asset history
# MAGIC 900 assets over 8 years. Failures are drawn from a known formula plus noise, so results show the pipeline works,
# MAGIC not how real equipment behaves.

# COMMAND ----------

REGIONS = ["North", "South", "East"]
PARTS = {"dist_25kva": (0.45, 18), "dist_75kva": (0.30, 26), "substation_xfmr": (0.10, 128), "breaker_69kv": (0.15, 52)}
YEARS = list(range(2019, 2027))
FEATURES = ["age", "load_factor", "inspection_score", "oil_acidity", "past_failures", "storm_severity"]


def make_history(seed=7, n=900):
    rng = np.random.default_rng(seed)
    region = rng.choice(REGIONS, n, p=[0.30, 0.38, 0.32])
    part = rng.choice(list(PARTS), n, p=[v[0] for v in PARTS.values()])
    age_base = {"North": 18, "South": 38, "East": 27}
    age0 = np.clip(rng.normal([age_base[r] for r in region], 9), 2, 60)
    load0 = np.clip(rng.normal(0.62, 0.15, n), 0.2, 1.0)
    assets = pd.DataFrame({"asset_id": [f"A{i:04d}" for i in range(n)], "region": region, "part": part})
    rng = np.random.default_rng(seed + 1)
    storm_shape = {"North": (1.0, 7), "South": (2.0, 4), "East": (1.2, 6)}
    storm = {(r, y): float(np.clip(rng.beta(*storm_shape[r]), 0, 1)) for r in REGIONS for y in YEARS}
    past = np.zeros(n)
    rows = []
    for y in YEARS:
        age = age0 + (y - YEARS[0])
        load = np.clip(load0 + rng.normal(0, 0.04, n), 0.2, 1)
        cond = rng.normal(0, 1, n)
        insp = np.clip(78 - 0.35 * age + 6 * cond * -1 + rng.normal(0, 6, n), 20, 100)
        oil = np.clip(0.05 + 0.004 * age + 0.03 * cond + rng.normal(0, 0.02, n), 0, 0.6)
        sev = np.array([storm[(r, y)] for r in assets.region])
        z = -7.4 + 0.05 * age + 1.6 * load - 0.022 * (insp - 70) + 1.3 * oil + 0.55 * past + 2.4 * sev
        fail = (rng.random(n) < 1 / (1 + np.exp(-z))).astype(int)
        df = assets.copy()
        df["year"] = y
        df["age"] = age.round(1); df["load_factor"] = load.round(3)
        df["inspection_score"] = insp.round(1); df["oil_acidity"] = oil.round(3)
        df["past_failures"] = past.copy(); df["storm_severity"] = sev.round(3); df["failed"] = fail
        rows.append(df)
        past = past + fail
    return pd.concat(rows, ignore_index=True)


raw = make_history()
(spark.createDataFrame(raw).write.mode("overwrite").saveAsTable("bronze_asset_history"))
print("bronze rows:", spark.table("bronze_asset_history").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Silver: quality checks and clean tables
# MAGIC The checks run before any model sees the data. A failed check stops the notebook.

# COMMAND ----------

bronze = spark.table("bronze_asset_history")
silver = (bronze.dropDuplicates(["asset_id", "year"])
          .filter(F.col("age").isNotNull() & F.col("failed").isin(0, 1))
          .withColumn("failed", F.col("failed").cast("int")))
n_bronze, n_silver = bronze.count(), silver.count()
dupes = n_bronze - bronze.dropDuplicates(["asset_id", "year"]).count()
nulls = bronze.select([F.sum(F.col(c).isNull().cast("int")).alias(c) for c in FEATURES]).collect()[0].asDict()
assert dupes == 0, f"duplicate asset-years found: {dupes}"
assert sum(nulls.values()) == 0, f"missing values found: {nulls}"
assert n_silver == n_bronze, "rows dropped by cleaning"
silver.write.mode("overwrite").saveAsTable("silver_asset_year")
print(f"quality checks passed: {n_silver} rows, {dupes} duplicates, no missing values")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Gold: model-ready tables, split by time
# MAGIC Train on 2019 to 2024. Test on 2025 and 2026. The model never sees the test years.

# COMMAND ----------

TEST_FROM = 2025
silver = spark.table("silver_asset_year")
silver.filter(F.col("year") < TEST_FROM).write.mode("overwrite").saveAsTable("gold_train")
silver.filter(F.col("year") >= TEST_FROM).write.mode("overwrite").saveAsTable("gold_test")
print("train rows:", spark.table("gold_train").count(), "| test rows:", spark.table("gold_test").count())

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Train and track with MLflow
# MAGIC Two models: a plain age-only rule (the baseline to beat) and gradient boosting on six inputs.

# COMMAND ----------

import mlflow
import mlflow.sklearn
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

if not ON_DATABRICKS:
    os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"  # local testing only; Databricks tracks runs itself
    mlflow.set_tracking_uri("file:./mlruns")
    mlflow.set_experiment("asset_readiness")

train = spark.table("gold_train").toPandas()
test = spark.table("gold_test").toPandas()


def precision_top10(y, p):
    k = max(1, int(len(y) * 0.10))
    return float(np.mean(y[np.argsort(-p)[:k]]))


def metrics(y, p):
    return {"auc": round(float(roc_auc_score(y, p)), 3), "brier": round(float(brier_score_loss(y, p)), 4),
            "precision_top10pct": round(precision_top10(y, p), 3)}


with mlflow.start_run(run_name="age_only_baseline"):
    base = LogisticRegression(max_iter=1000).fit(train[["age"]], train.failed)
    m_base = metrics(test.failed.values, base.predict_proba(test[["age"]])[:, 1])
    mlflow.log_params({"model": "logistic regression", "features": "age"})
    mlflow.log_metrics(m_base)

with mlflow.start_run(run_name="gradient_boosting") as run:
    gbm = GradientBoostingClassifier(n_estimators=150, max_depth=3, learning_rate=0.08, random_state=0)
    gbm.fit(train[FEATURES], train.failed)
    p_test = gbm.predict_proba(test[FEATURES])[:, 1]
    m_gbm = metrics(test.failed.values, p_test)
    mlflow.log_params({"model": "gradient boosting", "n_estimators": 150, "max_depth": 3, "features": ",".join(FEATURES),
                       "train_years": "2019-2024", "test_years": "2025-2026"})
    mlflow.log_metrics(m_gbm)
    mlflow.sklearn.log_model(gbm, "failure_risk_model", serialization_format="cloudpickle")
    print("MLflow run id:", run.info.run_id)

print("baseline        ", m_base)
print("gradient boosting", m_gbm)
assert m_gbm["auc"] > m_base["auc"] > 0.5, "model must beat the plain baseline on held-out years"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Score every asset and save the risk table

# COMMAND ----------

scored = test[["asset_id", "region", "part", "year", "failed"]].copy()
scored["risk"] = p_test
spark.createDataFrame(scored).write.mode("overwrite").saveAsTable("gold_risk_scores")
display(spark.sql("""
    SELECT region, COUNT(*) AS asset_years, ROUND(AVG(risk), 4) AS avg_predicted_risk, ROUND(AVG(failed), 4) AS actual_failure_rate
    FROM gold_risk_scores GROUP BY region ORDER BY region"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Place the spares
# MAGIC Both policies get the same total spares per part type (5% of assets). They differ only in where the spares go:
# MAGIC by asset count, or by the model's expected failures.

# COMMAND ----------

def allocate(total, weights):
    w = np.array([weights[r] for r in REGIONS], float)
    w = w / w.sum() if w.sum() > 0 else np.ones(len(REGIONS)) / len(REGIONS)
    raw_ = w * total
    base_ = np.floor(raw_).astype(int)
    for i in np.argsort(-(raw_ - base_))[: int(total - base_.sum())]:
        base_[i] += 1
    return dict(zip(REGIONS, base_.tolist()))


agg = (spark.table("gold_risk_scores").groupBy("year", "part", "region")
       .agg(F.count("*").alias("assets"), F.sum("risk").alias("expected_failures"), F.sum("failed").alias("actual_failures"))
       .toPandas())
plan_rows = []
for (year, part), g in agg.groupby(["year", "part"]):
    g = g.set_index("region").reindex(REGIONS).fillna(0)
    total = max(1, round(g.assets.sum() * 0.05))
    by_count, by_risk = allocate(total, g.assets.to_dict()), allocate(total, g.expected_failures.to_dict())
    for r in REGIONS:
        plan_rows.append((int(year), part, r, int(g.assets[r]), float(g.expected_failures[r]), int(g.actual_failures[r]), by_count[r], by_risk[r]))
cols = ["year", "part", "region", "assets", "expected_failures", "actual_failures", "spares_by_count", "spares_by_risk"]
spark.createDataFrame(pd.DataFrame(plan_rows, columns=cols)).write.mode("overwrite").saveAsTable("gold_spares_plan")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Check the plan against what really happened
# MAGIC Fill rate is the share of real failures that had a spare in the same region.

# COMMAND ----------

fill = spark.sql("""
    SELECT policy,
           SUM(LEAST(spares, actual_failures))                                AS failures_with_local_spare,
           SUM(actual_failures)                                               AS failures,
           ROUND(SUM(LEAST(spares, actual_failures)) / SUM(actual_failures), 3) AS fill_rate,
           SUM(GREATEST(spares - actual_failures, 0))                         AS spares_unused
    FROM (
        SELECT 'spread by asset count' AS policy, spares_by_count AS spares, actual_failures FROM gold_spares_plan
        UNION ALL
        SELECT 'placed by model risk', spares_by_risk, actual_failures FROM gold_spares_plan
    ) GROUP BY policy ORDER BY policy""")
display(fill)
res = {r["policy"]: r["fill_rate"] for r in fill.collect()}
print(res)
assert res["placed by model risk"] >= res["spread by asset count"], "risk-based placement should not do worse here"

# COMMAND ----------

# MAGIC %md
# MAGIC ## What this does not show
# MAGIC * The data is synthetic and we wrote the formula, so these numbers prove the pipeline works, not real-world value.
# MAGIC * The test years hold only a few dozen failures, so percentages are rough.
# MAGIC * Next on Databricks: register the model in Unity Catalog, schedule this notebook as a Job, and point it at a client's real tables.
