import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "statistical_summary.csv"
output_file = BASE_DIR / "final_evaluation_summary.csv"

df = pd.read_csv(input_file)

# Overall average performance of each algorithm
summary = (
    df.groupby("algorithm")
    .agg(
        average_fitness=("mean_fitness", "mean"),
        average_distance=("mean_distance", "mean"),
        average_runtime=("mean_runtime", "mean"),
        average_iterations=("mean_iterations", "mean"),
        total_constraint_violations=("total_constraint_violations", "sum")
    )
    .reset_index()
)

# Sort by fitness (lower is better)
summary = summary.sort_values("average_fitness")

summary.to_csv(output_file, index=False)

print("================================")
print("FINAL EVALUATION SUMMARY")
print("================================")

print(summary.to_string(index=False))

print("\n================================")
print("BEST OVERALL ALGORITHM")
print("================================")

best = summary.iloc[0]

print(f"Algorithm: {best['algorithm']}")
print(f"Average Fitness: {best['average_fitness']:.2f}")
print(f"Average Distance: {best['average_distance']:.2f}")
print(f"Average Runtime: {best['average_runtime']:.4f} seconds")

print("\n================================")
print("Evaluation completed!")
print(f"Results saved to: {output_file}")
print("================================")