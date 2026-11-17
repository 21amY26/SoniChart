// User-study helper: presents tasks, times answers and exports a CSV log.
(function (root) {
  // Each task targets one chart-comprehension skill (Brehmer & Munzner task typology).
  const TASKS = [
    { dataset: 'temperature', type: 'line', kind: 'extreme', q: 'In which month is the temperature highest?', answer: 'May' },
    { dataset: 'temperature', type: 'line', kind: 'trend', q: 'Describe the overall trend: increasing, decreasing, or peak then fall?', answer: 'peak' },
    { dataset: 'sales', type: 'bar', kind: 'retrieve', q: 'What were the sales in Q2?', answer: '95' },
    { dataset: 'sales', type: 'bar', kind: 'compare', q: 'Which quarter had lower sales: Q1 or Q3?', answer: 'Q1' },
    { dataset: 'rainfall', type: 'bar', kind: 'extreme', q: 'Which month has the least rainfall?', answer: 'Dec' },
    { dataset: 'stock', type: 'line', kind: 'trend', q: 'Is the share price generally rising or falling?', answer: 'ris' }
  ];

  function score(task, given) {
    return String(given).toLowerCase().includes(task.answer.toLowerCase()) ? 1 : 0;
  }

  function Session() {
    this.log = [];
    this.index = -1;
    this.started = 0;
  }
  Session.prototype.next = function () {
    this.index += 1;
    this.started = Date.now();
    return TASKS[this.index] || null;
  };
  Session.prototype.answer = function (pid, condition, given) {
    const task = TASKS[this.index];
    const row = {
      participant: pid, condition, task: this.index + 1, kind: task.kind,
      question: task.q, answer: given, correct: score(task, given),
      seconds: ((Date.now() - this.started) / 1000).toFixed(1)
    };
    this.log.push(row);
    return row;
  };
  Session.prototype.csv = function () {
    const cols = ['participant', 'condition', 'task', 'kind', 'question', 'answer', 'correct', 'seconds'];
    const q = v => `"${String(v).replace(/"/g, '""')}"`;
    return [cols.join(',')].concat(this.log.map(r => cols.map(c => q(r[c])).join(','))).join('\n');
  };

  const api = { TASKS, score, Session };
  if (typeof module !== 'undefined') module.exports = api; else root.Study = api;
})(this);
