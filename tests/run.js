// Unit tests for the non-DOM modules. Run with: node tests/run.js
const assert = require('assert');
const Braille = require('../js/braille.js');
const Describe = require('../js/describe.js');
const Sonify = require('../js/sonify.js');
const Tactile = require('../js/tactile.js');
const Study = require('../js/study.js');
const { DATASETS, parseCsv } = require('../js/data.js');

let passed = 0;
function test(name, fn) {
  try { fn(); passed++; console.log(`ok   ${name}`); }
  catch (e) { console.error(`FAIL ${name}\n     ${e.message}`); process.exitCode = 1; }
}

test('braille letters', () => assert.strictEqual(Braille.toUnicode('abc'), '⠁⠃⠉'));
test('braille capital sign', () => assert.strictEqual(Braille.toUnicode('Jan'), '⠠⠚⠁⠝'));
test('braille numbers use number sign', () => assert.strictEqual(Braille.toUnicode('25'), '⠼⠃⠑'));
test('braille decimal vs full stop', () => {
  assert.strictEqual(Braille.toAscii('2.5'), '#B.E');
  assert.strictEqual(Braille.toAscii('q4.'), 'Q#D4');
});
test('braille ascii for brf', () => assert.strictEqual(Braille.toAscii('may 33'), 'MAY #CC'));

test('pitch is monotonic and bounded', () => {
  assert.strictEqual(Math.round(Sonify.valueToFreq(0, 0, 10)), Sonify.MIN_HZ);
  assert.strictEqual(Math.round(Sonify.valueToFreq(10, 0, 10)), Sonify.MAX_HZ);
  assert.ok(Sonify.valueToFreq(4, 0, 10) < Sonify.valueToFreq(6, 0, 10));
});
test('pan spans left to right', () => {
  assert.strictEqual(Sonify.indexToPan(0, 5), -1);
  assert.strictEqual(Sonify.indexToPan(4, 5), 1);
});

test('trend: temperature peaks then falls', () =>
  assert.strictEqual(Describe.trend(DATASETS.temperature.data), 'rises to a peak and then falls'));
test('trend: stock increases', () =>
  assert.strictEqual(Describe.trend(DATASETS.stock.data), 'generally increases'));
test('summary names extremes', () => {
  const s = Describe.summary(DATASETS.sales, 'bar');
  assert.ok(s.includes('Highest 180') && s.includes('Q4') && s.includes('lowest 95'));
});
test('point description includes delta', () =>
  assert.ok(Describe.point(DATASETS.sales, 1).includes('down 25')));

test('tactile svg is A4 with braille labels', () => {
  const svg = Tactile.svg(DATASETS.sales, 'bar');
  assert.ok(svg.includes('width="297mm"'));
  assert.ok(svg.includes('⠠⠟⠼⠁'));
});
test('brf lines are at most 40 cells', () => {
  const brf = Tactile.brf(DATASETS.temperature, 'line');
  brf.split(/\r\n|\f/).forEach(l => assert.ok(l.length <= 40, l));
});
test('vibration pattern length', () =>
  assert.strictEqual(Tactile.vibrationPattern(DATASETS.sales.data).length, 8));

test('csv parsing skips header', () =>
  assert.deepStrictEqual(parseCsv('label,value\na,1\nb,2.5'), [['a', 1], ['b', 2.5]]));
test('study answers match sample data', () => {
  for (const t of Study.TASKS) {
    if (t.kind !== 'extreme' && t.kind !== 'retrieve' && t.kind !== 'compare') continue;
    const d = DATASETS[t.dataset].data;
    const s = Describe.stats(d);
    if (t.kind === 'extreme') assert.ok([d[s.maxI][0], d[s.minI][0]].includes(t.answer), t.q);
  }
  assert.strictEqual(Study.score(Study.TASKS[0], 'may'), 1);
  assert.strictEqual(Study.score(Study.TASKS[0], 'June'), 0);
});

console.log(`\n${passed} tests passed`);
