package com.examscheduler.core;

import javafx.embed.swing.SwingFXUtils;
import javafx.scene.Group;
import javafx.scene.Scene;
import javafx.scene.chart.*;
import javafx.scene.image.WritableImage;
import javafx.scene.paint.Color;
import javafx.scene.SnapshotParameters;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public class Report {

    private static final Map<Integer, String> SLOT_TIMES = Map.of(
        1, "09:00-11:00", 2, "12:00-14:00", 3, "15:00-17:00"
    );

    /** Writes schedule in day-grid format to a .txt file. */
    public static void saveSchedule(Map<String, String> schedule, String filepath) throws IOException {
        ensureDir(filepath);
        Map<String, List<String>> daySlots = new TreeMap<>();
        for (Map.Entry<String, String> e : schedule.entrySet())
            daySlots.computeIfAbsent(e.getValue(), k -> new ArrayList<>()).add(e.getKey());

        try (PrintWriter pw = new PrintWriter(new FileWriter(filepath))) {
            for (int day = 1; day <= 6; day++) {
                boolean printed = false;
                for (int s = 1; s <= 3; s++) {
                    String slot = "D" + day + "S" + s;
                    List<String> courses = daySlots.get(slot);
                    if (courses != null) {
                        if (!printed) { pw.println("Day " + day); printed = true; }
                        Collections.sort(courses);
                        pw.println("  " + SLOT_TIMES.get(s) + " : " + String.join(", ", courses));
                    }
                }
            }
        }
    }

    /** Writes run_log.csv with columns generation,best_penalty. */
    public static void saveLog(List<Integer> history, String filepath) throws IOException {
        ensureDir(filepath);
        try (PrintWriter pw = new PrintWriter(new FileWriter(filepath))) {
            pw.println("generation,best_penalty");
            for (int i = 0; i < history.size(); i++)
                pw.println(i + "," + history.get(i));
        }
    }

    /**
     * Saves convergence chart to PNG.
     * Must be called on the JavaFX Application Thread.
     */
    public static void savePlot(List<Integer> history, String filepath) throws IOException {
        ensureDir(filepath);
        LineChart<Number, Number> chart = buildConvergenceChart(history);
        chart.setPrefSize(750, 480);

        // Attach to an unshown scene so CSS and layout can run
        new Scene(new Group(chart));
        chart.applyCss();
        chart.layout();

        SnapshotParameters params = new SnapshotParameters();
        params.setFill(Color.WHITE);
        WritableImage image = chart.snapshot(params, null);

        BufferedImage buffered = SwingFXUtils.fromFXImage(image, null);
        ImageIO.write(buffered, "png", new File(filepath));
    }

    /** Builds a reusable JavaFX LineChart from a score history list. */
    public static LineChart<Number, Number> buildConvergenceChart(List<Integer> history) {
        NumberAxis xAxis = new NumberAxis();
        NumberAxis yAxis = new NumberAxis();
        xAxis.setLabel("Generation");
        yAxis.setLabel("Best Penalty");

        LineChart<Number, Number> chart = new LineChart<>(xAxis, yAxis);
        chart.setTitle("GA Convergence");
        chart.setLegendVisible(false);
        chart.setAnimated(false);
        chart.setCreateSymbols(false);

        XYChart.Series<Number, Number> series = new XYChart.Series<>();
        series.setName("Best Penalty");
        for (int i = 0; i < history.size(); i++)
            series.getData().add(new XYChart.Data<>(i, history.get(i)));
        chart.getData().add(series);

        return chart;
    }

    private static void ensureDir(String filepath) throws IOException {
        Path parent = Paths.get(filepath).getParent();
        if (parent != null) Files.createDirectories(parent);
    }
}
