import pathlib, json, yaml

BASE = pathlib.Path(__file__).resolve().parent.parent  # корень проекта
TEMPLATE = BASE / "src" / "html_template.html"
YAML_FILE = BASE / "config" / "data_model.yaml"
SETTINGS_FILE = BASE / "config" / "settings.yaml"
OUTPUT = BASE / "build" / "data_model_v1.html"


def textify(v):
    """Принудительно преобразует всё в текст (включая ключи и значения)."""
    if isinstance(v, dict):
        return {str(k): textify(vv) for k, vv in v.items()}
    if isinstance(v, list):
        return [textify(x) for x in v]
    return "" if v is None else str(v)


def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    data_model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))
    settings = yaml.safe_load(pathlib.Path(SETTINGS_FILE).read_text(encoding="utf-8"))

    nodes = data_model.get("nodes", [])
    edges = data_model.get("edges", [])

    vis_nodes = [{
        "id": str(n.get("name", "")),
        "label": f"{n.get('name', '')}\n({n.get('layer', '')})",
        "group": str(n.get("layer", ""))
    } for n in nodes]

    vis_edges = []
    for i, e in enumerate(edges):
        t_type = str(e.get("transfer_type", "pq"))
        d_type = str(e.get("data_type", "general"))
        color = settings["colors"]["data_type"].get(d_type, "#cfcfcf")
        tstyle = settings["colors"]["transfer_type"].get(t_type, {"dashes": False, "opacity": 1})
        rgba = f"rgba({int(color[1:3],16)}, {int(color[3:5],16)}, {int(color[5:7],16)}, {tstyle['opacity']})"
        vis_edges.append({
            "id": f"edge_{i}_{e['from']}_{e['to']}",
            "from": str(e["from"]),
            "to": str(e["to"]),
            "transfer": textify(e.get("transfer", [])),
            "transfer_type": t_type,
            "data_type": d_type,
            "color": rgba,
            "dashes": tstyle["dashes"],
            "arrows": {"to": {"enabled": True, "type": "arrow", "scaleFactor": 0.8}},
            "length": 250
        })

    # --- ДОБАВЛЯЕМ node_data с сохранением порядка колонок ---
    node_data = {}
    for n in nodes:
        columns = n.get("columns", [])
        # Преобразуем каждую строку в OrderedDict, сохраняя порядок ключей
        ordered_cols = []
        for row in columns:
            if isinstance(row, dict):
                ordered_cols.append({str(k): str(v or "") for k, v in row.items()})
            else:
                ordered_cols.append({})
        node_data[str(n.get("name", ""))] = {
            "layer": str(n.get("layer", "")),
            "type": str(n.get("type", "")),
            "comment": str(n.get("comment", "")),
            "columns": ordered_cols,
        }


    html = tpl.replace("__NODE_DATA__", json.dumps(node_data, ensure_ascii=False))
    html = html.replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
    html = html.replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))

    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")


if __name__ == "__main__":
    main()
