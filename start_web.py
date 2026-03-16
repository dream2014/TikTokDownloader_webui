import sys
import webbrowser
import time
import socket
import os
from asyncio import run
from src.application import TikTokDownloader
from src.custom import PROJECT_ROOT

# 打印当前工作目录
print(f"当前工作目录: {os.getcwd()}")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")

async def start_server():
    """直接启动服务器"""
    async with TikTokDownloader() as downloader:
        try:
            # 直接启动 Web UI 模式
            await downloader.web_ui()
        except Exception as e:
            print(f"服务器启动失败: {e}")
            import traceback
            traceback.print_exc()

def check_server_ready(port=5555, timeout=30):
    """检查服务器是否在指定端口上启动"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(('localhost', port))
            return True
        except (ConnectionRefusedError, socket.timeout):
            time.sleep(1)
    return False

# 启动服务器
print("正在启动服务器...")

# 启动服务器在后台
import threading
threading.Thread(target=lambda: run(start_server()), daemon=True).start()

# 等待服务器启动
print("正在等待服务器启动...")
if check_server_ready():
    print("服务器已启动，正在打开Web UI界面...")
    webbrowser.open('http://127.0.0.1:5555/web')
else:
    print("服务器启动超时，无法打开Web UI界面")

# 保持主进程运行
print("服务器已启动，按Ctrl+C退出...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("正在关闭服务器...")
