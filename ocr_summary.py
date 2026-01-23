#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR处理结果总结工具
"""

import json
from pathlib import Path

def summarize_ocr_results(json_path):
    """总结OCR处理结果"""
    json_path = Path(json_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        answers_data = json.load(f)
    
    print(f"=== {json_path.parent.name} OCR处理结果总结 ===")
    print(f"总图像数量: {len(answers_data)}")
    
    # 统计答案类型
    answer_types = {
        '动物': [],
        '物品': [],
        '数字': [],
        '字母': [],
        '中文词汇': [],
        '其他': []
    }
    
    # 分类答案
    animals = ['熊猫', '兔子', '老虎', '狼', '骆驼', '马', '牛', '羊', '金鱼', '蝴蝶', '蜻蜓', '鹅', '燕子']
    objects = ['手枪', '冲锋枪', '军舰', '卡车', '摩托车', '拖拉机', '剪刀', '壶', '高射炮']
    
    placeholder_count = 0
    
    for entry in answers_data:
        answer = entry['answer']
        filename = entry['filename']
        
        if answer == '1查看色弱滤镜':
            placeholder_count += 1
            continue
        
        if answer in animals:
            answer_types['动物'].append((filename, answer))
        elif answer in objects:
            answer_types['物品'].append((filename, answer))
        elif answer.isdigit():
            answer_types['数字'].append((filename, answer))
        elif answer.isalpha() and answer.isupper():
            answer_types['字母'].append((filename, answer))
        elif any('\u4e00' <= char <= '\u9fff' for char in answer):
            answer_types['中文词汇'].append((filename, answer))
        else:
            answer_types['其他'].append((filename, answer))
    
    # 显示统计结果
    print(f"已识别答案: {len(answers_data) - placeholder_count}")
    print(f"待处理答案: {placeholder_count}")
    print(f"识别完成率: {(len(answers_data) - placeholder_count) / len(answers_data) * 100:.1f}%")
    
    print("\n=== 答案分类统计 ===")
    for category, items in answer_types.items():
        if items:
            print(f"\n{category} ({len(items)}个):")
            for filename, answer in items:
                print(f"  {filename}: {answer}")
    
    if placeholder_count > 0:
        print(f"\n=== 待处理的图像 ({placeholder_count}个) ===")
        for entry in answers_data:
            if entry['answer'] == '1查看色弱滤镜':
                print(f"  {entry['filename']}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='OCR结果总结')
    parser.add_argument('json_path', help='answers.json文件路径')
    
    args = parser.parse_args()
    
    summarize_ocr_results(args.json_path)

if __name__ == "__main__":
    main()