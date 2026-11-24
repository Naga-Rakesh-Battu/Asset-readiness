"""Draw the detailed Asset Readiness architecture as one SVG."""
S = {"proto": ("#e3f0f4", "#0d5f7c"), "prop": ("#fbeadb", "#b85a0b"), "src": ("#ffffff", "#8a959c")}
out = []
def box(x, y, w, h, title, lines, st):
    fill, stroke = S[st]
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>')
    out.append(f'<text x="{x+12}" y="{y+22}" class="ar-t" fill="#15222e">{title}</text>')
    for i, l in enumerate(lines):
        out.append(f'<text x="{x+12}" y="{y+41+i*16}" class="ar-s" fill="#566570">{l}</text>')
def arrow(x1, y1, x2, y2):
    out.append(f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#15222e" stroke-width="1.8" fill="none" marker-end="url(#ar-ah)"/>')
def col(x, w, title):
    out.append(f'<text x="{x+w/2}" y="40" class="ar-c" text-anchor="middle">{title}</text>')
W, H = 1180, 700
col(20, 190, "1 · SOURCES"); col(250, 290, "2 · DATABRICKS LAKEHOUSE"); col(590, 260, "3 · INTELLIGENCE"); col(900, 260, "4 · PEOPLE AND APPS")
srcs = [("Asset registry", ["age, type, location"]), ("Inspections, sensors", ["condition readings"]), ("Work orders, manuals", ["repair history, guides"]),
        ("Parts inventory", ["stock by warehouse"]), ("Supplier lead times", ["weeks to deliver"]), ("Weather and storms", ["severity by region"])]
for i, (t, l) in enumerate(srcs):
    box(20, 60 + i * 84, 190, 68, t, l, "src")
out.append('<rect x="240" y="56" width="310" height="496" rx="12" fill="#f7faf9" stroke="#b85a0b" stroke-width="1.6" stroke-dasharray="6 4"/>')
box(256, 76, 278, 84, "Ingest and quality checks", ["catch duplicates, missing assets", "and bad readings before models"], "prop")
box(256, 192, 278, 120, "Governed Delta tables", ["raw  →  cleaned  →  model-ready", "one asset ID joins everything", "history kept for retraining"], "prop")
box(256, 344, 278, 84, "Access control and lineage", ["who can see what, and where", "each number came from (Unity Catalog)"], "prop")
box(256, 460, 278, 76, "Model tracking", ["every model version and its", "test scores recorded (MLflow)"], "prop")
box(590, 76, 260, 112, "Failure-risk model", ["gradient boosting, 6 inputs", "age, load, inspection, oil,", "past failures, storm severity"], "proto")
box(590, 220, 260, 96, "Parts-demand forecast", ["adds up risk by region", "and part type"], "proto")
box(590, 348, 260, 124, "Stock optimizer", ["today: split fixed spares by", "expected failures", "next: budgets, lead times,", "transfers between sites"], "proto")
box(900, 76, 260, 112, "Planner dashboard", ["storm what-if, spares by region", "assets most at risk", "(Live model page)"], "proto")
box(900, 220, 260, 112, "Technician assistant", ["reads manuals and work orders", "from the lakehouse, refuses when", "the answer is not there"], "proto")
box(900, 364, 260, 108, "Human approval", ["a planner approves every", "order or transfer"], "prop")
box(900, 504, 260, 60, "Work-order / ERP system", ["orders and moves are recorded"], "prop")
for i in range(6):
    y = 94 + i * 84
    arrow(210, y, 240, y if y < 540 else 520)
arrow(395, 160, 395, 192); arrow(395, 312, 395, 344)
arrow(550, 250, 590, 132); arrow(550, 250, 590, 268); arrow(550, 250, 590, 410)
arrow(720, 188, 720, 220); arrow(720, 316, 720, 348)
arrow(850, 132, 900, 132); arrow(850, 410, 900, 410)
arrow(1030, 472, 1030, 504)
out.append('<path d="M1030,564 L1030,612 L395,612 L395,552" stroke="#0d5f7c" stroke-width="1.8" fill="none" stroke-dasharray="6 4" marker-end="url(#ar-ah2)"/>')
out.append('<text x="712" y="604" class="ar-s" fill="#0d5f7c" text-anchor="middle">real failures and orders flow back, so the next model learns from what happened</text>')
out.append('<rect x="20" y="632" width="1140" height="52" rx="9" fill="#ffffff" stroke="#0d5f7c" stroke-width="1.6"/>')
out.append('<text x="34" y="654" class="ar-t" fill="#15222e">Trust layer across everything</text>')
out.append('<text x="34" y="674" class="ar-s" fill="#566570">Held-out test years and a plain baseline to beat  ·  budget and cost caps  ·  audit log of every recommendation  ·  a human approves orders  ·  guardrails on the assistant</text>')
body = "\n".join(out)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H+34}" width="100%" role="img" aria-labelledby="ar2-title ar2-desc" class="ar-diagram">
<title id="ar2-title">Asset Readiness detailed architecture</title>
<desc id="ar2-desc">Data from six sources flows into a Databricks lakehouse, then through a failure-risk model, a parts-demand forecast and a stock optimizer, then to a planner dashboard, a technician assistant and human approval, with a trust layer across all of it.</desc>
<style>.ar-t{{font:600 14px "IBM Plex Sans",system-ui,Arial,sans-serif}}.ar-s{{font:400 12.5px "IBM Plex Sans",system-ui,Arial,sans-serif}}.ar-c{{font:500 12.5px "IBM Plex Mono",ui-monospace,monospace;fill:#0d5f7c;letter-spacing:.04em}}.ar-lg{{font:400 12.5px "IBM Plex Sans",system-ui,Arial,sans-serif;fill:#15222e}}</style>
<defs><marker id="ar-ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#15222e"/></marker>
<marker id="ar-ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#0d5f7c"/></marker></defs>
<rect width="{W}" height="{H+34}" fill="#f3f4ef"/>
{body}
<g transform="translate(20,{H+8})"><rect width="14" height="14" rx="3" fill="#e3f0f4" stroke="#0d5f7c" stroke-width="1.6"/><text x="22" y="12" class="ar-lg">Prototype on synthetic data</text>
<rect x="260" width="14" height="14" rx="3" fill="#fbeadb" stroke="#b85a0b" stroke-width="1.6"/><text x="282" y="12" class="ar-lg">Proposed, not built</text>
<rect x="470" width="14" height="14" rx="3" fill="#ffffff" stroke="#8a959c" stroke-width="1.6"/><text x="492" y="12" class="ar-lg">Client's existing data</text></g>
</svg>'''
open("architecture_detailed.svg", "w").write(svg)
