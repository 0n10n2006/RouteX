import time
import random

random.seed(42)

from .problem import ProblemInstance
from .greedy_vrp import greedy_vrp
from .qpso import QPSO
from .hybrid import hybrid_qpso
from .fitness import fitness
from .scenarios import create_scenarios
from .ga import GeneticAlgorithm
from .pso import ParticleSwarmOptimization

def run_greedy(problem):
    start = time.perf_counter()

    routes = greedy_vrp(problem)

    runtime = time.perf_counter() - start
    score = fitness(routes, problem)

    return score, runtime


def run_qpso(problem):
    start = time.perf_counter()

    qpso = QPSO(
        num_particles=10,
        num_customers=len(problem.customers)
    )

    for _ in range(20):
        qpso.step(problem, fitness, beta=0.5)

    result = qpso.get_best_solution(problem)

    runtime = time.perf_counter() - start

    return result["fitness"], runtime

def run_ga(problem):
    start = time.perf_counter()

    ga = GeneticAlgorithm(
        population_size=20,
        generations=50
    )

    result = ga.solve(problem)

    runtime = time.perf_counter() - start

    return result["fitness"], runtime

def run_pso(problem):
    start = time.perf_counter()

    pso = ParticleSwarmOptimization(
        num_particles=20,
        iterations=50
    )

    result = pso.solve(problem)

    runtime = time.perf_counter() - start

    return result["fitness"], runtime


def run_hybrid(problem):
    start = time.perf_counter()

    result = hybrid_qpso(
        problem,
        num_particles=10,
        iterations=20,
        beta=0.5
    )

    runtime = time.perf_counter() - start

    return result["fitness"], runtime


def average(values):
    return sum(values) / len(values)

def improvement_percent(baseline, new):

    if baseline == 0:
        return 0.0

    return ((baseline - new) / baseline) * 100

if __name__ == "__main__":

    scenarios = create_scenarios()

    runs = 10

    for scenario_name, problem in scenarios.items():

        print("\n================================")
        print(f"SCENARIO: {scenario_name.upper()}")
        print("================================")

        greedy_scores = []
        ga_scores = []
        pso_scores = []
        qpso_scores = []
        hybrid_scores = []

        greedy_times = []
        ga_times = []
        pso_times = []
        qpso_times = []
        hybrid_times = []

        for i in range(runs):

            score, runtime = run_greedy(problem)
            greedy_scores.append(score)
            greedy_times.append(runtime)

            score, runtime = run_ga(problem)
            ga_scores.append(score)
            ga_times.append(runtime)

            score, runtime = run_qpso(problem)
            qpso_scores.append(score)
            qpso_times.append(runtime)
         
            score, runtime = run_pso(problem)
            pso_scores.append(score)
            pso_times.append(runtime)

            score, runtime = run_hybrid(problem)
            hybrid_scores.append(score)
            hybrid_times.append(runtime)

            print(f"Run {i + 1}/{runs} complete")

        greedy_avg = average(greedy_scores)
        ga_avg = average(ga_scores)
        pso_avg = average(pso_scores)
        qpso_avg = average(qpso_scores)
        hybrid_avg = average(hybrid_scores)
        print("\n===== RESULTS =====")

        print(
            f"Greedy: {greedy_avg:.2f} "
            f"| Runtime: {average(greedy_times):.6f}s"
        )
     
        print(
            f"GA: {ga_avg:.2f} "
            f"| Runtime: {average(ga_times):.6f}s"
        )

        print(
            f"PSO: {pso_avg:.2f} "
            f"| Runtime: {average(pso_times):.6f}s"
        )

        print(
            f"QPSO: {qpso_avg:.2f} "
            f"| Runtime: {average(qpso_times):.6f}s"
        )

        print(
            f"Hybrid: {hybrid_avg:.2f} "
            f"| Runtime: {average(hybrid_times):.6f}s"
        )

        print("\n===== IMPROVEMENT =====")

        print(
            f"QPSO vs Greedy: "
            f"{improvement_percent(greedy_avg, qpso_avg):.2f}%"
        )

        print(
            f"Hybrid vs Greedy: "
            f"{improvement_percent(greedy_avg, hybrid_avg):.2f}%"
        )

        print(
            f"Hybrid vs QPSO: "
            f"{improvement_percent(qpso_avg, hybrid_avg):.2f}%"
        )

        qpso_wins = sum(
            score < greedy_scores[i]
            for i, score in enumerate(qpso_scores)
        )

        hybrid_wins = sum(
            score < greedy_scores[i]
            for i, score in enumerate(hybrid_scores)
        )

        print("\n===== SUCCESS RATE =====")

        print(
            f"QPSO beat Greedy: "
            f"{qpso_wins}/{runs} "
            f"({qpso_wins / runs * 100:.1f}%)"
        )

        print(
            f"Hybrid beat Greedy: "
            f"{hybrid_wins}/{runs} "
            f"({hybrid_wins / runs * 100:.1f}%)"
        )