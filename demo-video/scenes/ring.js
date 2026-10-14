// Kader om het uitgelegde element, en een controle dat het kader niets anders raakt.
// Ondertitels staan niet in de pagina maar in een balk onder de video (stitch.py),
// zodat ze nooit een knop, tekst of grafiek afdekken.
({box, kleur, selectors}) => {
  document.querySelectorAll('.__a').forEach(e => e.remove());
  const P = 4, RAND = 3;
  const ring = document.createElement('div');
  ring.className = '__a';
  ring.style.cssText =
    'position:fixed;pointer-events:none;z-index:2147483647;' +
    `left:${box.x - P}px;top:${box.y - P}px;` +
    `width:${box.width + 2 * P}px;height:${box.height + 2 * P}px;` +
    `border:${RAND}px solid ${kleur};border-radius:10px;box-shadow:0 0 12px ${kleur}88;`;
  document.body.appendChild(ring);

  const k = {l: box.x - P - RAND, t: box.y - P - RAND,
             r: box.x + box.width + P + RAND, b: box.y + box.height + P + RAND};
  const binnen = r => r.left >= box.x - 1 && r.right <= box.x + box.width + 1 &&
                      r.top >= box.y - 1 && r.bottom <= box.y + box.height + 1;
  const omvat = r => r.left <= box.x + 1 && r.right >= box.x + box.width - 1 &&
                     r.top <= box.y + 1 && r.bottom >= box.y + box.height - 1;
  const geraakt = [];
  for (const e of document.querySelectorAll(selectors)) {
    const r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2 || r.bottom < 0 || r.top > innerHeight) continue;
    if (binnen(r) || omvat(r)) continue;
    if (r.left < k.r && r.right > k.l && r.top < k.b && r.bottom > k.t) {
      geraakt.push((e.id ? '#' + e.id : e.tagName + '.' + e.className).slice(0, 60));
    }
  }
  return geraakt;
}
