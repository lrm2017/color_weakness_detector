#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证OCR结果准确性工具
对比已知正确答案与OCR识别结果
"""

import json
from pathlib import Path

def compare_ocr_results(current_file, backup_file, known_correct_count=23):
    """
    对比OCR结果与已知正确答案
    
    Args:
        current_file: 当前答案文件（包含OCR结果）
        backup_file: 备份文件（包含正确答案）
        known_correct_count: 已知正确答案的数量
    """
    
    # 读取文件
    with open(current_file, 'r', encoding='utf-8') as f:
        current_data = json.load(f)
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    print(f"=== OCR结果验证 ===")
    print(f"对比前 {known_correct_count} 个已知正确答案")
    print()
    
    correct_count = 0
    incorrect_count = 0
    
    print("序号 | 文件名    | 正确答案    | OCR结果     | 状态")
    print("-" * 60)
    
    for i in range(min(known_correct_count, len(current_data), len(backup_data))):
        current_entry = current_data[i]
        backup_entry = backup_data[i]
        
        filename = current_entry['filename']
        correct_answer = backup_entry['answer']
        ocr_result = current_entry['answer']
        
        # 检查是否匹配
        is_correct = correct_answer == ocr_result
        status = "✓" if is_correct else "✗"
        
        if is_correct:
            correct_count += 1
        else:
            incorrect_count += 1
        
        print(f"{i+1:2d}   | {filename:9s} | {correct_answer:10s} | {ocr_result:10s} | {status}")
    
    print("-" * 60)
    print(f"总计: {known_correct_count} 个")
    print(f"正确: {correct_count} 个")
    print(f"错误: {incorrect_count} 个")
    print(f"准确率: {correct_count/known_correct_count*100:.1f}%")
    
    # 显示错误详情
    if incorrect_count > 0:
        print(f"\n=== 错误详情 ===")
        for i in range(min(known_correct_count, len(current_data), len(backup_data))):
            current_entry = current_data[i]
            backup_entry = backup_data[i]
            
            filename = current_entry['filename']
            correct_answer = backup_entry['answer']
            ocr_result = current_entry['answer']
            
            if correct_answer != ocr_result:
                print(f"{filename}: 期望 '{correct_answer}' -> 实际 '{ocr_result}'")
    
    # 分析OCR从第24个开始的结果
    print(f"\n=== OCR生成的答案 (第{known_correct_count+1}个开始) ===")
    ocr_generated = current_data[known_correct_count:]
    
    # 统计OCR生成答案的类型
    answer_types = {
        '数字': [],
        '字母': [],
        '中文': [],
        '动物': [],
        '物品': [],
        '其他': []
    }
    
    animals = ['熊猫', '兔子', '老虎', '狼', '骆驼', '马', '牛', '羊', '金鱼', '蝴蝶', '蜻蜓', '鹅', '燕子', '袋鼠', '大象']
    objects = ['手枪', '冲锋枪', '军舰', '卡车', '摩托车', '拖拉机', '剪刀', '壶', '高射炮', '飞机']
    
    for i, entry in enumerate(ocr_generated, start=known_correct_count+1):
        answer = entry['answer']
        filename = entry['filename']
        
        if answer.isdigit():
            answer_types['数字'].append(f"{i:2d}. {filename}: {answer}")
        elif answer.isalpha() and answer.isupper():
            answer_types['字母'].append(f"{i:2d}. {filename}: {answer}")
        elif answer in animals:
            answer_types['动物'].append(f"{i:2d}. {filename}: {answer}")
        elif answer in objects:
            answer_types['物品'].append(f"{i:2d}. {filename}: {answer}")
        elif any('\u4e00' <= char <= '\u9fff' for char in answer):
            answer_types['中文'].append(f"{i:2d}. {filename}: {answer}")
        else:
            answer_types['其他'].append(f"{i:2d}. {filename}: {answer}")
    
    for category, items in answer_types.items():
        if items:
            print(f"\n{category} ({len(items)}个):")
            for item in items:
                print(f"  {item}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='验证OCR结果准确性')
    parser.add_argument('current_file', help='当前答案文件路径')
    parser.add_argument('--backup', help='备份文件路径', default=None)
    parser.add_argument('--known-count', type=int, default=23, help='已知正确答案数量')
    
    args = parser.parse_args()
    
    current_file = Path(args.current_file)
    
    # 自动查找备份文件
    if args.backup:
        backup_file = Path(args.backup)
    else:
        # 尝试找到备份文件
        possible_backups = [
            current_file.with_suffix('.json.backup2'),
            current_file.with_suffix('.json.backup'),
            current_file.with_suffix('.json.backup_easy'),
        ]
        
        backup_file = None
        for backup in possible_backups:
            if backup.exists():
                backup_file = backup
                break
        
        if not backup_file:
            print("未找到备份文件，请使用 --backup 参数指定")
            return
    
    print(f"当前文件: {current_file}")
    print(f"备份文件: {backup_file}")
    print()
    
    compare_ocr_results(current_file, backup_file, args.known_count)

if __name__ == "__main__":
    main()