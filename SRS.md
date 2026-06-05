# Software Requirements Specification
## Exam Timetable Scheduler using Genetic Algorithm
### COMP338 — Introduction to Artificial Intelligence

---

## 1. Overview

This document covers the requirements for a Genetic Algorithm that generates
a conflict-free exam timetable for 95 students across 22 courses.
The system runs as a desktop application (Python + Tkinter) and produces
a schedule, a convergence log, and a convergence plot.

---

## 2. Problem Definition

### 2.1 Input

- 95 students, each enrolled in 4 to 7 courses
- 22 courses total
- 18 available exam slots: 6 days, 3 slots per day
- Slot times: 09:00-11:00, 12:00-14:00, 15:00-17:00

### 2.2 Output

- One slot assignment per course (22 assignments total)
- A penalty score for the final schedule (lower = better)
- A convergence history (best penalty per generation)

### 2.3 Representation

Each candidate solution (chromosome) is a dictionary mapping
every course code to one slot ID. Example:

```
{ "COMP2110": "D1S2", "COMP2340": "D3S1", ..., "PHYS1411": "D2S3" }
```

A gene is a single course-to-slot pair. The chromosome contains 22 genes.

---

## 3. Constraints

### 3.1 Hard Constraints

| ID   | Constraint                                                        | Penalty     |
|------|-------------------------------------------------------------------|-------------|
| HC1  | No two courses share a slot if any student is in both            | 1000 / pair |
| HC2  | No student has more than 2 exams on the same day                 | 800 / student|
| HC3  | No student has 4 exams across two back-to-back days              | 500 / student|

HC1 is per conflicting course pair per student overlap.
HC2 and HC3 are per affected student.

### 3.2 Soft Constraints

| ID   | Constraint                                                        | Penalty     |
|------|-------------------------------------------------------------------|-------------|
| SC1  | Avoid giving a student exactly 2 exams on the same day           | 50 / student|
| SC2  | Minimize total days used — preferred maximum is 5                | 100 / extra day|

### 3.3 Structural Constraints

- Each day holds exactly 3 slots
- Total available slots: 18
- Total courses to schedule: 22 (more courses than slots is intentional —
  some slots will hold multiple courses)

---

## 4. Functional Requirements

### 4.1 Data Loading (core/parse.py)

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| FR1.1 | Read course list from Course_Catalog sheet (openpyxl, read_only=True)   |
| FR1.2 | Build conflict_table from Enrollment_Pairs sheet                         |
| FR1.3 | Build student_courses dict: { student_id: [course, ...] }               |
| FR1.4 | Return hardcoded list of 18 slot IDs                                     |
| FR1.5 | Read Sample_Bad_Schedule sheet for penalty function testing              |

### 4.2 Penalty Function (core/penalty.py)

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| FR2.1 | Accept schedule dict, conflict_table, and student_courses as arguments  |
| FR2.2 | Return a single non-negative integer (total penalty)                    |
| FR2.3 | Apply all five penalty rules from section 3                             |
| FR2.4 | Be pure — no I/O, no side effects, deterministic                        |
| FR2.5 | Score the bad sample schedule and return a value clearly above zero     |

### 4.3 Genetic Algorithm (core/evolve.py)

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| FR3.1 | init_population: generate N random schedules                            |
| FR3.2 | tournament_select: pick best of k random candidates by score            |
| FR3.3 | crossover: single-point on ordered course list                          |
| FR3.4 | mutate: per-gene random reassignment with given probability             |
| FR3.5 | run_ga: full loop with elitism (keep top 2 each generation)             |
| FR3.6 | Return best schedule and list of best scores per generation             |
| FR3.7 | No imports from tkinter or app.py                                       |

### 4.4 Tkinter UI (app.py)

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| FR4.1 | Window: 900x620, title "Exam Scheduler"                                 |
| FR4.2 | Input fields for: pop_size, max_gen, mutation_rate, tournament_k        |
| FR4.3 | Run button — disabled during execution                                  |
| FR4.4 | Status label updated before and after GA runs                           |
| FR4.5 | GA runs in a background thread (threading.Thread)                       |
| FR4.6 | Thread communicates back to UI using root.after(0, callback)            |
| FR4.7 | ScrolledText shows day-grid schedule after each run                     |
| FR4.8 | "Show Plot" opens convergence.png in a new Toplevel window              |
| FR4.9 | "Save" writes best_schedule.txt and run_log.csv to output/              |
| FR4.10| Load dataset on startup; show error and exit if file not found          |

