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

from multi_channel_color_detector import MultiChannelColorDetector
from simple_color_test import analyze_color_channels
from color_vision_filters import ColorVisionFilters, FilterType
from image_utils import imread_unicode, imwrite_unicode

# # 设置输入法环境变量（在导入Qt之后设置）
# os.environ.setdefault('QT_IM_MODULE', 'fcitx')  # 使用fcitx而不是fcitx5
# os.environ.setdefault('XMODIFIERS', '@im=fcitx')
# os.environ.setdefault('GTK_IM_MODULE', 'fcitx')


# 支持的图片格式
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}

# 程序目录
APP_DIR = Path(__file__).parent.resolve()
DEFAULT_IMAGES_DIR = APP_DIR / "downloaded_images"
RESULTS_DIR = APP_DIR / "test_results"  # 测试结果目录

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
        
        # 初始化图库路径和结果目录
        self.images_dir = DEFAULT_IMAGES_DIR
        self.wrong_answers_dir = None
        self.results_dir = RESULTS_DIR
        
        # 确保结果目录存在
        self.results_dir.mkdir(exist_ok=True)
        
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
        
        # 多通道检测器
        self.multichannel_detector = MultiChannelColorDetector()
        
        # 当前滤镜状态
        self.current_filter = FilterType.NONE
        self.filtered_image = None
        
        self._setup_ui()
        self._connect_signals()
        self._load_config()  # 先加载配置，获取图库路径
        self._load_gallery_list()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # === 顶部控制区 ===
        top_group = QGroupBox("图库选择")
        top_layout = QVBoxLayout(top_group)
        
        # 图库路径选择行
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("图库路径:"))
        
        self.path_label = QLabel()
        self.path_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        self.path_label.setMinimumWidth(300)
        path_layout.addWidget(self.path_label, 1)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self._browse_images_dir)
        path_layout.addWidget(self.browse_btn)
        
        self.reset_path_btn = QPushButton("重置为默认")
        self.reset_path_btn.setMinimumWidth(100)
        self.reset_path_btn.clicked.connect(self._reset_images_dir)
        path_layout.addWidget(self.reset_path_btn)
        
        top_layout.addLayout(path_layout)
        
        # 图库选择行
        gallery_layout = QHBoxLayout()
        gallery_layout.addWidget(QLabel("选择图库:"))
        self.gallery_combo = QComboBox()
        self.gallery_combo.setMinimumWidth(200)
        gallery_layout.addWidget(self.gallery_combo)
        
        gallery_layout.addSpacing(20)
        
        # 练习模式选择
        gallery_layout.addWidget(QLabel("练习模式:"))
        self.mode_group = QButtonGroup(self)
        self.mode_sequential = QRadioButton("顺序")
        self.mode_random = QRadioButton("随机")
        self.mode_sequential.setChecked(True)
        self.mode_group.addButton(self.mode_sequential, 0)
        self.mode_group.addButton(self.mode_random, 1)
        self.mode_group.buttonClicked.connect(self._on_mode_changed)
        gallery_layout.addWidget(self.mode_sequential)
        gallery_layout.addWidget(self.mode_random)
        
        gallery_layout.addSpacing(20)
        
        # 统计显示
        self.stats_label = QLabel("正确: 0 | 错误: 0")
        self.stats_label.setStyleSheet("QLabel { font-weight: bold; color: #333; }")
        gallery_layout.addWidget(self.stats_label)
        
        self.reset_stats_btn = QPushButton("重置统计")
        self.reset_stats_btn.clicked.connect(self._reset_stats)
        gallery_layout.addWidget(self.reset_stats_btn)
        
        gallery_layout.addStretch()
        
        top_layout.addLayout(gallery_layout)
        
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
        
        self.remove_wrong_btn = QPushButton("移出错题库")
        self.remove_wrong_btn.setMinimumWidth(100)
        self.remove_wrong_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F57C00; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        input_layout.addWidget(self.remove_wrong_btn)
        
        answer_layout.addLayout(input_layout)
        
        main_layout.addWidget(answer_group)
        
        # === 滤镜控制区 ===
        filter_group = QGroupBox("色觉辅助滤镜")
        filter_layout = QVBoxLayout(filter_group)
        
        # 滤镜选择行
        filter_select_layout = QHBoxLayout()
        filter_select_layout.addWidget(QLabel("选择滤镜:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.setMinimumWidth(200)
        
        # 添加所有滤镜选项
        for filter_type in FilterType:
            description = ColorVisionFilters.get_filter_description(filter_type)
            self.filter_combo.addItem(description, filter_type.value)
        
        filter_select_layout.addWidget(self.filter_combo)
        
        self.apply_filter_btn = QPushButton("应用滤镜")
        self.apply_filter_btn.setMinimumWidth(100)
        self.apply_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #8BC34A;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #689F38; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.apply_filter_btn.clicked.connect(self._apply_filter)
        filter_select_layout.addWidget(self.apply_filter_btn)
        
        self.reset_filter_btn = QPushButton("重置滤镜")
        self.reset_filter_btn.setMinimumWidth(100)
        self.reset_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFC107;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #FF8F00; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.reset_filter_btn.clicked.connect(self._reset_filter)
        filter_select_layout.addWidget(self.reset_filter_btn)
        
        filter_select_layout.addStretch()
        filter_layout.addLayout(filter_select_layout)
        
        # 滤镜说明
        self.filter_description = QLabel("选择滤镜以辅助识别不同类型的色觉缺陷")
        self.filter_description.setStyleSheet("""
            QLabel {
                color: #666;
                font-style: italic;
                padding: 5px;
                background-color: #f9f9f9;
                border-radius: 3px;
            }
        """)
        self.filter_description.setWordWrap(True)
        filter_layout.addWidget(self.filter_description)
        
        main_layout.addWidget(filter_group)
        
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
        
        # 识别方法选择
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("识别方法:"))
        self.method_combo = QComboBox()
        self.method_combo.addItem("冷暖色识别", "warm_cool")
        self.method_combo.addItem("红绿通道测试", "red_green")
        self.method_combo.addItem("蓝黄通道测试", "blue_yellow")
        self.method_combo.addItem("综合多通道测试", "comprehensive")
        self.method_combo.addItem("快速颜色分析", "quick_analysis")
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
        
        # 结果管理按钮
        self.view_results_btn = QPushButton("查看结果")
        self.view_results_btn.setMinimumWidth(100)
        self.view_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.view_results_btn.clicked.connect(self._open_results_folder)
        bottom_layout.addWidget(self.view_results_btn)
        
        self.clear_results_btn = QPushButton("清理结果")
        self.clear_results_btn.setMinimumWidth(100)
        self.clear_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #455A64; }
        """)
        self.clear_results_btn.clicked.connect(self._clear_results)
        bottom_layout.addWidget(self.clear_results_btn)
        
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
        self.remove_wrong_btn.clicked.connect(self._remove_from_wrong_answers)
        self.submit_btn.clicked.connect(self._submit_answer)
        self.answer_input.returnPressed.connect(self._submit_answer)
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
    
    def _browse_images_dir(self):
        """浏览选择图库目录"""
        current_dir = str(self.images_dir) if self.images_dir.exists() else str(Path.home())
        
        new_dir = QFileDialog.getExistingDirectory(
            self, 
            "选择图库目录", 
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if new_dir:
            self.images_dir = Path(new_dir)
            self.wrong_answers_dir = self.images_dir / "错题库"
            self._update_path_display()
            self._load_gallery_list()
            self._save_config()
            self._reset_stats()  # 切换图库路径时重置统计
            self.status_bar.showMessage(f"图库路径已更改为: {self.images_dir}")
    
    def _reset_images_dir(self):
        """重置图库目录为默认路径"""
        self.images_dir = DEFAULT_IMAGES_DIR
        self.wrong_answers_dir = self.images_dir / "错题库"
        self._update_path_display()
        self._load_gallery_list()
        self._save_config()
        self._reset_stats()  # 重置路径时重置统计
        self.status_bar.showMessage("图库路径已重置为默认")
    
    def _on_mode_changed(self):
        """练习模式改变时保存配置"""
        self._save_config()
    
    def _browse_images_dir(self):
        """浏览选择图库目录"""
        current_dir = str(self.images_dir) if self.images_dir.exists() else str(Path.home())
        
        new_dir = QFileDialog.getExistingDirectory(
            self, 
            "选择图库目录", 
            current_dir,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if new_dir:
            self.images_dir = Path(new_dir)
            self.wrong_answers_dir = self.images_dir / "错题库"
            self._update_path_display()
            self._load_gallery_list()
            self._save_config()
            self._reset_stats()  # 切换图库路径时重置统计
            self.status_bar.showMessage(f"图库路径已更改为: {self.images_dir}")
    
    def _reset_images_dir(self):
        """重置图库目录为默认路径"""
        self.images_dir = DEFAULT_IMAGES_DIR
        self.wrong_answers_dir = self.images_dir / "错题库"
        self._update_path_display()
        self._load_gallery_list()
        self._save_config()
        self._reset_stats()  # 重置路径时重置统计
        self.status_bar.showMessage("图库路径已重置为默认")
    
    def _update_path_display(self):
        """更新路径显示"""
        path_text = str(self.images_dir)
        # 如果路径太长，显示省略号
        if len(path_text) > 50:
            path_text = "..." + path_text[-47:]
        self.path_label.setText(path_text)
        self.path_label.setToolTip(str(self.images_dir))  # 完整路径作为提示
    
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
        
        if self.images_dir.exists():
            # 确保错题库目录存在
            if self.wrong_answers_dir is None:
                self.wrong_answers_dir = self.images_dir / "错题库"
            self.wrong_answers_dir.mkdir(exist_ok=True)
            
            dirs = sorted([
                d for d in self.images_dir.iterdir()
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
        else:
            # 图库目录不存在时的提示
            self.gallery_combo.addItem("-- 图库目录不存在 --", "")
            self.status_bar.showMessage(f"图库目录不存在: {self.images_dir}")
        
        # 更新路径显示
        self._update_path_display()
        
        # 恢复上次选择的图库
        if hasattr(self, 'last_gallery') and self.last_gallery:
            for i in range(self.gallery_combo.count()):
                if self.gallery_combo.itemData(i) == self.last_gallery:
                    self.gallery_combo.setCurrentIndex(i)
                    break
    
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
                
                # 加载图库路径
                images_dir_str = config.get('images_dir', '')
                if images_dir_str and Path(images_dir_str).exists():
                    self.images_dir = Path(images_dir_str)
                else:
                    self.images_dir = DEFAULT_IMAGES_DIR
                
                self.wrong_answers_dir = self.images_dir / "错题库"
                
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
                
                # 恢复上次选择的图库（在加载图库列表后处理）
                self.last_gallery = config.get('last_gallery', '')
                    
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.images_dir = DEFAULT_IMAGES_DIR
                self.wrong_answers_dir = self.images_dir / "错题库"
                self.last_gallery = ''
        else:
            self.images_dir = DEFAULT_IMAGES_DIR
            self.wrong_answers_dir = self.images_dir / "错题库"
            self.last_gallery = ''
    
    def _save_config(self):
        """保存配置"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            config = {
                'images_dir': str(self.images_dir),
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
            
            self.current_image = imread_unicode(str(image_path))
            
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
                
                # 重置滤镜状态
                self.current_filter = FilterType.NONE
                self.filtered_image = None
                self.filter_combo.setCurrentIndex(0)
                
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
        
        try:
            # 获取当前显示的图像（可能是滤镜后的图像）
            display_image = self._get_current_display_image()
            
            if method == "warm_cool":
                result_image, stats = ColorDetector.detect_warm_cool(display_image)
                pixmap = self._cv2_to_pixmap(result_image)
                self.result_label.setImage(pixmap)
                self.status_bar.showMessage(stats['message'])
                
            elif method == "red_green":
                self._run_multichannel_test_on_image(display_image, "red_green")
                
            elif method == "blue_yellow":
                self._run_multichannel_test_on_image(display_image, "blue_yellow")
                
            elif method == "comprehensive":
                self._run_multichannel_test_on_image(display_image, "comprehensive")
                
            elif method == "quick_analysis":
                self._run_quick_analysis_on_image(display_image)
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"识别过程中发生错误: {str(e)}")
    
    def _run_multichannel_test_on_image(self, image, channel_type):
        """在指定图像上运行多通道测试"""
        if self.current_image_path is None:
            return
        
        try:
            # 临时保存当前图像用于测试
            temp_path = self.results_dir / "temp_filtered_image.jpg"
            imwrite_unicode(str(temp_path), image)
            
            # 生成输出文件名
            timestamp = self._get_timestamp()
            filter_suffix = f"_{self.current_filter.value}" if self.current_filter != FilterType.NONE else ""
            base_name = f"{self.current_image_path.stem}_{channel_type}{filter_suffix}_{timestamp}"
            output_path = self.results_dir / f"{base_name}.jpg"
            
            if channel_type == "red_green":
                result_image, data = self.multichannel_detector.test_red_green_channel(
                    temp_path, output_path, min_area=50
                )
                message = f"红绿通道测试完成 - 红色: {data['red_ratio']:.1%}, 绿色: {data['green_ratio']:.1%}"
                
            elif channel_type == "blue_yellow":
                result_image, data = self.multichannel_detector.test_blue_yellow_channel(
                    temp_path, output_path, min_area=50
                )
                message = f"蓝黄通道测试完成 - 蓝色: {data['blue_ratio']:.1%}, 黄色: {data['yellow_ratio']:.1%}"
                
            elif channel_type == "comprehensive":
                result_image, data = self.multichannel_detector.comprehensive_test(
                    temp_path, output_path, min_area=50
                )
                
                # 生成详细报告
                rg_result, rg_data = self.multichannel_detector.test_red_green_channel(
                    temp_path, min_area=50
                )
                by_result, by_data = self.multichannel_detector.test_blue_yellow_channel(
                    temp_path, min_area=50
                )
                
                report = self.multichannel_detector.generate_report(
                    temp_path, rg_data, by_data, data
                )
                
                # 添加滤镜信息到报告
                report['filter_applied'] = self.current_filter.value
                report['original_image_path'] = str(self.current_image_path)
                
                # 保存报告
                report_path = self.results_dir / f"{base_name}_report.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                diagnosis = report['diagnosis']
                message = f"综合测试完成 - 诊断: {diagnosis['type']} (置信度: {diagnosis['confidence']:.2f})"
            
            # 显示结果图像
            pixmap = self._cv2_to_pixmap(result_image)
            self.result_label.setImage(pixmap)
            
            if self.current_filter != FilterType.NONE:
                filter_name = ColorVisionFilters.get_filter_description(self.current_filter)
                message += f" [滤镜: {filter_name}]"
            
            self.status_bar.showMessage(message)
            
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"多通道测试失败: {str(e)}")
    
    def _run_quick_analysis_on_image(self, image):
        """在指定图像上运行快速分析"""
        if self.current_image_path is None:
            return
        
        try:
            # 临时保存当前图像用于分析
            temp_path = self.results_dir / "temp_filtered_image.jpg"
            imwrite_unicode(str(temp_path), image)
            
            results = analyze_color_channels(temp_path)
            
            if results is None:
                self.status_bar.showMessage("无法分析图像或未检测到彩色区域")
                return
            
            # 创建分析结果显示
            rg = results['red_green_channel']
            by = results['blue_yellow_channel']
            
            message = (f"快速分析完成 - "
                      f"红绿通道(红:{rg['red_ratio']:.1%}/绿:{rg['green_ratio']:.1%}) "
                      f"蓝黄通道(蓝:{by['blue_ratio']:.1%}/黄:{by['yellow_ratio']:.1%}) "
                      f"诊断:{results['diagnosis']}")
            
            # 保存分析结果
            timestamp = self._get_timestamp()
            filter_suffix = f"_{self.current_filter.value}" if self.current_filter != FilterType.NONE else ""
            result_path = self.results_dir / f"{self.current_image_path.stem}_quick_analysis{filter_suffix}_{timestamp}.json"
            
            # 添加滤镜信息
            results['filter_applied'] = self.current_filter.value
            results['original_image_path'] = str(self.current_image_path)
            
            with open(result_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 显示当前图像（快速分析不生成新图像）
            pixmap = self._cv2_to_pixmap(image)
            self.result_label.setImage(pixmap)
            
            if self.current_filter != FilterType.NONE:
                filter_name = ColorVisionFilters.get_filter_description(self.current_filter)
                message += f" [滤镜: {filter_name}]"
            
            self.status_bar.showMessage(message)
            
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"快速分析失败: {str(e)}")
    
    def _run_multichannel_test(self, channel_type):
        """运行多通道测试"""
        if self.current_image_path is None:
            return
        
        try:
            # 生成输出文件名
            timestamp = self._get_timestamp()
            base_name = f"{self.current_image_path.stem}_{channel_type}_{timestamp}"
            output_path = self.results_dir / f"{base_name}.jpg"
            
            if channel_type == "red_green":
                result_image, data = self.multichannel_detector.test_red_green_channel(
                    self.current_image_path, output_path, min_area=50
                )
                message = f"红绿通道测试完成 - 红色: {data['red_ratio']:.1%}, 绿色: {data['green_ratio']:.1%}"
                
            elif channel_type == "blue_yellow":
                result_image, data = self.multichannel_detector.test_blue_yellow_channel(
                    self.current_image_path, output_path, min_area=50
                )
                message = f"蓝黄通道测试完成 - 蓝色: {data['blue_ratio']:.1%}, 黄色: {data['yellow_ratio']:.1%}"
                
            elif channel_type == "comprehensive":
                result_image, data = self.multichannel_detector.comprehensive_test(
                    self.current_image_path, output_path, min_area=50
                )
                
                # 生成详细报告
                rg_result, rg_data = self.multichannel_detector.test_red_green_channel(
                    self.current_image_path, min_area=50
                )
                by_result, by_data = self.multichannel_detector.test_blue_yellow_channel(
                    self.current_image_path, min_area=50
                )
                
                report = self.multichannel_detector.generate_report(
                    self.current_image_path, rg_data, by_data, data
                )
                
                # 保存报告
                report_path = self.results_dir / f"{base_name}_report.json"
                with open(report_path, 'w', encoding='utf-8') as f:
                    import json
                    json.dump(report, f, ensure_ascii=False, indent=2)
                
                diagnosis = report['diagnosis']
                message = f"综合测试完成 - 诊断: {diagnosis['type']} (置信度: {diagnosis['confidence']:.2f})"
            
            # 显示结果图像
            pixmap = self._cv2_to_pixmap(result_image)
            self.result_label.setImage(pixmap)
            self.status_bar.showMessage(message)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"多通道测试失败: {str(e)}")
    
    def _run_quick_analysis(self):
        """运行快速颜色分析"""
        if self.current_image_path is None:
            return
        
        try:
            results = analyze_color_channels(self.current_image_path)
            
            if results is None:
                self.status_bar.showMessage("无法分析图像或未检测到彩色区域")
                return
            
            # 创建分析结果显示
            rg = results['red_green_channel']
            by = results['blue_yellow_channel']
            
            message = (f"快速分析完成 - "
                      f"红绿通道(红:{rg['red_ratio']:.1%}/绿:{rg['green_ratio']:.1%}) "
                      f"蓝黄通道(蓝:{by['blue_ratio']:.1%}/黄:{by['yellow_ratio']:.1%}) "
                      f"诊断:{results['diagnosis']}")
            
            # 保存分析结果
            timestamp = self._get_timestamp()
            result_path = self.results_dir / f"{self.current_image_path.stem}_quick_analysis_{timestamp}.json"
            with open(result_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 显示原图（快速分析不生成新图像）
            pixmap = self._cv2_to_pixmap(self.current_image)
            self.result_label.setImage(pixmap)
            self.status_bar.showMessage(message)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"快速分析失败: {str(e)}")
    
    def _get_timestamp(self):
        """获取时间戳字符串"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
    
    def _remove_from_wrong_answers(self):
        """从错题库中移出"""
        if self.current_image_path is None:
            return
        
        src_path = self.current_image_path
        src_dir_name = src_path.parent.name
        
        # 只有在错题库中才能移出
        if src_dir_name != "错题库":
            self.status_bar.showMessage("当前不在错题库中")
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认移出", 
            f"确定要将 '{src_path.name}' 从错题库中移出吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # 删除图片文件
            src_path.unlink()
            
            # 从answers.json中移除对应记录
            wrong_answers_file = self.wrong_answers_dir / 'answers.json'
            if wrong_answers_file.exists():
                with open(wrong_answers_file, 'r', encoding='utf-8') as f:
                    wrong_data = json.load(f)
                
                # 过滤掉要删除的记录
                wrong_data = [item for item in wrong_data if item.get('filename') != src_path.name]
                
                with open(wrong_answers_file, 'w', encoding='utf-8') as f:
                    json.dump(wrong_data, f, ensure_ascii=False, indent=2)
            
            # 刷新图库列表
            current_gallery = self.gallery_combo.currentData()
            self.gallery_combo.blockSignals(True)
            self._load_gallery_list()
            for i in range(self.gallery_combo.count()):
                if self.gallery_combo.itemData(i) == current_gallery:
                    self.gallery_combo.setCurrentIndex(i)
                    break
            self.gallery_combo.blockSignals(False)
            
            # 重新加载当前文件夹
            self._load_folder(current_gallery)
            
            self.status_bar.showMessage(f"已从错题库移出: {src_path.name}")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"移出错题库失败: {e}")
    
    def _add_to_wrong_answers(self, silent=False):
        """加入错题库"""
        if self.current_image_path is None:
            return
        
        self.wrong_answers_dir.mkdir(exist_ok=True)
        
        src_path = self.current_image_path
        src_dir_name = src_path.parent.name
        
        # 如果已经在错题库中，跳过
        if src_dir_name == "错题库":
            if not silent:
                self.status_bar.showMessage("已在错题库中")
            return
        
        new_filename = f"{src_dir_name}_{src_path.name}"
        dst_path = self.wrong_answers_dir / new_filename
        
        if dst_path.exists():
            if not silent:
                self.status_bar.showMessage("该题目已在错题库中")
            return
        
        try:
            shutil.copy2(src_path, dst_path)
            
            filename = src_path.name
            answer = self.answers_data.get(filename, "")
            if answer:
                wrong_answers_file = self.wrong_answers_dir / 'answers.json'
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
    
    def _open_results_folder(self):
        """打开结果文件夹"""
        try:
            import subprocess
            import platform
            
            # 确保结果目录存在
            self.results_dir.mkdir(exist_ok=True)
            
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", str(self.results_dir)])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", str(self.results_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.results_dir)])
                
            self.status_bar.showMessage(f"已打开结果目录: {self.results_dir}")
            
        except Exception as e:
            QMessageBox.information(
                self, 
                "结果目录", 
                f"结果保存在: {self.results_dir}\n\n无法自动打开文件夹: {str(e)}"
            )
    
    def _clear_results(self):
        """清理测试结果"""
        if not self.results_dir.exists():
            self.status_bar.showMessage("结果目录不存在")
            return
        
        # 统计文件数量
        files = list(self.results_dir.glob("*"))
        if not files:
            self.status_bar.showMessage("结果目录已经是空的")
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认清理",
            f"确定要删除结果目录中的 {len(files)} 个文件吗？\n\n这个操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                deleted_count = 0
                for file_path in files:
                    if file_path.is_file():
                        file_path.unlink()
                        deleted_count += 1
                    elif file_path.is_dir():
                        import shutil
                        shutil.rmtree(file_path)
                        deleted_count += 1
                
                self.status_bar.showMessage(f"已清理 {deleted_count} 个文件")
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"清理结果失败: {str(e)}")
    
    def _on_filter_changed(self):
        """滤镜选择改变时更新描述"""
        filter_value = self.filter_combo.currentData()
        if filter_value:
            filter_type = FilterType(filter_value)
            description = ColorVisionFilters.get_filter_description(filter_type)
            self.filter_description.setText(description)
    
    def _apply_filter(self):
        """应用选中的滤镜"""
        if self.current_image is None:
            QMessageBox.warning(self, "警告", "请先加载图片")
            return
        
        filter_value = self.filter_combo.currentData()
        if not filter_value:
            return
        
        try:
            filter_type = FilterType(filter_value)
            self.current_filter = filter_type
            
            # 应用滤镜
            self.filtered_image = ColorVisionFilters.apply_filter(self.current_image, filter_type)
            
            # 显示滤镜后的图像
            pixmap = self._cv2_to_pixmap(self.filtered_image)
            self.original_label.setImage(pixmap)
            
            # 清空识别结果
            self.result_label.clear()
            self.result_label.setText("滤镜已应用，点击\"开始识别\"查看结果")
            
            filter_name = ColorVisionFilters.get_filter_description(filter_type)
            self.status_bar.showMessage(f"已应用滤镜: {filter_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"应用滤镜失败: {str(e)}")
    
    def _reset_filter(self):
        """重置滤镜，显示原图"""
        if self.current_image is None:
            return
        
        self.current_filter = FilterType.NONE
        self.filtered_image = None
        
        # 显示原图
        pixmap = self._cv2_to_pixmap(self.current_image)
        self.original_label.setImage(pixmap)
        
        # 重置滤镜选择
        self.filter_combo.setCurrentIndex(0)
        
        # 清空识别结果
        self.result_label.clear()
        self.result_label.setText("点击\"开始识别\"查看结果")
        
        self.status_bar.showMessage("滤镜已重置")
    
    def _get_current_display_image(self):
        """获取当前显示的图像（原图或滤镜后的图像）"""
        if self.filtered_image is not None:
            return self.filtered_image
        else:
            return self.current_image

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
        
        # 加入错题库按钮：只有不在错题库中时才启用
        self.add_wrong_btn.setEnabled(has_current and not is_wrong_answers)
        
        # 移出错题库按钮：只有在错题库中时才启用
        self.remove_wrong_btn.setEnabled(has_current and is_wrong_answers)
        
        if has_images:
            self.image_info_label.setText(f"{self.current_index + 1} / {len(self.image_list)}")
        else:
            self.image_info_label.setText("0 / 0")


def main():
    # 在创建QApplication之前设置环境变量
    # os.environ.setdefault('QT_IM_MODULE', 'fcitx')  # 使用fcitx而不是fcitx5
    # os.environ.setdefault('XMODIFIERS', '@im=fcitx')
    # os.environ.setdefault('GTK_IM_MODULE', 'fcitx')
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 确保Qt应用程序支持输入法
    app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
