This repository contains implementations of three routing protocols and their evaluation on various network performance metrics:

- **OSPF (Open Shortest Path First)**: Traditional shortest path protocol using Dijkstra's algorithm.
- **ECMP (Equal-Cost Multi-Path Routing)**: Uses multiple equal-cost paths to balance traffic.
- **DMPF (Disjoint Multi-Path Forwarding)**: Uses edge-disjoint paths within a bounded cost for multipath routing.

The simulation is designed to work with a custom network topology defined in JSON format, and includes tools for evaluating link utilization, fairness, and other metrics.


## 📁 Project Structure
. ├── main.py # Entry point for running the routing simulations ├── topology.json # Network topology in JSON format ├── protocols/ │ ├── ospf.py # OSPF implementation │ ├── ecmp.py # ECMP implementation │ └── dmpf.py # DMPF implementation ├── utils/ │ ├── topology_loader.py # Helper for loading JSON topology │ └── visualize.py # (Optional) Topology graph visualizer ├── evaluate.py # Evaluation script to compute network metrics ├── paths/ │ ├── ospf_paths.csv # Generated OSPF paths │ ├── ecmp_paths.csv # Generated ECMP paths │ └── dmpf_paths.csv # Generated DMPF paths

## 🚀 How to Run

Use the main.py script to simulate any of the three routing protocols:
python main.py --protocol OSPF
python main.py --protocol ECMP
python main.py --protocol DMPF
By default, it uses topology.json. You can also specify a custom file.
