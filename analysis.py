# ---------------------- IMPORTS ----------------------
import networkx as nx
import numpy as np
import random
import time
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
from ospf import Router, flood_lsa, build_routing_table
import ecmp
import dmpf

# ---------------------- CONFIGURATION ----------------------
NUM_TOPOLOGIES = 1000 
NUM_ITERATIONS = 10
NUM_SRC_DST_PER_ITER = 10  #25
NUM_PACKETS = 100
BOTTLENECK_THRESHOLD_MULTIPLIER = 2

# ---------------------- ROUTING ALGORITHMS ----------------------
def ospf_paths(G, src, dst):
    from collections import defaultdict

    # Convert NetworkX graph G into topology format
    topology = {
        'routers': list(G.nodes),
        'links': [(u, v, G[u][v]['delay']) for u, v in G.edges]
    }

    # Create router instances
    routers = {rid: Router(rid) for rid in topology['routers']}
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    # Generate and flood LSA from each router
    for router in routers.values():
        router.sequence_number += 1
        lsa = router.generate_lsa()
        flood_lsa(router, lsa, routers)

    # Build routing tables
    for router in routers.values():
        build_routing_table(router)

    # Return the path from src to dst
    if dst not in routers[src].routing_table:
        print(f"Warning: No path from {src} to {dst}")
    return [routers[src].routing_table[dst]] if dst in routers[src].routing_table else []


def ecmp_paths(G, src, dst):
    # Convert NetworkX graph into topology format
    topology = {
        'routers': list(G.nodes),
        'links': [(u, v, G[u][v]['delay']) for u, v in G.edges]
    }

    # Initialize routers
    routers = {rid: ecmp.Router(rid) for rid in topology['routers']}
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    # LSA flooding
    for router in routers.values():
        router.sequence_number += 1
        lsa = router.generate_lsa()
        ecmp.flood_lsa(router, lsa, routers)

    # ECMP routing table creation
    for router in routers.values():
        ecmp.build_routing_table(router)
        
    if dst not in routers[src].routing_table:
        print(f"Warning: No path from {src} to {dst}")
    # Return equal-cost paths from src to dst
    return [routers[src].routing_table[dst]] if dst in routers[src].routing_table else []

def dmpf_paths(G, src, dst, k=3, delta=20):
    # Step 1: Extract topology from NetworkX graph
    topology = {
        'routers': list(G.nodes),
        'links': [(u, v, G[u][v]['delay']) for u, v in G.edges]
    }

    # Step 2: Initialize routers and their neighbors
    routers = {rid: dmpf.Router(rid) for rid in topology['routers']}
    for r1, r2, cost in topology['links']:
        routers[r1].neighbors[r2] = cost
        routers[r2].neighbors[r1] = cost

    # Step 3: Run DMPF convergence to simulate LSA flooding
    dmpf.converge_network(routers)

    # Step 4: Check if destination is reachable in the LSDB
    if dst not in routers[src].neighbors and dst not in routers[src].lsdb:
        print(f"[Routing Table Missing] {src} → {dst}: Destination not in neighbors or LSDB.")
        return []

    try:
        # Step 5: Compute disjoint paths
        results = dmpf.compute_dmpf_paths(routers[src].lsdb, src, dst, k, delta)
    except Exception as e:
        print(f"[Exception] DMPF path computation from {src} to {dst} failed: {e}")
        return []

    if not results:
        print(f"[Empty Result] DMPF path computation from {src} to {dst} returned no paths.")
        return []

    # Step 6: Extract only the path sequences
    paths = [path for path, cost in results]
    return paths


# ---------------------- TOPOLOGY GENERATOR ----------------------
def generate_random_topology():
    while True:
        choice = random.choice(["grid", "erdos", "powerlaw", "tree"])
        if choice == "grid":
            G = nx.grid_2d_graph(4, 4)
            G = nx.convert_node_labels_to_integers(G)
        elif choice == "erdos":
            G = nx.erdos_renyi_graph(20, 0.2)
        elif choice == "powerlaw":
            G = nx.powerlaw_cluster_graph(20, 3, 0.2)
        else:
            G = nx.balanced_tree(2, 4)

        if nx.is_connected(G):
            break  # only return a connected graph

    for u, v in G.edges():
        G[u][v]['bandwidth'] = random.randint(10, 100)
        G[u][v]['delay'] = random.randint(1, 1000)
    return G

