#!/usr/bin/env python3
"""
使用PyQt5的输入法测试程序
"""

import os
import sys

# 设置环境变量
os.environ['QT_IM_MODULE'] = 'fcitx5'
os.environ['XMODIFIERS'] = '@im=fcitx5'
os.environ['GTK_IM_MODULE'] = 'fcitx5'

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLineEdit, QLabel
from PyQt5.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 输入法测试")
        self.setGeometry(300, 300, 400, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        label = QLabel("请在下面的文本框中测试中文输入 (PyQt5):")
        layout.addWidget(label)
        
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("在这里输入中文...")
        layout.addWidget(self.text_input)
        
        result_label = QLabel("输入的内容会显示在这里:")
        layout.addWidget(result_label)
        
        self.result_text = QLabel("")
        self.result_text.setStyleSheet("QLabel { border: 1px solid gray; padding: 5px; }")
        layout.addWidget(self.result_text)
        
        self.text_input.textChanged.connect(self.on_text_changed)
        
        # 自动聚焦到输入框
        self.text_input.setFocus()
    
    def on_text_changed(self, text):
        self.result_text.setText(f"输入内容: {text}")

def main():
    app = QApplication(sys.argv)
    
    print("PyQt5 环境变量:")
    print(f"QT_IM_MODULE={os.environ.get('QT_IM_MODULE')}")
    print(f"XMODIFIERS={os.environ.get('XMODIFIERS')}")
    print(f"GTK_IM_MODULE={os.environ.get('GTK_IM_MODULE')}")
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()