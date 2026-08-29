"""Figure 1 for the paper: structural signal and bigram coverage as a function
of catalogue size under four merge rules, with the syllabary references at
their own L. Numbers transcribed from sweep_results.txt and
syllabary_ref_results.txt (N-matched windows).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

L = [25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 400, 500, 633]
sig = {
    "Horley":  [-0.025, -0.031, -0.038, -0.045, -0.054, -0.060, -0.068, -0.077],
    "frequency": [-0.029, -0.034, -0.039, -0.041, -0.045, -0.050, -0.058, -0.061, -0.063, -0.064, -0.063, -0.062, -0.059, -0.058, -0.055],
    "random":  [-0.016, -0.019, -0.025, -0.030, -0.034, -0.039, -0.045, -0.049, -0.052, -0.054, -0.054, -0.055, -0.055, -0.055, -0.055],
    "Barthel-adjacent": [-0.010, -0.011, -0.014, -0.016, -0.018, -0.022, -0.024, -0.030, -0.031, -0.036, -0.041, -0.042, -0.047, -0.049, -0.055],
}
cov = {
    "Horley":  [93.6, 87.9, 77.6, 65.8, 58.4, 44.7, 30.9, 23.9],
    "frequency": [84.6, 79.0, 69.8, 62.8, 55.4, 45.6, 33.6, 26.2, 20.6, 13.6, 9.5, 7.0, 4.2, 2.8, 1.7],
    "random":  [99.7, 98.2, 92.6, 83.2, 72.5, 58.9, 41.3, 30.5, 23.3, 14.4, 9.7, 7.0, 4.1, 2.7, 1.7],
    "Barthel-adjacent": [86.7, 80.0, 66.6, 56.9, 49.7, 39.5, 27.8, 21.3, 16.8, 11.0, 7.9, 6.0, 3.6, 2.5, 1.7],
}
# syllabary references, N=14812 windows: (label, L, signal, coverage)
refs = [("Rapa Nui, length folded", 55, -0.170, 43.9),
        ("Maori, folded", 52, -0.151, 44.1),
        ("Linear B", 95, -0.156, 25.6),
        ("Maori, length kept", 98, -0.177, 21.3),
        ("Rapa Nui, length kept", 105, -0.187, 18.7)]

COL = {"Horley": "#2a78d6", "frequency": "#eb6834", "Barthel-adjacent": "#1baf7a", "random": "#55554f"}
STYLE = {"random": dict(ls="--", lw=1.6), "Horley": dict(lw=2.0), "frequency": dict(lw=2.0), "Barthel-adjacent": dict(lw=2.0)}

plt.rcParams.update({"font.size": 8.5, "font.family": "serif", "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#8a8a85", "axes.labelcolor": "#222", "xtick.color": "#444", "ytick.color": "#444"})
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.9), dpi=200)

for ax, data, ylab in ((a, sig, "distance from unigram-matched shuffle"), (b, cov, "bigram coverage (% of table observed)")):
    for k in ("random", "Barthel-adjacent", "frequency", "Horley"):
        ys = data[k]
        ax.plot(L[:len(ys)], ys, color=COL[k], **STYLE[k], solid_capstyle="round")
    ax.set_xscale("log")
    ax.set_xticks([25, 50, 100, 200, 400, 633])
    ax.set_xticklabels(["25", "50", "100", "200", "400", "633"])
    ax.minorticks_off()
    ax.set_xlabel("inventory size after merging, L (classes)")
    ax.set_ylabel(ylab)
    ax.grid(axis="y", color="#e5e5e2", lw=0.6)
    ax.axvline(125, color="#c9c9c4", lw=0.8, zorder=0)
a.set_xlim(22, 750)
b.set_xlim(22, 750)
# direct labels, placed mid-curve where the lines are apart. Each line is a MERGE
# RULE applied to the same token stream, not a catalogue whose size varies.
a.annotate("Horley, merged down", (100, -0.068), xytext=(-5, -3), textcoords="offset points", ha="right", va="top", fontsize=7.5, color="#222")
a.annotate("frequency", (300, -0.062), xytext=(0, -8), textcoords="offset points", ha="center", va="top", fontsize=7.5, color="#222")
a.annotate("random", (40, -0.025), xytext=(3, 5), textcoords="offset points", ha="left", va="bottom", fontsize=7.5, color="#222")
a.annotate("Barthel-adjacent", (200, -0.036), xytext=(0, 5), textcoords="offset points", ha="center", va="bottom", fontsize=7.5, color="#222")
b.annotate("random", (40, 92.6), xytext=(5, 2), textcoords="offset points", fontsize=7.5, color="#222")
b.annotate("Horley, merged down", (60, 58.4), xytext=(7, 4), textcoords="offset points", fontsize=7.5, color="#222")
b.annotate("frequency", (200, 13.6), xytext=(6, 4), textcoords="offset points", fontsize=7.5, color="#222")
b.annotate("Barthel-adjacent", (150, 16.8), xytext=(-8, -12), textcoords="offset points", ha="right", fontsize=7.5, color="#222")
for ax in (a, b):
    ax.text(125, ax.get_ylim()[1], "125", ha="center", va="bottom", fontsize=6.5, color="#777")

# The published catalogues are single points on these curves: Horley's map is the
# right-hand end of its own line (it cannot be un-merged past his 125), and at
# L=633 every rule is the identity, which is the CEIPP numeric reading itself.
for ax, pts in ((a, [(125, -0.077), (633, -0.055)]), (b, [(125, 23.9), (633, 1.7)])):
    for x_, y_ in pts:
        ax.plot(x_, y_, marker="o", ms=6, mfc="white", mec="#222", mew=1.1, ls="none", zorder=5)
a.text(640, -0.088,
       "open circles: published catalogues\n"
       "Horley\u2019s line ends at his own 125\n"
       "at 633 all merge rules coincide",
       ha="right", va="top", fontsize=6.6, color="#555", linespacing=1.5)

# reference syllabaries
for lab, l_, s_, c_ in refs:
    a.plot(l_, s_, marker="D", ms=4.5, color="#111", mec="white", mew=0.6, ls="none")
    b.plot(l_, c_, marker="D", ms=4.5, color="#111", mec="white", mew=0.6, ls="none")
a.annotate("Rapa Nui\n(folded)", (55, -0.170), xytext=(-7, 0), textcoords="offset points", ha="right", va="center", fontsize=7, color="#111")
a.annotate("Maori\n(folded)", (52, -0.151), xytext=(-6, 4), textcoords="offset points", ha="right", va="bottom", fontsize=7, color="#111")
a.annotate("Linear B", (95, -0.156), xytext=(6, 4), textcoords="offset points", ha="left", va="bottom", fontsize=7, color="#111")
a.annotate("Maori, Rapa Nui\n(length kept)", (105, -0.187), xytext=(6, -3), textcoords="offset points", ha="left", va="top", fontsize=7, color="#111")
b.annotate("syllabaries", (50, 44), xytext=(-7, -2), textcoords="offset points", ha="right", va="center", fontsize=7, color="#111")
a.set_ylim(-0.21, 0.0)
a.set_yticks([0, -0.05, -0.10, -0.15, -0.20])
b.set_ylim(0, 102)
a.set_title("(a) structural signal", loc="left", fontsize=9)
b.set_title("(b) coverage", loc="left", fontsize=9)
fig.tight_layout(w_pad=2.0)
fig.savefig("fig_sweep.pdf")
fig.savefig("fig_sweep.png")
print("ok")
