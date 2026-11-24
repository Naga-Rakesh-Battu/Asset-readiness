# Asset Readiness

**The right part, in the right place, before it breaks.**

A concept project by Charithasri Ande and Naga Rakesh Battu, built for a conversation with Perficient. Live demo: https://naga-rakesh-battu.github.io/Asset-readiness/

## The problem

Big grid parts can take over two years to arrive, so utilities must predict years ahead which parts they will need and where to keep them. Guess wrong and customers wait, or millions of dollars sit idle on a shelf.

- Large power transformers averaged about 128 weeks of lead time in Wood Mackenzie's Q2 2025 survey.
- S&P Global projects about $1.295 trillion of U.S. utility capital spending for 2026 to 2030.
- Utilities report transformers cost four to six times what they did before 2022.

Sources are listed in the demo's Problem tab. We read them in secondary articles, not the original reports.

## What is in this folder

| Path | What it does |
|---|---|
| `generate_data.py` | Makes **synthetic** asset data: 900 assets, 8 years, failures drawn from a known formula plus noise |
| `train.py` | Trains a failure-risk model on 2019 to 2024, scores it on 2025 to 2026 against an age-only baseline |
| `plan.py` | Places the same number of spares two ways (by asset count, by predicted risk) and replays the held-out years |
| `run_all.py` | Runs everything and writes `metrics.json` |
| `train.csv`, `test.csv` | The generated train and test sets |
| `test_pipeline.py` | 6 tests: no time leak between train and test, no missing values, parts conserved, model beats baseline, counts consistent |
| `export_model.py` | Saves the trained model and the 2026 assets to `data.js` so the website can run the model in the browser |
| `build_site.py` | Writes the five website pages |
| `make_charts.py`, `charts.json`, `chart_facts.json` | Draw the four charts on the Evidence page from the held-out results |
| `make_diagram_detailed.py`, `architecture_detailed.svg`, `architecture.jpg` | The detailed architecture diagram and our hand-drawn sketch |
| `index.html`, `architecture.html`, `live.html`, `evidence.html`, `impact.html`, `site.css`, `site.js`, `data.js` | The website. The Live model page scores 900 assets with the trained model in the browser |

## Run it

```
pip install -r requirements.txt
python run_all.py
python export_model.py
python build_site.py
python -m pytest
```

## Results (held-out years, synthetic data)

| Model | AUC | Brier error | Precision, riskiest 10% |
|---|---|---|---|
| Age-only rule | 0.761 | 0.0418 | 17.2% |
| Gradient boosting | 0.796 | 0.0409 | 18.3% |

| Stocking policy (same total spares) | Failures with a local spare | Spares left unused |
|---|---|---|
| Spread by asset count | 70.2% of 84 | 31 |
| Placed by predicted risk | 83.3% of 84 | 20 |

## What these numbers do and do not show

- They show the pipeline works end to end: data, time-based split, model, baseline, plan, replay, tests.
- They do **not** show real-world value. We wrote the data generator, and we made the regions differ in age and storm exposure, so a risk-based policy is bound to help here.
- The test years hold only 84 failures, so the percentages are rough.
- This is one run of one made-up world. The next step is a pilot on a client's real records.

## Proposed design (not built)

Sources (asset registry, inspections, work orders, inventory, supplier lead times) feed a governed lakehouse on Databricks, then a risk model, a parts-demand forecast and a stock optimizer, then a planner dashboard and a technician assistant, with an evaluation and audit layer around all of it. The Databricks pieces (Delta tables, Unity Catalog, MLflow) are described as we understand them and would need a Databricks engineer's review.

## What it could mean for Perficient

Our reasoning from public information, not facts about Perficient:

1. **Repeatable.** The same core fits energy and utilities, manufacturing and distribution.
2. **Databricks pull-through.** The data and models live and are governed on the platform.
3. **Recurring work.** Models need monitoring and retraining, which turns a project into a service.
4. **Proof, not a pilot.** Every recommendation is tested against what really happened.

Value per year is roughly projects held up by parts, times weeks saved per project, times the cost of one week of delay. We cannot give a real number without client data.

## Honest limits

- All data here is synthetic. No real utility, including any named in conversation, is represented.
- Similar commercial tools exist. We have not compared against them.
- The Live model page runs the trained model in the browser. Its scores match the Python scores to about 7 decimal places. The technician assistant on that page is a small keyword demo on made-up manuals.

## Publishing on GitHub Pages

1. Put all files at the top level of the repo (no folders).
2. Settings, then Pages, then source `main` and the root folder.
3. The site is at `https://<account>.github.io/<repo>/`.
4. Check the footer: it shows the site version. If it is not the latest, hard refresh with Ctrl+Shift+R.
