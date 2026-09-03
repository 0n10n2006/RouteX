import pandas as pd
from pathlib import Path

# --------------------------------------------------
# Load statistical summary
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "statistical_summary.csv"
output_file = BASE_DIR / "performance_comparison.csv"

df = pd.read_csv(input_file)

# --------------------------------------------------
# Get Hybrid QPSO results
# --------------------------------------------------

hybrid = df[df["algorithm"] == "Hybrid QPSO"][
    ["scenario_id", "mean_fitness"]
].rename(columns={"mean_fitness": "hybrid_fitness"})

# --------------------------------------------------
# Compare with other algorithms
# --------------------------------------------------

algorithms = [
    "Greedy VRP",
    "GA",
    "PSO",
    "QPSO"
]

results = []

for algorithm in algorithms:

    baseline = df[df["algorithm"] == algorithm][
        ["scenario_id", "mean_fitness"]
    ].rename(columns={"mean_fitness": "baseline_fitness"})

    merged = hybrid.merge(baseline, on="scenario_id")

    # Lower fitness = better
    merged["improvement_percent"] = (
        (merged["baseline_fitness"] - merged["hybrid_fitness"])
        / merged["baseline_fitness"]
    ) * 100

    merged["comparison"] = algorithm

    results.append(
        merged[
            [
                "scenario_id",
                "comparison",
                "baseline_fitness",
                "hybrid_fitness",
                "improvement_percent"
            ]
        ]
    )

# --------------------------------------------------
# Combine results
# --------------------------------------------------

comparison = pd.concat(results, ignore_index=True)

comparison.to_csv(output_file, index=False)

# --------------------------------------------------
# Display results
# --------------------------------------------------

print("================================")
print("HYBRID QPSO PERFORMANCE ANALYSIS")
print("================================")

print(comparison.to_string(index=False))

print("\n================================")
print("AVERAGE IMPROVEMENT")
print("================================")

average = (
    comparison
    .groupby("comparison")["improvement_percent"]
    .mean()
    .sort_values(ascending=False)
)

for algorithm, value in average.items():
    print(f"{algorithm}: {value:.2f}%")

print("\n================================")
print("Analysis completed!")
print(f"Results saved to: {output_file}")
print("================================")