// Tactile output: swell-paper SVG with Braille labels, .brf summaries and
// vibration patterns for phones.
(function (root) {
  const isNode = typeof module !== 'undefined';
  const Braille = isNode ? require('./braille.js') : root.Braille;
  const Describe = isNode ? require('./describe.js') : root.Describe;

  // A4 landscape in mm. Tactile guidelines (BANA 2010) recommend line widths
  // of at least 1 mm, distinct textures and Braille labels instead of print.
  const W = 297, H = 210, M = { top: 25, right: 15, bottom: 35, left: 30 };

  function esc(s) {
    return String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  }

  function svg(ds, type) {
    const n = ds.data.length;
    const vals = ds.data.map(d => d[1]);
    const yMax = Math.max(...vals);
    const iw = W - M.left - M.right, ih = H - M.top - M.bottom;
    const step = iw / n;
    const x = i => M.left + step * (i + 0.5);
    const y = v => M.top + ih - (v / yMax) * ih;
    const br = s => esc(Braille.toUnicode(s));
    const out = [];
    out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${W}mm" height="${H}mm" viewBox="0 0 ${W} ${H}">`);
    out.push('<defs><pattern id="dots" width="3" height="3" patternUnits="userSpaceOnUse">' +
      '<circle cx="1.5" cy="1.5" r="0.7" fill="#000"/></pattern></defs>');
    out.push('<rect width="100%" height="100%" fill="#fff"/>');
    out.push(`<text x="${M.left}" y="12" font-size="7" font-family="sans-serif">${br(ds.title)}</text>`);
    // Axes: thick solid lines.
    out.push(`<line x1="${M.left}" y1="${M.top + ih}" x2="${M.left + iw}" y2="${M.top + ih}" stroke="#000" stroke-width="1.2"/>`);
    out.push(`<line x1="${M.left}" y1="${M.top}" x2="${M.left}" y2="${M.top + ih}" stroke="#000" stroke-width="1.2"/>`);
    // Max tick label in Braille only; fewer labels keep the graphic readable by touch.
    out.push(`<text x="${M.left - 3}" y="${M.top + 2}" font-size="6" text-anchor="end">${br(Describe.fmt(yMax))}</text>`);
    out.push(`<text x="${M.left - 3}" y="${M.top + ih + 2}" font-size="6" text-anchor="end">${br('0')}</text>`);
    if (type === 'bar') {
      ds.data.forEach((d, i) => {
        out.push(`<rect x="${x(i) - step * 0.3}" y="${y(d[1])}" width="${step * 0.6}" height="${M.top + ih - y(d[1])}" fill="url(#dots)" stroke="#000" stroke-width="1"/>`);
      });
    } else {
      out.push(`<polyline fill="none" stroke="#000" stroke-width="1.5" points="${ds.data.map((d, i) => `${x(i)},${y(d[1])}`).join(' ')}"/>`);
      ds.data.forEach((d, i) => out.push(`<circle cx="${x(i)}" cy="${y(d[1])}" r="1.6" fill="#000"/>`));
    }
    // x labels: abbreviate to 3 chars and alternate rows to avoid Braille overlap.
    ds.data.forEach((d, i) => {
      const row = n > 8 && i % 2 ? 14 : 7;
      out.push(`<text x="${x(i)}" y="${M.top + ih + row}" font-size="6" text-anchor="middle">${br(String(d[0]).slice(0, 3))}</text>`);
    });
    out.push('</svg>');
    return out.join('\n');
  }

  // .brf: 40 cells per line, 25 lines per page, ASCII Braille.
  function brf(ds, type) {
    const lines = [Describe.summary(ds, type), ''];
    ds.data.forEach(d => lines.push(`${d[0]}: ${Describe.fmt(d[1])}`));
    const out = [];
    for (const line of lines) {
      // Wrap at word boundaries; words longer than a line are split.
      let current = '';
      for (const word of line.split(' ').map(w => Braille.toAscii(w))) {
        if (current && current.length + 1 + word.length > 40) { out.push(current); current = ''; }
        let w = word;
        while (w.length > 40) { out.push(w.slice(0, 40)); w = w.slice(40); }
        current = current ? `${current} ${w}` : w;
      }
      out.push(current);
    }
    const pages = [];
    for (let i = 0; i < out.length; i += 25) pages.push(out.slice(i, i + 25).join('\r\n'));
    return pages.join('\r\n\f');
  }

  // Each value becomes a pulse whose length (60–400 ms) encodes its magnitude.
  function vibrationPattern(data) {
    const vals = data.map(d => d[1]);
    const min = Math.min(...vals), max = Math.max(...vals);
    const pattern = [];
    vals.forEach(v => {
      const t = max === min ? 0.5 : (v - min) / (max - min);
      pattern.push(Math.round(60 + t * 340), 150);
    });
    return pattern;
  }

  const api = { svg, brf, vibrationPattern };
  if (isNode) module.exports = api; else root.Tactile = api;
})(this);
