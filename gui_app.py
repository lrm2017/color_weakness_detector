#!/usr/bin/env python3
"""
色弱图谱识别程序 - GUI版本
使用PySide6构建图形界面
"""

import json
import sys
import random
from pathlib import Path

import cv2
import numpy as np
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QComboBox, QGroupBox,
    QScrollArea, QSplitter, QStatusBar, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage, QFont


# 支持的图片格式
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}


class ColorDetector:
    """颜色检测器基类"""
    
    @staticmethod
    def get_warm_mask(hsv_image):
        """获取暖色掩码（红、橙、黄）"""
        # 红色范围1 (0-10)
        lower_red1 = np.array([0, 70, 50])
        upper_red1 = np.array([10, 255, 255])
        mask_red1 = cv2.inRange(hsv_image, lower_red1, upper_red1)
        
        # 红色范围2 (160-180)
        lower_red2 = np.array([160, 70, 50])
        upper_red2 = np.array([180, 255, 255])
        mask_red2 = cv2.inRange(hsv_image, lower_red2, upper_red2)
        
        # 橙色范围 (10-25)
        lower_orange = np.array([10, 70, 50])
        upper_orange = np.array([25, 255, 255])
        mask_orange = cv2.inRange(hsv_image, lower_orange, upper_orange)
        
        # 黄色范围 (25-40)
        lower_yellow = np.array([25, 70, 50])
        upper_yellow = np.array([40, 255, 255])
        mask_yellow = cv2.inRange(hsv_image, lower_yellow, upper_yellow)
        
        return mask_red1 | mask_red2 | mask_orange | mask_yellow

    @staticmethod
    def get_cool_mask(hsv_image):
        """获取冷色掩码（绿、青、蓝、紫）"""
        # 绿色范围 (40-80)
        lower_green = np.array([40, 70, 50])
        upper_green = np.array([80, 255, 255])
        mask_green = cv2.inRange(hsv_image, lower_green, upper_green)
        
        # 青色范围 (80-100)
        lower_cyan = np.array([80, 70, 50])
        upper_cyan = np.array([100, 255, 255])
        mask_cyan = cv2.inRange(hsv_image, lower_cyan, upper_cyan)
        
        # 蓝色范围 (100-130)
        lower_blue = np.array([100, 70, 50])
        upper_blue = np.array([130, 255, 255])
        mask_blue = cv2.inRange(hsv_image, lower_blue, upper_blue)
        
        # 紫色范围 (130-160)
        lower_purple = np.array([130, 70, 50])
        upper_purple = np.array([160, 255, 255])
        mask_purple = cv2.inRange(hsv_image, lower_purple, upper_purple)
        
        return mask_green | mask_cyan | mask_blue | mask_purple

    @staticmethod
    def find_and_draw_contours(image, mask, color, min_area=100):
        """在图像上找到并绘制轮廓"""
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
        """
        冷暖色识别
        返回: (结果图像, 统计信息字典)
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        warm_mask = cls.get_warm_mask(hsv)
        cool_mask = cls.get_cool_mask(hsv)
        
        warm_pixels = cv2.countNonZero(warm_mask)
        cool_pixels = cv2.countNonZero(cool_mask)
        
        total_colored = warm_pixels + cool_pixels
        if total_colored == 0:
            return image.copy(), {
                'warm_pixels': 0,
                'cool_pixels': 0,
                'warm_ratio': 0,
                'cool_ratio': 0,
                'blocks_found': 0,
                'message': '未检测到明显的暖色或冷色区域'
            }
        
        warm_ratio = warm_pixels / total_colored * 100
        cool_ratio = cool_pixels / total_colored * 100
        
        if warm_pixels > cool_pixels:
            result, count = cls.find_and_draw_contours(image, cool_mask, (255, 0, 0), min_area)
            message = f'暖色居多，已圈出 {count} 个冷色块（蓝框）'
        else:
            result, count = cls.find_and_draw_contours(image, warm_mask, (0, 0, 255), min_area)
            message = f'冷色居多，已圈出 {count} 个暖色块（红框）'
        
        return result, {
            'warm_pixels': warm_pixels,
            'cool_pixels': cool_pixels,
            'warm_ratio': warm_ratio,
            'cool_ratio': cool_ratio,
            'blocks_found': count,
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
        self.setMinimumSize(1000, 750)
        
        self.image_list = []
        self.current_index = -1
        self.current_image = None  # BGR格式的OpenCV图像
        self.answers_data = {}  # 答案数据 {filename: answer}
        self.answer_visible = False  # 答案是否可见
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # === 顶部控制区 ===
        top_group = QGroupBox("图库设置")
        top_layout = QHBoxLayout(top_group)
        
        top_layout.addWidget(QLabel("图库路径:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("请选择图库目录...")
        top_layout.addWidget(self.path_edit, 1)
        
        self.browse_btn = QPushButton("浏览...")
        top_layout.addWidget(self.browse_btn)
        
        main_layout.addWidget(top_group)
        
        # === 中间图像显示区 ===
        splitter = QSplitter(Qt.Horizontal)
        
        # 原图显示
        left_group = QGroupBox("原图")
        left_layout = QVBoxLayout(left_group)
        self.original_label = ImageLabel()
        self.original_label.setText("请选择图库并加载图片")
        left_layout.addWidget(self.original_label)
        splitter.addWidget(left_group)
        
        # 识别结果显示
        right_group = QGroupBox("识别结果")
        right_layout = QVBoxLayout(right_group)
        self.result_label = ImageLabel()
        self.result_label.setText("点击\"开始识别\"查看结果")
        right_layout.addWidget(self.result_label)
        splitter.addWidget(right_group)
        
        splitter.setSizes([500, 500])
        main_layout.addWidget(splitter, 1)
        
        # === 答案显示区 ===
        answer_group = QGroupBox("答案")
        answer_layout = QHBoxLayout(answer_group)
        
        self.answer_label = QLabel("???")
        self.answer_label.setAlignment(Qt.AlignCenter)
        answer_font = QFont()
        answer_font.setPointSize(24)
        answer_font.setBold(True)
        self.answer_label.setFont(answer_font)
        self.answer_label.setStyleSheet("QLabel { color: #333; padding: 10px; }")
        answer_layout.addWidget(self.answer_label, 1)
        
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
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        answer_layout.addWidget(self.show_answer_btn)
        
        main_layout.addWidget(answer_group)
        
        # === 底部控制区 ===
        bottom_group = QGroupBox("控制面板")
        bottom_layout = QHBoxLayout(bottom_group)
        
        # 图片导航
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一张")
        self.next_btn = QPushButton("下一张")
        self.random_btn = QPushButton("随机")
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
        self.method_combo.setMinimumWidth(150)
        method_layout.addWidget(self.method_combo)
        bottom_layout.addLayout(method_layout)
        
        bottom_layout.addSpacing(20)
        
        # 识别按钮
        self.detect_btn = QPushButton("开始识别")
        self.detect_btn.setMinimumWidth(120)
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        bottom_layout.addWidget(self.detect_btn)
        
        bottom_layout.addStretch()
        
        main_layout.addWidget(bottom_group)
        
        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 初始状态禁用按钮
        self._update_button_states()
    
    def _connect_signals(self):
        """连接信号"""
        self.browse_btn.clicked.connect(self._browse_folder)
        self.prev_btn.clicked.connect(self._prev_image)
        self.next_btn.clicked.connect(self._next_image)
        self.random_btn.clicked.connect(self._random_image)
        self.detect_btn.clicked.connect(self._detect)
        self.show_answer_btn.clicked.connect(self._toggle_answer)
    
    def _browse_folder(self):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择图库目录", str(Path.home())
        )
        if folder:
            self._load_folder(folder)
    
    def _load_folder(self, folder_path):
        """加载文件夹中的图片"""
        folder = Path(folder_path)
        self.image_list = sorted([
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ])
        
        self.path_edit.setText(folder_path)
        
        # 加载答案数据
        self._load_answers(folder)
        
        if self.image_list:
            self.current_index = 0
            self._load_current_image()
            self.status_bar.showMessage(f"已加载 {len(self.image_list)} 张图片")
        else:
            self.current_index = -1
            self.current_image = None
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
                self.status_bar.showMessage(f"已加载 {len(self.answers_data)} 个答案")
            except Exception as e:
                print(f"加载答案失败: {e}")
    
    def _load_current_image(self):
        """加载当前图片"""
        if 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]
            
            # 使用OpenCV读取图片
            self.current_image = cv2.imread(str(image_path))
            
            if self.current_image is not None:
                # 转换为QPixmap显示
                pixmap = self._cv2_to_pixmap(self.current_image)
                self.original_label.setImage(pixmap)
                
                # 清除之前的识别结果
                self.result_label.clear()
                self.result_label.setText("点击\"开始识别\"查看结果")
                
                # 重置答案显示
                self.answer_visible = False
                self._update_answer_display()
                
                self.status_bar.showMessage(f"已加载: {image_path.name}")
            else:
                self.original_label.setText(f"无法加载图片: {image_path.name}")
                self.status_bar.showMessage(f"加载失败: {image_path.name}")
        
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
            # 确保不会选到当前图片
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
            
            # 显示结果
            pixmap = self._cv2_to_pixmap(result_image)
            self.result_label.setImage(pixmap)
            
            # 更新状态栏
            self.status_bar.showMessage(
                f"暖色: {stats['warm_ratio']:.1f}% | "
                f"冷色: {stats['cool_ratio']:.1f}% | "
                f"{stats['message']}"
            )
    
    def _toggle_answer(self):
        """切换答案显示"""
        self.answer_visible = not self.answer_visible
        self._update_answer_display()
    
    def _update_answer_display(self):
        """更新答案显示"""
        if self.answer_visible:
            # 显示答案
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
            # 隐藏答案
            self.answer_label.setText("???")
            self.answer_label.setStyleSheet("QLabel { color: #333; padding: 10px; }")
            self.show_answer_btn.setText("显示答案")
    
    def _update_button_states(self):
        """更新按钮状态"""
        has_images = len(self.image_list) > 0
        has_current = self.current_image is not None
        
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_list) - 1)
        self.random_btn.setEnabled(len(self.image_list) > 1)
        self.detect_btn.setEnabled(has_current)
        
        # 更新图片计数
        if has_images:
            self.image_info_label.setText(f"{self.current_index + 1} / {len(self.image_list)}")
        else:
            self.image_info_label.setText("0 / 0")


def main():
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
