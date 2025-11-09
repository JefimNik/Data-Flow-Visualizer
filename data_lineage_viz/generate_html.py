import json, yaml, pathlib

TEMPLATE = "html_template.html"
YAML_FILE = "data_model.yaml"
OUTPUT = "data_model.html"

def main():
    tpl = pathlib.Path(TEMPLATE).read_text(encoding="utf-8")
    model = yaml.safe_load(pathlib.Path(YAML_FILE).read_text(encoding="utf-8"))

    nodes_in = model.get("nodes", [])
    edges_in = model.get("edges", [])

    # 1) Правый сайдбар: словарь -> id узла => метаданные и колонки
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

    # 2) Узлы для vis-network. Лейбл с переносом строки: реальный \n
    vis_nodes = []
    for n in nodes_in:
        label = f"{n['name']}\n({n.get('layer','')})"  # важен реальный \n
        vis_nodes.append({
            "id": n["name"],
            "label": label,
            "group": n.get("layer","") or "Default"
        })

    # 3) Рёбра
    vis_edges = [{"from": e["from"], "to": e["to"], "arrows":"to"} for e in edges_in]

    # Безопасно вставляем JSON внутрь <script type="application/json">
    html = (tpl
        .replace("__NODE_DATA__", json.dumps(node_data, ensure_ascii=False))
        .replace("__VIS_NODES__", json.dumps(vis_nodes, ensure_ascii=False))
        .replace("__VIS_EDGES__", json.dumps(vis_edges, ensure_ascii=False))
    )

    pathlib.Path(OUTPUT).write_text(html, encoding="utf-8")
    print(f"✅ Сгенерировано: {pathlib.Path(OUTPUT).resolve()}")

if __name__ == "__main__":
    main()
