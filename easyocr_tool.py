#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于EasyOCR的答案提取工具
"""

import json
import cv2
import numpy as np
from pathlib import Path
import re
import requests
import time
import argparse
import easyocr

class EasyOCRTool:
    def __init__(self):
        # 初始化EasyOCR
        print("初始化EasyOCR...")
        self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)  # 使用CPU模式
        print("EasyOCR初始化完成")
        
        # 网络会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 已知答案词典
        self.known_answers = {
            # 动物类
            '熊猫', '兔子', '老虎', '狼', '骆驼', '马', '牛', '羊', '金鱼', '蝴蝶', '蜻蜓', '鹅', '燕子',
            '大熊猫', '鸡', '鸭', '猪', '狗', '猫', '鸟', '鱼', '虾', '蟹',
            
            # 物品类
            '手枪', '冲锋枪', '军舰', '卡车', '摩托车', '拖拉机', '剪刀', '壶', '高射炮',
            '飞机', '坦克', '大炮', '轮船', '火车', '汽车', '自行车', '船', '枪',
            
            # 几何图形和符号
            '五角星', '三角形', '圆形', '正方形', '△', '○', '□', '两颗星星', '星星',
            
            # 特殊描述
            '单色图-红色', '单色图-黄色', '单色图-蓝色', '单色图-绿色', '单色图-紫色',
            '单色图', '两颗',
            
            # 其他中文词汇
            '洪水', '人', '和', '了', '的', '在', '是', '有', '不', '这', '那'
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
            print(f"  下载失败: {e}")
            return False
    
    def preprocess_image_for_ocr(self, image_path):
        """
        为OCR预处理图像，提取可能的答案区域
        """
        img = cv2.imread(image_path)
        if img is None:
            return []
        
        height, width = img.shape[:2]
        regions = []
        
        # 定义多个可能的答案区域，包括左侧和右侧
        answer_regions = [
            # 左下角区域
            {"name": "left_bottom", "coords": (0, int(height*0.75), int(width*0.3), height)},
            {"name": "left_bottom_large", "coords": (0, int(height*0.7), int(width*0.4), height)},
            {"name": "left_bottom_small", "coords": (0, int(height*0.8), int(width*0.25), height)},
            
            # 右下角区域 - 增强右侧扫描
            {"name": "right_bottom", "coords": (int(width*0.7), int(height*0.75), width, height)},
            {"name": "right_bottom_large", "coords": (int(width*0.6), int(height*0.7), width, height)},
            {"name": "right_bottom_small", "coords": (int(width*0.75), int(height*0.8), width, height)},
            {"name": "right_bottom_extended", "coords": (int(width*0.5), int(height*0.75), width, height)},
            
            # 底部中央
            {"name": "center_bottom", "coords": (int(width*0.3), int(height*0.8), int(width*0.7), height)},
            
            # 整个底部
            {"name": "full_bottom", "coords": (0, int(height*0.85), width, height)},
            {"name": "full_bottom_large", "coords": (0, int(height*0.8), width, height)},
            
            # 左侧区域
            {"name": "left_side", "coords": (0, int(height*0.5), int(width*0.3), height)},
            {"name": "left_side_large", "coords": (0, int(height*0.4), int(width*0.4), height)},
            
            # 右侧区域 - 增强右侧扫描
            {"name": "right_side", "coords": (int(width*0.7), int(height*0.5), width, height)},
            {"name": "right_side_large", "coords": (int(width*0.6), int(height*0.4), width, height)},
            {"name": "right_side_extended", "coords": (int(width*0.5), int(height*0.3), width, height)},
            
            # 四个角落
            {"name": "top_left", "coords": (0, 0, int(width*0.3), int(height*0.3))},
            {"name": "top_right", "coords": (int(width*0.7), 0, width, int(height*0.3))},
            {"name": "bottom_left", "coords": (0, int(height*0.7), int(width*0.3), height)},
            {"name": "bottom_right", "coords": (int(width*0.7), int(height*0.7), width, height)},
        ]
        
        for region in answer_regions:
            x1, y1, x2, y2 = region["coords"]
            roi = img[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
            
            regions.append({
                "name": region["name"],
                "image": roi,
                "coords": (x1, y1, x2, y2)
            })
        
        return regions
    
    def extract_text_with_easyocr(self, image_regions, debug=False):
        """
        使用EasyOCR提取文字
        """
        all_results = []
        
        for region_data in image_regions:
            region_name = region_data["name"]
            roi = region_data["image"]
            
            try:
                # 使用EasyOCR识别，降低置信度阈值以捕获更多可能的文字
                results = self.reader.readtext(roi)
                
                for (bbox, text, confidence) in results:
                    if text and text.strip() and confidence > 0.05:  # 降低置信度阈值
                        all_results.append({
                            "text": text.strip(),
                            "confidence": confidence,
                            "region": region_name,
                            "bbox": bbox
                        })
                        
                        if debug:
                            print(f"    {region_name}: '{text.strip()}' (置信度: {confidence:.2f})")
                
            except Exception as e:
                if debug:
                    print(f"    {region_name} OCR失败: {e}")
                continue
        
        return all_results
    
    def extract_answer_candidates(self, ocr_results):
        """
        从OCR结果中提取答案候选
        """
        candidates = {}
        
        for result in ocr_results:
            text = result["text"]
            confidence = result["confidence"]
            region = result["region"]
            
            # 清理文本
            cleaned_text = self.clean_text(text)
            if not cleaned_text:
                continue
            
            # 尝试从原始文本中提取序号后的内容
            # 匹配模式: "数字 + 空格/标点 + 内容"
            content_patterns = [
                r'^\d+[\.、\s:：]\s*(.+)',  # "12. 内容" 或 "12 内容"
                r'^\d+\s+(.+)',             # "12 内容"
                r'^第?\d+题?\s*(.+)',       # "第12题 内容"
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, text.strip())
                if match:
                    content = match.group(1).strip()
                    if content and len(content) > 1:  # 确保提取到有意义的内容
                        score = confidence * 4  # 从序号后提取的内容给予最高权重
                        if content not in candidates:
                            candidates[content] = {"score": 0, "count": 0, "sources": []}
                        candidates[content]["score"] += score
                        candidates[content]["count"] += 1
                        candidates[content]["sources"].append(f"{region}_content({confidence:.2f})")
            
            # 检查已知答案
            for known_answer in self.known_answers:
                if known_answer in text:
                    score = confidence * 3  # 已知答案加权更高
                    if known_answer not in candidates:
                        candidates[known_answer] = {"score": 0, "count": 0, "sources": []}
                    candidates[known_answer]["score"] += score
                    candidates[known_answer]["count"] += 1
                    candidates[known_answer]["sources"].append(f"{region}({confidence:.2f})")
            
            # 提取数字（1-4位）
            numbers = re.findall(r'\b\d{1,4}\b', text)
            for num in numbers:
                if len(num) >= 2:  # 至少2位数
                    score = confidence * 1.5  # 数字适度加权
                    if num not in candidates:
                        candidates[num] = {"score": 0, "count": 0, "sources": []}
                    candidates[num]["score"] += score
                    candidates[num]["count"] += 1
                    candidates[num]["sources"].append(f"{region}({confidence:.2f})")
            
            # 提取大写字母组合（2-6位）
            letters = re.findall(r'\b[A-Z]{2,6}\b', text)
            for letter in letters:
                score = confidence * 1.5
                if letter not in candidates:
                    candidates[letter] = {"score": 0, "count": 0, "sources": []}
                candidates[letter]["score"] += score
                candidates[letter]["count"] += 1
                candidates[letter]["sources"].append(f"{region}({confidence:.2f})")
            
            # 提取中文词汇（1-4字）
            chinese_words = re.findall(r'[\u4e00-\u9fff]{1,4}', text)
            for word in chinese_words:
                if len(word) >= 1:
                    score = confidence * 2  # 中文词汇加权
                    if word not in candidates:
                        candidates[word] = {"score": 0, "count": 0, "sources": []}
                    candidates[word]["score"] += score
                    candidates[word]["count"] += 1
                    candidates[word]["sources"].append(f"{region}({confidence:.2f})")
            
            # 提取符号组合和单个字符
            symbols = re.findall(r'[△○□/\-XxOo]{1,5}', text)
            for symbol in symbols:
                score = confidence * 1.5  # 符号适度加权
                if symbol not in candidates:
                    candidates[symbol] = {"score": 0, "count": 0, "sources": []}
                candidates[symbol]["score"] += score
                candidates[symbol]["count"] += 1
                candidates[symbol]["sources"].append(f"{region}({confidence:.2f})")
            
            # 提取单个英文字母（可能是答案）
            single_letters = re.findall(r'\b[A-Za-z]\b', text)
            for letter in single_letters:
                score = confidence * 1.2
                if letter not in candidates:
                    candidates[letter] = {"score": 0, "count": 0, "sources": []}
                candidates[letter]["score"] += score
                candidates[letter]["count"] += 1
                candidates[letter]["sources"].append(f"{region}({confidence:.2f})")
        
        return candidates
    
    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        
        # 去除换行和多余空格
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
        
        return text.strip()
    
    def is_likely_sequence_number(self, candidate, filename):
        """判断候选答案是否可能是序号"""
        if not candidate.isdigit():
            return False
        
        # 提取文件名中的数字
        file_number = re.search(r'(\d+)', filename)
        if file_number:
            file_num = int(file_number.group(1))
            candidate_num = int(candidate)
            
            # 如果候选答案与文件序号相同，很可能是序号
            if candidate_num == file_num:
                return True
            
            # 如果是1位数字且在1-9范围内，可能是序号
            if len(candidate) == 1 and 1 <= candidate_num <= 9:
                return True
                
            # 如果是2位数字且与文件序号相差很大，可能不是序号
            if len(candidate) == 2:
                # 如果与文件序号相差超过20，可能是答案而不是序号
                if abs(candidate_num - file_num) > 20:
                    return False
                # 如果在合理的序号范围内（1-100），可能是序号
                if 1 <= candidate_num <= 100:
                    return True
        
        return False
    
    def select_best_answer(self, candidates, filename="", debug=False):
        """选择最佳答案"""
        if not candidates:
            return ""
        
        # 按综合得分排序（得分 * 出现次数）
        scored_candidates = []
        for candidate, data in candidates.items():
            final_score = data["score"] * data["count"]
            scored_candidates.append((candidate, final_score, data))
        
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        if debug:
            print("  候选答案排序:")
            for candidate, score, data in scored_candidates[:8]:
                avg_conf = data["score"]/data["count"]
                is_seq = self.is_likely_sequence_number(candidate, filename)
                print(f"    '{candidate}': 得分={score:.2f} (出现{data['count']}次, 平均置信度={avg_conf:.2f}, 序号={is_seq})")
        
        # 分离序号候选和内容候选
        content_candidates = []
        sequence_candidates = []
        
        for candidate, score, data in scored_candidates:
            if self.is_likely_sequence_number(candidate, filename):
                sequence_candidates.append((candidate, score, data))
            else:
                content_candidates.append((candidate, score, data))
        
        if debug:
            print(f"  内容候选: {len(content_candidates)}, 序号候选: {len(sequence_candidates)}")
        
        # 优先从内容候选中选择
        if content_candidates:
            # 优先选择已知答案
            for candidate, score, data in content_candidates:
                if candidate in self.known_answers and data["score"]/data["count"] > 0.4:
                    if debug:
                        print(f"  选择已知答案: '{candidate}'")
                    return candidate
            
            # 选择得分最高且置信度合理的内容
            for candidate, score, data in content_candidates:
                avg_conf = data["score"]/data["count"]
                if avg_conf > 0.3 and len(candidate) >= 1:
                    if debug:
                        print(f"  选择内容候选: '{candidate}' (置信度={avg_conf:.2f})")
                    return candidate
            
            # 如果都不满足条件，选择最高得分的内容候选
            if content_candidates:
                candidate = content_candidates[0][0]
                if debug:
                    print(f"  选择最高得分内容: '{candidate}'")
                return candidate
        
        # 如果没有内容候选，才考虑序号候选（但要更严格）
        if sequence_candidates:
            for candidate, score, data in sequence_candidates:
                avg_conf = data["score"]/data["count"]
                # 对序号候选要求更高的置信度
                if avg_conf > 0.7 and len(candidate) >= 3:  # 至少3位数字且高置信度
                    if debug:
                        print(f"  选择高置信度序号: '{candidate}' (置信度={avg_conf:.2f})")
                    return candidate
        
        if debug:
            print("  未找到合适答案")
        return ""
    
    def process_single_image(self, image_path, original_url=None, debug=False):
        """处理单个图像"""
        if debug:
            print(f"  处理图像: {Path(image_path).name}")
        
        # 下载原始图像
        if original_url:
            original_dir = Path(image_path).parent / "original_images"
            original_dir.mkdir(exist_ok=True)
            original_path = original_dir / Path(image_path).name
            
            if not original_path.exists():
                if debug:
                    print(f"  下载原始图像...")
                if not self.download_image(original_url, original_path):
                    return ""
                time.sleep(0.5)
            
            image_path = str(original_path)
        
        # 预处理图像
        regions = self.preprocess_image_for_ocr(image_path)
        if not regions:
            if debug:
                print("  图像预处理失败")
            return ""
        
        # OCR识别
        ocr_results = self.extract_text_with_easyocr(regions, debug)
        if not ocr_results:
            if debug:
                print("  未识别到文字")
            return ""
        
        # 提取候选答案
        candidates = self.extract_answer_candidates(ocr_results)
        if not candidates:
            if debug:
                print("  未找到有效候选答案")
            return ""
        
        # 选择最佳答案
        filename = Path(image_path).name
        answer = self.select_best_answer(candidates, filename, debug)
        
        if debug and answer:
            print(f"  最终答案: '{answer}'")
        
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
            backup_path = json_path.with_suffix('.json.backup_easy')
            if not backup_path.exists():
                json_path.rename(backup_path)
                print(f"  原文件已备份: {backup_path.name}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, ensure_ascii=False, indent=2)
            
            print(f"  已保存更新")
    
    def test_single_image(self, image_path, original_url=None):
        """测试单个图像"""
        print(f"=== 测试图像: {image_path} ===")
        
        answer = self.process_single_image(image_path, original_url, debug=True)
        
        print(f"\n最终结果: '{answer}'")
        return answer

def main():
    parser = argparse.ArgumentParser(description='EasyOCR答案提取工具')
    parser.add_argument('json_path', nargs='?', help='answers.json文件路径')
    parser.add_argument('--no-update', action='store_true', help='不更新文件')
    parser.add_argument('--debug', action='store_true', help='显示调试信息')
    parser.add_argument('--test', help='测试单个图像文件')
    
    args = parser.parse_args()
    
    tool = EasyOCRTool()
    
    if args.test:
        # 测试单个图像
        tool.test_single_image(args.test)
    else:
        if not args.json_path:
            parser.error("json_path is required when not using --test")
        # 处理整个答案文件
        tool.process_answers_file(args.json_path, update_file=not args.no_update, debug=args.debug)

if __name__ == "__main__":
    main()