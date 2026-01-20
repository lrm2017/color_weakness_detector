#!/usr/bin/env python3
"""
色觉辅助滤镜演示脚本
展示所有滤镜效果
"""

import cv2
import numpy as np
from pathlib import Path
from color_vision_filters import ColorVisionFilters, FilterType
from image_utils import imread_unicode, imwrite_unicode
import argparse


def create_filter_comparison(image_path, output_dir=None):
    """
    创建滤镜对比图
    """
    # 读取原图
    original = imread_unicode(str(image_path))
    if original is None:
        print(f"错误：无法读取图像 {image_path}")
        return
    
    if output_dir is None:
        output_dir = Path("test_results/filter_demo")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"正在生成滤镜演示图像...")
    print(f"原图: {image_path}")
    print(f"输出目录: {output_dir}")
    
    # 获取图像尺寸
    h, w = original.shape[:2]
    
    # 创建滤镜效果对比
    filters_to_demo = [
        FilterType.NONE,
        FilterType.PROTANOPIA_ASSIST,
        FilterType.DEUTERANOPIA_ASSIST,
        FilterType.TRITANOPIA_ASSIST,
        FilterType.HIGH_CONTRAST,
        FilterType.EDGE_ENHANCEMENT,
        FilterType.BRIGHTNESS_BOOST,
        FilterType.SATURATION_BOOST,
        FilterType.GRAYSCALE,
        FilterType.INVERTED,
        FilterType.WARM_COOL_HIGHLIGHT,
        FilterType.RED_GREEN_SEPARATE,
        FilterType.BLUE_YELLOW_SEPARATE
    ]
    
    # 计算网格布局
    cols = 4
    rows = (len(filters_to_demo) + cols - 1) // cols
    
    # 调整图像大小以适应网格
    target_w, target_h = 300, 200
    
    # 创建大图
    grid_w = cols * target_w
    grid_h = rows * target_h
    grid_image = np.zeros((grid_h, grid_w, 3), dtype=np.uint8)
    
    for i, filter_type in enumerate(filters_to_demo):
        row = i // cols
        col = i % cols
        
        # 应用滤镜
        filtered = ColorVisionFilters.apply_filter(original, filter_type)
        
        # 调整大小
        resized = cv2.resize(filtered, (target_w, target_h))
        
        # 添加标题
        title = ColorVisionFilters.get_filter_description(filter_type)
        if len(title) > 20:
            title = title[:17] + "..."
        
        # 在图像上添加文字
        cv2.putText(resized, title, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(resized, title, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 0, 0), 1, cv2.LINE_AA)
        
        # 放置到网格中
        y1 = row * target_h
        y2 = y1 + target_h
        x1 = col * target_w
        x2 = x1 + target_w
        
        grid_image[y1:y2, x1:x2] = resized
        
        # 保存单个滤镜效果
        filter_filename = f"{Path(image_path).stem}_{filter_type.value}.jpg"
        imwrite_unicode(str(output_dir / filter_filename), filtered)
        
        print(f"  ✓ {title}")
    
    # 保存网格对比图
    grid_filename = f"{Path(image_path).stem}_filters_comparison.jpg"
    imwrite_unicode(str(output_dir / grid_filename), grid_image)
    
    print(f"\n演示完成！")
    print(f"网格对比图: {output_dir / grid_filename}")
    print(f"单个滤镜图: {output_dir}/*_{Path(image_path).stem}_*.jpg")


def demo_specific_filters(image_path, output_dir=None):
    """
    演示特定的辅助滤镜
    """
    if output_dir is None:
        output_dir = Path("test_results/filter_demo")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取原图
    original = imread_unicode(str(image_path))
    if original is None:
        print(f"错误：无法读取图像 {image_path}")
        return
    
    print(f"\n=== 色觉辅助滤镜演示 ===")
    print(f"原图: {image_path}")
    
    # 重点演示的滤镜
    key_filters = [
        (FilterType.PROTANOPIA_ASSIST, "红色盲用户"),
        (FilterType.DEUTERANOPIA_ASSIST, "绿色盲用户"),
        (FilterType.TRITANOPIA_ASSIST, "蓝色盲用户"),
        (FilterType.WARM_COOL_HIGHLIGHT, "暖冷色区分"),
        (FilterType.RED_GREEN_SEPARATE, "红绿色区分"),
        (FilterType.BLUE_YELLOW_SEPARATE, "蓝黄色区分"),
        (FilterType.HIGH_CONTRAST, "高对比度增强")
    ]
    
    for filter_type, description in key_filters:
        print(f"\n{description}:")
        print(f"  滤镜: {ColorVisionFilters.get_filter_description(filter_type)}")
        
        # 应用滤镜
        filtered = ColorVisionFilters.apply_filter(original, filter_type)
        
        # 保存结果
        filename = f"{Path(image_path).stem}_{filter_type.value}_demo.jpg"
        output_path = output_dir / filename
        imwrite_unicode(str(output_path), filtered)
        
        print(f"  输出: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="色觉辅助滤镜演示")
    parser.add_argument("image", help="输入图像路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--comparison", action="store_true", help="生成滤镜对比图")
    parser.add_argument("--demo", action="store_true", help="演示重点滤镜")
    parser.add_argument("--all", action="store_true", help="生成所有演示")
    
    args = parser.parse_args()
    
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"错误：文件不存在 {image_path}")
        return 1
    
    if args.all or args.comparison:
        create_filter_comparison(image_path, args.output)
    
    if args.all or args.demo:
        demo_specific_filters(image_path, args.output)
    
    if not (args.comparison or args.demo or args.all):
        # 默认行为：演示重点滤镜
        demo_specific_filters(image_path, args.output)
    
    return 0


if __name__ == "__main__":
    exit(main())