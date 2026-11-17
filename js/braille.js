// Grade-1 (uncontracted) English Braille: converts text to Unicode Braille cells
// and to North American ASCII Braille (used in .brf embosser files).
(function (root) {
  // Dot patterns for a-z; digits reuse a-j after the number sign.
  const LETTER_DOTS = {
    a: [1], b: [1, 2], c: [1, 4], d: [1, 4, 5], e: [1, 5], f: [1, 2, 4], g: [1, 2, 4, 5],
    h: [1, 2, 5], i: [2, 4], j: [2, 4, 5], k: [1, 3], l: [1, 2, 3], m: [1, 3, 4],
    n: [1, 3, 4, 5], o: [1, 3, 5], p: [1, 2, 3, 4], q: [1, 2, 3, 4, 5], r: [1, 2, 3, 5],
    s: [2, 3, 4], t: [2, 3, 4, 5], u: [1, 3, 6], v: [1, 2, 3, 6], w: [2, 4, 5, 6],
    x: [1, 3, 4, 6], y: [1, 3, 4, 5, 6], z: [1, 3, 5, 6]
  };
  const PUNCT_DOTS = { ',': [2], '.': [2, 5, 6], '-': [3, 6], ':': [2, 5], ';': [2, 3] };
  const NUMBER_SIGN = [3, 4, 5, 6];
  const CAPITAL_SIGN = [6];
  const DIGIT_TO_LETTER = '0123456789'.split('').reduce((m, d) => {
    m[d] = 'jabcdefghi'[Number(d)]; return m;
  }, {});
  // ASCII Braille table indexed by Unicode dot-bitmask (0x00–0x3F).
  const ASCII_BRAILLE = ' A1B\'K2L@CIF/MSP"E3H9O6R^DJG>NTQ,*5<-U8V.%[$+X!&;:4\\0Z7(_?W]#Y)=';

  function cell(dots) {
    let mask = 0;
    for (const d of dots) mask |= 1 << (d - 1);
    return mask;
  }

  // Returns an array of 6-dot bitmasks (0 = blank cell).
  function toCells(text) {
    const cells = [];
    let inNumber = false;
    const chars = Array.from(String(text));
    chars.forEach((ch, idx) => {
      if (/[0-9]/.test(ch)) {
        if (!inNumber) { cells.push(cell(NUMBER_SIGN)); inNumber = true; }
        cells.push(cell(LETTER_DOTS[DIGIT_TO_LETTER[ch]]));
        return;
      }
      if (ch === '.' && inNumber && /[0-9]/.test(chars[idx + 1] || '')) { cells.push(cell([4, 6])); return; } // decimal point
      inNumber = false;
      const lower = ch.toLowerCase();
      if (LETTER_DOTS[lower]) {
        if (ch !== lower) cells.push(cell(CAPITAL_SIGN));
        cells.push(cell(LETTER_DOTS[lower]));
      } else if (ch === '%') {
        cells.push(cell([4, 6]), cell([3, 5, 6]));
      } else if (PUNCT_DOTS[ch]) {
        cells.push(cell(PUNCT_DOTS[ch]));
      } else {
        cells.push(0); // space and unsupported characters
      }
    });
    return cells;
  }

  function toUnicode(text) {
    return toCells(text).map(m => String.fromCharCode(0x2800 + m)).join('');
  }

  function toAscii(text) {
    return toCells(text).map(m => ASCII_BRAILLE[m]).join('');
  }

  const api = { toCells, toUnicode, toAscii };
  if (typeof module !== 'undefined') module.exports = api; else root.Braille = api;
})(this);
