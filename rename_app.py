import os
import json
import shutil
import subprocess
import re

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}

def resize_icon(src_png, android_dir):
    if not HAS_PIL:
        print("⚠ 缺少 Pillow 库，跳过图标替换")
        print("  运行: pip install Pillow")
        return
    
    img = Image.open(src_png).convert("RGBA")
    
    for folder, size in SIZES.items():
        resized = img.resize((size, size), Image.LANCZOS)
        res_dir = os.path.join(android_dir, "app", "src", "main", "res", folder)
        os.makedirs(res_dir, exist_ok=True)
        
        for name in ["ic_launcher.png", "ic_launcher_round.png", "ic_launcher_foreground.png"]:
            resized.save(os.path.join(res_dir, name))
        
        print(f"✓ 已生成 {folder}/{name} ({size}x{size})")

def rename_app(project_dir, app_name, icon_path=None):
    app_id = f"com.{app_name}.app"
    android_dir = os.path.join(project_dir, "android")
    
    if not os.path.exists(android_dir):
        print(f"错误: 找不到 android 目录，请先运行 npx cap add android")
        return
    
    # 1. capacitor.config.json
    config_path = os.path.join(project_dir, "capacitor.config.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        config["appName"] = app_name
        config["appId"] = app_id
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✓ 已更新 capacitor.config.json")
    
    # 2. strings.xml
    strings_path = os.path.join(android_dir, "app", "src", "main", "res", "values", "strings.xml")
    if os.path.exists(strings_path):
        with open(strings_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'<string name="app_name">[^<]*</string>', 
                        f'<string name="app_name">{app_name}</string>', content)
        content = re.sub(r'<string name="title_activity_main">[^<]*</string>', 
                        f'<string name="title_activity_main">{app_name}</string>', content)
        content = re.sub(r'<string name="package_name">[^<]*</string>', 
                        f'<string name="package_name">{app_id}</string>', content)
        content = re.sub(r'<string name="custom_url_scheme">[^<]*</string>', 
                        f'<string name="custom_url_scheme">{app_id}</string>', content)
        with open(strings_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ 已更新 strings.xml")
    
    # 3. app/build.gradle (关键！)
    app_gradle = os.path.join(android_dir, "app", "build.gradle")
    if os.path.exists(app_gradle):
        with open(app_gradle, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'namespace\s*=\s*"[^"]*"', f'namespace = "{app_id}"', content)
        content = re.sub(r'applicationId\s+"[^"]*"', f'applicationId "{app_id}"', content)
        with open(app_gradle, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ 已更新 app/build.gradle")
    
    # 4. 替换图标
    if icon_path and os.path.exists(icon_path):
        resize_icon(icon_path, android_dir)
    elif icon_path:
        print(f"⚠ 找不到图标文件: {icon_path}")
    
    # 5. MainActivity.java
    java_src = os.path.join(android_dir, "app", "src", "main", "java")
    main_activity = None
    for root, dirs, files in os.walk(java_src):
        if "MainActivity.java" in files:
            main_activity = os.path.join(root, "MainActivity.java")
            break
    
    if main_activity and os.path.exists(main_activity):
        with open(main_activity, "r", encoding="utf-8") as f:
            content = f.read()
        content = re.sub(r'package\s+[^;]+;', f'package {app_id};', content)
        
        package_parts = app_id.split(".")
        new_package_dir = os.path.join(java_src, *package_parts)
        os.makedirs(new_package_dir, exist_ok=True)
        
        new_main_activity = os.path.join(new_package_dir, "MainActivity.java")
        with open(new_main_activity, "w", encoding="utf-8") as f:
            f.write(content)
        
        old_package_dir = os.path.dirname(main_activity)
        if old_package_dir != new_package_dir and os.path.exists(old_package_dir):
            shutil.rmtree(old_package_dir, ignore_errors=True)
            parent = os.path.dirname(old_package_dir)
            while parent != java_src:
                try:
                    if not os.listdir(parent):
                        os.rmdir(parent)
                    parent = os.path.dirname(parent)
                except:
                    break
        
        print(f"✓ 已更新 MainActivity.java")
    
    # 6. 清理 build
    build_dir = os.path.join(android_dir, "app", "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir, ignore_errors=True)
        print(f"✓ 已清理 build 目录")
    
    # 7. cap sync
    print(f"\n执行 npx cap sync...")
    result = subprocess.run(["npx", "cap", "sync"], cwd=project_dir, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ npx cap sync 完成")
    else:
        print(f"✗ npx cap sync 失败: {result.stderr}")
    
    print(f"\n=== 完成！名称: {app_name}，包名: {app_id} ===")

if __name__ == "__main__":
    # ====== 在这里修改 ======
    APP_NAME = "timeliss"
    ICON_PATH = "02.png"
    # ========================
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    if ICON_PATH and not os.path.isabs(ICON_PATH):
        ICON_PATH = os.path.join(project_dir, ICON_PATH)
    
    rename_app(project_dir, APP_NAME, ICON_PATH)
