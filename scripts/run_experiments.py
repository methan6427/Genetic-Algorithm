"""
Run all GA experiments with current dataset, generate all figures,
capture app screenshot, then rebuild report_final_new.docx.
"""
import os, sys, json, time, threading
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA  = os.path.join(ROOT, "exam_scheduler", "data", "ga_exam_timetable_dataset.xlsx")
IMGS  = os.path.join(ROOT, "scripts", "new_figures")
os.makedirs(IMGS, exist_ok=True)

sys.path.insert(0, os.path.join(ROOT, "exam_scheduler"))
from core.parse   import load_data, load_slots, load_bad_schedule
from core.penalty import score as penalty_score
from core.evolve  import run_ga

courses, conflict_table, student_courses = load_data(DATA)
slots = load_slots()
bad   = load_bad_schedule(DATA)

print(f"Courses: {len(courses)}")
print(f"Students: {len(student_courses)}")
print(f"Enrollments: {sum(len(v) for v in student_courses.values())}")
print(f"Courses list: {courses}")

# ── 1. Bad-schedule breakdown ─────────────────────────────────────────────────
def breakdown(schedule):
    slot_to_courses = {}
    for c, s in schedule.items():
        slot_to_courses.setdefault(s, []).append(c)
    hc1 = sum(
        conflict_table.get(a, {}).get(b, 0) * 1000
        for cs in slot_to_courses.values()
        for i, a in enumerate(cs) for b in cs[i+1:]
    )
    hc2 = hc3 = sc1 = 0
    for enrolled in student_courses.values():
        dc = {}
        for c in enrolled:
            s = schedule.get(c)
            if s:
                d = int(s[1]); dc[d] = dc.get(d, 0) + 1
        for d, cnt in dc.items():
            if cnt > 2: hc2 += 800
            elif cnt == 2: sc1 += 50
        ds = sorted(dc)
        for i in range(len(ds)-1):
            if ds[i+1] == ds[i]+1 and dc[ds[i]]+dc[ds[i+1]] >= 4:
                hc3 += 500
    du = len({int(s[1]) for s in schedule.values()})
    sc2 = max(0, (du - 5)) * 100
    return hc1, hc2, hc3, sc1, sc2

hc1, hc2, hc3, sc1, sc2 = breakdown(bad)
bad_total = hc1 + hc2 + hc3 + sc1 + sc2
print(f"\nBad schedule: HC1={hc1} HC2={hc2} HC3={hc3} SC1={sc1} SC2={sc2} Total={bad_total}")

# shared students for the biggest HC1 pair
shared_info = {}
for a in courses:
    for b in courses:
        if a < b:
            sh = conflict_table.get(a, {}).get(b, 0)
            if sh > 0:
                shared_info[(a,b)] = sh
top_pair = max(shared_info, key=shared_info.get)
top_shared = shared_info[top_pair]
print(f"Top conflict pair: {top_pair[0]}/{top_pair[1]} = {top_shared} shared students")
# also check bad schedule slot for this pair
slot_a = bad.get(top_pair[0], "?")
slot_b = bad.get(top_pair[1], "?")
print(f"  In bad schedule: {slot_a} / {slot_b}")

# ── Figure 2: penalty breakdown bar chart ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
labels = ["HC1\n(same-slot)", "HC2\n(>2/day)", "HC3\n(consec.)", "SC1\n(2/day)", "SC2\n(days>5)"]
values = [hc1, hc2, hc3, sc1, sc2]
colors = ["#d32f2f","#e65100","#f9a825","#388e3c","#1565c0"]
bars = ax.bar(labels, values, color=colors)
for bar, val in zip(bars, values):
    if val > 0:
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+200,
                f"{val:,}", ha="center", va="bottom", fontsize=10)
