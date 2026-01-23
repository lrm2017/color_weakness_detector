#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有图库中的占位符答案
"""

import json
import os
from pathlib import Path

def check_placeholder_answers():
    """检查所有答案文件中的占位符"""
    
    downloaded_images_dir = Path("downloaded_images")
    
    # 占位符模式
    placeholder_patterns = [
        "1查看色弱滤镜",
        "查看色弱滤镜", 
        "placeholder",
        "待识别",
        "未识别"
    ]
    
    results = {}
    
    # 遍历所有子目录
    for subdir in downloaded_images_dir.iterdir():
        if subdir.is_dir():
            answers_file = subdir / "answers.json"
            if answers_file.exists():
                try:
                    with open(answers_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    placeholder_count = 0
                    total_count = len(data)
                    placeholder_items = []
                    
                    for i, entry in enumerate(data):
                        answer = entry.get('answer', '')
                        
                        # 检查是否是占位符
                        is_placeholder = any(pattern in answer for pattern in placeholder_patterns)
                        
                        if is_placeholder:
                            placeholder_count += 1
                            placeholder_items.append({
                                'index': i + 1,
                                'filename': entry.get('filename', ''),
                                'answer': answer,
                                'original_url': entry.get('original_url', '')
                            })
                    
                    if placeholder_count > 0:
                        results[subdir.name] = {
                            'total': total_count,
                            'placeholder_count': placeholder_count,
                            'percentage': placeholder_count / total_count * 100,
                            'items': placeholder_items[:10]  # 只显示前10个
                        }
                        
                except Exception as e:
                    print(f"读取 {answers_file} 失败: {e}")
    
    # 输出结果
    print("=== 占位符答案检查结果 ===\n")
    
    if not results:
        print("没有发现占位符答案")
        return
    
    for dataset_name, info in results.items():
        print(f"📁 {dataset_name}")
        print(f"   总数: {info['total']}")
        print(f"   占位符: {info['placeholder_count']} ({info['percentage']:.1f}%)")
        print(f"   示例:")
        
        for item in info['items']:
            print(f"     {item['index']:2d}. {item['filename']}: '{item['answer']}'")
        
        if len(info['items']) == 10 and info['placeholder_count'] > 10:
            print(f"     ... 还有 {info['placeholder_count'] - 10} 个")
        
        print()
    
    return results

if __name__ == "__main__":
    check_placeholder_answers()