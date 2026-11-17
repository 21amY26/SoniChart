// Sample datasets used in the demo and in the user study tasks.
(function (root) {
  const DATASETS = {
    temperature: {
      title: 'Average monthly temperature in Jaipur',
      unit: '°C',
      data: [
        ['Jan', 15.9], ['Feb', 18.9], ['Mar', 24.4], ['Apr', 29.7], ['May', 33.6], ['Jun', 33.4],
        ['Jul', 30.6], ['Aug', 29.2], ['Sep', 28.9], ['Oct', 26.4], ['Nov', 21.2], ['Dec', 17.0]
      ]
    },
    sales: {
      title: 'Quarterly sales of a small shop',
      unit: 'thousand rupees',
      data: [['Q1', 120], ['Q2', 95], ['Q3', 140], ['Q4', 180]]
    },
    rainfall: {
      title: 'Monthly rainfall in Jaipur',
      unit: 'mm',
      data: [
        ['Jan', 8], ['Feb', 9], ['Mar', 5], ['Apr', 5], ['May', 15], ['Jun', 60],
        ['Jul', 195], ['Aug', 190], ['Sep', 75], ['Oct', 15], ['Nov', 4], ['Dec', 3]
      ]
    },
    stock: {
      title: 'Share price over ten trading days',
      unit: 'rupees',
      data: [
        ['Day 1', 410], ['Day 2', 418], ['Day 3', 405], ['Day 4', 399], ['Day 5', 425],
        ['Day 6', 440], ['Day 7', 436], ['Day 8', 452], ['Day 9', 447], ['Day 10', 460]
      ]
    }
  };

  // Parses "label,value" lines; skips a header row if its value is not numeric.
  function parseCsv(text) {
    const rows = [];
    for (const line of text.split(/\r?\n/)) {
      const parts = line.split(',');
      if (parts.length < 2) continue;
      const value = parseFloat(parts[1]);
      if (Number.isNaN(value)) continue;
      rows.push([parts[0].trim(), value]);
    }
    return rows;
  }

  const api = { DATASETS, parseCsv };
  if (typeof module !== 'undefined') module.exports = api; else root.SoniData = api;
})(this);
