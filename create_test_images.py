#!/usr/bin/env python3
"""
生成测试图像用于测试色弱图谱识别程序
"""

import cv2
import numpy as np
from pathlib import Path


def create_warm_dominant_test():
    """创建暖色居多的测试图像"""
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200  # 灰色背景
    
    # 添加大量暖色块
    cv2.rectangle(img, (20, 20), (150, 150), (0, 0, 255), -1)    # 红色
    cv2.rectangle(img, (170, 20), (300, 150), (0, 165, 255), -1) # 橙色
    cv2.rectangle(img, (20, 170), (150, 300), (0, 255, 255), -1) # 黄色
    cv2.rectangle(img, (170, 170), (300, 300), (0, 100, 255), -1)# 深橙色
    
    # 添加少量冷色块（应该被圈出）
    cv2.circle(img, (350, 80), 40, (255, 0, 0), -1)    # 蓝色
    cv2.circle(img, (350, 200), 30, (0, 255, 0), -1)   # 绿色
    
    return img


def create_cool_dominant_test():
    """创建冷色居多的测试图像"""
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200  # 灰色背景
    
    # 添加大量冷色块
    cv2.rectangle(img, (20, 20), (150, 150), (255, 0, 0), -1)    # 蓝色
    cv2.rectangle(img, (170, 20), (300, 150), (0, 255, 0), -1)   # 绿色
    cv2.rectangle(img, (20, 170), (150, 300), (128, 0, 128), -1) # 紫色
    cv2.rectangle(img, (170, 170), (300, 300), (255, 255, 0), -1)# 青色
    
    # 添加少量暖色块（应该被圈出）
    cv2.circle(img, (350, 80), 40, (0, 0, 255), -1)    # 红色
    cv2.circle(img, (350, 200), 30, (0, 165, 255), -1) # 橙色
    
    return img


def main():
    output_dir = Path(__file__).parent / "test_images"
    output_dir.mkdir(exist_ok=True)
    
    # 创建暖色居多的测试图
    warm_img = create_warm_dominant_test()
    warm_path = output_dir / "warm_dominant.png"
    cv2.imwrite(str(warm_path), warm_img)
    print(f"已创建暖色居多测试图: {warm_path}")
    
    # 创建冷色居多的测试图
    cool_img = create_cool_dominant_test()
    cool_path = output_dir / "cool_dominant.png"
    cv2.imwrite(str(cool_path), cool_img)
    print(f"已创建冷色居多测试图: {cool_path}")
    
    print("\n测试图像生成完成！")
    print("使用方法：")
    print(f"  python color_detector.py {warm_path}")
    print(f"  python color_detector.py {cool_path}")


if __name__ == "__main__":
    main()
