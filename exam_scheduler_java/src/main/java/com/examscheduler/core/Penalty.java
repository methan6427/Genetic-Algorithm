package com.examscheduler.core;

import java.util.*;

public class Penalty {

    /**
     * Returns total penalty for a schedule. 0 = perfect, higher = worse.
     * Pure function — no I/O, no side effects.
     */
    public static int score(
        Map<String, String> schedule,
        Map<String, Map<String, Integer>> conflictTable,
        Map<String, List<String>> studentCourses
    ) {
        int total = 0;

        // Invert: slot -> list of courses in that slot
        Map<String, List<String>> slotToCourses = new HashMap<>();
        for (Map.Entry<String, String> e : schedule.entrySet())
            slotToCourses.computeIfAbsent(e.getValue(), k -> new ArrayList<>()).add(e.getKey());

        // HC1: same-slot conflict pairs — add sharedStudents * 1000
        for (List<String> inSlot : slotToCourses.values()) {
            int n = inSlot.size();
            for (int i = 0; i < n; i++) {
                for (int j = i + 1; j < n; j++) {
                    String a = inSlot.get(i);
                    String b = inSlot.get(j);
                    int shared = conflictTable.getOrDefault(a, Map.of()).getOrDefault(b, 0);
                    total += shared * 1000;
                }
            }
        }

        // Per-student day-load checks
        for (List<String> enrolled : studentCourses.values()) {
            Map<Integer, Integer> dayCount = new HashMap<>();
            for (String course : enrolled) {
                String slot = schedule.get(course);
                if (slot != null) {
                    int day = slot.charAt(1) - '0'; // "D3S1" -> 3
                    dayCount.merge(day, 1, Integer::sum);
                }
            }

            for (int count : dayCount.values()) {
                if (count > 2)      total += 800; // HC2: >2 exams same day
                else if (count == 2) total +=  50; // SC1: exactly 2 exams same day
            }

            // HC3: 4+ exams across two consecutive days
            List<Integer> sorted = new ArrayList<>(dayCount.keySet());
            Collections.sort(sorted);
            for (int i = 0; i < sorted.size() - 1; i++) {
                int d1 = sorted.get(i), d2 = sorted.get(i + 1);
                if (d2 == d1 + 1 && dayCount.get(d1) + dayCount.get(d2) >= 4)
                    total += 500;
            }
        }

        // SC2: each day beyond 5 costs 100
        long daysUsed = schedule.values().stream()
            .mapToInt(s -> s.charAt(1) - '0')
            .distinct().count();
        if (daysUsed > 5) total += (int)(daysUsed - 5) * 100;

        return total;
    }
}
