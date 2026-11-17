// Generates natural-language descriptions of a series for speech and Braille.
(function (root) {
  function fmt(n) {
    return Number.isInteger(n) ? String(n) : n.toFixed(1);
  }

  function stats(data) {
    const values = data.map(d => d[1]);
    let maxI = 0, minI = 0;
    values.forEach((v, i) => {
      if (v > values[maxI]) maxI = i;
      if (v < values[minI]) minI = i;
    });
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    return { values, maxI, minI, mean, first: values[0], last: values[values.length - 1] };
  }

  // Classifies the overall shape using the position of the extremes.
  function trend(data) {
    const s = stats(data);
    const n = data.length;
    const range = s.values[s.maxI] - s.values[s.minI] || 1;
    const change = (s.last - s.first) / range;
    const interior = i => i > 0 && i < n - 1;
    if (interior(s.maxI) && Math.abs(change) < 0.5) return 'rises to a peak and then falls';
    if (interior(s.minI) && Math.abs(change) < 0.5) return 'falls to a low point and then rises';
    if (change > 0.25) return 'generally increases';
    if (change < -0.25) return 'generally decreases';
    return 'stays roughly level';
  }

  function summary(ds, type) {
    const s = stats(ds.data);
    const n = ds.data.length;
    return `${type === 'bar' ? 'Bar' : 'Line'} chart: ${ds.title}, ${n} points from ` +
      `${ds.data[0][0]} to ${ds.data[n - 1][0]}. Highest ${fmt(s.values[s.maxI])} ${ds.unit} ` +
      `at ${ds.data[s.maxI][0]}; lowest ${fmt(s.values[s.minI])} ${ds.unit} at ` +
      `${ds.data[s.minI][0]}. The series ${trend(ds.data)}.`;
  }

  function point(ds, i) {
    const [label, value] = ds.data[i];
    const prev = i > 0 ? ds.data[i - 1][1] : null;
    let delta = '';
    if (prev !== null) {
      const d = value - prev;
      delta = d === 0 ? ', unchanged' : `, ${d > 0 ? 'up' : 'down'} ${fmt(Math.abs(d))}`;
    }
    return `${label}: ${fmt(value)} ${ds.unit}${delta}. Point ${i + 1} of ${ds.data.length}.`;
  }

  const api = { stats, trend, summary, point, fmt };
  if (typeof module !== 'undefined') module.exports = api; else root.Describe = api;
})(this);
