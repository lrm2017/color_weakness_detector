#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新所有图库中的占位符答案
"""

import json
import os
import time
from pathlib import Path
from easyocr_tool import EasyOCRTool

def extract_answer_from_placeholder(placeholder_text):
    """从占位符中提取可能的答案信息"""
    if not placeholder_text:
        return ""
    
    # 移除"查看色弱滤镜"部分，保留前面的内容
    patterns_to_remove = [
        r'查看色弱滤镜$',
        r'1查看色弱滤镜$',
        r'placeholder$',
        r'待识别$',
        r'未识别$'
    ]
    
    cleaned = placeholder_text
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned).strip()
    
    # 如果清理后还有内容，可能是有用的答案信息
    if cleaned and cleaned != placeholder_text:
        return cleaned
    
    return ""

def is_placeholder_answer(answer):
    """判断是否是占位符答案"""
    if not answer:
        return False
    
    placeholder_patterns = [
        "查看色弱滤镜",
        "placeholder",
        "待识别",
        "未识别"
    ]
    
    return any(pattern in answer for pattern in placeholder_patterns)
def batch_update_answers():
    """批量更新所有答案文件中的占位符"""
    
    downloaded_images_dir = Path("downloaded_images")
    
    # 初始化OCR工具
    print("初始化OCR工具...")
    ocr_tool = EasyOCRTool()
    
    # 统计信息
    total_datasets = 0
    total_processed = 0
    total_updated = 0
    
    # 遍历所有子目录
    for subdir in downloaded_images_dir.iterdir():
        if subdir.is_dir():
            answers_file = subdir / "answers.json"
            if answers_file.exists():
                print(f"\n=== 处理 {subdir.name} ===")
                
                try:
                    with open(answers_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 找出需要更新的条目
                    placeholder_items = []
                    for i, entry in enumerate(data):
                        answer = entry.get('answer', '')
                        
                        # 检查是否是占位符
                        if is_placeholder_answer(answer):
                            # 尝试从占位符中提取答案信息
                            extracted_answer = extract_answer_from_placeholder(answer)
                            placeholder_items.append((i, entry, extracted_answer))
                    
                    if not placeholder_items:
                        print(f"  没有需要更新的占位符答案")
                        continue
                    
                    total_datasets += 1
                    print(f"  发现 {len(placeholder_items)} 个占位符答案")
                    
                    # 备份原文件
                    backup_path = answers_file.with_suffix('.json.backup_batch')
                    if not backup_path.exists():
                        import shutil
                        shutil.copy2(answers_file, backup_path)
                        print(f"  已备份: {backup_path.name}")
                    
                    updated_count = 0
                    
                    # 处理每个占位符条目
                    for idx, (i, entry, extracted_answer) in enumerate(placeholder_items):
                        filename = entry.get('filename', '')
                        original_url = entry.get('original_url', '')
                        current_answer = entry.get('answer', '')
                        
                        print(f"  处理 {idx+1}/{len(placeholder_items)}: {filename}")
                        
                        # 如果从占位符中提取到了答案，先尝试使用它
                        if extracted_answer and len(extracted_answer) > 1:
                            print(f"    从占位符提取到答案: '{extracted_answer}'")
                            data[i]['answer'] = extracted_answer
                            updated_count += 1
                            total_updated += 1
                            print(f"    ✓ 使用提取答案: '{current_answer}' → '{extracted_answer}'")
                            total_processed += 1
                            continue
                        
                        if not original_url:
                            print(f"    跳过: 没有原始URL")
                            total_processed += 1
                            continue
                        
                        # 处理图像
                        image_path = subdir / filename
                        original_image_path = subdir / "original_images" / filename
                        
                        # 使用原始图像路径（如果存在）
                        if original_image_path.exists():
                            test_path = str(original_image_path)
                        else:
                            test_path = str(image_path)
                        
                        try:
                            answer = ocr_tool.process_single_image(test_path, original_url, debug=False)
                            
                            if answer and answer != current_answer:
                                # 清理答案中的占位符文本
                                clean_answer = answer
                                placeholder_patterns = [
                                    "查看色弱滤镜",
                                    "placeholder",
                                    "待识别",
                                    "未识别"
                                ]
                                for pattern in placeholder_patterns:
                                    clean_answer = clean_answer.replace(pattern, '').strip()
                                
                                if clean_answer:
                                    data[i]['answer'] = clean_answer
                                    updated_count += 1
                                    total_updated += 1
                                    print(f"    ✓ OCR更新: '{current_answer}' → '{clean_answer}'")
                                else:
                                    print(f"    - 清理后答案为空")
                            elif answer == current_answer:
                                print(f"    - 答案未变: '{answer}'")
                            else:
                                print(f"    ✗ 未识别出答案")
                        except Exception as e:
                            print(f"    ✗ 处理失败: {e}")
                        
                        total_processed += 1
                        
                        # 添加小延迟避免过载
                        time.sleep(0.1)
                    
                    # 保存更新后的文件
                    if updated_count > 0:
                        with open(answers_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        print(f"  已保存 {updated_count} 个更新")
                    else:
                        print(f"  没有成功更新任何答案")
                        
                except Exception as e:
                    print(f"  读取 {answers_file} 失败: {e}")
    
    print(f"\n=== 批量更新完成 ===")
    print(f"处理数据集: {total_datasets}")
    print(f"处理条目: {total_processed}")
    print(f"成功更新: {total_updated}")
    print(f"成功率: {total_updated/total_processed*100:.1f}%" if total_processed > 0 else "0%")

def update_single_dataset(dataset_name):
    """更新单个数据集"""
    
    downloaded_images_dir = Path("downloaded_images")
    dataset_dir = downloaded_images_dir / dataset_name
    
    if not dataset_dir.exists():
        print(f"数据集 {dataset_name} 不存在")
        return
    
    answers_file = dataset_dir / "answers.json"
    if not answers_file.exists():
        print(f"答案文件 {answers_file} 不存在")
        return
    
    # 占位符模式
    placeholder_patterns = [
        "1查看色弱滤镜",
        "查看色弱滤镜", 
        "placeholder",
        "待识别",
        "未识别"
    ]
    
    print(f"=== 更新 {dataset_name} ===")
    
    # 初始化OCR工具
    print("初始化OCR工具...")
    ocr_tool = EasyOCRTool()
    
    try:
        with open(answers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 找出需要更新的条目
        placeholder_items = []
        for i, entry in enumerate(data):
            answer = entry.get('answer', '')
            
            # 检查是否是占位符
            is_placeholder = any(pattern in answer for pattern in placeholder_patterns)
            
            if is_placeholder:
                placeholder_items.append((i, entry))
        
        if not placeholder_items:
            print(f"没有需要更新的占位符答案")
            return
        
        print(f"发现 {len(placeholder_items)} 个占位符答案")
        
        # 备份原文件
        backup_path = answers_file.with_suffix('.json.backup_single')
        if not backup_path.exists():
            import shutil
            shutil.copy2(answers_file, backup_path)
            print(f"已备份: {backup_path.name}")
        
        updated_count = 0
        
        # 处理每个占位符条目
        for idx, (i, entry) in enumerate(placeholder_items):
            filename = entry.get('filename', '')
            original_url = entry.get('original_url', '')
            current_answer = entry.get('answer', '')
            
            print(f"\n处理 {idx+1}/{len(placeholder_items)}: {filename}")
            
            if not original_url:
                print(f"  跳过: 没有原始URL")
                continue
            
            # 处理图像
            image_path = dataset_dir / filename
            original_image_path = dataset_dir / "original_images" / filename
            
            # 使用原始图像路径（如果存在）
            if original_image_path.exists():
                test_path = str(original_image_path)
            else:
                test_path = str(image_path)
            
            try:
                answer = ocr_tool.process_single_image(test_path, original_url, debug=True)
                
                if answer and answer != current_answer:
                    # 清理答案中的占位符文本
                    clean_answer = answer
                    for pattern in placeholder_patterns:
                        clean_answer = clean_answer.replace(pattern, '').strip()
                    
                    if clean_answer:
                        data[i]['answer'] = clean_answer
                        updated_count += 1
                        print(f"  ✓ 更新: '{current_answer}' → '{clean_answer}'")
                    else:
                        print(f"  - 清理后答案为空")
                elif answer == current_answer:
                    print(f"  - 答案未变: '{answer}'")
                else:
                    print(f"  ✗ 未识别出答案")
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
        
        # 保存更新后的文件
        if updated_count > 0:
            with open(answers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n已保存 {updated_count} 个更新")
        else:
            print(f"\n没有成功更新任何答案")
            
    except Exception as e:
        print(f"读取 {answers_file} 失败: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='批量更新占位符答案')
    parser.add_argument('--dataset', help='指定单个数据集名称')
    parser.add_argument('--all', action='store_true', help='更新所有数据集')
    
    args = parser.parse_args()
    
    if args.dataset:
        update_single_dataset(args.dataset)
    elif args.all:
        batch_update_answers()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()