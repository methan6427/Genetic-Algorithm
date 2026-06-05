package com.examscheduler;

import com.examscheduler.core.*;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.*;
import javafx.scene.Scene;
import javafx.scene.chart.LineChart;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.text.Font;
import javafx.stage.*;

import java.io.File;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.CompletableFuture;

public class App extends Application {

    private static final String BASE_DIR   = System.getProperty("user.dir");
    private static final String DATA_PATH  = BASE_DIR + File.separator + "data"   + File.separator + "dataset.xlsx";
    private static final String OUTPUT_DIR = BASE_DIR + File.separator + "output";

    private static final Map<Integer, String> SLOT_TIMES = Map.of(
        1, "09:00-11:00", 2, "12:00-14:00", 3, "15:00-17:00"
    );

    // Data loaded on startup
    private List<String> courses;
    private List<String> slots;
    private Map<String, Map<String, Integer>> conflictTable;
    private Map<String, List<String>> studentCourses;

    // GA results — written from FX thread after run completes
    private Map<String, String> lastSchedule;
    private List<Integer>       lastHistory;

    // UI controls shared between methods
    private TextField popSizeField, maxGenField, mutRateField, tournKField;
    private Button    runButton;
    private Label     statusLabel;
    private TextArea  scheduleArea;

    // ── Application entry ─────────────────────────────────────────────────────

    @Override
    public void start(Stage stage) throws Exception {
        if (!new File(DATA_PATH).exists()) {
            new Alert(Alert.AlertType.ERROR,
                "Dataset not found:\n" + DATA_PATH +
                "\n\nPlace dataset.xlsx in the data/ folder.",
                ButtonType.OK).showAndWait();
            Platform.exit();
            return;
        }

        Parser.DataSet ds = Parser.loadData(DATA_PATH);
        courses       = ds.courses();
        conflictTable = ds.conflictTable();
        studentCourses = ds.studentCourses();
        slots          = Parser.loadSlots();

        stage.setTitle("Exam Scheduler");
        stage.setMinWidth(950);
        stage.setMinHeight(640);
        stage.setScene(new Scene(buildRoot(), 950, 640));
        stage.show();
    }

    // ── Layout ────────────────────────────────────────────────────────────────

    private HBox buildRoot() {
        HBox root = new HBox(8);
        root.setPadding(new Insets(14));

        VBox left  = buildLeftPanel();
        Separator sep = new Separator(Orientation.VERTICAL);
        VBox right = buildRightPanel();
        HBox.setHgrow(right, Priority.ALWAYS);

        root.getChildren().addAll(left, sep, right);
        return root;
    }

    private VBox buildLeftPanel() {
        VBox panel = new VBox(10);
        panel.setPadding(new Insets(4, 12, 4, 4));
        panel.setPrefWidth(220);

        Label title = new Label("Settings");
        title.setStyle("-fx-font-size:14px; -fx-font-weight:bold;");

        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(8);

        popSizeField = addRow(grid, "Population Size",  "100", 0);
        maxGenField  = addRow(grid, "Max Generations",  "500", 1);
        mutRateField = addRow(grid, "Mutation Rate",   "0.05", 2);
        tournKField  = addRow(grid, "Tournament K",      "5", 3);

        runButton = new Button("Run GA");
        runButton.setPrefWidth(170);
        runButton.setOnAction(e -> onRunGA());

        statusLabel = new Label("Ready");
        statusLabel.setWrapText(true);
        statusLabel.setPrefWidth(210);

        panel.getChildren().addAll(title, grid, runButton, statusLabel);
        return panel;
    }

    private TextField addRow(GridPane grid, String label, String def, int row) {
        grid.add(new Label(label + ":"), 0, row);
        TextField tf = new TextField(def);
        tf.setPrefWidth(85);
        grid.add(tf, 1, row);
        return tf;
    }

    private VBox buildRightPanel() {
        VBox panel = new VBox(10);
        panel.setPadding(new Insets(4, 4, 4, 8));
        VBox.setVgrow(panel, Priority.ALWAYS);

        Label title = new Label("Results");
        title.setStyle("-fx-font-size:14px; -fx-font-weight:bold;");

        scheduleArea = new TextArea();
        scheduleArea.setEditable(false);
        scheduleArea.setFont(Font.font("Courier New", 12));
        VBox.setVgrow(scheduleArea, Priority.ALWAYS);

        Button showPlotBtn = new Button("Show Plot");
        Button saveBtn     = new Button("Save Results");
        showPlotBtn.setOnAction(e -> onShowPlot());
        saveBtn.setOnAction(e -> onSaveResults());

        HBox buttons = new HBox(8, showPlotBtn, saveBtn);
        buttons.setAlignment(Pos.CENTER_LEFT);

        panel.getChildren().addAll(title, scheduleArea, buttons);
        return panel;
    }

