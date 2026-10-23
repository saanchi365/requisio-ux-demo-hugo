/* The few things on the Hugo handbook that react to clicks: search, menu, slideshow, flowcharts, filters. */
(function () {
  const DATA = JSON.parse(document.getElementById('hb-data').textContent);
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));

  /* ---- menu on small screens */
  const side = $('#hb-side');
  $('#hb-menu-btn')?.addEventListener('click', () => side.classList.toggle('show'));

  /* ---- search: features, requirements and flowcharts */
  const q = $('#hb-q'), res = $('#hb-res');
  q?.addEventListener('input', () => {
    const t = q.value.trim().toLowerCase();
    if (t.length < 2) { res.hidden = true; return; }
    const hits = DATA.index.filter((x) => x.t.toLowerCase().includes(t)).slice(0, 10);
    res.innerHTML = hits.length ? hits.map((x) => `<a href="${x.u}"><span>${esc(x.t)}</span><span class="xs" style="margin-left:auto">${x.k}</span></a>`).join('')
      : `<div class="sm mu" style="padding:8px">Nothing found for "${esc(t)}".</div>`;
    res.hidden = false;
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('.hb-srch')) res && (res.hidden = true); });

  /* ---- wireframes: slideshow and flow view */
  const wf = $('[data-wf]');
  if (wf) {
    const slides = $$('.slide', wf), total = slides.length;
    let cur = 0;
    const show = (i) => {
      cur = (i + total) % total;
      slides.forEach((s, k) => { s.hidden = k !== cur; });
      $('[data-pager]', wf).textContent = `${cur + 1} / ${total}`;
      $$('.mapsc', wf).forEach((b) => b.classList.toggle('on', +b.dataset.go === cur));
      const open = $(`.mapsc[data-go="${cur}"]`, wf)?.closest('details');
      if (open) open.open = true;
    };
    const mode = (m) => {
      $$('[data-mode]', wf).forEach((b) => b.classList.toggle('on', b.dataset.mode === m));
      $$('[data-view]', wf).forEach((v) => { v.hidden = v.dataset.view !== m; });
    };
    wf.addEventListener('click', (e) => {
      const t = e.target.closest('[data-step],[data-go],[data-mode]');
      if (!t) return;
      if (t.dataset.mode) mode(t.dataset.mode);
      else if (t.dataset.step) show(cur + +t.dataset.step);
      else { e.preventDefault(); show(+t.dataset.go); if (t.hasAttribute('data-to-slides')) mode('slideshow'); }
    });
    document.addEventListener('keydown', (e) => {
      if (e.target.closest('input,textarea,select') || $('[data-view="slideshow"]', wf).hidden) return;
      if (e.key === 'ArrowLeft') show(cur - 1);
      if (e.key === 'ArrowRight') show(cur + 1);
    });
    const m = location.hash.match(/^#screen-(.+)$/);
    if (m) { const k = slides.findIndex((s) => s.dataset.file === decodeURIComponent(m[1])); if (k >= 0) show(k); }
  }

  /* ---- flowcharts: draw, zoom, hide details, switch flows, open features from the product chart */
  if (window.mermaid && $('.mermaid')) {
    const dark = matchMedia('(prefers-color-scheme: dark)').matches;
    mermaid.initialize({startOnLoad: false, theme: dark ? 'dark' : 'neutral', securityLevel: 'strict', flowchart: {htmlLabels: true}});
    mermaid.run({querySelector: '.mermaid'}).then(() => {
      $$('.fcpane[data-product] svg g.node').forEach((node) => {
        const n = (node.textContent.match(/#(\d+)/) || [])[1];
        const f = n && DATA.reqFeature[n];
        if (!f) return;
        node.style.cursor = 'pointer';
        node.addEventListener('click', () => { location.href = `${DATA.base}feature-${f}/flowcharts/`; });
      });
    }).catch(() => {});
  }
  let zoom = 1;
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-zoom],[data-hide],[data-fc],[data-fccol]');
    if (!t) return;
    if (t.dataset.zoom !== undefined) {
      const z = +t.dataset.zoom; zoom = z === 0 ? 1 : Math.min(2, Math.max(0.6, zoom + z * 0.2));
      $$('.fcscroll .mermaid').forEach((m) => { m.style.transform = `scale(${zoom})`; });
    } else if (t.hasAttribute('data-hide')) {
      const pane = t.closest('.fcpane'), d = $('[data-details]', pane);
      d.hidden = !d.hidden; t.textContent = d.hidden ? 'Show details' : 'Hide details';
    } else if (t.dataset.fc) {
      $$('.fcpane').forEach((p) => { p.hidden = p.dataset.fcid !== t.dataset.fc; });
    } else if (t.hasAttribute('data-fccol')) {
      const steps = t.closest('.fcitem').nextElementSibling;
      if (steps && steps.matches('[data-steps]')) { steps.hidden = !steps.hidden; t.style.transform = steps.hidden ? 'rotate(-90deg)' : ''; }
    }
  });

  /* ---- requirements: filter by status, highlight a row */
  const reqs = $('[data-reqs]');
  if (reqs) {
    const rows = $$('tbody tr', reqs);
    const filter = (s) => {
      $$('[data-flt]', reqs).forEach((c) => c.classList.toggle('on', c.dataset.flt === s));
      let n = 0;
      rows.forEach((r) => { const ok = s === 'All' || r.dataset.status === s; r.hidden = !ok; if (ok) n++; });
      $('[data-count]', reqs).textContent = `${n} of ${rows.length} requirements`;
    };
    reqs.addEventListener('click', (e) => { const c = e.target.closest('[data-flt]'); if (c) filter(c.dataset.flt); });
    const highlight = () => {
      const st = location.hash.match(/^#status-(.+)$/);
      if (st) { const s = ['All', 'In progress', 'Overdue', 'To do', 'Done'].find((x) => x.toLowerCase().replace(' ', '-') === st[1]); if (s) filter(s); return; }
      const r = location.hash.match(/^#r-(\d+)$/);
      rows.forEach((row) => row.classList.toggle('hl', r && row.id === `r-${r[1]}`));
      if (r) document.getElementById(`r-${r[1]}`)?.scrollIntoView({block: 'center'});
    };
    window.addEventListener('hashchange', highlight); highlight();
  }
})();
