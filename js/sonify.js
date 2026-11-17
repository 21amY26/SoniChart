// Sonification: maps data values to pitch and x-position to stereo pan.
(function (root) {
  const MIN_HZ = 220, MAX_HZ = 880; // two octaves, A3–A5

  // Logarithmic mapping so equal value steps sound like equal pitch steps.
  function valueToFreq(v, min, max) {
    const t = max === min ? 0.5 : (v - min) / (max - min);
    return MIN_HZ * Math.pow(MAX_HZ / MIN_HZ, t);
  }

  function indexToPan(i, n) {
    return n <= 1 ? 0 : -1 + (2 * i) / (n - 1);
  }

  let ctx = null;
  let timers = [];
  let active = [];

  function audio() {
    if (!ctx) ctx = new (root.AudioContext || root.webkitAudioContext)();
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  function tone(freq, pan, duration, when) {
    const a = audio();
    const t0 = a.currentTime + (when || 0);
    const osc = a.createOscillator();
    const gain = a.createGain();
    const panner = a.createStereoPanner ? a.createStereoPanner() : null;
    osc.type = 'triangle';
    osc.frequency.value = freq;
    gain.gain.setValueAtTime(0, t0);
    gain.gain.linearRampToValueAtTime(0.3, t0 + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.001, t0 + duration);
    osc.connect(gain);
    if (panner) { panner.pan.value = pan; gain.connect(panner).connect(a.destination); }
    else gain.connect(a.destination);
    osc.start(t0);
    osc.stop(t0 + duration + 0.05);
    active.push(osc);
  }

  // A short click marks the highest and lowest points during playback.
  function tick(when) {
    const a = audio();
    const t0 = a.currentTime + when;
    const osc = a.createOscillator();
    const gain = a.createGain();
    osc.type = 'square';
    osc.frequency.value = 1800;
    gain.gain.setValueAtTime(0.08, t0);
    gain.gain.exponentialRampToValueAtTime(0.001, t0 + 0.04);
    osc.connect(gain).connect(a.destination);
    osc.start(t0); osc.stop(t0 + 0.05);
    active.push(osc);
  }

  function playPoint(data, i) {
    const vals = data.map(d => d[1]);
    tone(valueToFreq(vals[i], Math.min(...vals), Math.max(...vals)), indexToPan(i, data.length), 0.25);
  }

  function playSeries(data, msPerPoint, onPoint) {
    stop();
    const vals = data.map(d => d[1]);
    const min = Math.min(...vals), max = Math.max(...vals);
    const sec = msPerPoint / 1000;
    vals.forEach((v, i) => {
      tone(valueToFreq(v, min, max), indexToPan(i, vals.length), sec * 0.9, i * sec);
      if (v === min || v === max) tick(i * sec);
      timers.push(setTimeout(() => onPoint && onPoint(i), i * msPerPoint));
    });
  }

  function stop() {
    timers.forEach(clearTimeout);
    timers = [];
    active.forEach(o => { try { o.stop(); } catch (e) { /* already stopped */ } });
    active = [];
  }

  const api = { valueToFreq, indexToPan, playPoint, playSeries, stop, MIN_HZ, MAX_HZ };
  if (typeof module !== 'undefined') module.exports = api; else root.Sonify = api;
})(typeof window !== 'undefined' ? window : this);
