#!/usr/bin/env python3
"""
最简单的输入法测试程序
"""

import os
import sys

# 设置环境变量
os.environ['QT_IM_MODULE'] = 'fcitx'
os.environ['XMODIFIERS'] = '@im=fcitx'
os.environ['GTK_IM_MODULE'] = 'fcitx'
os.environ['QT_QPA_PLATFORM'] = 'xcb'  # 强制使用X11

from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt

class SimpleTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("简单输入法测试")
        self.setGeometry(300, 300, 300, 100)
        
        layout = QVBoxLayout()
        
        label = QLabel("测试中文输入:")
        layout.addWidget(label)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请输入中文...")
        layout.addWidget(self.input_field)
        
        self.setLayout(layout)
        
        # 聚焦到输入框
        self.input_field.setFocus()

def main():
    app = QApplication(sys.argv)
    
    print("环境变量:")
    for key in ['QT_IM_MODULE', 'XMODIFIERS', 'GTK_IM_MODULE', 'QT_QPA_PLATFORM']:
        print(f"{key}={os.environ.get(key)}")
    
    widget = SimpleTest()
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()