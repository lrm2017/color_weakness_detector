#!/usr/bin/env python3
"""
批量色觉测试脚本
"""

import os
import json
from pathlib import Path
from multi_channel_color_detector import MultiChannelColorDetector
import argparse


def batch_test(input_dir, output_dir=None, max_files=10):
    """
    批量测试指定目录下的图像
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"错误：目录不存在: {input_dir}")
        return
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
    else:
        output_path = input_path / "test_results"
        output_path.mkdir(exist_ok=True)
    
    detector = MultiChannelColorDetector()
    
    # 查找图像文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))
    
    image_files = image_files[:max_files]  # 限制测试数量
    
    print(f"找到 {len(image_files)} 个图像文件，开始批量测试...")
    
    results_summary = []
    
    for i, image_file in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] 测试: {image_file.name}")
        
        try:
            # 执行多通道测试
            output_base = output_path / image_file.stem
            
            # 红绿通道测试
            _, rg_data = detector.test_red_green_channel(image_file, output_base, min_area=50)
            
            # 蓝黄通道测试  
            _, by_data = detector.test_blue_yellow_channel(image_file, output_base, min_area=50)
            
            # 综合测试
            _, comp_data = detector.comprehensive_test(image_file, output_base, min_area=50)
            
            # 生成报告
            report = detector.generate_report(image_file, rg_data, by_data, comp_data)
            
            # 保存单个报告
            report_file = output_path / f"{image_file.stem}_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # 添加到汇总
            summary_item = {
                'file': image_file.name,
                'diagnosis': report['diagnosis']['type'],
                'confidence': report['diagnosis']['confidence'],
                'red_green_ratio': rg_data['red_ratio'],
                'blue_yellow_ratio': by_data['blue_ratio'],
                'notes': report['diagnosis']['notes']
            }
            results_summary.append(summary_item)
            
            print(f"  诊断: {report['diagnosis']['type']} (置信度: {report['diagnosis']['confidence']:.2f})")
            
        except Exception as e:
            print(f"  错误: {e}")
            continue
    
    # 保存汇总报告
    summary_file = output_path / "batch_test_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\n批量测试完成！结果保存在: {output_path}")
    print(f"汇总报告: {summary_file}")
    
    # 统计结果
    diagnosis_counts = {}
    for item in results_summary:
        diagnosis = item['diagnosis']
        diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
    
    print("\n诊断统计:")
    for diagnosis, count in diagnosis_counts.items():
        print(f"  {diagnosis}: {count} 个")


def main():
    parser = argparse.ArgumentParser(description="批量色觉测试")
    parser.add_argument("input_dir", help="输入图像目录")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--max-files", type=int, default=10, help="最大测试文件数")
    
    args = parser.parse_args()
    
    batch_test(args.input_dir, args.output, args.max_files)


if __name__ == "__main__":
    main()