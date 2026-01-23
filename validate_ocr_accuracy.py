#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证OCR准确性工具
对比OCR结果与已知正确答案
"""

import json
import cv2
import pytesseract
import numpy as np
from pathlib import Path
import re
import requests
import time

class OCRValidator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_original_image(self, url, save_path):
        """下载原始图像"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False
    
    def preprocess_image_for_answer_region(self, image_path):
        """
        专门针对答案区域的图像预处理
        尝试多种区域和预处理方法
        """
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        processed_images = []
        
        # 尝试不同的答案区域位置
        regions = [
            # 左下角 - 最常见的答案位置
            {"name": "left_bottom", "coords": (0, int(height*0.75), int(width*0.3), height)},
            {"name": "left_bottom_large", "coords": (0, int(height*0.7), int(width*0.4), height)},
            # 右下角 - 有些图可能在右下
            {"name": "right_bottom", "coords": (int(width*0.7), int(height*0.75), width, height)},
            # 底部中央
            {"name": "center_bottom", "coords": (int(width*0.3), int(height*0.8), int(width*0.7), height)},
            # 整个底部
            {"name": "full_bottom", "coords": (0, int(height*0.8), width, height)},
        ]
        
        for region in regions:
            x1, y1, x2, y2 = region["coords"]
            roi = img[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            # 转换为灰度
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
                # 放大图像提高识别率
                for scale in [3, 4, 5]:
                    scaled = cv2.resize(processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
                    
                    # 可选的形态学操作
                    kernel = np.ones((2,2), np.uint8)
                    morphed = cv2.morphologyEx(scaled, cv2.MORPH_CLOSE, kernel)
                    
                    processed_images.append({
                        "name": f"{region['name']}_{method_name}_scale{scale}",
                        "image": scaled,
                        "region": region['name'],
                        "method": method_name,
                        "scale": scale
                    })
                    
                    processed_images.append({
                        "name": f"{region['name']}_{method_name}_scale{scale}_morphed",
                        "image": morphed,
                        "region": region['name'],
                        "method": f"{method_name}_morphed",
                        "scale": scale
                    })
        
        return processed_images
    
    def extract_text_comprehensive(self, processed_images, debug_prefix=""):
        """
        全面的文字提取
        """
        all_results = []
        
        # OCR配置
        configs = [
            "--oem 3 --psm 6",  # 统一文本块
            "--oem 3 --psm 7",  # 单行文本
            "--oem 3 --psm 8",  # 单词
            "--oem 3 --psm 13", # 原始行
            "--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",  # 只识别字母数字
            "--oem 3 --psm 7 -c tessedit_char_whitelist=0123456789",  # 只识别数字
        ]
        
        for i, img_data in enumerate(processed_images[:20]):  # 限制处理数量避免过慢
            img = img_data["image"]
            name = img_data["name"]
            
            # 保存调试图像
            if debug_prefix:
                debug_path = f"{debug_prefix}_{name}.jpg"
                cv2.imwrite(debug_path, img)
            
            for config in configs:
                try:
                    # 中文识别
                    text_chi = pytesseract.image_to_string(img, lang='chi_sim', config=config)
                    if text_chi.strip():
                        all_results.append({
                            "lang": "chi_sim",
                            "config": config,
                            "method": name,
                            "text": text_chi.strip(),
                            "region": img_data["region"],
                            "preprocessing": img_data["method"]
                        })
                    
                    # 英文识别
                    text_eng = pytesseract.image_to_string(img, lang='eng', config=config)
                    if text_eng.strip():
                        all_results.append({
                            "lang": "eng", 
                            "config": config,
                            "method": name,
                            "text": text_eng.strip(),
                            "region": img_data["region"],
                            "preprocessing": img_data["method"]
                        })
                        
                except Exception as e:
                    continue
        
        return all_results
    
    def clean_and_extract_answer(self, text):
        """
        清理文本并提取可能的答案
        """
        if not text:
            return []
        
        # 去除换行和多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        
        candidates = []
        
        # 提取中文词汇（动物、物品等）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{1,4}', text)
        candidates.extend(chinese_words)
        
        # 提取英文单词
        english_words = re.findall(r'[A-Za-z]{2,10}', text)
        candidates.extend([w.upper() for w in english_words])
        
        # 提取数字
        numbers = re.findall(r'\d{1,4}', text)
        candidates.extend(numbers)
        
        # 提取特殊符号组合
        symbols = re.findall(r'[△○□/\-]{1,3}', text)
        candidates.extend(symbols)
        
        return candidates
    
    def test_ocr_on_known_answers(self, json_path, test_count=10):
        """
        在已知答案上测试OCR准确性
        """
        json_path = Path(json_path)
        
        # 读取答案文件
        with open(json_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        # 创建原始图像目录
        original_dir = json_path.parent / "original_images"
        original_dir.mkdir(exist_ok=True)
        
        # 测试前几个已知答案
        test_results = []
        
        for i, entry in enumerate(answers_data[:test_count]):
            filename = entry['filename']
            expected_answer = entry['answer']
            original_url = entry.get('original_url', '')
            
            print(f"\n=== 测试 {i+1}/{test_count}: {filename} ===")
            print(f"期望答案: {expected_answer}")
            
            if not original_url:
                print("没有原始URL")
                continue
            
            # 下载原始图像
            original_path = original_dir / filename
            if not original_path.exists():
                print(f"下载原始图像...")
                if not self.download_original_image(original_url, original_path):
                    continue
                time.sleep(0.5)
            
            # OCR处理
            processed_images = self.preprocess_image_for_answer_region(str(original_path))
            if not processed_images:
                print("图像预处理失败")
                continue
            
            # 提取文字
            debug_prefix = f"debug_{filename.split('.')[0]}"
            ocr_results = self.extract_text_comprehensive(processed_images, debug_prefix)
            
            print(f"OCR识别到 {len(ocr_results)} 个结果:")
            
            # 分析所有候选答案
            all_candidates = []
            for result in ocr_results:
                candidates = self.clean_and_extract_answer(result["text"])
                for candidate in candidates:
                    all_candidates.append({
                        "candidate": candidate,
                        "source": result,
                        "original_text": result["text"]
                    })
            
            # 显示候选答案
            unique_candidates = {}
            for item in all_candidates:
                candidate = item["candidate"]
                if candidate not in unique_candidates:
                    unique_candidates[candidate] = []
                unique_candidates[candidate].append(item)
            
            print("候选答案:")
            correct_found = False
            for candidate, sources in unique_candidates.items():
                count = len(sources)
                is_correct = candidate == expected_answer
                if is_correct:
                    correct_found = True
                
                print(f"  '{candidate}' (出现{count}次) {'✓' if is_correct else ''}")
                
                # 显示最佳来源
                best_source = sources[0]["source"]
                print(f"    来源: {best_source['region']} | {best_source['preprocessing']} | {best_source['lang']}")
                print(f"    原文: '{sources[0]['original_text'][:50]}...'")
            
            test_results.append({
                "filename": filename,
                "expected": expected_answer,
                "candidates": list(unique_candidates.keys()),
                "correct_found": correct_found
            })
            
            print(f"结果: {'✓ 正确识别' if correct_found else '✗ 识别失败'}")
        
        # 统计结果
        correct_count = sum(1 for r in test_results if r["correct_found"])
        print(f"\n=== 测试总结 ===")
        print(f"测试数量: {len(test_results)}")
        print(f"正确识别: {correct_count}")
        print(f"准确率: {correct_count/len(test_results)*100:.1f}%")
        
        return test_results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='验证OCR准确性')
    parser.add_argument('json_path', help='answers.json文件路径')
    parser.add_argument('--count', type=int, default=10, help='测试数量')
    
    args = parser.parse_args()
    
    validator = OCRValidator()
    validator.test_ocr_on_known_answers(args.json_path, args.count)

if __name__ == "__main__":
    main()