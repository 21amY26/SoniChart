"""Generate the report's diagrams (architecture and sonification mapping) into report/figures/."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams["font.family"] = "Times New Roman"

# ---- architecture
fig, ax = plt.subplots(figsize=(10, 5.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 5.6); ax.axis("off")


def box(x, y, w, h, title, sub, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec="#222", lw=1.2))
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=11.5, weight="bold")
    ax.text(x + w / 2, y + h / 2 - 0.18, sub, ha="center", va="center", fontsize=9.5)


def arrow(x1, y1, x2, y2):
    ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#222"))


box(0.2, 2.2, 2.0, 1.3, "Data input", "sample datasets\nCSV upload\n(data.js)", "#E8EEF8")
box(3.0, 2.2, 2.0, 1.3, "Data model", "label/value series\nstatistics, trend\n(describe.js)", "#E8EEF8")
box(6.0, 4.0, 3.8, 1.3, "Visual + text channel", "SVG chart, data table,\nARIA live region, speech (chart.js, app.js)", "#FFF4D6")
box(6.0, 2.2, 3.8, 1.3, "Auditory channel", "pitch = value, pan = position,\nextreme clicks (sonify.js)", "#E3F4E6")
box(6.0, 0.4, 3.8, 1.3, "Tactile channel", "swell-paper SVG, Braille .brf,\nphone vibration (tactile.js, braille.js)", "#F6E3EC")
box(3.0, 0.4, 2.0, 1.3, "Study mode", "tasks, timing,\naccuracy, CSV log\n(study.js)", "#EEE")
arrow(2.2, 2.85, 3.0, 2.85)
for y in (4.65, 2.85, 1.05):
    arrow(5.0, 2.85, 6.0, y)
arrow(4.0, 2.2, 4.0, 1.7)
ax.text(7.9, 3.75, "keyboard: ← → Home End Space S T H L Esc", ha="center", fontsize=8.5, style="italic")
fig.tight_layout(); fig.savefig(OUT / "architecture.png", dpi=200); plt.close(fig)

# ---- sonification mapping
import numpy as np
v = np.linspace(0, 1, 200)
f = 220 * (880 / 220) ** v
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.6))
a.plot(v, f, lw=2, color="#0050b3"); a.set_xlabel("normalised value"); a.set_ylabel("frequency (Hz)")
a.set_title("Value → pitch (log scale, A3–A5)"); a.grid(alpha=.3)
temp = [15.9, 18.9, 24.4, 29.7, 33.6, 33.4, 30.6, 29.2, 28.9, 26.4, 21.2, 17.0]
lo, hi = min(temp), max(temp)
fr = [220 * 4 ** ((t - lo) / (hi - lo)) for t in temp]
pan = np.linspace(-1, 1, len(temp))
sc = b.scatter(pan, fr, c=temp, cmap="viridis", s=60, zorder=3); b.plot(pan, fr, color="#999", zorder=2)
for p_, f_, m in zip(pan, fr, "JFMAMJJASOND"):
    b.annotate(m, (p_, f_), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
b.set_xlabel("stereo pan (left −1 … right +1)"); b.set_ylabel("frequency (Hz)")
b.set_title("Jaipur temperature as played"); b.grid(alpha=.3)
fig.colorbar(sc, ax=b, label="°C")
fig.tight_layout(); fig.savefig(OUT / "sonification_mapping.png", dpi=200); plt.close(fig)
print("figures written to", OUT)
