"""Write the five pages of the Asset Readiness website from shared pieces."""
import json
M = json.load(open("metrics.json"))
rm = {r["model"]: r for r in M["risk_model"]}
base, gb = rm["age-only baseline"], rm["gradient boosting"]
sp = M["stocking_plan"]; sc, sr = sp["asset_count policy"], sp["model-risk policy"]
REPO = "https://github.com/Naga-Rakesh-Battu/Asset-readiness"
PAGES = [("index.html", "Problem"), ("architecture.html", "Architecture"), ("live.html", "Live model"), ("databricks.html", "Databricks"), ("evidence.html", "Evidence"), ("impact.html", "Impact")]

def page(fname, title, body, scripts=""):
    nav = "".join(f'<a href="{f}"{" aria-current=\"page\"" if f == fname else ""}>{n}</a>' for f, n in PAGES)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Asset Readiness</title>
<meta name="description" content="Asset Readiness: a concept project that predicts which grid equipment will fail and where to keep spare parts. Synthetic data, tested code.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 32 32%27%3E%3Crect width=%2732%27 height=%2732%27 rx=%277%27 fill=%27%230d5f7c%27/%3E%3Cpath d=%27M8 22 L16 8 L24 22 M11 17 H21%27 stroke=%27white%27 stroke-width=%273%27 fill=%27none%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27/%3E%3C/svg%3E">
<meta property="og:title" content="Asset Readiness">
<meta property="og:description" content="The right part, in the right place, before it breaks. A concept project on synthetic data.">
<link rel="stylesheet" href="site.css?v=202611241522">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar">
  <a class="brand" href="index.html"><b>Asset Readiness</b><span class="tag">Concept project · synthetic data</span></a>
  <nav aria-label="Pages">{nav}</nav>
</div></header>
<main class="wrap" id="main">
{body}
</main>
<footer><div class="wrap">Concept project by Charithasri Ande and Naga Rakesh Battu. All utility data, manuals, model results and storm results are synthetic. Market figures are cited on the Problem page. <a href="{REPO}" target="_blank" rel="noopener">Code on GitHub</a>. Site version 2026-11-24 15:22 CT.</div></footer>
{scripts}
<script src="site.js?v=202611241522"></script>
</body>
</html>
'''

index = '''
<div class="statement">
  <p class="eyebrow">The right part, in the right place, before it breaks</p>
  <p class="big">Big grid parts can take over two years to arrive, so utilities must predict years ahead which parts they will need and where to keep them. Guess wrong and customers wait, or millions of dollars sit idle on a shelf.</p>
</div>
<div class="grid g3">
  <div class="card stat"><b>128 wks</b><span>Average lead time for a large power transformer, nearly two and a half years.</span><small>Wood Mackenzie, Q2 2025, as reported by Foley</small></div>
  <div class="card stat"><b>$1.295T</b><span>Projected U.S. utility capital spending, 2026 to 2030. Every project that waits for a part is held up.</span><small>S&amp;P Global Regulatory Research, as reported by Foley</small></div>
  <div class="card stat"><b>4 to 6×</b><span>What utilities say transformers cost compared with before 2022.</span><small>Renewable Energy World</small></div>
</div>
<div class="grid g2" style="margin-top:16px">
  <div class="card"><h3>A storm, in three steps</h3><ol class="steps">
    <li><p>A storm damages a substation. The utility needs a transformer now.</p></li>
    <li><p>The nearest warehouse has the wrong size. The right one sits in a warehouse far away that nobody checked.</p></li>
    <li><p>A new unit takes over two years to order, so the repair waits, or a project slips.</p></li></ol></div>
  <div class="card"><h3>Why this is hard</h3><ol class="steps">
    <li><p>Failure prediction and stock planning usually live in different teams and different systems.</p></li>
    <li><p>Hold too many parts and cash is tied up. Hold too few and outages last longer.</p></li>
    <li><p>The facts that decide it are scattered: asset records, inspections, work orders, inventory, supplier lead times.</p></li></ol>
    <p class="src" style="margin-top:12px">These three reasons are our own analysis, not from the sources below.</p></div>
