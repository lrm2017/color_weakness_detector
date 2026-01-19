#!/usr/bin/env python3
"""
色弱图谱识别程序 - GUI版本
使用PySide6构建图形界面
"""

import json
import sys
import random
import shutil
import os
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QGroupBox,
    QScrollArea, QSplitter, QStatusBar, QLineEdit, QMessageBox,
    QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QSize, QStandardPaths
from PySide6.QtGui import QPixmap, QImage, QFont

# 设置输入法环境变量（在导入Qt之后设置）
os.environ.setdefault('QT_IM_MODULE', 'fcitx')  # 使用fcitx而不是fcitx5
os.environ.setdefault('XMODIFIERS', '@im=fcitx')
os.environ.setdefault('GTK_IM_MODULE', 'fcitx')


# 支持的图片格式
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}

# 程序目录
APP_DIR = Path(__file__).parent.resolve()
IMAGES_DIR = APP_DIR / "downloaded_images"
WRONG_ANSWERS_DIR = IMAGES_DIR / "错题库"

# 配置文件路径
CONFIG_DIR = Path(QStandardPaths.writableLocation(QStandardPaths.AppConfigLocation)) / "color_weakness_detector"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ColorDetector:
    """颜色检测器"""
    
    @staticmethod
    def get_warm_mask(hsv_image):
        # 红色范围1 (0-10)
        lower_red1 = np.array([0, 25, 40])
        upper_red1 = np.array([10, 255, 255])
        mask_red1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
        
        # 红色范围2 (156-180)
        lower_red2 = np.array([156, 25, 40])
        upper_red2 = np.array([180, 255, 255])
        mask_red2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
        
        # 橙色范围 (10-20)
        lower_orange = np.array([10, 25, 40])
        upper_orange = np.array([20, 255, 255])
        mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)
        
        # 黄色范围 (20-30)
        lower_yellow = np.array([20, 25, 40])
        upper_yellow = np.array([30, 255, 255])
        mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
        
        return mask_red1 | mask_red2 | mask_orange | mask_yellow

    @staticmethod
    def get_cool_mask(hsv_image):
        # 黄绿+绿色范围 (30-85)
        lower_green = np.array([30, 25, 40])
        upper_green = np.array([85, 255, 255])
        mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
        
        # 青色范围 (85-105)
        lower_cyan = np.array([85, 25, 40])
        upper_cyan = np.array([105, 255, 255])
        mask_cyan = cv2.inRange(hsv_image, lower_cyan, upper_cyan)
        
        # 蓝色范围 (105-130)
        lower_blue = np.array([105, 25, 40])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
        
        # 紫色范围 (130-156)
        lower_purple = np.array([130, 25, 40])
        upper_purple = np.array([156, 255, 255])
        mask_purple = cv2.inRange(hsv_image, lower_purple, upper_purple)
        
        return mask_green | mask_cyan | mask_blue | mask_purple

    @staticmethod
    def find_and_draw_contours(image, mask, color, min_area=100):
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        result = image.copy()
        count = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                cv2.drawContours(result, [contour], -1, color, 3)
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
                count += 1
        
        return result, count

    @classmethod
    def detect_warm_cool(cls, image, min_area=100):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        warm_mask = cls.get_warm_mask(hsv)
        cool_mask = cls.get_cool_mask(hsv)
        
        warm_pixels = cv2.countNonZero(warm_mask)
        cool_pixels = cv2.countNonZero(cool_mask)
        
        total_colored = warm_pixels + cool_pixels
        if total_colored == 0:
            return image.copy(), {'message': '未检测到明显的暖色或冷色区域'}
        
        warm_ratio = warm_pixels / total_colored * 100
        cool_ratio = cool_pixels / total_colored * 100
        
        if warm_pixels > cool_pixels:
            result, count = cls.find_and_draw_contours(image, cool_mask, (255, 0, 0), min_area)
            message = f'暖色居多，已圈出 {count} 个冷色块（蓝框）'
        else:
            result, count = cls.find_and_draw_contours(image, warm_mask, (0, 0, 255), min_area)
            message = f'冷色居多，已圈出 {count} 个暖色块（红框）'
        
        return result, {
            'warm_ratio': warm_ratio, 'cool_ratio': cool_ratio,
            'message': message
        }


