import json, yaml, pathlib

TEMPLATE = "html_template.html"
YAML_FILE = "data_model.yaml"
OUTPUT = "data_model.html"

def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))

    nodes_in = model.get("nodes", [])
    edges_in = model.get("edges", [])

    node_data = {n["name"]: {"layer": n.get("layer",""), "type": n.get("type",""), "comment": n.get("comment","")} for n in nodes_in}
    vis_nodes = [{"id": n["name"], "label": f"{n['name']}\n({n.get('layer','')})", "group": n.get("layer","")} for n in nodes_in]

    # Тип линии (форма)
    style_map = {
        "pq":       {"dashes": False, "opacity": 1.0},
        "manual":   {"dashes": True,  "opacity": 1.0},
        "planned":  {"dashes": False, "opacity": 0.3},
        "default":  {"dashes": False, "opacity": 1.0},
    }

    # Цвет по типу данных
    color_map = {
        "workers":    "#66c2a5",
        "progress":   "#fc8d62",
        "hours":      "#8da0cb",
        "cost":       "#e78ac3",
        "materials":  "#a6d854",
        "documents":  "#ffd92f",
        "general":    "#cfcfcf",
    }

    vis_edges = []
    for i, e in enumerate(edges_in):
        t_type = e.get("transfer_type", "default")
        d_type = e.get("data_type", "general")
        s = style_map.get(t_type, style_map["default"])
        color = color_map.get(d_type, color_map["general"])
        vis_edges.append({
            "id": f"edge_{i}_{e['from']}_{e['to']}",
            "from": e["from"],
            "to": e["to"],
            "transfer": e.get("transfer", []),
            "transfer_type": t_type,
            "data_type": d_type,
            "color": f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, {s['opacity']})",
            "dashes": s["dashes"],
            "arrows": {"to": {"enabled": True, "type": "arrow", "scaleFactor": 0.8}},
            "length": 250
        })

    html = tpl.replace("__NODE_DATA__", json.dumps(node_data, ensure_ascii=False))
    html = html.replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
    html = html.replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))
    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")

if __name__ == "__main__":
    main()