</div>
<div class="note"><b>Billion-dollar problem, unproven product.</b> The problem is large and documented. Whether this solution wins depends on results with real client data, and similar tools already exist.</div>
<div class="cta"><a class="btn" href="live.html">Try the live model</a><a class="btn ghost" href="architecture.html">See the architecture</a></div>
<div class="src">Sources (we read them in secondary articles, not the original reports):
  <ul>
    <li><a href="https://www.foley.com/?p=125261" target="_blank" rel="noopener">Foley &amp; Lardner, utility equipment and capital spending (cites Wood Mackenzie and S&amp;P Global)</a></li>
    <li><a href="https://www.renewableenergyworld.com/?p=80798132761" target="_blank" rel="noopener">Renewable Energy World, supply-chain delays and equipment prices</a></li>
    <li><a href="https://www.utilitydive.com/news/electric-transformer-shortage-nrel-niac/738947/" target="_blank" rel="noopener">Utility Dive, replacement needs exceed utility inventories</a></li>
  </ul></div>
'''

arch = '''
<p class="eyebrow">Proposed design</p>
<h2>Five steps from client data to approved spares</h2>
<p class="lede">Our sketch of how it fits together. Data flows from top to bottom: client data, a Databricks lakehouse, predicting failures, placing the spares, and a planner approving. The dashed arrow on the left means what failed feeds the next model. The notes on the right show where we think Perficient comes in, which is our proposal for Perficient to correct.</p>
<figure class="card fig" style="max-width:640px;margin:0 auto"><img src="architecture.jpg?v=202611241522" alt="Hand-drawn architecture. Client data flows down to a Databricks Lakehouse, then predict failures, place the spares, and planner approves. A dashed arrow labeled what failed feeds the next model returns to predict failures. Perficient links the client system to the lakehouse and handles build, test, tune, integrate, run and improve." style="width:100%;height:auto;border-radius:8px;display:block"></figure>
<h3 class="sec">The detailed version</h3>
<p class="lede" style="margin-bottom:12px">The same flow with every piece spelled out. Blue is a prototype on synthetic data, orange is proposed and not built, and white is the client's own data.</p>
<div class="tblwrap" style="background:var(--paper)"><div style="min-width:860px">__SVG__</div></div>
<p class="src"><a href="architecture_detailed.svg" target="_blank" rel="noopener">Open the detailed diagram on its own</a></p>
<h3 class="sec">Tap a block for more detail</h3>
<div class="layers" id="layers"></div>
<div class="legend"><span class="st-sim">● Prototype on synthetic data</span><span class="st-prop">● Proposed, not built</span></div>
<div class="card detail" id="detail" aria-live="polite"></div>
'''

live = '''
<p class="eyebrow">Live · the trained model runs in your browser · synthetic data</p>
<h2>Storm planner</h2>
<p class="lede">This page scores 5,000 made-up assets with the same gradient-boosting model that was trained in Python and tested on held-out years. Move a region's storm slider and the model re-scores every asset. The planner then shows where a fixed number of spares should go.</p>
<div class="card"><div class="ctl">
  <div><label for="sl-North">North storm severity <span class="mono" id="sv-North"></span></label><input id="sl-North" type="range" min="0" max="100" step="1" value="10"></div>
  <div><label for="sl-South">South storm severity <span class="mono" id="sv-South"></span></label><input id="sl-South" type="range" min="0" max="100" step="1" value="30"></div>
  <div><label for="sl-East">East storm severity <span class="mono" id="sv-East"></span></label><input id="sl-East" type="range" min="0" max="100" step="1" value="15"></div>
</div>
<div class="cta" style="margin-top:16px"><button class="btn" id="hurr" type="button">Try a South hurricane</button><button class="btn ghost" id="reset" type="button">Back to the 2026 data</button></div></div>
<div class="kpis" id="kpis"></div>
<p class="lede" style="margin-bottom:0">Fill rate comes from 300 simulated years drawn from the model's risk scores. Both policies get the same total spares.</p>
<h3 class="sec">Where the spares should go</h3>
<div class="tblwrap"><table id="matrix" aria-label="Spares by part and region"></table></div>
<h3 class="sec">Assets most at risk</h3>
<div class="tblwrap"><table id="assets" aria-label="Assets by risk"></table></div>
<h3 class="sec">Check against what happened in 2026</h3>
<div class="card"><p id="replay"></p></div>

