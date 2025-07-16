import json


def load_tokens(server_name):
    try:
        if server_name == "IND":
            path = "tokens/ind.json"
        elif server_name in {"BR", "US", "SAC", "NA"}:
            path = "tokens/br.json"
        else:
            path = "tokens/bd.json"
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None
