import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --------------------------------------------------
# Load fixed demo results
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

input_file = BASE_DIR / "fixed_demo_results.csv"
output_dir = BASE_DIR / "graphs"

output_dir.mkdir(exist_ok=True)

df = pd.read_csv(input_file)

# --------------------------------------------------
# Graph 1: Fitness Comparison
# --------------------------------------------------

pivot_fitness = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="fitness"
)

pivot_fitness.plot(kind="bar", figsize=(12, 6))

plt.title("Fitness Comparison Across Fixed Demo Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Fitness")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "fixed_demo_fitness_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 2: Runtime Comparison
# --------------------------------------------------

pivot_runtime = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="runtime"
)

pivot_runtime.plot(kind="bar", figsize=(12, 6))

plt.title("Runtime Comparison Across Fixed Demo Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Runtime (seconds)")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "fixed_demo_runtime_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 3: Distance Comparison
# --------------------------------------------------

pivot_distance = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="distance"
)

pivot_distance.plot(kind="bar", figsize=(12, 6))

plt.title("Distance Comparison Across Fixed Demo Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Distance")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "fixed_demo_distance_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Graph 4: Iterations Comparison
# --------------------------------------------------

pivot_iterations = df.pivot(
    index="scenario_id",
    columns="algorithm",
    values="iterations"
)

pivot_iterations.plot(kind="bar", figsize=(12, 6))

plt.title("Iterations Comparison Across Fixed Demo Scenarios")
plt.xlabel("Scenario")
plt.ylabel("Iterations")
plt.xticks(rotation=0)
plt.legend(title="Algorithm")
plt.tight_layout()

plt.savefig(output_dir / "fixed_demo_iterations_comparison.png", dpi=300)
plt.close()

# --------------------------------------------------
# Completed
# --------------------------------------------------

print("================================")
print("FIXED DEMO GRAPH GENERATION COMPLETED")
print("================================")
print(f"Graphs saved to: {output_dir}")