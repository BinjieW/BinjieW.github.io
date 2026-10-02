// Shared header, tooltip, and small SVG chart helpers for the DECK demo site.
const PAGES = [
  ['index.html', 'Overview'],
  ['benchmark.html', 'Benchmark'],
  ['results.html', 'Results'],
  ['cases.html', 'Case explorer'],
  ['verifier.html', 'Verifier'],
  ['self-improvement.html', 'Self-improvement'],
  ['findings.html', 'More findings'],
  ['gallery.html', 'Gallery'],
];

function mountChrome() {
  const here = location.pathname.split('/').pop() || 'index.html';
  const header = document.createElement('header');
  header.className = 'site-header';
  header.innerHTML = `<div class="shell nav-wrap">
      <a class="brand" href="./index.html"><span class="brand-mark">D</span><span>DECK</span></a>
      <button class="nav-toggle" aria-expanded="false">Menu</button>
      <nav class="site-nav">${PAGES.map(([h, t]) => `<a href="./${h}" class="${h === here ? 'active' : ''}">${t}</a>`).join('')}</nav>
    </div>`;
  document.body.prepend(header);
  header.querySelector('.nav-toggle').onclick = (e) => {
    const nav = header.querySelector('.site-nav');
    nav.classList.toggle('open');
    e.target.setAttribute('aria-expanded', nav.classList.contains('open'));
  };
  const footer = document.createElement('footer');
  footer.className = 'site-footer';
  footer.innerHTML = `<div class="shell">DECK · Benchmarking code edits through the 3D artifacts they produce · Research in progress, October 2026</div>`;
  document.body.append(footer);
}

const tip = (() => {
  let el;
  return {
    show(html, x, y) {
      if (!el) { el = document.createElement('div'); el.className = 'tooltip'; document.body.append(el); }
      el.innerHTML = html;
      el.classList.add('show');
      const r = el.getBoundingClientRect();
      el.style.left = Math.min(x + 14, innerWidth - r.width - 8) + 'px';
      el.style.top = Math.max(8, y - r.height - 12) + 'px';
    },
    hide() { el && el.classList.remove('show'); },
  };
})();

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', '#e87ba4', '#008300', '#4a3aa7', '#e34948'];
const DATA_VERSION = '2026-10-02b'; // bump when data files change so browsers skip stale caches
const loadJSON = (p) => fetch(`${p}?v=${DATA_VERSION}`).then((r) => r.json());

