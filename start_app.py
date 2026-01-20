#!/usr/bin/env python3
"""
启动器 - 确保正确的输入法环境
"""

import os
import sys
import subprocess

def main():
    # 设置fcitx5环境变量
    os.environ['QT_IM_MODULE'] = 'fcitx5'
    os.environ['XMODIFIERS'] = '@im=fcitx5'
    os.environ['GTK_IM_MODULE'] = 'fcitx5'
    
    # 检查fcitx5是否运行
    try:
        subprocess.run(['pgrep', '-x', 'fcitx5'], check=True, capture_output=True)
        print("fcitx5 正在运行")
    except subprocess.CalledProcessError:
        print("启动 fcitx5...")
        subprocess.Popen(['fcitx5', '-d'])
        import time
        time.sleep(2)
    
    print("环境变量设置:")
    print(f"QT_IM_MODULE={os.environ.get('QT_IM_MODULE')}")
    print(f"XMODIFIERS={os.environ.get('XMODIFIERS')}")
    print(f"GTK_IM_MODULE={os.environ.get('GTK_IM_MODULE')}")
    
    # 导入并运行主程序
    print("启动色弱图谱识别程序...")
    from gui_app import main as gui_main
    gui_main()

if __name__ == "__main__":
    main()