#!/usr/bin/env python3
"""
色弱图谱识别程序 - PyQt5版本（更好的输入法支持）
"""

import os
import sys

# 在导入任何Qt模块之前设置环境变量
os.environ['QT_IM_MODULE'] = 'fcitx'
os.environ['XMODIFIERS'] = '@im=fcitx'
os.environ['GTK_IM_MODULE'] = 'fcitx'

import json
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

# 使用PyQt5而不是PySide6
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QGroupBox, QStatusBar, 
    QLineEdit, QMessageBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QStandardPaths
from PyQt5.QtGui import QPixmap, QImage, QFont

# 程序目录和配置
APP_DIR = Path(__file__).parent.resolve()
IMAGES_DIR = APP_DIR / "downloaded_images"
WRONG_ANSWERS_DIR = IMAGES_DIR / "错题库"
CONFIG_DIR = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / "color_weakness_detector"
CONFIG_FILE = CONFIG_DIR / "config.json"
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("色弱图谱识别程序 - PyQt5版本")
        self.setMinimumSize(800, 600)
        
        self.image_list = []
        self.current_index = -1
        self.current_image = None
        self.current_image_path = None
        self.answers_data = {}
        self.correct_count = 0
        self.wrong_count = 0
        
        self._setup_ui()
        self._connect_signals()
        self._load_gallery_list()
        self._load_config()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 图库选择
        gallery_group = QGroupBox("图库选择")
        gallery_layout = QHBoxLayout(gallery_group)
        
        gallery_layout.addWidget(QLabel("选择图库:"))
        self.gallery_combo = QComboBox()
        self.gallery_combo.setMinimumWidth(200)
        gallery_layout.addWidget(self.gallery_combo)
        
        # 统计显示
        self.stats_label = QLabel("正确: 0 | 错误: 0")
        self.stats_label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        gallery_layout.addWidget(self.stats_label)
        
        self.reset_stats_btn = QPushButton("重置统计")
        gallery_layout.addWidget(self.reset_stats_btn)
        gallery_layout.addStretch()
        
        main_layout.addWidget(gallery_group)
        
        # 图像显示区域
        image_group = QGroupBox("图像")
        image_layout = QVBoxLayout(image_group)
        
        self.image_label = QLabel("请选择图库")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setStyleSheet("QLabel { background-color: #f0f0f0; border: 1px solid #ccc; }")
        image_layout.addWidget(self.image_label)
        
        main_layout.addWidget(image_group)
        
        # 答案输入区域
        answer_group = QGroupBox("答案输入")
        answer_layout = QVBoxLayout(answer_group)
        
        # 符号快捷面板
        symbols_layout = QHBoxLayout()
        symbols_layout.addWidget(QLabel("常用符号:"))
        
        symbols = ["○", "△", "□", "▽", "✩", "◇", "◆", "●", "▲", "■"]
        for symbol in symbols:
            btn = QPushButton(symbol)
            btn.setFixedSize(35, 35)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #e0e0e0; }
            """)
            btn.clicked.connect(lambda checked, s=symbol: self._insert_symbol(s))
            symbols_layout.addWidget(btn)
        
        symbols_layout.addStretch()
        answer_layout.addLayout(symbols_layout)
        
        # 输入框和按钮
        input_layout = QHBoxLayout()
        
        input_layout.addWidget(QLabel("答案:"))
        
        # 使用标准的QLineEdit，PyQt5对输入法支持更好
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("请输入答案（支持中文）...")
        self.answer_input.setMinimumWidth(200)
        font = QFont()
        font.setPointSize(14)
        self.answer_input.setFont(font)
        input_layout.addWidget(self.answer_input)
        
        self.submit_btn = QPushButton("提交")
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        input_layout.addWidget(self.submit_btn)
        
        # 答案显示
        self.answer_display = QLabel("???")
        self.answer_display.setAlignment(Qt.AlignCenter)
        display_font = QFont()
        display_font.setPointSize(18)
        display_font.setBold(True)
        self.answer_display.setFont(display_font)
        self.answer_display.setStyleSheet("QLabel { color: #333; padding: 10px; }")
        input_layout.addWidget(self.answer_display)
        
        self.show_answer_btn = QPushButton("显示答案")
        self.show_answer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        input_layout.addWidget(self.show_answer_btn)
        
        answer_layout.addLayout(input_layout)
        main_layout.addWidget(answer_group)
        
        # 导航控制
        nav_group = QGroupBox("导航")
        nav_layout = QHBoxLayout(nav_group)
        
        self.prev_btn = QPushButton("上一张")
        self.next_btn = QPushButton("下一张")
        self.random_btn = QPushButton("随机")
        self.image_info = QLabel("0 / 0")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_info)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.random_btn)
        nav_layout.addStretch()
        
        main_layout.addWidget(nav_group)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 请测试中文输入（按Ctrl+Space切换输入法）")
        
        self._update_button_states()
    
    def _connect_signals(self):
        """连接信号"""
        self.gallery_combo.currentIndexChanged.connect(self._on_gallery_changed)
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn.clicked.connect(self._next_image)
        self.random_btn.clicked.connect(self._random_image)
        self.submit_btn.clicked.connect(self._submit_answer)
        self.answer_input.returnPressed.connect(self._submit_answer)
        self.show_answer_btn.clicked.connect(self._show_answer)
        self.reset_stats_btn.clicked.connect(self._reset_stats)
    
    def _insert_symbol(self, symbol):
        """插入符号"""
        current_text = self.answer_input.text()
        cursor_pos = self.answer_input.cursorPosition()
        new_text = current_text[:cursor_pos] + symbol + current_text[cursor_pos:]
        self.answer_input.setText(new_text)
        self.answer_input.setCursorPosition(cursor_pos + len(symbol))
        self.answer_input.setFocus()
    
    def _submit_answer(self):
        """提交答案"""
        user_answer = self.answer_input.text().strip()
        if not user_answer:
            self.status_bar.showMessage("请输入答案")
            return
        
        if self.current_image_path is None:
            return
        
        filename = self.current_image_path.name
        correct_answer = self.answers_data.get(filename, "")
        
        if not correct_answer:
            self.status_bar.showMessage("该题目没有标准答案")
            return
        
        # 比较答案
        if user_answer.lower().replace(" ", "") == correct_answer.lower().replace(" ", ""):
            self.correct_count += 1
            self.answer_display.setText(f"✓ {correct_answer}")
            self.answer_display.setStyleSheet("QLabel { color: #4CAF50; padding: 10px; }")
            self.status_bar.showMessage("回答正确!")
        else:
            self.wrong_count += 1
            self.answer_display.setText(f"✗ 正确: {correct_answer}")
            self.answer_display.setStyleSheet("QLabel { color: #f44336; padding: 10px; }")
            self.status_bar.showMessage(f"回答错误! 正确答案: {correct_answer}")
        
        self._update_stats()
        self._save_config()
        self.answer_input.clear()
        
        # 自动跳转到下一张
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self._load_current_image()
    
    def _show_answer(self):
        """显示答案"""
        if self.current_image_path is None:
            return
        
        filename = self.current_image_path.name
        answer = self.answers_data.get(filename, "无答案")
        self.answer_display.setText(answer)
        self.answer_display.setStyleSheet("QLabel { color: #2196F3; padding: 10px; }")
    
    def _load_gallery_list(self):
        """加载图库列表"""
        self.gallery_combo.clear()
        self.gallery_combo.addItem("-- 请选择图库 --", "")
        
        if IMAGES_DIR.exists():
            dirs = sorted([d for d in IMAGES_DIR.iterdir() if d.is_dir()])
            for d in dirs:
                count = len([f for f in d.iterdir() 
                           if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS])
                self.gallery_combo.addItem(f"{d.name} ({count}张)", str(d))
    
    def _on_gallery_changed(self, index):
        """图库选择变化"""
        folder = self.gallery_combo.currentData()
        if folder:
            self._load_folder(folder)
            self._save_config()
    
    def _load_folder(self, folder_path):
        """加载文件夹"""
        folder = Path(folder_path)
        self.image_list = sorted([
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ])
        
        self._load_answers(folder)
        
        if self.image_list:
            # 尝试恢复上次的图片索引
            saved_index = 0
            if CONFIG_FILE.exists():
                try:
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if config.get('last_gallery') == folder_path:
                        saved_index = config.get('last_image_index', 0)
                        if 0 <= saved_index < len(self.image_list):
                            self.current_index = saved_index
                        else:
                            self.current_index = 0
                    else:
                        self.current_index = 0
                except:
                    self.current_index = 0
            else:
                self.current_index = 0
            
            self._load_current_image()
        else:
            self.current_index = -1
            self.image_label.setText("该目录下没有图片")
        
        self._update_button_states()
    
    def _load_answers(self, folder):
        """加载答案"""
        self.answers_data = {}
        answers_file = folder / 'answers.json'
        
        if answers_file.exists():
            try:
                with open(answers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for item in data:
                    filename = item.get('filename', '')
                    answer = item.get('answer', '')
                    if filename and answer:
                        self.answers_data[filename] = answer
            except Exception as e:
                print(f"加载答案失败: {e}")
    
    def _load_current_image(self):
        """加载当前图片"""
        if 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]
            self.current_image_path = image_path
            
            self.current_image = cv2.imread(str(image_path))
            
            if self.current_image is not None:
                pixmap = self._cv2_to_pixmap(self.current_image)
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                
                self.answer_display.setText("???")
                self.answer_display.setStyleSheet("QLabel { color: #333; padding: 10px; }")
                self.answer_input.clear()
                self.answer_input.setFocus()
                
                self._save_config()
        
        self._update_button_states()
    
    def _cv2_to_pixmap(self, cv_image):
        """转换OpenCV图像为QPixmap"""
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_image)
    
    def _prev_image(self):
        """上一张"""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_image()
    
    def _next_image(self):
        """下一张"""
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self._load_current_image()
    
    def _random_image(self):
        """随机"""
        if len(self.image_list) > 1:
            new_index = self.current_index
            while new_index == self.current_index:
                new_index = random.randint(0, len(self.image_list) - 1)
            self.current_index = new_index
            self._load_current_image()
    
    def _reset_stats(self):
        """重置统计"""
        self.correct_count = 0
        self.wrong_count = 0
        self._update_stats()
        self._save_config()
    
    def _update_stats(self):
        """更新统计"""
        total = self.correct_count + self.wrong_count
        if total > 0:
            accuracy = self.correct_count / total * 100
            self.stats_label.setText(
                f"正确: {self.correct_count} | 错误: {self.wrong_count} | 正确率: {accuracy:.1f}%"
            )
        else:
            self.stats_label.setText("正确: 0 | 错误: 0")
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_images = len(self.image_list) > 0
        
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_list) - 1)
        self.random_btn.setEnabled(len(self.image_list) > 1)
        self.submit_btn.setEnabled(has_images)
        self.show_answer_btn.setEnabled(has_images)
        
        if has_images:
            self.image_info.setText(f"{self.current_index + 1} / {len(self.image_list)}")
        else:
            self.image_info.setText("0 / 0")
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 恢复图库选择
                last_gallery = config.get('last_gallery', '')
                if last_gallery:
                    for i in range(self.gallery_combo.count()):
                        if self.gallery_combo.itemData(i) == last_gallery:
                            self.gallery_combo.setCurrentIndex(i)
                            break
                
                # 恢复统计
                self.correct_count = config.get('correct_count', 0)
                self.wrong_count = config.get('wrong_count', 0)
                self._update_stats()
                        
            except Exception as e:
                print(f"加载配置失败: {e}")
    
    def _save_config(self):
        """保存配置"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {
                'last_gallery': self.gallery_combo.currentData() or '',
                'last_image_index': self.current_index if self.current_index >= 0 else 0,
                'correct_count': self.correct_count,
                'wrong_count': self.wrong_count
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def closeEvent(self, event):
        """关闭时保存配置"""
        self._save_config()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    print("PyQt5版本启动")
    print("环境变量:")
    for key in ['QT_IM_MODULE', 'XMODIFIERS', 'GTK_IM_MODULE']:
        print(f"  {key}={os.environ.get(key)}")
    
    print("\n输入法使用提示:")
    print("1. 点击输入框获得焦点")
    print("2. 按 Ctrl+Space 切换输入法")
    print("3. 或者按 Shift 键切换输入法")
    print("4. 如果还是不行，请在终端中运行: fcitx5-configtool")
    
    window = MainWindow()
    window.show()
    
    # 确保输入框获得焦点
    window.answer_input.setFocus()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()