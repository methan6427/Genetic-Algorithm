"""User interface for exam scheduler."""
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

# Paths to the data file and the output folder
_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(_HERE, "data", "ga_exam_timetable_dataset.xlsx")
OUTPUT_DIR = os.path.join(_HERE, "output")

# Maps slot number (1-3) to a readable time string
_SLOT_TIMES = {1: "09:00-11:00", 2: "12:00-14:00", 3: "15:00-17:00"}

# Store the last GA run results so the Save button can use them
_last_schedule: dict | None = None
_last_history: list | None = None


def _format_schedule(schedule: dict) -> str:
    """Convert schedule dict to readable day-by-day format with times."""
    # Group courses by (day, slot number)
    day_slots: dict[tuple[int, int], list[str]] = {}
    for course, slot_id in schedule.items():
        day = int(slot_id[1])
        slot_num = int(slot_id[3])
        day_slots.setdefault((day, slot_num), []).append(course)

    lines = []
    for day in range(1, 7):
        # Skip days that have no exams
        day_has_courses = any(d == day for (d, _) in day_slots)
        if not day_has_courses:
            continue
        lines.append(f"Day {day}")
        for slot_num in range(1, 4):
            courses = day_slots.get((day, slot_num), [])
            if courses:
                lines.append(f"  {_SLOT_TIMES[slot_num]} : {', '.join(sorted(courses))}")
    return "\n".join(lines)