class ImageLabel(QLabel):
    """可缩放的图像标签"""
    
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(200, 200)
        self.setStyleSheet("QLabel { background-color: #2b2b2b; border: 1px solid #555; }")
        self._pixmap = None
    
    def setImage(self, pixmap):
        self._pixmap = pixmap
        self._updateDisplay()
    
    def _updateDisplay(self):
        if self._pixmap:
            scaled = self._pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateDisplay()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("色弱图谱识别程序")
        self.setMinimumSize(1000, 800)
        
        # 启用输入法支持
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        
        self.image_list = []
        self.current_index = -1
        self.current_image = None
        self.current_image_path = None
        self.answers_data = {}
        self.answer_visible = False
        
        # 练习模式统计
        self.correct_count = 0
        self.wrong_count = 0
        self.practice_mode = False  # 是否处于练习模式
        
        self._setup_ui()
        self._connect_signals()
        self._load_gallery_list()
        self._load_config()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # === 顶部控制区 ===
        top_group = QGroupBox("图库选择")
        top_layout = QHBoxLayout(top_group)
        
        top_layout.addWidget(QLabel("选择图库:"))
        self.gallery_combo = QComboBox()
        self.gallery_combo.setMinimumWidth(200)
        top_layout.addWidget(self.gallery_combo)
        
        top_layout.addSpacing(20)
        
        # 练习模式选择
        top_layout.addWidget(QLabel("练习模式:"))
        self.mode_group = QButtonGroup(self)
        self.mode_sequential = QRadioButton("顺序")
        self.mode_random = QRadioButton("随机")
        self.mode_sequential.setChecked(True)
        self.mode_group.addButton(self.mode_sequential, 0)
        self.mode_group.addButton(self.mode_random, 1)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        top_layout.addWidget(self.mode_sequential)
        top_layout.addWidget(self.mode_random)
        
        top_layout.addSpacing(20)
        
        # 统计显示
        self.stats_label = QLabel("正确: 0 | 错误: 0")
        self.stats_label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        top_layout.addWidget(self.stats_label)
        
        self.reset_stats_btn = QPushButton("重置统计")
        self.reset_stats_btn.clicked.connect(self._reset_stats)
        top_layout.addWidget(self.reset_stats_btn)
        
        top_layout.addStretch()
        
        main_layout.addWidget(top_group)
        
        # === 中间图像显示区 ===
        splitter = QSplitter(Qt.Horizontal)
        
        left_group = QGroupBox("原图")
        left_layout = QVBoxLayout(left_group)
        self.original_label = ImageLabel()
        self.original_label.setText("请选择图库")
        left_layout.addWidget(self.original_label)
        splitter.addWidget(left_group)
        
        right_group = QGroupBox("识别结果")
        right_layout = QVBoxLayout(right_group)
        self.result_label = ImageLabel()
        self.result_label.setText("点击\"开始识别\"查看结果")
        right_layout.addWidget(self.result_label)
        splitter.addWidget(right_group)
        
        splitter.setSizes([500, 500])
        main_layout.addWidget(splitter, 1)
        
        # === 答案输入区 ===
        answer_group = QGroupBox("答案")
        answer_layout = QVBoxLayout(answer_group)
        
        # 图形符号快捷面板
        symbols_layout = QHBoxLayout()
        symbols_layout.addWidget(QLabel("常用符号:"))
        
        # 定义常用符号
        symbols = ["○", "△", "□", "▽", "✩", "◇", "◆", "●", "▲", "■"]
        self.symbol_buttons = []
        
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
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(lambda checked, s=symbol: self._insert_symbol(s))
            btn.setToolTip(f"点击插入符号: {symbol}")
            symbols_layout.addWidget(btn)
            self.symbol_buttons.append(btn)
        
        symbols_layout.addStretch()
        answer_layout.addLayout(symbols_layout)
        
        # 答案输入行
        input_layout = QHBoxLayout()
        
        # 答案输入框
        input_layout.addWidget(QLabel("输入答案:"))
        self.answer_input = QLineEdit()
        self.answer_input.setPlaceholderText("输入你的答案后按回车或点击提交...")
        self.answer_input.setMinimumWidth(150)
        input_font = QFont()
        input_font.setPointSize(14)
        self.answer_input.setFont(input_font)
        
        # 强制启用输入法支持
        self.answer_input.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.answer_input.setInputMethodHints(Qt.ImhNone)
        
        # 设置焦点策略，确保能接收输入法事件
        self.answer_input.setFocusPolicy(Qt.StrongFocus)
        
        # 确保窗口能接收输入法事件
        self.answer_input.installEventFilter(self)
        input_layout.addWidget(self.answer_input)
        
        self.submit_btn = QPushButton("提交答案")
        self.submit_btn.setMinimumWidth(100)
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
        
        input_layout.addSpacing(20)
        
        # 答案显示
        self.answer_label = QLabel("???")
        self.answer_label.setAlignment(Qt.AlignCenter)
        answer_font = QFont()
        answer_font.setPointSize(20)
        answer_font.setBold(True)
        self.answer_label.setFont(answer_font)
        self.answer_label.setStyleSheet("QLabel { color: #333; padding: 10px; }")
        self.answer_label.setMinimumWidth(150)
        input_layout.addWidget(self.answer_label)
        
        self.show_answer_btn = QPushButton("显示答案")
        self.show_answer_btn.setMinimumWidth(100)
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
        
        self.add_wrong_btn = QPushButton("加入错题库")
        self.add_wrong_btn.setMinimumWidth(100)
        self.add_wrong_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        input_layout.addWidget(self.add_wrong_btn)
        
        answer_layout.addLayout(input_layout)
        
        main_layout.addWidget(answer_group)
        
        # === 底部控制区 ===
        bottom_group = QGroupBox("控制面板")
        bottom_layout = QHBoxLayout(bottom_group)
        
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一张")
        self.next_btn = QPushButton("下一张")
        self.random_btn = QPushButton("随机跳转")
        self.image_info_label = QLabel("0 / 0")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_info_label)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.random_btn)
        bottom_layout.addLayout(nav_layout)
        
        bottom_layout.addSpacing(30)
        
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("识别方法:"))
        self.method_combo = QComboBox()
        self.method_combo.addItem("冷暖色识别", "warm_cool")
        self.method_combo.setMinimumWidth(150)
        method_layout.addWidget(self.method_combo)
        bottom_layout.addLayout(method_layout)
        
        bottom_layout.addSpacing(20)
        
        self.detect_btn = QPushButton("开始识别")
        self.detect_btn.setMinimumWidth(120)
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        bottom_layout.addWidget(self.detect_btn)
        
        bottom_layout.addStretch()
        
        main_layout.addWidget(bottom_group)
        
        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 输入答案后按回车提交")
        
        self._update_button_states()
    
    def _connect_signals(self):
        """连接信号"""
        self.gallery_combo.currentIndexChanged.connect(self._on_gallery_changed)
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn.clicked.connect(self._next_image)
        self.random_btn.clicked.connect(self._random_image)
        self.detect_btn.clicked.connect(self._detect)
        self.show_answer_btn.clicked.connect(self._toggle_answer)
        self.add_wrong_btn.clicked.connect(self._add_to_wrong_answers)
        self.submit_btn.clicked.connect(self._submit_answer)
        self.answer_input.returnPressed.connect(self._submit_answer)
    
    def _on_mode_changed(self):
        """练习模式改变时保存配置"""
        self._save_config()
    
    def _insert_symbol(self, symbol):
        """插入符号到答案输入框"""
        current_text = self.answer_input.text()
        cursor_pos = self.answer_input.cursorPosition()
        
        # 在光标位置插入符号
        new_text = current_text[:cursor_pos] + symbol + current_text[cursor_pos:]
        self.answer_input.setText(new_text)
        
        # 将光标移动到插入符号之后
        self.answer_input.setCursorPosition(cursor_pos + len(symbol))
        
        # 保持输入框焦点
        self.answer_input.setFocus()
    
    def _submit_answer(self):
        """提交答案"""
        if self.current_image_path is None:
            return
        
        user_answer = self.answer_input.text().strip()
        if not user_answer:
            self.status_bar.showMessage("请输入答案")
            return
        
        filename = self.current_image_path.name
        correct_answer = self.answers_data.get(filename, "")
        
        if not correct_answer:
            self.status_bar.showMessage("该题目没有标准答案")
            return
        
        # 比较答案（忽略大小写和空格）
        user_clean = user_answer.lower().replace(" ", "")
        correct_clean = correct_answer.lower().replace(" ", "")
        
        if user_clean == correct_clean:
            # 答案正确
            self.correct_count += 1
            self._update_stats()
            self.answer_label.setText(correct_answer)
            self.answer_label.setStyleSheet("QLabel { color: #4CAF50; padding: 10px; }")
            self.status_bar.showMessage("回答正确!")
            self.answer_input.clear()
            
            # 保存统计数据
            self._save_config()
            
            # 自动跳转到下一张
            if self.mode_random.isChecked():
                # 随机模式
                self._random_image()
            else:
                # 顺序模式
                if self.current_index < len(self.image_list) - 1:
                    self.current_index += 1
                    self._load_current_image()
                else:
                    self.status_bar.showMessage("恭喜! 已完成所有题目!")
        else:
            # 答案错误
            self.wrong_count += 1
            self._update_stats()
            self.answer_label.setText(f"错! 正确: {correct_answer}")
            self.answer_label.setStyleSheet("QLabel { color: #f44336; padding: 10px; }")
            self.status_bar.showMessage(f"回答错误! 正确答案是: {correct_answer}")
            
            # 保存统计数据
            self._save_config()
            
            # 自动加入错题库
            self._add_to_wrong_answers(silent=True)
            self.answer_input.clear()
    
    def _reset_stats(self):
        """重置统计"""
        self.correct_count = 0
        self.wrong_count = 0
        self._update_stats()
        self._save_config()  # 保存重置后的统计
        self.status_bar.showMessage("统计已重置")
    
    def _update_stats(self):
        """更新统计显示"""
        total = self.correct_count + self.wrong_count
        if total > 0:
            accuracy = self.correct_count / total * 100
            self.stats_label.setText(
                f"正确: {self.correct_count} | 错误: {self.wrong_count} | 正确率: {accuracy:.1f}%"
            )
        else:
            self.stats_label.setText("正确: 0 | 错误: 0")
    
    def _load_gallery_list(self):
        """加载图库列表"""
        self.gallery_combo.clear()
        self.gallery_combo.addItem("-- 请选择图库 --", "")
        
        if IMAGES_DIR.exists():
            WRONG_ANSWERS_DIR.mkdir(exist_ok=True)
            
            dirs = sorted([
                d for d in IMAGES_DIR.iterdir()
                if d.is_dir() and d.name != "backup_original"
            ])
            
            for d in dirs:
                if d.name == "错题库":
                    count = len(list(d.glob("*.jpg")) + list(d.glob("*.png")))
                    self.gallery_combo.addItem(f"错题库 ({count}题)", str(d))
                    break
            
            for d in dirs:
                if d.name != "错题库":
                    count = len([f for f in d.iterdir() 
                               if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS])
                    self.gallery_combo.addItem(f"{d.name} ({count}张)", str(d))
    
    def _on_gallery_changed(self, index):
        """图库选择变化"""
        folder = self.gallery_combo.currentData()
        if folder:
            self._load_folder(folder)
            self._save_config()
            self._reset_stats()  # 切换图库时重置统计
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                last_gallery = config.get('last_gallery', '')
                if last_gallery:
                    for i in range(self.gallery_combo.count()):
                        if self.gallery_combo.itemData(i) == last_gallery:
                            self.gallery_combo.setCurrentIndex(i)
                            break
                
                # 恢复统计数据
                self.correct_count = config.get('correct_count', 0)
                self.wrong_count = config.get('wrong_count', 0)
                self._update_stats()
                
                # 恢复练习模式
                practice_mode = config.get('practice_mode', 'sequential')
                if practice_mode == 'random':
                    self.mode_random.setChecked(True)
                else:
                    self.mode_sequential.setChecked(True)
                    
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
                'wrong_count': self.wrong_count,
                'practice_mode': 'random' if self.mode_random.isChecked() else 'sequential'
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def _load_folder(self, folder_path):
        """加载文件夹中的图片"""
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
                        # 确保索引在有效范围内
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
            self.status_bar.showMessage(f"已加载 {len(self.image_list)} 张图片 - 输入答案后按回车提交")
        else:
            self.current_index = -1
            self.current_image = None
            self.current_image_path = None
            self.original_label.clear()
            self.original_label.setText("该目录下没有图片")
            self.result_label.clear()
            self.result_label.setText("无图片")
            self.status_bar.showMessage("未找到图片文件")
        
        self._update_button_states()
    
    def _load_answers(self, folder):
        """加载答案数据"""
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
                self.original_label.setImage(pixmap)
                
                self.result_label.clear()
                self.result_label.setText("点击\"开始识别\"查看结果")
                
                # 重置答案显示
                self.answer_visible = False
                self.answer_label.setText("???")
                self.answer_label.setStyleSheet("QLabel { color: #333; padding: 10px; }")
                self.show_answer_btn.setText("显示答案")
                
                # 清空输入框并聚焦
                self.answer_input.clear()
                self.answer_input.setFocus()
                
                # 保存当前进度
                self._save_config()
        
        self._update_button_states()
    
    def _cv2_to_pixmap(self, cv_image):
        """将OpenCV图像转换为QPixmap"""
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_image)
    
    def _prev_image(self):
        """上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self._load_current_image()
    
    def _next_image(self):
        """下一张图片"""
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self._load_current_image()
    
    def _random_image(self):
        """随机切换图片"""
        if len(self.image_list) > 1:
            new_index = self.current_index
            while new_index == self.current_index:
                new_index = random.randint(0, len(self.image_list) - 1)
            self.current_index = new_index
            self._load_current_image()
    
    def _detect(self):
        """执行识别"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
        
        method = self.method_combo.currentData()
        
        if method == "warm_cool":
            result_image, stats = ColorDetector.detect_warm_cool(self.current_image)
            pixmap = self._cv2_to_pixmap(result_image)
            self.result_label.setImage(pixmap)
            self.status_bar.showMessage(stats['message'])
    
    def _toggle_answer(self):
        """切换答案显示"""
        self.answer_visible = not self.answer_visible
        
        if self.answer_visible:
            if 0 <= self.current_index < len(self.image_list):
                filename = self.image_list[self.current_index].name
                answer = self.answers_data.get(filename, "")
                if answer:
                    self.answer_label.setText(answer)
                    self.answer_label.setStyleSheet("QLabel { color: #4CAF50; padding: 10px; }")
                else:
                    self.answer_label.setText("(无答案)")
                    self.answer_label.setStyleSheet("QLabel { color: #999; padding: 10px; }")
            self.show_answer_btn.setText("隐藏答案")
        else:
            self.answer_label.setText("???")
            self.answer_label.setStyleSheet("QLabel { color: #333; padding: 10px; }")
            self.show_answer_btn.setText("显示答案")
    
    def _add_to_wrong_answers(self, silent=False):
        """加入错题库"""
        if self.current_image_path is None:
            return
        
        WRONG_ANSWERS_DIR.mkdir(exist_ok=True)
        
        src_path = self.current_image_path
        src_dir_name = src_path.parent.name
        
        # 如果已经在错题库中，跳过
        if src_dir_name == "错题库":
            if not silent:
                self.status_bar.showMessage("已在错题库中")
            return
        
        new_filename = f"{src_dir_name}_{src_path.name}"
        dst_path = WRONG_ANSWERS_DIR / new_filename
        
        if dst_path.exists():
            if not silent:
                self.status_bar.showMessage("该题目已在错题库中")
            return
        
        try:
            shutil.copy2(src_path, dst_path)
            
            filename = src_path.name
            answer = self.answers_data.get(filename, "")
            if answer:
                wrong_answers_file = WRONG_ANSWERS_DIR / 'answers.json'
                wrong_data = []
                if wrong_answers_file.exists():
                    with open(wrong_answers_file, 'r', encoding='utf-8') as f:
                        wrong_data = json.load(f)
                
                wrong_data.append({
                    'filename': new_filename,
                    'original_url': '',
                    'answer': answer,
                    'source': src_dir_name
                })
                
                with open(wrong_answers_file, 'w', encoding='utf-8') as f:
                    json.dump(wrong_data, f, ensure_ascii=False, indent=2)
            
            # 刷新图库列表（阻止信号触发以避免重置统计）
            current_gallery = self.gallery_combo.currentData()
            self.gallery_combo.blockSignals(True)
            self._load_gallery_list()
            for i in range(self.gallery_combo.count()):
                if self.gallery_combo.itemData(i) == current_gallery:
                    self.gallery_combo.setCurrentIndex(i)
                    break
            self.gallery_combo.blockSignals(False)
            
            if not silent:
                self.status_bar.showMessage(f"已加入错题库: {new_filename}")
            
        except Exception as e:
            if not silent:
                QMessageBox.warning(self, "错误", f"加入错题库失败: {e}")
    
    def eventFilter(self, obj, event):
        """事件过滤器，处理输入法事件"""
        if obj == self.answer_input:
            # 确保输入法事件能正确传递
            if event.type() in [event.Type.InputMethod, event.Type.InputMethodQuery]:
                return False  # 让事件继续传递
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        """程序关闭时保存配置"""
        self._save_config()
        event.accept()
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_images = len(self.image_list) > 0
        has_current = self.current_image is not None
        
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_list) - 1)
        self.random_btn.setEnabled(len(self.image_list) > 1)
        self.detect_btn.setEnabled(has_current)
        self.submit_btn.setEnabled(has_current)
        
        current_gallery = self.gallery_combo.currentData()
        is_wrong_answers = current_gallery and "错题库" in current_gallery
        self.add_wrong_btn.setEnabled(has_current and not is_wrong_answers)
        
        if has_images:
            self.image_info_label.setText(f"{self.current_index + 1} / {len(self.image_list)}")
        else:
            self.image_info_label.setText("0 / 0")


def main():
    # 在创建QApplication之前设置环境变量
    os.environ.setdefault('QT_IM_MODULE', 'fcitx')  # 使用fcitx而不是fcitx5
    os.environ.setdefault('XMODIFIERS', '@im=fcitx')
    os.environ.setdefault('GTK_IM_MODULE', 'fcitx')
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 确保Qt应用程序支持输入法
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
