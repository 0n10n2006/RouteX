import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# Load statistical summary
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "statistical_summary.csv"
output_dir = BASE_DIR / "graphs"

output_dir.mkdir(exist_ok=True)

df = pd.read_csv(input_file)

# --------------------------------------------------
# Graph 1: Mean Fitness by Algorithm and Scenario
# --------------------------------------------------

pivot_fitness = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="mean_fitness"
)

pivot_fitness.plot(kind="bar", figsize=(12, 6))

plt.title("Mean Fitness Comparison Across Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Mean Fitness")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "mean_fitness_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 2: Runtime Comparison
# --------------------------------------------------

pivot_runtime = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="mean_runtime"
)

pivot_runtime.plot(kind="bar", figsize=(12, 6))

plt.title("Average Runtime Comparison")
plt.xlabel("Scenario")
plt.ylabel("Runtime (seconds)")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "runtime_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 3: Mean Distance Comparison
# --------------------------------------------------

pivot_distance = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="mean_distance"
)

pivot_distance.plot(kind="bar", figsize=(12, 6))

plt.title("Mean Travel Distance Comparison")
plt.xlabel("Scenario")
plt.ylabel("Distance")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "distance_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 4: Standard Deviation / Stability
# --------------------------------------------------

pivot_std = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="std_fitness"
)

pivot_std.plot(kind="bar", figsize=(12, 6))

plt.title("Fitness Stability Across Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Standard Deviation")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "fitness_stability.png", dpi=300)
plt.close()

# --------------------------------------------------
# Completed
# --------------------------------------------------

print("================================")
print("GRAPH GENERATION COMPLETED")
print("================================")
print(f"Graphs saved to: {output_dir}")