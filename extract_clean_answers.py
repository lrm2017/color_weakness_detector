#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从OCR结果中提取干净的答案
"""

import re
import json
from pathlib import Path

class AnswerExtractor:
    def __init__(self):
        # 常见的色弱检测答案模式
        self.answer_patterns = [
            # 动物
            r'(熊猫|兔子|老虎|狼|骆驼|马|牛|羊|金鱼|蝴蝶|蜻蜓|鹅|燕子)',
            # 物品
            r'(手枪|冲锋枪|军舰|卡车|摩托车|拖拉机|剪刀|壶)',
            # 几何图形
            r'(五角星|三角形|圆形|正方形|△|○|□)',
            # 数字（1-4位）
            r'(\d{1,4})',
            # 字母组合
            r'([A-Z]{2,6})',
            # 中文词汇
            r'(单色图|两颗|星星|红色|黄色|蓝色|绿色|紫色)',
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern) for pattern in self.answer_patterns]
    
    def extract_answer_from_text(self, text):
        """
        从OCR文本中提取答案
        """
        if not text:
            return ""
        
        # 查找所有可能的答案
        candidates = []
        
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            candidates.extend(matches)
        
        if not candidates:
            return ""
        
        # 选择最佳候选答案
        # 优先选择动物和物品名称
        priority_patterns = [
            r'(熊猫|兔子|老虎|狼|骆驼|马|牛|羊|金鱼|蝴蝶|蜻蜓|鹅|燕子)',
            r'(手枪|冲锋枪|军舰|卡车|摩托车|拖拉机|剪刀|壶)',
            r'(五角星|三角形|圆形|正方形)',
        ]
        
        for priority_pattern in priority_patterns:
            priority_regex = re.compile(priority_pattern)
            priority_matches = priority_regex.findall(text)
            if priority_matches:
                return priority_matches[0]
        
        # 如果没有优先答案，选择最长的候选答案
        return max(candidates, key=len) if candidates else ""
    
    def process_ocr_results(self, json_path):
        """
        处理OCR结果，提取干净的答案
        """
        # 从之前的OCR输出中手动提取答案
        manual_answers = {
            "009.jpg": "拖拉机",  # 从 '人和Ce4总本拖拉机' 提取
            "029.jpg": "骆驼",    # 从 '所贞Geeg8转3529骆驼' 提取
            "033.jpg": "老虎",    # 从 '本本1站内seee办需33老虎Eee' 提取
            "035.jpg": "冲锋枪",  # 从 'UGOeeBgeNeANDB全OO35冲锋枪1加人4Vi' 提取
            "037.jpg": "高射炮",  # 从 'YN人OO人上这人SB罗和一237高出炮' 提取
            "038.jpg": "洪水",    # 从 '9e6NT238洪半' 提取 (可能是洪水)
            "039.jpg": "卡车",    # 从 '人人0cGXR0人39卡车ER' 提取
            "040.jpg": "军舰",    # 从 '和者全作eeCC了和ee万鳃人40军舰Re' 提取
            "047.jpg": "手枪",    # 从 '这TANNSNE5e47手枪' 提取
            "048.jpg": "金鱼",    # 从 '全SanAN人Ga48金鱼' 提取
            "049.jpg": "摩托车",  # 从 'ac有Ge-SG人ee四要全思5亿9NT849摩托车的' 提取
            "050.jpg": "狼",      # 从 '和NeEN85人下50狼二ER' 提取
            "053.jpg": "五角星",  # 从 'Gaoees1驴友汉罗人和全3六53五角星/蝴蝶人' 提取
            "055.jpg": "骆驼",    # 从 '多中夫人AAAjnA六992O和5Go9Gocos9剖vtesAe0o00055骆驼/马AC广-' 提取
        }
        
        # 读取答案文件
        json_path = Path(json_path)
        with open(json_path, 'r', encoding='utf-8') as f:
            answers_data = json.load(f)
        
        # 更新答案
        updated_count = 0
        for entry in answers_data:
            filename = entry['filename']
            current_answer = entry.get('answer', '')
            
            # 如果当前答案是占位符，且我们有手动提取的答案
            if current_answer == '1查看色弱滤镜' and filename in manual_answers:
                entry['answer'] = manual_answers[filename]
                updated_count += 1
                print(f"更新 {filename}: {manual_answers[filename]}")
        
        # 保存更新后的文件
        if updated_count > 0:
            backup_path = json_path.with_suffix('.json.backup2')
            if not backup_path.exists():
                json_path.rename(backup_path)
                print(f"原文件已备份: {backup_path}")
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(answers_data, f, ensure_ascii=False, indent=2)
            
            print(f"成功更新 {updated_count} 个答案")
        else:
            print("没有需要更新的答案")

def main():
    extractor = AnswerExtractor()
    
    # 处理李春慧新编的答案
    json_path = "downloaded_images/李春慧新编/answers.json"
    extractor.process_ocr_results(json_path)

if __name__ == "__main__":
    main()