### 4.5 Output Files (output/)

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| FR5.1 | best_schedule.txt: day-grid format, one day per section                 |
| FR5.2 | run_log.csv: columns generation, best_penalty                           |
| FR5.3 | convergence.png: line chart, dpi=150, saved with savefig not show       |
| FR5.4 | output/ directory created automatically if it does not exist            |

---

## 5. Non-Functional Requirements

| ID    | Requirement                                                              |
|-------|--------------------------------------------------------------------------|
| NF1   | No GA libraries — only openpyxl, tkinter, matplotlib, csv, random, threading|
| NF2   | UI stays responsive during GA execution (non-blocking thread)           |
| NF3   | penalty.py has no side effects — testable in isolation                  |
| NF4   | evolve.py has no dependency on UI code                                  |
| NF5   | All file writes go to output/ — data/ is read-only                      |
| NF6   | Dataset file path is configurable (not hardcoded in multiple places)    |

---

## 6. GA Parameters

| Parameter      | Type  | Default | Description                                  |
|----------------|-------|---------|----------------------------------------------|
| pop_size       | int   | 100     | Number of schedules in each generation       |
| max_gen        | int   | 500     | Maximum number of generations to run        |
| mutation_rate  | float | 0.05    | Probability of reassigning any single gene  |
| tournament_k   | int   | 5       | Pool size for tournament selection           |

These are tunable from the UI and affect convergence rate.
The report must include plots comparing at least two values per parameter.

---

## 7. Slot ID Reference

Slot IDs follow the pattern `D{day}S{slot}` where day is 1-6 and slot is 1-3.

| Slot | Day | Time        |
|------|-----|-------------|
| D1S1 | 1   | 09:00-11:00 |
| D1S2 | 1   | 12:00-14:00 |
| D1S3 | 1   | 15:00-17:00 |
| D2S1 | 2   | 09:00-11:00 |
| D2S2 | 2   | 12:00-14:00 |
| D2S3 | 2   | 15:00-17:00 |
| D3S1 | 3   | 09:00-11:00 |
| D3S2 | 3   | 12:00-14:00 |
| D3S3 | 3   | 15:00-17:00 |
| D4S1 | 4   | 09:00-11:00 |
| D4S2 | 4   | 12:00-14:00 |
| D4S3 | 4   | 15:00-17:00 |
| D5S1 | 5   | 09:00-11:00 |
| D5S2 | 5   | 12:00-14:00 |
| D5S3 | 5   | 15:00-17:00 |
| D6S1 | 6   | 09:00-11:00 |
| D6S2 | 6   | 12:00-14:00 |
| D6S3 | 6   | 15:00-17:00 |

Parse day and slot from a slot ID:
```python
day  = int(slot_id[1])   # "D3S2" -> 3
slot = int(slot_id[3])   # "D3S2" -> 2
```

---

## 8. Test Cases

### 8.1 Parser

- load_data() returns a list of exactly 22 courses
- conflict_table has 22 x 22 entries (diagonal = 0)
- Total enrollment pair count = 481
- Student count = 95

### 8.2 Penalty function

- Bad schedule (from Sample_Bad_Schedule sheet) must score > 0
- COMP3320 and COMP3330 are both in D3S1 in the bad schedule —
  this alone should add at least 1000 to the score
- A perfect schedule (zero hard violations) must score 0 on HC1, HC2, HC3

### 8.3 GA

- Score history list length = max_gen
- Final score <= initial score (GA is not making things worse)
- Best schedule dict has exactly 22 keys
- All values in best schedule are valid slot IDs

### 8.4 UI

- Window opens without error when dataset.xlsx is present
- Run button disabled during execution, re-enabled after
- ScrolledText updated after run completes
- output/ directory created on first save