// Line chart: series [{name, values, color}], x labels, y in percent. Direct end labels + hover crosshair.
function lineChart(el, { series, xLabels, yMax = 100, yMin = 0, height = 300, yLabel = 'All-pass (%)' }) {
  const W = Math.max(380, el.clientWidth || 640), H = height, m = { l: 44, r: 150, t: 24, b: 34 };
  const iw = W - m.l - m.r, ih = H - m.t - m.b;
  const x = (i) => m.l + (i * iw) / (xLabels.length - 1);
  const y = (v) => m.t + ih - ((v - yMin) / (yMax - yMin)) * ih;
  const ticks = [];
  for (let v = yMin; v <= yMax; v += (yMax - yMin) / 4) ticks.push(v);
  let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img">`;
  s += ticks.map((v) => `<g class="grid"><line x1="${m.l}" x2="${m.l + iw}" y1="${y(v)}" y2="${y(v)}"/></g><text class="tick" x="${m.l - 8}" y="${y(v) + 4}" text-anchor="end">${Math.round(v)}</text>`).join('');
  s += xLabels.map((t, i) => `<text class="tick" x="${x(i)}" y="${H - 10}" text-anchor="middle">${t}</text>`).join('');
  s += `<text x="${m.l - 36}" y="${m.t - 12}" class="tick">${yLabel}</text>`;
  // end labels, nudged apart
  const ends = series.map((se, k) => ({ k, y: y(se.values[se.values.length - 1]) })).sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) if (ends[i].y - ends[i - 1].y < 15) ends[i].y = ends[i - 1].y + 15;
  const over = ends.length ? ends[ends.length - 1].y - (m.t + ih + 4) : 0;
  if (over > 0) ends.forEach((e) => (e.y -= over));
  for (let i = ends.length - 2; i >= 0; i--) if (ends[i + 1].y - ends[i].y < 15) ends[i].y = ends[i + 1].y - 15;
  series.forEach((se, k) => {
    const c = se.color || SERIES[k];
    const d = se.values.map((v, i) => `${i ? 'L' : 'M'}${x(i)},${y(v)}`).join('');
    s += `<path d="${d}" fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round" ${se.dash ? 'stroke-dasharray="5 4"' : ''}/>`;
    s += se.values.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="3" fill="${c}" stroke="var(--card)" stroke-width="1.5"/>`).join('');
    const ey = ends.find((e) => e.k === k).y;
    s += `<text x="${x(se.values.length - 1) + 10}" y="${ey + 4}" style="fill:var(--ink)">${esc(se.name)}</text>`;
  });
  s += `<line class="xh" x1="0" x2="0" y1="${m.t}" y2="${m.t + ih}" stroke="var(--muted)" stroke-dasharray="3 3" opacity="0"/>`;
  s += `<rect x="${m.l}" y="${m.t}" width="${iw}" height="${ih}" fill="transparent" class="hit"/></svg>`;
  el.innerHTML = s;
  const svg = el.querySelector('svg'), xh = svg.querySelector('.xh');
  svg.querySelector('.hit').addEventListener('mousemove', (ev) => {
    const pt = svg.createSVGPoint(); pt.x = ev.clientX; pt.y = ev.clientY;
    const p = pt.matrixTransform(svg.getScreenCTM().inverse());
    const i = Math.max(0, Math.min(xLabels.length - 1, Math.round(((p.x - m.l) / iw) * (xLabels.length - 1))));
    xh.setAttribute('x1', x(i)); xh.setAttribute('x2', x(i)); xh.setAttribute('opacity', 1);
    tip.show(`<b>${xLabels[i]}</b><br>${series.map((se, k) => `<span style="color:${se.color || SERIES[k]}">●</span> ${esc(se.name)}: ${se.values[i].toFixed(1)}%`).join('<br>')}`, ev.clientX, ev.clientY);
  });
  svg.querySelector('.hit').addEventListener('mouseleave', () => { tip.hide(); xh.setAttribute('opacity', 0); });
}

// Sequential blue ramp for heat tables (light -> dark).
const RAMP = ['#f3f7fd', '#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab'];
function heatColor(v, lo = 0, hi = 100) {
  const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  return RAMP[Math.round(t * (RAMP.length - 1))];
}

// Heat table: rows [{name, values[], extra?}] with optional group headers.
function heatTable(el, { cols, rows, lo = 0, hi = 100, extraCols = [], fmt = (v) => v.toFixed(1) }) {
  let h = `<div class="table-wrap"><table class="data heat"><thead><tr><th>Model</th>${cols.map((c) => `<th>${c}</th>`).join('')}${extraCols.map((c) => `<th>${c}</th>`).join('')}</tr></thead><tbody>`;
  for (const r of rows) {
    if (r.group) { h += `<tr class="group"><td colspan="${cols.length + extraCols.length + 1}">${esc(r.group)}</td></tr>`; continue; }
    h += `<tr><td>${esc(r.name)}</td>` + r.values.map((v, i) => {
      const bg = heatColor(v, lo, hi), dark = RAMP.indexOf(bg) >= 7;
      return `<td class="cell ${dark ? 'dark' : ''}" style="background:${bg}" data-tip="${esc(r.name)} · ${cols[i]}: ${fmt(v)}%">${fmt(v)}</td>`;
    }).join('') + (r.extra || []).map((v) => `<td class="hl">${v}</td>`).join('') + '</tr>';
  }
  el.innerHTML = h + '</tbody></table></div>';
  el.querySelectorAll('td.cell').forEach((td) => {
    td.addEventListener('mousemove', (e) => tip.show(td.dataset.tip, e.clientX, e.clientY));
    td.addEventListener('mouseleave', tip.hide);
  });
}

// 100% stacked horizontal bars, one per row. parts [{key,label,color}], rows [{label, values{key:pct}}].
function stackedBars(el, { parts, rows }) {
  const W = Math.max(380, el.clientWidth || 640), rowH = 30, m = { l: 44, r: 10, t: 6 }, iw = W - m.l - m.r;
  const H = m.t + rows.length * rowH + 22;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}">`;
  rows.forEach((r, i) => {
    let x0 = m.l; const yy = m.t + i * rowH;
    s += `<text x="${m.l - 8}" y="${yy + 17}" text-anchor="end" class="tick">${esc(r.label)}</text>`;
    parts.forEach((p) => {
      const v = r.values[p.key] || 0, w = (v / 100) * iw;
      if (w <= 0) return;
      s += `<rect x="${x0 + 1}" y="${yy}" width="${Math.max(0, w - 2)}" height="${rowH - 8}" rx="3" fill="${p.color}" data-tip="${esc(r.label)} · ${esc(p.label)}: ${v.toFixed(1)}%"/>`;
      if (w > 34) s += `<text x="${x0 + w / 2}" y="${yy + 15}" text-anchor="middle" style="fill:#fff;font-size:11px;font-weight:600;pointer-events:none">${Math.round(v)}</text>`;
      x0 += w;
    });
  });
  [0, 25, 50, 75, 100].forEach((t) => (s += `<text class="tick" x="${m.l + (t / 100) * iw}" y="${H - 4}" text-anchor="middle">${t}%</text>`));
  el.innerHTML = `<div class="legend">${parts.map((p) => `<span><i style="background:${p.color};height:10px;width:10px;border-radius:3px"></i>${esc(p.label)}</span>`).join('')}</div>` + s + '</svg>';
  el.querySelectorAll('rect[data-tip]').forEach((rc) => {
    rc.addEventListener('mousemove', (e) => tip.show(rc.dataset.tip, e.clientX, e.clientY));
    rc.addEventListener('mouseleave', tip.hide);
  });
}

document.addEventListener('DOMContentLoaded', mountChrome);
// Open any render strip at full size in a new tab (useful on small screens).
document.addEventListener('click', (e) => { if (e.target.matches && e.target.matches('img.strip')) window.open(e.target.src, '_blank'); });
