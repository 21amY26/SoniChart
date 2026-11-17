# User Study Protocol — SoniChart

## Research questions
- **RQ1** Do sonification + speech and tactile graphics let blind and low-vision (BLV) users answer chart questions more accurately than a data table alone?
- **RQ2** How do the three conditions compare in task time and perceived workload?
- **RQ3** Which modality do participants prefer for which task type (retrieve, compare, extreme, trend)?

## Participants
- 8–12 adults who are blind or have low vision and use a screen reader (NVDA, JAWS, VoiceOver or TalkBack).
- Recruit through local blind associations or university disability support offices. Participation is voluntary and you need informed consent (an accessible consent form read aloud or sent as a document a screen reader can read). Pay or thank participants as your institution's ethics rules allow.
- Record: age range, vision status (self-reported), screen reader, Braille literacy and how often they use charts.

## Design
Within-subjects, 3 conditions:
1. **Table** — the accessible data table only (baseline).
2. **Sonify** — keyboard exploration with tones, spoken point descriptions and summary.
3. **Tactile** — swell-paper print of the tactile SVG (with the Braille `.brf` summary for Braille readers).

Counterbalance the condition order with a Latin square. Each condition uses the six tasks in study mode. Use different but equivalent datasets per condition, or shuffle the task order, to reduce learning effects.

## Procedure (≈ 45 min)
1. Consent and demographics (5 min).
2. Training on each condition with a practice chart (5 min each).
3. Tasks: in study mode the researcher clicks **Start next task**, reads the question aloud, the participant answers verbally, and the researcher types the answer and clicks **Submit**. The time recorded runs from when the question is shown to when the answer is submitted.
4. After each condition: NASA-TLX (raw) and SUS questionnaires, asked verbally.
5. Semi-structured interview (10 min): what was easy or hard, which modality they would use for which purpose, and suggestions.

## Measures
| Measure | Source |
|---|---|
| Accuracy (0/1 per task) | study log CSV |
| Task time (s) | study log CSV |
| Workload | NASA-TLX raw, 0–100 |
| Usability | SUS, 0–100 |
| Preference and comments | interview, thematic analysis |

## Analysis
- Accuracy: Cochran's Q across conditions, with pairwise McNemar tests and Bonferroni correction.
- Time, TLX and SUS: Friedman test, with pairwise Wilcoxon signed-rank tests.
- Interviews: inductive thematic analysis (Braun & Clarke).

## Ethics
- Get ethics approval from the institution before you recruit.
- Store data under participant IDs only. Do not record faces, and get consent before recording audio.
- Participants may stop at any time without giving a reason.
