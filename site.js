(function () {
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; }

  /* ---------- architecture page ---------- */
  if ($('layers')) {
    var ARCH = [
      { lab: 'Sources', blocks: [
        ['Asset registry', 'prop', 'Every machine, its age, location and type. The starting point for everything else.'],
        ['Inspections and sensors', 'prop', 'Readings and inspection notes that show how healthy each machine is.'],
        ['Work orders and manuals', 'prop', 'Past repairs and repair guides. Mostly free text, which is where language models help.'],
        ['Parts inventory', 'prop', 'What is on hand at each plant, regional warehouse and central warehouse.'],
        ['Supplier lead times', 'prop', 'How long each part takes to arrive. This decides what must be ordered years ahead.']
      ]},
      { lab: 'Databricks lakehouse', blocks: [
        ['Ingest and quality checks', 'prop', 'Bring the sources into tables and check them: duplicate or missing assets, bad readings. Bad data here ruins every model after it.'],
        ['Governed tables', 'prop', 'Clean tables with role-based access and a record of where each number came from. We understand Unity Catalog handles permissions and lineage, and want Perficient to confirm.']
      ]},
      { lab: 'Intelligence', blocks: [
        ['Failure-risk model', 'proto', 'A gradient-boosting model with six inputs (age, load, inspection score, oil acidity, past failures, storm severity). Trained on synthetic 2019 to 2024 data and scored on 2025 and 2026. It runs live on the Live model page. Not tried on real data.'],
        ['Parts-demand forecast', 'proto', 'Adds up each asset’s failure risk by region and part type to get expected failures.'],
        ['Stock optimizer', 'proto', 'Today: splits a fixed number of spares across regions in proportion to expected failures. A real optimizer would also use budgets, lead times and transfers. Not built.']
      ]},
      { lab: 'Apps', blocks: [
        ['Planner dashboard', 'proto', 'The Live model page is a first version: change the storm, see expected failures and where the spares should go.'],
        ['Technician assistant', 'proto', 'Answers from the manuals and past work orders, and refuses when the answer is not there. The version on the Live model page is a small keyword demo on made-up manuals. Not built for real client documents.']
      ]},
      { lab: 'Trust layer', blocks: [
        ['Held-out evaluation', 'proto', 'Test on data the model has never seen and report the misses. This project holds out the later years and compares against a plain age-only rule. Not yet done on real data.'],
        ['Cost and audit', 'prop', 'Budget caps, a record of every recommendation, and a human approving every order or transfer. Proposed, not built.']
      ]}
    ];
    var STNAME = { proto: 'Prototype on synthetic data', prop: 'Proposed, not built' };
    var STCLS = { built: 'st-built', proto: 'st-sim', prop: 'st-prop' };
    var layersEl = $('layers'), pressed = null;
    ARCH.forEach(function (L, li) {
      if (li > 0) { var ar = el('div', 'arrow'); ar.appendChild(el('span', null, '↓')); layersEl.appendChild(ar); }
      var row = el('div', 'layer'); row.appendChild(el('div', 'lab', L.lab));
      var bl = el('div', 'blocks');
      L.blocks.forEach(function (b, bi) {
        var btn = el('button', 'blk', b[0]); btn.type = 'button'; btn.setAttribute('aria-pressed', 'false');
        btn.appendChild(el('i', STCLS[b[1]], '● ' + STNAME[b[1]]));
        btn.addEventListener('click', function () {
          if (pressed) pressed.setAttribute('aria-pressed', 'false');
          btn.setAttribute('aria-pressed', 'true'); pressed = btn;
          var d = $('detail'); d.textContent = '';
          d.appendChild(el('h3', null, b[0])); d.appendChild(el('p', null, b[2]));
          var s = el('p', STCLS[b[1]], '● ' + STNAME[b[1]]); s.style.marginTop = '8px'; d.appendChild(s);
        });
        bl.appendChild(btn);
        if (li === 2 && bi === 0) setTimeout(function () { btn.click(); }, 0);
      });
      row.appendChild(bl); layersEl.appendChild(row);
    });
  }

  /* ---------- live model page ---------- */
  if ($('sl-North')) {
    var M = window.AR_MODEL, A = window.AR_ASSETS, ci = {};
    A.cols.forEach(function (c, i) { ci[c] = i; });
    var REG = ['North', 'South', 'East'];
    var PARTS = [['dist_25kva', 'Distribution transformer, 25 kVA', 18], ['dist_75kva', 'Distribution transformer, 75 kVA', 26],
                 ['substation_xfmr', 'Substation transformer', 128], ['breaker_69kv', '69 kV circuit breaker', 52]];
    var ASSETS = A.rows.map(function (r) {
      var o = { id: r[ci.asset_id], region: r[ci.region], part: r[ci.part], failed: r[ci.failed], x: M.features.map(function (f) { return r[ci[f]]; }) };
      return o;
    });
    var SI = M.features.indexOf('storm_severity');
    var actualStorm = {};
    ASSETS.forEach(function (a) { actualStorm[a.region] = a.x[SI]; });

    function score(x) {
      var f = M.init;
      for (var k = 0; k < M.trees.length; k++) {
        var t = M.trees[k], n = 0;
        while (t.l[n] !== -1) n = (Math.fround(x[t.f[n]]) <= t.t[n]) ? t.l[n] : t.r[n];
        f += M.lr * t.v[n];
      }
      return 1 / (1 + Math.exp(-f));
    }
    function risks(storm) {
      return ASSETS.map(function (a) {
        var x = a.x.slice(); x[SI] = storm[a.region]; return score(x);
      });
    }
    function allocate(total, w) {
      var s = w.reduce(function (p, q) { return p + q; }, 0);
      var ww = s > 0 ? w.map(function (v) { return v / s; }) : w.map(function () { return 1 / w.length; });
      var raw = ww.map(function (v) { return v * total; }), base = raw.map(Math.floor);
      var left = total - base.reduce(function (p, q) { return p + q; }, 0);
      raw.map(function (v, i) { return [v - base[i], i]; }).sort(function (p, q) { return q[0] - p[0]; })
        .slice(0, left).forEach(function (p) { base[p[1]] += 1; });
      return base;
    }
    function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

    function build(p) {
      // per part and region: asset indices, expected failures, spares under both policies
      var cells = [];
      PARTS.forEach(function (pt) {
        var idx = REG.map(function () { return []; });
        ASSETS.forEach(function (a, i) { if (a.part === pt[0]) idx[REG.indexOf(a.region)].push(i); });
        var nPart = idx.reduce(function (s, v) { return s + v.length; }, 0);
        var total = Math.max(1, Math.round(nPart * 0.05));
        var cnt = idx.map(function (v) { return v.length; });
        var exp = idx.map(function (v) { return v.reduce(function (s, i) { return s + p[i]; }, 0); });
        cells.push({ part: pt, idx: idx, total: total, cnt: cnt, exp: exp, stockCount: allocate(total, cnt), stockRisk: allocate(total, exp) });
      });
      return cells;
    }
    function monteCarlo(cells, p, trials) {
      var rand = rng(2026), cov = [0, 0], tot = 0, idle = [0, 0];
      for (var t = 0; t < trials; t++) {
        cells.forEach(function (c) {
          for (var r = 0; r < REG.length; r++) {
            var f = 0; c.idx[r].forEach(function (i) { if (rand() < p[i]) f++; });
            tot += f;
            cov[0] += Math.min(c.stockCount[r], f); cov[1] += Math.min(c.stockRisk[r], f);
            idle[0] += Math.max(0, c.stockCount[r] - f); idle[1] += Math.max(0, c.stockRisk[r] - f);
          }
        });
      }
      return { fillCount: cov[0] / tot, fillRisk: cov[1] / tot, idleCount: idle[0] / trials, idleRisk: idle[1] / trials, fails: tot / trials };
    }
    function pct(v) { return Math.round(v * 100) + '%'; }

    function render() {
      var storm = {};
      REG.forEach(function (r) { storm[r] = +$('sl-' + r).value / 100; $('sv-' + r).textContent = Math.round(storm[r] * 100) + '%'; });
      var p = risks(storm), cells = build(p), mc = monteCarlo(cells, p, 300);
      var k = $('kpis'); k.textContent = '';
      function kpi(l, v, s) { var d = el('div', 'kpi'); d.appendChild(el('span', null, l)); d.appendChild(el('b', null, v)); d.appendChild(el('small', null, s)); k.appendChild(d); }
      kpi('Expected failures', mc.fails.toFixed(1), 'per year, all 5,000 assets');
      kpi('Spares placed by asset count', pct(mc.fillCount), 'of failures had a local spare');
      kpi('Spares placed by model risk', pct(mc.fillRisk), 'of failures had a local spare');
      kpi('Unused spares, model risk', mc.idleRisk.toFixed(1), 'vs ' + mc.idleCount.toFixed(1) + ' by asset count');

      var m = $('matrix'); m.textContent = '';
      var hr = el('tr'); ['Part', 'Region', 'Assets', 'Expected failures', 'Spares by count', 'Spares by risk', 'Lead time'].forEach(function (h) { hr.appendChild(el('th', null, h)); }); m.appendChild(hr);
      cells.forEach(function (c) {
        REG.forEach(function (r, ri) {
          var tr = el('tr'); tr.appendChild(el('td', null, ri === 0 ? c.part[1] : '')); tr.appendChild(el('td', null, r));
          tr.appendChild(el('td', 'cell', String(c.cnt[ri]))); tr.appendChild(el('td', 'cell', c.exp[ri].toFixed(2)));
          tr.appendChild(el('td', 'cell', String(c.stockCount[ri])));
          var d = c.stockRisk[ri] - c.stockCount[ri];
          tr.appendChild(el('td', 'cell ' + (d > 0 ? 'ok' : d < 0 ? 'warnc' : ''), c.stockRisk[ri] + (d > 0 ? ' (+' + d + ')' : d < 0 ? ' (' + d + ')' : '')));
          tr.appendChild(el('td', 'cell', ri === 0 ? c.part[2] + ' wks' : '')); m.appendChild(tr);
        });
      });

      var a = $('assets'); a.textContent = '';
      var ah = el('tr'); ['Asset', 'Region', 'Part', 'Age', 'Inspection', 'Past failures', 'Failure risk'].forEach(function (h) { ah.appendChild(el('th', null, h)); }); a.appendChild(ah);
      ASSETS.map(function (s, i) { return [i, p[i]]; }).sort(function (x, y) { return y[1] - x[1]; }).slice(0, 8).forEach(function (e) {
        var s = ASSETS[e[0]], tr = el('tr'), nm = PARTS.filter(function (q) { return q[0] === s.part; })[0][1];
        tr.appendChild(el('td', 'cell', s.id)); tr.appendChild(el('td', null, s.region)); tr.appendChild(el('td', null, nm));
        tr.appendChild(el('td', 'cell', s.x[0].toFixed(0) + ' yrs')); tr.appendChild(el('td', 'cell', s.x[2].toFixed(0))); tr.appendChild(el('td', 'cell', String(s.x[4])));
        var td = el('td', 'cell'), bar = el('span', 'riskbar'), fill = el('i'); fill.style.width = Math.round(e[1] * 100) + '%'; bar.appendChild(fill);
        td.appendChild(bar); td.appendChild(document.createTextNode(Math.round(e[1] * 100) + '%')); tr.appendChild(td); a.appendChild(tr);
      });
    }
    // replay of the real 2026 outcomes at the real 2026 storms
    (function replay() {
      var p = risks(actualStorm), cells = build(p), cov = [0, 0], tot = 0;
      cells.forEach(function (c) {
        for (var r = 0; r < REG.length; r++) {
          var f = c.idx[r].reduce(function (s, i) { return s + ASSETS[i].failed; }, 0);
          tot += f; cov[0] += Math.min(c.stockCount[r], f); cov[1] += Math.min(c.stockRisk[r], f);
        }
      });
      $('replay').textContent = 'In the 2026 rows of the held-out data, ' + tot + ' assets actually failed. With the same spares, placing them by asset count gave ' + cov[0] + ' of those failures a local spare (' + pct(cov[0] / tot) + '), and placing them by model risk gave ' + cov[1] + ' (' + pct(cov[1] / tot) + '). One year only, so treat it as a rough check.';
    })();
    REG.forEach(function (r) {
      $('sl-' + r).value = Math.round(actualStorm[r] * 100); $('sl-' + r).addEventListener('input', render);
    });
    $('reset').addEventListener('click', function () { REG.forEach(function (r) { $('sl-' + r).value = Math.round(actualStorm[r] * 100); }); render(); });
    $('hurr').addEventListener('click', function () { $('sl-South').value = 85; $('sl-North').value = 20; $('sl-East').value = 30; render(); });
    render();
  }

  /* ---------- technician assistant ---------- */
  if ($('qform')) {
    var MAN = [
      ['M1 Transformer replacement', 'To replace a 25 kVA transformer: de-energize and verify, isolate the secondary, apply lockout and tagout, swap the transformer, check polarity, re-energize, and record the serial number in the work order.'],
      ['M2 Oil leak inspection', 'Oil leak inspection: check gaskets and bushings. A slow seep is monitored weekly. A drip rate over one drop per minute means schedule replacement.'],
      ['M3 Storm response', 'Storm response: patrol feeders, serve hospitals and water plants first, tag damaged units, and request crews through dispatch.'],
      ['M4 Breaker maintenance', 'Breaker maintenance for a 69 kV breaker: test trip time every year. Contact resistance above 150 microohms means schedule service.'],
      ['M5 Parts transfers', 'The planner approves moving parts between warehouses in the work order system, and every move is logged with a transit record.']
    ];
    var STOP = ['a', 'an', 'the', 'is', 'are', 'was', 'what', 'how', 'do', 'does', 'i', 'to', 'of', 'on', 'in', 'for', 'and', 'or', 'can', 'who', 'when', 'where', 'my', 'me', 'it', 'if', 'at', 'by', 'with', 'before', 'should', 'we', 'you', 'there', 'this', 'that', 'be', 'have', 'has'];
    var toks = function (s) { return s.toLowerCase().split(/[^a-z0-9]+/).filter(function (w) { return w && STOP.indexOf(w) < 0; }); };
    var ml = $('manuals'); MAN.forEach(function (m) { var li = el('li'); li.appendChild(el('b', null, m[0] + ': ')); li.appendChild(document.createTextNode(m[1])); ml.appendChild(li); });
    var QS = ['How do I replace a 25 kVA transformer?', 'How fast can an oil leak drip before replacement?', 'Who approves moving parts between warehouses?', 'What is the warranty on the 500 kVA unit?'];
    var qc = $('qchips');
    var ask = function (q) {
      var box = $('answer'); box.textContent = ''; box.className = 'answer';
      var qt = toks(q);
      if (!qt.length) { box.textContent = 'Type a question first.'; return; }
      var best = null, bestN = 0, bestHit = [], uniq = qt.filter(function (w, i) { return qt.indexOf(w) === i; });
      MAN.forEach(function (m) {
        var dt = toks(m[0] + ' ' + m[1]), hit = uniq.filter(function (w) { return dt.indexOf(w) >= 0; });
        if (hit.length > bestN) { best = m; bestN = hit.length; bestHit = hit; }
      });
      if (best && bestN >= 2 && bestN / uniq.length >= 0.6) {
        box.appendChild(el('p', null, best[1]));
        box.appendChild(el('p', 'src2', 'Source: ' + best[0] + ' · matched ' + bestN + ' of ' + uniq.length + ' key terms (' + bestHit.join(', ') + ')'));
      } else {
        box.className = 'answer refuse';
        box.appendChild(el('p', null, 'I can’t find that in the manuals, so I won’t guess. Ask the equipment vendor or the planning team.'));
        box.appendChild(el('p', 'src2', best ? 'Closest match was ' + best[0] + ', with only ' + bestN + ' of ' + uniq.length + ' key terms. Not enough to answer.' : 'No manual shares a key term with this question.'));
      }
    };
    QS.forEach(function (q) {
      var b = el('button', 'chip', q); b.type = 'button'; b.setAttribute('aria-pressed', 'false');
      b.addEventListener('click', function () { $('qtext').value = q; ask(q); [].forEach.call(qc.children, function (c) { c.setAttribute('aria-pressed', c === b ? 'true' : 'false'); }); });
      qc.appendChild(b);
    });
    $('qform').addEventListener('submit', function (e) { e.preventDefault(); [].forEach.call(qc.children, function (c) { c.setAttribute('aria-pressed', 'false'); }); ask($('qtext').value); });
  }

  /* ---------- value calculator ---------- */
  if ($('c1')) {
    var calc = function () { $('val').textContent = '$' + Math.round((+$('c1').value || 0) * (+$('c2').value || 0) * (+$('c3').value || 0)).toLocaleString('en-US'); };
    ['c1', 'c2', 'c3'].forEach(function (id) { $(id).addEventListener('input', calc); });
    calc();
  }
})();
