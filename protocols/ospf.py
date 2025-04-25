import networkx as nx
from utils.visualize import visualize_topology
import csv

# Represents a router in the OSPF protocol
class Router:
    def __init__(self, router_id):
        self.router_id = router_id  # Unique ID for the router
        self.neighbors = {}  # dictionary mapping neighbor router IDs to the link costs
        self.lsdb = {}  # Link-state database
        self.routing_table = {}  # to store computed shortest paths to each destination router
        self.sequence_number = 0  # Sequence number for LSA
        self.received_lsas = set()  # Set of received LSA keys (origin, sequence)

    # Generate a Link State Advertisement (LSA) with the current state
    def generate_lsa(self):
        return {"origin": self.router_id, "sequence": self.sequence_number, "neighbors": self.neighbors.copy()}

# Recursively flood an LSA to all routers in the network
def flood_lsa(router, lsa, routers, visited=None):
    if visited is None:
        visited = set()

    key = (lsa['origin'], lsa['sequence'])
    if key in router.received_lsas:
        return  # Discard already received LSA

    router.received_lsas.add(key)
    router.lsdb[lsa['origin']] = lsa  # Update LSDB

    for neighbor_id in router.neighbors:
        if neighbor_id not in visited:
            visited.add(neighbor_id)
            flood_lsa(routers[neighbor_id], lsa, routers, visited)

# Build network graph from LSDB
def build_graph_from_lsdb(lsdb):
    G = nx.Graph()
    for lsa in lsdb.values():
        origin = lsa['origin']
        for neighbor, cost in lsa['neighbors'].items():
            G.add_edge(origin, neighbor, weight=cost)
    return G

# Dijkstra's algorithm to compute shortest path
def dijkstra(graph, source):
    D = {node: float('inf') for node in graph.nodes}
    previous = {}
    D[source] = 0
    visited = set()

    while len(visited) < len(graph.nodes):
        min_node = None
        min_dist = float('inf')
        for node in graph.nodes:
            if node not in visited and D[node] < min_dist:
                min_node = node
                min_dist = D[node]

        if min_node is None:
            break

        visited.add(min_node)
        for neighbor in graph.neighbors(min_node):
            weight = graph[min_node][neighbor]['weight']
            if D[min_node] + weight < D[neighbor]:
                D[neighbor] = D[min_node] + weight
                previous[neighbor] = min_node

    return previous

# Construct routing table using Dijkstra's algorithm
def build_routing_table(router):
    graph = build_graph_from_lsdb(router.lsdb)
    parent = dijkstra(graph, router.router_id)

    # Construct full path to each destination
    for dest in graph.nodes:
        if dest == router.router_id:
            continue
        path = []
        current = dest
        while current != router.router_id:
            path.append(current)
            current = parent.get(current)
            if current is None:
                path = []
                break
        if path:
            path.append(router.router_id)
            path.reverse()
            router.routing_table[dest] = path

# Save all routing paths from each router to a CSV file
def save_paths_to_csv(routers, filename="ospf_paths.csv"):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Source', 'Destination', 'Path'])

        for src_id, router in routers.items():
            for dest_id, path in router.routing_table.items():
                writer.writerow([src_id, dest_id, path])

# Run OSPF simulation
def run(topology):
    routers = {rid: Router(rid) for rid in topology['routers']}
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    visualize_topology(topology)

    # Generate and flood LSA from each router
    for router in routers.values():
        router.sequence_number += 1
        lsa = router.generate_lsa()
        flood_lsa(router, lsa, routers)

    # Build routing table after LSDB is populated
    for router in routers.values():
        build_routing_table(router)

    # Output LSDB and routing table
    with open("ospf_state.txt", "w") as f:
        for router_id, router in routers.items():
            f.write(f"Router {router_id} LSDB:\n")
            for k, v in router.lsdb.items():
                f.write(f"  {k}: {v}\n")

            f.write(f"\nRouting Table for Router {router_id}:\n")
            f.write(f"{'Destination':<15}{'Path'}\n")
            f.write(f"{'-'*40}\n")
            for dest, path in router.routing_table.items():
                f.write(f"{dest:<15}{' -> '.join(path)}\n")
            f.write("\n")
            
    save_paths_to_csv(routers)



