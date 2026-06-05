"""Genetic Algorithm for exam scheduling. No tkinter imports."""
import random


def init_population(size: int, courses: list, slots: list) -> list[dict]:
    """Generate `size` random schedule dicts."""
    return [
        {course: random.choice(slots) for course in courses}
        for _ in range(size)
    ]


def tournament_select(population: list, scores: list, k: int) -> dict:
    """Return a copy of the lowest-scoring chromosome from k random candidates."""
    k = min(k, len(population))
    indices = random.sample(range(len(population)), k)
    best = min(indices, key=lambda i: scores[i])
    return dict(population[best])


def crossover(parent_a: dict, parent_b: dict, courses: list) -> dict:
    """Single-point crossover on the ordered course list. Returns a new child dict."""
    point = random.randint(1, len(courses) - 1)
    child = {}
    for i, course in enumerate(courses):
        child[course] = parent_a[course] if i < point else parent_b[course]
    return child


def mutate(schedule: dict, slots: list, rate: float) -> dict:
    """Return a new dict where each gene is randomly reassigned with probability=rate."""
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
    """
    Run the full GA loop.
    config keys: pop_size, max_gen, mutation_rate, tournament_k
    Returns (best_schedule, score_history) where score_history[i] = best penalty at gen i.
    """
    from core.penalty import score as penalty_score

    pop_size = config["pop_size"]
    max_gen = config["max_gen"]
    mutation_rate = config["mutation_rate"]
    tournament_k = config["tournament_k"]

    population = init_population(pop_size, courses, slots)
    score_history: list[int] = []
    best_schedule: dict = {}
    best_score = float("inf")

    for _ in range(max_gen):
        scores = [
            penalty_score(ind, conflict_table, student_courses)
            for ind in population
        ]

        # Track global best
        gen_best_idx = min(range(pop_size), key=lambda i: scores[i])
        if scores[gen_best_idx] < best_score:
            best_score = scores[gen_best_idx]
            best_schedule = dict(population[gen_best_idx])

        score_history.append(best_score)

        # Elitism: preserve top 2 unchanged
        ranked = sorted(range(pop_size), key=lambda i: scores[i])
        new_population = [dict(population[ranked[0]]), dict(population[ranked[1]])]

        # Fill remainder with crossover + mutation
        while len(new_population) < pop_size:
            pa = tournament_select(population, scores, tournament_k)
            pb = tournament_select(population, scores, tournament_k)
            child = crossover(pa, pb, courses)
            child = mutate(child, slots, mutation_rate)
            new_population.append(child)

        population = new_population

    return best_schedule, score_history
