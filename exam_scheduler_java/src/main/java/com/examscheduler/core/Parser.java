package com.examscheduler.core;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.*;
import java.util.*;

public class Parser {

    public record DataSet(
        List<String> courses,
        Map<String, Map<String, Integer>> conflictTable,
        Map<String, List<String>> studentCourses
    ) {}

    public static DataSet loadData(String filepath) throws IOException {
        try (FileInputStream fis = new FileInputStream(filepath);
             Workbook wb = new XSSFWorkbook(fis)) {

            // Course_Catalog sheet
            Sheet catalogSheet = wb.getSheet("Course_Catalog");
            List<String> courses = new ArrayList<>();
            for (Row row : catalogSheet) {
                if (row.getRowNum() == 0) continue;
                Cell cell = row.getCell(0);
                if (cell != null) {
                    String code = cellString(cell);
                    if (!code.isEmpty()) courses.add(code);
                }
            }

            // Enrollment_Pairs sheet
            Sheet enrollSheet = wb.getSheet("Enrollment_Pairs");
            Map<String, List<String>> studentCourses = new LinkedHashMap<>();
            for (Row row : enrollSheet) {
                if (row.getRowNum() == 0) continue;
                Cell sidCell    = row.getCell(0);
                Cell courseCell = row.getCell(1);
                if (sidCell == null || courseCell == null) continue;
                String sid    = cellString(sidCell);
                String course = cellString(courseCell);
                if (sid.isEmpty() || course.isEmpty()) continue;
                studentCourses.computeIfAbsent(sid, k -> new ArrayList<>()).add(course);
            }

            // Build conflict table: conflictTable[A][B] = shared student count
            Map<String, Map<String, Integer>> conflictTable = new HashMap<>();
            for (String c : courses) {
                Map<String, Integer> row = new HashMap<>();
                for (String d : courses) row.put(d, 0);
                conflictTable.put(c, row);
            }
            for (List<String> enrolled : studentCourses.values()) {
                for (int i = 0; i < enrolled.size(); i++) {
                    for (int j = i + 1; j < enrolled.size(); j++) {
                        String a = enrolled.get(i);
                        String b = enrolled.get(j);
                        if (conflictTable.containsKey(a) && conflictTable.get(a).containsKey(b)) {
                            conflictTable.get(a).merge(b, 1, Integer::sum);
                            conflictTable.get(b).merge(a, 1, Integer::sum);
                        }
                    }
                }
            }

            return new DataSet(courses, conflictTable, studentCourses);
        }
    }

    public static List<String> loadSlots() {
        List<String> slots = new ArrayList<>(18);
        for (int d = 1; d <= 6; d++)
            for (int s = 1; s <= 3; s++)
                slots.add("D" + d + "S" + s);
        return slots;
    }

    public static Map<String, String> loadBadSchedule(String filepath) throws IOException {
        try (FileInputStream fis = new FileInputStream(filepath);
             Workbook wb = new XSSFWorkbook(fis)) {
            Sheet sheet = wb.getSheet("Sample_Bad_Schedule");
            Map<String, String> schedule = new LinkedHashMap<>();
            for (Row row : sheet) {
                if (row.getRowNum() == 0) continue;
                Cell courseCell = row.getCell(0);
                Cell slotCell   = row.getCell(1);
                if (courseCell == null || slotCell == null) continue;
                String course = cellString(courseCell);
                String slot   = cellString(slotCell);
                if (!course.isEmpty() && !slot.isEmpty()) schedule.put(course, slot);
            }
            return schedule;
        }
    }

    private static String cellString(Cell cell) {
        return switch (cell.getCellType()) {
            case STRING  -> cell.getStringCellValue().trim();
            case NUMERIC -> String.valueOf((long) cell.getNumericCellValue()).trim();
            default      -> "";
        };
    }
}
