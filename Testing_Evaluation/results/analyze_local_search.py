import pandas as pd

df = pd.read_csv(
    "Testing_Evaluation/results/local_search_tuning.csv"
)

scenario_analysis = (
    df.groupby(["scenario_id", "local_search_probability"])["fitness"]
    .mean()
    .reset_index()
)

print("\nScenario-wise Average Fitness")
print(scenario_analysis)

print("\nBest Probability for Each Scenario:")

best = (
    scenario_analysis
    .loc[
        scenario_analysis.groupby("scenario_id")["fitness"].idxmin()
    ]
)

print(best)