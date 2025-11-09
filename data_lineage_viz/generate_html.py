import json, yaml, pathlib

TEMPLATE = "html_template.html"
YAML_FILE = "data_model.yaml"
OUTPUT = "data_model.html"

def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))

    nodes_in = model.get("nodes", [])
    edges_in = model.get("edges", [])

    # --- данные узлов
    node_data = {}
    for n in nodes_in:
        cols = []
        for sh in n.get("sheets", []) or []:
            for c in sh.get("columns", []) or []:
                cols.append({
                    "Sheet": sh.get("name",""),
                    "Column": c.get("name",""),
                    "Link": c.get("link",""),
                    "Comment": c.get("comment",""),
                })
        node_data[n["name"]] = {
            "layer": n.get("layer",""),
            "type": n.get("type",""),
            "comment": n.get("comment",""),
            "columns": cols
        }

    # --- узлы
    vis_nodes = []
    for n in nodes_in:
        label = f"{n['name']}\n({n.get('layer','')})"
        vis_nodes.append({
            "id": n["name"],
            "label": label,
            "group": n.get("layer",""),
        })

    # --- стили стрелок (5 типов)
    edge_styles = {
        "normal":          {"color": "rgba(180,180,180,1)",   "dashes": False, "type": "arrow"},
        "manual":          {"color": "rgba(255,223,107,1)",   "dashes": True,  "type": "arrow"},
        "planned":         {"color": "rgba(150,150,150,0.25)","dashes": False, "type": "arrow"},
        "normal_diamond":  {"color": "rgba(180,180,180,1)",   "dashes": False, "type": "diamond"},
        "normal_bar":      {"color": "rgba(180,180,180,1)",   "dashes": False, "type": "bar"},
    }

    vis_edges = []
    for e in edges_in:
        etype = e.get("type", "normal")
        style = edge_styles.get(etype, edge_styles["normal"])
        vis_edges.append({
            "from": e["from"],
            "to": e["to"],
            "arrows": { "to": { "enabled": True, "type": style["type"], "scaleFactor": 0.7 } },
            "color": style["color"],
            "dashes": style["dashes"],
            "type": etype,
        })

    html = (
        tpl
        .replace("__NODE_DATA__", json.dumps(node_data, ensure_ascii=False))
        .replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
        .replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))
    )

    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")

if __name__ == "__main__":
    main()
