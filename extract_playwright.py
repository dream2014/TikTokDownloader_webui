import os
import zipfile
import shutil

base_dir = r"C:\Users\kk\AppData\Local\ms-playwright"

# 定义需要解压的文件和对应的目录
files_to_extract = [
    {
        "zip_file": "chrome-win64.zip",
        "target_dir": "chromium-1208",
        "subdir": "chrome-win64"
    },
    {
        "zip_file": "chrome-headless-shell-win64.zip",
        "target_dir": "chromium_headless_shell-1208",
        "subdir": "chrome-headless-shell-win64"
    },
    {
        "zip_file": "firefox-win64.zip",
        "target_dir": "firefox-1509",
        "subdir": ""
    },
    {
        "zip_file": "webkit-win64.zip",
        "target_dir": "webkit-2248",
        "subdir": ""
    },
    {
        "zip_file": "ffmpeg-win64.zip",
        "target_dir": "ffmpeg-1011",
        "subdir": ""
    },
    {
        "zip_file": "winldd-win64.zip",
        "target_dir": "winldd-1007",
        "subdir": ""
    }
]

print("开始解压Playwright浏览器文件...")
print(f"基础目录: {base_dir}")

for item in files_to_extract:
    zip_path = os.path.join(base_dir, item["zip_file"])
    target_dir = os.path.join(base_dir, item["target_dir"])
    
    print(f"\n处理: {item['zip_file']}")
    
    # 检查zip文件是否存在
    if not os.path.exists(zip_path):
        print(f"  跳过: 文件不存在 - {zip_path}")
        continue
    
    # 如果目标目录已存在，先备份或清理
    if os.path.exists(target_dir):
        backup_dir = f"{target_dir}.backup"
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        shutil.move(target_dir, backup_dir)
        print(f"  备份现有目录到: {backup_dir}")
    
    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)
    print(f"  创建目标目录: {target_dir}")
    
    # 解压文件
    print(f"  正在解压...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)
    
    # 如果需要子目录
    if item["subdir"]:
        # 检查解压后的内容
        extracted_contents = os.listdir(target_dir)
        print(f"  解压后的内容: {extracted_contents}")
    
    print(f"  完成: {item['zip_file']}")

print("\n所有文件解压完成！")

# 验证目录结构
print("\n验证目录结构:")
for item in files_to_extract:
    target_dir = os.path.join(base_dir, item["target_dir"])
    if os.path.exists(target_dir):
        contents = os.listdir(target_dir)
        print(f"{item['target_dir']}: {len(contents)} 个文件/目录")
    else:
        print(f"{item['target_dir']}: 目录不存在")
