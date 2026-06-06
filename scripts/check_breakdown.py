"""Compute exact penalty breakdown for the bad schedule."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'exam_scheduler'))
from core.parse import load_data, load_bad_schedule

data_path = r"c:\akaza\General\Antigravit Projects\AI-Project\exam_scheduler\data\ga_exam_timetable_dataset.xlsx"
courses, conflict_table, student_courses = load_data(data_path)
schedule = load_bad_schedule(data_path)

# HC1
slot_to_courses = {}
for course, slot in schedule.items():
    slot_to_courses.setdefault(slot, []).append(course)

hc1 = 0
for courses_in_slot in slot_to_courses.values():
    n = len(courses_in_slot)
    for i in range(n):
        for j in range(i+1, n):
            a, b = courses_in_slot[i], courses_in_slot[j]
            shared = conflict_table.get(a, {}).get(b, 0)
            hc1 += shared * 1000

# Per-student constraints
hc2 = hc3 = sc1 = 0
for enrolled in student_courses.values():
    day_count = {}
    for course in enrolled:
        slot = schedule.get(course)
        if slot:
            d = int(slot[1])
            day_count[d] = day_count.get(d, 0) + 1
    for day, count in day_count.items():
        if count > 2:
            hc2 += 800
        elif count == 2:
            sc1 += 50
    days_sorted = sorted(day_count)
    for i in range(len(days_sorted)-1):
        d1, d2 = days_sorted[i], days_sorted[i+1]
        if d2 == d1+1 and day_count[d1] + day_count[d2] >= 4:
            hc3 += 500

# SC2
days_used = len({int(s[1]) for s in schedule.values()})
sc2 = (days_used - 5) * 100 if days_used > 5 else 0

total = hc1 + hc2 + hc3 + sc1 + sc2
print(f"HC1 (same-slot):  {hc1:,}")
print(f"HC2 (>2/day):     {hc2:,}")
print(f"HC3 (consec.):    {hc3:,}")
print(f"SC1 (2/day):      {sc1:,}")
print(f"SC2 (days>5):     {sc2:,}")
print(f"Total:            {total:,}")
print(f"Days used:        {days_used}")
