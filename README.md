# Exam Timetable Scheduling — Genetic Algorithm

**COMP338 · Introduction to Artificial Intelligence**
Adam Khabisa · 1210475 · Birzeit University

Assigns 22 university course exams to 18 time slots (6 days × 3 slots/day) for 95 students using a hand-built Genetic Algorithm — no GA libraries used. Two independent implementations are provided: one in **Python + Tkinter** and one in **Java + JavaFX**.

---

## Table of Contents

- [Problem Overview](#problem-overview)
- [Penalty Function](#penalty-function)
- [Part 1 — Python Implementation](#part-1--python-implementation)
  - [Requirements](#requirements)
  - [File Tree](#file-tree)
  - [How to Run](#how-to-run)
  - [UI Walkthrough](#ui-walkthrough)
  - [Module Reference](#module-reference)
  - [Output Files](#output-files)
- [Part 2 — Java Implementation](#part-2--java-implementation)
  - [Requirements](#requirements-1)
  - [File Tree](#file-tree-1)
  - [How to Run](#how-to-run-1)
  - [Class Reference](#class-reference)
  - [Output Files](#output-files-1)
- [GA Design](#ga-design)
- [Constraint Reference](#constraint-reference)

---

## Problem Overview

| Item | Value |
|---|---|
| Courses | 22 |
| Students | 95 |
| Enrolments | 481 (4–7 courses per student) |
| Available slots | 18 (D1S1 … D6S3) |
| Slot times | 09:00–11:00 · 12:00–14:00 · 15:00–17:00 |

A **chromosome** is a Python `dict` / Java `Map<String,String>` mapping each course code to a slot ID:

```
{ "COMP2110": "D1S2", "COMP3320": "D3S1", ... }   // 22 entries
```

---

## Penalty Function

The fitness function returns a total penalty — **lower is better, 0 is perfect**.

| ID | Type | Rule | Penalty |
|---|---|---|---|
| HC1 | Hard | Two courses in the same slot share at least one student | shared\_students × 1,000 |
| HC2 | Hard | A student has more than 2 exams on one day | 800 per student |
| HC3 | Hard | A student has ≥ 4 exams across two consecutive days | 500 per student |
| SC1 | Soft | A student has exactly 2 exams on one day | 50 per student |
| SC2 | Soft | Schedule uses more than 5 days | 100 per extra day |

---

## Part 1 — Python Implementation

### Requirements

- Python 3.10+
- `openpyxl` — reads the Excel dataset
- `matplotlib` — draws the convergence chart
- `tkinter` — bundled with the standard library (no install needed)

Install dependencies:

```bash
pip install -r requirements.txt
```

`requirements.txt`:
```
openpyxl
matplotlib
```

### File Tree

```
exam_scheduler/
├── app.py                      # Entry point — launches the Tkinter window
├── data/
│   └── ga_exam_timetable_dataset.xlsx   # Read-only dataset (do not modify)
├── core/
│   ├── __init__.py             # Package marker
│   ├── parse.py                # Reads Excel → courses, conflict table, student map
│   ├── penalty.py              # Pure fitness function (same input → same output)
│   ├── evolve.py               # GA: init, selection, crossover, mutation, main loop
│   └── report.py               # Saves schedule .txt, run_log .csv, convergence .png
└── output/                     # All generated files land here (git-tracked for samples)
    ├── best_schedule.txt
    ├── run_log.csv
    └── convergence.png
```

### How to Run

```bash
cd exam_scheduler
python app.py
```

> On Windows with a space in the path, wrap it in quotes:
> ```
> cd "C:\path\to\AI-Project\exam_scheduler"
> python app.py
> ```

### UI Walkthrough

The window is split into two panels:

**Left — Settings**

| Field | Default | Description |
|---|---|---|
| Population Size | 100 | Number of candidate schedules per generation |
| Max Generations | 500 | How many generations the GA runs |
| Mutation Rate | 0.05 | Per-gene probability of random slot reassignment |
| Tournament K | 5 | Candidates compared in each tournament selection |

Click **Run GA** — the GA runs in a background thread so the window stays responsive. The status label updates to `Running…` then `Done — penalty: X` when finished.

**Right — Results**

- The best schedule is displayed as a day-by-day timetable in the scrollable text box.
- **Show Plot** — opens the convergence chart in a new window.
- **Save Results** — writes `best_schedule.txt` and `run_log.csv` to `output/`.

### Module Reference

#### `core/parse.py`

| Function | Returns | Description |
|---|---|---|
| `load_data(filepath)` | `(courses, conflict_table, student_courses)` | Reads `Course_Catalog`, `Enrollment_Pairs` sheets; builds the conflict table |
| `load_slots()` | `list[str]` | Returns the 18 slot IDs `D1S1`…`D6S3` |
| `load_bad_schedule(filepath)` | `dict` | Reads `Sample_Bad_Schedule` sheet for penalty testing |

#### `core/penalty.py`

```python
def score(schedule: dict, conflict_table: dict, student_courses: dict) -> int
```

Pure function — no side effects. Returns total penalty. Run it directly to test against the bad schedule:

```bash
python -m core.penalty
# Bad schedule penalty: 201,650
# COMP3320/COMP3330 shared students: 36  →  HC1 contribution: 36,000
```

#### `core/evolve.py`

| Function | Description |
|---|---|
| `init_population(size, courses, slots)` | Creates `size` random schedules |
| `tournament_select(population, scores, k)` | Picks the best of `k` random individuals |
| `crossover(parent_a, parent_b, courses)` | Single-point crossover; returns one child |
| `mutate(schedule, slots, rate)` | Randomly reassigns genes with probability `rate` |
| `run_ga(courses, slots, conflict_table, student_courses, config)` | Full GA loop; returns `(best_schedule, score_history)` |

`config` is a plain `dict` with keys: `pop_size`, `max_gen`, `mutation_rate`, `tournament_k`.

Elitism: the two best individuals are copied unchanged to every new generation.

#### `core/report.py`

| Function | Description |
|---|---|
| `save_schedule(schedule, filepath)` | Writes day-grid `.txt` |
| `save_log(score_history, filepath)` | Writes `generation,best_penalty` CSV |
| `save_plot(score_history, filepath)` | Saves `convergence.png` via matplotlib Agg backend |

### Output Files

**`output/best_schedule.txt`**
```
Day 1
  09:00-11:00 : COMP3390, MATH2380
  15:00-17:00 : COMP3130, ENEE2304
Day 2
  ...
```

**`output/run_log.csv`**
```
generation,best_penalty
0,15050
1,12300
...
499,1000
```

**`output/convergence.png`** — matplotlib line chart, x = generation, y = best penalty.

---

## Part 2 — Java Implementation

### Requirements

- **Java 21** (JDK 21+) — must be on `PATH`
- **JavaFX 21.0.2** — downloaded automatically by Maven on first build
- **Apache POI 5.2.5** — downloaded automatically by Maven on first build
- No manual Maven install needed — `mvnw.cmd` is self-contained

Check your Java version:
```bash
java -version
# Should print: openjdk 21 (or Oracle JDK 21)
```

### File Tree

```
exam_scheduler_java/
├── run.bat                          # Double-click or run from terminal to launch
├── mvnw.cmd                         # Maven wrapper — downloads Maven automatically
├── pom.xml                          # Project config: Java 21, JavaFX 21.0.2, POI 5.2.5
├── data/
│   └── dataset.xlsx                 # Read-only dataset
├── output/                          # Generated files saved here
│   ├── best_schedule.txt
│   ├── run_log.csv
│   └── convergence.png
├── .mvn/
│   ├── wrapper/
│   │   └── maven-wrapper.properties # Points mvnw.cmd at Maven 3.9.9
│   └── apache-maven-3.9.9/          # Bundled Maven (no PATH install needed)
└── src/main/java/com/examscheduler/
    ├── App.java                     # JavaFX Application entry point
    └── core/
        ├── Parser.java              # Reads dataset.xlsx via Apache POI
        ├── Penalty.java             # Pure fitness function
        ├── GeneticAlgorithm.java    # GA logic (records: GaConfig, GaResult)
        └── Report.java              # Saves schedule, CSV log, PNG convergence chart
```

### How to Run

**Option A — double-click** `run.bat`

**Option B — terminal**

```bat
cd exam_scheduler_java
run.bat
```

**Option C — Maven directly** (if Maven is installed separately)

```bash
cd exam_scheduler_java
mvn javafx:run
```

Maven downloads JavaFX and POI on the first run (~30 seconds). Subsequent runs are instant.

### Class Reference

#### `Parser.java`

```java
Parser.DataSet ds = Parser.loadData("data/dataset.xlsx");
// ds.courses()        → List<String>  (22 course codes)
// ds.conflictTable()  → Map<String, Map<String, Integer>>
// ds.studentCourses() → Map<String, List<String>>

List<String> slots = Parser.loadSlots();   // D1S1 … D6S3
```

Reads three sheets: `Course_Catalog`, `Enrollment_Pairs`, `Sample_Bad_Schedule`.

#### `Penalty.java`

```java
int score = Penalty.score(schedule, conflictTable, studentCourses);
```

Same constraint logic as the Python version — HC1/HC2/HC3/SC1/SC2. Pure static method, no side effects.

#### `GeneticAlgorithm.java`

Uses Java 16 **records** for immutable config and result objects:

```java
GeneticAlgorithm.GaConfig config =
    new GeneticAlgorithm.GaConfig(popSize, maxGen, mutRate, tournK);

GeneticAlgorithm.GaResult result =
    new GeneticAlgorithm().runGa(courses, slots, conflictTable, studentCourses, config);

Map<String, String> best    = result.bestSchedule();
List<Integer>       history = result.scoreHistory();
```

| Method | Description |
|---|---|
| `initPopulation(size, courses, slots)` | Random initialisation |
| `tournamentSelect(population, scores, k)` | Picks best of `k` random individuals |
| `crossover(parentA, parentB, courses)` | Single-point crossover |
| `mutate(schedule, slots, rate)` | Per-gene random reassignment |
| `runGa(...)` | Full loop with elitism (top 2 preserved each generation) |

#### `App.java`

JavaFX `Application` subclass. Mirrors the Python UI exactly:

- Left panel: `TextField` inputs + **Run GA** button + status `Label`
- Right panel: read-only `TextArea` + **Show Plot** + **Save Results**
- GA runs on a `CompletableFuture` background thread; UI updated via `Platform.runLater()`
- **Show Plot** opens a live `LineChart<Number,Number>` in a new `Stage`

#### `Report.java`

| Method | Description |
|---|---|
| `saveSchedule(schedule, path)` | Day-grid `.txt` |
| `saveLog(history, path)` | `generation,best_penalty` CSV |
| `savePlot(history, path)` | Saves convergence PNG via JavaFX `WritableImage` → `ImageIO` |
| `buildConvergenceChart(history)` | Returns a `LineChart` node for the Show Plot window |

### Output Files

Same format as the Python version — `best_schedule.txt`, `run_log.csv`, `convergence.png` — written to `exam_scheduler_java/output/`.

---

## GA Design

Both implementations use the same algorithm:

```
1. Initialise   — N random schedules (each course → random slot)
2. Evaluate     — score every individual with the penalty function
3. Elitism      — copy the 2 best individuals to the next generation unchanged
4. Selection    — tournament selection (k candidates, pick lowest penalty)
5. Crossover    — single-point: split course list at random index,
                  take left half from parent A, right half from parent B
6. Mutation     — each gene (course slot) reassigned randomly with P = mutation_rate
7. Repeat       — from step 2 for max_gen generations
8. Return       — best schedule seen across all generations
```

Default parameters: `pop=100 · gen=500 · mutation=0.05 · k=5`

---

## Constraint Reference

Slot IDs follow the pattern `D{day}S{slot}` where day ∈ {1…6} and slot ∈ {1,2,3}.

| Slot | Day | Time |
|---|---|---|
| D1S1 | 1 | 09:00–11:00 |
| D1S2 | 1 | 12:00–14:00 |
| D1S3 | 1 | 15:00–17:00 |
| D2S1 | 2 | 09:00–11:00 |
| … | … | … |
| D6S3 | 6 | 15:00–17:00 |