<h3 class="sec">Technician assistant</h3>
<p class="lede">Answers only from the utility's own manuals and says so when the answer isn't there. This is a small keyword version of the idea. The manuals below are made up for this demo.</p>
<div class="qrow" id="qchips"></div>
<form class="qin" id="qform"><input id="qtext" type="text" maxlength="160" placeholder="Ask a question about the manuals…" aria-label="Question for the technician assistant"><button class="btn" type="submit">Ask</button></form>
<div class="answer" id="answer" aria-live="polite">Pick a question or type your own.</div>
<details class="manuals"><summary>See the demo manuals</summary><ul id="manuals"></ul></details>
'''

evidence = f'''
<p class="eyebrow">Tested code · synthetic data · held-out years</p>
<h2>We trained a model and tested it on years it never saw</h2>
<p class="lede">The code is public. It generates made-up utility data for 5,000 assets over 8 years (40,000 asset-years), trains on 2019 to 2024, and tests on 2025 and 2026. Everything below comes from running that code. Because we wrote the data generator, these numbers show the pipeline works. They do not show how real equipment behaves.</p>
<div class="grid g3">
  <div class="card stat"><b>{M["data"]["train_rows"]:,} / {M["data"]["test_rows"]:,}</b><span>Training rows and held-out test rows. The test years come after the training years, so the model cannot peek.</span></div>
  <div class="card stat"><b>{gb["auc"]:.2f}</b><span>Model AUC on held-out years, against {base["auc"]:.2f} for a plain "older means riskier" rule. 0.5 is a coin flip.</span></div>
  <div class="card stat"><b>{round(sc["fill_rate"]*100)}% → {round(sr["fill_rate"]*100)}%</b><span>Share of real failures that had a spare in the same region, when the same spares are placed by predicted risk instead of by asset count.</span></div>
</div>
<h3 class="sec">Four pictures from the held-out data</h3>
<p class="lede" style="margin-bottom:12px">Hover over a bar to see its exact value. All of it is synthetic data.</p>
<div class="grid g2 figs">
  <figure class="card fig">__C1__<figcaption>Assets in the model's riskiest tenth failed __TOP__% of the time, and the safest tenth failed __BOT__%.</figcaption></figure>
  <figure class="card fig">__C2__<figcaption>In this made-up data, equipment over 50 fails about __OLD__% a year, against under 1% for equipment under 20.</figcaption></figure>
  <figure class="card fig">__C3__<figcaption>Placing spares by risk moves them to the South: __S_RISK__ instead of __S_COUNT__. Real failures there were __S_FAIL__ of __TOTAL__.</figcaption></figure>
  <figure class="card fig">__C4__<figcaption>__IMPTXT__</figcaption></figure>
</div>
<h3 class="sec">Risk model, scored on the held-out years</h3>
<div class="tblwrap"><table>
  <tr><th>Model</th><th>AUC (higher is better)</th><th>Brier error (lower is better)</th><th>Precision, riskiest 10%</th></tr>
  <tr><td>Age-only rule (baseline)</td><td class="cell">{base["auc"]:.3f}</td><td class="cell">{base["brier"]:.4f}</td><td class="cell">{base["precision_top10pct"]*100:.1f}%</td></tr>
  <tr><td>Gradient boosting (6 features)</td><td class="cell">{gb["auc"]:.3f}</td><td class="cell">{gb["brier"]:.4f}</td><td class="cell">{gb["precision_top10pct"]*100:.1f}%</td></tr>
</table></div>
<h3 class="sec">Stocking plan, replayed on the held-out years</h3>
<p class="lede" style="margin-bottom:10px">Both policies get the same total spares. They differ only in where the spares go.</p>
<div class="tblwrap"><table>
  <tr><th>Policy</th><th>Failures with a local spare</th><th>Spares left unused</th></tr>
  <tr><td>Spread by asset count</td><td class="cell">{sc["fill_rate"]*100:.1f}% of {sc["failures"]}</td><td class="cell">{sc["idle_spares"]}</td></tr>
  <tr><td>Placed by predicted risk</td><td class="cell ok">{sr["fill_rate"]*100:.1f}% of {sr["failures"]}</td><td class="cell ok">{sr["idle_spares"]}</td></tr>
</table></div>
<div class="note"><b>Read this before quoting a number.</b>
  <ul style="margin:6px 0 0;padding-left:20px">
    <li>{sc["failures"]} failures in the test years. Enough for a rough read, not for fine claims.</li>
    <li>The boosted model ranks assets better (AUC, precision) but its Brier error is no better than the age-only rule, so its risk numbers are not better calibrated.</li>
    <li>Regions differ in age and storm exposure by design in our generator, so a risk-based policy is bound to help. A real utility may or may not look like this.</li>
    <li>This is one run of one made-up world. A real pilot would use the client's records.</li>
    <li>The Live model page runs the same trained model in your browser. Its results match the Python results to about 7 decimal places.</li>
  </ul></div>
