#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终OCR处理工具
基于验证结果优化的OCR答案提取
"""

import json
import cv2
import pytesseract
import numpy as np
from pathlib import Path
import re
import requests
import time

class FinalOCRProcessor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 基于测试结果的最佳OCR配置
        self.best_configs = [
            "--oem 3 --psm 6",  # 对数字和字母效果好
            "--oem 3 --psm 7",  # 单行文本
            "--oem 3 --psm 8",  # 单词识别
        ]
        
        # 答案模式匹配
        self.answer_patterns = {
            # 动物类 - 从之前的OCR结果中提取的
            '拖拉机': ['拖拉机', 'tractor'],
            '骆驼': ['骆驼', 'camel'],
            '老虎': ['老虎', 'tiger'],
            '冲锋枪': ['冲锋枪'],
            '高射炮': ['高射炮', '炮'],
            '卡车': ['卡车', 'truck'],
            '军舰': ['军舰', 'ship'],
            '手枪': ['手枪', 'gun'],
            '金鱼': ['金鱼', 'fish'],
            '摩托车': ['摩托车', 'motor'],
            '狼': ['狼', 'wolf'],
            '五角星': ['五角星', '星', 'star'],
            '熊猫': ['熊猫', 'panda'],
            '兔子': ['兔子', 'rabbit'],
            '马': ['马', 'horse'],
            '牛': ['牛', 'cow'],
            '羊': ['羊', 'sheep'],
            '蝴蝶': ['蝴蝶', 'butterfly'],
            '蜻蜓': ['蜻蜓'],
            '鹅': ['鹅', 'goose'],
            '燕子': ['燕子'],
            '剪刀': ['剪刀', 'scissors'],
            '壶': ['壶', 'pot'],
        }
    
    def download_image(self, url, save_path):
        """下载图像"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def get_optimal_preprocessing(self, image_path):
        """
        基于测试结果的最优预处理
        """
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        processed_images = []
        
        # 最有效的区域：左下角
        regions = [
            (0, int(height*0.75), int(width*0.3), height),  # 左下角小区域
            (0, int(height*0.7), int(width*0.4), height),   # 左下角大区域
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(regions):
            roi = img[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 最有效的预处理方法
            methods = [
                ("original", gray),
                ("otsu", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                ("adaptive", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)),
            ]
            
            for method_name, processed in methods:
                # 最有效的放大倍数
                for scale in [3, 4]:
                    scaled = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                    processed_images.append({
                        "name": f"region{i}_{method_name}_scale{scale}",
                        "image": scaled
                    })
        
        return processed_images
    
    def extract_answer_candidates(self, processed_images):
        """提取答案候选"""
        all_candidates = {}
        
        for img_data in processed_images:
            img = img_data["image"]
            
            for config in self.best_configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        candidates = self.parse_text_for_answers(text_chi.strip())
                        for candidate in candidates:
                            if candidate not in all_candidates:
                                all_candidates[candidate] = 0
                            all_candidates[candidate] += 1
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(img, lang='eng', config=config)
                    if text_eng.strip():
                        candidates = self.parse_text_for_answers(text_eng.strip())
                        for candidate in candidates:
                            if candidate not in all_candidates:
                                all_candidates[candidate] = 0
                            all_candidates[candidate] += 1
                            
                except Exception:
                    continue
        
        return all_candidates
    
    def parse_text_for_answers(self, text):
        """从文本中解析可能的答案"""
        candidates = []
        
        # 检查已知答案模式
        for answer, keywords in self.answer_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    candidates.append(answer)
                    break
        
        # 提取数字（2-4位）
        numbers = re.findall(r'\b\d{2,4}\b', text)
        candidates.extend(numbers)
        
        # 提取大写字母组合（2-6位）
        letters = re.findall(r'\b[A-Z]{2,6}\b', text)
        candidates.extend(letters)
        
        # 提取中文词汇（1-4字）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{1,4}', text)
        candidates.extend(chinese_words)
        
        # 提取符号组合
        symbols = re.findall(r'[△○□/\-]{1,3}', text)
        candidates.extend(symbols)
        
        return candidates
    
    def select_best_answer(self, candidates):
        """选择最佳答案"""
        if not candidates:
            return ""
        
        # 按出现频次排序
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        
        # 优先选择已知答案模式
        for candidate, count in sorted_candidates:
            if candidate in self.answer_patterns:
                return candidate
        
        # 选择出现次数最多的
        return sorted_candidates[0][0]
    
    def process_single_image(self, image_path, original_url=None):
        """处理单个图像"""
        # 下载原始图像
        if original_url:
            original_dir = Path(image_path).parent / "original_images"
            original_dir.mkdir(exist_ok=True)
            original_path = original_dir / Path(image_path).name
            
            if not original_path.exists():
                if not self.download_image(original_url, original_path):
                    return ""
                time.sleep(0.5)
            
            image_path = str(original_path)
        
        # OCR处理
        processed_images = self.get_optimal_preprocessing(image_path)
        if not processed_images:
            return ""
        
        candidates = self.extract_answer_candidates(processed_images)
        answer = self.select_best_answer(candidates)
        
        return answer
    
    def process_remaining_answers(self, json_path):
        """处理剩余的答案"""
        json_path = Path(json_path)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        updated_count = 0
        
        for i, entry in enumerate(answers_data):
            filename = entry['filename']
            original_url = entry.get('original_url', '')
            current_answer = entry.get('answer', '')
            
            print(f"\n处理 {i+1}/{len(answers_data)}: {filename}")
            
            # 只处理占位符答案
            if current_answer != '1查看色弱滤镜':
                print(f"跳过已有答案: {current_answer}")
                continue
            
            if not original_url:
                print("没有原始URL")
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
        
        # 保存结果
        if updated_count > 0:
            backup_path = json_path.with_suffix('.json.backup_final')
            if not backup_path.exists():
                json_path.rename(backup_path)
                print(f"\n原文件已备份: {backup_path}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功更新 {updated_count} 个答案")
        else:
            print("\n没有需要更新的答案")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='最终OCR处理工具')
    parser.add_argument('json_path', help='answers.json文件路径')
    
    args = parser.parse_args()
    
    processor = FinalOCRProcessor()
    processor.process_remaining_answers(args.json_path)

if __name__ == "__main__":
    main()