# ---------------------- METRIC CALCULATOR ----------------------
def compute_new_metrics(G, paths, failed_edge=None):
    edge_usage = Counter()
    packets_lost = 0
    impacted_paths = 0
    flat_paths = []
    for group in paths:
        if isinstance(group[0], list):  # nested list
            flat_paths.extend(group)
        else:
            flat_paths.append(group)

    for path in flat_paths:
        failed = False
        for u, v in zip(path[:-1], path[1:]):
            edge = (u, v)
            if failed_edge and (edge == failed_edge or edge[::-1] == failed_edge):
                packets_lost += 1
                failed = True
                break
        if not failed:
            for u, v in zip(path[:-1], path[1:]):
                edge_usage[(u, v)] += 1
        else:
            impacted_paths += 1

    total_usage = sum(edge_usage.values())
    used_edges = list(edge_usage.keys())

    # Normalized traffic load
    normalized_traffic = total_usage / len(used_edges) if used_edges else 0

    # Bandwidth utilization ratio
    bandwidth_utilization = 0
    if used_edges:
        util_ratios = []
        for (u, v) in used_edges:
            bw = G[u][v]['bandwidth'] if G.has_edge(u, v) else G[v][u]['bandwidth']
            util_ratios.append(edge_usage[(u, v)] / bw)
        bandwidth_utilization = np.mean(util_ratios)

    # Entropy and bottlenecks
    probs = np.array(list(edge_usage.values())) / total_usage if total_usage > 0 else np.array([])
    entropy = -np.sum(probs * np.log2(probs)) if probs.size > 0 else 0

    if edge_usage:
        usages = np.array(list(edge_usage.values()))
        mean_usage = usages.mean()
        bottleneck_threshold = BOTTLENECK_THRESHOLD_MULTIPLIER * mean_usage
        bottleneck_edges = np.sum(usages > bottleneck_threshold)
        bottleneck_ratio = bottleneck_edges / len(usages)
        max_util = usages.max()
        min_util = usages.min()
    else:
        bottleneck_ratio = max_util = min_util = 0

    return {
        'normalized_traffic': normalized_traffic,
        'bandwidth_utilization': bandwidth_utilization,
        'packet_loss': packets_lost,
        'failure_impact_score': impacted_paths / len(paths) if paths else 0,
        'bottleneck_freq': bottleneck_ratio,
        'max_util': max_util,
        'min_util': min_util,
        'entropy': entropy
    }


# ---------------------- MAIN EVALUATION LOOP ----------------------
def evaluate_algorithms():
    final_results = defaultdict(lambda: defaultdict(list))

    for t in range(NUM_TOPOLOGIES):
        G = generate_random_topology()
        nodes = list(G.nodes())
        for name, algo_fn in zip(['OSPF', 'ECMP', 'DMPF'], [ospf_paths, ecmp_paths, dmpf_paths]):
            for _ in range(NUM_ITERATIONS):
                pairs = [random.sample(nodes, 2) for _ in range(NUM_SRC_DST_PER_ITER)]
                all_paths = []
                for src, dst in pairs:
                    paths = algo_fn(G, src, dst)
                    if not paths:
                        print(f"No paths found from {src} to {dst}, skipping.")
                        continue

                    packets_per_path = NUM_PACKETS // len(paths)
                    for path in paths:
                        all_paths.extend([path] * packets_per_path)

                failed_edge = random.choice(list(G.edges())) if G.number_of_edges() > 0 else None
                metrics = compute_new_metrics(G, all_paths, failed_edge)

                for k, v in metrics.items():
                    final_results[(t, name)][k].append(v)

    # Final Aggregated Output
    for (topo_id, algo), metrics_dict in final_results.items():
        print(f"Topology {topo_id} - {algo}")
        for k, vals in metrics_dict.items():
            print(f"  {k}: {np.mean(vals):.4f}")
        print("----------------------")

    # Overall average per algorithm
    print("\nOVERALL COMPARISON:")
    overall = defaultdict(lambda: defaultdict(list))
    for (topo_id, algo), metrics_dict in final_results.items():
        for k, vals in metrics_dict.items():
            overall[algo][k].extend(vals)

    for algo, metrics_dict in overall.items():
        print(f"{algo}:")
        for k, vals in metrics_dict.items():
            print(f"  {k}: {np.mean(vals):.4f}")
        print("----------------------")

# ---------------------- RUN ----------------------
if __name__ == "__main__":
    evaluate_algorithms()
