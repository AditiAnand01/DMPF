import csv
import networkx as nx
from utils.visualize import visualize_topology

# Router class for representing each router/node in the network
class Router:
    def __init__(self, router_id):
        self.router_id = router_id  # Unique identifier for the router
        self.neighbors = {}  # Neighbor routers with corresponding link costs
        self.lsdb = {}  # Link State Database: stores latest LSAs received from all routers
        self.routing_table = {}  # Routing table: stores next hops and costs to destinations
        self.received_sequences = {}  # Latest sequence numbers received per router
        self.pending_lsas = []  # LSAs to process and flood further

    def generate_lsa(self, sequence):
        # Create and return a Link State Advertisement (LSA)
        return {
            "origin": self.router_id,
            "sequence": sequence,
            "neighbors": self.neighbors.copy()
        }

    def receive_lsa(self, lsa):
        # Process an incoming LSA; returns True if accepted (newer), else False
        origin = lsa['origin']
        seq = lsa['sequence']
        if origin not in self.received_sequences or seq > self.received_sequences[origin]:
            self.received_sequences[origin] = seq  # Update received sequence number
            self.lsdb[origin] = lsa  # Save LSA to LSDB
            self.pending_lsas.append(lsa)  # Queue for flooding
            return True
        return False  # LSA was already received or older

# Build graph from Link State Database (LSDB)
def build_networkx_graph(lsdb):
    G = nx.Graph()
    for router_id, lsa in lsdb.items():
        for neighbor, cost in lsa["neighbors"].items():
            G.add_edge(router_id, neighbor, weight=cost)
    return G

# Compute Disjoint Multi-Path Forwarding (DMPF) paths between source and destination
# k: maximum number of paths
# delta: max percentage above minimum cost allowed

def compute_dmpf_paths(lsdb, source, destination, k=3, delta=20):
    G = build_networkx_graph(lsdb)  # Convert LSDB to graph
    paths = []  # Stores resulting paths with their cost
    min_cost = None  # Minimum cost of the first/shortest path

    for _ in range(k):  # Try to find up to k paths
        try:
            # Compute the shortest path based on Dijkstra
            path = nx.dijkstra_path(G, source, destination, weight='weight')
            cost = sum(G[u][v]['weight'] for u, v in zip(path[:-1], path[1:]))
        except nx.NetworkXNoPath:
            break  # No further path exists

        if min_cost is None:
            min_cost = cost  # Save minimum cost for constraint check
        elif cost > min_cost * (1 + delta / 100):
            break  # Exceeds allowed cost constraint

        paths.append((path, cost))  # Store valid path and cost

        # Remove edges from graph to ensure edge-disjoint paths
        G.remove_edges_from([(path[i], path[i+1]) for i in range(len(path) - 1)])

    return paths  # Return computed paths

# Simulate reliable flooding of LSAs until convergence of LSDBs across routers
def converge_network(routers):
    sequence = 1
    converged = False
    # Track last advertised neighbor states to detect changes
    last_advertised = {r.router_id: None for r in routers.values()}
    while not converged:
        converged = True
        # Routers only advertise LSA if their neighbor state changed
        for router in routers.values():
            current_neighbors = router.neighbors.copy()
            if last_advertised[router.router_id] != current_neighbors:
                lsa = router.generate_lsa(sequence)
                last_advertised[router.router_id] = current_neighbors
                for neighbor_id in router.neighbors:
                    neighbor = routers[neighbor_id]
                    if neighbor.receive_lsa(lsa):
                        converged = False
        # Process and propagate pending LSAs
        for router in routers.values():
            while router.pending_lsas:
                lsa = router.pending_lsas.pop(0)
                for neighbor_id in router.neighbors:
                    if routers[neighbor_id].receive_lsa(lsa):
                        converged = False
        sequence += 1
        
# Save DMPF paths to a CSV file: [source, destination, [list of disjoint paths]]
def save_dmpf_paths_to_csv(routers, topology, k=3, delta=20, filename="dmpf_paths.csv"):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Source', 'Destination', 'Disjoint Paths'])

        for router in routers.values():
            for dest in topology['routers']:
                if dest == router.router_id:
                    continue
                paths = compute_dmpf_paths(router.lsdb, router.router_id, dest, k, delta)
                path_list = [path for path, cost in paths]
                writer.writerow([router.router_id, dest, path_list])


# Main function to run the DMPF protocol on a given topology
def run(topology, k=3, delta=20):
    # Initialize routers with IDs
    routers = {rid: Router(rid) for rid in topology['routers']}

    # Set up bidirectional links and their costs
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    # Visualize the network topology
    visualize_topology(topology)

    # Simulate LSA flooding until convergence
    converge_network(routers)

    # Output the LSDBs and computed disjoint paths to a file
    with open("dmpf_state.txt", "w") as f:
        for router in routers.values():
            f.write(f"Router {router.router_id} LSDB:\n")
            for k_, v_ in router.lsdb.items():
                f.write(f"  {k_}: {v_}\n")

            f.write(f"Disjoint Multi-Path Forwarding (DMPF) Paths:\n")
            for dest in topology['routers']:
                if dest == router.router_id:
                    continue
                # Compute up to k disjoint paths with delta% cost tolerance
                paths = compute_dmpf_paths(router.lsdb, router.router_id, dest, k, delta)
                f.write(f"  {dest}:\n")
                for i, (path, cost) in enumerate(paths):
                    f.write(f"    Path {i+1}: cost={cost}, path={path}\n")
    
        save_dmpf_paths_to_csv(routers, topology, k, delta)

