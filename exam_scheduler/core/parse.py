"""Loads dataset.xlsx and builds data structures for the GA."""
import openpyxl


def load_data(filepath: str) -> tuple[list, dict, dict]:
    """
    Opens the xlsx and extracts course list, conflict table, and student enrollments.
    Returns (courses, conflict_table, student_courses).
      courses:         list[str] of 22 course codes in catalog order
      conflict_table:  dict[str][str] -> int  (shared student count for each pair)
      student_courses: dict[str] -> list[str] (courses per student)
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)

    # --- Course_Catalog sheet ---
    ws_catalog = wb["Course_Catalog"]
    courses = []
    for row in ws_catalog.iter_rows(min_row=2, values_only=True):
        code = row[0]
        if code is not None:
            courses.append(str(code).strip())

    # --- Enrollment_Pairs sheet ---
    ws_enroll = wb["Enrollment_Pairs"]
    student_courses: dict[str, list[str]] = {}
    for row in ws_enroll.iter_rows(min_row=2, values_only=True):
        if row[0] is None or row[1] is None:
            continue
        sid = str(row[0]).strip()
        course = str(row[1]).strip()
        if sid not in student_courses:
            student_courses[sid] = []
        student_courses[sid].append(course)

    wb.close()

    # Build conflict_table[A][B] = number of students enrolled in both A and B
    conflict_table: dict[str, dict[str, int]] = {
        c: {d: 0 for d in courses} for c in courses
    }
    for sid, enrolled in student_courses.items():
        for i in range(len(enrolled)):
            for j in range(i + 1, len(enrolled)):
                a, b = enrolled[i], enrolled[j]
                if a in conflict_table and b in conflict_table.get(a, {}):
                    conflict_table[a][b] += 1
                    conflict_table[b][a] += 1

    return courses, conflict_table, student_courses


def load_slots() -> list[str]:
    """Returns all 18 valid slot IDs in day-then-slot order."""
    return [f"D{d}S{s}" for d in range(1, 7) for s in range(1, 4)]


def load_bad_schedule(filepath: str) -> dict:
    """
    Reads the Sample_Bad_Schedule sheet.
    Returns { course_code: slot_id }.
    """
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb["Sample_Bad_Schedule"]
    schedule = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None or row[1] is None:
            continue
        schedule[str(row[0]).strip()] = str(row[1]).strip()
    wb.close()
    return schedule
