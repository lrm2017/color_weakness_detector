#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用OCR答案提取工具
适用于所有色弱检测图像版本
"""

import json
import cv2
import pytesseract
import numpy as np
from pathlib import Path
import re
import requests
import time
import argparse

class UniversalOCRTool:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 综合答案词典（基于所有版本的已知答案）
        self.known_answers = {
            # 动物类
            '熊猫', '兔子', '老虎', '狼', '骆驼', '马', '牛', '羊', '金鱼', '蝴蝶', '蜻蜓', '鹅', '燕子',
            '大熊猫', '壶',
            
            # 物品类
            '手枪', '冲锋枪', '军舰', '卡车', '摩托车', '拖拉机', '剪刀', '壶', '高射炮',
            
            # 几何图形和符号
            '五角星', '三角形', '圆形', '正方形', '△', '○', '□', '两颗星星',
            
            # 特殊描述
            '单色图-红色', '单色图-黄色', '单色图-蓝色', '单色图-绿色', '单色图-紫色',
            '单色图', '两颗',
            
            # 其他中文词汇
            '洪水', '人', '和', '了'
        }
        
        # OCR配置
        self.ocr_configs = [
            "--oem 3 --psm 6",
            "--oem 3 --psm 7", 
            "--oem 3 --psm 8",
            "--oem 3 --psm 13",
        ]
    
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
    
    def preprocess_image_comprehensive(self, image_path):
        """全面的图像预处理"""
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        processed_images = []
        
        # 多个可能的答案区域
        regions = [
            # 左下角 - 最常见
            (0, int(height*0.75), int(width*0.3), height),
            (0, int(height*0.7), int(width*0.4), height),
            # 右下角
            (int(width*0.7), int(height*0.75), width, height),
            # 底部中央
            (int(width*0.3), int(height*0.8), int(width*0.7), height),
            # 整个底部
            (0, int(height*0.85), width, height),
        ]
        
        for i, (x1, y1, x2, y2) in enumerate(regions):
            roi = img[y1:y2, x1:x2]
            if roi.size == 0:
                continue
            
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # 多种预处理方法
            methods = [
                ("original", gray),
                ("otsu", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
                ("otsu_inv", cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]),
                ("adaptive_mean", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 10)),
                ("adaptive_gaussian", cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)),
            ]
            
            for method_name, processed in methods:
                # 多种放大倍数
                for scale in [3, 4, 5]:
                    scaled = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                    processed_images.append({
                        "name": f"region{i}_{method_name}_scale{scale}",
                        "image": scaled,
                        "region": i,
                        "method": method_name,
                        "scale": scale
                    })
        
        return processed_images[:30]  # 限制数量避免过慢
    
    def extract_text_from_images(self, processed_images):
        """从预处理图像中提取文字"""
        all_texts = []
        
        for img_data in processed_images:
            img = img_data["image"]
            
            for config in self.ocr_configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        all_texts.append({
                            "text": text_chi.strip(),
                            "lang": "chi_sim",
                            "config": config,
                            "source": img_data
                        })
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(img, lang='eng', config=config)
                    if text_eng.strip():
                        all_texts.append({
                            "text": text_eng.strip(),
                            "lang": "eng", 
                            "config": config,
                            "source": img_data
                        })
                        
                except Exception:
                    continue
        
        return all_texts
    
    def extract_answer_candidates(self, texts):
        """从文本中提取答案候选"""
        candidates = {}
        
        for text_data in texts:
            text = text_data["text"]
            
            # 检查已知答案
            for known_answer in self.known_answers:
                if known_answer in text:
                    if known_answer not in candidates:
                        candidates[known_answer] = 0
                    candidates[known_answer] += 1
            
            # 提取数字（1-4位）
            numbers = re.findall(r'\b\d{1,4}\b', text)
            for num in numbers:
                if len(num) >= 2:  # 至少2位数
                    if num not in candidates:
                        candidates[num] = 0
                    candidates[num] += 1
            
            # 提取大写字母组合（2-6位）
            letters = re.findall(r'\b[A-Z]{2,6}\b', text)
            for letter in letters:
                if letter not in candidates:
                    candidates[letter] = 0
                candidates[letter] += 1
            
            # 提取中文词汇（1-4字）
            chinese_words = re.findall(r'[\u4e00-\u9fff]{1,4}', text)
            for word in chinese_words:
                if len(word) >= 1:
                    if word not in candidates:
                        candidates[word] = 0
                    candidates[word] += 1
            
            # 提取符号组合
            symbols = re.findall(r'[△○□/\-]{1,5}', text)
            for symbol in symbols:
                if symbol not in candidates:
                    candidates[symbol] = 0
                candidates[symbol] += 1
        
        return candidates
    
    def select_best_answer(self, candidates):
        """选择最佳答案"""
        if not candidates:
            return ""
        
        # 按出现频次排序
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
        
        # 优先选择已知答案
        for candidate, count in sorted_candidates:
            if candidate in self.known_answers:
                return candidate
        
        # 选择出现次数最多且长度合理的
        for candidate, count in sorted_candidates:
            if len(candidate) >= 2 or candidate.isdigit():
                return candidate
        
        return sorted_candidates[0][0] if sorted_candidates else ""
    
    def process_single_image(self, image_path, original_url=None, debug=False):
        """处理单个图像"""
        # 下载原始图像
        if original_url:
            original_dir = Path(image_path).parent / "original_images"
            original_dir.mkdir(exist_ok=True)
            original_path = original_dir / Path(image_path).name
            
            if not original_path.exists():
                print(f"  下载原始图像...")
                if not self.download_image(original_url, original_path):
                    return ""
                time.sleep(0.5)
            
            image_path = str(original_path)
        
        # OCR处理
        processed_images = self.preprocess_image_comprehensive(image_path)
        if not processed_images:
            return ""
        
        texts = self.extract_text_from_images(processed_images)
        candidates = self.extract_answer_candidates(texts)
        
        if debug and candidates:
            print(f"  候选答案: {dict(list(candidates.items())[:5])}")
        
        answer = self.select_best_answer(candidates)
        return answer
    
    def process_answers_file(self, json_path, update_file=True, debug=False):
        """处理整个answers.json文件"""
        json_path = Path(json_path)
        
        with open(json_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        print(f"处理 {json_path.parent.name} ({len(answers_data)} 个图像)")
        
        updated_count = 0
        placeholder_count = 0
        
        for i, entry in enumerate(answers_data):
            filename = entry['filename']
            original_url = entry.get('original_url', '')
            current_answer = entry.get('answer', '')
            
            if current_answer == '1查看色弱滤镜':
                placeholder_count += 1
                
                print(f"\n处理 {i+1}/{len(answers_data)}: {filename}")
                
                if not original_url:
                    print("  没有原始URL")
                    continue
                
                # 处理图像
                image_path = json_path.parent / filename
                answer = self.process_single_image(str(image_path), original_url, debug)
                
                if answer:
                    entry['answer'] = answer
                    updated_count += 1
                    print(f"  识别结果: {answer}")
                else:
                    print("  未识别出答案")
        
        print(f"\n处理完成:")
        print(f"  待处理: {placeholder_count}")
        print(f"  已更新: {updated_count}")
        print(f"  成功率: {updated_count/placeholder_count*100:.1f}%" if placeholder_count > 0 else "  无需处理")
        
        # 保存结果
        if update_file and updated_count > 0:
            backup_path = json_path.with_suffix('.json.backup_universal')
            if not backup_path.exists():
                json_path.rename(backup_path)
                print(f"  原文件已备份: {backup_path.name}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, ensure_ascii=False, indent=2)
            
            print(f"  已保存更新")

def main():
    parser = argparse.ArgumentParser(description='通用OCR答案提取工具')
    parser.add_argument('json_path', help='answers.json文件路径')
    parser.add_argument('--no-update', action='store_true', help='不更新文件')
    parser.add_argument('--debug', action='store_true', help='显示调试信息')
    
    args = parser.parse_args()
    
    tool = UniversalOCRTool()
    tool.process_answers_file(args.json_path, update_file=not args.no_update, debug=args.debug)

if __name__ == "__main__":
    main()