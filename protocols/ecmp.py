import networkx as nx
import csv
from utils.visualize import visualize_topology

# Represents a router in the OSPF-ECMP protocol
class Router:
    def __init__(self, router_id):
        self.router_id = router_id # Unique ID for the router
        self.neighbors = {}  # neighbor_id -> cost
        self.lsdb = {}  # origin_id -> LSA dict
        self.routing_table = {}  # dest_id -> list of paths
        self.sequence_number = 0 # Sequence number for LSA
        self.received_lsas = set() # Set of received LSA keys (origin, sequence)

    # Generate a Link State Advertisement (LSA) with the current state
    def generate_lsa(self):
        return {
            "origin": self.router_id,
            "sequence": self.sequence_number,
            "neighbors": self.neighbors.copy(),
        }

# Reliable flooding of LSAs
def flood_lsa(router, lsa, routers, visited=None):
    if visited is None:
        visited = set()
    key = (lsa['origin'], lsa['sequence'])
    if key in router.received_lsas:
        return

    router.received_lsas.add(key)
    router.lsdb[lsa['origin']] = lsa

    for neighbor_id in router.neighbors:
        if neighbor_id not in visited:
            visited.add(neighbor_id)
            flood_lsa(routers[neighbor_id], lsa, routers, visited)

# Build graph from LSDB
def build_graph_from_lsdb(lsdb):
    G = nx.Graph()
    for lsa in lsdb.values():
        origin = lsa['origin']
        for neighbor, cost in lsa['neighbors'].items():
            G.add_edge(origin, neighbor, weight=cost)
    return G

# Compute all equal-cost shortest paths
def all_ecmp_paths(graph, source):
    shortest_paths = {}
    try:
        lengths = nx.single_source_dijkstra_path_length(graph, source)
        for dest, cost in lengths.items():
            if dest != source:
                paths = list(nx.all_shortest_paths(graph, source, dest, weight='weight'))
                shortest_paths[dest] = paths
    except nx.NetworkXNoPath:
        pass
    return shortest_paths

# Build ECMP routing table
def build_routing_table(router):
    graph = build_graph_from_lsdb(router.lsdb)
    ecmp_paths = all_ecmp_paths(graph, router.router_id)
    router.routing_table = ecmp_paths

# Save all ECMP routing paths to a CSV file
def save_ecmp_paths_to_csv(routers, filename="ospf_ecmp_paths.csv"):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Source', 'Destination', 'Equal-Cost Paths'])

        for src_id, router in routers.items():
            for dest_id, paths in router.routing_table.items():
                writer.writerow([src_id, dest_id, paths])


# Run ECMP OSPF Simulation
def run(topology):
    routers = {rid: Router(rid) for rid in topology['routers']}
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    visualize_topology(topology)

    # Flooding stage
    for router in routers.values():
        router.sequence_number += 1
        lsa = router.generate_lsa()
        flood_lsa(router, lsa, routers)

    # Path calculation
    for router in routers.values():
        build_routing_table(router)

    # Write LSDB and ECMP routing table to file
    with open("ospf_ecmp_state.txt", "w") as f:
        for router_id, router in routers.items():
            f.write(f"Router {router_id} LSDB:\n")
            for k, v in router.lsdb.items():
                f.write(f"  {k}: {v}\n")

            f.write(f"\nRouting Table for Router {router_id} (ECMP):\n")
            f.write(f"{'Destination':<15}{'Paths (Equal Cost)'}\n")
            f.write(f"{'-'*60}\n")
            for dest, paths in router.routing_table.items():
                path_str = '; '.join([' -> '.join(p) for p in paths])
                f.write(f"{dest:<15}{path_str}\n")
            f.write("\n")
            
    save_ecmp_paths_to_csv(routers)