<h3 class="sec">Run it yourself</h3>
<div class="card"><p>The code, data files and 6 tests are in the <a href="{REPO}" target="_blank" rel="noopener">Asset-readiness repository on GitHub</a>. Install the requirements, run <span class="mono">python run_all.py</span>, then <span class="mono">python -m pytest</span>.</p></div>
'''

databricks = '''
<p class="eyebrow">Databricks · how the pipeline maps onto the platform</p>
<h2>The same pipeline, written as a Databricks notebook</h2>
<p class="lede">We turned the prototype into one notebook that builds the tables, trains the model and checks the stocking plan using Databricks building blocks: Delta tables, MLflow and Spark SQL.</p>
<div class="card"><h3>Status, plainly</h3>
<p><b>Written and tested on local Spark. Not yet run in a Databricks workspace.</b> Everything below is the plan for how it runs there. We would run it in a free Databricks account before claiming more.</p></div>
<h3 class="sec">Step by step</h3>
<div class="tblwrap wrapcell"><table>
  <tr><th>Step</th><th>What happens</th><th>Databricks piece</th></tr>
  <tr><td>1 Bronze</td><td>Raw asset history lands as is: 5,000 assets, 8 years, 40,000 rows.</td><td>Delta table</td></tr>
  <tr><td>2 Silver</td><td>Checks for duplicates and missing values. The notebook stops if a check fails.</td><td>Delta table plus assertions</td></tr>
  <tr><td>3 Gold</td><td>Split by time: train 2019 to 2024, test 2025 and 2026.</td><td>Delta tables</td></tr>
  <tr><td>4 Model</td><td>Age-only baseline and gradient boosting, with settings and scores recorded for each run.</td><td>MLflow tracking</td></tr>
  <tr><td>5 Scores</td><td>Every asset gets a failure risk, saved as a table.</td><td>Delta table</td></tr>
  <tr><td>6 Spares</td><td>Same total spares, placed by asset count or by model risk.</td><td>PySpark</td></tr>
  <tr><td>7 Check</td><td>Share of real failures that had a spare in the same region.</td><td>Spark SQL</td></tr>
</table></div>
<h3 class="sec">What the local Spark run gave</h3>
<div class="grid g3">
  <div class="card"><h3>Model on held-out years</h3><p>AUC <span class="big-n">0.753</span> against 0.725 for the age-only rule.</p></div>
  <div class="card"><h3>Spread by asset count</h3><p><span class="big-n">80%</span> of failures (369 of 461) had a local spare. 131 spares unused.</p></div>
  <div class="card"><h3>Placed by model risk</h3><p><span class="big-n">90.5%</span> of failures (417 of 461) had a local spare. 83 spares unused.</p></div>
</div>
<p class="lede">These match the Evidence page. The data is synthetic and we wrote the failure formula, so this shows the pipeline works, not real-world value.</p>
<h3 class="sec">What Databricks would add for a client</h3>
<div class="card"><ul>
  <li>Governed tables, so the client controls who sees which data (Unity Catalog).</li>
  <li>A model registry and a schedule, so retraining runs as a monitored job.</li>
  <li>Real client tables in place of our synthetic ones. Most of the work would be here.</li>
</ul></div>
<h3 class="sec">Try it</h3>
<div class="card"><ol class="steps">
  <li><p>Make a free Databricks account (Free Edition).</p></li>
  <li><p>Import <span class="mono">databricks_notebook.py</span> into the workspace.</p></li>
  <li><p>Attach compute and choose Run all. It takes a few minutes.</p></li>
</ol><p>If a step fails there, we will fix the notebook. Only the local run is verified so far.</p></div>
'''

impact = '''
<p class="eyebrow">What it means for Perficient · our reasoning</p>
<h2>A repeatable offering, not a one-off project</h2>
<p class="lede">Four reasons this fits how Perficient already works. These are our own reasoning from public information, and we would like to hear where we are wrong.</p>
<div class="grid g4">
  <div class="card"><h3>Repeatable</h3><p>The same core serves energy and utilities, manufacturing and distribution, industries Perficient already covers.</p></div>
  <div class="card"><h3>Databricks pull-through</h3><p>Sensor, inspection and inventory data keeps growing, and it lives and is governed on the platform.</p></div>
  <div class="card"><h3>Recurring work</h3><p>Models must be monitored and retrained, so delivery becomes an ongoing service.</p></div>
  <div class="card"><h3>Proof, not a pilot</h3><p>Every recommendation is tested against what really happened, which backs the claim that the work runs in production.</p></div>
