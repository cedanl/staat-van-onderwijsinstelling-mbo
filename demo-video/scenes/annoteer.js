({box, label, tekst, kleur, sub, selectors}) => {
  document.querySelectorAll('.__a').forEach(e => e.remove());
  const vw = innerWidth, vh = innerHeight, M = 9;
  const mk = (css, cls) => { const d = document.createElement('div'); d.className = '__a ' + (cls||'');
    d.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;' + css;
    document.body.appendChild(d); return d; };
  const rect = e => { const r = e.getBoundingClientRect(); return {l:r.left,t:r.top,r:r.right,b:r.bottom}; };
  const clip = b => ({l:Math.max(4,b.x), t:Math.max(4,b.y), r:Math.min(vw-4,b.x+b.width), b:Math.min(vh-4,b.y+b.height)});
  const c = clip(box);
  const ring = mk(`left:${c.l-M}px;top:${c.t-M}px;width:${c.r-c.l+2*M}px;height:${c.b-c.t+2*M}px;` +
    `border:3px solid ${kleur};border-radius:12px;box-shadow:0 0 0 3px ${kleur}33,0 0 18px ${kleur}66;`);
  const R = rect(ring);
  let chip = null, CR = null, side = null, arrow = null;
  if (label) {
    chip = mk(`width:290px;font-family:Inter,system-ui,sans-serif;filter:drop-shadow(0 6px 14px rgba(0,0,0,.25));`);
    chip.innerHTML = `<div style="background:${kleur};color:#fff;font:700 14px/1.3 inherit;padding:6px 12px;border-radius:8px 8px 0 0">${label}</div>` +
      `<div style="background:#fff;color:#0f172a;font:500 13px/1.4 inherit;padding:8px 12px;border:1px solid ${kleur};border-top:0;border-radius:0 0 8px 8px">${tekst}</div>`;
    const cw = 290, ch = chip.getBoundingClientRect().height;
    const cx = Math.max(36, Math.min(vw - cw - 36, R.l));
    const cy = (R.t + R.b) / 2 - ch / 2;
    const kand = {
      above: [cx, R.t - ch - 28], below: [cx, R.b + 28],
      right: [R.r + 28, cy], left: [R.l - cw - 28, cy]
    };
    const els = [...document.querySelectorAll(selectors)].map(rect)
      .filter(r => r.r - r.l > 4 && r.b - r.t > 4 && r.b > 0 && r.t < vh)
      .filter(r => !(r.l >= R.l - 2 && r.r <= R.r + 2 && r.t >= R.t - 2 && r.b <= R.b + 2));
    const ov = (a, b) => Math.max(0, Math.min(a.r, b.r) - Math.max(a.l, b.l)) * Math.max(0, Math.min(a.b, b.b) - Math.max(a.t, b.t));
    const score = ([x, y]) => {
      if (x < 12 || y < 12 || x + cw > vw - 12 || y + ch > vh - 12) return 1e12;
      const r = {l:x, t:y, r:x+cw, b:y+ch};
      return els.reduce((s, e) => s + ov(r, e), 0) + ov(r, R) * 10;
    };
    side = Object.keys(kand).sort((a, b) => score(kand[a]) - score(kand[b]))[0];
    chip.style.left = kand[side][0] + 'px'; chip.style.top = kand[side][1] + 'px';
    CR = rect(chip);
    // pijl: kwadratische Bezier van chip naar de ringrand, buiging afhankelijk van afstand
    const ccx = (CR.l + CR.r) / 2, ccy = (CR.t + CR.b) / 2;
    const sx = side === 'right' ? CR.l : side === 'left' ? CR.r : Math.max(CR.l + 24, Math.min(CR.r - 24, (R.l + R.r) / 2));
    const sy = side === 'above' ? CR.b : side === 'below' ? CR.t : ccy;
    const ex = Math.max(R.l + 14, Math.min(R.r - 14, sx)), ey = side === 'above' ? R.t : side === 'below' ? R.b : ccy;
    const ex2 = side === 'right' ? R.r : side === 'left' ? R.l : ex;
    const dx = ex2 - sx, dy = ey - sy, bend = Math.max(-70, Math.min(70, dx * 0.28 || dy * 0.28));
    const qx = (sx + ex2) / 2 + (side === 'above' || side === 'below' ? bend : 0);
    const qy = (sy + ey) / 2 + (side === 'left' || side === 'right' ? bend : 0);
    const svg = mk(`left:0;top:0;width:${vw}px;height:${vh}px;`);
    svg.innerHTML = `<svg width="${vw}" height="${vh}"><defs><marker id="__h" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">` +
      `<path d="M0,0 L10,5 L0,10 z" fill="${kleur}"/></marker></defs>` +
      `<path d="M ${sx} ${sy} Q ${qx} ${qy} ${ex2} ${ey}" stroke="${kleur}" stroke-width="3" fill="none" marker-end="url(#__h)"/></svg>`;
  }
  // ondertitel: kies uit midden/links/rechts en alle hoogtes de plek met minste overlap
  const s = mk('background:rgba(15,23,42,.92);color:#fff;padding:14px 26px;border-radius:12px;' +
    'border-left:6px solid ' + kleur + ';font:600 21px/1.35 Inter,system-ui,sans-serif;' +
    'box-shadow:0 8px 30px rgba(0,0,0,.25);');
  s.textContent = sub;
  const all = [...document.querySelectorAll(selectors)].map(rect)
    .filter(r => r.r - r.l > 4 && r.b - r.t > 4 && r.b > 0 && r.t < vh);
  const extra = [R].concat(CR ? [CR] : []);
  const modes = {
    center: {maxw: 900, x: null},
    left: {maxw: 420, x: 24},
    right: {maxw: 420, x: vw - 24 - 420},
  };
  let bestAll = null;
  for (const [mode, m] of Object.entries(modes)) {
    s.style.maxWidth = m.maxw + 'px';
    s.style.transform = m.x === null ? 'translateX(-50%)' : 'none';
    s.style.left = m.x === null ? '50%' : m.x + 'px';
    s.style.right = 'auto';
    const sr = s.getBoundingClientRect(), sh = sr.height, sw = sr.width;
    const x0 = m.x === null ? (vw - sw) / 2 : m.x, x1 = x0 + sw;
    const ov2 = (t, a) => Math.max(0, Math.min(a.r, x1) - Math.max(a.l, x0)) * Math.max(0, Math.min(a.b, t + sh) - Math.max(a.t, t));
    const scoreY = t => all.reduce((a, e) => a + ov2(t, e), 0) + extra.reduce((a, e) => a + ov2(t, e) * 50, 0);
    for (let y = vh - sh - 24; y >= 48; y -= 12) {
      if (y < vh * 0.5 && y > vh * 0.2) continue;   // alleen onder- of bovenband
      const sc0 = scoreY(y) + (mode === 'center' ? 0 : 1);   // midden/onder bij gelijkspel
      if (!bestAll || sc0 < bestAll.sc) bestAll = {sc: sc0, mode, y, m};
    }
  }
  s.style.maxWidth = bestAll.m.maxw + 'px';
  s.style.transform = bestAll.m.x === null ? 'translateX(-50%)' : 'none';
  s.style.left = bestAll.m.x === null ? '50%' : bestAll.m.x + 'px';
  s.style.top = bestAll.y + 'px';
  const best = bestAll.mode + '@' + Math.round(bestAll.y);
  const sc = {best: Math.floor(bestAll.sc)};
  return {chip: side, sub: best, scores: sc};
}
