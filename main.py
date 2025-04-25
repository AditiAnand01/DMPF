from protocols import ospf, ecmp, dmpf
from utils.topology_loader import load_topology
import argparse

# Simulation program
def main():
    parser = argparse.ArgumentParser(description="Protocol simulation")
    parser.add_argument("--protocol", type=str, choices=["OSPF", "ECMP","DMPF"], required=True, help="Routing protocol to use")
    parser.add_argument("--topology", type=str, default="topology.json", help="Path to topology JSON file")
    args = parser.parse_args()

    # Load network topology from the given JSON file
    topology = load_topology(args.topology)

    # Run the selected protocol simulation
    if args.protocol == "OSPF":
        ospf.run(topology)
    elif args.protocol == "ECMP":
        ecmp.run(topology)
    elif args.protocol == "DMPF":
        dmpf.run(topology)
    else:
        print("Please enter correct protocol name")

if __name__ == "__main__":
    main()