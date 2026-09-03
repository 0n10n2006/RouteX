import pandas as pd
from pathlib import Path

# -----------------------------------------
# Load repeated experiment results
# -----------------------------------------

input_file = Path(__file__).resolve().parent / "repeated_results.csv"

df = pd.read_csv(input_file)

print("================================")
print("STATISTICAL ANALYSIS")
print("================================")

print("\nTotal experiments:", len(df))

# -----------------------------------------
# Calculate statistics
# -----------------------------------------

summary = (
    df.groupby(["scenario_id", "algorithm"])
    .agg(
        mean_fitness=("fitness", "mean"),
        std_fitness=("fitness", "std"),
        min_fitness=("fitness", "min"),
        max_fitness=("fitness", "max"),
        mean_runtime=("runtime", "mean"),
        mean_distance=("distance", "mean"),
        mean_iterations=("iterations", "mean"),
        total_constraint_violations=("constraint_violations", "sum")
    )
    .reset_index()
)

# Round values
summary["mean_fitness"] = summary["mean_fitness"].round(2)
summary["std_fitness"] = summary["std_fitness"].round(2)
summary["min_fitness"] = summary["min_fitness"].round(2)
summary["max_fitness"] = summary["max_fitness"].round(2)
summary["mean_runtime"] = summary["mean_runtime"].round(4)
summary["mean_distance"] = summary["mean_distance"].round(2)

# -----------------------------------------
# Display results
# -----------------------------------------

print("\nSummary:")
print(summary.to_string(index=False))

# -----------------------------------------
# Save summary
# -----------------------------------------

output_file = (
    Path(__file__).resolve().parent
    / "statistical_summary.csv"
)

summary.to_csv(output_file, index=False)

print("\n================================")
print("STATISTICAL ANALYSIS COMPLETED")
print("================================")
print("Results saved to:", output_file)