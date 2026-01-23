#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复序号错误的OCR结果
"""

import json
import re
from pathlib import Path
from easyocr_tool import EasyOCRTool

def fix_sequence_errors(json_path):
    """修复序号错误"""
    
    json_path = Path(json_path)
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== 修复序号错误 ===")
    
    # 找出序号错误的条目
    sequence_errors = []
    for i, entry in enumerate(data):
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
                    'entry': entry
                })
    
    print(f"发现 {len(sequence_errors)} 个序号错误")
    
    if not sequence_errors:
        print("没有需要修复的序号错误")
        return
    
    # 初始化OCR工具
    ocr_tool = EasyOCRTool()
    
    fixed_count = 0
    
    for error_info in sequence_errors:
        index = error_info['index']
        entry = error_info['entry']
        filename = entry['filename']
        original_url = entry.get('original_url', '')
        current_answer = entry['answer']
        
        print(f"\n修复 {index+1}. {filename} (当前答案: '{current_answer}')")
        
        if not original_url:
            print("  没有原始URL，跳过")
            continue
        
        # 处理图像
        image_path = json_path.parent / filename
        original_image_path = json_path.parent / "original_images" / filename
        
        # 使用原始图像路径（如果存在）
        if original_image_path.exists():
            test_path = str(original_image_path)
        else:
            test_path = str(image_path)
        
        try:
            answer = ocr_tool.process_single_image(test_path, original_url, debug=True)
            
            if answer and answer != current_answer:
                entry['answer'] = answer
                fixed_count += 1
                print(f"  ✓ 修复: '{current_answer}' → '{answer}'")
            elif answer == current_answer:
                print(f"  - 答案未变: '{answer}'")
            else:
                print(f"  ✗ 未识别出新答案")
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
    
    print(f"\n=== 修复完成 ===")
    print(f"处理: {len(sequence_errors)}")
    print(f"修复: {fixed_count}")
    print(f"成功率: {fixed_count/len(sequence_errors)*100:.1f}%" if sequence_errors else "0%")
    
    # 保存结果
    if fixed_count > 0:
        backup_path = json_path.with_suffix('.json.backup_before_fix')
        if not backup_path.exists():
            import shutil
            shutil.copy2(json_path, backup_path)
            print(f"原文件已备份: {backup_path.name}")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"已保存修复结果")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='修复序号错误')
    parser.add_argument('json_path', help='answers.json文件路径')
    
    args = parser.parse_args()
    
    fix_sequence_errors(args.json_path)

if __name__ == "__main__":
    main()