    // ── Actions ───────────────────────────────────────────────────────────────

    private void onRunGA() {
        int    popSize, maxGen, tournK;
        double mutRate;
        try {
            popSize = Integer.parseInt(popSizeField.getText().trim());
            maxGen  = Integer.parseInt(maxGenField.getText().trim());
            mutRate = Double.parseDouble(mutRateField.getText().trim());
            tournK  = Integer.parseInt(tournKField.getText().trim());
        } catch (NumberFormatException ex) {
            alert(Alert.AlertType.ERROR, "All fields must be numeric.");
            return;
        }

        runButton.setDisable(true);
        statusLabel.setText("Running...");
        scheduleArea.clear();

        GeneticAlgorithm.GaConfig config =
            new GeneticAlgorithm.GaConfig(popSize, maxGen, mutRate, tournK);

        CompletableFuture.runAsync(() -> {
            GeneticAlgorithm ga = new GeneticAlgorithm();
            GeneticAlgorithm.GaResult result =
                ga.runGa(courses, slots, conflictTable, studentCourses, config);

            Platform.runLater(() -> {
                lastSchedule = result.bestSchedule();
                lastHistory  = result.scoreHistory();

                runButton.setDisable(false);
                statusLabel.setText("Done — penalty: " + lastHistory.get(lastHistory.size() - 1));
                scheduleArea.setText(formatSchedule(lastSchedule));

                try {
                    Files.createDirectories(Paths.get(OUTPUT_DIR));
                    Report.savePlot(lastHistory, OUTPUT_DIR + File.separator + "convergence.png");
                } catch (Exception ex) {
                    System.err.println("Plot save failed: " + ex.getMessage());
                }
            });
        });
    }

    private void onShowPlot() {
        if (lastHistory == null) {
            alert(Alert.AlertType.INFORMATION, "Run the GA first.");
            return;
        }
        Stage plotStage = new Stage();
        plotStage.setTitle("Convergence Plot");

        LineChart<Number, Number> chart = Report.buildConvergenceChart(lastHistory);
        plotStage.setScene(new Scene(chart, 780, 500));
        plotStage.show();
    }

    private void onSaveResults() {
        if (lastSchedule == null) {
            alert(Alert.AlertType.INFORMATION, "Run the GA first.");
            return;
        }
        try {
            Files.createDirectories(Paths.get(OUTPUT_DIR));
            Report.saveSchedule(lastSchedule, OUTPUT_DIR + File.separator + "best_schedule.txt");
            Report.saveLog(lastHistory,        OUTPUT_DIR + File.separator + "run_log.csv");
            alert(Alert.AlertType.INFORMATION, "Files saved to:\n" + OUTPUT_DIR);
        } catch (Exception ex) {
            alert(Alert.AlertType.ERROR, "Save failed: " + ex.getMessage());
        }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private String formatSchedule(Map<String, String> schedule) {
        Map<String, List<String>> daySlots = new HashMap<>();
        for (Map.Entry<String, String> e : schedule.entrySet())
            daySlots.computeIfAbsent(e.getValue(), k -> new ArrayList<>()).add(e.getKey());

        StringBuilder sb = new StringBuilder();
        for (int day = 1; day <= 6; day++) {
            boolean printed = false;
            for (int s = 1; s <= 3; s++) {
                String slot = "D" + day + "S" + s;
                List<String> cs = daySlots.get(slot);
                if (cs != null) {
                    if (!printed) { sb.append("Day ").append(day).append("\n"); printed = true; }
                    Collections.sort(cs);
                    sb.append("  ").append(SLOT_TIMES.get(s))
                      .append(" : ").append(String.join(", ", cs)).append("\n");
                }
            }
        }
        return sb.toString().trim();
    }

    private static void alert(Alert.AlertType type, String msg) {
        new Alert(type, msg, ButtonType.OK).showAndWait();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
