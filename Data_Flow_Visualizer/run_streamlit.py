import subprocess
import sys
import pathlib

# Путь к твоему Streamlit приложению
APP_PATH = pathlib.Path(__file__).parent / "app_streamlit.py"

def main():
    # Проверяем, что файл существует
    if not APP_PATH.exists():
        print("❌ Не найден app_streamlit.py")
        sys.exit(1)

    print("🚀 Запуск Streamlit приложения...")
    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", str(APP_PATH)],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Ошибка при запуске Streamlit: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Прервано пользователем.")

if __name__ == "__main__":
    main()
