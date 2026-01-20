#!/usr/bin/env python3
"""
多通道色觉检测演示脚本
展示所有新增功能的使用方法
"""

import os
import sys
from pathlib import Path
import subprocess


def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"演示: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"执行错误: {e}")
        return False


def main():
    print("多通道色觉检测系统演示")
    print("="*60)
    
    # 检查测试图像
    test_image = "downloaded_images/俞自萍第五版/001.jpg"
    test_dir = "downloaded_images/俞自萍第五版"
    
    if not Path(test_image).exists():
        print(f"错误: 测试图像不存在: {test_image}")
        print("请确保有可用的测试图像")
        return 1
    
    print(f"使用测试图像: {test_image}")
    print(f"测试目录: {test_dir}")
    
    # 1. 原始色觉检测
    run_command(
        f"python color_detector.py '{test_image}' --show",
        "原始暖冷色检测"
    )
    
    # 2. 多通道检测 - 红绿通道
    run_command(
        f"python multi_channel_color_detector.py '{test_image}' --channel red_green",
        "红绿通道专项测试"
    )
    
    # 3. 多通道检测 - 蓝黄通道
    run_command(
        f"python multi_channel_color_detector.py '{test_image}' --channel blue_yellow",
        "蓝黄通道专项测试"
    )
    
    # 4. 综合多通道测试
    run_command(
        f"python multi_channel_color_detector.py '{test_image}' --channel all --report",
        "全通道综合测试（含报告生成）"
    )
    
    # 5. 简化快速测试
    run_command(
        f"python simple_color_test.py '{test_image}'",
        "简化快速色觉分析"
    )
    
    # 6. 可视化分析
    run_command(
        f"python visualize_color_test.py '{test_image}'",
        "可视化分析（生成图表）"
    )
    
    # 7. 批量测试演示
    run_command(
        f"python simple_color_test.py '{test_dir}' --batch --max-files 3",
        "批量测试演示（3个文件）"
    )
    
    print(f"\n{'='*60}")
    print("演示完成！")
    print("="*60)
    
    # 显示生成的文件
    print("\n生成的文件:")
    output_dir = Path(test_dir)
    
    extensions = ['.jpg', '.png', '.json']
    for ext in extensions:
        files = list(output_dir.glob(f"*{ext}"))
        if files:
            print(f"\n{ext.upper()} 文件:")
            for file in sorted(files):
                if any(keyword in file.name for keyword in ['multichannel', 'visualization', 'chart', 'report']):
                    print(f"  - {file.name}")
    
    print(f"\n查看详细说明: README_multichannel.md")
    print(f"测试报告示例: {test_dir}/001_multichannel_report.json")
    
    return 0


if __name__ == "__main__":
    exit(main())