ax.set_title(f"Bad-Schedule Penalty Breakdown  (total = {bad_total:,})", fontsize=12)
ax.set_ylabel("Penalty Points")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.grid(axis="y", linestyle="--", alpha=0.4)
fig.tight_layout()
fig.savefig(os.path.join(IMGS, "fig2_breakdown.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved fig2_breakdown.png")

# ── 2. Default GA run (500 gen) ───────────────────────────────────────────────
print("\nRunning default GA (pop=100, gen=500, mut=0.05, k=5)...")
cfg_default = {"pop_size":100,"max_gen":500,"mutation_rate":0.05,"tournament_k":5}
best_default, hist_default = run_ga(courses, slots, conflict_table, student_courses, cfg_default)
gen0_penalty   = hist_default[0]
gen499_penalty = hist_default[-1]
improvement    = gen0_penalty - gen499_penalty
pct_improve    = improvement / gen0_penalty * 100
print(f"  Gen 0:   {gen0_penalty}")
print(f"  Gen 499: {gen499_penalty}")
print(f"  Improvement: {improvement} ({pct_improve:.1f}%)")

# ── Figure 3: convergence default ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(hist_default, linewidth=1.5, color="#1565c0")
ax.fill_between(range(len(hist_default)), hist_default, alpha=0.12, color="#1565c0")
ax.axhline(gen499_penalty, color="red", linestyle="--", linewidth=1.2,
           label=f"Final penalty: {gen499_penalty:,}")
ax.set_title(f"GA Convergence — Default Parameters (pop=100, gen=500, mut=0.05, k=5)", fontsize=11)
ax.set_xlabel("Generation"); ax.set_ylabel("Best Penalty Score")
ax.legend(fontsize=10)
ax.grid(linestyle="--", alpha=0.4)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.tight_layout()
fig.savefig(os.path.join(IMGS, "fig3_convergence.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved fig3_convergence.png")

# ── Figure 4: best schedule grid ──────────────────────────────────────────────
SLOT_TIMES = {1:"09:00-11:00", 2:"12:00-14:00", 3:"15:00-17:00"}
day_slots = {}
for c, s in best_default.items():
    d, sn = int(s[1]), int(s[3])
    day_slots.setdefault((d, sn), []).append(c)

days_used = sorted({int(s[1]) for s in best_default.values()})
colors_palette = [
    "#AED6F1","#A9DFBF","#FAD7A0","#D2B4DE","#F1948A",
    "#85C1E9","#82E0AA","#F8C471","#BB8FCE","#EC7063",
    "#5DADE2","#58D68D","#F5CBA7","#A569BD","#E74C3C",
    "#2E86C1","#1E8449","#D4AC0D","#7D3C98","#CB4335",
    "#1A5276","#117A65",
]
course_color = {c: colors_palette[i % len(colors_palette)] for i, c in enumerate(sorted(courses))}

fig, ax = plt.subplots(figsize=(max(10, len(days_used)*1.8), 5))
ax.axis("off")
ax.set_xlim(0, len(days_used))
ax.set_ylim(0, 3)

col_w = 1.0
row_h = 1.0
for ci, day in enumerate(days_used):
    ax.text(ci + 0.5, 3.12, f"Day {day}", ha="center", va="bottom",
            fontsize=11, fontweight="bold")
    for sn in range(1, 4):
        cs = day_slots.get((day, sn), [])
        row = 3 - sn
        n = len(cs)
        if n == 0:
            rect = plt.Rectangle((ci, row), col_w, row_h, fc="#f5f5f5", ec="#cccccc", lw=0.5)
            ax.add_patch(rect)
        else:
            w = col_w / n
            for k, course in enumerate(cs):
                rect = plt.Rectangle((ci + k*w, row), w, row_h,
                                     fc=course_color[course], ec="white", lw=1.2)
                ax.add_patch(rect)
                ax.text(ci + k*w + w/2, row + 0.5, course,
                        ha="center", va="center", fontsize=7, fontweight="bold")

for sn in range(1, 4):
    row = 3 - sn
    ax.text(-0.08, row + 0.5, SLOT_TIMES[sn], ha="right", va="center", fontsize=8)

ax.set_title(f"Best Schedule Layout  (penalty = {gen499_penalty:,})", fontsize=12, pad=20)
fig.tight_layout()
fig.savefig(os.path.join(IMGS, "fig4_schedule.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved fig4_schedule.png")

# ── 3. Parameter tuning (4 runs × 300 gen) ───────────────────────────────────
tuning_configs = [
    ("pop_size=50",  {"pop_size": 50,  "max_gen":300,"mutation_rate":0.05,"tournament_k":5}),
    ("pop_size=200", {"pop_size":200,  "max_gen":300,"mutation_rate":0.05,"tournament_k":5}),
    ("mut=0.02",     {"pop_size":100,  "max_gen":300,"mutation_rate":0.02,"tournament_k":5}),
    ("mut=0.10",     {"pop_size":100,  "max_gen":300,"mutation_rate":0.10,"tournament_k":5}),
]
tuning_results = []
for label, cfg in tuning_configs:
    print(f"Running tuning: {label}...")
    _, hist = run_ga(courses, slots, conflict_table, student_courses, cfg)
    final = hist[-1]
    tuning_results.append((label, cfg, hist, final))
    print(f"  Final: {final}")

# ── Figure 5: tuning comparison ───────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
titles = [
    ("pop_size=50",  f"pop=50, mut=0.05, k=5"),
    ("pop_size=200", f"pop=200, mut=0.05, k=5"),
    ("mut=0.02",     f"pop=100, mut=0.02, k=5"),
    ("mut=0.10",     f"pop=100, mut=0.1, k=5"),
]
for ax, (label, cfg, hist, final), (_, subtitle) in zip(axes.flat, tuning_results, titles):
    cfg_key = list(cfg.keys())[0] + "=" + str(list(cfg.values())[0])
    ax.plot(hist, linewidth=1.3, color="#1565c0")
    ax.annotate(f"final: {final:,}",
                xy=(len(hist)-1, final),
                xytext=(len(hist)*0.6, final + (max(hist)-final)*0.15 + 200),
                arrowprops=dict(arrowstyle="->", color="black"),
                fontsize=9)
    short = label.replace("pop_size","pop_size")
    ax.set_title(f"{short}\n{subtitle}", fontsize=9)
    ax.set_xlabel("Generation", fontsize=8)
    ax.set_ylabel("Best Penalty", fontsize=8)
    ax.grid(linestyle="--", alpha=0.4)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
fig.suptitle("GA Parameter Tuning — Convergence Comparison", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(IMGS, "fig5_tuning.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("Saved fig5_tuning.png")

# ── 4. App screenshot via Tkinter + PIL ───────────────────────────────────────
print("\nLaunching app for screenshot (150 gen)...")

import tkinter as tk
from tkinter import scrolledtext
import subprocess, importlib

screenshot_path = os.path.join(IMGS, "fig1_app.png")

def take_app_screenshot():
    from core.evolve import run_ga as _run
    cfg_shot = {"pop_size":100,"max_gen":150,"mutation_rate":0.05,"tournament_k":5}
    SLOT_TIMES_LOCAL = {1:"09:00-11:00",2:"12:00-14:00",3:"15:00-17:00"}

    def fmt(schedule):
        ds = {}
        for c, s in schedule.items():
            d, sn = int(s[1]), int(s[3])
            ds.setdefault((d,sn),[]).append(c)
        lines = []
        for day in range(1,7):
            if not any(d==day for (d,_) in ds): continue
            lines.append(f"Day {day}")
            for sn in range(1,4):
                cs = ds.get((day,sn),[])
                if cs:
                    lines.append(f"  {SLOT_TIMES_LOCAL[sn]} : {', '.join(sorted(cs))}")
        return "\n".join(lines)

    root = tk.Tk()
    root.title("Exam Scheduler")
    root.geometry("900x620")
    root.resizable(False, False)

    left = tk.Frame(root, padx=14, pady=14)
    left.pack(side=tk.LEFT, fill=tk.Y)
    tk.Label(left, text="Settings", font=("Arial",12,"bold")).pack(anchor="w")
    tk.Frame(left, height=10).pack()
    for label, val in [("Population Size","100"),("Max Generations","150"),
                       ("Mutation Rate","0.05"),("Tournament K","5")]:
        row = tk.Frame(left); row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=label, width=17, anchor="w").pack(side=tk.LEFT)
        tk.Entry(row, width=9).insert(0, val)
        e = tk.Entry(row, width=9); e.pack(side=tk.LEFT)
        e.insert(0, val)

    tk.Frame(left, height=14).pack()
    btn = tk.Button(left, text="Run GA", width=16, bg="#4CAF50", fg="white",
                    font=("Arial",10,"bold"))
    btn.pack(pady=4)
    status_var = tk.StringVar(value="Running...")
    status_lbl = tk.Label(left, textvariable=status_var, wraplength=190)
    status_lbl.pack(anchor="w", pady=4)

    tk.Frame(root, width=2, bg="#c0c0c0").pack(side=tk.LEFT, fill=tk.Y, padx=2)
    right = tk.Frame(root, padx=14, pady=14)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tk.Label(right, text="Results", font=("Arial",12,"bold")).pack(anchor="w")
    tk.Frame(right, height=8).pack()
    text_box = scrolledtext.ScrolledText(right, state=tk.DISABLED,
                                         wrap=tk.WORD, font=("Courier",10))
    text_box.pack(fill=tk.BOTH, expand=True)
    btn_row = tk.Frame(right); btn_row.pack(fill=tk.X, pady=8)
    tk.Button(btn_row, text="Show Plot").pack(side=tk.LEFT, padx=4)
    tk.Button(btn_row, text="Save Results").pack(side=tk.LEFT, padx=4)

    result_holder = {}

    def worker():
        best, hist = _run(courses, slots, conflict_table, student_courses, cfg_shot)
        result_holder["best"] = best
        result_holder["hist"] = hist
        def done():
            final = hist[-1]
            status_var.set(f"Done — penalty: {final}")
            text_box.config(state=tk.NORMAL)
            text_box.delete("1.0", tk.END)
            text_box.insert(tk.END, fmt(best))
            text_box.config(state=tk.DISABLED)
            # take screenshot after small delay
            root.after(800, capture_and_close)
        root.after(0, done)

    def capture_and_close():
        try:
            from PIL import ImageGrab
            root.update()
            x, y = root.winfo_rootx(), root.winfo_rooty()
            w, h = root.winfo_width(), root.winfo_height()
            img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            img.save(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
        except Exception as e:
            print(f"Screenshot failed: {e}")
        finally:
            root.destroy()

    threading.Thread(target=worker, daemon=True).start()
    root.mainloop()
    return result_holder

result = take_app_screenshot()
shot_penalty = result.get("hist", [0])[-1] if result.get("hist") else gen499_penalty

# ── Save all numbers to JSON ──────────────────────────────────────────────────
nums = {
    "courses": len(courses),
    "students": len(student_courses),
    "enrollments": sum(len(v) for v in student_courses.values()),
    "enroll_range": f"{min(len(v) for v in student_courses.values())}–{max(len(v) for v in student_courses.values())}",
    "bad_total": bad_total,
    "hc1": hc1, "hc2": hc2, "hc3": hc3, "sc1": sc1, "sc2": sc2,
    "top_pair_a": top_pair[0], "top_pair_b": top_pair[1],
    "top_shared": top_shared,
    "top_hc1_contrib": top_shared * 1000,
    "gen0": gen0_penalty,
    "gen499": gen499_penalty,
    "improvement": improvement,
    "pct_improve": round(pct_improve, 1),
    "tuning": [
        {"label": r[0], "pop_size": r[1]["pop_size"],
         "mutation_rate": r[1]["mutation_rate"],
         "generations": 300, "final": r[3]}
        for r in tuning_results
    ],
    "screenshot_penalty": shot_penalty,
}
# population size improvement
t = nums["tuning"]
pop50  = t[0]["final"]
pop200 = t[1]["final"]
pop_pct = round((pop50 - pop200) / pop50 * 100, 1)
nums["pop_pct_improve"] = pop_pct

json_path = os.path.join(ROOT, "scripts", "experiment_numbers.json")
with open(json_path, "w") as f:
    json.dump(nums, f, indent=2)
print(f"\nAll numbers saved to {json_path}")
print(json.dumps(nums, indent=2))
