import csv
import sys

# Add the backend optimization folder to Python's search path
sys.path.append("../backend/optimization")

from scenarios import create_scenarios
from benchmark import run_greedy, evaluate_routes_with_dijkstra


def run_experiments():

    # Load the existing team scenarios
    scenarios = create_scenarios()

    # Open results.csv
    with open("results.csv", "w", newline="") as file:

        writer = csv.writer(file)

        # CSV column headings
        writer.writerow([
            "scenario_id",
            "algorithm",
            "travel_time",
            "distance",
            "congestion_penalty",
            "fuel_cost",
            "constraint_violations",
            "runtime",
            "iterations",
            "best_fitness"
        ])

        # Run Greedy on every scenario
        for scenario_name, problem in scenarios.items():

            print("Running scenario:", scenario_name)

            # Run the real Greedy VRP algorithm
            result = run_greedy(problem)

            # Calculate distance using Dijkstra
            distance = evaluate_routes_with_dijkstra(
                result["routes"],
                problem
            )

            # Save the result
            writer.writerow([
                scenario_name,
                result["algorithm"],
                0,
                distance,
                0,
                0,
                0,
                result["runtime"],
                0,
                result["fitness"]
            ])

            print("Routes:", result["routes"])
            print("Fitness:", result["fitness"])
            print("Distance:", distance)
            print("Runtime:", result["runtime"])
            print("-------------------------")

    print("Experiment completed!")
    print("Results saved to results.csv")


if __name__ == "__main__":
    run_experiments()