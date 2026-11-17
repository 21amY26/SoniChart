// Renders a simple line or bar chart into an SVG element.
(function (root) {
  const NS = 'http://www.w3.org/2000/svg';
  const M = { top: 20, right: 20, bottom: 40, left: 56 };

  function el(name, attrs, parent) {
    const node = document.createElementNS(NS, name);
    for (const k in attrs) node.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(node);
    return node;
  }

  function niceMax(v) {
    const p = Math.pow(10, Math.floor(Math.log10(v || 1)));
    return Math.ceil(v / p) * p;
  }

  // Returns layout helpers so the cursor can be positioned later.
  function render(svg, ds, type) {
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    const w = svg.clientWidth || 800, h = svg.clientHeight || 340;
    svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
    const iw = w - M.left - M.right, ih = h - M.top - M.bottom;
    const n = ds.data.length;
    const yMax = niceMax(Math.max(...ds.data.map(d => d[1])));
    const step = iw / n;
    const x = i => M.left + step * (i + 0.5);
    const y = v => M.top + ih - (v / yMax) * ih;

    el('line', { class: 'axis', x1: M.left, y1: M.top + ih, x2: M.left + iw, y2: M.top + ih }, svg);
    el('line', { class: 'axis', x1: M.left, y1: M.top, x2: M.left, y2: M.top + ih }, svg);
    for (let t = 0; t <= 4; t++) {
      const v = (yMax / 4) * t;
      el('text', { x: M.left - 8, y: y(v) + 4, 'text-anchor': 'end' }, svg).textContent = Describe.fmt(v);
    }
    ds.data.forEach((d, i) => {
      el('text', { x: x(i), y: M.top + ih + 18, 'text-anchor': 'middle' }, svg).textContent = d[0];
    });

    if (type === 'bar') {
      ds.data.forEach((d, i) => {
        el('rect', { class: 'bar', x: x(i) - step * 0.35, y: y(d[1]), width: step * 0.7, height: M.top + ih - y(d[1]) }, svg);
      });
    } else {
      el('polyline', { class: 'series', points: ds.data.map((d, i) => `${x(i)},${y(d[1])}`).join(' ') }, svg);
      ds.data.forEach((d, i) => el('circle', { class: 'point', cx: x(i), cy: y(d[1]), r: 4 }, svg));
    }
    const cursor = el('circle', { class: 'cursor', r: 10, cx: -100, cy: -100 }, svg);
    return {
      moveCursor(i) {
        cursor.setAttribute('cx', x(i));
        cursor.setAttribute('cy', y(ds.data[i][1]));
      }
    };
  }

  root.Chart = { render };
})(this);
