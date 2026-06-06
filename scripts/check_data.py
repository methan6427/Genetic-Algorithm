"""Verify dataset statistics reported in the ODT."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'exam_scheduler'))
from core.parse import load_data

data_path = r"c:\akaza\General\Antigravit Projects\AI-Project\exam_scheduler\data\ga_exam_timetable_dataset.xlsx"
courses, conflict_table, student_courses = load_data(data_path)

print(f"Courses: {len(courses)}")
print(f"Students: {len(student_courses)}")
total_enroll = sum(len(v) for v in student_courses.values())
print(f"Total enrollments: {total_enroll}")
min_e = min(len(v) for v in student_courses.values())
max_e = max(len(v) for v in student_courses.values())
print(f"Enrollments per student: {min_e}–{max_e}")
