#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ensure_deps.py —— 运行前自动检查并安装缺失的第三方依赖
import importlib
import subprocess
import sys

# (import 名, pip 包名) —— 应与 requirements.txt 保持一致
REQUIRED = [
    ("lxml", "lxml"),
    ("requests", "requests"),
    ("flask", "Flask"),
    ("werkzeug", "Werkzeug"),
    ("numpy", "numpy"),
    ("ddddocr", "ddddocr"),
    ("cv2", "opencv-python"),
    ("customtkinter", "customtkinter"),
]


def ensure():
    missing = []
    for mod, pkg in REQUIRED:
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(pkg)
    if missing:
        print("检测到缺少依赖，正在自动安装：%s" % ", ".join(missing))
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        except subprocess.CalledProcessError as e:
            print("自动安装失败（可手动 pip install -r requirements.txt）：%s" % e)
            return False
        # 复核
        for mod, pkg in REQUIRED:
            try:
                importlib.import_module(mod)
            except ImportError:
                print("警告：仍无法导入 %s，请手动安装 %s" % (mod, pkg))
    else:
        print("依赖检查通过。")
    return True


if __name__ == "__main__":
    ensure()
