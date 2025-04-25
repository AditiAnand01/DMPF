import networkx as nx
import matplotlib.pyplot as plt

def visualize_topology(topology):
    G = nx.Graph() # Create an undirected graph object

    # Add edges to the graph. Each link is a tuple: (router1, router2, cost)
    for r1, r2, cost in topology['links']:
        G.add_edge(r1, r2, weight=cost)  # Add edge, 'weight' attribute represents cost

    pos = nx.spring_layout(G) # Generate positions for each node using spring layout
    nx.draw(G, pos, with_labels=True, node_size=1500, node_color='lightblue')  # Draw the graph
    labels = nx.get_edge_attributes(G, 'weight') # Extract the edge weights (costs) from the graph
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels) # Draw the edge labels (the costs on the links) at their respective positions
    plt.title("Network Topology") # Add title to the plot
    plt.show() # Display the plot
