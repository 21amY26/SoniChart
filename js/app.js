// Wires the UI together: dataset selection, keyboard navigation, speech,
// sonification, tactile export and study mode.
(function () {
  const $ = id => document.getElementById(id);
  const state = { ds: null, type: 'line', i: 0, view: null };
  const session = new Study.Session();

  function announce(text, speak) {
    $('live').textContent = text;
    // Screen-reader users hear the live region; speech synthesis is for users without one.
    if (speak && 'speechSynthesis' in window) {
      speechSynthesis.cancel();
      speechSynthesis.speak(new SpeechSynthesisUtterance(text));
    }
  }

  function download(name, content, mime) {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([content], { type: mime }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  function load(ds) {
    state.ds = ds;
    state.i = 0;
    state.view = Chart.render($('chart'), ds, state.type);
    $('chart-summary').textContent = Describe.summary(ds, state.type);
    const tbody = $('data-table').querySelector('tbody');
    tbody.innerHTML = '';
    ds.data.forEach(([label, value]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td></td><td></td>`;
      tr.children[0].textContent = label;
      tr.children[1].textContent = `${Describe.fmt(value)} ${ds.unit}`;
      tbody.appendChild(tr);
    });
    $('data-table').querySelector('caption').textContent = ds.title;
  }

  function focusPoint(i) {
    const n = state.ds.data.length;
    state.i = Math.max(0, Math.min(n - 1, i));
    state.view.moveCursor(state.i);
    Sonify.playPoint(state.ds.data, state.i);
    announce(Describe.point(state.ds, state.i));
  }

  function playAll() {
    Sonify.playSeries(state.ds.data, Number($('speed').value), i => {
      state.i = i;
      state.view.moveCursor(i);
    });
    announce('Playing. Low pitch is a low value, high pitch a high value; sound moves left to right.');
  }

  // Populate datasets.
  for (const key in SoniData.DATASETS) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = SoniData.DATASETS[key].title;
    $('dataset').appendChild(opt);
  }
  $('dataset').addEventListener('change', e => load(SoniData.DATASETS[e.target.value]));
  $('chart-type').addEventListener('change', e => { state.type = e.target.value; load(state.ds); });
  $('csv-file').addEventListener('change', async e => {
    const file = e.target.files[0];
    if (!file) return;
    const data = SoniData.parseCsv(await file.text());
    if (data.length < 2) { announce('Could not read at least two rows of label,value data.'); return; }
    load({ title: file.name.replace(/\.csv$/i, ''), unit: '', data });
    announce(`Loaded ${data.length} rows from ${file.name}.`);
  });

  $('chart-region').addEventListener('keydown', e => {
    const n = state.ds.data.length;
    const s = Describe.stats(state.ds.data);
    const actions = {
      ArrowRight: () => focusPoint(state.i + 1),
      ArrowLeft: () => focusPoint(state.i - 1),
      Home: () => focusPoint(0),
      End: () => focusPoint(n - 1),
      ' ': playAll,
      Escape: () => { Sonify.stop(); announce('Stopped.'); },
      s: () => announce(Describe.summary(state.ds, state.type), true),
      t: () => announce(`The series ${Describe.trend(state.ds.data)}.`, true),
      h: () => focusPoint(s.maxI),
      l: () => focusPoint(s.minI)
    };
    const fn = actions[e.key.length === 1 ? e.key.toLowerCase() : e.key];
    if (fn) { e.preventDefault(); fn(); }
  });

  $('play-btn').addEventListener('click', playAll);
  $('stop-btn').addEventListener('click', () => Sonify.stop());
  $('speed').addEventListener('input', e => e.target.setAttribute('aria-valuetext', `${e.target.value} milliseconds per point`));
  $('tactile-svg-btn').addEventListener('click', () =>
    download(`${state.ds.title}-tactile.svg`, Tactile.svg(state.ds, state.type), 'image/svg+xml'));
  $('brf-btn').addEventListener('click', () =>
    download(`${state.ds.title}.brf`, Tactile.brf(state.ds, state.type), 'text/plain'));
  $('vibrate-btn').addEventListener('click', () => {
    if (navigator.vibrate) { navigator.vibrate(Tactile.vibrationPattern(state.ds.data)); announce('Vibrating: longer pulses mean higher values.'); }
    else announce('Vibration is not supported on this device.');
  });

  // Study mode.
  $('study-start').addEventListener('click', () => {
    const task = session.next();
    if (!task) { $('study-task').textContent = 'All tasks complete. Export the log.'; $('answer-row').hidden = true; return; }
    $('dataset').value = task.dataset;
    $('chart-type').value = state.type = task.type;
    load(SoniData.DATASETS[task.dataset]);
    $('study-task').textContent = `Task ${session.index + 1} of ${Study.TASKS.length}: ${task.q}`;
    $('answer-row').hidden = false;
    $('answer').value = '';
  });
  $('answer-submit').addEventListener('click', () => {
    const row = session.answer($('pid').value, $('condition').value, $('answer').value);
    $('answer-row').hidden = true;
    $('study-count').textContent = `${session.log.length} answers recorded (last took ${row.seconds} s).`;
  });
  $('study-export').addEventListener('click', () =>
    download(`study-${$('pid').value}.csv`, session.csv(), 'text/csv'));

  load(SoniData.DATASETS.temperature);
  window.addEventListener('resize', () => load(state.ds));
})();
