# SoniChart — Screen-Reader-Friendly Data Visualisation

SoniChart turns line and bar charts into **sound**, **speech**, **Braille** and **tactile graphics** so that blind and low-vision people can explore data on their own. It also includes a **study mode** for evaluating these modalities with BLV participants.

Human–Computer Interaction course project.

## Features
- **Sonification**: each value maps to a pitch (220–880 Hz, log scale) and its x-position to stereo pan. Clicks mark the highest and lowest points.
- **Keyboard exploration**: arrow keys step through points with a tone and a spoken description (“May: 33.6 °C, up 3.9. Point 5 of 12”) through an ARIA live region.
- **Auto summary and trend**: generated text that names the extremes and the overall shape of the series.
- **Tactile output**: an A4 swell-paper SVG with thick lines, textured bars and Grade-1 Braille labels; a `.brf` Braille file for embossers; vibration patterns on phones.
- **Accessible data table** and support for loading your own CSV.
- **Study mode**: presents tasks, records accuracy and time, and exports a CSV log.

## Keyboard
| Key | Action |
|---|---|
| ← / → | previous / next point |
| Home / End | first / last point |
| Space | play the whole series |
| S / T | speak summary / trend |
| H / L | jump to highest / lowest |
| Esc | stop sound |

## Run
No build step is needed:
```bash
python3 -m http.server 8765
```
Then open http://localhost:8765.

## Tests
```bash
node tests/run.js
```

## Structure
```
index.html        UI
js/braille.js     Grade-1 Braille (Unicode + ASCII/BRF)
js/describe.js    natural-language summaries
js/sonify.js      Web Audio sonification
js/tactile.js     tactile SVG, .brf, vibration
js/study.js       user-study tasks and logging
docs/             study protocol
report/           project report
```

## User study
See [docs/study-protocol.md](docs/study-protocol.md).
