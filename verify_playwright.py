from playwright.sync_api import sync_playwright

# 验证Playwright是否安装成功
try:
    with sync_playwright() as p:
        print('Playwright初始化成功')
        print('Chromium版本:', p.chromium.version)
        print('验证成功！')
except Exception as e:
    print(f'验证过程中出现错误: {e}')
