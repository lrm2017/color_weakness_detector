#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能OCR答案提取工具
自动从OCR结果中提取色弱检测答案
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

class SmartOCRExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 色弱检测答案词典
        self.answer_keywords = {
            # 动物类
            '熊猫': ['熊猫', 'panda'],
            '兔子': ['兔子', 'rabbit'],
            '老虎': ['老虎', 'tiger'],
            '狼': ['狼', 'wolf'],
            '骆驼': ['骆驼', 'camel'],
            '马': ['马', 'horse'],
            '牛': ['牛', 'cow', 'bull'],
            '羊': ['羊', 'sheep'],
            '金鱼': ['金鱼', 'goldfish'],
            '蝴蝶': ['蝴蝶', 'butterfly'],
            '蜻蜓': ['蜻蜓', 'dragonfly'],
            '鹅': ['鹅', 'goose'],
            '燕子': ['燕子', 'swallow'],
            
            # 物品类
            '手枪': ['手枪', 'pistol', 'gun'],
            '冲锋枪': ['冲锋枪', 'submachine'],
            '军舰': ['军舰', 'warship', 'ship'],
            '卡车': ['卡车', 'truck'],
            '摩托车': ['摩托车', 'motorcycle'],
            '拖拉机': ['拖拉机', 'tractor'],
            '剪刀': ['剪刀', 'scissors'],
            '壶': ['壶', 'pot', 'kettle'],
            '高射炮': ['高射炮', '炮'],
            
            # 几何图形
            '五角星': ['五角星', '星星', 'star'],
            '三角形': ['三角形', 'triangle', '△'],
            '圆形': ['圆形', 'circle', '○'],
            '正方形': ['正方形', 'square', '□'],
            
            # 其他
            '单色图': ['单色图', '单色'],
            '两颗': ['两颗', '两个'],
        }
        
        # 数字和字母模式
        self.number_pattern = re.compile(r'\b\d{1,4}\b')
        self.letter_pattern = re.compile(r'\b[A-Z]{2,6}\b')
        
    def download_image(self, url, save_path):
        """下载图像"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"下载失败 {url}: {e}")
            return False
    
    def preprocess_image(self, image_path):
        """预处理图像用于OCR"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return []
            
            height, width = img.shape[:2]
            
            # 尝试不同的区域大小和位置
            regions = [
                # 左下角不同大小
                (0, int(height * 0.7), int(width * 0.3), height),
                (0, int(height * 0.75), int(width * 0.35), height),
                (0, int(height * 0.8), int(width * 0.4), height),
                # 右下角
                (int(width * 0.6), int(height * 0.8), width, height),
                # 底部中央
                (int(width * 0.3), int(height * 0.8), int(width * 0.7), height),
            ]
            
            processed_images = []
            
            for i, (x1, y1, x2, y2) in enumerate(regions):
                roi = img[y1:y2, x1:x2]
                if roi.size == 0:
                    continue
                
                # 转换为灰度图
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                
                # 多种预处理方法
                methods = [
                    ('otsu', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                    ('otsu_inv', cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
                    ('adaptive', cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)),
                ]
                
                for method_name, processed in methods:
                    # 放大图像
                    scale_factor = 4
                    scaled = cv2.resize(processed, None, fx=scale_factor, fy=scale_factor, 
                                      interpolation=cv2.INTER_CUBIC)
                    processed_images.append((f"region{i}_{method_name}", scaled))
            
            return processed_images
            
        except Exception as e:
            print(f"图像预处理失败: {e}")
            return []
    
    def extract_text_from_image(self, image_path):
        """从图像提取文字"""
        processed_images = self.preprocess_image(image_path)
        if not processed_images:
            return []
        
        all_texts = []
        
        for method_name, processed_img in processed_images:
            # 尝试不同的OCR配置
            configs = [
                '--oem 3 --psm 6',
                '--oem 3 --psm 7',
                '--oem 3 --psm 8',
                '--oem 3 --psm 13',
            ]
            
            for config in configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(processed_img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        all_texts.append(text_chi.strip())
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(processed_img, lang='eng', config=config)
                    if text_eng.strip():
                        all_texts.append(text_eng.strip())
                        
                except Exception:
                    continue
        
        return all_texts
    
    def extract_answer_from_texts(self, texts):
        """从OCR文本列表中提取答案"""
        if not texts:
            return ""
        
        # 合并所有文本
        combined_text = ' '.join(texts)
        
        # 查找关键词答案
        for answer, keywords in self.answer_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    return answer
        
        # 查找数字答案
        numbers = []
        for text in texts:
            numbers.extend(self.number_pattern.findall(text))
        
        if numbers:
            # 选择最常见的数字，或最长的数字
            number_counts = {}
            for num in numbers:
                number_counts[num] = number_counts.get(num, 0) + 1
            
            # 优先选择出现次数多的，然后选择长度长的
            best_number = max(numbers, key=lambda x: (number_counts[x], len(x)))
            if len(best_number) >= 2:  # 至少2位数
                return best_number
        
        # 查找字母答案
        letters = []
        for text in texts:
            letters.extend(self.letter_pattern.findall(text))
        
        if letters:
            letter_counts = {}
            for letter in letters:
                letter_counts[letter] = letter_counts.get(letter, 0) + 1
            
            best_letter = max(letters, key=lambda x: (letter_counts[x], len(x)))
            if len(best_letter) >= 2:
                return best_letter
        
        return ""
    
    def process_single_image(self, image_path, original_url=None):
        """处理单个图像"""
        # 如果有原始URL，先下载
        if original_url:
            original_dir = Path(image_path).parent / "original_images"
            original_dir.mkdir(exist_ok=True)
            original_path = original_dir / Path(image_path).name
            
            if not original_path.exists():
                if not self.download_image(original_url, original_path):
                    return ""
                time.sleep(0.5)  # 避免请求过快
            
            image_path = str(original_path)
        
        # OCR识别
        texts = self.extract_text_from_image(image_path)
        answer = self.extract_answer_from_texts(texts)
        
        return answer
    
    def process_answers_json(self, json_path, update_file=True):
        """处理整个answers.json文件"""
        json_path = Path(json_path)
        
        # 读取答案文件
        with open(json_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        updated_count = 0
        
        for i, entry in enumerate(answers_data):
            filename = entry['filename']
            original_url = entry.get('original_url', '')
            current_answer = entry.get('answer', '')
            
            print(f"\n处理 {i+1}/{len(answers_data)}: {filename}")
            
            # 跳过已有正确答案的
            if current_answer and current_answer != '1查看色弱滤镜':
                print(f"跳过已有答案: {current_answer}")
                continue
            
            # 处理图像
            image_path = json_path.parent / filename
            answer = self.process_single_image(str(image_path), original_url)
            
            if answer:
                entry['answer'] = answer
                updated_count += 1
                print(f"识别结果: {answer}")
            else:
                print("未识别出答案")
        
        # 保存更新后的文件
        if update_file and updated_count > 0:
            backup_path = json_path.with_suffix('.json.backup3')
            if not backup_path.exists():
                json_path.rename(backup_path)
                print(f"\n原文件已备份: {backup_path}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功更新 {updated_count} 个答案")
        else:
            print(f"\n处理完成，更新了 {updated_count} 个答案")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='智能OCR答案提取工具')
    parser.add_argument('json_path', help='answers.json文件路径')
    parser.add_argument('--no-update', action='store_true', help='不更新文件')
    
    args = parser.parse_args()
    
    extractor = SmartOCRExtractor()
    extractor.process_answers_json(args.json_path, update_file=not args.no_update)

if __name__ == "__main__":
    main()