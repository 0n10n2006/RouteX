import csv

from scenario_generator import scenarios
from metrics import create_result


# Algorithm  testing
algorithm = "Baseline"


# Create and open results.csv
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

    # Run through all scenarios
    for scenario in scenarios:

        print("Running scenario:", scenario["id"])

        # Temporary values for testing
    
        result = create_result(
            scenario["id"],
            algorithm,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0
        )

        # Save the result to CSV
        writer.writerow([
            result["scenario_id"],
            result["algorithm"],
            result["travel_time"],
            result["distance"],
            result["congestion_penalty"],
            result["fuel_cost"],
            result["constraint_violations"],
            result["runtime"],
            result["iterations"],
            result["best_fitness"]
        ])


print("Experiment completed!")
print("Results saved to results.csv")