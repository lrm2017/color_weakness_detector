#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的OCR测试工具
"""

import os
import cv2
import pytesseract
import numpy as np
from pathlib import Path
import json
import re

class ImprovedOCR:
    def __init__(self):
        # 多种OCR配置
        self.ocr_configs = [
            '--oem 3 --psm 6',  # 默认配置
            '--oem 3 --psm 7',  # 单行文字
            '--oem 3 --psm 8',  # 单词
            '--oem 3 --psm 13', # 原始行，不进行hack
        ]
    
    def preprocess_image_multiple_ways(self, image_path):
        """
        用多种方式预处理图像
        """
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        
        # 尝试不同的区域大小
        region_ratios = [0.25, 0.3, 0.35, 0.4]
        processed_images = []
        
        for ratio in region_ratios:
            # 提取左下角区域
            start_y = int(height * (1 - ratio))
            end_y = height
            start_x = 0
            end_x = int(width * ratio)
            
            roi = img[start_y:end_y, start_x:end_x]
            
            # 多种预处理方法
            methods = self.get_preprocessing_methods(roi)
            processed_images.extend(methods)
        
        return processed_images
    
    def get_preprocessing_methods(self, roi):
        """
        获取多种预处理方法
        """
        methods = []
        
        # 转换为灰度图
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 方法1: 简单二值化
        _, binary1 = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        methods.append(('binary_simple', binary1))
        
        # 方法2: OTSU二值化
        _, binary2 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        methods.append(('binary_otsu', binary2))
        
        # 方法3: 自适应阈值
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        methods.append(('adaptive', adaptive))
        
        # 方法4: 反色处理
        inverted = cv2.bitwise_not(binary2)
        methods.append(('inverted', inverted))
        
        # 方法5: 形态学处理
        kernel = np.ones((2, 2), np.uint8)
        morphed = cv2.morphologyEx(binary2, cv2.MORPH_CLOSE, kernel)
        methods.append(('morphed', morphed))
        
        # 方法6: 高斯模糊后二值化
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary_blur = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        methods.append(('blur_binary', binary_blur))
        
        # 放大所有图像
        scale_factor = 3
        scaled_methods = []
        for name, img in methods:
            scaled = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, 
                              interpolation=cv2.INTER_CUBIC)
            scaled_methods.append((name, scaled))
        
        return scaled_methods
    
    def extract_text_comprehensive(self, image_path):
        """
        综合提取文字
        """
        processed_images = self.preprocess_image_multiple_ways(image_path)
        
        all_results = []
        
        for i, (method_name, processed_img) in enumerate(processed_images):
            # 保存调试图像
            debug_path = f"debug_{method_name}_{i}.jpg"
            cv2.imwrite(debug_path, processed_img)
            
            # 尝试不同的OCR配置
            for config in self.ocr_configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(processed_img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        all_results.append(('chi_sim', method_name, config, text_chi.strip()))
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(processed_img, lang='eng', config=config)
                    if text_eng.strip():
                        all_results.append(('eng', method_name, config, text_eng.strip()))
                        
                except Exception as e:
                    continue
        
        return all_results
    
    def clean_text(self, text):
        """
        清理识别的文字
        """
        if not text:
            return ""
        
        # 去除换行符和多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 去除序号
        patterns = [
            r'^\d+[\.、\s]',
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',
            r'^第\d+题',
            r'^题目\d+',
            r'^\d+\s*[:：]',
            r'^[A-Z]\.',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text).strip()
        
        # 只保留有意义的字符
        text = re.sub(r'[^\w\u4e00-\u9fff△○□/\-]', '', text)
        
        return text.strip()
    
    def test_image(self, image_path):
        """
        测试单个图像
        """
        print(f"\n=== 测试图像: {image_path} ===")
        
        results = self.extract_text_comprehensive(image_path)
        
        if not results:
            print("未识别出任何文字")
            return None
        
        print(f"共获得 {len(results)} 个识别结果:")
        
        # 显示所有结果
        cleaned_results = []
        for lang, method, config, text in results:
            cleaned = self.clean_text(text)
            if cleaned:
                cleaned_results.append((lang, method, config, text, cleaned))
                print(f"  {lang} | {method} | {config[:15]}... | 原文: '{text}' | 清理后: '{cleaned}'")
        
        if not cleaned_results:
            print("清理后无有效结果")
            return None
        
        # 选择最佳结果（最长的清理后文字）
        best_result = max(cleaned_results, key=lambda x: len(x[4]))
        best_text = best_result[4]
        
        print(f"\n最佳结果: '{best_text}'")
        return best_text

def main():
    ocr = ImprovedOCR()
    
    # 测试目录
    test_dir = Path("downloaded_images/李春慧新编")
    if not test_dir.exists():
        print(f"测试目录不存在: {test_dir}")
        return
    
    # 测试前几个图像
    test_files = ["001.jpg", "002.jpg", "003.jpg", "004.jpg", "005.jpg"]
    
    results = {}
    for filename in test_files:
        image_path = test_dir / filename
        if image_path.exists():
            result = ocr.test_image(str(image_path))
            if result:
                results[filename] = result
    
    print(f"\n=== 测试总结 ===")
    for filename, result in results.items():
        print(f"{filename}: '{result}'")
    
    # 清理调试文件
    print(f"\n清理调试文件...")
    for debug_file in Path(".").glob("debug_*.jpg"):
        debug_file.unlink()
        print(f"删除: {debug_file}")

if __name__ == "__main__":
    main()