#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试OCR图像识别
"""

import cv2
import easyocr
import numpy as np
from pathlib import Path

def debug_image_ocr(image_path):
    """调试图像OCR识别"""
    print(f"=== 调试图像: {image_path} ===")
    
    # 初始化EasyOCR
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    
    # 读取图像
    img = cv2.imread(image_path)
    if img is None:
        print("无法读取图像")
        return
    
    height, width = img.shape[:2]
    print(f"图像尺寸: {width}x{height}")
    
    # 定义多个区域进行测试
    regions = [
        {"name": "全图", "coords": (0, 0, width, height)},
        {"name": "左下角", "coords": (0, int(height*0.75), int(width*0.3), height)},
        {"name": "左下角大", "coords": (0, int(height*0.7), int(width*0.4), height)},
        {"name": "右下角", "coords": (int(width*0.7), int(height*0.75), width, height)},
        {"name": "底部", "coords": (0, int(height*0.8), width, height)},
        {"name": "左侧", "coords": (0, 0, int(width*0.3), height)},
        {"name": "右侧", "coords": (int(width*0.7), 0, width, height)},
    ]
    
    for region in regions:
        x1, y1, x2, y2 = region["coords"]
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            continue
        
        print(f"\n--- {region['name']} ({x1},{y1},{x2},{y2}) ---")
        
        try:
            results = reader.readtext(roi)
            if results:
                for i, (bbox, text, confidence) in enumerate(results):
                    print(f"  {i+1}. '{text}' (置信度: {confidence:.3f})")
                    print(f"     边界框: {bbox}")
            else:
                print("  未识别到文字")
        except Exception as e:
            print(f"  OCR失败: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("用法: python debug_ocr_image.py <图像路径>")
        sys.exit(1)
    
    debug_image_ocr(sys.argv[1])