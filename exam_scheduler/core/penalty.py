"""Pure penalty scoring function for exam schedules."""


def score(schedule: dict, conflict_table: dict, student_courses: dict) -> int:
    """
    Returns total penalty for a given schedule. 0 = perfect, higher = worse.

    schedule:        { course_code: slot_id }
    conflict_table:  { course_a: { course_b: shared_student_count } }
    student_courses: { student_id: [course_code, ...] }
    """
    total = 0

    # Invert schedule: slot_id -> list of courses in that slot
    slot_to_courses: dict[str, list[str]] = {}
    for course, slot in schedule.items():
        slot_to_courses.setdefault(slot, []).append(course)

    # HC1: for every same-slot course pair, add shared_students * 1000
    for courses_in_slot in slot_to_courses.values():
        n = len(courses_in_slot)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = courses_in_slot[i], courses_in_slot[j]
                shared = conflict_table.get(a, {}).get(b, 0)
                total += shared * 1000

    # Per-student day-load constraints
    for enrolled in student_courses.values():
        # Count this student's exams per day
        day_count: dict[int, int] = {}
        for course in enrolled:
            slot = schedule.get(course)
            if slot is not None:
                day = int(slot[1])  # "D3S1" -> 3
                day_count[day] = day_count.get(day, 0) + 1

        for day, count in day_count.items():
            if count > 2:
                total += 800   # HC2: more than 2 exams same day
            elif count == 2:
                total += 50    # SC1: exactly 2 exams same day

        # HC3: 4+ exams across two consecutive days -> 500 per student
        days_sorted = sorted(day_count)
        for i in range(len(days_sorted) - 1):
            d1, d2 = days_sorted[i], days_sorted[i + 1]
            if d2 == d1 + 1 and day_count[d1] + day_count[d2] >= 4:
                total += 500

    # SC2: each day beyond 5 costs 100
    days_used = len({int(s[1]) for s in schedule.values()})
    if days_used > 5:
        total += (days_used - 5) * 100

    return total


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.parse import load_data, load_bad_schedule

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.xlsx")
    courses, conflict_table, student_courses = load_data(data_path)
    bad = load_bad_schedule(data_path)

    penalty = score(bad, conflict_table, student_courses)
    print(f"Bad schedule penalty: {penalty}")

    comp3320_comp3330 = conflict_table.get("COMP3320", {}).get("COMP3330", 0)
    print(f"COMP3320/COMP3330 shared students: {comp3320_comp3330}")
    if bad.get("COMP3320") == bad.get("COMP3330"):
        print(f"Both in slot {bad['COMP3320']} -> HC1 contribution: {comp3320_comp3330 * 1000}")
