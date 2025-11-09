import streamlit as st
import pandas as pd
import yaml
import pathlib
import subprocess
import os
from io import BytesIO
import openpyxl

# --------- Пути ---------
BASE = pathlib.Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config" / "data_model.yaml"
GENERATOR = BASE / "src" / "generate_html.py"
BUILD_HTML = BASE / "build" / "data_model_v1.html"


# --------- Работа с YAML ---------
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        f.flush()
        os.fsync(f.fileno())


# --------- Генерация HTML ---------
def generate_html():
    try:
        result = subprocess.run(["python", str(GENERATOR)], capture_output=True, text=True)
        if result.returncode != 0:
            st.error("❌ Ошибка при генерации HTML:")
            st.code(result.stderr or result.stdout)
        else:
            st.success("✅ HTML успешно сгенерирован.")
    except Exception as e:
        st.error(f"⚠️ Не удалось запустить генерацию: {e}")


# --------- Универсальная текстовая очистка ---------
def textify(value):
    if isinstance(value, dict):
        return {str(k): textify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [textify(v) for v in value]
    if value is None:
        return ""
    return str(value)


# --------- Создание Excel-шаблона для всей модели ---------
def make_excel(data_model: dict) -> BytesIO:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        # ----- Лист 1: Узлы -----
        nodes = data_model.get("nodes", [])
        df_nodes = pd.DataFrame(
            [
                {
                    "name": n.get("name", ""),
                    "layer": n.get("layer", ""),
                    "type": n.get("type", ""),
                    "comment": n.get("comment", ""),
                }
                for n in nodes
            ]
        )
        df_nodes.to_excel(writer, sheet_name="Nodes", index=False)

        # ----- Лист 2: Колонки -----
        records = []
        for n in nodes:
            for col in n.get("columns", []):
                row = {"node_name": n.get("name", "")}
                for k, v in col.items():
                    row[k] = v
                records.append(row)
        df_cols = pd.DataFrame(records)
        df_cols.to_excel(writer, sheet_name="Columns", index=False)

        # ----- Лист 3: Связи -----
        edges = data_model.get("edges", [])
        df_edges = pd.DataFrame(edges)
        df_edges.to_excel(writer, sheet_name="Edges", index=False)

    buffer.seek(0)
    return buffer


# --------- Сборка YAML из Excel ---------
def rebuild_from_excel(uploaded_file) -> dict:
    wb = openpyxl.load_workbook(uploaded_file)
    data_model = {"nodes": [], "edges": []}

    # --- Узлы ---
    df_nodes = pd.DataFrame(wb["Nodes"].values)
    df_nodes.columns = df_nodes.iloc[0]
    df_nodes = df_nodes.drop(0).fillna("").astype(str)

    # --- Колонки ---
    if "Columns" in wb.sheetnames:
        df_cols = pd.DataFrame(wb["Columns"].values)
        df_cols.columns = df_cols.iloc[0]
        df_cols = df_cols.drop(0).fillna("").astype(str)
    else:
        df_cols = pd.DataFrame(columns=["node_name", "name", "type", "description", "comment"])

    # --- Связи ---
    if "Edges" in wb.sheetnames:
        df_edges = pd.DataFrame(wb["Edges"].values)
        df_edges.columns = df_edges.iloc[0]
        df_edges = df_edges.drop(0).fillna("").astype(str)
    else:
        df_edges = pd.DataFrame(columns=["from", "to", "transfer_type", "data_type", "transfer"])

    # --- Формируем узлы с колонками ---
    for _, n in df_nodes.iterrows():
        node_name = n["name"]
        cols_df = df_cols[df_cols["node_name"] == node_name].drop(columns=["node_name"], errors="ignore")
        node_dict = {
            "name": node_name,
            "layer": n.get("layer", ""),
            "type": n.get("type", ""),
            "comment": n.get("comment", ""),
            "columns": textify(cols_df.to_dict(orient="records")),
        }
        data_model["nodes"].append(node_dict)

    # --- Связи ---
    for _, e in df_edges.iterrows():
        e_dict = {str(k): str(v) for k, v in e.items()}
        data_model["edges"].append(e_dict)

    return data_model


# --------- Интерфейс Streamlit ---------
st.set_page_config(page_title="Data Flow Visualizer Editor", layout="wide")
st.title("🧩 Data Flow Visualizer — Полная модель данных")

if not CONFIG_PATH.exists():
    st.error(f"❌ Файл YAML не найден: {CONFIG_PATH}")
    st.stop()

data_model = load_yaml(CONFIG_PATH)

# ---------- ВЕРХНИЙ БЛОК ----------
st.subheader("📥 Экспорт и импорт всей модели")

col1, col2 = st.columns(2)

with col1:
    st.download_button(
        label="📤 Скачать всю модель в Excel",
        data=make_excel(data_model),
        file_name="data_model.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

with col2:
    uploaded = st.file_uploader("📥 Загрузить обновлённый Excel", type=["xlsx"])

    if uploaded is not None:
        try:
            new_model = rebuild_from_excel(uploaded)
            save_yaml(CONFIG_PATH, new_model)
            generate_html()
            st.success("✅ YAML обновлён и HTML перегенерирован.")
        except Exception as e:
            st.error(f"Ошибка при обработке Excel: {e}")

# ---------- НИЖНИЙ БЛОК ----------
st.markdown("---")
st.subheader("🔗 Визуализация модели данных")

try:
    if BUILD_HTML.exists():
        html_code = BUILD_HTML.read_text(encoding="utf-8")
        st.components.v1.html(html_code, height=850, scrolling=True)
    else:
        st.warning("⚠️ HTML не найден. Сначала экспортируйте и обновите YAML.")
except Exception as e:
    st.error(f"Ошибка отображения HTML: {e}")
