from tests.demo_scenarios import create_all_demo_scenarios
from traffic.simulation import run_simulation


def main():
    scenarios = create_all_demo_scenarios()

    print("=== ROUTEX WEEK 7 DEMO RESULTS ===")

    for scenario in scenarios:
        result = run_simulation(
            scenario["graph"],
            scenario["locations"],
            scenario["routes"],
            time_step=1,
            max_time=7200,
            traffic_factors=scenario.get("traffic_factors"),
            incident_edges=scenario.get("incident_edges"),
        )

        vehicle = result.vehicles[0]

        print()
        print(f"Scenario: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Completed: {result.completed}")
        print(f"Travel time: {vehicle.elapsed_time:.2f} seconds")
        print(f"Distance: {vehicle.travelled_distance:.2f} meters")
        print(f"Path edges: {len(vehicle.path_nodes) - 1}")
        print(f"Final network loading: {result.edge_load}")


if __name__ == "__main__":
    main()