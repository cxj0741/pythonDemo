# app.py
import subprocess
import threading
import time

def run_data_fetcher():
    subprocess.run(["python", "DataDigger.py"])

def run_api_server():
    subprocess.run(["python", "api_server.py"])

if __name__ == '__main__':
    fetcher_thread = threading.Thread(target=run_data_fetcher)
    api_thread = threading.Thread(target=run_api_server)

    fetcher_thread.start()
    time.sleep(5)  # 确保数据抓取器先启动
    api_thread.start()

    fetcher_thread.join()
    api_thread.join()
