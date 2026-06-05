package com.examscheduler.core;

import java.util.*;

public class GeneticAlgorithm {

    public record GaConfig(int popSize, int maxGen, double mutationRate, int tournamentK) {}
    public record GaResult(Map<String, String> bestSchedule, List<Integer> scoreHistory) {}

    private final Random rng = new Random();

    public List<Map<String, String>> initPopulation(int size, List<String> courses, List<String> slots) {
        List<Map<String, String>> pop = new ArrayList<>(size);
        for (int i = 0; i < size; i++) {
            Map<String, String> ind = new LinkedHashMap<>();
            for (String c : courses) ind.put(c, slots.get(rng.nextInt(slots.size())));
            pop.add(ind);
        }
        return pop;
    }

    public Map<String, String> tournamentSelect(
        List<Map<String, String>> population, List<Integer> scores, int k
    ) {
        k = Math.min(k, population.size());
        List<Integer> all = new ArrayList<>();
        for (int i = 0; i < population.size(); i++) all.add(i);
        Collections.shuffle(all, rng);
        int best = all.get(0);
        for (int i = 1; i < k; i++)
            if (scores.get(all.get(i)) < scores.get(best)) best = all.get(i);
        return new LinkedHashMap<>(population.get(best));
    }

    public Map<String, String> crossover(
        Map<String, String> parentA, Map<String, String> parentB, List<String> courses
    ) {
        int point = 1 + rng.nextInt(courses.size() - 1);
        Map<String, String> child = new LinkedHashMap<>();
        for (int i = 0; i < courses.size(); i++) {
            String c = courses.get(i);
            child.put(c, i < point ? parentA.get(c) : parentB.get(c));
        }
        return child;
    }

    public Map<String, String> mutate(Map<String, String> schedule, List<String> slots, double rate) {
        Map<String, String> result = new LinkedHashMap<>();
        for (Map.Entry<String, String> e : schedule.entrySet()) {
            String slot = rng.nextDouble() < rate ? slots.get(rng.nextInt(slots.size())) : e.getValue();
            result.put(e.getKey(), slot);
        }
        return result;
    }

    public GaResult runGa(
        List<String> courses,
        List<String> slots,
        Map<String, Map<String, Integer>> conflictTable,
        Map<String, List<String>> studentCourses,
        GaConfig config
    ) {
        List<Map<String, String>> population = initPopulation(config.popSize(), courses, slots);
        List<Integer> history = new ArrayList<>(config.maxGen());
        Map<String, String> bestSchedule = null;
        int bestScore = Integer.MAX_VALUE;

        for (int gen = 0; gen < config.maxGen(); gen++) {
            // Score
            List<Integer> scores = new ArrayList<>(population.size());
            for (Map<String, String> ind : population)
                scores.add(Penalty.score(ind, conflictTable, studentCourses));

            // Track global best
            int genBest = 0;
            for (int i = 1; i < scores.size(); i++)
                if (scores.get(i) < scores.get(genBest)) genBest = i;
            if (scores.get(genBest) < bestScore) {
                bestScore    = scores.get(genBest);
                bestSchedule = new LinkedHashMap<>(population.get(genBest));
            }
            history.add(bestScore);

            // Elitism: keep top 2
            List<Integer> ranked = new ArrayList<>();
            for (int i = 0; i < population.size(); i++) ranked.add(i);
            final List<Integer> finalScores = scores;
            ranked.sort(Comparator.comparingInt(finalScores::get));

            List<Map<String, String>> next = new ArrayList<>(config.popSize());
            next.add(new LinkedHashMap<>(population.get(ranked.get(0))));
            next.add(new LinkedHashMap<>(population.get(ranked.get(1))));

            while (next.size() < config.popSize()) {
                Map<String, String> pa = tournamentSelect(population, scores, config.tournamentK());
                Map<String, String> pb = tournamentSelect(population, scores, config.tournamentK());
                Map<String, String> child = crossover(pa, pb, courses);
                child = mutate(child, slots, config.mutationRate());
                next.add(child);
            }
            population = next;
        }

        return new GaResult(bestSchedule, history);
    }
}
