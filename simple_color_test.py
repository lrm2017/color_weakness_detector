#!/usr/bin/env python3
"""
简化的多通道色觉测试
"""

import cv2
import numpy as np
from pathlib import Path
import argparse
from image_utils import imread_unicode


def analyze_color_channels(image_path):
    """
    分析图像的颜色通道分布
    """
    # 读取图像
    image = imread_unicode(str(image_path))
    if image is None:
        return None
    
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 过滤低饱和度像素
    mask_colorful = cv2.inRange(hsv, np.array([0, 20, 40]), np.array([180, 255, 255]))
    total_colorful = np.sum(mask_colorful > 0)
    
    if total_colorful == 0:
        return None
    
    # 定义颜色范围
    color_ranges = {
        'red': [(0, 10), (156, 180)],
        'orange': [(10, 25)],
        'yellow': [(25, 35)],
        'green': [(35, 85)],
        'cyan': [(85, 105)],
        'blue': [(105, 130)],
        'purple': [(130, 156)]
    }
    
    # 统计各颜色像素
    color_stats = {}
    for color_name, ranges in color_ranges.items():
        color_mask = np.zeros_like(hsv[:, :, 0])
        for h_range in ranges:
            lower = np.array([h_range[0], 25, 40])
            upper = np.array([h_range[1], 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            color_mask = cv2.bitwise_or(color_mask, mask)
        
        color_pixels = np.sum(cv2.bitwise_and(color_mask, mask_colorful) > 0)
        color_stats[color_name] = {
            'pixels': color_pixels,
            'percentage': (color_pixels / total_colorful) * 100
        }
    
    # 计算通道比例
    red_pixels = color_stats['red']['pixels'] + color_stats['orange']['pixels']
    green_pixels = color_stats['green']['pixels']
    blue_pixels = color_stats['blue']['pixels'] + color_stats['cyan']['pixels'] + color_stats['purple']['pixels']
    yellow_pixels = color_stats['yellow']['pixels']
    
    rg_total = red_pixels + green_pixels
    by_total = blue_pixels + yellow_pixels
    
    results = {
        'file': image_path.name,
        'total_colorful_pixels': total_colorful,
        'red_green_channel': {
            'red_pixels': red_pixels,
            'green_pixels': green_pixels,
            'red_ratio': red_pixels / rg_total if rg_total > 0 else 0,
            'green_ratio': green_pixels / rg_total if rg_total > 0 else 0
        },
        'blue_yellow_channel': {
            'blue_pixels': blue_pixels,
            'yellow_pixels': yellow_pixels,
            'blue_ratio': blue_pixels / by_total if by_total > 0 else 0,
            'yellow_ratio': yellow_pixels / by_total if by_total > 0 else 0
        },
        'color_distribution': color_stats
    }
    
    # 简单诊断
    diagnosis = "normal"
    notes = []
    
    if rg_total > 0:
        red_ratio = red_pixels / rg_total
        if red_ratio < 0.2:
            diagnosis = "possible_protanomaly"
            notes.append("红色识别可能异常")
        elif red_ratio > 0.8:
            diagnosis = "possible_deuteranomaly"
            notes.append("绿色识别可能异常")
    
    if by_total > 0:
        blue_ratio = blue_pixels / by_total
        if blue_ratio < 0.3:
            diagnosis = "possible_tritanomaly"
            notes.append("蓝色识别可能异常")
    
    results['diagnosis'] = diagnosis
    results['notes'] = notes
    
    return results


def test_single_image(image_path):
    """
    测试单个图像
    """
    print(f"\n测试图像: {image_path}")
    
    results = analyze_color_channels(Path(image_path))
    
    if results is None:
        print("  无法分析图像或未检测到彩色区域")
        return
    
    print(f"  总彩色像素: {results['total_colorful_pixels']}")
    
    # 红绿通道
    rg = results['red_green_channel']
    print(f"  红绿通道 - 红色: {rg['red_ratio']:.1%}, 绿色: {rg['green_ratio']:.1%}")
    
    # 蓝黄通道
    by = results['blue_yellow_channel']
    print(f"  蓝黄通道 - 蓝色: {by['blue_ratio']:.1%}, 黄色: {by['yellow_ratio']:.1%}")
    
    # 颜色分布
    print("  颜色分布:")
    for color, stats in results['color_distribution'].items():
        if stats['percentage'] > 1.0:
            print(f"    {color}: {stats['percentage']:.1f}%")
    
    # 诊断
    print(f"  诊断: {results['diagnosis']}")
    for note in results['notes']:
        print(f"    备注: {note}")


def batch_test_simple(input_dir, max_files=10):
    """
    简化的批量测试
    """
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"错误：目录不存在: {input_dir}")
        return
    
    # 查找图像文件
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(input_path.glob(f"*{ext}"))
        image_files.extend(input_path.glob(f"*{ext.upper()}"))
    
    image_files = image_files[:max_files]
    
    print(f"找到 {len(image_files)} 个图像文件")
    
    diagnosis_counts = {}
    
    for image_file in image_files:
        results = analyze_color_channels(image_file)
        if results:
            test_single_image(image_file)
            diagnosis = results['diagnosis']
            diagnosis_counts[diagnosis] = diagnosis_counts.get(diagnosis, 0) + 1
    
    print(f"\n=== 批量测试汇总 ===")
    print("诊断统计:")
    for diagnosis, count in diagnosis_counts.items():
        print(f"  {diagnosis}: {count} 个")


def main():
    parser = argparse.ArgumentParser(description="简化多通道色觉测试")
    parser.add_argument("input", help="输入图像文件或目录")
    parser.add_argument("--batch", action="store_true", help="批量测试模式")
    parser.add_argument("--max-files", type=int, default=10, help="最大测试文件数")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if args.batch or input_path.is_dir():
        batch_test_simple(args.input, args.max_files)
    else:
        test_single_image(args.input)


if __name__ == "__main__":
    main()