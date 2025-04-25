This repository contains implementations of three routing protocols and their evaluation on various network performance metrics:

- **OSPF (Open Shortest Path First)**: Traditional shortest path protocol using Dijkstra's algorithm.
- **ECMP (Equal-Cost Multi-Path Routing)**: Uses multiple equal-cost paths to balance traffic.
- **DMPF (Disjoint Multi-Path Forwarding)**: Uses edge-disjoint paths within a bounded cost for multipath routing.

The simulation is designed to work with a custom network topology defined in JSON format, and includes tools for evaluating link utilization, fairness, and other metrics.


## Features

- Custom network topology input in JSON format
- Path computation and logging for each protocol
- Evaluation metrics including:
  - Link utilization
  - Fairness
  - Path diversity
- Optional topology visualization

## Project Structure

```
.
├── main.py                  # Entry point for running the routing simulations
├── topology.json            # Network topology in JSON format
├── protocols/
│   ├── ospf.py              # OSPF protocol implementation
│   ├── ecmp.py              # ECMP protocol implementation
│   └── dmpf.py              # DMPF protocol implementation
├── utils/
│   ├── topology_loader.py   # Helper module for loading and parsing topology JSON
│   └── visualize.py         # (Optional) Topology visualization
├── evaluate.py              # Script to evaluate and compare routing protocol performance
├── paths/
│   ├── ospf_paths.csv       # Computed paths using OSPF
│   ├── ecmp_paths.csv       # Computed paths using ECMP
│   └── dmpf_paths.csv       # Computed paths using DMPF
```

## How to Run

Run the simulator by specifying the protocol you want to test:

```bash
python main.py --protocol OSPF
python main.py --protocol ECMP
python main.py --protocol DMPF
```

By default, the simulation uses `topology.json` in the root directory. To use a different topology file, pass the `--topology` argument:

```bash
python main.py --protocol DMPF --topology custom_topology.json
```
