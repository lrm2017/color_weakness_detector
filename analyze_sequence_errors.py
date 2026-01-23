#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析序号错误的OCR结果
"""

import json
import re
from pathlib import Path

def analyze_sequence_errors(json_path):
    """分析哪些答案是序号错误"""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== 序号错误分析 ===")
    print("检查答案是否与文件序号相同（这些都是错误的）")
    print()
    
    sequence_errors = []
    correct_answers = []
    
    for i, entry in enumerate(data, 1):
        filename = entry['filename']
        answer = entry['answer']
        
        # 从文件名提取序号
        file_number = re.search(r'(\d+)', filename)
        if file_number:
            file_num = int(file_number.group(1))
            
            # 检查答案是否与序号相同
            if answer.isdigit() and int(answer) == file_num:
                sequence_errors.append({
                    'index': i,
                    'filename': filename,
                    'answer': answer,
                    'file_number': file_num
                })
            else:
                correct_answers.append({
                    'index': i,
                    'filename': filename,
                    'answer': answer,
                    'file_number': file_num
                })
    
    print(f"序号错误 ({len(sequence_errors)}个):")
    for error in sequence_errors:
        print(f"  {error['index']:2d}. {error['filename']}: '{error['answer']}' (= 序号{error['file_number']})")
    
    print(f"\n正确答案 ({len(correct_answers)}个):")
    for correct in correct_answers:
        print(f"  {correct['index']:2d}. {correct['filename']}: '{correct['answer']}'")
    
    print(f"\n=== 统计 ===")
    print(f"总数: {len(data)}")
    print(f"序号错误: {len(sequence_errors)}")
    print(f"正确答案: {len(correct_answers)}")
    print(f"错误率: {len(sequence_errors)/len(data)*100:.1f}%")
    print(f"正确率: {len(correct_answers)/len(data)*100:.1f}%")
    
    return sequence_errors, correct_answers

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='分析序号错误')
    parser.add_argument('json_path', help='answers.json文件路径')
    
    args = parser.parse_args()
    
    analyze_sequence_errors(args.json_path)

if __name__ == "__main__":
    main()