"""Genetic algorithm (GA) functions for exam scheduling."""
import random


def init_population(size: int, courses: list, slots: list) -> list[dict]:
    """Create random schedules: each course gets a random slot."""
    # Each individual in the population is one possible schedule
    return [
        {course: random.choice(slots) for course in courses}
        for _ in range(size)
    ]


def tournament_select(population: list, scores: list, k: int) -> dict:
    """Pick k random schedules and return the best one."""
    k = min(k, len(population))
    indices = random.sample(range(len(population)), k)
    # The best individual has the lowest penalty score
    best = min(indices, key=lambda i: scores[i])
    return dict(population[best])


def crossover(parent_a: dict, parent_b: dict, courses: list) -> dict:
    """Create new schedule by mixing genes from both parents."""
    # Split courses at a random point; take left from parent A, right from parent B
    point = random.randint(1, len(courses) - 1)
    child = {}
    for i, course in enumerate(courses):
        child[course] = parent_a[course] if i < point else parent_b[course]
    return child


def mutate(schedule: dict, slots: list, rate: float) -> dict:
    """Randomly change some courses' slots with given probability."""
    # Each course slot is replaced with a random slot based on mutation rate
    return {
        course: (random.choice(slots) if random.random() < rate else slot)
        for course, slot in schedule.items()
    }


def run_ga(
    courses: list,
    slots: list,
    conflict_table: dict,
    student_courses: dict,
    config: dict,
) -> tuple[dict, list[int]]:
    """Run genetic algorithm and return (best schedule, list of best scores per generation)."""
    from core.penalty import score as penalty_score

    # Read GA settings from config dict
    pop_size = config["pop_size"]
    max_gen = config["max_gen"]
    mutation_rate = config["mutation_rate"]
    tournament_k = config["tournament_k"]

    population = init_population(pop_size, courses, slots)
    score_history: list[int] = []
    best_schedule: dict = {}
    best_score = float("inf")  # Start with the worst possible score

    for _ in range(max_gen):
        # Score every schedule in the current population
        scores = [
            penalty_score(ind, conflict_table, student_courses)
            for ind in population
        ]

        # Update the best schedule if this generation improved
        gen_best_idx = min(range(pop_size), key=lambda i: scores[i])
        if scores[gen_best_idx] < best_score:
            best_score = scores[gen_best_idx]
            best_schedule = dict(population[gen_best_idx])

        score_history.append(best_score)

        # Sort population by score so we can keep the top two (elitism)
        ranked = sorted(range(pop_size), key=lambda i: scores[i])
        new_population = [dict(population[ranked[0]]), dict(population[ranked[1]])]  # Keep best 2

        # Fill the rest of the new population with children
        while len(new_population) < pop_size:
            pa = tournament_select(population, scores, tournament_k)
            pb = tournament_select(population, scores, tournament_k)
            child = crossover(pa, pb, courses)
            child = mutate(child, slots, mutation_rate)
            new_population.append(child)

        population = new_population

    return best_schedule, score_history
