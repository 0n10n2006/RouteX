import networkx as nx

from backend.optimization.traffic_scenarios import (
    prepare_graph,
    load_road_network,
    KOTHRUD_OSM_FILE,
    _connected_locations,
)

graph = prepare_graph(load_road_network(KOTHRUD_OSM_FILE))
locations = _connected_locations(graph)

nodes = []

for location in locations:
    node = next(
        n
        for n, data in graph.nodes(data=True)
        if data["y"] == location["latitude"]
        and data["x"] == location["longitude"]
    )
    nodes.append(node)

simple_graph = nx.DiGraph()

for u, v, data in graph.edges(data=True):
    length = float(data.get("length", 0))

    if (
        not simple_graph.has_edge(u, v)
        or length < simple_graph[u][v]["length"]
    ):
        simple_graph.add_edge(u, v, length=length)

print("0 -> 1 ALTERNATIVE PATHS")
print("=" * 60)

paths = nx.shortest_simple_paths(
    simple_graph,
    nodes[0],
    nodes[1],
    weight="length",
)

for i, path in enumerate(paths):
    if i >= 2:
        break

    length = sum(
        simple_graph.edges[path[j], path[j + 1]]["length"]
        for j in range(len(path) - 1)
    )

    print(f"\nPATH {i + 1}")
    print(f"Length: {length:.2f} m")
    print("Nodes:", path)

    print("Edges:")
    for j in range(len(path) - 1):
        u = path[j]
        v = path[j + 1]
        data = simple_graph[u][v]

        print(
            f"  {u} -> {v} | "
            f"{data['length']:.2f} m"
        )