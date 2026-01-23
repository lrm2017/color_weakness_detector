#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可视化遮挡结果工具
"""

import cv2
import numpy as np
import json
from pathlib import Path
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle

class MaskingVisualizer:
    def __init__(self):
        """初始化可视化器"""
        pass
    
    def create_before_after_comparison(self, original_path, masked_path, output_path, 
                                     result_info=None, show_bbox=True):
        """
        创建遮挡前后对比图
        
        Args:
            original_path: 原始图像路径
            masked_path: 遮挡后图像路径
            output_path: 输出对比图路径
            result_info: 遮挡结果信息
            show_bbox: 是否显示边界框
        """
        # 读取图像
        original_img = cv2.imread(original_path)
        masked_img = cv2.imread(masked_path)
        
        if original_img is None or masked_img is None:
            print(f"无法读取图像: {original_path} 或 {masked_path}")
            return False
        
        # 转换颜色空间
        original_rgb = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
        masked_rgb = cv2.cvtColor(masked_img, cv2.COLOR_BGR2RGB)
        
        # 创建对比图
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 显示原始图像
        ax1.imshow(original_rgb)
        ax1.set_title('原始图像', fontsize=14, fontweight='bold')
        ax1.axis('off')
        
        # 如果有结果信息且要显示边界框
        if result_info and show_bbox and result_info.get('success'):
            masked_regions = result_info.get('masked_regions', [])
            for region in masked_regions:
                bbox = region.get('bbox', [])
                if bbox and len(bbox) >= 4:
                    # 计算边界框的矩形
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]
                    x_min, x_max = min(x_coords), max(x_coords)
                    y_min, y_max = min(y_coords), max(y_coords)
                    
                    # 添加边界框
                    rect = Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                                   linewidth=2, edgecolor='red', facecolor='none')
                    ax1.add_patch(rect)
                    
                    # 添加文字标签
                    ax1.text(x_min, y_min - 5, f"'{region['text']}'", 
                           color='red', fontsize=10, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
        
        # 显示遮挡后图像
        ax2.imshow(masked_rgb)
        ax2.set_title('遮挡后图像', fontsize=14, fontweight='bold')
        ax2.axis('off')
        
        # 添加结果信息
        if result_info:
            info_text = []
            if result_info.get('success'):
                info_text.append(f"✓ 遮挡成功")
                info_text.append(f"遮挡区域数: {result_info.get('total_masked', 0)}")
                
                masked_regions = result_info.get('masked_regions', [])
                for i, region in enumerate(masked_regions[:3]):  # 最多显示3个
                    confidence = region.get('confidence', 0)
                    text = region.get('text', '')
                    info_text.append(f"区域{i+1}: '{text}' ({confidence:.2f})")
            else:
                info_text.append("✗ 遮挡失败")
                error = result_info.get('error', '未知错误')
                info_text.append(f"错误: {error}")
            
            # 在图像下方添加信息
            fig.text(0.5, 0.02, ' | '.join(info_text), ha='center', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.1)
        
        # 保存对比图
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
    
    def create_dataset_summary(self, dataset_path, output_path=None):
        """
        创建数据集遮挡效果总览
        
        Args:
            dataset_path: 数据集路径
            output_path: 输出图像路径
        """
        dataset_path = Path(dataset_path)
        
        # 读取遮挡结果
        results_file = dataset_path / "masked_images" / "masking_results.json"
        if not results_file.exists():
            print(f"未找到遮挡结果文件: {results_file}")
            return False
        
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 统计信息
        total_count = len(results)
        success_count = sum(1 for r in results if r['success'])
        success_rate = success_count / total_count * 100 if total_count > 0 else 0
        
        # 创建网格显示
        grid_size = min(6, int(np.ceil(np.sqrt(min(total_count, 36)))))  # 最多显示36个
        fig, axes = plt.subplots(grid_size, grid_size, figsize=(15, 15))
        
        if grid_size == 1:
            axes = [[axes]]
        elif len(axes.shape) == 1:
            axes = [axes]
        
        # 显示样本图像
        sample_results = results[:grid_size*grid_size]
        
        for i, result in enumerate(sample_results):
            row = i // grid_size
            col = i % grid_size
            ax = axes[row][col]
            
            filename = result['filename']
            masked_image_path = dataset_path / "masked_images" / filename
            
            if masked_image_path.exists():
                img = cv2.imread(str(masked_image_path))
                if img is not None:
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    ax.imshow(img_rgb)
                    
                    # 设置标题颜色
                    title_color = 'green' if result['success'] else 'red'
                    status = '✓' if result['success'] else '✗'
                    ax.set_title(f"{status} {filename}", fontsize=8, color=title_color)
                else:
                    ax.text(0.5, 0.5, '无法加载图像', ha='center', va='center')
                    ax.set_title(filename, fontsize=8)
            else:
                ax.text(0.5, 0.5, '图像不存在', ha='center', va='center')
                ax.set_title(filename, fontsize=8)
            
            ax.axis('off')
        
        # 隐藏多余的子图
        for i in range(len(sample_results), grid_size*grid_size):
            row = i // grid_size
            col = i % grid_size
            axes[row][col].axis('off')
        
        # 添加总体统计信息
        fig.suptitle(f'{dataset_path.name} 遮挡效果总览\n'
                    f'总计: {total_count} | 成功: {success_count} | 成功率: {success_rate:.1f}%',
                    fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        # 保存总览图
        if output_path is None:
            output_path = dataset_path / "masked_images" / "summary_overview.png"
        
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"数据集总览已保存: {output_path}")
        return True
    
    def create_detailed_comparisons(self, dataset_path, max_samples=10):
        """
        创建详细的对比图（原图 vs 遮挡图）
        
        Args:
            dataset_path: 数据集路径
            max_samples: 最大样本数
        """
        dataset_path = Path(dataset_path)
        
        # 读取遮挡结果
        results_file = dataset_path / "masked_images" / "masking_results.json"
        if not results_file.exists():
            print(f"未找到遮挡结果文件: {results_file}")
            return False
        
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        # 创建对比图目录
        comparison_dir = dataset_path / "masked_images" / "comparisons"
        comparison_dir.mkdir(exist_ok=True)
        
        # 选择样本（优先选择成功的）
        success_results = [r for r in results if r['success']]
        failure_results = [r for r in results if not r['success']]
        
        # 平衡选择成功和失败的样本
        max_success = min(len(success_results), max_samples // 2 + max_samples % 2)
        max_failure = min(len(failure_results), max_samples - max_success)
        
        selected_results = success_results[:max_success] + failure_results[:max_failure]
        
        print(f"创建 {len(selected_results)} 个详细对比图...")
        
        created_count = 0
        
        for result in selected_results:
            filename = result['filename']
            
            # 原始图像路径
            original_path = dataset_path / "original_images" / filename
            if not original_path.exists():
                original_path = dataset_path / filename
            
            # 遮挡后图像路径
            masked_path = dataset_path / "masked_images" / filename
            
            # 输出对比图路径
            comparison_path = comparison_dir / f"comparison_{filename.replace('.jpg', '.png')}"
            
            if original_path.exists() and masked_path.exists():
                success = self.create_before_after_comparison(
                    str(original_path), 
                    str(masked_path), 
                    str(comparison_path),
                    result,
                    show_bbox=True
                )
                
                if success:
                    created_count += 1
                    print(f"  ✓ 创建对比图: {comparison_path.name}")
                else:
                    print(f"  ✗ 创建失败: {comparison_path.name}")
            else:
                print(f"  ✗ 图像文件不存在: {filename}")
        
        print(f"完成! 共创建 {created_count} 个对比图，保存在: {comparison_dir}")
        return created_count > 0

def main():
    parser = argparse.ArgumentParser(description='可视化遮挡结果工具')
    parser.add_argument('--dataset', required=True, help='数据集路径')
    parser.add_argument('--summary', action='store_true', help='创建数据集总览')
    parser.add_argument('--comparisons', action='store_true', help='创建详细对比图')
    parser.add_argument('--max-samples', type=int, default=10, help='最大样本数')
    
    args = parser.parse_args()
    
    visualizer = MaskingVisualizer()
    
    if args.summary:
        visualizer.create_dataset_summary(args.dataset)
    
    if args.comparisons:
        visualizer.create_detailed_comparisons(args.dataset, args.max_samples)
    
    if not args.summary and not args.comparisons:
        # 默认创建总览和对比图
        visualizer.create_dataset_summary(args.dataset)
        visualizer.create_detailed_comparisons(args.dataset, args.max_samples)

if __name__ == "__main__":
    main()