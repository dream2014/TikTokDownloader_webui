from playwright.sync_api import Playwright, sync_playwright

# 尝试安装Playwright浏览器
try:
    print("正在安装Playwright浏览器...")
    # 使用sync_playwright来安装浏览器
    with sync_playwright() as p:
        print("Playwright初始化成功")
        print("浏览器安装完成")
except Exception as e:
    print(f"安装过程中出现错误: {e}")

print("安装完成")