</div>
<h3 class="sec">How we would size the value with a client</h3>
<div class="card">
  <p class="lede" style="margin-bottom:6px">Value per year = projects held up by parts × weeks saved per project × cost of one week of delay. The inputs below are placeholders to show the method. Replace them with the client's own numbers.</p>
  <div class="calc">
    <div><label for="c1">Projects held up by parts, per year</label><input id="c1" type="number" min="0" value="20" inputmode="numeric"></div>
    <div><label for="c2">Weeks of delay avoided, per project</label><input id="c2" type="number" min="0" value="6" inputmode="numeric"></div>
    <div><label for="c3">Cost of one week of delay, in dollars</label><input id="c3" type="number" min="0" value="50000" inputmode="numeric"></div>
  </div>
  <p>Example result: <span class="big-n" id="val">$6,000,000</span> a year. <b>Placeholder inputs, not a forecast.</b></p>
</div>
<h3 class="sec">How it grows</h3>
<div class="card">
  <div class="phase"><b>Phase 1</b><p>Prove it small: one asset type in one region, on the client's real records. Test the predictions and the stocking advice on years the model has never seen.</p></div>
  <div class="phase"><b>Phase 2</b><p>Widen it to more asset types and regions.</p></div>
  <div class="phase"><b>Phase 3</b><p>Reuse the core in manufacturing and distribution.</p></div>
  <div class="phase"><b>Phase 4</b><p>Learn across clients, only with client permission and strong privacy controls. This is a governance question we would raise early.</p></div>
</div>
<h3 class="sec">What exists today, and what does not</h3>
<div class="tblwrap wrapcell"><table>
  <tr><th>Piece</th><th>Status</th></tr>
  <tr><td>Technician assistant that refuses when unsure</td><td class="warnc">Small keyword demo on made-up manuals. Not built for real client documents.</td></tr>
  <tr><td>Honest testing</td><td class="ok">Done for the risk model: later years held out, a plain baseline to beat, and 6 tests. Not yet done on real data.</td></tr>
  <tr><td>Failure-risk model and parts forecast</td><td class="warnc">Prototype on synthetic data only, tested on held-out years (see Evidence). Not tried on real utility data.</td></tr>
  <tr><td>Stock-positioning optimizer</td><td class="warnc">Simple allocation tested on synthetic data. A real optimizer with budgets and lead times is not built.</td></tr>
  <tr><td>Data foundation on Databricks</td><td class="warnc">Notebook written and tested on local Spark. Not yet run in a Databricks workspace. See the Databricks page.</td></tr>
</table></div>
<h3 class="sec">Questions for Perficient</h3>
<div class="card"><ol class="steps">
  <li><p>Do you already have a standard way to test AI quality across projects?</p></li>
  <li><p>Is this the kind of problem you would build a platform for, or does it work better one engagement at a time?</p></li>
</ol></div>
'''


import json as _j
def fill_charts(h):
    C = _j.load(open("charts.json")); F = _j.load(open("/tmp/chart_facts.json")) if False else _j.load(open("chart_facts.json"))
    reg = F["reg"]
    for k, v in C.items(): h = h.replace("__" + k.upper() + "__", v)
    h = h.replace("__TOP__", f'{F["top_actual"]*100:.0f}').replace("__OLD__", f'{F["old_rate"]*100:.0f}')
    h = h.replace("__S_RISK__", str(reg["South"][1])).replace("__S_COUNT__", str(reg["South"][0])).replace("__S_FAIL__", str(reg["South"][2]))
    imp = sorted(M["feature_importance"].items(), key=lambda kv: -kv[1]) if isinstance(M["feature_importance"], dict) else M["feature_importance"]
    nm = {"age":"age","storm_severity":"storm severity","oil_acidity":"oil acidity","inspection_score":"inspection score","past_failures":"past failures","load_factor":"load"}
    names = [nm[k] for k, _ in imp]
    h = h.replace("__IMPTXT__", "Age matters most to the model, then " + ", ".join(names[1:-1]) + ". " + names[-1].capitalize() + " matters least here.")
    h = h.replace("__BOT__", f'{F["bottom_actual"]*100:.1f}')
    return h.replace("__TOTAL__", str(sum(v[2] for v in reg.values())))

out = {
    "index.html": page("index.html", "Problem", index),
    "architecture.html": page("architecture.html", "Architecture", arch.replace("__SVG__", open("architecture_detailed.svg").read())),
    "live.html": page("live.html", "Live model", live, '<script src="data.js?v=202611241522"></script>'),
    "databricks.html": page("databricks.html", "Databricks", databricks),
    "evidence.html": page("evidence.html", "Evidence", fill_charts(evidence)),
    "impact.html": page("impact.html", "Impact", impact),
}
for f, h in out.items():
    open(f, "w").write(h)
print("wrote", list(out))
