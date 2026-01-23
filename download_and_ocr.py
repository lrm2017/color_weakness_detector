#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载原始图像并进行OCR识别答案
"""

import os
import json
import requests
import cv2
import pytesseract
import numpy as np
from pathlib import Path
import re
import time
from urllib.parse import urlparse

class DownloadAndOCR:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # OCR配置
        self.ocr_configs = [
            '--oem 3 --psm 6',  # 默认配置
            '--oem 3 --psm 7',  # 单行文字
            '--oem 3 --psm 8',  # 单词
        ]
    
    def download_image(self, url, save_path):
        """
        下载图像
        """
        try:
            print(f"下载: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"保存到: {save_path}")
            return True
            
        except Exception as e:
            print(f"下载失败 {url}: {e}")
            return False
    
    def preprocess_for_ocr(self, image_path, region_ratio=0.3):
        """
        预处理图像用于OCR
        """
        try:
            img = cv2.imread(image_path)
            if img is None:
                return []
            
            height, width = img.shape[:2]
            
            # 提取左下角区域
            start_y = int(height * (1 - region_ratio))
            end_y = height
            start_x = 0
            end_x = int(width * region_ratio)
            
            roi = img[start_y:end_y, start_x:end_x]
            
            # 转换为灰度图
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 多种预处理方法
            processed_images = []
            
            # 方法1: OTSU二值化
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            processed_images.append(('otsu', binary))
            
            # 方法2: 反色OTSU
            _, binary_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            processed_images.append(('otsu_inv', binary_inv))
            
            # 方法3: 自适应阈值
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, 11, 2)
            processed_images.append(('adaptive', adaptive))
            
            # 放大图像
            scale_factor = 4
            scaled_images = []
            for name, img_proc in processed_images:
                scaled = cv2.resize(img_proc, None, fx=scale_factor, fy=scale_factor, 
                                  interpolation=cv2.INTER_CUBIC)
                scaled_images.append((name, scaled))
            
            return scaled_images
            
        except Exception as e:
            print(f"图像预处理失败 {image_path}: {e}")
            return []
    
    def extract_text_from_processed_images(self, processed_images, debug_prefix=""):
        """
        从预处理图像中提取文字
        """
        all_results = []
        
        for i, (method_name, processed_img) in enumerate(processed_images):
            # 保存调试图像
            if debug_prefix:
                debug_path = f"{debug_prefix}_{method_name}.jpg"
                cv2.imwrite(debug_path, processed_img)
            
            # 尝试不同的OCR配置和语言
            for config in self.ocr_configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(processed_img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        all_results.append(('chi_sim', method_name, text_chi.strip()))
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(processed_img, lang='eng', config=config)
                    if text_eng.strip():
                        all_results.append(('eng', method_name, text_eng.strip()))
                        
                except Exception as e:
                    continue
        
        return all_results
    
    def clean_extracted_text(self, text):
        """
        清理提取的文字
        """
        if not text:
            return ""
        
        # 去除换行符和多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 去除序号模式
        patterns = [
            r'^\d+[\.、\s]',
            r'^[①②③④⑤⑥⑦⑧⑨⑩]',
            r'^第\d+题',
            r'^题目\d+',
            r'^\d+\s*[:：]',
            r'^[A-Z]\.',
            r'^\d+\)',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text).strip()
        
        # 只保留有意义的字符
        text = re.sub(r'[^\w\u4e00-\u9fff△○□/\-]', '', text)
        
        return text.strip()
    
    def ocr_single_image(self, image_path, debug=False):
        """
        对单个图像进行OCR
        """
        processed_images = self.preprocess_for_ocr(image_path)
        if not processed_images:
            return ""
        
        debug_prefix = f"debug_{Path(image_path).stem}" if debug else ""
        results = self.extract_text_from_processed_images(processed_images, debug_prefix)
        
        if not results:
            return ""
        
        # 清理所有结果
        cleaned_results = []
        for lang, method, text in results:
            cleaned = self.clean_extracted_text(text)
            if cleaned and len(cleaned) > 0:
                cleaned_results.append((lang, method, text, cleaned))
        
        if not cleaned_results:
            return ""
        
        # 选择最佳结果
        # 优先选择中文结果，然后选择最长的
        chi_results = [r for r in cleaned_results if r[0] == 'chi_sim']
        if chi_results:
            best_result = max(chi_results, key=lambda x: len(x[3]))
        else:
            best_result = max(cleaned_results, key=lambda x: len(x[3]))
        
        return best_result[3]
    
    def process_answers_json(self, json_path, download_originals=True, update_answers=True):
        """
        处理answers.json文件
        """
        json_path = Path(json_path)
        if not json_path.exists():
            print(f"文件不存在: {json_path}")
            return
        
        # 读取答案文件
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                answers_data = json.load(f)
        except Exception as e:
            print(f"读取JSON文件失败: {e}")
            return
        
        # 创建原始图像目录
        original_dir = json_path.parent / "original_images"
        original_dir.mkdir(exist_ok=True)
        
        updated_count = 0
        
        for i, entry in enumerate(answers_data):
            filename = entry['filename']
            original_url = entry.get('original_url', '')
            current_answer = entry.get('answer', '')
            
            print(f"\n处理 {i+1}/{len(answers_data)}: {filename}")
            
            # 跳过已有正确答案的项目
            if current_answer and current_answer != '1查看色弱滤镜':
                print(f"跳过已有答案: {current_answer}")
                continue
            
            if not original_url:
                print("没有原始URL")
                continue
            
            # 下载原始图像
            original_image_path = original_dir / filename
            
            if download_originals:
                if not original_image_path.exists():
                    if not self.download_image(original_url, original_image_path):
                        continue
                    time.sleep(1)  # 避免请求过快
                else:
                    print(f"原始图像已存在: {original_image_path}")
            
            if not original_image_path.exists():
                print(f"原始图像不存在: {original_image_path}")
                continue
            
            # OCR识别
            extracted_text = self.ocr_single_image(str(original_image_path), debug=False)
            
            if extracted_text:
                entry['answer'] = extracted_text
                updated_count += 1
                print(f"识别结果: '{extracted_text}'")
            else:
                print("未识别出文字")
        
        # 保存更新后的答案
        if update_answers and updated_count > 0:
            try:
                # 备份原文件
                backup_path = json_path.with_suffix('.json.backup')
                if not backup_path.exists():
                    json_path.rename(backup_path)
                    print(f"原文件已备份: {backup_path}")
                
                # 保存新文件
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(answers_data, f, ensure_ascii=False, indent=2)
                
                print(f"\n成功更新 {updated_count} 个答案")
                
            except Exception as e:
                print(f"保存文件失败: {e}")
        else:
            print(f"\n未更新任何答案")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='下载原始图像并进行OCR识别')
    parser.add_argument('json_path', help='answers.json文件路径')
    parser.add_argument('--no-download', action='store_true', help='不下载图像，只处理已有的')
    parser.add_argument('--no-update', action='store_true', help='不更新答案文件')
    parser.add_argument('--test', help='测试单个图像文件')
    
    args = parser.parse_args()
    
    ocr_tool = DownloadAndOCR()
    
    if args.test:
        # 测试单个图像
        result = ocr_tool.ocr_single_image(args.test, debug=True)
        print(f"识别结果: '{result}'")
    else:
        # 处理整个答案文件
        download_originals = not args.no_download
        update_answers = not args.no_update
        
        ocr_tool.process_answers_json(args.json_path, download_originals, update_answers)

if __name__ == "__main__":
    main()