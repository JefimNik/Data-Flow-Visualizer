import streamlit as st
import yaml
import pandas as pd
from pyvis.network import Network
import tempfile
import os
import uuid

# ---------- Загрузка модели ----------
@st.cache_data
def load_model(path="data_model.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

model = load_model()
nodes = model["nodes"]
edges = model["edges"]

layer_colors = {
    "SharePoint": "#FFD580",
    "PowerQuery": "#85C1E9",
    "Output": "#58D68D"
}

# ---------- Конфигурация ----------
st.set_page_config(page_title="Data Lineage Visualizer", layout="wide")
st.title("📊 Data Model & Lineage Viewer (упрощённый)")
st.caption("Выбери узел слева, чтобы увидеть детали справа")

if "selected_node" not in st.session_state:
    st.session_state.selected_node = None

left, right = st.columns([2, 1])

# ---------- Левая панель ----------
with left:
    st.markdown("### 🔗 Взаимосвязи таблиц")

    # создаём граф
    net = Network(height="750px", width="100%", bgcolor="#202225", font_color="white", directed=True)
    for node in nodes:
        color = layer_colors.get(node["layer"], "#AAAAAA")
        net.add_node(node["name"], label=node["name"], color=color)
    for e in edges:
        net.add_edge(e["from"], e["to"], color="#AAAAAA")

    tmp_path = os.path.join(tempfile.gettempdir(), f"graph_{uuid.uuid4().hex}.html")
    net.save_graph(tmp_path)

    with open(tmp_path, "r", encoding="utf-8") as f:
        html_code = f.read()
    st.components.v1.html(html_code, height=750, scrolling=True)

    # список для выбора узла (здесь реальное взаимодействие)
    st.markdown("### 🧭 Выбор таблицы")
    selected = st.selectbox("Выбери таблицу", [n["name"] for n in nodes])
    if st.button("Показать детали"):
        st.session_state.selected_node = selected

# ---------- Правая панель ----------
with right:
    st.markdown("### 🔍 Детали таблицы")

    node_name = st.session_state.selected_node
    if not node_name:
        st.info("Выбери таблицу и нажми «Показать детали»")
    else:
        node = next((n for n in nodes if n["name"] == node_name), None)
        if node:
            st.subheader(node["name"])
            st.markdown(f"**Уровень:** {node['layer']}")
            st.markdown(f"**Тип:** {node['type']}")
            st.markdown(f"**Комментарий:** {node.get('comment', '-')}")
            all_rows = []
            for sheet in node.get("sheets", []):
                for col in sheet.get("columns", []):
                    all_rows.append({
                        "Sheet": sheet["name"],
                        "Column": col["name"],
                        "Link": col.get("link", ""),
                        "Comment": col.get("comment", "")
                    })
            if all_rows:
                st.dataframe(pd.DataFrame(all_rows), use_container_width=True, height=450)
            else:
                st.write("Нет данных о колонках")

            st.markdown("**Входящие связи:**")
            incoming = [e["from"] for e in edges if e["to"] == node_name]
            st.write(incoming or "-")

            st.markdown("**Исходящие связи:**")
            outgoing = [e["to"] for e in edges if e["from"] == node_name]
            st.write(outgoing or "-")
