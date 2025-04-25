def load_topology(path):
    import json
    with open(path) as f:
        return json.load(f)