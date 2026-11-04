// Kader, pijl en chip bij het uitgelegde element, met controle dat niets wordt geraakt.
// De chip staat in de rechtermarge (de pagina is voor de opname smaller gemaakt);
// kan dat niet zonder een element of de pijl te raken, dan komt hij in een lege band
// onder het blok (een spacer die na de stap weer verdwijnt). Ondertitels staan niet in
// de pagina maar in een balk onder de video (stitch.py).
// Geeft {geraakt: [...], chip: 'marge' | 'onder' | null} terug.
({box, kleur, selectors, pad = 4, rand = 3, label, tekst, last}) => {
  document.querySelectorAll('.__a').forEach(e => e.remove());
  const vw = innerWidth, vh = innerHeight, P = pad, RAND = rand;
  const mk = (css) => {
    const d = document.createElement('div');
    d.className = '__a';
    d.style.cssText = 'position:fixed;pointer-events:none;z-index:2147483647;' + css;
    document.body.appendChild(d);
    return d;
  };
  const c = {l: Math.max(4 + P + RAND, box.x), t: Math.max(4 + P + RAND, box.y),
             r: Math.min(vw - 4 - P - RAND, box.x + box.width),
             b: Math.min(vh - 4 - P - RAND, box.y + box.height)};
  mk(`left:${c.l - P}px;top:${c.t - P}px;width:${c.r - c.l + 2 * P}px;` +
     `height:${c.b - c.t + 2 * P}px;border:${RAND}px solid ${kleur};border-radius:10px;` +
     `box-shadow:0 0 12px ${kleur}88;`);
  const R = {l: c.l - P - RAND, t: c.t - P - RAND, r: c.r + P + RAND, b: c.b + P + RAND};

  const binnen = r => r.left >= box.x - 1 && r.right <= box.x + box.width + 1 &&
                      r.top >= box.y - 1 && r.bottom <= box.y + box.height + 1;
  const omvat = r => r.left <= box.x + 1 && r.right >= box.x + box.width - 1 &&
                     r.top <= box.y + 1 && r.bottom >= box.y + box.height - 1;
  const lijst = () => [...document.querySelectorAll(selectors)]
    .filter(e => !e.closest('.__a'))
    .map(e => ({e, r: e.getBoundingClientRect()}))
    .filter(({r}) => r.width >= 2 && r.height >= 2 && r.bottom > 0 && r.top < vh)
    .filter(({r}) => !(binnen(r) || omvat(r)));
  const beschrijf = ({e, r}) => (e.id ? '#' + e.id : e.tagName + '.' + e.className).slice(0, 40) +
    ' "' + (e.innerText || '').slice(0, 30) + '" ' + Math.round(r.top) + '-' + Math.round(r.bottom);
  const raakt = (a, r) => r.left < a.r && r.right > a.l && r.top < a.b && r.bottom > a.t;

  const geraakt = lijst().filter(({r}) => raakt(R, r)).map(beschrijf);
  if (!label) return {geraakt, chip: null};

  const CW = 256;
  const chip = mk(`width:${CW}px;font-family:Inter,system-ui,sans-serif;` +
                  'filter:drop-shadow(0 6px 14px rgba(0,0,0,.25));');
  chip.innerHTML =
    `<div style="background:${kleur};color:#fff;font:700 14px/1.3 Inter,system-ui,sans-serif;` +
    `padding:6px 12px;border-radius:8px 8px 0 0">${label}</div>` +
    `<div style="background:#fff;color:#0f172a;font:500 13px/1.4 Inter,system-ui,sans-serif;` +
    `padding:8px 12px;border:1px solid ${kleur};border-top:0;border-radius:0 0 8px 8px">${tekst}</div>`;
  const CH = chip.getBoundingClientRect().height;
  const klem = (v, a, b) => Math.max(a, Math.min(b, v));

  const pijl = (x1, y1, x2, y2) => {
    const svg = mk(`left:0;top:0;width:${vw}px;height:${vh}px;`);
    const bx = (x1 + x2) / 2, by = (y1 + y2) / 2 + (x1 === x2 ? 0 : -14);
    svg.innerHTML = `<svg width="${vw}" height="${vh}"><defs>` +
      `<marker id="__h" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">` +
      `<path d="M0,0 L10,5 L0,10 z" fill="${kleur}"/></marker></defs>` +
      `<path d="M ${x1} ${y1} Q ${bx} ${by} ${x2} ${y2}" stroke="${kleur}" stroke-width="3" ` +
      `fill="none" marker-end="url(#__h)"/></svg>`;
  };
  const kruist = (x1, x2, y, els) => els.filter(({r}) =>
    r.left < x2 && r.right > x1 && r.top < y + 4 && r.bottom > y - 4);

  // 1. rechtermarge
  const cy0 = klem((R.t + R.b) / 2, 64 + CH / 2, vh - 12 - CH / 2);
  const cTop = cy0 - CH / 2;
  let els = lijst();
  let gx = R.r + 24;
  for (const {r} of els) if (r.top < cTop + CH && r.bottom > cTop) gx = Math.max(gx, r.right + 24);
  const ay = klem(cy0, R.t + 14, R.b - 14);
  const chipRect = {l: gx, t: cTop, r: gx + CW, b: cTop + CH};
  const past = gx + CW <= vw - 12 &&
    !els.some(({r}) => raakt(chipRect, r)) && kruist(R.r, gx, ay, els).length === 0;
  if (past) {
    chip.style.left = gx + 'px';
    chip.style.top = cTop + 'px';
    pijl(gx, cTop + CH / 2, R.r, ay);
    return {geraakt, chip: 'marge'};
  }

  // 2. lege band onder het blok
  const top = (el) => {
    let e = el;
    while (e.parentElement && !(e.parentElement.getAttribute('data-testid') === 'stVerticalBlock' &&
           e.parentElement.parentElement &&
           e.parentElement.parentElement.getAttribute('data-testid') === 'stMainBlockContainer'))
      e = e.parentElement;
    return e;
  };
  const blok = top(last);
  const spacer = document.createElement('div');
  spacer.className = '__a';
  spacer.style.cssText = `height:${Math.ceil(CH + 60)}px;pointer-events:none;`;
  blok.after(spacer);
  const cx = klem(R.l, 36, vw - CW - 36), cyy = R.b + 30;
  if (cyy + CH > vh - 12) {
    geraakt.push('chip past niet in beeld onder het blok (marge: gx=' + Math.round(gx) + ', ring ' + Math.round(R.t) + '-' + Math.round(R.b) + ', kruist ' + kruist(R.r, gx, ay, els).map(beschrijf).join('|') + ')');
    return {geraakt, chip: null};
  }
  chip.style.left = cx + 'px';
  chip.style.top = cyy + 'px';
  const rect2 = {l: cx, t: cyy, r: cx + CW, b: cyy + CH};
  for (const x of lijst()) if (raakt(rect2, x.r)) geraakt.push('chip raakt ' + beschrijf(x));
  const px = klem((R.l + R.r) / 2, cx + 24, cx + CW - 24);
  pijl(px, cyy, klem(px, R.l + 14, R.r - 14), R.b);
  return {geraakt, chip: 'onder'};
}
