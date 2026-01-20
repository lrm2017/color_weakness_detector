#!/usr/bin/env python3
"""
PyQt5输入法测试程序
"""

import os
import sys

# 设置环境变量
os.environ['QT_IM_MODULE'] = 'fcitx'
os.environ['XMODIFIERS'] = '@im=fcitx'
os.environ['GTK_IM_MODULE'] = 'fcitx'

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton
from PyQt5.QtCore import Qt

class InputTest(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 输入法测试")
        self.setGeometry(300, 300, 400, 200)
        
        layout = QVBoxLayout()
        
        # 说明
        info = QLabel("测试步骤:\n1. 点击下面的输入框\n2. 按 Ctrl+Space 切换输入法\n3. 输入拼音测试")
        info.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; }")
        layout.addWidget(info)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("请在这里测试中文输入...")
        self.input_field.setStyleSheet("QLineEdit { font-size: 16px; padding: 8px; }")
        layout.addWidget(self.input_field)
        
        # 显示输入内容
        self.display = QLabel("输入内容将显示在这里")
        self.display.setStyleSheet("QLabel { border: 1px solid #ccc; padding: 10px; min-height: 30px; }")
        layout.addWidget(self.display)
        
        # 测试按钮
        test_btn = QPushButton("测试输入法状态")
        test_btn.clicked.connect(self.test_input_method)
        layout.addWidget(test_btn)
        
        self.setLayout(layout)
        
        # 连接信号
        self.input_field.textChanged.connect(self.on_text_changed)
        
        # 聚焦到输入框
        self.input_field.setFocus()
    
    def on_text_changed(self, text):
        self.display.setText(f"输入内容: {text}")
    
    def test_input_method(self):
        import subprocess
        try:
            # 检查fcitx5状态
            result = subprocess.run(['fcitx5-remote', '-s'], capture_output=True, text=True)
            if result.returncode == 0:
                status = "激活" if result.stdout.strip() == "2" else "未激活"
                self.display.setText(f"fcitx5状态: {status}")
            else:
                self.display.setText("无法检查fcitx5状态")
        except:
            self.display.setText("fcitx5-remote命令不可用")

def main():
    app = QApplication(sys.argv)
    
    print("PyQt5输入法测试")
    print("环境变量:")
    for key in ['QT_IM_MODULE', 'XMODIFIERS', 'GTK_IM_MODULE']:
        print(f"  {key}={os.environ.get(key)}")
    
    widget = InputTest()
    widget.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()