#!/usr/bin/env python3
"""
色觉测试结果可视化
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from simple_color_test import analyze_color_channels


def create_color_distribution_chart(results, save_path=None):
    """
    创建颜色分布饼图
    """
    colors = []
    percentages = []
    color_names = []
    
    # 颜色映射 (RGB格式用于matplotlib)
    color_map = {
        'red': '#FF0000',
        'orange': '#FF8000', 
        'yellow': '#FFFF00',
        'green': '#00FF00',
        'cyan': '#00FFFF',
        'blue': '#0000FF',
        'purple': '#8000FF'
    }
    
    for color_name, stats in results['color_distribution'].items():
        if stats['percentage'] > 0.5:  # 只显示占比超过0.5%的颜色
            colors.append(color_map.get(color_name, '#808080'))
            percentages.append(stats['percentage'])
            color_names.append(f"{color_name}\n{stats['percentage']:.1f}%")
    
    # 创建饼图
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 颜色分布饼图
    ax1.pie(percentages, labels=color_names, colors=colors, autopct='', startangle=90)
    ax1.set_title(f"颜色分布 - {results['file']}")
    
    # 通道比例柱状图
    channels = ['红色', '绿色', '蓝色', '黄色']
    ratios = [
        results['red_green_channel']['red_ratio'] * 100,
        results['red_green_channel']['green_ratio'] * 100,
        results['blue_yellow_channel']['blue_ratio'] * 100,
        results['blue_yellow_channel']['yellow_ratio'] * 100
    ]
    bar_colors = ['red', 'green', 'blue', 'yellow']
    
    bars = ax2.bar(channels, ratios, color=bar_colors, alpha=0.7)
    ax2.set_ylabel('百分比 (%)')
    ax2.set_title('色觉通道分析')
    ax2.set_ylim(0, 100)
    
    # 添加数值标签
    for bar, ratio in zip(bars, ratios):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{ratio:.1f}%', ha='center', va='bottom')
    
    # 添加诊断信息
    diagnosis_text = f"诊断: {results['diagnosis']}"
    if results['notes']:
        diagnosis_text += "\n备注: " + "; ".join(results['notes'])
    
    fig.suptitle(diagnosis_text, fontsize=12, y=0.02)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    return fig


def create_visual_test_result(image_path, results, save_path=None):
    """
    创建可视化测试结果
    """
    # 读取原图
    image = cv2.imread(str(image_path))
    if image is None:
        return None
    
    # 转换为RGB用于matplotlib显示
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # 创建颜色掩码
    def create_color_mask(hsv_img, h_ranges, s_min=25, v_min=40):
        mask = np.zeros_like(hsv_img[:, :, 0])
        for h_range in h_ranges:
            lower = np.array([h_range[0], s_min, v_min])
            upper = np.array([h_range[1], 255, 255])
            range_mask = cv2.inRange(hsv_img, lower, upper)
            mask = cv2.bitwise_or(mask, range_mask)
        return mask
    
    # 创建各颜色通道的掩码
    red_mask = create_color_mask(hsv, [(0, 10), (156, 180)])
    green_mask = create_color_mask(hsv, [(35, 85)])
    blue_mask = create_color_mask(hsv, [(105, 130), (85, 105), (130, 156)])
    yellow_mask = create_color_mask(hsv, [(25, 35), (10, 25)])
    
    # 创建可视化图像
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 原图
    axes[0, 0].imshow(image_rgb)
    axes[0, 0].set_title('原始图像')
    axes[0, 0].axis('off')
    
    # 红色通道
    red_overlay = image_rgb.copy()
    red_overlay[red_mask > 0] = [255, 0, 0]  # 红色高亮
    axes[0, 1].imshow(red_overlay)
    axes[0, 1].set_title(f'红色通道 ({results["red_green_channel"]["red_ratio"]:.1%})')
    axes[0, 1].axis('off')
    
    # 绿色通道
    green_overlay = image_rgb.copy()
    green_overlay[green_mask > 0] = [0, 255, 0]  # 绿色高亮
    axes[0, 2].imshow(green_overlay)
    axes[0, 2].set_title(f'绿色通道 ({results["red_green_channel"]["green_ratio"]:.1%})')
    axes[0, 2].axis('off')
    
    # 蓝色通道
    blue_overlay = image_rgb.copy()
    blue_overlay[blue_mask > 0] = [0, 0, 255]  # 蓝色高亮
    axes[1, 0].imshow(blue_overlay)
    axes[1, 0].set_title(f'蓝色通道 ({results["blue_yellow_channel"]["blue_ratio"]:.1%})')
    axes[1, 0].axis('off')
    
    # 黄色通道
    yellow_overlay = image_rgb.copy()
    yellow_overlay[yellow_mask > 0] = [255, 255, 0]  # 黄色高亮
    axes[1, 1].imshow(yellow_overlay)
    axes[1, 1].set_title(f'黄色通道 ({results["blue_yellow_channel"]["yellow_ratio"]:.1%})')
    axes[1, 1].axis('off')
    
    # 综合分析
    axes[1, 2].axis('off')
    analysis_text = f"""
诊断结果: {results['diagnosis']}

红绿通道分析:
• 红色: {results['red_green_channel']['red_ratio']:.1%}
• 绿色: {results['red_green_channel']['green_ratio']:.1%}

蓝黄通道分析:
• 蓝色: {results['blue_yellow_channel']['blue_ratio']:.1%}
• 黄色: {results['blue_yellow_channel']['yellow_ratio']:.1%}

主要颜色分布:
"""
    
    for color, stats in results['color_distribution'].items():
        if stats['percentage'] > 2.0:
            analysis_text += f"• {color}: {stats['percentage']:.1f}%\n"
    
    if results['notes']:
        analysis_text += f"\n备注:\n"
        for note in results['notes']:
            analysis_text += f"• {note}\n"
    
    axes[1, 2].text(0.05, 0.95, analysis_text, transform=axes[1, 2].transAxes,
                   fontsize=10, verticalalignment='top', fontfamily='monospace')
    
    plt.suptitle(f'多通道色觉测试结果 - {Path(image_path).name}', fontsize=16)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"可视化结果已保存到: {save_path}")
    
    return fig


def main():
    parser = argparse.ArgumentParser(description="色觉测试结果可视化")
    parser.add_argument("image", help="输入图像路径")
    parser.add_argument("-o", "--output", help="输出图像路径")
    parser.add_argument("--show", action="store_true", help="显示图表")
    
    args = parser.parse_args()
    
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"错误：文件不存在: {image_path}")
        return 1
    
    # 分析图像
    results = analyze_color_channels(image_path)
    if results is None:
        print("无法分析图像")
        return 1
    
    # 生成输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = image_path.parent / f"{image_path.stem}_visualization.png"
    
    # 创建可视化
    fig = create_visual_test_result(image_path, results, output_path)
    
    # 创建分布图表
    chart_path = image_path.parent / f"{image_path.stem}_chart.png"
    chart_fig = create_color_distribution_chart(results, chart_path)
    
    if args.show:
        plt.show()
    else:
        plt.close('all')
    
    return 0


if __name__ == "__main__":
    exit(main())