def _build_ui(root: tk.Tk, courses: list, slots: list,
              conflict_table: dict, student_courses: dict) -> None:
    """Build all UI widgets and attach event handlers."""
    global _last_schedule, _last_history

    root.title("Exam Scheduler")
    root.geometry("900x620")
    root.minsize(900, 620)

    # Left panel holds settings and the Run button
    left = tk.Frame(root, padx=14, pady=14)
    left.pack(side=tk.LEFT, fill=tk.Y)

    tk.Label(left, text="Settings", font=("Arial", 12, "bold")).pack(anchor="w")
    tk.Frame(left, height=10).pack()

    # Each tuple defines a label, config key, and default value
    _field_defs = [
        ("Population Size", "pop_size",     "100"),
        ("Max Generations", "max_gen",      "500"),
        ("Mutation Rate",   "mutation_rate","0.05"),
        ("Tournament K",    "tournament_k", "5"),
    ]
    entries: dict[str, tk.StringVar] = {}
    for label, key, default in _field_defs:
        row = tk.Frame(left)
        row.pack(fill=tk.X, pady=3)
        tk.Label(row, text=label, width=17, anchor="w").pack(side=tk.LEFT)
        var = tk.StringVar(value=default)
        tk.Entry(row, textvariable=var, width=9).pack(side=tk.LEFT)
        entries[key] = var

    tk.Frame(left, height=14).pack()

    run_btn = tk.Button(left, text="Run GA", width=16)
    run_btn.pack(pady=4)

    # Status label shows "Ready", "Running...", or "Done — penalty: X"
    status_var = tk.StringVar(value="Ready")
    tk.Label(left, textvariable=status_var, wraplength=190,
             justify=tk.LEFT).pack(anchor="w", pady=4)

    # Thin vertical line to separate left and right panels
    tk.Frame(root, width=2, bg="#c0c0c0").pack(side=tk.LEFT, fill=tk.Y, padx=2)

    # Right panel shows the schedule and action buttons
    right = tk.Frame(root, padx=14, pady=14)
    right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    tk.Label(right, text="Results", font=("Arial", 12, "bold")).pack(anchor="w")
    tk.Frame(right, height=8).pack()

    # Read-only text area displays the best schedule after GA runs
    text_box = scrolledtext.ScrolledText(right, state=tk.DISABLED,
                                         wrap=tk.WORD, font=("Courier", 10))
    text_box.pack(fill=tk.BOTH, expand=True)

    btn_row = tk.Frame(right)
    btn_row.pack(fill=tk.X, pady=8)

    def _show_plot() -> None:
        """Open the convergence chart in a new window."""
        plot_path = os.path.join(OUTPUT_DIR, "convergence.png")
        if not os.path.exists(plot_path):
            messagebox.showinfo("No plot", "Run the GA first to generate a plot.")
            return
        top = tk.Toplevel(root)
        top.title("Convergence Plot")
        try:
            # Try to load PNG with built-in tkinter (only supports GIF/PNG in some versions)
            img = tk.PhotoImage(file=plot_path)
            tk.Label(top, image=img).pack()
            top._img = img  # Keep reference so image is not garbage collected
        except Exception:
            try:
                # Fall back to Pillow if tkinter cannot open the PNG
                from PIL import Image, ImageTk
                img = ImageTk.PhotoImage(Image.open(plot_path))
                tk.Label(top, image=img).pack()
                top._img = img
            except ImportError:
                # If Pillow is not installed, just tell the user where the file is
                messagebox.showinfo("Plot saved", f"Plot saved to:\n{plot_path}")
                top.destroy()

    def _save_results() -> None:
        """Write schedule text file and penalty log CSV to the output folder."""
        if _last_schedule is None:
            messagebox.showinfo("No results", "Run the GA first.")
            return
        from core.report import save_schedule, save_log
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        save_schedule(_last_schedule, os.path.join(OUTPUT_DIR, "best_schedule.txt"))
        save_log(_last_history, os.path.join(OUTPUT_DIR, "run_log.csv"))
        messagebox.showinfo("Saved", f"Files written to:\n{OUTPUT_DIR}")

    tk.Button(btn_row, text="Show Plot",    command=_show_plot).pack(side=tk.LEFT, padx=4)
    tk.Button(btn_row, text="Save Results", command=_save_results).pack(side=tk.LEFT, padx=4)

    def _on_run() -> None:
        """Validate inputs, disable the button, and start the GA in a background thread."""
        global _last_schedule, _last_history
        try:
            config = {
                "pop_size":      int(entries["pop_size"].get()),
                "max_gen":       int(entries["max_gen"].get()),
                "mutation_rate": float(entries["mutation_rate"].get()),
                "tournament_k":  int(entries["tournament_k"].get()),
            }
        except ValueError:
            messagebox.showerror("Invalid input", "All fields must be numeric.")
            return

        # Disable the button so the user cannot start two runs at the same time
        run_btn.config(state=tk.DISABLED)
        status_var.set("Running...")
        text_box.config(state=tk.NORMAL)
        text_box.delete("1.0", tk.END)
        text_box.config(state=tk.DISABLED)

        def _worker() -> None:
            """Run the GA and then update the UI when done (called from background thread)."""
            from core.evolve import run_ga
            from core.report import save_plot
            best, history = run_ga(courses, slots, conflict_table,
                                   student_courses, config)

            def _on_done() -> None:
                """Update UI widgets with results — must run on the main thread."""
                global _last_schedule, _last_history
                _last_schedule = best
                _last_history = history

                run_btn.config(state=tk.NORMAL)
                status_var.set(f"Done — penalty: {history[-1]}")

                # Show the best schedule in the text box
                text_box.config(state=tk.NORMAL)
                text_box.delete("1.0", tk.END)
                text_box.insert(tk.END, _format_schedule(best))
                text_box.config(state=tk.DISABLED)

                # Save the convergence chart to the output folder
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                save_plot(history, os.path.join(OUTPUT_DIR, "convergence.png"))

            # Use root.after to safely update the UI from the background thread
            root.after(0, _on_done)

        threading.Thread(target=_worker, daemon=True).start()

    run_btn.config(command=_on_run)


def main() -> None:
    """Load data and open the main window."""
    # Stop early if the dataset file is missing
    if not os.path.exists(DATA_PATH):
        _r = tk.Tk()
        _r.withdraw()
        messagebox.showerror(
            "Dataset not found",
            f"Could not find:\n{DATA_PATH}\n\n"
            "Place ga_exam_timetable_dataset.xlsx in the data/ folder."
        )
        sys.exit(1)

    from core.parse import load_data, load_slots

    courses, conflict_table, student_courses = load_data(DATA_PATH)
    slots = load_slots()

    root = tk.Tk()
    _build_ui(root, courses, slots, conflict_table, student_courses)
    root.mainloop()


if __name__ == "__main__":
    main()
