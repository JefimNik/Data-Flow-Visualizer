import subprocess, pathlib, datetime
print("🚀 Запуск пайплайна Data Flow Visualizer...")
timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
subprocess.run(["python","src/generate_html.py"], check=True)
pathlib.Path("docs/build_log.txt").write_text(f"Build at {timestamp}\n", encoding="utf-8")
print("✅ Пайплайн завершён успешно.")
