import json, yaml, pathlib

TEMPLATE = "html_template.html"
YAML_FILE = "data_model.yaml"
OUTPUT = "data_model.html"

def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))

    nodes_in = model.get("nodes", [])
    edges_in = model.get("edges", [])

    # --- узлы ---
    node_data = {}
    for n in nodes_in:
        cols = []
        for sh in n.get("sheets", []) or []:
            for c in sh.get("columns", []) or []:
                cols.append({
                    "Sheet": sh.get("name", ""),
                    "Column": c.get("name", ""),
                    "Link": c.get("link", ""),
                    "Comment": c.get("comment", ""),
                })
        node_data[n["name"]] = {
            "layer": n.get("layer", ""),
            "type": n.get("type", ""),
            "comment": n.get("comment", ""),
            "columns": cols,
        }

    vis_nodes = [
        {"id": n["name"], "label": f"{n['name']}\n({n.get('layer','')})", "group": n.get("layer", "")}
        for n in nodes_in
    ]

    vis_edges = []
    for i, e in enumerate(edges_in):
        vis_edges.append({
            "id": f"edge_{i}_{e['from']}_{e['to']}",
            "from": e["from"],
            "to": e["to"],
            "transfer": e.get("transfer", []),
            "transfer_type": e.get("transfer_type", "pq"),
            "data_type": e.get("data_type", "general"),
            "color": "rgba(200,200,200,1)",
            "arrows": {"to": {"enabled": True, "type": "arrow"}},
            "length": 250
        })

    html = tpl.replace("__NODE_DATA__", json.dumps(node_data, ensure_ascii=False))
    html = html.replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
    html = html.replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))

    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")

if __name__ == "__main__":
    main()
