"""Capture app screenshot with window forced to front."""
import os, sys, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exam_scheduler"))

import tkinter as tk
from tkinter import scrolledtext
from core.parse  import load_data, load_slots
from core.evolve import run_ga

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "exam_scheduler", "data", "ga_exam_timetable_dataset.xlsx")
OUT  = os.path.join(ROOT, "scripts", "new_figures", "fig1_app.png")

courses, conflict_table, student_courses = load_data(DATA)
slots = load_slots()
SLOT_TIMES = {1:"09:00-11:00", 2:"12:00-14:00", 3:"15:00-17:00"}

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
                lines.append(f"  {SLOT_TIMES[sn]} : {', '.join(sorted(cs))}")
    return "\n".join(lines)

root = tk.Tk()
root.title("Exam Scheduler")
root.geometry("900x620")
root.resizable(False, False)
root.attributes("-topmost", True)  # keep on top

left = tk.Frame(root, padx=14, pady=14)
left.pack(side=tk.LEFT, fill=tk.Y)
tk.Label(left, text="Settings", font=("Arial",12,"bold")).pack(anchor="w")
tk.Frame(left, height=10).pack()
fields = [("Population Size","100"),("Max Generations","150"),
          ("Mutation Rate","0.05"),("Tournament K","5")]
for label, val in fields:
    row = tk.Frame(left); row.pack(fill=tk.X, pady=3)
    tk.Label(row, text=label, width=17, anchor="w").pack(side=tk.LEFT)
    e = tk.Entry(row, width=9); e.pack(side=tk.LEFT); e.insert(0, val)

tk.Frame(left, height=14).pack()
btn = tk.Button(left, text="Run GA", width=16, bg="#4CAF50", fg="white",
                font=("Arial",10,"bold"))
btn.pack(pady=4)
status_var = tk.StringVar(value="Running...")
tk.Label(left, textvariable=status_var, wraplength=190).pack(anchor="w", pady=4)

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

def worker():
    cfg = {"pop_size":100,"max_gen":150,"mutation_rate":0.05,"tournament_k":5}
    best, hist = run_ga(courses, slots, conflict_table, student_courses, cfg)
    def done():
        final = hist[-1]
        status_var.set(f"Done — penalty: {final}")
        text_box.config(state=tk.NORMAL)
        text_box.delete("1.0", tk.END)
        text_box.insert(tk.END, fmt(best))
        text_box.config(state=tk.DISABLED)
        root.after(1200, capture)
    root.after(0, done)

def capture():
    try:
        from PIL import ImageGrab
        root.update()
        root.lift()
        root.focus_force()
        time.sleep(0.3)
        root.update()
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
        img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
        img.save(OUT)
        print(f"Saved: {OUT}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        root.destroy()

threading.Thread(target=worker, daemon=True).start()
root.mainloop()
