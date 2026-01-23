#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR答案提取工具
用于识别色弱检测图像左下角的答案文字，并自动更新answers.json文件
"""

import os
import json
import re
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pathlib import Path
import argparse
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OCRAnswerExtractor:
    def __init__(self):
        # 配置tesseract路径（如果需要）
        # pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
        
        # OCR配置
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz△○□熊猫兔子牛蜻蜓鹅金鱼燕子羊蝴蝶剪刀壶星星红色黄色蓝色绿色紫色单色图两颗'
        
    def preprocess_image_for_ocr(self, image_path, region_ratio=0.3):
        """
        预处理图像，提取左下角区域并优化OCR识别
        
        Args:
            image_path: 图像路径
            region_ratio: 左下角区域占图像的比例
        
        Returns:
            处理后的图像数组
        """
        try:
            # 读取图像
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图像: {image_path}")
                return None
                
            height, width = img.shape[:2]
            
            # 提取左下角区域
            start_y = int(height * (1 - region_ratio))
            end_y = height
            start_x = 0
            end_x = int(width * region_ratio)
            
            roi = img[start_y:end_y, start_x:end_x]
            
            # 转换为灰度图
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 图像增强
            # 1. 高斯模糊去噪
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 2. 自适应阈值二值化
            binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
            
            # 3. 形态学操作去除噪点
            kernel = np.ones((2, 2), np.uint8)
            cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            # 4. 放大图像提高识别率
            scale_factor = 3
            resized = cv2.resize(cleaned, None, fx=scale_factor, fy=scale_factor, 
                               interpolation=cv2.INTER_CUBIC)
            
            return resized
            
        except Exception as e:
            logger.error(f"图像预处理失败 {image_path}: {e}")
            return None
    
    def extract_text_from_image(self, image_path):
        """
        从图像中提取文字
        
        Args:
            image_path: 图像路径
            
        Returns:
            识别出的文字
        """
        processed_img = self.preprocess_image_for_ocr(image_path)
        if processed_img is None:
            return ""
            
        try:
            # 使用中英文混合识别
            text_chi = pytesseract.image_to_string(processed_img, lang='chi_sim', config=self.ocr_config)
            text_eng = pytesseract.image_to_string(processed_img, lang='eng', config=self.ocr_config)
            
            # 选择识别结果更好的
            text = text_chi if len(text_chi.strip()) > len(text_eng.strip()) else text_eng
            
            # 清理文字
            cleaned_text = self.clean_extracted_text(text)
            
            logger.info(f"从 {os.path.basename(image_path)} 识别出: '{cleaned_text}'")
            return cleaned_text
            
        except Exception as e:
            logger.error(f"OCR识别失败 {image_path}: {e}")
            return ""
    
    def clean_extracted_text(self, text):
        """
        清理提取的文字，去除序号和无关字符
        
        Args:
            text: 原始识别文字
            
        Returns:
            清理后的文字
        """
        if not text:
            return ""
            
        # 去除换行符和多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 去除常见的序号模式
        # 匹配模式如: "1.", "1、", "①", "1 ", "第1题", "题目1"等
        patterns_to_remove = [
            r'^\d+[\.、\s]',  # 数字+点/顿号/空格
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',  # 圆圈数字
            r'^第\d+题',  # "第X题"
            r'^题目\d+',  # "题目X"
            r'^\d+\s*[:：]',  # 数字+冒号
            r'^[A-Z]\.',  # 字母选项
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text).strip()
        
        # 去除特殊字符，但保留中文、英文、数字和常见符号
        text = re.sub(r'[^\w\u4e00-\u9fff△○□/\-]', '', text)
        
        return text.strip()
    
    def process_directory(self, directory_path, update_json=True):
        """
        处理整个目录的图像
        
        Args:
            directory_path: 目录路径
            update_json: 是否更新answers.json文件
        """
        directory_path = Path(directory_path)
        if not directory_path.exists():
            logger.error(f"目录不存在: {directory_path}")
            return
            
        # 查找answers.json文件
        answers_file = directory_path / "answers.json"
        if not answers_file.exists():
            logger.error(f"未找到answers.json文件: {answers_file}")
            return
            
        # 读取现有答案
        try:
            with open(answers_file, 'r', encoding='utf-8') as f:
                answers_data = json.load(f)
        except Exception as e:
            logger.error(f"读取answers.json失败: {e}")
            return
            
        # 处理每个图像
        updated_count = 0
        for answer_entry in answers_data:
            filename = answer_entry['filename']
            image_path = directory_path / filename
            
            if not image_path.exists():
                logger.warning(f"图像文件不存在: {image_path}")
                continue
                
            # 如果答案已经是正确的（不是占位符），跳过
            current_answer = answer_entry.get('answer', '')
            if current_answer and current_answer != '1查看色弱滤镜':
                logger.info(f"跳过已有正确答案的图像: {filename}")
                continue
                
            # 提取答案
            extracted_text = self.extract_text_from_image(str(image_path))
            
            if extracted_text:
                answer_entry['answer'] = extracted_text
                updated_count += 1
                logger.info(f"更新 {filename}: {extracted_text}")
            else:
                logger.warning(f"未能从 {filename} 提取到文字")
        
        # 保存更新后的答案
        if update_json and updated_count > 0:
            try:
                # 备份原文件
                backup_file = answers_file.with_suffix('.json.backup')
                answers_file.rename(backup_file)
                logger.info(f"原文件已备份为: {backup_file}")
                
                # 保存新文件
                with open(answers_file, 'w', encoding='utf-8') as f:
                    json.dump(answers_data, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"成功更新 {updated_count} 个答案到 {answers_file}")
                
            except Exception as e:
                logger.error(f"保存answers.json失败: {e}")
        else:
            logger.info("未进行文件更新")
    
    def test_single_image(self, image_path):
        """
        测试单个图像的OCR识别
        
        Args:
            image_path: 图像路径
        """
        logger.info(f"测试图像: {image_path}")
        
        # 显示预处理后的图像（用于调试）
        processed_img = self.preprocess_image_for_ocr(image_path)
        if processed_img is not None:
            cv2.imshow('Processed Image', processed_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # 提取文字
        text = self.extract_text_from_image(image_path)
        print(f"识别结果: '{text}'")

def main():
    parser = argparse.ArgumentParser(description='OCR答案提取工具')
    parser.add_argument('path', help='图像文件路径或目录路径')
    parser.add_argument('--test', action='store_true', help='测试模式，只识别不更新文件')
    parser.add_argument('--no-update', action='store_true', help='不更新answers.json文件')
    
    args = parser.parse_args()
    
    extractor = OCRAnswerExtractor()
    
    path = Path(args.path)
    
    if path.is_file():
        # 单个文件测试
        extractor.test_single_image(str(path))
    elif path.is_dir():
        # 目录处理
        update_json = not args.no_update and not args.test
        extractor.process_directory(str(path), update_json=update_json)
    else:
        logger.error(f"路径不存在: {path}")

if __name__ == "__main__":
    main()