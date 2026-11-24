"""Draw four charts from the real held-out results as inline SVG (hover shows the exact value)."""
import numpy as np, pandas as pd, json
from generate_data import REGIONS, PARTS
from train import train_and_score
from plan import allocate, spares_per_part

TEAL, GRAY, INK, GRID, MUTED = "#0d5f7c", "#7a858d", "#15222e", "#d8ddd6", "#566570"
tr, te = pd.read_csv("train.csv"), pd.read_csv("test.csv")
gbm, p, models, imp = train_and_score(tr, te)
te = te.assign(risk=p)
FONT = 'font-family="IBM Plex Sans,system-ui,Arial,sans-serif"'

def svg(w, h, title, desc, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{title}" class="chart">'
            f'<title>{title}</title><desc>{desc}</desc>{body}</svg>')

def t(x, y, s, size=12.5, fill=MUTED, anchor="start", weight=400):
    return f'<text x="{x}" y="{y}" {FONT} font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{s}</text>'

def yaxis(x0, x1, y0, y1, vmax, ticks, fmt):
    o = []
    for v in ticks:
        y = y0 - (y0 - y1) * v / vmax
        o.append(f'<line x1="{x0}" x2="{x1}" y1="{y:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(t(x0 - 8, y + 4, fmt(v), 11.5, MUTED, "end"))
    return "".join(o)

def bar(x, y0, w, h, fill, tip):
    h = max(h, 0)
    return f'<g><title>{tip}</title><rect x="{x:.1f}" y="{y0-h:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="{fill}"/><rect x="{x:.1f}" y="{y0-min(h,4):.1f}" width="{w:.1f}" height="{min(h,4):.1f}" fill="{fill}"/></g>'

# ---- Chart 1: predicted vs actual failure rate by risk decile (held-out years) ----
te["dec"] = pd.qcut(te.risk.rank(method="first"), 10, labels=False)
g = te.groupby("dec").agg(pred=("risk", "mean"), act=("failed", "mean"), n=("failed", "size"), f=("failed", "sum"))
W, H, x0, x1, y0, y1 = 640, 340, 56, 620, 270, 40
vmax = 0.30
b = yaxis(x0, x1, y0, y1, vmax, [0, .1, .2, .3], lambda v: f"{v*100:.0f}%")
bw = (x1 - x0) / 10
for i, r in g.iterrows():
    cx = x0 + bw * i + bw * 0.5
    b += bar(cx - bw * 0.30, y0, bw * 0.60, (y0 - y1) * r.act / vmax, TEAL, f"Risk group {i+1} of 10: {r.act*100:.1f}% actually failed ({int(r.f)} of {int(r.n)}); model predicted {r.pred*100:.1f}%")
    py = y0 - (y0 - y1) * r.pred / vmax
    b += f'<g><title>Model predicted {r.pred*100:.1f}%</title><circle cx="{cx:.1f}" cy="{py:.1f}" r="5" fill="#ffffff" stroke="{INK}" stroke-width="2"/></g>'
    b += t(cx, y0 + 18, str(i + 1), 12, MUTED, "middle")
b += t((x0 + x1) / 2, y0 + 40, "Assets sorted from lowest predicted risk (1) to highest (10), held-out years", 12.5, MUTED, "middle")
b += f'<rect x="{x0}" y="8" width="12" height="12" rx="3" fill="{TEAL}"/>' + t(x0 + 18, 19, "Share that actually failed", 12.5, INK)
b += f'<circle cx="{x0+210}" cy="14" r="5" fill="#fff" stroke="{INK}" stroke-width="2"/>' + t(x0 + 222, 19, "What the model predicted", 12.5, INK)
c1 = svg(W, H, "Predicted versus actual failure rate by risk group", "Bars show the share of assets that failed in each of ten risk groups. Circles show the model's prediction.", b)
top, bot = g.loc[9], g.loc[0]

# ---- Chart 2: failure rate by age band ----
allr = pd.concat([tr, te])
bands = [(0, 20, "Under 20"), (20, 30, "20 to 29"), (30, 40, "30 to 39"), (40, 50, "40 to 49"), (50, 99, "50 and over")]
vals = []
for lo, hi, lab in bands:
    s = allr[(allr.age >= lo) & (allr.age < hi)]
    vals.append((lab, s.failed.mean(), len(s)))
W, H, x0, x1, y0, y1 = 640, 300, 56, 620, 232, 30
vmax = max(v[1] for v in vals) * 1.15
tick = 0.05 if vmax > 0.12 else 0.02
ticks = [i * tick for i in range(0, int(vmax / tick) + 1)]
b = yaxis(x0, x1, y0, y1, vmax, ticks, lambda v: f"{v*100:.0f}%")
bw = (x1 - x0) / len(vals)
for i, (lab, v, n) in enumerate(vals):
    cx = x0 + bw * i + bw / 2
    b += bar(cx - 34, y0, 68, (y0 - y1) * v / vmax, TEAL, f"{lab} years: {v*100:.1f}% failed per year ({n:,} asset-years)")
    b += t(cx, y0 - (y0 - y1) * v / vmax - 8, f"{v*100:.1f}%", 13, INK, "middle", 600)
    b += t(cx, y0 + 18, lab, 12, MUTED, "middle")
b += t((x0 + x1) / 2, y0 + 40, "Equipment age in years, all eight years of data", 12.5, MUTED, "middle")
c2 = svg(W, H, "Yearly failure rate by equipment age", "Older equipment fails more often in this synthetic data.", b)

# ---- Chart 3: spares by region vs failures, held-out years ----
reg = {r: [0, 0, 0] for r in REGIONS}  # spares by count, spares by risk, actual failures
for y, gy in te.groupby("year"):
    for part in PARTS:
        gp = gy[gy.part == part]
        tot = spares_per_part({part: len(gp)})[part]
        cw = gp.groupby("region").size().reindex(REGIONS, fill_value=0).to_dict()
        rw = gp.groupby("region").risk.sum().reindex(REGIONS, fill_value=0).to_dict()
        fl = gp.groupby("region").failed.sum().reindex(REGIONS, fill_value=0).to_dict()
        a, bb = allocate(tot, cw), allocate(tot, rw)
        for r in REGIONS:
            reg[r][0] += a[r]; reg[r][1] += bb[r]; reg[r][2] += int(fl[r])
W, H, x0, x1, y0, y1 = 640, 330, 56, 620, 250, 56
vmax = max(max(v) for v in reg.values()) * 1.2
step = 10 if vmax > 40 else 5
b = yaxis(x0, x1, y0, y1, vmax, list(range(0, int(vmax) + 1, step)), lambda v: f"{v:.0f}")
gw = (x1 - x0) / 3
for i, r in enumerate(REGIONS):
    cx = x0 + gw * i + gw / 2
    for j, (v, col, lab) in enumerate(zip(reg[r], [GRAY, TEAL, INK], ["Spares placed by asset count", "Spares placed by model risk", "Failures that actually happened"])):
        x = cx - 66 + j * 46
        if j < 2:
            b += bar(x, y0, 40, (y0 - y1) * v / vmax, col, f"{r}: {lab}: {v}")
        else:
            yy = y0 - (y0 - y1) * v / vmax
            b += f'<g><title>{r}: {lab}: {v}</title><rect x="{x:.1f}" y="{yy:.1f}" width="40" height="{y0-yy:.1f}" rx="4" fill="#ffffff" stroke="{INK}" stroke-width="2"/></g>'
        b += t(x + 20, y0 - (y0 - y1) * v / vmax - 7, str(v), 12.5, INK, "middle", 600)
    b += t(cx, y0 + 20, r, 13, INK, "middle", 600)
lx = x0
for col, lab, hollow in [(GRAY, "Spares by asset count", False), (TEAL, "Spares by model risk", False), (INK, "Real failures", True)]:
    b += (f'<rect x="{lx}" y="12" width="12" height="12" rx="3" fill="#fff" stroke="{INK}" stroke-width="2"/>' if hollow else f'<rect x="{lx}" y="12" width="12" height="12" rx="3" fill="{col}"/>') + t(lx + 18, 23, lab, 12.5, INK)
    lx += 190
b += t((x0 + x1) / 2, y0 + 44, "Totals for 2025 and 2026, all four part types", 12.5, MUTED, "middle")
c3 = svg(W, H, "Spares and real failures by region", "Placing spares by predicted risk moves them toward the South, where most failures happen.", b)

# ---- Chart 4: what the model pays attention to ----
names = {"past_failures": "Past failures", "age": "Age", "oil_acidity": "Oil acidity", "load_factor": "Load", "inspection_score": "Inspection score", "storm_severity": "Storm severity"}
W, H, x0, x1 = 640, 300, 150, 600
rows = imp
vm = max(v for _, v in rows) * 1.1
b = ""
rh = 38
for i, (f, v) in enumerate(rows):
    y = 24 + i * rh
    wv = (x1 - x0) * v / vm
    b += t(x0 - 10, y + 17, names.get(f, f), 13, INK, "end")
    b += f'<g><title>{names.get(f,f)}: {v*100:.0f}% of the model\'s attention</title><rect x="{x0}" y="{y}" width="{wv:.1f}" height="24" rx="4" fill="{TEAL}"/></g>'
    b += t(x0 + wv + 8, y + 17, f"{v*100:.0f}%", 13, INK, "start", 600)
b += t((x0 + x1) / 2, H - 14, "Share of the trained model's splits by each input (importance)", 12.5, MUTED, "middle")
c4 = svg(W, H, "What the failure model pays attention to", "Bars show how much each of the six inputs matters to the trained model.", b)

json.dump({"top_actual": round(float(top.act), 3), "bottom_actual": round(float(bot.act), 3), "old_rate": round(float(vals[-1][1]), 3), "reg": reg}, open("chart_facts.json", "w"))
open("charts.json", "w").write(json.dumps({"c1": c1, "c2": c2, "c3": c3, "c4": c4}))
print("top decile actual", round(float(top.act), 3), "bottom", round(float(bot.act), 3)); print(reg); print(vals); print(imp)
