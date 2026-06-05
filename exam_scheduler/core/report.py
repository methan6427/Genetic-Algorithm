"""Output writers: schedule txt, run log csv, convergence plot."""
import csv
import os

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — safe to call from threads
import matplotlib.pyplot as plt


_SLOT_TIMES = {1: "09:00-11:00", 2: "12:00-14:00", 3: "15:00-17:00"}


def _ensure_dir(filepath: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)


def save_schedule(schedule: dict, filepath: str) -> None:
    """Write the schedule in day-grid format to a .txt file."""
    _ensure_dir(filepath)

    # Group courses by (day, slot_num)
    day_slots: dict[tuple[int, int], list[str]] = {}
    for course, slot_id in schedule.items():
        day = int(slot_id[1])
        slot_num = int(slot_id[3])
        day_slots.setdefault((day, slot_num), []).append(course)

    with open(filepath, "w", encoding="utf-8") as f:
        for day in range(1, 7):
            day_entries = {s: cs for (d, s), cs in day_slots.items() if d == day}
            if not day_entries:
                continue
            f.write(f"Day {day}\n")
            for slot_num in range(1, 4):
                courses = day_slots.get((day, slot_num), [])
                if courses:
                    time_str = _SLOT_TIMES[slot_num]
                    f.write(f"  {time_str} : {', '.join(sorted(courses))}\n")


def save_log(score_history: list, filepath: str) -> None:
    """Write run_log.csv with columns generation,best_penalty."""
    _ensure_dir(filepath)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["generation", "best_penalty"])
        for gen, penalty in enumerate(score_history):
            writer.writerow([gen, penalty])


def save_plot(score_history: list, filepath: str) -> None:
    """Save a convergence line chart. Does NOT call plt.show()."""
    _ensure_dir(filepath)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(range(len(score_history)), score_history, linewidth=1.2)
    ax.set_title("GA Convergence")
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best Penalty")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)
