import sys
import webbrowser
import time
import socket
import os
import subprocess
from asyncio import run
from src.application import TikTokDownloader
from src.custom import PROJECT_ROOT

def kill_process_on_port(port):
    """终止在指定端口上运行的进程"""
    try:
        # 使用 netstat 命令查找在指定端口上运行的进程
        if sys.platform == 'win32':
            # Windows 系统
            cmd = f'netstat -ano | findstr :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                # 解析输出，获取进程ID
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        pid = parts[4]
                        # 终止进程
                        try:
                            subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
                            print(f"已终止在端口 {port} 上运行的进程 (PID: {pid})")
                        except subprocess.CalledProcessError:
                            print(f"终止进程 {pid} 失败")
        else:
            # Linux/macOS 系统
            cmd = f'lsof -i :{port}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                # 解析输出，获取进程ID
                lines = result.stdout.strip().split('\n')[1:]  # 跳过标题行
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        # 终止进程
                        try:
                            subprocess.run(f'kill -9 {pid}', shell=True, check=True)
                            print(f"已终止在端口 {port} 上运行的进程 (PID: {pid})")
                        except subprocess.CalledProcessError:
                            print(f"终止进程 {pid} 失败")
    except Exception as e:
        print(f"检测并终止进程时发生错误: {e}")

# 检测并终止在端口 5555 上运行的进程
print("正在检测是否有服务器进程在运行...")
kill_process_on_port(5555)
print("检测完成，准备启动新服务器...")

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
            print("请查看上面的错误信息，按任意键退出...")
            input()

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
