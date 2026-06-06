"""Calculate penalty score for a schedule."""


def score(schedule: dict, conflict_table: dict, student_courses: dict) -> int:
    """Return total penalty: 0 is perfect, higher is worse."""
    total = 0

    # Group courses by their slot so we can check for same-slot conflicts
    slot_to_courses: dict[str, list[str]] = {}
    for course, slot in schedule.items():
        slot_to_courses.setdefault(slot, []).append(course)

    # Add 1000 for every pair of courses in the same slot that share students
    for courses_in_slot in slot_to_courses.values():
        n = len(courses_in_slot)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = courses_in_slot[i], courses_in_slot[j]
                shared = conflict_table.get(a, {}).get(b, 0)
                total += shared * 1000  # Hard constraint: no shared-student clash

    # Check each student's exam spread across days
    for enrolled in student_courses.values():
        day_count: dict[int, int] = {}
        for course in enrolled:
            slot = schedule.get(course)
            if slot is not None:
                day = int(slot[1])  # Day number is second character in slot ID
                day_count[day] = day_count.get(day, 0) + 1

        for day, count in day_count.items():
            if count > 2:
                total += 800  # Hard: more than 2 exams in one day is too many
            elif count == 2:
                total += 50   # Soft: 2 exams in one day is not ideal

        # Check if student has 4+ exams on two days in a row
        days_sorted = sorted(day_count)
        for i in range(len(days_sorted) - 1):
            d1, d2 = days_sorted[i], days_sorted[i + 1]
            if d2 == d1 + 1 and day_count[d1] + day_count[d2] >= 4:
                total += 500  # Hard: too many exams on back-to-back days

    # Add penalty if the schedule uses more than 5 days
    days_used = len({int(s[1]) for s in schedule.values()})
    if days_used > 5:
        total += (days_used - 5) * 100  # Soft: each extra day costs 100

    return total


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from core.parse import load_data, load_bad_schedule

    data_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "ga_exam_timetable_dataset.xlsx"
    )
    courses, conflict_table, student_courses = load_data(data_path)
    bad = load_bad_schedule(data_path)

    penalty = score(bad, conflict_table, student_courses)
    print(f"Bad schedule penalty: {penalty}")

    comp3320_comp3330 = conflict_table.get("COMP3320", {}).get("COMP3330", 0)
    print(f"COMP3320/COMP3330 shared students: {comp3320_comp3330}")
    if bad.get("COMP3320") == bad.get("COMP3330"):
        print(f"Both in slot {bad['COMP3320']} -> HC1 contribution: {comp3320_comp3330 * 1000}")
